#!/usr/bin/env python3
"""
Controls for devloop_serverd.py, the supervisor whose lifetime has to exceed a turn.

What is being guarded
---------------------
AGENTS.md states the constraint this daemon exists for: native multi-agent lanes "require a
manager whose process outlives a turn" -- a subagent that has not finished when the turn ends
dies with the process. job.py made ONE unit of work survive that; the supervisor is what
watches, restarts and publishes. And the moment a process claims to be watching, a new failure
becomes possible, worse than not watching at all:

    A SUPERVISOR THAT LOOKS ALIVE WHILE SUPERVISING NOTHING.

That is a Skip-as-Pass (SKILL.md 7) wearing a daemon's clothes: an operator sees a state file
saying `supervising`, stops looking, and nothing is running. So the headline control here is
not "does it start workers" -- it is "can it ever report healthy when it is not". Three shapes
of that lie are planted deliberately and must each be caught:

  * a LIVE daemon whose workers are all gone      -> supervising_nothing (exit 2)
  * a DEAD daemon whose file still says supervising -> dead              (exit 3)
  * a live daemon whose loop stopped ticking      -> stale               (exit 4)

The third is the subtle one: the pid is alive, so a naive liveness check passes, and only the
heartbeat age shows the loop is gone.

Every planted state file also sets `"verdict": "supervising"` -- the field the daemon itself
writes. A reader that trusts it passes nothing here. That is the negative control baked into
the suite: patch derive_verdict() to return the file's own claim and these tests go red.

Testing a different build
-------------------------
Set DEVLOOP_SERVERD=/path/to/devloop_serverd.py to run every control against another copy.
That is how the negative control is run: copy the scripts directory to a scratch dir, break
the copy there, and point this suite at it. The tree is never modified to prove a test works.

Run: python3 tests/test_devloop_serverd.py
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SERVERD = Path(os.environ.get("DEVLOOP_SERVERD")
               or (ROOT / "skills" / "dev-loop" / "scripts" / "devloop_serverd.py")).resolve()
SCRIPTS = SERVERD.parent
sys.path.insert(0, str(SCRIPTS))

_spec = importlib.util.spec_from_file_location("devloop_serverd_under_test", SERVERD)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)

import job  # noqa: E402  same directory as the module under test

FAILURES: list[str] = []
_TMP: list[Path] = []
_PROCS: list[subprocess.Popen] = []


def check(name: str, cond, detail: str = "") -> None:
    if cond:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name}{': ' + detail if detail else ''}")
        FAILURES.append(name)


def tmp(prefix: str) -> Path:
    d = Path(tempfile.mkdtemp(prefix=f"serverd-{prefix}-"))
    _TMP.append(d)
    return d


def serverd(*args: str, timeout: int = 90) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SERVERD), *args],
                          capture_output=True, text=True, timeout=timeout)


def write_workers(d: Path, workers: list[dict]) -> Path:
    p = d / "workers.json"
    p.write_text(json.dumps({"schema": "serverd.workers.v1", "workers": workers}, indent=2))
    return p


def state_of(d: Path) -> dict:
    return json.loads((d / ".devloop" / "serverd" / "state.json").read_text())


def live_pid() -> tuple[int, str]:
    """A real process we own, so a planted 'live daemon' state is genuinely live."""
    p = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"])
    _PROCS.append(p)
    return p.pid, mod.pidstart_of(p.pid)


def plant(state_dir: Path, *, pid: int, pidstart: str, heartbeat_age: float,
          workers: dict, daemon_state: str = "running", claim: str = "supervising",
          host: str | None = None) -> Path:
    """Write a state file that CLAIMS health, so the reader's derivation is what is measured."""
    state_dir.mkdir(parents=True, exist_ok=True)
    doc = {
        "schema": "serverd.v1",
        "daemon": {"state": daemon_state, "pid": pid, "pidstart": pidstart,
                   "host": host or os.uname().nodename, "started_at": time.time() - 600,
                   "heartbeat_at": time.time() - heartbeat_age, "tick": 99, "interval_s": 5},
        "workers": workers,
        "verdict": claim,
        "verdict_reason": "planted claim; a reader that repeats this has measured nothing",
    }
    p = state_dir / "state.json"
    p.write_text(json.dumps(doc, indent=2))
    return p


