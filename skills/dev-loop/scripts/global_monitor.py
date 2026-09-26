#!/usr/bin/env python3
"""
global_monitor.py -- THE global reporting monitor for the dev loop.

One monitor, not one of many. It runs on a 30-second tick under WHICHEVER harness spawned as
the manager, it enumerates agents from EVERY harness, and its subject is staleness: agents that
have gone stale, and references that have gone stale.

It is a MONITOR worker in devloop_serverd.py's sense -- a short periodic poller the supervisor
runs on an interval, whose exit code, duration and output tail are recorded each run. It does
not supervise anything itself and it contains no loop of its own. Register it, do not daemonise
it (see "Registering this monitor" below).

Harness-agnostic by construction
--------------------------------
Nothing here needs a particular manager to be the one that started it. The primary signal is
the dev loop's OWN on-disk run layout (references/run-directory.md), which exists regardless of
which harness ran the lane: `.devloop/run-*/lane-<id>.json` names the lane AND its harness,
`worker-<id>.exit` is the receipt the shell writes, `jobs/<id>/` is the durable job record, and
`report-<id>.json` is the lane's own claim. Per-harness CLI queries are OPTIONAL enrichment;
each degrades on its own and none of them is required for the monitor to work.

The failure this file is designed against
-----------------------------------------
A MONITOR THAT REPORTS HEALTHY WHILE OBSERVING NOTHING. A naive monitor whose run directory is
missing, whose harness is not installed, or whose read permissions fail, emits "0 stale agents,
all healthy" -- a sentence indistinguishable from a genuinely clean fleet. So:

  * "clean" and "could not observe" are DIFFERENT VERDICTS, and the second is louder.
  * Every observation source reports `observed | blind | not_applicable` with a reason. A source
    that could not answer is listed by name in `coverage.blind_sources`.
  * `clean` is reachable ONLY from complete coverage with zero findings. Any blind source caps
    the verdict at `partial`, whatever the agent counts say.
  * Zero observing sources is verdict `blind` and a NON-ZERO EXIT, so the supervisor escalates
    an instrument that has stopped measuring rather than recording a calm tick.
  * A missing `.devloop` directory is `blind`, never "an empty fleet": you cannot tell "no runs
    ever happened" from "you were pointed at the wrong root".

Staleness: silence is NOT evidence of death
-------------------------------------------
agy_monitor.py carries a measured finding this monitor must not regress. On a real multi-lane
run a manager went 128 SECONDS SILENT while a gate executed, and a time-based staleness
heuristic flipped the verdict to stalled on a perfectly healthy process. The lesson is that
silence is a poor proxy for death, so an explicit marker is preferred over a silence threshold.

Here the explicit marker is LIVENESS: job.py's /proc-based, zombie-aware, pid-reuse-guarded
predicate, plus the shell-written receipt. A lane with a live process is NEVER stale, for any
duration of silence. Staleness is only ever asserted from a POSITIVE fact:

  receipt   the shell wrote `worker-<id>.exit` = 125 (dispatch failed / no receipt recovered),
            or job.py reports `forged` (a receipt the wrapper did not write)
  liveness  job.py reports `lost`: no receipt AND the pid is gone
  marker    a run marker says `running` while the pid it names is dead
  budget    the process is genuinely alive but has outlived its own declared budget -- an
            explicit contract that was exceeded, not a threshold someone guessed
  supervisor  the supervisor recorded the worker failed

and exactly one weak basis, used ONLY where liveness is unmeasurable (no job record exists, so
there is no pid to ask about):

  silence   nothing has been written for --silence-after-s (default 900s, deliberately an order
            of magnitude above the measured 128s quiet period)

Silence-based findings are `confidence: "weak"`, are counted separately as `suspected_stale`,
and produce the distinct verdict `suspect` -- never `stale`. They cannot fire at all for a lane
whose liveness IS measurable. `--count-silence` promotes them, for a caller that wants it.

THREE outcomes, never collapsed into two
----------------------------------------
`outcome` is the top-level three-valued answer, and it is the word the headline prints:

  CLEAN         observed >=1 source that can enumerate agents, full coverage, nothing stale,
                nothing suspected, and no agent whose state could not be determined
  STALE         observed, and something is stale: a measured-stale agent, a stale reference, or
                a silence-based suspicion (which is LISTED, and marked unconfirmed)
  UNOBSERVABLE  could not observe. Either nothing could enumerate agents at all, or some source
                went blind, or some enumerated agent's state could not be determined. The report
                then says WHAT could not be seen (coverage.blind_sources, agents.unknown) and WHY.

`verdict` keeps the finer five-value lattice underneath, so nothing is lost by the collapse:

  blind    no source observed anything -- the monitor is not measuring    <- the headline failure
  stale    >=1 measured-stale agent, or the reference scan found stale references
  partial  >=1 source is blind, or >=1 enumerated agent is `unknown`: coverage is incomplete,
           so `clean` cannot be claimed
  suspect  full coverage, nothing measured-stale, but >=1 silence-based suspicion
  clean    full coverage, no findings, nothing suspected, nothing undetermined

  verdict -> outcome:  clean->CLEAN   suspect,stale->STALE   partial,blind->UNOBSERVABLE

Exit codes
----------
  0  CLEAN
  5  STALE         -- distinct from CLEAN by requirement: the three outcomes are three codes
  3  UNOBSERVABLE  -- the loudest, because an instrument that stopped measuring is worse than
                     a fleet with a known fault
  4  --strict: any outcome but CLEAN, for a gate that wants one code
  1  usage error.   2  the report could not be published.

  --supervised INVERTS the emphasis for devloop_serverd, and the registration below uses it.
  Under a supervisor, findings must NOT ride the exit code: max_failures consecutive non-zero
  exits mark a monitor `failed_permanent`, and a monitor that is the only live worker then ends
  the supervisor. A persistently stale fleet would therefore kill the very monitor reporting it.
  So --supervised returns 0 for CLEAN and for STALE -- the finding lives in the report -- and
  keeps 3 for verdict `blind` ALONE, where escalating to failed_permanent is the right outcome:
  a monitor that has enumerated nothing for max_failures ticks should be declared broken, not
  left ticking calmly over an empty view.

Registering this monitor (devloop_serverd.py worker registry, `serverd.workers.v1`)
  {"schema": "serverd.workers.v1", "workers": [
     {"id": "global", "kind": "monitor",
      "argv": ["python3", "<this dir>/global_monitor.py", "--once", "--supervised", "--quiet",
               "--root", ".", "--report-out", ".devloop/global-monitor.json"],
      "cwd": ".", "interval_s": 30, "timeout_s": 25, "max_failures": 5}]}
  `timeout_s` MUST be <= `interval_s` (the supervisor refuses otherwise: monitors run inside the
  tick). Pass --supervised there, for the reason in the exit-code table above.

What "a 30-second tick" honestly means, and why a long scan cannot corrupt anything
-----------------------------------------------------------------------------------
The supervisor is single-threaded: `tick()` calls a BLOCKING subprocess.run(..., timeout=
timeout_s) inline, and sets `next_run_at = time.time() + interval_s` AFTER the run returns.
There is no thread, pool or queue, so runs NEVER overlap, are never queued, and are never
skipped -- but `interval_s` is a GAP AFTER COMPLETION, not a wall-clock period. Measured on the
supervisor: a monitor sleeping 2s at interval_s=3 started every 5.015s, i.e. duration+interval,
and the daemon's own --interval quantises that further. So 30s means "at least 30s after the
previous scan ended, plus up to one daemon tick" -- claiming an exact 30s cadence would be an
overclaim, and this file does not make it.

A scan can therefore never overlap into corruption from the supervisor's side. Two defences
cover the side the supervisor does not control -- a human, a second supervisor, or an AGY
workflow running this by hand at the same moment:
  * --deadline-s (default 25s) bounds the scan from the inside, so the supervisor's kill at
    timeout_s is a backstop rather than the mechanism. A killed run is recorded rc=None and
    counts as a failure; a self-bounded one returns a report.
  * --report-out is published tmp+rename with a PID-UNIQUE temporary name, so two monitors
    writing the same path cannot interleave into a half-written document. rename(2) is atomic
    on one filesystem: a reader sees the old report or the new one, never a torn one.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import re
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

try:
    import job as _job                      # /proc liveness + shell-written receipts
    _JOB_ERR = ""
except Exception as _e:                     # degraded, and said out loud rather than hidden
    _job = None
    _JOB_ERR = f"{type(_e).__name__}: {_e}"

try:
    import devloop_serverd as _serverd      # measure(): re-derives the supervisor verdict here
    _SERVERD_ERR = ""
except Exception as _e:
    _serverd = None
    _SERVERD_ERR = f"{type(_e).__name__}: {_e}"

SCHEMA = "devloop.globalmonitor.v1"
TICK_S = 30.0                   # the operator's specified tick rate; also the registry default
DEFAULT_SILENCE_S = 900.0       # >> the measured 128s quiet period (agy_monitor.py)
DEFAULT_DEADLINE_S = 25.0       # under a 30s tick, with room for the supervisor's own timeout

# Severity order, least to most severe. A verdict is the max over every axis.
VERDICTS = ("clean", "suspect", "partial", "stale", "blind")

# The three top-level outcomes the operator asked for, and the only words the headline prints.
# The five-value verdict above stays in the report underneath, so collapsing to three loses
# nothing -- but a reader who takes only one field takes a three-valued one, never a boolean.
CLEAN, STALE, UNOBSERVABLE = "CLEAN", "STALE", "UNOBSERVABLE"
OUTCOME_OF = {"clean": CLEAN, "suspect": STALE, "stale": STALE,
              "partial": UNOBSERVABLE, "blind": UNOBSERVABLE}

# One code per outcome, so a caller that reads only $? still gets three answers, not two.
OUTCOME_EXIT = {CLEAN: 0, STALE: 5, UNOBSERVABLE: 3}


def outcome_of(verdict: str) -> str:
    """Collapse the verdict lattice to the three outcomes. An unknown verdict is UNOBSERVABLE --
    degrading pessimistically, never into CLEAN."""
    return OUTCOME_OF.get(verdict, UNOBSERVABLE)

# Source status vocabulary. `not_applicable` is NOT a pass -- it says the source has nothing to
# do with this tree, and it never counts as an observation.
OBSERVED, BLIND, NA = "observed", "blind", "not_applicable"

# Sources that can actually ENUMERATE agents. `blind` is judged on these alone, because
# `process_scan` only corroborates -- it reads /proc, so it answers on any Linux box whatever
# the tree looks like. Counting it as an observation would make `blind` almost unreachable and
# hand this monitor the exact failure it exists to prevent: a calm tick over an empty view.
# (Caught by tests/test_global_monitor.py, which refused the first version of this rule.)
ENUMERATING_SOURCES = ("devloop_runs", "serverd", "native_marker", "agy_teamwork", "harness_cli")

# `worker-<id>.exit` values with a meaning beyond "the command returned this"
# (references/run-directory.md 3).
EXIT_TIMEOUT = 124
EXIT_NEVER_STARTED = 125


# --------------------------------------------------------------------------- harness registry

# What is ACTUALLY observable per harness. Every `verified` entry below was measured by running
# the command named in `evidence`; anything unverified says so, and an unverified guess at a
# session path is not permitted here. This table is REPORTED as-is so a reader can judge the
# monitor's reach instead of trusting it.
HARNESSES = [
    {
        "harness": "claude-code", "bin": "claude",
        "live_query": ["agents", "--json"], "parse": "json_array",
        "signal": "`claude agents --json` prints active interactive AND background sessions as "
                  "a JSON array (pid, cwd, kind, startedAt, sessionId, status) and explicitly "
                  "does not require a TTY",
        "confidence": "verified",
        "evidence": "ran `claude agents --json`: returned one record, status 'busy', pid 108 -- "
                    "the same pid `ps -eo pid,args` showed for the live harness process",
    },
    {
        "harness": "opencode", "bin": "opencode",
        "live_query": ["session", "list"], "parse": "lines",
        "signal": "`opencode session list` runs headlessly and lists sessions",
        "confidence": "verified",
        "evidence": "ran `opencode session list`: exited 0 with empty output (no sessions "
                    "existed). It is a session LIST, not a liveness probe -- a listed session "
                    "is not necessarily running",
    },
    {
        "harness": "codex", "bin": "codex",
        "live_query": None, "parse": None,
        "signal": "NOT OBSERVABLE from a monitor. `codex agents` browses agent sessions on the "
                  "shared local app-server daemon but is a TUI",
        "confidence": "verified",
        "evidence": "ran `codex agents` non-interactively: printed 'ERROR: stdin is not a "
                    "terminal'. No non-TTY listing subcommand appears in `codex --help`",
    },
    {
        "harness": "copilot", "bin": "copilot",
        "live_query": None, "parse": None,
        "signal": "NOT OBSERVABLE from a monitor. The `sessions` subcommand manages saved "
                  "sessions only",
        "confidence": "verified",
        "evidence": "`copilot sessions --help` lists exactly one subcommand, `import`; "
                    "`copilot sessions list` fails with 'unrecognized subcommand'",
    },
    {
        "harness": "antigravity", "bin": "agy",
        "live_query": None, "parse": None,
        "signal": "NOT OBSERVABLE via the CLI. Its own state directory holds conversation "
                  "artifacts, not liveness. The dev loop's run marker is the signal instead -- "
                  "see the `native_marker` source",
        "confidence": "verified",
        "evidence": "`agy --help` lists no session/conversation listing subcommand (`agents` "
                    "lists agent TYPES). A presence/*.lock left in its state dir tested FREE "
                    "under a non-blocking flock with no process holding it, so the file's "
                    "existence is not liveness",
    },
    {
        "harness": "gemini-cli", "bin": "gemini",
        "live_query": None, "parse": None,
        "signal": "A `--list-sessions` flag exists but could not be exercised: it refuses "
                  "before listing unless an auth method is configured, so it is not a "
                  "dependable monitor probe",
        "confidence": "unverified",
        "evidence": "ran `gemini --list-sessions`: refused with 'Please set an Auth method'. "
                    "Whether it lists LIVE sessions or only saved ones is therefore unmeasured",
    },
    {
        "harness": "cursor", "bin": "agent",
        "live_query": None, "parse": None,
        "signal": "not installed here",
        "confidence": "verified",
        "evidence": "`command -v agent` and `adapters.py probe` both report MISSING",
    },
]


def _now() -> float:
    return time.time()


def _iso(ts: float | None = None) -> str:
    return datetime.fromtimestamp(ts if ts is not None else _now(),
                                  tz=timezone.utc).isoformat(timespec="seconds")


def _worst(*verdicts: str) -> str:
    """Max over the severity lattice. Anything unknown is treated as the worst, never the best."""
    best = "clean"
    for v in verdicts:
        if v not in VERDICTS:
            return "blind"
        if VERDICTS.index(v) > VERDICTS.index(best):
            best = v
    return best


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _mtime(path: Path) -> float | None:
    try:
        return path.stat().st_mtime
    except OSError:
        return None


def _newest_mtime(paths) -> float | None:
    best = None
    for p in paths:
        m = _mtime(p)
        if m is not None and (best is None or m > best):
            best = m
    return best


def agent(agent_id: str, harness: str, source: str, state: str, *, stale: bool = False,
          basis: str = "", confidence: str = "measured", reason: str = "",
          where: str = "", pid=None, last_signal_s=None) -> dict:
    """One agent record. `stale` is never set without a `basis` naming the fact that proved it."""
    if stale and not basis:
        raise ValueError(f"{agent_id}: stale asserted with no basis -- refusing to invent one")
    return {"agent_id": agent_id, "harness": harness or "unknown", "source": source,
            "state": state, "stale": bool(stale), "basis": basis,
            "confidence": confidence if stale else "n/a", "reason": reason,
            "where": where, "pid": pid,
            "last_signal_s": round(last_signal_s, 1) if last_signal_s is not None else None}


def source(name: str, status: str, reason: str, *, agents=None, detail=None) -> dict:
    return {"source": name, "status": status, "reason": reason,
            "agents": list(agents or []), "detail": detail or {}}


# ------------------------------------------------------------------- source: dev-loop run dirs

def _job_state(jobs_root: Path, lane_id: str) -> dict:
    """job.py's view of a lane, or an explicit 'unmeasurable' -- never an assumed absence."""
    if _job is None:
        return {"ok": False, "why": f"job.py could not be imported ({_JOB_ERR})"}
    if not (jobs_root / lane_id).is_dir():
        return {"ok": False, "why": "no job record for this lane"}
    try:
        return {"ok": True, "st": _job.status(jobs_root, lane_id)}
    except Exception as e:
        return {"ok": False, "why": f"job.py status failed: {type(e).__name__}: {e}"}


