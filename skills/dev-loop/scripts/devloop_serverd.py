#!/usr/bin/env python3
"""
devloop_serverd.py -- the part of the loop that has to outlive a turn.

Why this exists
---------------
Every agent harness is turn-based, and AGENTS.md states the consequence for native multi-agent
lanes: they "require a manager whose process outlives a turn" -- a subagent that has not
finished when the turn ends dies with the process. job.py already solved that for ONE unit of
work (a setsid orphan whose completion is a receipt the shell writes). What job.py does not do
is WATCH: nothing restarts a manager that died at minute two of an hour, nothing polls a run
while it is happening, and a stateless request/response MCP call cannot hold that either -- it
returns, and the watching stops with it.

This is the missing half: a supervisor process that starts, watches and restarts registered
workers, and publishes what it sees where any other process can read it.

Two kinds of worker, because the loop needs two different lifetimes:

  MANAGER  one long process driven to completion (an orchestrator, a held session, a lane
           runner). Spawned through job.py, so it is a setsid orphan with a shell-written
           receipt -- it survives the turn AND it survives this supervisor dying.
  MONITOR  a short periodic poller run on an interval (a `--once` status reader, a gate probe,
           any status script). Its exit code, duration and output tail are recorded each run.

The failure this file is designed against
-----------------------------------------
A supervisor that LOOKS ALIVE WHILE SUPERVISING NOTHING. Every choice below bends to it:

  * Nothing trusts a claim. `state.json` carries a `verdict` field and `status` NEVER reads it:
    the verdict is recomputed from measured facts -- is the pid alive, how old is the heartbeat,
    what state is each worker in. A daemon that died holding `verdict: supervising` reads back
    `dead`, in exactly the way job.py refuses to let a receipt outrank liveness.
  * Zero workers is not a healthy idle. An empty registry is REFUSED at startup (exit 2), and a
    running daemon whose last live worker is gone stops instead of ticking forever.
  * A stale heartbeat is its own verdict. A supervisor whose pid is alive but whose loop has
    stopped reads `stale`, never `supervising`.
  * A crash loop is capped and cannot be laundered. A worker that dies faster than
    --min-healthy-s counts as a flap, max_restarts bounds it, and the counters are CARRIED
    THROUGH a supervisor restart -- killing the supervisor does not hand a worker a fresh
    restart budget.

Transport: a JSON file, not a socket
------------------------------------
State is published as `<state-dir>/state.json`, written tmp+rename (atomic on one filesystem,
so a reader never sees half a document), beside an append-only `events.ndjson` of transitions.

Why a file. A socket dies with the process, and the single most important thing a reader must
be able to tell is "the supervisor is GONE" apart from "there never was one" -- over a dead
socket those are the same refused connection. A file survives the death and carries the pid,
the pid start-tick and the last heartbeat, so a reader can measure both facts for itself. It
also costs the reader nothing: cat, jq, any language, any harness, no port, no client library,
no auth, and it works from inside a container that can see the tree. The price is that readers
poll and the state is at most one --interval (default 5s) stale; every record carries its own
timestamp, so staleness is measurable rather than assumed. The events log is the post-mortem:
transitions survive even when the final state write does not.

If the daemon dies mid-run
--------------------------
The state file freezes at its last heartbeat. MANAGERS keep running -- they are setsid jobs and
their receipts are written by the shell -- so no work is lost, and the next `run` re-adopts any
whose job is still alive and carries its counters forward. MONITORS stop, because they run
inside the daemon; their last observation keeps its own timestamp so the gap is visible instead
of implied. No reader is fooled in the meantime: `status` measures pid liveness before it reads
anything the daemon claimed, and reports `dead` (the daemon recorded itself running and is
gone) or `orphaned` (it exited leaving live workers), never `supervising`.

Linux only, on purpose: liveness is job.py's /proc-based predicate (zombie-aware,
pid-reuse-guarded). On a box with no /proc every process would read as dead, so the supervisor
REFUSES TO START there rather than supervising by coin flip.

Registry (--workers FILE, or --workers-json '{...}')
----------------------------------------------------
  {"schema": "serverd.workers.v1", "workers": [
     {"id": "run", "kind": "manager", "argv": ["sh", "-c", "..."], "cwd": ".",
      "budget_s": 3600, "restart": "never|on-failure|always", "max_restarts": 3},
     {"id": "pulse", "kind": "monitor", "argv": ["python3", "agy_monitor.py", "--once", "S"],
      "interval_s": 15, "timeout_s": 10, "max_failures": 5}]}
  A bare list of worker objects is accepted too. A monitor's timeout_s must be <= its
  interval_s: monitors run inside the tick, so a monitor allowed to outlast its own interval
  would stall the supervision of every manager beside it.

Subcommands
  run     [--once | --max-ticks N | --budget S] [--dry-run]  the loop itself, in the foreground
  start                                                      detach `run` through job.py and
                                                             CONFIRM it came up -- a spawn that
                                                             returned is not a running daemon
  status  [--stale-after S]                                  recompute the verdict from facts
  stop    [--kill-workers]                                   signal it, and confirm it went away

Verdicts (derived, never read back from the file)
  supervising          alive, ticking, at least one live worker
  supervising_nothing  alive and ticking with nothing left to supervise   <- the headline failure
  degraded             alive and supervising, but a worker has failed
  stale                pid alive, heartbeat older than --stale-after: the loop is not ticking
  dead                 the daemon recorded itself running and its pid is gone, or it crashed
  orphaned             the daemon exited leaving live workers unsupervised
  failed / finished    it ended; a worker failed / everything ended cleanly
  absent / unreadable / unverifiable   no state file · corrupt file · written on another host

Exit codes: 0 supervising or finished clean · 1 usage or registry error · 2 CANNOT SUPERVISE
            (empty registry, another live daemon, no /proc, unwritable state dir, nothing to
            read) · 3 a worker failed, or the daemon died / left workers unsupervised · 4 alive
            but stale, or a state file this host cannot judge.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import job              # noqa: E402  detached jobs, shell-written receipts, liveness
import git_lock         # noqa: E402  index.lock-safe git, for the base-tree observation

try:
    import agy_session as _session   # noqa: E402  base-tree guard + lane-completion predicate
    _SESSION_ERR = ""
except Exception as _imp_err:        # degraded, and said out loud rather than hidden
    _session = None
    _SESSION_ERR = f"{type(_imp_err).__name__}: {_imp_err}"

SCHEMA = "serverd.v1"
WORKER_SCHEMA = "serverd.workers.v1"
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
KINDS = ("manager", "monitor")
RESTART_POLICIES = ("never", "on-failure", "always")

# A worker in one of these states is being supervised. Anything else is finished or given up on,
# and a daemon with none of them left is supervising nothing -- which is never healthy.
MANAGER_LIVE = ("pending", "running", "backoff")
MONITOR_LIVE = ("pending", "ok", "failing")
MANAGER_BAD = ("failed", "failed_permanent")
MONITOR_BAD = ("failed_permanent",)

# Daemon states that mean the loop is OVER. Unlike `running`, these are self-reports that cost
# the daemon something, so they are believed even if the pid is somehow still around.
TERMINAL_DAEMON_STATES = ("finished", "stopped", "once", "crashed")

VERDICT_EXIT = {
    "supervising": 0, "finished": 0,
    "degraded": 3, "failed": 3, "dead": 3, "orphaned": 3,
    "supervising_nothing": 2, "absent": 2, "unreadable": 2,
    "stale": 4, "unverifiable": 4,
}


class ConfigError(Exception):
    """The registry or the arguments are wrong. Exit 1 -- nothing was started."""


class CannotSupervise(Exception):
    """Preconditions for supervising are not met. Exit 2 -- and SAY so, never tick anyway."""


# --------------------------------------------------------------------------- small primitives

def _now() -> float:
    return round(time.time(), 3)


def pidstart_of(pid: int) -> str:
    """The process's start-tick, /proc/<pid>/stat field 22. Paired with the pid it is a stable
    identity: a recycled pid has a different start-tick, which is what stops a stale pid file
    from reading as a live daemon forever. job.py._alive consumes exactly this value."""
    try:
        fields = Path(f"/proc/{int(pid)}/stat").read_text().rsplit(")", 1)[1].split()
        return fields[19]
    except (OSError, IndexError, ValueError):
        return ""


def _alive(pid: int, pidstart: str) -> bool:
    """job.py's measured liveness predicate: zombie-aware and pid-reuse-guarded. Deliberately
    NOT reimplemented here -- a second, weaker liveness check is how a dead thing starts looking
    busy again."""
    return job._alive(int(pid or 0), pidstart or "")


def _tail(text: str, n: int = 400) -> str:
    text = (text or "").strip()
    return text if len(text) <= n else text[:n] + " ...(truncated)"


def read_json(path: Path):
    return json.loads(path.read_text())


def write_json_atomic(path: Path, doc) -> None:
    """tmp+rename on the same directory: a reader either sees the previous document or the new
    one, never a half-written one. This is the whole reason a crash cannot corrupt state."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(doc, indent=2, sort_keys=False) + "\n")
    os.replace(tmp, path)