def cleanup() -> None:
    for p in _PROCS:
        try:
            p.kill()
            p.wait(timeout=5)
        except Exception:
            pass
    for d in _TMP:
        jobs = d / ".devloop" / "serverd" / "jobs"
        if jobs.is_dir():
            for j in jobs.iterdir():
                if j.is_dir():
                    try:
                        job.kill(jobs, j.name, "KILL")
                    except Exception:
                        pass
        dj = d / ".devloop" / "serverd" / "daemon"
        if dj.is_dir():
            try:
                job.kill(dj, "serverd", "KILL")
            except Exception:
                pass
        shutil.rmtree(d, ignore_errors=True)


# ------------------------------------------------------------------ THE HEADLINE CONTROL

def test_healthy_is_never_claimed_while_supervising_nothing() -> None:
    """The one that matters: a daemon may not read as healthy when it is supervising nothing.

    Each case plants a state file whose own `verdict` field says `supervising`. The library
    (measure) and the CLI (`status`) are both exercised, because a correct derivation that the
    CLI does not use is still an operator reading `supervising` off a dead daemon.
    """
    print("healthy is never claimed while supervising nothing:")
    pid, pidstart = live_pid()

    # 1. ALIVE, ticking, and nothing left to supervise.
    d = tmp("nothing") / "sd"
    plant(d, pid=pid, pidstart=pidstart, heartbeat_age=0.5, workers={})
    m = mod.measure(d / "state.json")
    check("live daemon with zero workers is supervising_nothing",
          m["verdict"] == "supervising_nothing",
          f"got {m['verdict']!r} -- the state file claimed {m.get('verdict_claimed_by_daemon')!r}")
    check("supervising_nothing does not exit 0", m["exit_code"] != 0, f"exit {m['exit_code']}")
    check("the daemon's own claim is kept for audit, not used",
          m.get("verdict_claimed_by_daemon") == "supervising")
    r = serverd("status", "--state-dir", str(d))
    check("the CLI agrees (supervising_nothing)", '"supervising_nothing"' in r.stdout, r.stdout[:200])
    check("the CLI exits non-zero", r.returncode != 0, f"rc={r.returncode}")

    # 2. ALIVE, ticking, every worker terminal -- the realistic version of case 1.
    d2 = tmp("terminal") / "sd"
    plant(d2, pid=pid, pidstart=pidstart, heartbeat_age=0.5, workers={
        "mgr": {"kind": "manager", "state": "done", "rc": 0},
        "gate": {"kind": "manager", "state": "failed", "rc": 1}})
    m2 = mod.measure(d2 / "state.json")
    check("all-terminal workers is supervising_nothing too",
          m2["verdict"] == "supervising_nothing", f"got {m2['verdict']!r}")

    # 3. DEAD daemon whose file still says it is supervising.
    d3 = tmp("dead") / "sd"
    dead = subprocess.Popen([sys.executable, "-c", "pass"])
    dead.wait()
    plant(d3, pid=dead.pid, pidstart=mod.pidstart_of(dead.pid), heartbeat_age=1.0,
          workers={"mgr": {"kind": "manager", "state": "running"}})
    m3 = mod.measure(d3 / "state.json")
    check("a dead daemon reads dead, not supervising", m3["verdict"] == "dead",
          f"got {m3['verdict']!r} while the file claimed supervising")
    check("dead exits 3", m3["exit_code"] == 3, f"exit {m3['exit_code']}")

    # 4. ALIVE pid, dead loop: the heartbeat is the only witness.
    d4 = tmp("stale") / "sd"
    plant(d4, pid=pid, pidstart=pidstart, heartbeat_age=600.0,
          workers={"mgr": {"kind": "manager", "state": "running"}})
    m4 = mod.measure(d4 / "state.json")
    check("a live pid with a stale heartbeat reads stale", m4["verdict"] == "stale",
          f"got {m4['verdict']!r} -- pid liveness alone cannot see a stopped loop")
    check("stale does not exit 0", m4["exit_code"] != 0)

    # 5. A state file from another host cannot be judged here, and says so.
    d5 = tmp("host") / "sd"
    plant(d5, pid=pid, pidstart=pidstart, heartbeat_age=0.5,
          workers={"mgr": {"kind": "manager", "state": "running"}}, host="some-other-box")
    m5 = mod.measure(d5 / "state.json")
    check("a state file from another host is unverifiable, not healthy",
          m5["verdict"] == "unverifiable", f"got {m5['verdict']!r}")

    # 6. Static guard on the same rule, so a future edit that starts trusting the file is
    #    caught at the source as well as at runtime.
    src = SERVERD.read_text()
    body = src.split("def derive_verdict(", 1)[1].split("\ndef ", 1)[0]
    check("derive_verdict never reads the file's own verdict",
          'get("verdict"' not in body and '["verdict"]' not in body,
          "derive_verdict references the claimed verdict; the claim is not evidence")