def _budget_of(jobs_root: Path, lane_id: str, lane: dict) -> float | None:
    """The lane's OWN declared budget. Never a default invented here."""
    try:
        txt = (jobs_root / lane_id / "budget").read_text().strip()
        if txt:
            return float(txt)
    except (OSError, ValueError):
        pass
    t = ((lane.get("worker") or {}).get("timeout_s"))
    try:
        return float(t) if t else None
    except (TypeError, ValueError):
        return None


def _classify_lane(run: Path, lane_path: Path, now: float, silence_after_s: float) -> dict:
    """Decide one lane's state from evidence, in the order the run-directory contract sets:
    receipt, then job liveness, then -- only where liveness cannot be measured -- silence."""
    lane_id, lane, harness = lane_path.stem[len("lane-"):], {}, "unknown"
    try:
        lane = _read_json(lane_path) or {}
        harness = str((lane.get("worker") or {}).get("harness") or "unknown")
    except (OSError, json.JSONDecodeError) as e:
        harness = "unknown"
        lane = {"_read_error": f"{type(e).__name__}: {e}"}

    aid = f"run:{run.name}:{lane_id}"
    where = str(run / f"lane-{lane_id}.json")
    jobs_root = run / "jobs"
    receipt = run / f"worker-{lane_id}.exit"
    artifacts = [lane_path, receipt, run / f"report-{lane_id}.json",
                 run / f"worker-{lane_id}.log", jobs_root / lane_id / "out"]
    age = None
    newest = _newest_mtime(artifacts)
    if newest is not None:
        age = max(0.0, now - newest)

    def mk(state, **kw):
        return agent(aid, harness, "devloop_run", state, where=where, last_signal_s=age, **kw)

    # 1. the receipt the SHELL wrote. It outranks every claim the lane made about itself.
    if receipt.is_file():
        raw = ""
        try:
            raw = receipt.read_text().strip()
        except OSError as e:
            return mk("unknown", reason=f"receipt unreadable: {type(e).__name__}: {e}")
        try:
            rc = int(raw)
        except ValueError:
            return mk("stale", stale=True, basis="receipt",
                      reason=f"receipt {raw!r} is not an exit code -- it was not written by the "
                             "shell wrapper")
        if rc == EXIT_NEVER_STARTED:
            return mk("stale", stale=True, basis="receipt",
                      reason="receipt 125: the lane never started, or ended leaving no receipt "
                             "of its own -- dispatched and gone")
        if rc == EXIT_TIMEOUT:
            return mk("finished", reason="receipt 124: the outer wall-clock timeout fired. The "
                                         "lane terminated -- a failure, not a stale agent")
        return mk("finished", reason=f"receipt {rc}: the lane command returned")

    # 2. no receipt: ask /proc, through the predicate job.py already guards for pid reuse.
    js = _job_state(jobs_root, lane_id)
    if js["ok"]:
        st = js["st"]
        pid, state = st.get("pid"), st.get("state")
        if state == "running":
            budget = _budget_of(jobs_root, lane_id, lane)
            started = st.get("started_at")
            ran = (now - float(started)) if started else None
            if budget and ran and ran > budget:
                return mk("stale", stale=True, basis="budget", pid=pid,
                          reason=f"alive for {ran:.0f}s against its own declared budget of "
                                 f"{budget:.0f}s -- an exceeded contract, not a guessed timeout")
            # THE 128-SECOND RULE. A live pid is not stale, for any length of silence.
            return mk("live", pid=pid, reason=(
                f"pid {pid} is alive"
                + (f", {ran:.0f}s into a {budget:.0f}s budget" if (budget and ran) else "")
                + ". Silence is not evidence of death (measured: 128s quiet while a gate ran)"))
        if state == "lost":
            return mk("stale", stale=True, basis="liveness", pid=pid,
                      reason="job lost: no receipt and the pid is gone. Live grandchildren may "
                             "remain -- clean up by session id, never by process group")
        if state == "forged":
            return mk("stale", stale=True, basis="receipt", pid=pid,
                      reason="job forged: a receipt the wrapper did not write, or pid reuse was "
                             "detected. Untrusted, and not done")
        if state == "done":
            return mk("finished", pid=pid,
                      reason=f"job done rc={st.get('rc')} (the shell receipt has not landed yet, "
                             "or was cleaned up)")
        # `absent`: the job directory exists but holds no usable record. Fall through to silence.

    # 3. liveness is UNMEASURABLE here. This is the only place a time threshold may speak, and
    #    it speaks weakly: `suspected`, never `stale`.
    why_blind = js.get("why", "job state unavailable")
    if age is None:
        return mk("unknown", reason=f"{why_blind}, and no artifact carries a timestamp: this "
                                    "lane's state CANNOT be determined from disk")
    if age >= silence_after_s:
        return mk("suspected", stale=True, basis="silence", confidence="weak",
                  reason=f"{why_blind}; nothing written for {age:.0f}s (>= {silence_after_s:.0f}s). "
                         "SUSPICION ONLY -- silence is a poor proxy for death and no pid was "
                         "available to ask")
    return mk("unknown", reason=f"{why_blind}; last artifact {age:.0f}s ago, under the "
                                f"{silence_after_s:.0f}s silence threshold. Undetermined, which "
                                "is not the same as healthy")