def lane_ids_of(lanes_path: Path) -> list[str]:
    try:
        doc = read_json(lanes_path)
    except (OSError, json.JSONDecodeError):
        return []
    return [l["id"] for l in (doc.get("lanes") or []) if isinstance(l, dict) and l.get("id")]


# ------------------------------------------------------------------------------- the registry

def normalize_worker(raw, index: int, seen: set, default_cwd: Path) -> dict:
    if not isinstance(raw, dict):
        raise ConfigError(f"worker #{index}: expected an object, got {type(raw).__name__}")
    wid = str(raw.get("id") or "").strip()
    if not ID_RE.match(wid):
        raise ConfigError(f"worker #{index}: id {wid!r} must match {ID_RE.pattern} "
                          "(it becomes a job directory name)")
    if wid in seen:
        raise ConfigError(f"worker {wid!r}: duplicate id")
    seen.add(wid)
    kind = str(raw.get("kind") or "").strip()
    if kind not in KINDS:
        raise ConfigError(f"worker {wid!r}: kind must be one of {KINDS}, got {kind!r}")
    argv = raw.get("argv")
    if not isinstance(argv, list) or not argv or not all(isinstance(a, str) for a in argv):
        raise ConfigError(f"worker {wid!r}: argv must be a non-empty list of strings")
    cwd = Path(raw.get("cwd") or default_cwd)
    if not cwd.is_dir():
        raise ConfigError(f"worker {wid!r}: cwd {cwd} does not exist")
    # Resolve the command NOW. A worker whose command does not exist would otherwise spawn,
    # fail with 127, restart, fail again -- a crash loop that reads as supervision.
    if not (shutil.which(argv[0]) or Path(argv[0]).exists()):
        raise ConfigError(f"worker {wid!r}: command {argv[0]!r} not found on PATH")

    w = {"id": wid, "kind": kind, "argv": list(argv), "cwd": str(cwd.resolve()),
         "label": str(raw.get("label") or "")}
    if kind == "manager":
        w["budget_s"] = int(raw.get("budget_s") or 3600)
        # Default `never`: a manager that died mid-merge is not safely re-runnable and this
        # process cannot know whether it was. Restarting one is an explicit decision.
        w["restart"] = str(raw.get("restart") or "never")
        if w["restart"] not in RESTART_POLICIES:
            raise ConfigError(f"worker {wid!r}: restart must be one of {RESTART_POLICIES}")
        w["max_restarts"] = int(raw.get("max_restarts", 3))
        if w["budget_s"] <= 0:
            raise ConfigError(f"worker {wid!r}: budget_s must be > 0")
    else:
        w["interval_s"] = float(raw.get("interval_s") or 30)
        w["timeout_s"] = float(raw.get("timeout_s") or min(30.0, w["interval_s"]))
        w["max_failures"] = int(raw.get("max_failures", 5))
        if w["interval_s"] <= 0:
            raise ConfigError(f"worker {wid!r}: interval_s must be > 0")
        if w["timeout_s"] > w["interval_s"]:
            raise ConfigError(
                f"worker {wid!r}: timeout_s ({w['timeout_s']}) must be <= interval_s "
                f"({w['interval_s']}) -- monitors run inside the tick, so one allowed to outlast "
                "its own interval stalls the supervision of every manager beside it")
    return w


def load_workers(path: Path | None, inline: str | None, default_cwd: Path) -> list[dict]:
    if path and inline:
        raise ConfigError("pass --workers or --workers-json, not both")
    if path:
        try:
            doc = read_json(path)
        except OSError as e:
            raise ConfigError(f"--workers {path}: {e}") from None
        except json.JSONDecodeError as e:
            raise ConfigError(f"--workers {path}: invalid JSON: {e}") from None
    elif inline:
        try:
            doc = json.loads(inline)
        except json.JSONDecodeError as e:
            raise ConfigError(f"--workers-json: invalid JSON: {e}") from None
    else:
        raise ConfigError("no registry given: pass --workers FILE or --workers-json JSON")
    raw = doc if isinstance(doc, list) else (doc.get("workers") if isinstance(doc, dict) else None)
    if raw is None:
        raise ConfigError("registry must be a list of workers or an object with a 'workers' list")
    seen: set = set()
    return [normalize_worker(w, i, seen, default_cwd) for i, w in enumerate(raw)]