# ------------------------------------------------------------------ preconditions

def test_an_empty_registry_is_refused() -> None:
    """Nothing to supervise is not a healthy idle: it is a refusal, out loud, exit 2."""
    print("an empty registry is refused:")
    d = tmp("empty")
    r = serverd("run", "--root", str(d), "--workers-json", '{"workers": []}')
    check("exit 2 (cannot supervise)", r.returncode == 2, f"rc={r.returncode}")
    check("it says so on stderr", "CANNOT SUPERVISE" in r.stderr, r.stderr[:200])
    check("no state file was written", not (d / ".devloop" / "serverd" / "state.json").exists(),
          "a refused start must not leave something a later status reads as a daemon")


def test_a_bad_registry_is_a_config_error_not_a_crash_loop() -> None:
    """A worker whose command does not exist would otherwise spawn-fail-restart forever, which
    looks exactly like supervision. It is rejected before anything starts."""
    print("registry validation:")
    d = tmp("badreg")
    cases = {
        "unknown kind": [{"id": "a", "kind": "wizard", "argv": ["sh", "-c", "true"]}],
        "empty argv": [{"id": "a", "kind": "manager", "argv": []}],
        "missing command": [{"id": "a", "kind": "manager", "argv": ["definitely-not-a-binary-xyz"]}],
        "duplicate id": [{"id": "a", "kind": "manager", "argv": ["sh", "-c", "true"]},
                         {"id": "a", "kind": "manager", "argv": ["sh", "-c", "true"]}],
        "monitor outlasting its interval": [{"id": "m", "kind": "monitor", "argv": ["sh", "-c", "true"],
                                             "interval_s": 2, "timeout_s": 30}],
    }
    for name, workers in cases.items():
        r = serverd("run", "--root", str(d), "--workers-json", json.dumps({"workers": workers}))
        check(f"rejected: {name}", r.returncode == 1, f"rc={r.returncode} {r.stderr[:160]}")
    check("nothing was started by any rejected registry",
          not (d / ".devloop" / "serverd" / "jobs").exists())


def test_dry_run_starts_nothing_and_writes_nothing() -> None:
    """A dry run that left a state file behind would be read as a daemon by the next status."""
    print("dry run:")
    d = tmp("dry")
    w = write_workers(d, [{"id": "mgr", "kind": "manager", "argv": ["sh", "-c", "sleep 5"]}])
    r = serverd("run", "--root", str(d), "--workers", str(w), "--dry-run")
    check("exit 0", r.returncode == 0, r.stderr[:200])
    doc = json.loads(r.stdout)
    check("it reports what it would supervise", doc.get("would_supervise") == 1)
    check("no state file", not (d / ".devloop" / "serverd" / "state.json").exists())
    check("no jobs were spawned", not (d / ".devloop" / "serverd" / "jobs").exists())
    check("status still reports absent afterwards",
          mod.measure(d / ".devloop" / "serverd" / "state.json")["verdict"] == "absent")


def test_absent_state_is_not_success() -> None:
    print("absent and corrupt state:")
    d = tmp("absent")
    m = mod.measure(d / "state.json")
    check("no state file reads absent", m["verdict"] == "absent")
    check("absent is not exit 0", m["exit_code"] != 0)
    sd = tmp("corrupt") / "sd"
    sd.mkdir(parents=True)
    (sd / "state.json").write_text("{not json at all")
    m2 = mod.measure(sd / "state.json")
    check("a corrupt state file reads unreadable", m2["verdict"] == "unreadable")
    check("unreadable is not exit 0", m2["exit_code"] != 0)


# ------------------------------------------------------------------ POSITIVE CONTROL