def scan_runs(root: Path, now: float, silence_after_s: float, max_runs: int) -> dict:
    """THE backbone source: harness-agnostic, because the dev loop writes it whoever ran the lane."""
    dl = root / ".devloop"
    if not dl.exists():
        return source("devloop_runs", BLIND,
                      f"no .devloop directory under {root}: agents CANNOT be enumerated. This is "
                      "not an empty fleet -- a wrong --root reads exactly the same way")
    if not dl.is_dir():
        return source("devloop_runs", BLIND, f"{dl} exists but is not a directory")
    try:
        runs = sorted((p for p in dl.glob("run-*") if p.is_dir()), key=lambda p: p.name)
    except OSError as e:
        return source("devloop_runs", BLIND,
                      f"{dl} could not be listed: {type(e).__name__}: {e}")
    detail = {"runs_found": len(runs), "runs_scanned": 0, "run_ids": [],
              "silence_after_s": silence_after_s}
    if not runs:
        return source("devloop_runs", OBSERVED,
                      f"{dl} is readable and holds no run-* directory: there are no dev-loop "
                      "runs here to watch", detail=detail)
    runs = runs[-max_runs:]
    agents, unreadable = [], []
    for run in runs:
        try:
            lanes = sorted(run.glob("lane-*.json"))
        except OSError as e:
            unreadable.append(f"{run.name}: {type(e).__name__}: {e}")
            continue
        detail["runs_scanned"] += 1
        detail["run_ids"].append(run.name)
        for lane_path in lanes:
            agents.append(_classify_lane(run, lane_path, now, silence_after_s))
    detail["unreadable_runs"] = unreadable
    if unreadable and not detail["runs_scanned"]:
        return source("devloop_runs", BLIND,
                      f"every run directory under {dl} refused to be listed: "
                      + "; ".join(unreadable[:3]), detail=detail)
    reason = (f"scanned {detail['runs_scanned']} of {len(runs)} run director(ies) under {dl}; "
              f"{len(agents)} lane(s) enumerated")
    if unreadable:
        reason += f"; {len(unreadable)} run(s) unreadable"
    return source("devloop_runs", OBSERVED, reason, agents=agents, detail=detail)