# ------------------------------------------------------------------- verdicts, derived from fact

def live_workers(doc: dict) -> list[str]:
    out = []
    for wid, rec in (doc.get("workers") or {}).items():
        live = MANAGER_LIVE if rec.get("kind") == "manager" else MONITOR_LIVE
        if rec.get("state") in live:
            out.append(wid)
    return sorted(out)


def failed_workers(doc: dict) -> list[str]:
    out = []
    for wid, rec in (doc.get("workers") or {}).items():
        bad = MANAGER_BAD if rec.get("kind") == "manager" else MONITOR_BAD
        if rec.get("state") in bad:
            out.append(wid)
    return sorted(out)


def derive_verdict(doc: dict, *, alive: bool, heartbeat_age_s: float | None,
                   stale_after_s: float) -> tuple[str, str]:
    """The whole point of this module, in one function.

    It reads ONLY measured facts: whether the pid is alive, how old the heartbeat is, and what
    state each worker is in. It deliberately does NOT read doc['verdict'] -- that field is an
    audit copy of what the daemon last concluded, and trusting it is how a corpse reports
    healthy. Same rule as job.py: liveness outranks the claim.
    """
    live, failed = live_workers(doc), failed_workers(doc)
    daemon = doc.get("daemon") or {}
    claimed_state, crash = daemon.get("state"), daemon.get("crash")

    # An ADMISSION is believed; a boast is not. A daemon that recorded itself finished, stopped
    # or crashed is taken at its word even while its pid lingers -- that claim can only make the
    # picture worse, and the loop it describes is over either way. (Measured: a process that
    # drives one --once tick in-process and then keeps running leaves its own live pid in the
    # file, and liveness alone read that as `supervising` long after supervision had stopped.)
    # A daemon that recorded itself RUNNING is believed only for as long as its pid backs it.
    if claimed_state in TERMINAL_DAEMON_STATES or not alive:
        if claimed_state == "crashed":
            return ("dead", f"the supervisor CRASHED ({crash or 'no reason recorded'}); "
                            f"{len(live)} worker(s) may still be running: "
                            f"{', '.join(live) or 'none'}")
        if claimed_state == "running":          # reachable only when the pid is gone
            return ("dead", "the daemon recorded itself RUNNING and its pid is gone: it died "
                            f"without finishing. {len(live)} worker(s) may still be running: "
                            f"{', '.join(live) or 'none'}")
        if live:
            return ("orphaned", f"the daemon exited ({claimed_state}) leaving {len(live)} "
                                f"worker(s) running unsupervised: {', '.join(live)}")
        if failed:
            return ("failed", f"the daemon ended with {len(failed)} failed worker(s): "
                              f"{', '.join(failed)}")
        return ("finished", "the daemon ended with every worker terminal and none failed")

    if heartbeat_age_s is not None and heartbeat_age_s > stale_after_s:
        return ("stale", f"pid is alive but the last heartbeat is {heartbeat_age_s}s old "
                         f"(> {stale_after_s}s): the loop is not ticking")
    if not live:
        return ("supervising_nothing",
                "the daemon is alive with no live worker: it is supervising NOTHING. "
                f"failed={', '.join(failed) or 'none'}; "
                f"terminal or absent={len(doc.get('workers') or {})} worker record(s)")
    if failed:
        return ("degraded", f"supervising {len(live)} worker(s) with {len(failed)} failed: "
                            f"live={', '.join(live)}; failed={', '.join(failed)}")
    return ("supervising", f"supervising {len(live)} worker(s): {', '.join(live)}")


def measure(state_path: Path, stale_after_s: float | None = None,
            now: float | None = None) -> dict:
    """Read the published state and RE-DERIVE its verdict here, in the reader's process."""
    now = time.time() if now is None else now

    def _early(verdict: str, reason: str, alive=False) -> dict:
        # EVERY return carries exit_code. A reader that has to guess one for the "I could not
        # read it" cases is a reader that will guess 0.
        return {"verdict": verdict, "reason": reason, "state_path": str(state_path),
                "daemon_alive": alive, "exit_code": VERDICT_EXIT.get(verdict, 3)}

    if not state_path.is_file():
        return _early("absent", f"no supervisor state at {state_path} -- none has ever run "
                                "here, or it ran with a different --state-dir")
    try:
        doc = read_json(state_path)
        if not isinstance(doc, dict):
            raise json.JSONDecodeError("not an object", "", 0)
    except (OSError, json.JSONDecodeError) as e:
        return _early("unreadable", f"{state_path} could not be read: {e}")

    d = doc.get("daemon") or {}
    host = d.get("host")
    if host and host != os.uname().nodename:
        return _early("unverifiable",
                      f"state was written on host {host!r}; this is {os.uname().nodename!r}, "
                      "so its pid cannot be measured from here", alive=None)
    pid = int(d.get("pid") or 0)
    alive = _alive(pid, str(d.get("pidstart") or ""))
    hb = float(d.get("heartbeat_at") or 0)
    age = round(now - hb, 1) if hb else None
    stale = stale_after_s if stale_after_s is not None else max(15.0, float(d.get("interval_s") or 5) * 3)
    verdict, reason = derive_verdict(doc, alive=alive, heartbeat_age_s=age, stale_after_s=stale)
    return {
        "verdict": verdict, "reason": reason, "state_path": str(state_path),
        "daemon_alive": alive, "pid": pid or None, "daemon_state_claimed": d.get("state"),
        "heartbeat_age_s": age, "stale_after_s": stale, "tick": d.get("tick"),
        "started_at": d.get("started_at"), "stop_reason": d.get("stop_reason"),
        "live_workers": live_workers(doc), "failed_workers": failed_workers(doc),
        "workers": {k: {"kind": v.get("kind"), "state": v.get("state"), "rc": v.get("rc"),
                        "restarts": v.get("restarts"), "runs": v.get("runs"),
                        "detail": v.get("detail")}
                    for k, v in (doc.get("workers") or {}).items()},
        "observations": doc.get("observations") or {},
        "recovery": doc.get("recovery") or {},
        # Kept for audit so a reader can SEE the divergence; never an input to the verdict above.
        "verdict_claimed_by_daemon": doc.get("verdict"),
        "exit_code": VERDICT_EXIT.get(verdict, 3),
    }


# -------------------------------------------------------------------------------- the daemon