def test_one_tick_supervises_a_live_manager() -> None:
    """POSITIVE CONTROL: --once must actually start the manager, run the monitor, and publish
    state a separate process can read."""
    print("one tick supervises a live manager:")
    d = tmp("once")
    w = write_workers(d, [
        {"id": "mgr", "kind": "manager", "argv": ["sh", "-c", "sleep 30"], "restart": "never"},
        {"id": "pulse", "kind": "monitor", "argv": ["sh", "-c", "echo alive"],
         "interval_s": 2, "timeout_s": 2}])
    r = serverd("run", "--root", str(d), "--workers", str(w), "--once")
    check("exit 0 while supervising", r.returncode == 0, f"rc={r.returncode} {r.stderr[:300]}")
    out = json.loads(r.stdout)
    check("it reports what it observed", out.get("observed_verdict") == "supervising",
          json.dumps(out)[:300])
    st = state_of(d)
    check("the manager is running", st["workers"]["mgr"]["state"] == "running",
          st["workers"]["mgr"].get("detail", ""))
    check("the manager runs as a detached job, not a child of the tick",
          bool(st["workers"]["mgr"]["job_id"]))
    check("the monitor ran and its exit code was recorded",
          st["workers"]["pulse"]["rc"] == 0 and st["workers"]["pulse"]["runs"] == 1)
    check("the monitor's output was captured", "alive" in st["workers"]["pulse"]["output"])
    check("a heartbeat was published", float(st["daemon"]["heartbeat_at"]) > 0)
    check("the published file is valid JSON for any other process",
          mod.measure(d / ".devloop" / "serverd" / "state.json")["verdict"] in
          ("orphaned", "supervising"))

    # The manager must OUTLIVE the supervisor -- that is the whole point of the file.
    js = job.status(d / ".devloop" / "serverd" / "jobs", st["workers"]["mgr"]["job_id"])
    check("the manager is still running after the supervisor exited", js["state"] == "running",
          f"job state {js['state']} -- a worker that dies with its supervisor solves nothing")
    m = mod.measure(d / ".devloop" / "serverd" / "state.json")
    check("and the exited supervisor reports orphaned, never supervising",
          m["verdict"] == "orphaned", f"got {m['verdict']!r}")


def test_a_failed_manager_is_not_a_clean_finish() -> None:
    """NEGATIVE-SHAPED CONTROL for the run itself: a worker that fails must fail the run."""
    print("a failed manager fails the run:")
    d = tmp("fail")
    w = write_workers(d, [{"id": "boom", "kind": "manager", "argv": ["sh", "-c", "exit 3"],
                           "restart": "never"}])
    r = serverd("run", "--root", str(d), "--workers", str(w), "--interval", "1",
                "--max-ticks", "10")
    check("exit 3", r.returncode == 3, f"rc={r.returncode} {r.stdout[:300]}")
    st = state_of(d)
    check("the failure is recorded with the shell-written rc",
          st["workers"]["boom"]["state"] == "failed" and st["workers"]["boom"]["rc"] == 3,
          json.dumps(st["workers"]["boom"])[:300])
    check("the loop stopped instead of ticking over a dead worker",
          st["daemon"]["stop_reason"] == "no live workers left",
          st["daemon"].get("stop_reason", ""))
    check("the post-mortem verdict is failed, not finished",
          st["verdict"] == "failed", st.get("verdict_reason", ""))


def test_a_flapping_worker_is_capped_and_its_budget_is_not_laundered() -> None:
    """A crash loop is the other way to look busy while achieving nothing. The cap bounds it,
    and restarting the SUPERVISOR must not hand the worker a fresh budget."""
    print("a flapping worker is capped:")
    d = tmp("flap")
    w = write_workers(d, [{"id": "flap", "kind": "manager", "argv": ["sh", "-c", "exit 1"],
                           "restart": "on-failure", "max_restarts": 1}])
    r = serverd("run", "--root", str(d), "--workers", str(w), "--interval", "1",
                "--max-ticks", "12")
    st = state_of(d)
    check("it gives up rather than restarting forever",
          st["workers"]["flap"]["state"] == "failed_permanent",
          json.dumps(st["workers"]["flap"])[:300])
    check("the restart cap was honoured", st["workers"]["flap"]["restarts"] == 1,
          f"restarts={st['workers']['flap']['restarts']} for max_restarts=1")
    check("the fast death is named as a flap", "FLAP" in st["workers"]["flap"]["detail"],
          st["workers"]["flap"]["detail"])
    check("the run fails", r.returncode == 3, f"rc={r.returncode}")

    before = sorted(p.name for p in (d / ".devloop" / "serverd" / "jobs").iterdir())
    serverd("run", "--root", str(d), "--workers", str(w), "--interval", "1", "--max-ticks", "12")
    st2 = state_of(d)
    after = sorted(p.name for p in (d / ".devloop" / "serverd" / "jobs").iterdir())
    check("a supervisor restart does not reset the restart budget",
          st2["workers"]["flap"]["restarts"] == 1,
          f"restarts={st2['workers']['flap']['restarts']} after a restart -- killing the "
          "supervisor would be a way to loop forever")
    check("so the second supervisor makes at most one more attempt",
          len(after) - len(before) <= 1, f"{before} -> {after}")


