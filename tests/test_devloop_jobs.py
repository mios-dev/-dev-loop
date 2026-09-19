#!/usr/bin/env python3
"""
Controls for devloop.sh's job-backed lane dispatch.

What changed and why
--------------------
Lanes used to be launched three ways, each broken differently:

  headless   `sh -c "$CMD"`                 SEQUENTIAL — one lane at a time
  detached   `( cd "$WTA" && sh -c "$CMD" ) &`  concurrent, but a plain `&` child is still a
                                            CHILD: it dies when the shell's session ends,
                                            which is the turn boundary that has killed lane
                                            trees here before
  tmux_grid  a pane per lane                concurrent, but tied to tmux

and every one of them was waited on by:

  while [ ! -f "$RUN/worker-$ID.exit" ]; do sleep 20; done

which has no budget and no liveness check. A lane that died hard hung the orchestrator forever
waiting for a receipt that would never be written — silence that looks exactly like work.

Detached lanes are now spawned through job.py: setsid, stdin closed, an orphan by construction,
and completion is a receipt the SHELL writes. wait_lane blocks on that receipt with a budget,
and distinguishes `lost` from `running` so a dead lane fails instead of hanging.

These controls run devloop.sh's real functions against trivial commands — no agent, no network.

Run: python3 tests/test_devloop_jobs.py
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills" / "dev-loop" / "scripts"
DEVLOOP = SCRIPTS / "devloop.sh"
JOB = SCRIPTS / "job.py"
sys.path.insert(0, str(SCRIPTS))

import job  # noqa: E402

FAILURES: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name}{': ' + detail if detail else ''}")
        FAILURES.append(name)


def test_detached_lanes_are_jobs_not_background_children() -> None:
    """The source-level claim: the detached branch must not use a bare `&`."""
    print("dispatch shape:")
    src = DEVLOOP.read_text()
    check("detached branch spawns through job.py", "$JOB_PY\" spawn --root \"$JOBS\"" in src)
    check("the old bare-& detached launch is gone",
          '( cd "$WTA" && sh -c "$CMD" ) >/dev/null 2>&1 &' not in src,
          "a plain background child still dies with the shell's session")
    check("wait_lane has a budget", "LANE_WAIT_BUDGET" in src,
          "the old loop waited forever for a receipt that might never come")
    check("wait_lane treats lost/forged as failure", "lost|forged" in src)
    check("headless stays sequential on purpose", "SEQUENTIAL by design" in src)
    check("the concurrency cap is stated as provisional", "provisional" in src,
          "no measurement here establishes a number; saying so is the honest form")


def test_jobs_run_concurrently() -> None:
    """POSITIVE CONTROL for the fan-out: three one-second jobs must overlap, not queue.

    If they ran sequentially the wall clock would be ~3s; concurrent it is ~1s. The assertion
    is deliberately loose (< 2.5s) so it measures overlap, not machine speed."""
    print("fan-out is concurrent:")
    root = Path(tempfile.mkdtemp(prefix="jobs-conc-"))
    t0 = time.time()
    for i in range(3):
        job.spawn(root, f"lane{i}", ["sh", "-c", "sleep 1"], Path("."), budget_s=30)
    spawn_elapsed = time.time() - t0
    check("spawning 3 jobs returns immediately", spawn_elapsed < 1.0,
          f"took {spawn_elapsed:.2f}s — spawn must not block")

    res = job.wait(root, [f"lane{i}" for i in range(3)], budget_s=30, interval_s=1)
    total = time.time() - t0
    check("all three completed", all(r["state"] == "done" and r["rc"] == 0 for r in res.values()),
          str({k: (v["state"], v["rc"]) for k, v in res.items()}))
    check("they overlapped rather than queued", total < 2.5,
          f"{total:.2f}s for 3x1s jobs — sequential would be ~3s")


def test_a_dead_lane_fails_instead_of_hanging() -> None:
    """THE control that matters. Kill a lane's wrapper so no receipt is ever written, then
    require the wait to TERMINATE with a failure rather than block forever.

    The old `while [ ! -f .exit ]; do sleep 20; done` would still be looping."""
    print("a lane that dies hard:")
    root = Path(tempfile.mkdtemp(prefix="jobs-dead-"))
    job.spawn(root, "doomed", ["sh", "-c", "sleep 300"], Path("."), budget_s=600)

    end = time.time() + 15
    s = job.status(root, "doomed")
    while s["pid"] is None and time.time() < end:
        time.sleep(0.2)
        s = job.status(root, "doomed")
    if not s["pid"]:
        check("lane started", False, "never got a pid")
        return
    os.kill(s["pid"], 9)

    t0 = time.time()
    res = job.wait(root, ["doomed"], budget_s=30, interval_s=1)
    elapsed = time.time() - t0
    check("wait TERMINATED instead of hanging", elapsed < 25, f"{elapsed:.1f}s")
    check("state is lost, not running", res["doomed"]["state"] == "lost", str(res["doomed"]))
    check("no exit code is invented", res["doomed"]["rc"] is None)

    cp = subprocess.run([sys.executable, str(JOB), "wait", "--root", str(root),
                         "--id", "doomed", "--budget", "5", "--interval", "1"],
                        capture_output=True, text=True, timeout=60)
    check("CLI exits 3 so the orchestrator can act", cp.returncode == 3, f"rc={cp.returncode}")
    job.kill(root, "doomed", "KILL")


def test_partial_completion_is_visible() -> None:
    """A wave where one lane succeeds and one fails must report BOTH, not collapse to a single
    verdict — partial completion is the normal case and hiding it is how a half-done run reads
    as done."""
    print("partial completion:")
    root = Path(tempfile.mkdtemp(prefix="jobs-partial-"))
    job.spawn(root, "good", ["sh", "-c", "exit 0"], Path("."), budget_s=30)
    job.spawn(root, "bad", ["sh", "-c", "exit 9"], Path("."), budget_s=30)
    res = job.wait(root, ["good", "bad"], budget_s=30, interval_s=1)
    check("the good lane is done rc=0", res["good"]["state"] == "done" and res["good"]["rc"] == 0)
    check("the bad lane is done rc=9", res["bad"]["state"] == "done" and res["bad"]["rc"] == 9,
          "a failing lane must report its real code, not be flattened")

    cp = subprocess.run([sys.executable, str(JOB), "wait", "--root", str(root),
                         "--id", "good", "--id", "bad", "--budget", "5", "--interval", "1"],
                        capture_output=True, text=True, timeout=60)
    check("CLI exits 2 when any lane failed", cp.returncode == 2, f"rc={cp.returncode}")


def test_budget_expiry_does_not_read_as_success() -> None:
    """Timeout-as-Pass, at the wave level: a wait whose budget expires while a lane is still
    running must NOT report success."""
    print("wait budget expiring mid-flight:")
    root = Path(tempfile.mkdtemp(prefix="jobs-budget-"))
    job.spawn(root, "slow", ["sh", "-c", "sleep 20"], Path("."), budget_s=60)
    res = job.wait(root, ["slow"], budget_s=2, interval_s=1)
    check("returns while the lane is still running", res["slow"]["state"] == "running",
          str(res["slow"]))
    check("no rc is invented for an unfinished lane", res["slow"]["rc"] is None)

    cp = subprocess.run([sys.executable, str(JOB), "wait", "--root", str(root),
                         "--id", "slow", "--budget", "2", "--interval", "1"],
                        capture_output=True, text=True, timeout=60)
    check("CLI exits non-zero on an unfinished lane", cp.returncode != 0, f"rc={cp.returncode}")
    job.kill(root, "slow", "KILL")


def main() -> int:
    for t in (test_detached_lanes_are_jobs_not_background_children,
              test_jobs_run_concurrently,
              test_a_dead_lane_fails_instead_of_hanging,
              test_partial_completion_is_visible,
              test_budget_expiry_does_not_read_as_success):
        t()
    print()
    if FAILURES:
        print(f"FAILED ({len(FAILURES)}): {', '.join(FAILURES)}")
        return 1
    print("all devloop-job controls passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