class Supervisor:
    def __init__(self, *, root: Path, state_dir: Path, workers: list[dict],
                 interval_s: float = 5.0, observe_interval_s: float = 30.0,
                 min_healthy_s: float = 5.0, lanes_path: Path | None = None,
                 lane_jobs_root: Path | None = None, argv_record: list[str] | None = None):
        self.root = root.resolve()
        self.state_dir = state_dir.resolve()
        self.jobs_root = self.state_dir / "jobs"
        self.state_path = self.state_dir / "state.json"
        self.events_path = self.state_dir / "events.ndjson"
        self.lock_path = self.state_dir / "daemon.pid"
        self.resolved_path = self.state_dir / "workers.resolved.json"
        self.specs = {w["id"]: w for w in workers}
        self.interval_s = float(interval_s)
        self.observe_interval_s = float(observe_interval_s)
        self.min_healthy_s = float(min_healthy_s)
        self.lanes_path = lanes_path
        self.lane_jobs_root = lane_jobs_root
        self.argv_record = list(argv_record or sys.argv)
        self.state: dict = {}
        self._stop_signal: str | None = None
        self._next_observe = 0.0
        self._base_before = None

    # ---- preconditions ------------------------------------------------------------------

    def preflight(self) -> None:
        if not Path("/proc/self/stat").exists():
            raise CannotSupervise(
                "/proc is not available, so process liveness cannot be measured. Every worker "
                "would read as dead and this supervisor would be guessing. Refusing to start.")
        if not self.specs:
            raise CannotSupervise(
                "the registry lists no workers. A supervisor with nothing to supervise is "
                "refused here rather than started and reported healthy.")
        try:
            self.state_dir.mkdir(parents=True, exist_ok=True)
            self.jobs_root.mkdir(parents=True, exist_ok=True)
            probe = self.state_dir / ".writable"
            probe.write_text("ok\n")
            probe.unlink()
        except OSError as e:
            raise CannotSupervise(f"state dir {self.state_dir} is not writable: {e}") from None
        held = self._live_lock()
        if held:
            raise CannotSupervise(
                f"another supervisor is already live for this state dir (pid {held['pid']}, "
                f"started {held.get('started_at')}). Two supervisors would fight over "
                f"{self.state_path}. Stop it first: devloop_serverd.py stop "
                f"--state-dir {self.state_dir}")

    def _live_lock(self) -> dict | None:
        try:
            doc = read_json(self.lock_path)
        except (OSError, json.JSONDecodeError):
            return None
        if _alive(int(doc.get("pid") or 0), str(doc.get("pidstart") or "")):
            return doc
        return None

    def _acquire_lock(self) -> None:
        write_json_atomic(self.lock_path, {
            "pid": os.getpid(), "pidstart": pidstart_of(os.getpid()),
            "started_at": _now(), "host": os.uname().nodename, "argv": self.argv_record})

    def _release_lock(self) -> None:
        try:
            doc = read_json(self.lock_path)
            if int(doc.get("pid") or 0) == os.getpid():
                self.lock_path.unlink(missing_ok=True)
        except (OSError, json.JSONDecodeError):
            pass

    # ---- restart-safety -----------------------------------------------------------------

    def _job_generations(self, wid: str) -> list[int]:
        gens = []
        if self.jobs_root.is_dir():
            for d in self.jobs_root.iterdir():
                if d.is_dir() and d.name.startswith(wid + "."):
                    suffix = d.name[len(wid) + 1:]
                    if suffix.isdigit():
                        gens.append(int(suffix))
        return sorted(gens)

    def recover(self) -> dict:
        """Re-adopt what a previous supervisor left behind, or say plainly that we cannot.

        Managers are setsid jobs: they outlive their supervisor, so a restarted supervisor that
        blindly respawned them would run two of each. It adopts a job whose receipt says it is
        still running, and carries every counter forward -- restarts included, so a supervisor
        restart cannot launder a crash-looping worker's budget.
        """
        rec = {"attempted": True, "recovered": False, "adopted": [], "carried": [],
               "error": None, "previous_state": None}
        prev = None
        if self.state_path.is_file():
            try:
                prev = read_json(self.state_path)
                if not isinstance(prev, dict):
                    raise json.JSONDecodeError("not an object", "", 0)
            except (OSError, json.JSONDecodeError) as e:
                moved = self.state_path.with_name(f"state.json.corrupt.{int(time.time())}")
                try:
                    os.replace(self.state_path, moved)
                except OSError:
                    pass
                rec["error"] = (f"previous state was unreadable ({e}); moved to {moved}. "
                                "Restart counters and prior worker history are LOST -- this "
                                "supervisor starts them from zero and says so rather than "
                                "pretending to have recovered.")
                print(f"devloop_serverd: {rec['error']}", file=sys.stderr)
                prev = None
        if prev is not None:
            rec["recovered"] = True
            rec["previous_state"] = (prev.get("daemon") or {}).get("state")
        self._prev_workers = (prev or {}).get("workers") or {}
        return rec

    # ---- state --------------------------------------------------------------------------

    def _new_record(self, spec: dict) -> dict:
        old = self._prev_workers.get(spec["id"]) or {}
        base = {
            "id": spec["id"], "kind": spec["kind"], "state": "pending",
            "argv": spec["argv"], "cwd": spec["cwd"],
            "restarts": int(old.get("restarts") or 0),
            "runs": int(old.get("runs") or 0),
            "failures": int(old.get("failures") or 0),
            "gen": int(old.get("gen", -1)),
            "job_id": None, "pid": None, "rc": None, "detail": "",
            "started_at": None, "last_change": _now(), "adopted": False,
        }
        if spec["kind"] == "monitor":
            base.update({"next_run_at": 0.0, "last_run_at": None, "duration_s": None,
                         "consecutive_failures": int(old.get("consecutive_failures") or 0),
                         "output": ""})
        return base

    def _init_state(self, recovery: dict) -> None:
        self.state = {
            "schema": SCHEMA,
            "daemon": {
                "state": "running", "pid": os.getpid(), "pidstart": pidstart_of(os.getpid()),
                "host": os.uname().nodename, "started_at": _now(), "heartbeat_at": _now(),
                "tick": 0, "interval_s": self.interval_s, "root": str(self.root),
                "state_dir": str(self.state_dir), "jobs_root": str(self.jobs_root),
                "argv": self.argv_record, "python": sys.executable,
            },
            "recovery": recovery,
            "workers": {wid: self._new_record(spec) for wid, spec in self.specs.items()},
            "observations": {},
            "verdict": "supervising_nothing",
            "verdict_reason": "no tick has run yet",
            "verdict_note": "AUDIT COPY ONLY -- readers recompute this from pid liveness and "
                            "heartbeat age (see measure()); a reader that trusts this field "
                            "will believe a dead daemon.",
        }
        # Adopt still-running managers from the previous supervisor before the first tick, so we
        # never spawn a second copy of work that is already in flight.
        for wid, spec in self.specs.items():
            if spec["kind"] != "manager":
                continue
            gens = self._job_generations(wid)
            if not gens:
                continue
            jid = f"{wid}.{gens[-1]}"
            st = job.status(self.jobs_root, jid)
            r = self.state["workers"][wid]
            r["gen"] = gens[-1]
            if st["state"] == "running":
                r.update({"state": "running", "job_id": jid, "pid": st.get("pid"),
                          "started_at": st.get("started_at") or _now(), "adopted": True,
                          "detail": f"adopted a live job ({jid}) from a previous supervisor"})
                recovery["adopted"].append(jid)
                self._event("adopt", worker=wid, job_id=jid, pid=st.get("pid"))
            if self._prev_workers.get(wid, {}).get("restarts"):
                recovery["carried"].append(
                    f"{wid}: restarts={self._prev_workers[wid]['restarts']}")
        self._write_state()

    def _event(self, kind: str, **fields) -> None:
        """Append-only transition log. It survives a crash that eats the final state write, and
        it is the only place a post-mortem can see ordering."""
        line = json.dumps({"ts": _now(), "event": kind, **fields}, sort_keys=False)
        try:
            with self.events_path.open("a") as fh:
                fh.write(line + "\n")
        except OSError:
            pass

    def _set(self, rec: dict, state: str, detail: str = "") -> None:
        if rec["state"] != state or detail != rec.get("detail"):
            self._event("worker_state", worker=rec["id"], frm=rec["state"], to=state,
                        detail=detail, rc=rec.get("rc"))
        rec["state"], rec["detail"], rec["last_change"] = state, detail, _now()

    def _write_state(self) -> None:
        write_json_atomic(self.state_path, self.state)

    # ---- workers ------------------------------------------------------------------------

    def _spawn_manager(self, rec: dict, spec: dict, now: float) -> None:
        rec["gen"] += 1
        jid = f"{spec['id']}.{rec['gen']}"
        try:
            res = job.spawn(self.jobs_root, jid, spec["argv"], Path(spec["cwd"]),
                            budget_s=spec["budget_s"], label=spec["label"] or spec["id"],
                            replay="rerun")
        except Exception as e:                      # spawn itself failed: never silently retried
            rec["rc"] = None
            self._set(rec, "failed_permanent", f"spawn failed: {type(e).__name__}: {e}")
            return
        rec.update({"job_id": jid, "started_at": now, "rc": None, "runs": rec["runs"] + 1})
        self._event("spawn", worker=spec["id"], job_id=jid, result=res, argv=spec["argv"])
        self._set(rec, "running", f"job {jid} ({res})")

    def _tick_manager(self, rec: dict, spec: dict, now: float) -> None:
        if rec["state"] == "pending":
            self._spawn_manager(rec, spec, now)
            return
        if rec["state"] == "backoff":
            if now >= float(rec.get("next_start_at") or 0):
                rec["restarts"] += 1
                self._spawn_manager(rec, spec, now)
            return
        if rec["state"] != "running" or not rec["job_id"]:
            return

        st = job.status(self.jobs_root, rec["job_id"])
        rec["pid"] = st.get("pid")
        if st["state"] == "running":
            return

        rec["rc"] = st.get("rc")
        ran_for = now - float(rec.get("started_at") or now)
        ok = st["state"] == "done" and st.get("rc") == 0
        # `lost` is a hard-kill or a reboot: no receipt and no process. `forged` is a receipt the
        # wrapper did not write. Neither is a completion, and neither may read as one.
        detail = (f"job {st['state']}" + (f" rc={st.get('rc')}" if st.get("rc") is not None else "")
                  + f" after {ran_for:.1f}s")
        if ok and spec["restart"] != "always":
            self._set(rec, "done", detail)
            return
        if not ok:
            rec["failures"] += 1
            if ran_for < self.min_healthy_s:
                detail += f" (FLAP: shorter than --min-healthy-s {self.min_healthy_s:g}s)"
        if spec["restart"] == "never":
            self._set(rec, "failed", detail + "; restart policy 'never'")
            return
        if spec["restart"] == "on-failure" and ok:
            self._set(rec, "done", detail)
            return
        if rec["restarts"] >= spec["max_restarts"]:
            self._set(rec, "failed_permanent",
                      detail + f"; {rec['restarts']} restart(s) used of {spec['max_restarts']} "
                               "-- giving up rather than looping forever")
            return
        backoff = min(60.0, float(2 ** min(rec["restarts"], 6)))
        rec["next_start_at"] = now + backoff
        self._set(rec, "backoff", detail + f"; restart {rec['restarts'] + 1}/"
                                           f"{spec['max_restarts']} in {backoff:.0f}s")

    def _tick_monitor(self, rec: dict, spec: dict, now: float) -> None:
        if rec["state"] == "failed_permanent" or now < float(rec.get("next_run_at") or 0):
            return
        t0 = time.time()
        env = {**os.environ, "CI": "1", "GIT_TERMINAL_PROMPT": "0", "NO_COLOR": "1"}
        try:
            p = subprocess.run(spec["argv"], cwd=spec["cwd"], capture_output=True, text=True,
                               timeout=spec["timeout_s"], env=env)
            rc, out = p.returncode, (p.stdout or "") + (p.stderr or "")
        except subprocess.TimeoutExpired:
            rc, out = None, f"timed out after {spec['timeout_s']:g}s"
        except OSError as e:
            rc, out = None, f"could not run: {type(e).__name__}: {e}"
        rec.update({"runs": rec["runs"] + 1, "rc": rc, "output": _tail(out),
                    "last_run_at": _now(), "duration_s": round(time.time() - t0, 2),
                    "next_run_at": time.time() + spec["interval_s"]})
        if rc == 0:
            rec["consecutive_failures"] = 0
            self._set(rec, "ok", f"exit 0 in {rec['duration_s']}s")
            return
        rec["consecutive_failures"] += 1
        rec["failures"] += 1
        if spec["max_failures"] and rec["consecutive_failures"] >= spec["max_failures"]:
            self._set(rec, "failed_permanent",
                      f"{rec['consecutive_failures']} consecutive failures (last rc={rc}): "
                      f"{_tail(out, 160)}")
        else:
            self._set(rec, "failing", f"rc={rc}: {_tail(out, 160)}")

    # ---- observations -------------------------------------------------------------------

    def _observe_base_tree(self) -> dict:
        """Watch for edits to the base tree while lanes run. Absence of an answer is reported as
        absence, never as a clean tree -- an instrument that is missing has measured nothing."""
        if _session is None:
            return {"available": False,
                    "reason": f"agy_session could not be imported ({_SESSION_ERR}); base-tree "
                              "drift is NOT being watched"}
        snap = _session.base_tree_state(self.root)
        probe_err = ""
        if snap is None:
            # git refused. Distinguish "no repository here" from "a lane is holding index.lock":
            # only the second is worth retrying, and run_git_safe is what retries through it.
            # (The quiet rev-parse first also keeps git_lock's own chatty rev-parse off stderr
            # when there is no repository at all.)
            seen = subprocess.run(["git", "-C", str(self.root), "rev-parse", "--git-dir"],
                                  capture_output=True, text=True)
            if seen.returncode != 0:
                probe_err = (seen.stderr or "").strip()[:200]
            else:
                probe = git_lock.run_git_safe(["status", "--porcelain"], cwd=self.root)
                probe_err = (probe.stderr or "").strip()[:200]
                if probe.returncode == 0:
                    snap = _session.base_tree_state(self.root)
        if snap is None:
            return {"available": False,
                    "reason": f"git could not read {self.root}: {probe_err or 'unknown error'}; "
                              "base-tree drift is NOT being watched"}
        if self._base_before is None:
            self._base_before = snap
            return {"available": True, "baseline_paths": len(snap), "changed_since_start": [],
                    "note": "baseline taken now; inherited dirt is never blamed on this run"}
        allowed = _session.BASE_TREE_ALWAYS_ALLOWED + (
            (_session.worktree_root_of(self.lanes_path),) if self.lanes_path else (".worktrees/",))
        strays = _session.stray_base_edits(self._base_before, snap, allowed)
        return {"available": True, "baseline_paths": len(self._base_before),
                "changed_since_start": strays,
                "note": ("paths outside every lane worktree that changed since this supervisor "
                         "started; lane gates read worktrees, so these were never gated")}

    def _observe_lanes(self) -> dict:
        if _session is None:
            return {"available": False, "reason": f"agy_session unavailable ({_SESSION_ERR})"}
        ids = lane_ids_of(self.lanes_path)
        if not ids:
            return {"available": False, "reason": f"{self.lanes_path} lists no lane ids"}
        jobs = self.lane_jobs_root if (self.lane_jobs_root and self.lane_jobs_root.is_dir()) else None
        outstanding = _session.missing_reports(self.root / ".devloop" / "native", ids, jobs)
        return {
            "available": True, "total": len(ids), "outstanding": outstanding,
            "finished": sorted(set(ids) - set(outstanding)),
            "predicate": ("shell-written job receipts (--lane-jobs-root)" if jobs else
                          "report-<id>.json files, which the reporting AGENT writes -- pass "
                          "--lane-jobs-root for a receipt-backed predicate the agent cannot fake"),
        }

    def _observe(self, now: float) -> None:
        if now < self._next_observe:
            return
        self._next_observe = now + self.observe_interval_s
        obs = self.state.setdefault("observations", {})
        obs["observed_at"] = _now()
        obs["base_tree"] = self._observe_base_tree()
        if self.lanes_path:
            obs["lanes"] = self._observe_lanes()

    # ---- the loop -----------------------------------------------------------------------

    def tick(self, now: float | None = None) -> dict:
        now = time.time() if now is None else now
        for wid, spec in self.specs.items():
            rec = self.state["workers"][wid]
            try:
                if spec["kind"] == "manager":
                    self._tick_manager(rec, spec, now)
                else:
                    self._tick_monitor(rec, spec, now)
            except Exception as e:      # a supervisor that dies of one bad worker supervises none
                self._event("tick_error", worker=wid, error=f"{type(e).__name__}: {e}")
                self._set(rec, "failed_permanent", f"supervisor error: {type(e).__name__}: {e}")
        self._observe(now)
        d = self.state["daemon"]
        d["tick"] += 1
        d["heartbeat_at"] = _now()
        self.state["live_workers"] = live_workers(self.state)
        self.state["failed_workers"] = failed_workers(self.state)
        v, why = derive_verdict(self.state, alive=True, heartbeat_age_s=0.0,
                                stale_after_s=max(15.0, self.interval_s * 3))
        self.state["verdict"], self.state["verdict_reason"] = v, why
        self.state["observed_verdict"] = v
        self._write_state()
        return self.state

    def _install_signals(self) -> None:
        def handler(signo, _frame):
            self._stop_signal = signal.Signals(signo).name
        for s in (signal.SIGTERM, signal.SIGINT):
            try:
                signal.signal(s, handler)
            except (ValueError, OSError):
                pass        # not the main thread / not supported: the loop still ends on budget

    def run(self, once: bool = False, max_ticks: int | None = None,
            budget_s: float | None = None) -> int:
        self.preflight()
        self._acquire_lock()
        recovery = self.recover()
        # Logged BEFORE the adoptions it causes, so the post-mortem trail reads in the order
        # things actually happened.
        self._event("start", pid=os.getpid(), workers=sorted(self.specs),
                    interval_s=self.interval_s, recovery=dict(recovery))
        self._init_state(recovery)
        write_json_atomic(self.resolved_path,
                          {"schema": WORKER_SCHEMA, "workers": list(self.specs.values())})
        self._install_signals()

        deadline = (time.time() + budget_s) if budget_s else None
        ticks, reason, crash = 0, "unknown", None
        bounded_probe = bool(once or max_ticks)     # a probe, not a run that ended on its own
        try:
            while True:
                self.tick()
                ticks += 1
                if self._stop_signal:
                    reason = f"signal {self._stop_signal}"
                    break
                if once:
                    reason = "--once"
                    break
                if not live_workers(self.state):
                    reason = "no live workers left"
                    break
                if max_ticks and ticks >= max_ticks:
                    reason = f"--max-ticks {max_ticks}"
                    break
                if deadline and time.time() >= deadline:
                    reason = "--budget expired"
                    break
                time.sleep(self.interval_s)
        except Exception as e:
            # A supervisor that dies of its own bug must not die SILENTLY: without this the
            # traceback escapes, the final state write never happens, and the published file is
            # left claiming `running` with no record of why the loop stopped.
            crash = f"{type(e).__name__}: {e}"
            reason = f"supervisor crashed: {crash}"
            print(f"devloop_serverd: {reason}", file=sys.stderr)
        finally:
            observed = self.state.get("observed_verdict", "supervising_nothing")
            observed_why = self.state.get("verdict_reason", "")
            d = self.state["daemon"]
            d["state"] = ("crashed" if crash else
                          "stopped" if self._stop_signal else
                          "once" if bounded_probe else "finished")
            d["stopped_at"] = _now()
            d["stop_reason"] = reason
            d["ticks"] = ticks
            d["crash"] = crash
            # Record the verdict a READER will derive once this pid is gone, so the published
            # file never outlives the process still holding a claim only a live process can back.
            post, why = derive_verdict(self.state, alive=False, heartbeat_age_s=0.0,
                                       stale_after_s=max(15.0, self.interval_s * 3))
            self.state["verdict"], self.state["verdict_reason"] = post, why
            self.state["observed_verdict"] = observed
            self._write_state()
            self._event("stop", reason=reason, ticks=ticks, observed_verdict=observed,
                        post_mortem_verdict=post)
            self._release_lock()

        # WHICH verdict the exit code reports depends on WHY the loop ended, never on which
        # flags were passed. A bounded probe (--once, --max-ticks) that stopped while work was
        # still live is judged on what it OBSERVED -- that is the question it was asked. A loop
        # that ran out of live workers, took a signal or spent its budget is judged on what it
        # LEFT BEHIND, because by then "it was supervising when I looked" is not the news.
        left_live = bool(live_workers(self.state))
        chosen = post if crash else (observed if (bounded_probe and left_live) else post)
        print(json.dumps({"stopped_because": reason, "ticks": ticks,
                          "observed_verdict": observed, "post_mortem_verdict": post,
                          "verdict_used_for_exit": chosen,
                          "observed_reason": observed_why, "post_mortem_reason": why,
                          "crash": crash, "state": str(self.state_path)}, indent=2))
        return 3 if crash else VERDICT_EXIT.get(chosen, 3)

    def plan(self) -> dict:
        """--dry-run: everything that WOULD happen, and nothing that would. No state file is
        written, because a dry run that leaves a state file behind is a dry run that a later
        `status` reads as a daemon."""
        return {
            "dry_run": True, "would_supervise": len(self.specs),
            "root": str(self.root), "state_dir": str(self.state_dir),
            "state_path": str(self.state_path), "jobs_root": str(self.jobs_root),
            "interval_s": self.interval_s, "observe_interval_s": self.observe_interval_s,
            "min_healthy_s": self.min_healthy_s,
            "lanes": str(self.lanes_path) if self.lanes_path else None,
            "base_tree_guard": ("available" if _session is not None else
                                f"UNAVAILABLE ({_SESSION_ERR})"),
            "existing_state": measure(self.state_path)["verdict"],
            "lock_held_by": self._live_lock(),
            "workers": [
                {**w, "job_id_next": (f"{w['id']}.{(self._job_generations(w['id']) or [-1])[-1] + 1}"
                                      if w["kind"] == "manager" else None)}
                for w in self.specs.values()],
            "wrote_nothing": True,
        }


