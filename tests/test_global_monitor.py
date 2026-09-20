#!/usr/bin/env python3
"""
Controls for global_monitor.py -- THE global reporting monitor.

What this monitor is for
------------------------
One monitor, 30-second tick, all agents from all harnesses, running under whichever harness
spawned as the manager. Its subject is staleness: agents that went stale, references that went
stale. So these controls are almost entirely about the monitor NOT reporting calm.

Every control here is TWO-SIDED (SKILL.md 6): a positive case, and a negative case proving the
same check CAN fail. A test that only ever sees the healthy path is a test that would pass
against a monitor hardwired to print "clean".

The three properties it must never break
  1. "clean" and "could not observe" are DIFFERENT VERDICTS. A missing run directory is `blind`
     with a non-zero exit, never "0 stale agents, all healthy".
  2. `clean` is unreachable while any source is blind, whatever the agent counts say.
  3. A LIVE PID IS NEVER STALE, for any duration of silence. agy_monitor.py measured a real
     multi-lane run going 128 SECONDS silent while a gate executed, and a naive time-based rule
     called that healthy manager stalled. Silence may only ever produce a weak SUSPICION, and
     only where liveness cannot be measured at all.

Run: python3 tests/test_global_monitor.py
"""
from __future__ import annotations

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
SCRIPTS = ROOT / "skills" / "dev-loop" / "scripts"
MON = SCRIPTS / "global_monitor.py"
sys.path.insert(0, str(SCRIPTS))

import global_monitor as gm     # noqa: E402  for the unit-level invariants
import job                      # noqa: E402  real jobs, so liveness is measured not mocked

FAILURES: list[str] = []


def first(seq, default=None):
    """Index defensively. A control file that raises IndexError on the very failure it exists to
    catch reports ONE crash instead of ninety results -- and a suite that cannot survive its own
    negative case is not a suite, it is a tripwire. (Caught by mutation probe B.)"""
    try:
        return seq[0]
    except (IndexError, TypeError, KeyError):
        return {} if default is None else default


def check(name: str, cond: bool, detail: str = "") -> None:
    print(f"  {'ok  ' if cond else 'FAIL'}  {name}" + (f"   [{detail}]" if detail and not cond
                                                       else ""))
    if not cond:
        FAILURES.append(name)


def run_monitor(root: Path, *extra: str, timeout: int = 90):
    """Drive the monitor as a subprocess, the way a supervisor does."""
    argv = [sys.executable, str(MON), "--root", str(root), "--format", "json", *extra]
    p = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    try:
        return p.returncode, json.loads(p.stdout), p.stderr
    except json.JSONDecodeError:
        return p.returncode, {}, (p.stderr + p.stdout)


# `/bin/false` stands in for a reference scanner that cannot run. `--no-cli` keeps the harness
# probes out of every case that is not about them, so no test depends on which CLIs are present.
NO_REFS = ("--refs-cmd", "/bin/false")
BASE = ("--no-cli", *NO_REFS)


def _refs_stub(tmp: Path, stale: int, verdict: str = "clean") -> tuple[str, ...]:
    """A reference scanner that reports a known count, so the refs axis can be driven both ways."""
    s = tmp / f"refs_{stale}_{verdict}.py"
    s.write_text("import json,sys\n"
                 f"print(json.dumps({{'schema':'devloop.stale_refs/1','verdict':{verdict!r},"
                 f"'counts':{{'stale':{stale}}}}}))\n")
    return ("--refs-cmd", f"{sys.executable} {s}")