# ----------------------------------------------------------------------- source: the supervisor

def scan_serverd(state_path: Path, now: float) -> dict:
    """The supervisor's own workers are agents. Its verdict is RE-DERIVED here, by its own
    reader, rather than read back out of the file it wrote."""
    if _serverd is None:
        return source("serverd", BLIND,
                      f"devloop_serverd could not be imported ({_SERVERD_ERR}): supervised "
                      "workers are NOT being watched")
    if not state_path.exists():
        return source("serverd", NA,
                      f"no supervisor state at {state_path}: none has run here, or it ran with "
                      "a different --state-dir. No worker is claimed either way")
    try:
        m = _serverd.measure(state_path)
    except Exception as e:
        return source("serverd", BLIND,
                      f"{state_path} could not be measured: {type(e).__name__}: {e}")
    verdict = m.get("verdict")
    if verdict in ("unreadable", "unverifiable"):
        return source("serverd", BLIND, f"supervisor state {verdict}: {m.get('reason')}",
                      detail={"serverd_verdict": verdict})

    agents = []
    # The daemon itself. `supervising_nothing` is its own headline failure and is stale here too.
    bad_daemon = {"stale": "the supervisor's pid is alive but its loop has stopped ticking",
                  "dead": "the supervisor recorded itself running and its pid is gone",
                  "orphaned": "the supervisor exited leaving live workers unsupervised",
                  "supervising_nothing": "the supervisor is alive and supervising NOTHING"}
    if verdict in bad_daemon:
        agents.append(agent(f"serverd:daemon:{state_path.name}", "any", "serverd", "stale",
                            stale=True, basis="supervisor", where=str(state_path),
                            pid=m.get("pid"),
                            reason=f"{bad_daemon[verdict]} ({m.get('reason')})",
                            last_signal_s=m.get("heartbeat_age_s")))
    else:
        agents.append(agent(f"serverd:daemon:{state_path.name}", "any", "serverd",
                            "live" if m.get("daemon_alive") else "finished",
                            where=str(state_path), pid=m.get("pid"),
                            reason=f"supervisor verdict {verdict}: {m.get('reason')}",
                            last_signal_s=m.get("heartbeat_age_s")))

    for wid, w in (m.get("workers") or {}).items():
        st = w.get("state")
        aid = f"serverd:{wid}"
        if st in ("failed", "failed_permanent"):
            agents.append(agent(aid, "any", "serverd", "stale", stale=True, basis="supervisor",
                                where=str(state_path),
                                reason=f"{w.get('kind')} worker {st}: {w.get('detail')}"))
        elif st in ("running", "ok", "pending", "backoff", "failing"):
            agents.append(agent(aid, "any", "serverd", "live", where=str(state_path),
                                reason=f"{w.get('kind')} worker {st}: {w.get('detail')}"))
        else:
            agents.append(agent(aid, "any", "serverd", "finished", where=str(state_path),
                                reason=f"{w.get('kind')} worker {st}: {w.get('detail')}"))
    return source("serverd", OBSERVED,
                  f"supervisor verdict {verdict}, re-derived here from pid liveness and "
                  f"heartbeat age; {len(agents)} record(s)",
                  agents=agents,
                  detail={"serverd_verdict": verdict, "reason": m.get("reason"),
                          "heartbeat_age_s": m.get("heartbeat_age_s"),
                          "verdict_claimed_by_daemon": m.get("verdict_claimed_by_daemon")})


# -------------------------------------------------------------- source: explicit run marker(s)

def scan_agy_teamwork(root: Path, now: float) -> dict:
    """Antigravity's /teamwork-preview publishes its own state, and it is NOT under .devloop.

    It writes .agents/<phase>_level_<NN>_assignments.json (what it dispatched) and
    .agents/<phase>_level_<NN>_results.json (what came back), one pair per tree level.
    A level with assignments but no results is work still in flight; the newest results
    file is the run's progress marker. Without this source an AGY-hosted run is invisible
    here, and "0 agents" would read exactly like an idle tree -- the failure this whole
    monitor is built against.
    """
    agents_dir = root / ".agents"
    if not agents_dir.is_dir():
        return source("agy_teamwork", NA,
                      f"no {agents_dir} directory: no Antigravity teamwork run has been "
                      "hosted from this tree")
    try:
        assigns = sorted(agents_dir.glob("*_level_*_assignments.json"))
        results = sorted(agents_dir.glob("*_level_*_results.json"))
    except OSError as e:
        return source("agy_teamwork", BLIND,
                      f"{agents_dir} could not be listed: {type(e).__name__}: {e}")
    if not assigns and not results:
        return source("agy_teamwork", NA,
                      f"{agents_dir} exists but holds no *_level_*_{{assignments,results}}.json: "
                      "no teamwork run has published here")

    def _lv(pth: Path):
        m = re.match(r"(?P<phase>.+)_level_(?P<idx>\d+)_(assignments|results)\.json$", pth.name)
        return (m.group("phase"), int(m.group("idx"))) if m else (pth.name, -1)

    done = {_lv(r) for r in results}
    out, blind_detail = [], []
    for a in assigns:
        phase, idx = _lv(a)
        finished = (phase, idx) in done
        try:
            age = max(0.0, now - a.stat().st_mtime)
        except OSError as e:
            blind_detail.append(f"{a.name}: {type(e).__name__}")
            continue
        aid = f"agy:{phase}:level{idx:02d}"
        if finished:
            out.append(agent(aid, "antigravity", "agy_teamwork", "finished",
                             basis=f"{a.name} has a matching results file",
                             where=str(a.parent), last_signal_s=age))
        else:
            # In flight. Silence is NOT death: a level legitimately runs long while its
            # subagents work, which is the measured lesson agy_monitor.py already carries.
            out.append(agent(aid, "antigravity", "agy_teamwork", "live",
                             basis=f"{a.name} present with no matching results file yet",
                             where=str(a.parent), last_signal_s=age))
    if blind_detail and not out:
        return source("agy_teamwork", BLIND,
                      "every teamwork assignment file was unreadable: " + "; ".join(blind_detail))
    # ACCUMULATED OBJECTIVES. `.agents/ORIGINAL_REQUEST.md` is teamwork's record of the
    # request, it PERSISTS in the tree after the session that wrote it is gone, and it
    # ACCUMULATES: each run appends a `## <ISO8601>` section. A session started in the same
    # tree can therefore act on an EARLIER run's objective while its manager reports the
    # current one -- observed 2026-09-20: a run told to fix the drift gate also rewrote the
    # Rust resolver, which was the dead previous run's task, and both sets of edits landed
    # in one working tree with no gate between them.
    #
    # Two wrong instruments were tried before this one and are recorded so they are not
    # retried. The file's MTIME: teamwork rewrites the file during a run, so a request
    # recorded at 14:43 carried an mtime of 15:22 and the check never fired. The NEWEST
    # recorded stamp vs the newest assignment: the newest stamp is by definition the current
    # run's, so it never predates anything and the check never fired again. What is actually
    # true, and checkable, is the COUNT: more than one request recorded in one tree means an
    # older objective is present and reachable.
    #
    # Reported, never acted on: deleting another harness's state mid-run destroys in-flight
    # work, which is a worse failure than the one being reported.
    detail = {"unreadable": blind_detail} if blind_detail else {}
    req = agents_dir / "ORIGINAL_REQUEST.md"
    stamps: list[float] = []
    if req.is_file():
        try:
            raws = re.findall(r"^##\s+(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})Z?\s*$",
                              req.read_text(errors="replace"), re.M)
        except OSError:
            raws = []
        for raw in raws:
            try:
                stamps.append(datetime.strptime(raw, "%Y-%m-%dT%H:%M:%S")
                              .replace(tzinfo=timezone.utc).timestamp())
            except ValueError:
                continue
    stamps.sort()
    note = (f"{len(out)} teamwork level(s) from {len(assigns)} assignment file(s), "
            f"{len(results)} with results")
    if len(stamps) > 1:
        span = stamps[-1] - stamps[0]
        detail["accumulated_requests"] = {
            "path": str(req), "count": len(stamps),
            "oldest_age_s": round(max(0.0, now - stamps[0]), 1),
            "newest_age_s": round(max(0.0, now - stamps[-1]), 1),
            "span_s": round(span, 1)}
        note += (f" -- ACCUMULATED OBJECTIVES: {req.name} records {len(stamps)} requests "
                 f"spanning {round(span)}s, the oldest {round(max(0.0, now - stamps[0]))}s "
                 f"ago. A previous session's objective is still present in this tree and "
                 f"agents can work it while the manager reports the current one; treat any "
                 f"change outside the stated objective as unrequested until reviewed")
    return source("agy_teamwork", OBSERVED, note, agents=out, detail=detail or None)


