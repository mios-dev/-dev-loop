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
            # A silence threshold of 1s, then sleep past it: a naive monitor calls this dead.
            time.sleep(2.0)
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
        check("receipt 0 -> finished, not stale",
              by["done"]["state"] == "finished" and by["done"]["stale"] is False, str(by["done"]))
        check("receipt 125 -> STALE (dispatched and gone)",
              by["never"]["stale"] is True and by["never"]["basis"] == "receipt",
              str(by["never"]))
        check("receipt 124 -> finished: a timeout terminated, it did not go stale",
              by["killed"]["state"] == "finished" and by["killed"]["stale"] is False,
              str(by["killed"]))
        check("the harness comes from the lane file, not from the monitor's host",
              by["done"]["harness"] == "antigravity", by["done"]["harness"])
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
        lane = rep["agents"]["records"][0]
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
        check("--fail-on-stale does NOT fire on a suspicion",
              run_monitor(root, *BASE, "--silence-after-s", "900", "--fail-on-stale")[0] == 0)

        # NEGATIVE CONTROL A: under the threshold nothing is suspected at all.
        rc2, rep2, _ = run_monitor(root, *BASE, "--silence-after-s", "100000")
        check("under the threshold it is `unknown`, not stale and not healthy",
              rep2["agents"]["records"][0]["state"] == "unknown"
              and rep2["agents"]["suspected_stale"] == 0,
              str(rep2["agents"]["records"][0]["state"]))
        check("...and `unknown` still does not read as clean",
              "Undetermined" in rep2["agents"]["records"][0]["reason"],
              rep2["agents"]["records"][0]["reason"][:120])

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
        check("--fail-on-stale fires on stale references",
              run_monitor(root, "--no-cli", *_refs_stub(root, 7, "regressed"),
                          "--fail-on-stale")[0] == 4)


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
        p = subprocess.run([sys.executable, str(MON), "--root", str(root), *BASE,
                            "--report-out", str(out), "--quiet"],
                           capture_output=True, text=True, timeout=90)
        check("it exits 0 having published", p.returncode == 0, p.stderr[-200:])
        check("the parent directory was created", out.is_file())
        doc = json.loads(out.read_text())
        check("the file carries the schema", doc.get("schema") == gm.SCHEMA)
        check("--quiet prints the verdict, not the document",
              doc["verdict"].upper() in p.stdout and len(p.stdout) < 600, p.stdout[:120])
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
             "argv": [sys.executable, str(MON), "--root", str(root), "--quiet", "--no-cli",
                      "--refs-cmd", "/bin/false",
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


def main() -> int:
    for t in (test_blind_is_not_clean,
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
        t()
    print()
    if FAILURES:
        print(f"FAILED ({len(FAILURES)}): {', '.join(FAILURES)}")
        return 1
    print("all global-monitor controls passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