def test_a_live_manager_is_adopted_not_duplicated() -> None:
    """Managers outlive their supervisor by design, so a restarted supervisor that respawned
    them would run two copies of the same work."""
    print("a live manager is adopted, not duplicated:")
    d = tmp("adopt")
    w = write_workers(d, [{"id": "mgr", "kind": "manager", "argv": ["sh", "-c", "sleep 30"],
                           "restart": "never"}])
    serverd("run", "--root", str(d), "--workers", str(w), "--once")
    first = sorted(p.name for p in (d / ".devloop" / "serverd" / "jobs").iterdir())
    serverd("run", "--root", str(d), "--workers", str(w), "--once")
    st = state_of(d)
    second = sorted(p.name for p in (d / ".devloop" / "serverd" / "jobs").iterdir())
    check("no second job was spawned", first == second, f"{first} -> {second}")
    check("the running job was adopted", st["workers"]["mgr"]["adopted"] is True,
          json.dumps(st["workers"]["mgr"])[:300])
    check("recovery says what it adopted", st["recovery"]["adopted"] == first,
          json.dumps(st["recovery"]))
    check("the run count was not inflated by the adoption",
          st["workers"]["mgr"]["runs"] == 1, f"runs={st['workers']['mgr']['runs']}")


def test_corrupt_previous_state_is_reported_not_papered_over() -> None:
    """Restarting must recover, or SAY it cannot. Silently starting fresh would erase a
    crash-looping worker's history and read as a clean run."""
    print("corrupt previous state is reported:")
    d = tmp("recover")
    sd = d / ".devloop" / "serverd"
    sd.mkdir(parents=True)
    (sd / "state.json").write_text('{"schema": "serverd.v1", "daemon": {trunc')
    w = write_workers(d, [{"id": "mgr", "kind": "manager", "argv": ["sh", "-c", "sleep 20"]}])
    r = serverd("run", "--root", str(d), "--workers", str(w), "--once")
    st = state_of(d)
    check("it starts anyway", r.returncode == 0, f"rc={r.returncode} {r.stderr[:200]}")
    check("but does not claim to have recovered", st["recovery"]["recovered"] is False,
          json.dumps(st["recovery"])[:300])
    check("the reason is recorded in the published state",
          "unreadable" in (st["recovery"].get("error") or ""), json.dumps(st["recovery"])[:300])
    check("and on stderr", "unreadable" in r.stderr, r.stderr[:200])
    check("the corrupt file is kept for the post-mortem",
          any(p.name.startswith("state.json.corrupt.") for p in sd.iterdir()),
          f"{[p.name for p in sd.iterdir()]}")


def test_a_second_supervisor_is_refused() -> None:
    """Two supervisors over one state dir would each publish a partial truth."""
    print("a second supervisor is refused:")
    d = tmp("lock")
    sd = d / ".devloop" / "serverd"
    sd.mkdir(parents=True)
    pid, pidstart = live_pid()
    (sd / "daemon.pid").write_text(json.dumps(
        {"pid": pid, "pidstart": pidstart, "started_at": time.time(),
         "host": os.uname().nodename}))
    w = write_workers(d, [{"id": "mgr", "kind": "manager", "argv": ["sh", "-c", "sleep 5"]}])
    r = serverd("run", "--root", str(d), "--workers", str(w), "--once")
    check("exit 2", r.returncode == 2, f"rc={r.returncode} {r.stderr[:200]}")
    check("it names the live supervisor", "already live" in r.stderr, r.stderr[:200])

    # A STALE lock (the pid is gone) must NOT block a restart -- that would make one crash
    # permanent.
    stale = subprocess.Popen([sys.executable, "-c", "pass"])
    stale.wait()
    (sd / "daemon.pid").write_text(json.dumps(
        {"pid": stale.pid, "pidstart": mod.pidstart_of(stale.pid), "started_at": time.time(),
         "host": os.uname().nodename}))
    r2 = serverd("run", "--root", str(d), "--workers", str(w), "--once")
    check("a stale lock does not block a restart", r2.returncode == 0,
          f"rc={r2.returncode} {r2.stderr[:200]}")