def scan_native_marker(root: Path, now: float) -> dict:
    """A run marker is the EXPLICIT signal agy_monitor.py prefers over a silence heuristic.
    Here it is checked against the pid it names, which is the only way a marker can lie."""
    native = root / ".devloop" / "native"
    marker = native / "session.status"
    if not native.exists():
        return source("native_marker", NA,
                      f"no {native} directory: no harness-native session has been hosted from "
                      "this tree. Lanes are covered by devloop_runs regardless")
    if not marker.is_file():
        return source("native_marker", BLIND,
                      f"{native} exists but {marker.name} does not: a native session was hosted "
                      "here and its run marker is missing, so its state is UNKNOWN")
    try:
        doc = _read_json(marker)
        if not isinstance(doc, dict):
            raise json.JSONDecodeError("not an object", "", 0)
    except (OSError, json.JSONDecodeError) as e:
        return source("native_marker", BLIND,
                      f"{marker} could not be read: {type(e).__name__}: {e}")

    state = str(doc.get("state") or "")
    pid = doc.get("pid")
    started = doc.get("started_at")
    age = (now - float(started)) if started else None
    stream = native / "session-events.ndjson"
    stream_idle = None
    m = _mtime(stream)
    if m is not None:
        stream_idle = now - m
    det = {"marker_state": state, "pid": pid, "stream_idle_s": stream_idle}

    if state in ("finished", "failed"):
        return source("native_marker", OBSERVED,
                      f"run marker says {state}: the session ended and said so", detail=det,
                      agents=[agent("native:session", "antigravity", "native_marker", "finished",
                                    where=str(marker), pid=pid,
                                    reason=f"marker state {state}", last_signal_s=stream_idle)])
    if state != "running":
        return source("native_marker", BLIND,
                      f"run marker carries state {state!r}, which is not one of "
                      "running/finished/failed: it cannot be interpreted", detail=det)

    # job.py's predicate, not a bare /proc/<pid> test: a zombie survives SIGKILL in /proc until
    # its parent reaps (measured ~1.2s, longer under load) and must not read as running. The
    # marker carries no start-tick, so the pid-reuse guard is left empty and that is stated.
    alive = None
    if _job is not None and pid:
        try:
            alive = _job._alive(int(pid), "")
        except (TypeError, ValueError, OSError):
            alive = None
    det["pid_alive"] = alive
    det["pid_reuse_guarded"] = False

    if alive is False:
        return source("native_marker", OBSERVED,
                      f"run marker claims running while pid {pid} is GONE", detail=det,
                      agents=[agent("native:session", "antigravity", "native_marker", "stale",
                                    stale=True, basis="marker", where=str(marker), pid=pid,
                                    last_signal_s=stream_idle,
                                    reason=f"marker says running, pid {pid} is not alive -- the "
                                           "session died without updating its own marker")])
    if alive is None:
        return source("native_marker", BLIND,
                      f"run marker claims running and pid {pid!r} could not be checked: the "
                      "claim is UNVERIFIED, not confirmed", detail=det)
    return source("native_marker", OBSERVED,
                  f"run marker says running and pid {pid} is alive"
                  + (f" ({stream_idle:.0f}s since the last event, which is not a fault)"
                     if stream_idle is not None else ""), detail=det,
                  agents=[agent("native:session", "antigravity", "native_marker", "live",
                                where=str(marker), pid=pid, last_signal_s=stream_idle,
                                reason="marker running and pid alive; stream silence is not "
                                       "evidence of death")])


# -------------------------------------------------------------------- source: per-harness CLIs

def _run_bounded(argv: list[str], timeout_s: float, cwd: Path):
    env = {**os.environ, "CI": "1", "GIT_TERMINAL_PROMPT": "0", "NO_COLOR": "1"}
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=timeout_s,
                           cwd=str(cwd), stdin=subprocess.DEVNULL, env=env)
        return p.returncode, (p.stdout or ""), (p.stderr or "")
    except subprocess.TimeoutExpired:
        return None, "", f"timed out after {timeout_s:g}s"
    except OSError as e:
        return None, "", f"could not run: {type(e).__name__}: {e}"