def _wait_running(jobs_root: Path, jid: str, timeout_s: float = 20.0):
    """job.spawn() returns as soon as it has detached; the WRAPPER writes pid/pidstart. Poll
    until the job is genuinely running, so a test never races its own fixture."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if job.status(jobs_root, jid)["state"] == "running":
            try:
                return int((jobs_root / jid / "pid").read_text().strip())
            except (OSError, ValueError):
                pass
        time.sleep(0.2)
    return None


def make_run(root: Path, run_id: str, lane_id: str, harness: str = "claude-code") -> Path:
    """A minimal but REAL run directory, in the layout references/run-directory.md specifies."""
    run = root / ".devloop" / run_id
    (run / "jobs").mkdir(parents=True, exist_ok=True)
    (run / f"lane-{lane_id}.json").write_text(json.dumps(
        {"id": lane_id, "objective": "fixture", "owned_paths": ["x/**"],
         "worker": {"harness": harness, "timeout_s": 600}}))
    return run


# ---------------------------------------------------------------------------------- the tests

def test_blind_is_not_clean() -> None:
    """THE headline property: observing nothing must not read like a clean fleet."""
    print("\n-- a tree with no run directory is BLIND, not clean")
    with tempfile.TemporaryDirectory() as td:
        empty = Path(td) / "empty"
        empty.mkdir()
        rc, rep, _ = run_monitor(empty, *BASE)
        check("verdict is blind", rep.get("verdict") == "blind", str(rep.get("verdict")))
        check("exit 3, so a supervisor escalates it", rc == 3, f"rc={rc}")
        check("it is NOT clean", rep.get("verdict") != "clean")
        check("the reason names the mistake a reader would otherwise make",
              "not a clean fleet" in rep.get("verdict_reason", "").lower()
              or "measured nothing" in rep.get("verdict_reason", "").lower(),
              rep.get("verdict_reason", "")[:120])
        check("the blind source is named, not just counted",
              any(b["source"] == "devloop_runs" for b in rep["coverage"]["blind_sources"]),
              str(rep["coverage"]["blind_sources"]))
        check("zero agents is reported alongside blind, never instead of it",
              rep["agents"]["total"] == 0 and rep["verdict"] == "blind")

        # NEGATIVE CONTROL: the same monitor on a READABLE .devloop with no runs must NOT be
        # blind -- otherwise `blind` is a constant and proves nothing.
        ok = Path(td) / "readable"
        (ok / ".devloop").mkdir(parents=True)
        rc2, rep2, _ = run_monitor(ok, "--no-cli", *_refs_stub(Path(td), 0))
        check("a readable, empty .devloop is NOT blind", rep2.get("verdict") != "blind",
              str(rep2.get("verdict")))
        check("...it is clean", rep2.get("verdict") == "clean", str(rep2.get("verdict")))
        check("...and exits 0", rc2 == 0, f"rc={rc2}")
        check("...and says the fleet is empty rather than implying it",
              "empty" in rep2.get("verdict_reason", "").lower(),
              rep2.get("verdict_reason", "")[:120])


def test_clean_needs_complete_coverage() -> None:
    """A blind source caps the verdict, whatever the agent counts say."""
    print("\n-- one blind source makes `clean` unreachable")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / ".devloop").mkdir()
        rc, rep, _ = run_monitor(root, *BASE)       # refs scanner cannot run
        check("verdict is partial, not clean", rep.get("verdict") == "partial",
              str(rep.get("verdict")))
        check("coverage.complete is False", rep["coverage"]["complete"] is False)
        check("the reference axis says unavailable, NOT zero",
              rep["references"]["scanned"] is False
              and rep["references"]["stale_refs"] is None,
              json.dumps(rep["references"])[:160])
        check("--strict turns it non-zero for a gate",
              run_monitor(root, *BASE, "--strict")[0] == 4)

        # NEGATIVE CONTROL: give the same tree a working scanner and `clean` must appear.
        rc2, rep2, _ = run_monitor(root, "--no-cli", *_refs_stub(root, 0))
        check("with every source answering it IS clean", rep2.get("verdict") == "clean",
              str(rep2.get("verdict")))
        check("...coverage.complete is True", rep2["coverage"]["complete"] is True)
        check("...and --strict now exits 0",
              run_monitor(root, "--no-cli", *_refs_stub(root, 0), "--strict")[0] == 0)


def test_a_live_pid_is_never_stale() -> None:
    """The 128-second rule, as a regression test. Measured: a healthy manager went 128s silent
    while a gate ran, and a time-based heuristic called it stalled."""
    print("\n-- a live process is not stale, however long it has been silent")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        run = make_run(root, "run-20260101-000000", "alive")
        job.spawn(run / "jobs", "alive", ["sleep", "120"], root, budget_s=3600, label="alive")
        try:
            # Wait for the job to be genuinely RUNNING rather than sleeping a fixed 2s. Measured:
            # under the load of a full validate.sh pass the detached wrapper had not yet written
            # pid/pidstart after 2s, job.status read `absent`, the lane fell through to the
            # silence branch and this control failed -- a flaky control that accuses a healthy
            # agent is the very bug this file exists to catch.
            started = _wait_running(run / "jobs", "alive")
            check("the fixture agent really is running", started is not None, "job never started")
            time.sleep(1.5)                     # ...and then let it go quiet past the threshold
            rc, rep, err = run_monitor(root, *BASE, "--silence-after-s", "1")
            recs = rep.get("agents", {}).get("records", [])
            lane = next((r for r in recs if r["agent_id"].endswith(":alive")), None)
            check("the lane was found", lane is not None, err[:200])
            if lane:
                check("it is reported LIVE", lane["state"] == "live", str(lane))
                check("it is NOT stale", lane["stale"] is False)
                check("the reason cites the measured finding",
                      "128s" in lane["reason"] or "not evidence of death" in lane["reason"],
                      lane["reason"][:140])
            check("no agent is counted stale", rep["agents"]["stale"] == 0)
            check("none is even suspected", rep["agents"]["suspected_stale"] == 0,
                  json.dumps(rep["agents"]["suspected_records"])[:200])

            # NEGATIVE CONTROL: kill the wrapper so no receipt is written. Same directory, same
            # silence threshold -- only liveness changed, and the verdict must flip.
            pid = int((run / "jobs" / "alive" / "pid").read_text().strip())
            os.kill(pid, signal.SIGKILL)
            deadline = time.time() + 15
            while time.time() < deadline:
                if job.status(run / "jobs", "alive")["state"] == "lost":
                    break
                time.sleep(0.3)
            st = job.status(run / "jobs", "alive")["state"]
            check("the job is now `lost` (no receipt, pid gone)", st == "lost", st)
            rc2, rep2, _ = run_monitor(root, *BASE, "--silence-after-s", "1")
            lane2 = next((r for r in rep2["agents"]["records"]
                          if r["agent_id"].endswith(":alive")), None)
            check("the dead lane IS stale", lane2 and lane2["stale"] is True, str(lane2))
            check("...on measured liveness, not on silence",
                  lane2 and lane2["basis"] == "liveness"
                  and lane2["confidence"] == "measured", str(lane2))
            check("...and the run-level verdict is stale", rep2["verdict"] == "stale",
                  rep2["verdict"])
        finally:
            for p in (run / "jobs" / "alive" / "pid",):
                try:
                    os.kill(int(p.read_text().strip()), signal.SIGKILL)
                except (OSError, ValueError):
                    pass


def test_receipt_outranks_everything() -> None:
    """The shell-written receipt is the completion artefact; 125 means never started."""
    print("\n-- worker-<id>.exit is read, and its vocabulary respected")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        run = make_run(root, "run-20260101-000001", "done", harness="antigravity")
        (run / "worker-done.exit").write_text("0\n")
        make_run(root, "run-20260101-000001", "never")
        (run / "worker-never.exit").write_text("125\n")
        make_run(root, "run-20260101-000001", "killed")
        (run / "worker-killed.exit").write_text("124\n")
        rc, rep, err = run_monitor(root, *BASE)
        by = {r["agent_id"].rsplit(":", 1)[1]: r for r in rep["agents"]["records"]}
        check("all three lanes enumerated", len(by) == 3, str(list(by)))
        by = {k: by.get(k, {}) for k in ("done", "never", "killed")}
        check("receipt 0 -> finished, not stale",
              by["done"].get("state") == "finished" and by["done"].get("stale") is False,
              str(by["done"]))
        check("receipt 125 -> STALE (dispatched and gone)",
              by["never"].get("stale") is True and by["never"].get("basis") == "receipt",
              str(by["never"]))
        check("receipt 124 -> finished: a timeout terminated, it did not go stale",
              by["killed"].get("state") == "finished" and by["killed"].get("stale") is False,
              str(by["killed"]))
        check("the harness comes from the lane file, not from the monitor's host",
              by["done"].get("harness") == "antigravity", str(by["done"].get("harness")))
        check("by_harness splits the fleet", set(rep["agents"]["by_harness"]) ==
              {"antigravity", "claude-code"}, str(rep["agents"]["by_harness"]))


def test_silence_is_only_ever_a_suspicion() -> None:
    """Where liveness cannot be measured, silence gives `suspect` -- never `stale`."""
    print("\n-- silence produces a weak suspicion, and a distinct verdict")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        run = make_run(root, "run-20260101-000002", "quiet")
        old = time.time() - 4000
        for p in (run / "lane-quiet.json",):
            os.utime(p, (old, old))
        # A WORKING reference scanner, so the only finding in play is the suspicion itself --
        # with a blind refs axis the verdict would be `partial` and this would prove nothing
        # about `suspect`.
        BASE = ("--no-cli", *_refs_stub(root, 0))

        rc, rep, _ = run_monitor(root, *BASE, "--silence-after-s", "900")
        lane = first(rep["agents"]["records"])
        check("state is `suspected`, not `stale`", lane["state"] == "suspected", str(lane))
        check("basis is silence and confidence is WEAK",
              lane["basis"] == "silence" and lane["confidence"] == "weak", str(lane))
        check("it is counted as suspected, not as stale",
              rep["agents"]["stale"] == 0 and rep["agents"]["suspected_stale"] == 1,
              json.dumps(rep["agents"]["by_harness"]))
        check("the verdict is `suspect`, a value of its own",
              rep["verdict"] == "suspect", rep["verdict"])
        check("the reason says it is unconfirmed",
              "unconfirmed" in rep["verdict_reason"].lower()
              or "suspected" in rep["verdict_reason"].lower(),
              rep["verdict_reason"][:120])
        check("a suspicion is STALE at the top level, but never counted as measured-stale",
              rep["outcome"] == "STALE" and rep["agents"]["stale"] == 0,
              f"{rep['outcome']} stale={rep['agents']['stale']}")
        check("...and the headline shows both, so truncation cannot overclaim",
              "stale=0" in rep["headline"] and "suspected=1" in rep["headline"],
              rep["headline"][:160])

        # NEGATIVE CONTROL A: under the threshold nothing is suspected at all.
        rc2, rep2, _ = run_monitor(root, *BASE, "--silence-after-s", "100000")
        lane2 = first(rep2["agents"]["records"])
        check("under the threshold it is `unknown`, not stale and not healthy",
              lane2.get("state") == "unknown" and rep2["agents"]["suspected_stale"] == 0,
              str(lane2.get("state")))
        check("...and `unknown` still does not read as clean",
              "Undetermined" in lane2.get("reason", ""), lane2.get("reason", "")[:120])

        # NEGATIVE CONTROL B: the caller may promote suspicion, and then it counts.
        rc3, rep3, _ = run_monitor(root, *BASE, "--silence-after-s", "900", "--count-silence")
        check("--count-silence promotes it to stale",
              rep3["agents"]["stale"] == 1 and rep3["verdict"] == "stale",
              f"{rep3['agents']['stale']} {rep3['verdict']}")


def test_reference_scan_absence_is_not_zero() -> None:
    """'No stale references' is a lie when nothing was scanned."""
    print("\n-- the reference axis degrades honestly")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / ".devloop").mkdir()

        # 1. the scanner cannot run at all
        _, rep, _ = run_monitor(root, *BASE)
        check("status is blind", rep["references"]["status"] == "blind",
              rep["references"]["status"])
        check("scanned is False and the count is None, never 0",
              rep["references"]["scanned"] is False
              and rep["references"]["stale_refs"] is None, json.dumps(rep["references"])[:160])

        # 2. the scanner runs and reports its OWN blindness -- an Empty-Set Pass it refused.
        blind = root / "blind_refs.py"
        blind.write_text("import json;print(json.dumps({'schema':'devloop.stale_refs/1',"
                         "'verdict':'could_not_run','verdict_reason':'corpus census failed',"
                         "'counts':{'stale':0}}))\n")
        _, rep2, _ = run_monitor(root, "--no-cli", "--refs-cmd", f"{sys.executable} {blind}")
        check("a scanner reporting could_not_run is read as blind",
              rep2["references"]["status"] == "blind", rep2["references"]["status"])
        check("...its counts.stale=0 is NOT adopted as a clean answer",
              rep2["references"]["stale_refs"] is None, str(rep2["references"]["stale_refs"]))
        check("...and the verdict cannot be clean", rep2["verdict"] != "clean", rep2["verdict"])

        # 3. an unparseable report is blind too, not zero.
        junk = root / "junk_refs.py"
        junk.write_text("print('not json')\n")
        _, rep3, _ = run_monitor(root, "--no-cli", "--refs-cmd", f"{sys.executable} {junk}")
        check("an unparseable report is blind, not zero",
              rep3["references"]["status"] == "blind"
              and rep3["references"]["stale_refs"] is None, json.dumps(rep3["references"])[:160])

        # NEGATIVE CONTROL: a scanner that really answers must be believed, both ways.
        _, rep4, _ = run_monitor(root, "--no-cli", *_refs_stub(root, 0))
        check("a real 0 is recorded as scanned",
              rep4["references"]["scanned"] is True
              and rep4["references"]["stale_refs"] == 0, json.dumps(rep4["references"])[:160])
        _, rep5, _ = run_monitor(root, "--no-cli", *_refs_stub(root, 7, "regressed"))
        check("a real non-zero drives the verdict to stale",
              rep5["references"]["stale_refs"] == 7 and rep5["verdict"] == "stale",
              f"{rep5['references']['stale_refs']} {rep5['verdict']}")
        check("...and stale references exit 5, the STALE code",
              run_monitor(root, "--no-cli", *_refs_stub(root, 7, "regressed"))[0] == 5)
        check("--strict collapses any non-CLEAN outcome to one gate code",
              run_monitor(root, "--no-cli", *_refs_stub(root, 7, "regressed"), "--strict")[0] == 4)


def test_run_marker_is_checked_against_its_pid() -> None:
    """An explicit run marker is preferred over silence -- and verified, because the only way a
    marker lies is by outliving the process it names."""
    print("\n-- a run marker that claims `running` is checked against its pid")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        native = root / ".devloop" / "native"
        native.mkdir(parents=True)
        (native / "session.status").write_text(json.dumps(
            {"state": "running", "pid": 999999, "started_at": int(time.time()) - 10}))
        _, rep, _ = run_monitor(root, *BASE)
        rec = next((r for r in rep["agents"]["records"] if r["source"] == "native_marker"), None)
        check("the marker's claim is not taken at face value",
              rec and rec["stale"] is True and rec["basis"] == "marker", str(rec))

        # NEGATIVE CONTROL: point the marker at a pid that IS alive; it must read live.
        p = subprocess.Popen(["sleep", "60"])
        try:
            (native / "session.status").write_text(json.dumps(
                {"state": "running", "pid": p.pid, "started_at": int(time.time()) - 10}))
            _, rep2, _ = run_monitor(root, *BASE)
            rec2 = next((r for r in rep2["agents"]["records"]
                         if r["source"] == "native_marker"), None)
            check("a marker whose pid is alive reads live",
                  rec2 and rec2["state"] == "live" and rec2["stale"] is False, str(rec2))
        finally:
            p.kill()
            p.wait()

        # A native/ directory whose marker vanished is blind, never "finished".
        (native / "session.status").unlink()
        _, rep3, _ = run_monitor(root, *BASE)
        src = next(s for s in rep3["coverage"]["sources"] if s["source"] == "native_marker")
        check("a missing marker beside an existing native/ dir is blind",
              src["status"] == "blind", src["status"])


def test_stale_cannot_be_asserted_without_a_basis() -> None:
    """The invariant behind every record: a staleness claim names the fact that proved it."""
    print("\n-- a stale record without a basis is refused at construction")
    ok = True
    try:
        gm.agent("x", "h", "s", "stale", stale=True)
        ok = False
    except ValueError:
        pass
    check("agent(stale=True) with no basis raises", ok)
    r = gm.agent("x", "h", "s", "stale", stale=True, basis="liveness")
    check("with a basis it is accepted", r["stale"] is True and r["basis"] == "liveness")
    check("a non-stale record carries confidence n/a, not a false 'measured'",
          gm.agent("y", "h", "s", "live")["confidence"] == "n/a")

    # NEGATIVE CONTROL for the severity lattice: it must not silently prefer the mild value.
    check("_worst picks the worse of two", gm._worst("clean", "stale") == "stale")
    check("_worst treats an unknown verdict as blind, not as clean",
          gm._worst("clean", "not-a-verdict") == "blind")
    check("blind outranks stale", gm._worst("stale", "blind") == "blind")


def test_report_is_published_atomically_and_matches() -> None:
    print("\n-- the published report is the report")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / ".devloop").mkdir()
        out = root / "nested" / "global-monitor.json"
        p = subprocess.run([sys.executable, str(MON), "--root", str(root), "--no-cli",
                            *_refs_stub(root, 0), "--once",
                            "--report-out", str(out), "--quiet"],
                           capture_output=True, text=True, timeout=90)
        check("it exits 0 having published a CLEAN tick", p.returncode == 0, p.stderr[-200:])
        check("the parent directory was created", out.is_file())
        doc = json.loads(out.read_text())
        check("the file carries the schema", doc.get("schema") == gm.SCHEMA)
        check("--quiet prints the headline, not the document",
              doc["outcome"] in p.stdout and doc["verdict"] in p.stdout
              and len(p.stdout) < 900, p.stdout[:160])
        check("the headline fits the 400 chars a supervisor keeps",
              len(doc["headline"]) <= 400, str(len(doc["headline"])))
        check("--quiet still names the file holding the rest",
              str(out.resolve()) in p.stdout, p.stdout[:200])
        check("--once is accepted", "unrecognized" not in p.stderr, p.stderr[-160:])
        check("no .tmp file is left behind", not list(out.parent.glob("*.tmp")),
              str(list(out.parent.glob('*.tmp'))))
        check("the tick rate it advertises is 30s", doc["tick_interval_s"] == 30.0,
              str(doc.get("tick_interval_s")))


def test_harness_table_claims_only_what_was_measured() -> None:
    """The monitor reports its own reach. An unverified entry must say so rather than guess."""
    print("\n-- per-harness observability is declared, with confidence")
    for h in gm.HARNESSES:
        check(f"{h['harness']}: confidence is a known value",
              h["confidence"] in ("verified", "likely", "unverified"), h["confidence"])
        check(f"{h['harness']}: carries evidence", bool(h["evidence"].strip()))
        check(f"{h['harness']}: a live query implies a parser",
              (h["live_query"] is None) == (h["parse"] is None), str(h))
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / ".devloop").mkdir()
        _, rep, _ = run_monitor(root, *NO_REFS, "--cli-budget-s", "8")
        tbl = {h["harness"]: h for h in rep["harnesses"]}
        check("the report carries the table", len(tbl) == len(gm.HARNESSES), str(list(tbl)))
        for h in tbl.values():
            check(f"{h['harness']}: status is a source status",
                  h["status"] in (gm.OBSERVED, gm.BLIND, gm.NA), h.get("status", ""))
            check(f"{h['harness']}: a harness with no query says so, rather than reporting 0",
                  h["status"] != gm.OBSERVED or "query" in h, str(h)[:140])

        # NEGATIVE CONTROL: --no-cli must not masquerade as a completed probe.
        _, rep2, _ = run_monitor(root, "--no-cli", *NO_REFS)
        src = next(s for s in rep2["coverage"]["sources"] if s["source"] == "harness_cli")
        check("--no-cli reports NOT RUN rather than a clean probe",
              src["status"] == gm.NA and "NOT" in src["reason"], src["reason"][:120])


def test_it_is_a_conforming_serverd_monitor_worker() -> None:
    """It must register and run under devloop_serverd.py as a `monitor` at interval 30 -- the
    contract it claims to conform to, exercised rather than asserted."""
    print("\n-- it runs as a devloop_serverd `monitor` worker at interval_s=30")
    serverd = SCRIPTS / "devloop_serverd.py"
    if not serverd.is_file():
        check("devloop_serverd.py present", False, "supervisor missing")
        return
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / ".devloop").mkdir()
        state = root / "state"
        reg = root / "workers.json"
        reg.write_text(json.dumps({"schema": "serverd.workers.v1", "workers": [
            {"id": "global", "kind": "monitor",
             "argv": [sys.executable, str(MON), "--once", "--supervised", "--quiet",
                      "--root", str(root), "--no-cli", "--refs-cmd", "/bin/false",
                      "--report-out", str(root / "global-monitor.json")],
             "cwd": str(root), "interval_s": 30, "timeout_s": 25, "max_failures": 5}]}))
        p = subprocess.run([sys.executable, str(serverd), "run", "--root", str(root),
                            "--state-dir", str(state), "--workers", str(reg),
                            "--interval", "1", "--max-ticks", "2"],
                           capture_output=True, text=True, timeout=120)
        doc = json.loads((state / "state.json").read_text())
        w = (doc.get("workers") or {}).get("global") or {}
        check("the registry was accepted", w.get("kind") == "monitor", p.stderr[-300:])
        check("the worker ran", (w.get("runs") or 0) >= 1, json.dumps(w)[:200])
        check("it exited 0, so the supervisor records `ok`",
              w.get("rc") == 0 and w.get("state") == "ok", json.dumps(w)[:200])
        check("it finished well inside timeout_s=25",
              (w.get("duration_s") or 99) < 25, str(w.get("duration_s")))
        check("the report was published from inside the tick",
              (root / "global-monitor.json").is_file())

        # NEGATIVE CONTROL for --supervised: the SAME tick without it must exit non-zero, so
        # the flag is load-bearing rather than decorative. This tree's reference scanner cannot
        # run, so the outcome is UNOBSERVABLE -- which a supervisor would count as a failure and
        # eventually escalate to failed_permanent, taking the supervisor with it.
        bare = subprocess.run([sys.executable, str(MON), "--once", "--quiet", "--root",
                               str(root), "--no-cli", "--refs-cmd", "/bin/false",
                               "--report-out", str(root / "bare.json")],
                              capture_output=True, text=True, timeout=90)
        check("without --supervised the same tick exits non-zero", bare.returncode != 0,
              f"rc={bare.returncode}")
        check("...and --supervised is what makes the supervised run record `ok`",
              w.get("rc") == 0 and bare.returncode != 0,
              f"supervised={w.get('rc')} bare={bare.returncode}")

        # NEGATIVE CONTROL: timeout_s > interval_s must be REFUSED, so the 30s tick is a real
        # constraint rather than a comment.
        bad = root / "bad.json"
        bad.write_text(json.dumps({"schema": "serverd.workers.v1", "workers": [
            {"id": "global", "kind": "monitor", "argv": [sys.executable, str(MON)],
             "cwd": str(root), "interval_s": 30, "timeout_s": 45}]}))
        q = subprocess.run([sys.executable, str(serverd), "run", "--root", str(root),
                            "--state-dir", str(root / "s2"), "--workers", str(bad),
                            "--once"], capture_output=True, text=True, timeout=60)
        check("a monitor allowed to outlast its own interval is refused",
              q.returncode != 0 and "timeout_s" in (q.stdout + q.stderr),
              (q.stdout + q.stderr)[-200:])


def test_a_blind_supervisor_state_is_not_silence() -> None:
    """A corrupt supervisor state must be blind, not an absent supervisor."""
    print("\n-- supervisor state: absent, readable and corrupt are three different answers")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / ".devloop").mkdir()
        sd = root / ".devloop" / "serverd"
        sd.mkdir()

        _, rep, _ = run_monitor(root, *BASE)        # absent
        src = next(s for s in rep["coverage"]["sources"] if s["source"] == "serverd")
        check("an absent supervisor state is n/a and claims no worker",
              src["status"] == gm.NA and src["agents"] == 0, str(src)[:160])

        (sd / "state.json").write_text("{ this is not json")
        _, rep2, _ = run_monitor(root, *BASE)
        src2 = next(s for s in rep2["coverage"]["sources"] if s["source"] == "serverd")
        check("a corrupt supervisor state is BLIND", src2["status"] == gm.BLIND,
              str(src2)[:160])
        check("...and caps the verdict below clean", rep2["verdict"] != "clean", rep2["verdict"])


# ----------------------------------------------------------- the five cases the brief names
# The four above already attack these properties from the inside. These five exist under the
# names the brief uses, so that a reader looking for "is UNOBSERVABLE actually tested?" finds a
# case called that rather than having to infer it from `test_blind_is_not_clean`.

def test_a_stale_agent_is_detected() -> None:
    """POSITIVE CONTROL: a genuinely stale agent is found, named, and drives the outcome."""
    print("\n-- a stale agent IS detected")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        run = make_run(root, "run-20260101-000010", "gone", harness="codex")
        (run / "worker-gone.exit").write_text("125\n")        # dispatched and never returned
        rc, rep, err = run_monitor(root, "--no-cli", *_refs_stub(root, 0))
        check("outcome is STALE", rep.get("outcome") == "STALE", str(rep.get("outcome")))
        check("exit 5, the STALE code", rc == 5, f"rc={rc}")
        check("exactly one agent is counted stale", rep["agents"]["stale"] == 1,
              json.dumps(rep["agents"])[:200])
        rec = first(rep["agents"]["stale_records"])
        check("the stale agent is LISTED, not just counted",
              rec.get("agent_id", "").endswith(":gone"), str(rec))
        check("it names the basis that proved it", rec.get("basis") == "receipt", str(rec))
        check("it carries the harness it ran under", rec.get("harness") == "codex",
              str(rec.get("harness")))
        check("it points at the evidence a human should open",
              rec.get("where", "").endswith("lane-gone.json"), str(rec.get("where")))
        check("the headline carries the finding in its first 400 chars",
              "STALE" in rep["headline"] and "stale=1" in rep["headline"],
              rep["headline"][:200])

        # NEGATIVE CONTROL: the identical fixture with a clean receipt must NOT be stale --
        # otherwise this test would pass against a monitor that calls everything stale.
        (run / "worker-gone.exit").write_text("0\n")
        rc2, rep2, _ = run_monitor(root, "--no-cli", *_refs_stub(root, 0))
        check("the same lane with receipt 0 is NOT stale", rep2["agents"]["stale"] == 0,
              json.dumps(rep2["agents"]["stale_records"])[:200])
        check("...and the outcome falls back to CLEAN", rep2.get("outcome") == "CLEAN",
              str(rep2.get("outcome")))
        check("...with a different exit code", rc2 == 0 and rc2 != rc, f"{rc2} vs {rc}")


def test_a_healthy_fleet_reports_clean() -> None:
    """POSITIVE CONTROL: agents really were enumerated, and CLEAN says so with a count."""
    print("\n-- a healthy fleet reports CLEAN")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        run = make_run(root, "run-20260101-000011", "a", harness="claude-code")
        make_run(root, "run-20260101-000011", "b", harness="antigravity")
        (run / "worker-a.exit").write_text("0\n")
        (run / "worker-b.exit").write_text("0\n")
        rc, rep, err = run_monitor(root, "--no-cli", *_refs_stub(root, 0))
        check("outcome is CLEAN", rep.get("outcome") == "CLEAN", str(rep.get("outcome")))
        check("exit 0", rc == 0, f"rc={rc}")
        check("CLEAN is backed by a real enumeration, not by an empty view",
              rep["agents"]["total"] == 2, json.dumps(rep["agents"]["by_harness"]))
        check("coverage is complete -- CLEAN is unreachable otherwise",
              rep["coverage"]["complete"] is True and rep["coverage"]["blind"] == 0,
              json.dumps(rep["coverage"]["blind_sources"])[:200])
        check("nothing stale, suspected or undetermined",
              rep["agents"]["stale"] == 0 and rep["agents"]["suspected_stale"] == 0
              and rep["agents"]["unknown"] == 0, json.dumps(rep["agents"])[:200])
        check("both harnesses are represented, from one monitor",
              set(rep["agents"]["by_harness"]) == {"claude-code", "antigravity"},
              str(rep["agents"]["by_harness"]))
        check("the references axis was actually scanned before claiming none",
              rep["references"]["scanned"] is True and rep["references"]["stale_refs"] == 0,
              json.dumps(rep["references"])[:200])

        # NEGATIVE CONTROL: break ONE lane and CLEAN must go away. A CLEAN that cannot be
        # falsified is a constant.
        (run / "worker-b.exit").write_text("125\n")
        rc2, rep2, _ = run_monitor(root, "--no-cli", *_refs_stub(root, 0))
        check("one broken lane removes CLEAN", rep2.get("outcome") != "CLEAN",
              str(rep2.get("outcome")))
        check("...and changes the exit code", rc2 != rc, f"{rc2} vs {rc}")


def test_an_unobservable_environment_reports_unobservable_and_not_clean() -> None:
    """THE MOST IMPORTANT CASE IN THIS FILE.

    No run directory, no harness on PATH, no reference scanner. A naive monitor emits
    "0 stale agents, all healthy" here -- a sentence indistinguishable from a genuinely clean
    fleet. It must instead say UNOBSERVABLE, name what it could not see, and exit differently."""
    print("\n-- an environment it cannot observe reports UNOBSERVABLE, never clean")
    with tempfile.TemporaryDirectory() as td:
        blind_root = Path(td) / "nothing"
        blind_root.mkdir()
        # PATH emptied: shutil.which finds no harness, so the CLI probes are exercised and find
        # a genuinely harness-less box rather than being switched off with --no-cli.
        env = {**os.environ, "PATH": "/nonexistent"}
        p = subprocess.run([sys.executable, str(MON), "--once", "--root", str(blind_root),
                            "--format", "json", "--refs-cmd", "/nonexistent/stale_refs.py"],
                           capture_output=True, text=True, timeout=90, env=env)
        rep = json.loads(p.stdout)

        check("outcome is UNOBSERVABLE", rep.get("outcome") == "UNOBSERVABLE",
              str(rep.get("outcome")))
        check("IT IS NOT CLEAN", rep.get("outcome") != "CLEAN" and rep.get("verdict") != "clean",
              f"{rep.get('outcome')}/{rep.get('verdict')}")
        check("exit 3 -- a third code, distinct from CLEAN(0) and STALE(5)", p.returncode == 3,
              f"rc={p.returncode}")
        check("zero agents is reported ALONGSIDE unobservable, never instead of it",
              rep["agents"]["total"] == 0 and rep["outcome"] == "UNOBSERVABLE")
        check("it says WHAT it could not see, by name",
              any(b["source"] == "devloop_runs" for b in rep["coverage"]["blind_sources"]),
              json.dumps(rep["coverage"]["blind_sources"])[:200])
        check("...and WHY, in the source's own reason",
              any("no .devloop" in b["reason"] for b in rep["coverage"]["blind_sources"]),
              json.dumps(rep["coverage"]["blind_sources"])[:240])
        check("it warns a reader off the exact misreading",
              "not a clean fleet" in rep["verdict_reason"].lower()
              or "measured nothing" in rep["verdict_reason"].lower(),
              rep["verdict_reason"][:160])
        check("no enumerating source claimed to have answered",
              rep["coverage"]["can_enumerate"] is False,
              json.dumps(rep["coverage"])[:200])
        check("an absent harness reads as not installed, not as zero agents",
              all(h["installed"] is False for h in rep["harnesses"]),
              json.dumps([h["harness"] for h in rep["harnesses"] if h["installed"]]))
        check("the reference axis is unavailable, not zero",
              rep["references"]["scanned"] is False
              and rep["references"]["stale_refs"] is None,
              json.dumps(rep["references"])[:200])
        check("the headline leads with the word, for a truncated reader",
              rep["headline"].split()[1] == "UNOBSERVABLE", rep["headline"][:120])

        # NEGATIVE CONTROL: the SAME code path, same flags, on a tree it CAN observe. If this
        # also came back UNOBSERVABLE the value would be a constant and would prove nothing.
        seen = Path(td) / "seen"
        run = make_run(seen, "run-20260101-000012", "ok")
        (run / "worker-ok.exit").write_text("0\n")
        q = subprocess.run([sys.executable, str(MON), "--once", "--root", str(seen),
                            "--format", "json", "--no-cli", *_refs_stub(Path(td), 0)],
                           capture_output=True, text=True, timeout=90)
        rep2 = json.loads(q.stdout)
        check("an observable tree is NOT unobservable",
              rep2.get("outcome") == "CLEAN", str(rep2.get("outcome")))
        check("...and exits 0, so the two are distinguishable by exit code alone",
              q.returncode == 0 and q.returncode != p.returncode,
              f"{q.returncode} vs {p.returncode}")


def test_a_128_second_silent_agent_is_not_reported_stale() -> None:
    """THE REGRESSION GUARD for the measured finding. agy_monitor.py recorded a real multi-lane
    run going 128 SECONDS silent while a gate executed, and a time-based rule called that
    healthy manager stalled. Here the agent is silent for 200s -- well past 128 -- with the
    threshold set BELOW its silence, and it must still read as working."""
    print("\n-- 128+ seconds of silence from a progressing agent is not staleness")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        run = make_run(root, "run-20260101-000013", "gating")
        job.spawn(run / "jobs", "gating", ["sleep", "120"], root, budget_s=3600, label="gating")
        pid = _wait_running(run / "jobs", "gating")
        check("the fixture agent really is running", pid is not None, "job never started")
        try:
            # Backdate EVERY artifact by 200s, the job's own out/err included: nothing has been
            # written for longer than the measured quiet period, which is exactly the trap.
            old = time.time() - 200
            for art in sorted(run.rglob("*")):
                try:
                    os.utime(art, (old, old))
                except OSError:
                    pass
            rc, rep, err = run_monitor(root, "--no-cli", *_refs_stub(root, 0),
                                       "--silence-after-s", "128")
            lane = next((r for r in rep["agents"]["records"]
                         if r["agent_id"].endswith(":gating")), None)
            check("the lane was enumerated", lane is not None, err[:200])
            if lane:
                check("silent for >128s and still LIVE", lane["state"] == "live", str(lane)[:200])
                check("NOT stale", lane["stale"] is False, str(lane)[:200])
                check("...and not even suspected", lane["basis"] == "", str(lane)[:200])
                check("it cites the fact that outranked the clock",
                      "alive" in lane["reason"], lane["reason"][:140])
                check("the silence it ignored is still REPORTED, not hidden",
                      lane["last_signal_s"] is not None and lane["last_signal_s"] >= 128,
                      str(lane["last_signal_s"]))
            check("no agent is stale and none is suspected",
                  rep["agents"]["stale"] == 0 and rep["agents"]["suspected_stale"] == 0,
                  json.dumps(rep["agents"])[:200])
            check("the whole tick is CLEAN", rep.get("outcome") == "CLEAN",
                  f"{rep.get('outcome')} :: {rep.get('verdict_reason','')[:120]}")
            check("the policy it applied is published so a reader can judge it",
                  rep["staleness_policy"]["silence_after_s"] == 128.0
                  and "128s" in rep["staleness_policy"]["measured_basis"],
                  json.dumps(rep["staleness_policy"])[:200])

            # NEGATIVE CONTROL: the clock WAS armed. Remove only the job record -- same lane,
            # same 200s of silence, same threshold -- so liveness becomes unmeasurable, and the
            # silence rule fires. That proves LIVENESS, not a disabled timer, spared the agent.
            shutil.rmtree(run / "jobs" / "gating")
            rc2, rep2, _ = run_monitor(root, "--no-cli", *_refs_stub(root, 0),
                                       "--silence-after-s", "128")
            lane2 = next((r for r in rep2["agents"]["records"]
                          if r["agent_id"].endswith(":gating")), None)
            check("with liveness unmeasurable the SAME silence does fire",
                  lane2 and lane2["state"] == "suspected", str(lane2)[:200])
            check("...and even then only as a WEAK suspicion, never measured-stale",
                  lane2 and lane2["basis"] == "silence" and lane2["confidence"] == "weak"
                  and rep2["agents"]["stale"] == 0, str(lane2)[:200])
        finally:
            try:
                os.kill(pid, signal.SIGKILL)
            except (OSError, TypeError):
                pass


def test_reference_scan_absent_reports_unavailable_not_none_found() -> None:
    """'No stale references' is a lie when nothing was scanned. Absent and zero must be two
    different values, at the unit level and through the CLI."""
    print("\n-- an absent reference scanner yields `unavailable`, never `none found`")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / ".devloop").mkdir()

        # Unit level: the default-path branch, with a scripts dir that holds no scanner.
        empty_scripts = Path(td) / "no_scripts"
        empty_scripts.mkdir()
        src = gm.scan_references(empty_scripts, root, None, 5.0)
        check("an absent scanner is BLIND", src["status"] == gm.BLIND, src["status"])
        check("...and says so in the words a reader needs",
              "unavailable" in src["reason"].lower(), src["reason"][:160])
        check("...naming the file it looked for",
              "stale_refs.py" in src["reason"], src["reason"][:160])
        check("...and reporting NO count at all, rather than zero",
              "stale_refs" not in src["detail"] and src["detail"]["available"] is False,
              json.dumps(src["detail"])[:160])

        # Through the CLI, end to end.
        _, rep, _ = run_monitor(root, "--no-cli", "--refs-cmd", "/nonexistent/stale_refs.py")
        check("the report says unavailable", rep["references"]["status"] == gm.BLIND
              and "unavailable" in rep["references"]["reason"].lower(),
              rep["references"]["reason"][:160])
        check("stale_refs is None, NEVER 0", rep["references"]["stale_refs"] is None,
              repr(rep["references"]["stale_refs"]))
        check("scanned is False", rep["references"]["scanned"] is False)
        check("the headline says unavailable rather than a quiet zero",
              "refs=unavailable" in rep["headline"], rep["headline"][:200])
        check("and the tick cannot be CLEAN without having scanned",
              rep.get("outcome") != "CLEAN", str(rep.get("outcome")))

        # NEGATIVE CONTROL: a scanner that really ran and really found none. `unavailable` and
        # `none` must be visibly different values -- that difference IS the property.
        _, rep2, _ = run_monitor(root, "--no-cli", *_refs_stub(root, 0))
        check("a real zero is recorded as scanned, with the count 0",
              rep2["references"]["scanned"] is True
              and rep2["references"]["stale_refs"] == 0,
              json.dumps(rep2["references"])[:160])
        check("...and renders as `none`, a different word from `unavailable`",
              "refs=none" in rep2["headline"], rep2["headline"][:200])
        check("...and only THEN may the tick be CLEAN", rep2.get("outcome") == "CLEAN",
              str(rep2.get("outcome")))


# ------------------------------------------------------ the three outcomes, and overlap safety

def test_the_three_outcomes_have_three_exit_codes() -> None:
    """The three outcomes must never collapse into two, in the report OR in $?."""
    print("\n-- CLEAN / STALE / UNOBSERVABLE are three values and three exit codes")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        run = make_run(root, "run-20260101-000014", "x")
        (run / "worker-x.exit").write_text("0\n")
        good = _refs_stub(root, 0)

        rc_clean, rep_clean, _ = run_monitor(root, "--no-cli", *good)
        (run / "worker-x.exit").write_text("125\n")
        rc_stale, rep_stale, _ = run_monitor(root, "--no-cli", *good)
        blind_root = Path(td) / "void"
        blind_root.mkdir()
        rc_blind, rep_blind, _ = run_monitor(blind_root, "--no-cli", *good)

        got = {rep_clean.get("outcome"): rc_clean, rep_stale.get("outcome"): rc_stale,
               rep_blind.get("outcome"): rc_blind}
        check("three distinct outcomes appeared", set(got) == {"CLEAN", "STALE", "UNOBSERVABLE"},
              str(got))
        check("three distinct exit codes", len(set(got.values())) == 3, str(got))
        check("they are the documented codes", got == {"CLEAN": 0, "STALE": 5,
                                                       "UNOBSERVABLE": 3}, str(got))
        check("the mapping is one function, attackable in one place",
              gm.outcome_of("clean") == "CLEAN" and gm.outcome_of("stale") == "STALE"
              and gm.outcome_of("suspect") == "STALE"
              and gm.outcome_of("partial") == "UNOBSERVABLE"
              and gm.outcome_of("blind") == "UNOBSERVABLE")
        check("an unknown verdict degrades to UNOBSERVABLE, never to CLEAN",
              gm.outcome_of("something-new") == "UNOBSERVABLE")

        # NEGATIVE CONTROL: --supervised deliberately collapses findings to 0, and ONLY `blind`
        # stays non-zero. Without this a persistently stale fleet kills the monitor watching it.
        (run / "worker-x.exit").write_text("125\n")
        check("--supervised exits 0 on STALE, so the supervisor keeps the monitor alive",
              run_monitor(root, "--no-cli", *good, "--supervised")[0] == 0)
        check("...but still escalates `blind`, where failing IS the right outcome",
              run_monitor(blind_root, "--no-cli", *good, "--supervised")[0] == 3)


def test_enumerated_but_undetermined_is_not_counted_healthy() -> None:
    """An agent that was found but not understood must not be silently counted as fine."""
    print("\n-- an enumerated agent whose state is undetermined caps the verdict")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        run = make_run(root, "run-20260101-000015", "vague")   # no receipt, no job, recent
        rc, rep, _ = run_monitor(root, "--no-cli", *_refs_stub(root, 0),
                                 "--silence-after-s", "100000")
        check("it is `unknown`, not stale and not healthy",
              rep["agents"]["unknown"] == 1 and rep["agents"]["stale"] == 0,
              json.dumps(rep["agents"])[:200])
        check("the tick is NOT clean", rep.get("outcome") == "UNOBSERVABLE",
              f"{rep.get('outcome')}/{rep.get('verdict')}")
        check("the reason says it was not observed rather than observed healthy",
              "could NOT be determined" in rep["verdict_reason"],
              rep["verdict_reason"][:200])
        check("the count is in the headline", "unknown=1" in rep["headline"],
              rep["headline"][:200])

        # NEGATIVE CONTROL: give the same lane a receipt and the doubt must clear.
        (run / "worker-vague.exit").write_text("0\n")
        rc2, rep2, _ = run_monitor(root, "--no-cli", *_refs_stub(root, 0))
        check("with a receipt it is determined, and the tick is CLEAN",
              rep2["agents"]["unknown"] == 0 and rep2.get("outcome") == "CLEAN",
              f"{rep2['agents']['unknown']} {rep2.get('outcome')}")


def test_a_slow_tick_cannot_corrupt_the_published_report() -> None:
    """The supervisor never overlaps its own monitor (single-threaded, killed at timeout_s), but
    a human or a second supervisor can. Concurrent publishes must not tear the file."""
    print("\n-- concurrent publishes leave one whole report, never half of two")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        run = make_run(root, "run-20260101-000016", "p")
        (run / "worker-p.exit").write_text("0\n")
        out = root / "global-monitor.json"
        procs = [subprocess.Popen([sys.executable, str(MON), "--once", "--root", str(root),
                                   "--no-cli", *_refs_stub(root, 0), "--quiet",
                                   "--report-out", str(out)],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                 for _ in range(6)]
        for q in procs:
            q.wait(timeout=90)
        check("every concurrent run exited 0", all(q.returncode == 0 for q in procs),
              str([q.returncode for q in procs]))
        try:
            doc = json.loads(out.read_text())
            whole = doc.get("schema") == gm.SCHEMA and "outcome" in doc
        except (json.JSONDecodeError, OSError) as e:
            whole = False
            doc = {"error": str(e)}
        check("the surviving report is ONE whole document", whole, json.dumps(doc)[:160])
        check("no temporary file is left behind", not list(root.glob("*.tmp")),
              str([x.name for x in root.glob('*.tmp')]))
        check("the monitor bounds itself under the supervisor's timeout",
              gm.DEFAULT_DEADLINE_S <= 25.0 and gm.DEFAULT_DEADLINE_S < gm.TICK_S,
              f"{gm.DEFAULT_DEADLINE_S} vs {gm.TICK_S}")

        # NEGATIVE CONTROL: an unpublishable path must FAIL loudly rather than pretend.
        bad = subprocess.run([sys.executable, str(MON), "--once", "--root", str(root),
                              "--no-cli", *_refs_stub(root, 0), "--quiet",
                              "--report-out", "/proc/1/cannot/write/here.json"],
                             capture_output=True, text=True, timeout=90)
        check("an unwritable report path exits 2, not 0", bad.returncode == 2,
              f"rc={bad.returncode} {bad.stderr[-120:]}")


def main() -> int:
    def run(t):
        try:
            t()
        except Exception as e:                  # a crashing control is a FAILURE, not an abort
            print(f"  FAIL  {t.__name__} RAISED {type(e).__name__}: {e}")
            FAILURES.append(f"{t.__name__} raised {type(e).__name__}")

    for t in (test_a_stale_agent_is_detected,
              test_a_healthy_fleet_reports_clean,
              test_an_unobservable_environment_reports_unobservable_and_not_clean,
              test_a_128_second_silent_agent_is_not_reported_stale,
              test_reference_scan_absent_reports_unavailable_not_none_found,
              test_the_three_outcomes_have_three_exit_codes,
              test_enumerated_but_undetermined_is_not_counted_healthy,
              test_a_slow_tick_cannot_corrupt_the_published_report,
              test_blind_is_not_clean,
              test_clean_needs_complete_coverage,
              test_a_live_pid_is_never_stale,
              test_receipt_outranks_everything,
              test_silence_is_only_ever_a_suspicion,
              test_reference_scan_absence_is_not_zero,
              test_run_marker_is_checked_against_its_pid,
              test_stale_cannot_be_asserted_without_a_basis,
              test_report_is_published_atomically_and_matches,
              test_harness_table_claims_only_what_was_measured,
              test_it_is_a_conforming_serverd_monitor_worker,
              test_a_blind_supervisor_state_is_not_silence):
        run(t)
    print()
    if FAILURES:
        print(f"FAILED ({len(FAILURES)}): {', '.join(FAILURES)}")
        return 1
    print("all global-monitor controls passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