def test_a_failing_monitor_is_recorded_and_capped() -> None:
    print("a failing monitor is recorded and capped:")
    d = tmp("mon")
    w = write_workers(d, [{"id": "watch", "kind": "monitor",
                           "argv": ["sh", "-c", "echo nope >&2; exit 4"],
                           "interval_s": 1, "timeout_s": 1, "max_failures": 2}])
    r = serverd("run", "--root", str(d), "--workers", str(w), "--interval", "1",
                "--max-ticks", "8")
    st = state_of(d)
    rec = st["workers"]["watch"]
    check("the exit code is recorded", rec["rc"] == 4, json.dumps(rec)[:200])
    check("the output is captured", "nope" in rec["output"], rec["output"][:120])
    check("repeated failure is capped, not retried forever",
          rec["state"] == "failed_permanent", rec["state"])
    check("a run whose only monitor gave up does not exit 0", r.returncode != 0,
          f"rc={r.returncode}")


def test_start_detaches_a_daemon_that_outlives_its_caller() -> None:
    """The reason this file exists: the supervisor must not be a child of the caller's turn.

    `start` spawns it through job.py (setsid, stdin closed), so it reparents to init. The
    assertion is on the PARENT PID, because "it is still running right now" would also be true
    of a child that dies the moment the caller's session ends.
    """
    print("start detaches a daemon that outlives its caller:")
    d = tmp("start")
    w = write_workers(d, [
        {"id": "mgr", "kind": "manager", "argv": ["sh", "-c", "sleep 300"], "restart": "never"},
        {"id": "pulse", "kind": "monitor", "argv": ["sh", "-c", "echo up"],
         "interval_s": 1, "timeout_s": 1}])
    r = serverd("start", "--root", str(d), "--workers", str(w), "--interval", "1")
    check("start exits 0", r.returncode == 0, f"rc={r.returncode} {r.stderr[:300]}")
    started = json.loads(r.stdout) if r.stdout.strip().startswith("{") else {}
    check("it confirms a heartbeat rather than a spawn", started.get("started") is True,
          r.stdout[:300])
    pid = started.get("pid")
    check("it reports the daemon pid", bool(pid), r.stdout[:200])
    if pid:
        ppid = int(Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[1])
        check("the daemon is not a child of the caller", ppid != os.getpid(),
              f"ppid={ppid} == this test process: it would die with the caller's session")

    m = mod.measure(d / ".devloop" / "serverd" / "state.json")
    check("status sees a live supervisor", m["verdict"] == "supervising" and m["daemon_alive"],
          f"{m['verdict']} alive={m.get('daemon_alive')}")

    jobs = d / ".devloop" / "serverd" / "jobs"
    wpid = int((jobs / "mgr.0" / "pid").read_text().strip())
    r2 = serverd("stop", "--root", str(d), "--kill-workers")
    stopped = json.loads(r2.stdout) if r2.stdout.strip().startswith("{") else {}
    check("stop exits 0 when everything it was asked to kill died", r2.returncode == 0,
          f"rc={r2.returncode} {r2.stdout[:300]}{r2.stderr[:200]}")
    check("it reports the kill as measured, not assumed",
          all("still_alive" in k for k in (stopped.get("killed_workers") or [{}])),
          r2.stdout[:300])
    check("no worker survived the kill", not stopped.get("workers_that_survived_kill"),
          r2.stdout[:300])
    check("and the worker's session really is empty", job._session_pids(wpid) == [],
          f"still alive: {job._session_pids(wpid)}")
    m2 = mod.measure(d / ".devloop" / "serverd" / "state.json")
    check("the stopped daemon never reads as supervising", m2["verdict"] != "supervising",
          f"got {m2['verdict']!r}")