def scan_harness_clis(root: Path, per_timeout_s: float, budget_s: float, deadline: float) -> dict:
    """Optional enrichment. Each harness degrades on its own and NONE of them is required.
    A harness with no scriptable live query is reported as not observable -- which is a
    legitimate answer, and is never silently rendered as 'no agents'."""
    agents, per_harness = [], []
    spent, observed_any = 0.0, False
    for h in HARNESSES:
        rec = {"harness": h["harness"], "bin": h["bin"], "signal": h["signal"],
               "confidence": h["confidence"], "evidence": h["evidence"]}
        path = shutil.which(h["bin"])
        rec["installed"] = bool(path)
        rec["path"] = path
        if not path:
            rec["status"] = NA
            rec["reason"] = f"{h['bin']} is not on PATH here"
            per_harness.append(rec)
            continue
        if not h["live_query"]:
            rec["status"] = NA
            rec["reason"] = ("installed, but exposes no scriptable live-agent query: agents run "
                             "under it are visible ONLY through the dev-loop run directory")
            per_harness.append(rec)
            continue
        left = min(per_timeout_s, budget_s - spent, max(0.0, deadline - _now()))
        if left <= 0.5:
            rec["status"] = BLIND
            rec["reason"] = "skipped: the CLI probe budget for this tick was exhausted"
            per_harness.append(rec)
            continue
        t0 = _now()
        rc, out, err = _run_bounded([path, *h["live_query"]], left, root)
        spent += _now() - t0
        rec["query"] = " ".join([h["bin"], *h["live_query"]])
        rec["rc"] = rc
        if rc is None or rc != 0:
            rec["status"] = BLIND
            rec["reason"] = f"probe failed (rc={rc}): {(err or out).strip()[:200]}"
            per_harness.append(rec)
            continue
        rec["status"] = OBSERVED
        observed_any = True
        found = 0
        if h["parse"] == "json_array":
            try:
                rows = json.loads(out or "[]")
                rows = rows if isinstance(rows, list) else []
            except json.JSONDecodeError as e:
                rec["status"] = BLIND
                rec["reason"] = f"probe returned unparseable JSON: {e}"
                per_harness.append(rec)
                continue
            for i, r in enumerate(rows):
                r = r if isinstance(r, dict) else {}
                sid = str(r.get("sessionId") or r.get("id") or i)
                st = str(r.get("status") or "")
                started = r.get("startedAt")
                age = None
                if isinstance(started, (int, float)) and started > 0:
                    # epoch milliseconds, as measured
                    age = max(0.0, _now() - (float(started) / 1000.0))
                agents.append(agent(f"cli:{h['harness']}:{sid}", h["harness"], "harness_cli",
                                    "live", where=str(r.get("cwd") or ""), pid=r.get("pid"),
                                    last_signal_s=age,
                                    reason=f"the harness reports this session {st or 'active'}. "
                                           "A CLI listing is the harness's own claim; the run "
                                           "directory is the evidence"))
                found += 1
        else:
            found = len([ln for ln in (out or "").splitlines() if ln.strip()])
        rec["rows"] = found
        rec["reason"] = f"probe ok: {found} session(s) listed"
        per_harness.append(rec)

    blind = [r for r in per_harness if r["status"] == BLIND]
    if observed_any:
        st, why = OBSERVED, (f"{sum(1 for r in per_harness if r['status'] == OBSERVED)} harness "
                             f"CLI(s) answered, {len(blind)} failed, "
                             f"{sum(1 for r in per_harness if r['status'] == NA)} have no "
                             "scriptable live-agent query")
    elif blind:
        st, why = BLIND, ("every harness CLI probe that could have answered failed: "
                          + "; ".join(f"{r['harness']}: {r['reason']}" for r in blind[:3]))
    else:
        st, why = NA, ("no installed harness exposes a scriptable live-agent query. This is a "
                       "measured fact about the harnesses, not an observation that the fleet "
                       "is empty")
    return source("harness_cli", st, why, agents=agents, detail={"harnesses": per_harness,
                                                                "cli_seconds": round(spent, 2)})


# ------------------------------------------------------------------------ source: process scan

def scan_processes(root: Path) -> dict:
    """A cheap, harness-agnostic cross-check: which harness binaries hold a live pid right now.
    It CANNOT attribute a process to a dev-loop lane, and it never claims to -- its job is to
    make "a harness is running something this monitor cannot account for" visible instead of
    invisible."""
    proc = Path("/proc")
    if not proc.is_dir():
        return source("process_scan", BLIND,
                      "/proc is not available, so no process liveness can be measured here")
    names = {h["bin"]: h["harness"] for h in HARNESSES}
    counts, seen, errors = {}, 0, 0
    try:
        entries = [p for p in proc.iterdir() if p.name.isdigit()]
    except OSError as e:
        return source("process_scan", BLIND, f"/proc could not be listed: {type(e).__name__}: {e}")
    me = {os.getpid(), os.getppid()}
    for p in entries:
        try:
            raw = (p / "cmdline").read_bytes()
        except OSError:
            errors += 1
            continue
        if not raw or int(p.name) in me:
            continue
        seen += 1
        argv = [a for a in raw.split(b"\0") if a]
        for tok in argv[:2]:
            base = os.path.basename(tok.decode("utf-8", "replace"))
            if base in names:
                counts[names[base]] = counts.get(names[base], 0) + 1
                break
    det = {"pids_read": seen, "pids_unreadable": errors, "by_harness": counts}
    if seen == 0:
        return source("process_scan", BLIND,
                      f"/proc listed {len(entries)} entr(ies) and none could be read "
                      f"({errors} refused): process liveness is NOT being measured", detail=det)
    total = sum(counts.values())
    return source("process_scan", OBSERVED,
                  f"read {seen} process(es); {total} belong to a known harness binary "
                  + (f"({', '.join(f'{k}={v}' for k, v in sorted(counts.items()))})"
                     if counts else "(none)")
                  + ". A live harness process is not by itself a dev-loop lane", detail=det)


# -------------------------------------------------------------- the stale-REFERENCE half

def scan_references(scripts_dir: Path, root: Path, cmd: list[str] | None,
                    timeout_s: float) -> dict:
    """Delegated to the reference scanner, which this monitor does not own and does not
    reimplement. When it is absent the answer is 'unavailable' -- saying 'no stale references'
    without having scanned would be a lie, and it is the exact lie this monitor exists to
    prevent on the agent side."""
    if cmd is None:
        script = scripts_dir / "stale_refs.py"
        if not script.is_file():
            return source("stale_refs", BLIND,
                          f"reference scan unavailable: {script} is not present. NO reference "
                          "scan was performed, so nothing is known about stale references "
                          "either way",
                          detail={"available": False, "scanner": str(script)})
        # `--monitor` is the scanner's own supervisor mode; `--format json` puts the report on
        # stdout and the human summary on stderr. Overridable with --refs-cmd.
        cmd = [sys.executable or "python3", str(script), "--root", str(root),
               "--monitor", "--format", "json"]
    rc, out, err = _run_bounded(cmd, timeout_s, root)
    if rc is None:
        return source("stale_refs", BLIND,
                      f"reference scan unavailable: {' '.join(cmd)} did not complete "
                      f"({err.strip()[:200]})", detail={"available": False})
    doc = None
    try:
        doc = json.loads(out) if out.strip() else None
    except json.JSONDecodeError:
        doc = None
    if not isinstance(doc, (dict, list)):
        return source("stale_refs", BLIND,
                      f"reference scan unavailable: {' '.join(cmd)} exited {rc} without a JSON "
                      f"report on stdout ({(err or out).strip()[:200]})",
                      detail={"available": False, "exit_code": rc})

    # The scanner has its OWN blindness verdict. `could_not_run` means its corpus census failed
    # -- exactly the Empty-Set Pass it was built to refuse -- and it must never be read here as
    # a clean tree just because it emitted a well-formed document saying zero.
    sv = doc.get("verdict") if isinstance(doc, dict) else None
    if sv in ("could_not_run", "blind", "unavailable"):
        why = (doc.get("verdict_reason") if isinstance(doc, dict) else "") or ""
        return source("stale_refs", BLIND,
                      f"reference scan could not run: {why[:300]}. Its own census refused the "
                      "corpus, so ZERO stale references was never measured",
                      detail={"available": False, "scanner_verdict": sv, "exit_code": rc,
                              "report": doc})

    stale = _count_stale_refs(doc)
    if stale < 0:
        return source("stale_refs", BLIND,
                      f"reference scan returned a report this monitor cannot read a stale count "
                      f"out of (schema {doc.get('schema') if isinstance(doc, dict) else 'list'!r})"
                      ". Refusing to read an unparsed report as zero",
                      detail={"available": False, "exit_code": rc, "report": doc})
    return source("stale_refs", OBSERVED,
                  f"reference scan completed (verdict {sv!r}, rc={rc}): {stale} stale "
                  "reference(s)",
                  detail={"available": True, "stale_refs": stale, "exit_code": rc,
                          "scanner_verdict": sv,
                          "scanner_reason": doc.get("verdict_reason")
                          if isinstance(doc, dict) else None,
                          "corpus": doc.get("corpus") if isinstance(doc, dict) else None})