# ------------------------------------------------------------------------------------- CLI

def _add_common(p: argparse.ArgumentParser) -> None:
    p.add_argument("--root", default=".", help="repo root the workers run against")
    p.add_argument("--state-dir", help="default: <root>/.devloop/serverd")


def _state_dir_of(a) -> Path:
    return Path(a.state_dir).resolve() if a.state_dir else (Path(a.root).resolve() / ".devloop" / "serverd")


def _build(a) -> Supervisor:
    root = Path(a.root).resolve()
    workers = load_workers(Path(a.workers) if a.workers else None, a.workers_json, root)
    return Supervisor(root=root, state_dir=_state_dir_of(a), workers=workers,
                      interval_s=a.interval, observe_interval_s=a.observe_interval,
                      min_healthy_s=a.min_healthy_s,
                      lanes_path=Path(a.lanes).resolve() if a.lanes else None,
                      lane_jobs_root=Path(a.lane_jobs_root).resolve() if a.lane_jobs_root else None,
                      argv_record=sys.argv)


def cmd_run(a) -> int:
    sup = _build(a)
    if a.dry_run:
        if not sup.specs:
            print("devloop_serverd: the registry lists no workers -- nothing to supervise",
                  file=sys.stderr)
            return 2
        print(json.dumps(sup.plan(), indent=2))
        return 0
    return sup.run(once=a.once, max_ticks=a.max_ticks, budget_s=a.budget)