def test_a_supervisor_crash_is_published_not_swallowed() -> None:
    """If the loop itself throws, the published file must not be left claiming `running`.

    Driven in-process (no broken copy needed): the observation step is made to raise, which is
    the shape of a bug in the supervisor rather than in a worker.
    """
    print("a supervisor crash is published:")
    d = tmp("crash")
    sup = mod.Supervisor(root=d, state_dir=d / ".devloop" / "serverd",
                         workers=[{"id": "mgr", "kind": "manager", "argv": ["sh", "-c", "sleep 20"],
                                   "cwd": str(d), "label": "", "budget_s": 60,
                                   "restart": "never", "max_restarts": 0}],
                         interval_s=1.0)

    def boom(_now):
        raise RuntimeError("planted supervisor bug")

    sup._observe = boom
    handlers = {s: signal.getsignal(s) for s in (signal.SIGTERM, signal.SIGINT)}
    try:
        rc = sup.run(once=True)
    finally:
        for sig, h in handlers.items():
            signal.signal(sig, h)
    st = state_of(d)
    check("the crash exits 3", rc == 3, f"rc={rc}")
    check("the daemon records that it crashed", st["daemon"]["state"] == "crashed",
          st["daemon"].get("state", ""))
    check("the crash reason is published", "planted supervisor bug" in (st["daemon"].get("crash") or ""),
          str(st["daemon"].get("crash")))
    m = mod.measure(d / ".devloop" / "serverd" / "state.json")
    check("and a reader never sees it as supervising", m["verdict"] != "supervising",
          f"got {m['verdict']!r}")


def test_the_state_file_is_the_documented_transport() -> None:
    """The transport claim in the docstring has to be true: atomically written, readable by any
    process, and carrying enough facts for a reader to judge liveness itself."""
    print("the published state is readable and self-describing:")
    d = tmp("transport")
    w = write_workers(d, [{"id": "mgr", "kind": "manager", "argv": ["sh", "-c", "sleep 20"]}])
    serverd("run", "--root", str(d), "--workers", str(w), "--once")
    sd = d / ".devloop" / "serverd"
    st = state_of(d)
    for key in ("pid", "pidstart", "host", "heartbeat_at", "tick", "interval_s"):
        check(f"state carries daemon.{key}", key in st["daemon"],
              "a reader cannot measure liveness or staleness without it")
    check("no temp file is left beside it", not (sd / "state.json.tmp").exists(),
          "tmp+rename must not leave a partial document readers can pick up")
    check("transitions are logged for a post-mortem", (sd / "events.ndjson").is_file())
    lines = [json.loads(l) for l in (sd / "events.ndjson").read_text().splitlines() if l.strip()]
    check("the event log is NDJSON with a start event",
          any(e.get("event") == "start" for e in lines), f"{len(lines)} line(s)")
    check("the resolved registry is published beside the state",
          (sd / "workers.resolved.json").is_file(),
          "a reader must be able to see WHAT was being supervised, not just how it went")


def main() -> int:
    print(f"devloop_serverd under test: {SERVERD}\n")
    try:
        for t in (test_healthy_is_never_claimed_while_supervising_nothing,
                  test_an_empty_registry_is_refused,
                  test_a_bad_registry_is_a_config_error_not_a_crash_loop,
                  test_dry_run_starts_nothing_and_writes_nothing,
                  test_absent_state_is_not_success,
                  test_one_tick_supervises_a_live_manager,
                  test_a_failed_manager_is_not_a_clean_finish,
                  test_a_flapping_worker_is_capped_and_its_budget_is_not_laundered,
                  test_a_live_manager_is_adopted_not_duplicated,
                  test_corrupt_previous_state_is_reported_not_papered_over,
                  test_a_second_supervisor_is_refused,
                  test_a_failing_monitor_is_recorded_and_capped,
                  test_start_detaches_a_daemon_that_outlives_its_caller,
                  test_a_supervisor_crash_is_published_not_swallowed,
                  test_the_state_file_is_the_documented_transport):
            t()
    finally:
        cleanup()
    print()
    if FAILURES:
        print(f"FAILED ({len(FAILURES)}): {', '.join(FAILURES)}")
        return 1
    print("all devloop_serverd controls passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