def _count_stale_refs(doc) -> int:
    """Read a count out of the scanner's report without dictating its schema. An unrecognised
    shape yields -1, which is reported as UNREADABLE rather than collapsed to zero -- a monitor
    that cannot parse a report has not measured a clean one."""
    if isinstance(doc, list):
        return len(doc)
    if not isinstance(doc, dict):
        return -1
    counts = doc.get("counts")
    if isinstance(counts, dict) and isinstance(counts.get("stale"), int):
        return counts["stale"]
    for k in ("stale_count", "stale_refs_count", "count"):
        v = doc.get(k)
        if isinstance(v, int):
            return v
    for k in ("stale", "stale_refs", "findings", "results", "refs"):
        v = doc.get(k)
        if isinstance(v, list):
            return len(v)
        if isinstance(v, int):
            return v
    return -1


# ----------------------------------------------------------------------------- the tick itself

def observe(root: Path, *, now: float | None = None, silence_after_s: float = DEFAULT_SILENCE_S,
            max_runs: int = 20, serverd_state: Path | None = None, want_cli: bool = True,
            cli_timeout_s: float = 5.0, cli_budget_s: float = 12.0,
            refs_cmd: list[str] | None = None, refs_timeout_s: float = 10.0,
            deadline_s: float = DEFAULT_DEADLINE_S, count_silence: bool = False,
            harness_filter: str = "*") -> dict:
    """One tick. Enumerates every source, then derives ONE verdict from what was measured."""
    t0 = _now()
    now = t0 if now is None else now
    deadline = t0 + deadline_s
    root = root.resolve()
    state_path = serverd_state or (root / ".devloop" / "serverd" / "state.json")

    sources = [scan_runs(root, now, silence_after_s, max_runs),
               scan_serverd(state_path, now),
               scan_native_marker(root, now),
               scan_agy_teamwork(root, now),
               scan_processes(root)]
    if want_cli:
        sources.append(scan_harness_clis(root, cli_timeout_s, cli_budget_s, deadline))
    else:
        sources.append(source("harness_cli", NA,
                              "per-harness CLI probes disabled with --no-cli: live-agent "
                              "queries were NOT run this tick"))
    refs = scan_references(HERE, root, refs_cmd, min(refs_timeout_s,
                                                    max(1.0, deadline - _now())))
    sources.append(refs)

    records = []
    for s in sources:
        for a in s["agents"]:
            if harness_filter == "*" or fnmatch.fnmatch(a["harness"], harness_filter):
                records.append(a)

    measured_stale = [a for a in records if a["stale"] and a["confidence"] != "weak"]
    weak_stale = [a for a in records if a["stale"] and a["confidence"] == "weak"]
    if count_silence:
        measured_stale, weak_stale = measured_stale + weak_stale, []

    observed = [s for s in sources if s["status"] == OBSERVED]
    blind = [s for s in sources if s["status"] == BLIND]
    na = [s for s in sources if s["status"] == NA]
    enumerating = [s for s in sources if s["source"] in ENUMERATING_SOURCES]
    enum_observed = [s for s in enumerating if s["status"] == OBSERVED]

    undetermined = [a for a in records if a["state"] == "unknown"]
    stale_refs = refs["detail"].get("stale_refs", -1) if refs["status"] == OBSERVED else -1

    # ---- the verdict. Worst axis wins, and `clean` needs complete coverage to be reachable.
    if not enum_observed:
        verdict = "blind"
        reason = ("NO SOURCE COULD ENUMERATE AGENTS this tick. "
                  + "; ".join(f"{s['source']}: {s['reason']}" for s in enumerating)
                  + ". This is not a clean fleet -- it is a monitor that measured nothing")
    else:
        axes = ["clean"]
        bits = []
        if measured_stale:
            axes.append("stale")
            bits.append(f"{len(measured_stale)} agent(s) measured stale ("
                        + ", ".join(sorted({a['basis'] for a in measured_stale})) + ")")
        if stale_refs > 0:
            axes.append("stale")
            bits.append(f"{stale_refs} stale reference(s)")
        if blind:
            axes.append("partial")
            bits.append(f"{len(blind)} source(s) blind: "
                        + ", ".join(s["source"] for s in blind))
        # An agent that was ENUMERATED but whose state could not be DETERMINED is the headline
        # failure in miniature: counting it as "not stale" would let "clean" mean "I found five
        # agents and could not tell you anything about any of them".
        if undetermined:
            axes.append("partial")
            bits.append(f"{len(undetermined)} enumerated agent(s) whose state could NOT be "
                        "determined -- not observed to be healthy, merely not observed")
        if weak_stale:
            axes.append("suspect")
            bits.append(f"{len(weak_stale)} agent(s) SUSPECTED stale on silence alone -- "
                        "unconfirmed, because no pid was available to ask")
        verdict = _worst(*axes)
        if verdict == "clean":
            bits.append(f"all {len(observed)} observing source(s) answered, "
                        f"{len(records)} agent(s) enumerated, none stale")
            if not records:
                bits.append("the fleet is EMPTY -- every source answered and found no agent, "
                            "which is not the same as having failed to look")
        reason = "; ".join(bits)

    out = {
        "schema": SCHEMA,
        "observed_at": _iso(now),
        "observed_at_epoch": round(now, 3),
        "tick_interval_s": TICK_S,
        "root": str(root),
        # The three-valued answer first, because a reader who takes one field must not take a
        # field that can only say "fine" or "not fine".
        "outcome": outcome_of(verdict),
        "verdict": verdict,
        "verdict_reason": reason,
        "coverage": {
            "complete": not blind,
            # The axis `blind` is judged on: a source that can name agents, not merely corroborate.
            "enumerating_sources": len(enumerating),
            "enumerating_observed": len(enum_observed),
            "can_enumerate": bool(enum_observed),
            "sources_total": len(sources),
            "observed": len(observed),
            "blind": len(blind),
            "not_applicable": len(na),
            "blind_sources": [{"source": s["source"], "reason": s["reason"]} for s in blind],
            "sources": [{k: v for k, v in s.items() if k != "agents"} | {"agents": len(s["agents"])}
                        for s in sources],
        },
        "agents": {
            "total": len(records),
            "live": sum(1 for a in records if a["state"] == "live"),
            "finished": sum(1 for a in records if a["state"] == "finished"),
            "stale": len(measured_stale),
            "suspected_stale": len(weak_stale),
            "unknown": sum(1 for a in records if a["state"] == "unknown"),
            "by_harness": _by_harness(records),
            "stale_records": measured_stale,
            "suspected_records": weak_stale,
            "records": records,
        },
        "references": {
            "status": refs["status"],
            "reason": refs["reason"],
            "stale_refs": stale_refs if stale_refs >= 0 else None,
            "scanned": refs["status"] == OBSERVED,
        },
        "harnesses": next((s["detail"].get("harnesses", []) for s in sources
                           if s["source"] == "harness_cli"), []),
        "staleness_policy": {
            "silence_after_s": silence_after_s,
            "count_silence": count_silence,
            "rule": "A live pid is NEVER stale, for any duration of silence. Staleness is "
                    "asserted only from a positive fact (receipt, liveness, run marker, an "
                    "exceeded declared budget, or the supervisor). Silence is used ONLY where "
                    "liveness cannot be measured, and then only as a weak suspicion.",
            "measured_basis": "A real multi-lane run went 128s silent while a gate executed and "
                              "a naive time-based rule called it stalled. The default silence "
                              "threshold is an order of magnitude above that.",
        },
        "duration_s": round(_now() - t0, 3),
    }
    out["headline"] = headline(out)
    return out


def headline(rep: dict) -> str:
    """The whole verdict in ONE line, because a supervisor keeps only _tail(stdout, 400) of a
    monitor run (measured: 5000 chars in, 415 out). Counts come before prose so that truncating
    the prose cannot turn a finding into a silence."""
    c, a, rf = rep["coverage"], rep["agents"], rep["references"]
    refs = ("unavailable" if not rf["scanned"]
            else ("none" if rf["stale_refs"] == 0 else str(rf["stale_refs"])))
    head = (f"[global-monitor] {rep['outcome']} ({rep['verdict']}) "
            f"agents={a['total']} live={a['live']} finished={a['finished']} "
            f"stale={a['stale']} suspected={a['suspected_stale']} unknown={a['unknown']} "
            f"refs={refs} coverage={c['observed']}/{c['sources_total']} blind={c['blind']}")
    room = max(0, 380 - len(head))
    return head + " :: " + rep["verdict_reason"][:room]