def cmd_start(a) -> int:
    """Detach `run` through job.py, then CONFIRM it came up. A spawn that returned is not a
    daemon: that assumption is the exact turn-boundary failure this whole file exists to fix."""
    sup = _build(a)
    sup.preflight()                                   # fail fast, in the caller's process
    state_dir = sup.state_dir
    state_dir.mkdir(parents=True, exist_ok=True)
    write_json_atomic(sup.resolved_path,
                      {"schema": WORKER_SCHEMA, "workers": list(sup.specs.values())})
    daemon_jobs = state_dir / "daemon"
    argv = [sys.executable, str(Path(__file__).resolve()), "run",
            "--root", str(sup.root), "--state-dir", str(state_dir),
            "--workers", str(sup.resolved_path),
            "--interval", str(sup.interval_s), "--observe-interval", str(sup.observe_interval_s),
            "--min-healthy-s", str(sup.min_healthy_s)]
    if sup.lanes_path:
        argv += ["--lanes", str(sup.lanes_path)]
    if sup.lane_jobs_root:
        argv += ["--lane-jobs-root", str(sup.lane_jobs_root)]
    if a.budget:
        argv += ["--budget", str(a.budget)]
    job.spawn(daemon_jobs, "serverd", argv, sup.root, budget_s=a.daemon_budget,
              label="devloop supervisor", replay="rerun")

    deadline = time.time() + a.start_timeout
    while time.time() < deadline:
        m = measure(sup.state_path)
        if m["verdict"] in ("supervising", "degraded", "supervising_nothing") and m.get("daemon_alive"):
            print(json.dumps({"started": True, "pid": m["pid"], "verdict": m["verdict"],
                              "reason": m["reason"], "state": str(sup.state_path),
                              "stop": f"{Path(__file__).name} stop --state-dir {state_dir}"},
                             indent=2))
            return VERDICT_EXIT.get(m["verdict"], 3)
        time.sleep(0.25)

    js = job.status(daemon_jobs, "serverd")
    err = _tail((daemon_jobs / "serverd" / "err").read_text(errors="ignore")
                if (daemon_jobs / "serverd" / "err").is_file() else "", 800)
    print(json.dumps({"started": False, "job_state": js["state"], "job_rc": js.get("rc"),
                      "waited_s": a.start_timeout, "daemon_stderr": err,
                      "reason": "no live daemon published a heartbeat within the timeout; "
                                "the spawn returning is NOT evidence that it is running"},
                     indent=2), file=sys.stderr)
    return 2