def _by_harness(records) -> dict:
    out: dict = {}
    for a in records:
        b = out.setdefault(a["harness"], {"total": 0, "live": 0, "stale": 0, "suspected": 0})
        b["total"] += 1
        if a["state"] == "live":
            b["live"] += 1
        if a["stale"]:
            b["suspected" if a["confidence"] == "weak" else "stale"] += 1
    return out


# ----------------------------------------------------------------------------------- rendering

def render_text(rep: dict) -> str:
    L = [rep["headline"],
         f"  at {rep['observed_at']}  root={rep['root']}  scan={rep['duration_s']}s  "
         f"tick>={rep['tick_interval_s']:g}s",
         f"  why: {rep['verdict_reason']}"]
    c, a = rep["coverage"], rep["agents"]
    L.append(f"  coverage: {c['observed']}/{c['sources_total']} observing, {c['blind']} BLIND, "
             f"{c['not_applicable']} n/a  (complete={c['complete']})")
    for b in c["blind_sources"]:
        L.append(f"    BLIND {b['source']}: {b['reason']}")
    L.append(f"  agents: {a['total']} total  live={a['live']}  finished={a['finished']}  "
             f"STALE={a['stale']}  suspected={a['suspected_stale']}  unknown={a['unknown']}")
    for h, b in sorted(a["by_harness"].items()):
        L.append(f"    {h:<14} total={b['total']} live={b['live']} stale={b['stale']} "
                 f"suspected={b['suspected']}")
    for r in a["stale_records"]:
        L.append(f"    STALE [{r['basis']}] {r['agent_id']} ({r['harness']}): {r['reason']}")
    for r in a["suspected_records"]:
        L.append(f"    SUSPECT [{r['basis']}] {r['agent_id']} ({r['harness']}): {r['reason']}")
    for r in a["records"]:
        if r["state"] == "unknown":
            L.append(f"    UNKNOWN {r['agent_id']} ({r['harness']}): {r['reason']}")
    rf = rep["references"]
    L.append(f"  references: {rf['status']} -- {rf['reason']}")
    return "\n".join(L)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="global_monitor.py",
        description="THE global reporting monitor: all agents, all harnesses, one 30s tick.")
    ap.add_argument("--root", default=".", help="repository root holding .devloop/ (default .)")
    ap.add_argument("--once", action="store_true",
                    help="run exactly one tick and exit. This is the ONLY mode -- the flag is "
                         "accepted so a caller can be explicit, and because this program must "
                         "never grow a loop of its own: the supervisor owns the interval")
    ap.add_argument("--supervised", action="store_true",
                    help="exit 0 for findings (CLEAN and STALE alike) and reserve a non-zero "
                         "exit for verdict `blind`. Pass this in a devloop_serverd registration: "
                         "without it a persistently stale fleet drives the monitor to "
                         "failed_permanent and takes the supervisor down with it")
    ap.add_argument("--report-out", help="also write the JSON report here (tmp+rename)")
    ap.add_argument("--format", choices=("json", "text", "both"), default="json",
                    help="json (machine-readable), text (human summary), or both -- the human "
                         "summary first, then the JSON document")
    ap.add_argument("--quiet", action="store_true",
                    help="with --report-out, print only the one-line verdict to stdout")
    ap.add_argument("--silence-after-s", type=float, default=DEFAULT_SILENCE_S,
                    help=f"weak-suspicion threshold used ONLY where liveness cannot be measured "
                         f"(default {DEFAULT_SILENCE_S:g}s; the measured quiet period is 128s)")
    ap.add_argument("--count-silence", action="store_true",
                    help="promote silence-based suspicions to measured stale (off by default: "
                         "silence is not evidence of death)")
    ap.add_argument("--max-runs", type=int, default=20,
                    help="scan at most this many newest run directories (default 20)")
    ap.add_argument("--serverd-state", help="supervisor state.json "
                                            "(default <root>/.devloop/serverd/state.json)")
    ap.add_argument("--no-cli", action="store_true", help="skip every per-harness CLI probe")
    ap.add_argument("--cli-timeout-s", type=float, default=5.0)
    ap.add_argument("--cli-budget-s", type=float, default=12.0)
    ap.add_argument("--refs-cmd", help="override the reference-scanner command (shell-free; "
                                       "split on spaces)")
    ap.add_argument("--refs-timeout-s", type=float, default=10.0)
    ap.add_argument("--deadline-s", type=float, default=DEFAULT_DEADLINE_S,
                    help=f"self-imposed wall-clock cap, under the supervisor's timeout_s "
                         f"(default {DEFAULT_DEADLINE_S:g}s)")
    ap.add_argument("--harness", default="*", help="report only agents of harnesses matching "
                                                   "this glob (the scan itself is unfiltered)")
    ap.add_argument("--strict", action="store_true",
                    help="exit 4 for any outcome but CLEAN -- one code for a gate that does not "
                         "want to distinguish STALE from UNOBSERVABLE")
    a = ap.parse_args(argv)

    root = Path(a.root)
    if not root.is_dir():
        print(f"global_monitor: --root {root} is not a directory", file=sys.stderr)
        return 1

    rep = observe(root,
                  silence_after_s=a.silence_after_s, max_runs=max(1, a.max_runs),
                  serverd_state=Path(a.serverd_state) if a.serverd_state else None,
                  want_cli=not a.no_cli, cli_timeout_s=a.cli_timeout_s,
                  cli_budget_s=a.cli_budget_s,
                  refs_cmd=a.refs_cmd.split() if a.refs_cmd else None,
                  refs_timeout_s=a.refs_timeout_s, deadline_s=a.deadline_s,
                  count_silence=a.count_silence, harness_filter=a.harness)

    doc = json.dumps(rep, indent=2)
    body = {"json": doc, "text": render_text(rep),
            "both": render_text(rep) + "\n" + doc}[a.format]
    if a.report_out:
        out = Path(a.report_out)
        try:
            out.parent.mkdir(parents=True, exist_ok=True)
            # PID-unique temporary name: two monitors publishing the same path concurrently
            # must not interleave into one half-written file. rename(2) is atomic on one
            # filesystem, so a reader sees the old document or the new one, never a torn one.
            tmp = out.with_name(f"{out.name}.{os.getpid()}.tmp")
            tmp.write_text(doc + "\n", encoding="utf-8")
            tmp.replace(out)
        except OSError as e:
            print(f"global_monitor: could not publish {out}: {type(e).__name__}: {e}",
                  file=sys.stderr)
            try:
                tmp.unlink()
            except (OSError, UnboundLocalError, NameError):
                pass
            return 2
        # The headline goes first WHATEVER the format, so the 400 characters a supervisor keeps
        # carry the verdict and the path to the rest rather than the opening of a JSON document.
        print(rep["headline"] if a.quiet else body)
        # Never after a JSON document: `--format json` keeps stdout parseable as ONE document.
        if a.quiet or a.format != "json":
            print(f"report: {out.resolve()}")
    else:
        print(body)

    if a.strict and rep["outcome"] != CLEAN:
        return 4
    if a.supervised:
        # Findings ride the report, not the exit code. Only an instrument that enumerated
        # nothing escalates -- see the exit-code table at the top of this file.
        return 3 if rep["verdict"] == "blind" else 0
    return OUTCOME_EXIT.get(rep["outcome"], 3)


if __name__ == "__main__":
    sys.exit(main())