def reap_job(jobs_root: Path, jid: str, grace_s: float = 5.0) -> dict:
    """TERM a worker's whole session, then MEASURE whether it actually went away.

    Measured here: a TERM'd job does not die instantly -- job.py's wrapper defers its trap until
    the foreground command returns, and `timeout` has its own grace -- so a snapshot taken
    immediately after signalling shows live pids and a snapshot a second later shows none.
    Reporting either one as the answer is guessing. This waits, escalates to KILL if the session
    is still populated, and reports the pids that survived even that.
    """
    signalled = job.kill(jobs_root, jid, "TERM")
    pidfile = jobs_root / jid / "pid"
    try:
        pid = int((pidfile.read_text().strip() or 0)) if pidfile.is_file() else 0
    except (OSError, ValueError):
        pid = 0
    deadline = time.time() + grace_s
    while pid and time.time() < deadline and job._session_pids(pid):
        time.sleep(0.2)
    survivors = job._session_pids(pid) if pid else []
    escalated = 0
    if survivors:
        escalated = job.kill(jobs_root, jid, "KILL")
        time.sleep(0.5)
        survivors = job._session_pids(pid) if pid else []
    return {"job_id": jid, "signalled_pids": signalled,
            "escalated_to_kill": bool(escalated), "still_alive": survivors}


def cmd_status(a) -> int:
    m = measure(_state_dir_of(a) / "state.json", a.stale_after)
    print(json.dumps(m, indent=2))
    return m.get("exit_code", VERDICT_EXIT.get(m["verdict"], 3))


def cmd_stop(a) -> int:
    state_dir = _state_dir_of(a)
    m = measure(state_dir / "state.json")
    if m["verdict"] in ("absent", "unreadable", "unverifiable"):
        print(json.dumps(m, indent=2), file=sys.stderr)
        return VERDICT_EXIT.get(m["verdict"], 2)
    if not m.get("daemon_alive"):
        print(json.dumps({"stopped": True, "already": m["verdict"], "reason": m["reason"]},
                         indent=2))
        return 0
    daemon_jobs = state_dir / "daemon"
    if (daemon_jobs / "serverd").is_dir():
        job.kill(daemon_jobs, "serverd", "TERM")      # by session id, never pgid (see job.py)
    else:
        try:
            os.kill(int(m["pid"]), signal.SIGTERM)
        except OSError as e:
            print(f"devloop_serverd: could not signal pid {m['pid']}: {e}", file=sys.stderr)
    deadline = time.time() + a.timeout
    while time.time() < deadline:
        m2 = measure(state_dir / "state.json")
        if not m2.get("daemon_alive"):
            killed = []
            if a.kill_workers:
                # Managers are setsid jobs in their own sessions, so the daemon's death never
                # took them with it. Killing them is a separate, explicit act.
                try:
                    recs = (read_json(state_dir / "state.json").get("workers") or {})
                except (OSError, json.JSONDecodeError) as e:
                    recs = {}
                    print(f"devloop_serverd: cannot read worker job ids to kill: {e}",
                          file=sys.stderr)
                for wid, rec in recs.items():
                    if rec.get("job_id"):
                        killed.append(reap_job(state_dir / "jobs", rec["job_id"]))
            survived = [k for k in killed if k["still_alive"]]
            print(json.dumps({"stopped": True, "verdict": m2["verdict"], "reason": m2["reason"],
                              "killed_workers": killed if a.kill_workers else None,
                              "workers_that_survived_kill": survived or None}, indent=2))
            # The daemon stopped, but --kill-workers asked for something that did not happen.
            return 3 if survived else 0
        time.sleep(0.25)
    print(json.dumps({"stopped": False, "pid": m["pid"], "waited_s": a.timeout,
                      "reason": "the daemon did not exit; it is still holding its state dir"},
                     indent=2), file=sys.stderr)
    return 3


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    for name in ("run", "start"):
        p = sub.add_parser(name)
        _add_common(p)
        p.add_argument("--workers", help="registry JSON file")
        p.add_argument("--workers-json", help="registry as an inline JSON string")
        p.add_argument("--interval", type=float, default=5.0, help="seconds between ticks")
        p.add_argument("--observe-interval", type=float, default=30.0,
                       help="seconds between base-tree / lane observations (they shell out)")
        p.add_argument("--min-healthy-s", type=float, default=5.0,
                       help="a worker that dies sooner than this counts as a flap")
        p.add_argument("--lanes", help="lane plan to observe lane completion against")
        p.add_argument("--lane-jobs-root", help="job.py root for lanes, so lane completion is "
                                                "read from shell receipts, not agent-written files")
        p.add_argument("--budget", type=float, help="stop the loop after this many seconds")
        if name == "run":
            p.add_argument("--once", action="store_true", help="one tick, then exit")
            p.add_argument("--max-ticks", type=int, help="stop after N ticks")
            p.add_argument("--dry-run", action="store_true",
                           help="validate and print the plan; start nothing, write nothing")
        else:
            p.add_argument("--start-timeout", type=float, default=20.0,
                           help="how long to wait for the daemon's first heartbeat")
            p.add_argument("--daemon-budget", type=int, default=86400,
                           help="hard wall-clock cap on the detached daemon")

    p = sub.add_parser("status")
    _add_common(p)
    p.add_argument("--stale-after", type=float,
                   help="heartbeat age that counts as stale (default: 3 x the daemon's interval, "
                        "minimum 15s)")

    p = sub.add_parser("stop")
    _add_common(p)
    p.add_argument("--timeout", type=float, default=15.0)
    p.add_argument("--kill-workers", action="store_true",
                   help="also kill the managers; by default they are left running, because they "
                        "are orphans by design and a later run re-adopts them")

    a = ap.parse_args(argv)
    try:
        if a.cmd == "run":
            return cmd_run(a)
        if a.cmd == "start":
            return cmd_start(a)
        if a.cmd == "status":
            return cmd_status(a)
        if a.cmd == "stop":
            return cmd_stop(a)
    except ConfigError as e:
        print(f"devloop_serverd: {e}", file=sys.stderr)
        return 1
    except CannotSupervise as e:
        print(f"devloop_serverd: CANNOT SUPERVISE -- {e}", file=sys.stderr)
        return 2
    return 1


if __name__ == "__main__":
    sys.exit(main())
