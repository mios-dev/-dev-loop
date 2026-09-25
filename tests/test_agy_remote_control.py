#!/usr/bin/env python3
"""
Controls for the ONE flag that decides whether a running manager can be seen and driven
from Antigravity Remote Control: `agy --remote-control`.

The defect these guard
----------------------
A manager was launched as `agy -p "<prompt>" --dangerously-skip-permissions`, reported as
running on the strength of `pgrep` alone, and was invisible in Remote Control for two
independent reasons, either of which is sufficient:

  1. NEVER REGISTERED. Without `--remote-control` the CLI session does not open a remote
     connection at all. Measured 2026-09-20 on agy 1.2.6, two probes in the same cwd
     differing ONLY in this flag:
       with    server.go:3565      "Remote control enabled, starting connection"
               remote_control_v2.go:2037 "Connection status: Connected"
               server.go:3650      "Deleted session instance <id>-v2"   (at exit)
       without server.go:3768      "[RemoteControl] Session toggle is off, staying disconnected"
               server.go:3479      "Resolved proxyServerURL: \"\""
  2. ALREADY GONE. `-p` is single-turn: the process exits when the turn ends, and the
     remote connection is torn down with it (the "Deleted session instance" line above
     fires on exit). A single-shot run cannot be attached to even in principle.

The trap worth naming: the `remote-control serve` DAEMON was up and authenticated the whole
time. It registers the MACHINE -- an instance name in the Remote Control list -- not the
sessions running on it. A healthy daemon is therefore NOT evidence that any session is
visible, and reading it as such is how the false "running" report was produced.

Run: python3 tests/test_agy_remote_control.py
"""
from __future__ import annotations

import json
import os
import subprocess
import threading
import time
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills" / "dev-loop" / "scripts"
SESSION = SCRIPTS / "agy_session.py"
HOST = SCRIPTS / "agy_host.sh"
sys.path.insert(0, str(SCRIPTS))

from agy_session import session_argv          # noqa: E402

FAILURES: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name}{': ' + detail if detail else ''}")
        FAILURES.append(name)


# A fake `agy` that records the argv it was called with, then speaks just enough of the
# measured wire protocol to let the caller finish. What the manager DOES is irrelevant
# here; the only question is which flags reached the binary.
FAKE = r'''#!/usr/bin/env python3
import json, os, sys
open(os.environ["FAKE_AGY_ARGV"], "w").write(json.dumps(sys.argv[1:]))
print(json.dumps({"event": "init", "conversation_id": "fake-conv",
                  "init": {"cwd": os.getcwd(), "tools": [], "permission_mode": "yolo"}}),
      flush=True)
for _ in sys.stdin:
    print(json.dumps({"event": "result", "result": {"conversation_id": "fake-conv",
                      "status": "ok", "response": "done", "num_turns": 1}}), flush=True)
'''


def recorded_argv(tmp: Path, extra: list[str]) -> list[str]:
    """Run agy_session.py against the fake and return the argv the binary actually saw."""
    bindir = tmp / "bin"
    bindir.mkdir(parents=True, exist_ok=True)
    fake = bindir / "agy"
    fake.write_text(FAKE)
    fake.chmod(0o755)
    argv_out = tmp / "argv.json"
    prompt = tmp / "prompt.txt"
    prompt.write_text("do the thing")
    subprocess.run(
        [sys.executable, str(SESSION), "--prompt-file", str(prompt),
         "--run-root", str(tmp), "--poll-max", "0", *extra],
        capture_output=True, text=True, timeout=120,
        env={**os.environ, "PATH": f"{bindir}:{os.environ['PATH']}",
             "FAKE_AGY_ARGV": str(argv_out)})
    return json.loads(argv_out.read_text()) if argv_out.is_file() else []


def test_builder_is_a_switch() -> None:
    """Both sides. A flag that is always present is not a flag, it is a constant -- and a
    constant here would mean every lane run opens a remote connection nobody asked for."""
    print("session_argv is a real switch:")
    on = session_argv(remote_control=True)
    off = session_argv()
    check("on  -> --remote-control present", "--remote-control" in on, str(on))
    check("off -> --remote-control ABSENT", "--remote-control" not in off, str(off))
    check("the two differ by exactly that flag",
          [x for x in on if x != "--remote-control"] == off, f"{on} vs {off}")


def test_flag_order_survives() -> None:
    """`-p=` must stay LAST and stay attached-empty. A bare `-p` swallows the next token as
    its prompt, so a flag appended after it would be eaten and silently do nothing -- the
    failure mode would be a manager that looks correctly launched and is still invisible."""
    print("flag order:")
    argv = session_argv(model="m", effort="high", yolo=True, remote_control=True)
    check("-p= is last", argv[-1] == "-p=", str(argv))
    check("--remote-control precedes it", argv.index("--remote-control") < len(argv) - 1, str(argv))
    check("no bare -p anywhere", "-p" not in argv, str(argv))


def test_reaches_the_binary() -> None:
    """The builder is only half the claim; the flag has to survive subprocess launch."""
    print("the flag reaches the agy binary:")
    with tempfile.TemporaryDirectory() as td:
        got = recorded_argv(Path(td), ["--remote-control"])
        check("with --remote-control, the binary saw it", "--remote-control" in got, str(got))
    with tempfile.TemporaryDirectory() as td:
        got = recorded_argv(Path(td), [])
        check("without it, the binary did NOT", got and "--remote-control" not in got, str(got))


def test_host_passes_it_through() -> None:
    """agy_host.sh --session is the launcher an operator actually types. A flag the driver
    supports but the launcher drops is a flag nobody can use."""
    print("agy_host.sh --session pass-through:")
    src = HOST.read_text()
    check("--session path forwards it",
          "--remote-control) REMOTE_CONTROL=1" in src and
          'set -- "$@" --remote-control' in src, "not wired in the session branch")
    # The headless branch must NOT forward it: that connection would be torn down at the
    # turn end, producing precisely the phantom this file exists to prevent.
    headless = src.split("    headless)")[1].split("    session)")[0]
    check("--headless path does NOT forward it",
          'set -- "$@" --remote-control' not in headless,
          "a single-turn run would register a session that is gone before anyone can open it")


def run_held(tmp: Path, extra: list[str], stop_after: float | None = None) -> tuple[float, str]:
    """Run the fake session with a hold and return (elapsed, stderr)."""
    bindir = tmp / "bin"
    bindir.mkdir(parents=True, exist_ok=True)
    fake = bindir / "agy"
    fake.write_text(FAKE)
    fake.chmod(0o755)
    prompt = tmp / "prompt.txt"
    prompt.write_text("do the thing")
    stop = tmp / "STOP"
    if stop_after is not None:
        threading.Timer(stop_after, lambda: stop.write_text("stop\n")).start()
    t0 = time.monotonic()
    cp = subprocess.run(
        [sys.executable, str(SESSION), "--prompt-file", str(prompt), "--run-root", str(tmp),
         "--poll-max", "0", "--hold-file", str(stop), *extra],
        capture_output=True, text=True, timeout=180,
        env={**os.environ, "PATH": f"{bindir}:{os.environ['PATH']}",
             "FAKE_AGY_ARGV": str(tmp / "argv.json")})
    return time.monotonic() - t0, cp.stderr


def test_hold_keeps_the_session_alive() -> None:
    """The second half of the defect. `--remote-control` registers the session; exiting
    DELETES it. A driver that returns the moment the manager stops speaking hands the
    operator a Remote Control entry that is already gone -- which looks identical to the
    original phantom from the outside."""
    print("the hold actually holds:")
    with tempfile.TemporaryDirectory() as td:
        elapsed, err = run_held(Path(td), ["--hold-max-s", "6"])
        check("without a stop file it stays up for the budget", elapsed >= 5.5,
              f"returned after {elapsed:.1f}s — it did not hold")
        check("and says WHY it ended", "hold ended (budget)" in err, err[-300:])
    with tempfile.TemporaryDirectory() as td:
        elapsed, err = run_held(Path(td), ["--hold-max-s", "60"], stop_after=2.0)
        check("the stop file ends it", "hold ended (stopped)" in err, err[-300:])
        check("promptly, not at the ceiling", elapsed < 20,
              f"took {elapsed:.1f}s — the stop file is not being noticed")


def test_no_hold_means_no_hold() -> None:
    """Negative control on the hold itself: omit --hold-file and the run must return at
    once. A driver that always holds would pin a model session open on every lane run."""
    print("hold is opt-in:")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        t0 = time.monotonic()
        recorded_argv(tmp, [])
        elapsed = time.monotonic() - t0
        check("no --hold-file -> returns immediately", elapsed < 15,
              f"took {elapsed:.1f}s with no hold requested")


def test_hold_warns_when_it_is_pointless() -> None:
    """Holding a session that was never registered keeps a process alive that no operator
    can reach. Say so rather than letting it look like remote control is on."""
    print("hold without registration is called out:")
    with tempfile.TemporaryDirectory() as td:
        _, err = run_held(Path(td), ["--hold-max-s", "6"])
        check("warns it is NOT attachable", "NOT registered with Remote Control" in err, err[-300:])
    with tempfile.TemporaryDirectory() as td:
        _, err = run_held(Path(td), ["--hold-max-s", "6", "--remote-control"])
        check("with the flag, says it IS attachable",
              "attachable from Remote Control" in err, err[-300:])



def test_the_driver_writes_its_own_run_marker() -> None:
    """The monitor's blind spot, closed at the source.

    Measured before this: `BLIND native_marker: .devloop/native exists but session.status
    does not: a native session was hosted here and its run marker is missing, so its state
    is UNKNOWN`. agy_host.sh wrote the marker, so every direct caller of the driver was
    unobservable -- and a manager inside a long run_command is silent for minutes, so
    staleness cannot substitute for it."""
    print("the driver publishes session.status:")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        bindir = tmp / "bin"
        bindir.mkdir(parents=True)
        fake = bindir / "agy"
        fake.write_text(FAKE)
        fake.chmod(0o755)
        prompt = tmp / "p.txt"
        prompt.write_text("go")
        events = tmp / "native" / "session-events.ndjson"
        subprocess.run(
            [sys.executable, str(SESSION), "--prompt-file", str(prompt), "--run-root", str(tmp),
             "--poll-max", "0", "--events-out", str(events), "--remote-control"],
            capture_output=True, text=True, timeout=120,
            env={**os.environ, "PATH": f"{bindir}:{os.environ['PATH']}",
                 "FAKE_AGY_ARGV": str(tmp / "argv.json")})
        marker = events.parent / "session.status"
        check("a marker is written beside the events file", marker.is_file(),
              "no session.status — the monitor cannot tell thinking from gone")
        if marker.is_file():
            doc = json.loads(marker.read_text())
            check("it ends in a terminal state", doc.get("state") == "finished", str(doc))
            check("it records the pid", isinstance(doc.get("pid"), int), str(doc))
            check("it records whether the session was remote-controlled",
                  doc.get("remote_control") is True, str(doc))
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        recorded_argv(tmp, [])
        check("no --events-out -> no marker invented elsewhere",
              not list(tmp.rglob("session.status")), "a marker was written with nowhere to put it")



COUNTING_FAKE = r'''#!/usr/bin/env python3
import json, os, sys
n = 0
print(json.dumps({"event": "init", "conversation_id": "c", "init": {"cwd": os.getcwd(), "tools": [], "permission_mode": "yolo"}}), flush=True)
for line in sys.stdin:
    n += 1
    open(os.environ["FAKE_AGY_TURNS"], "w").write(str(n))
    print(json.dumps({"event": "result", "result": {"status": "ok", "num_turns": n,
          "response": "Does this draft look good to run?"}}), flush=True)
'''


def turns_taken(extra: list[str]) -> int:
    """Run the driver against a manager that ends EVERY turn with a question (the measured
    /teamwork-preview behaviour) and return how many turns it was given."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        (tmp / "bin").mkdir()
        fake = tmp / "bin" / "agy"
        fake.write_text(COUNTING_FAKE)
        fake.chmod(0o755)
        (tmp / "p.txt").write_text("draft a plan")
        turns = tmp / "turns"
        subprocess.run([sys.executable, str(SESSION), "--prompt-file", str(tmp / "p.txt"),
                        "--run-root", str(tmp), "--poll-max", "0", *extra],
                       capture_output=True, text=True, timeout=120,
                       env={**os.environ, "PATH": f"{tmp / 'bin'}:{os.environ['PATH']}",
                            "FAKE_AGY_TURNS": str(turns)})
        return int(turns.read_text()) if turns.is_file() else 0


def test_auto_continue_answers_the_stall_and_stops_on_the_fact() -> None:
    """Measured stall: /teamwork-preview ends its turn asking 'does this draft look good?' and an
    unattended session waits forever. Auto-continue answers it -- and must STOP on an external
    fact, or it is a loop with no end that burns turns."""
    print("auto-continue:")
    check("off by default: one turn, then the stall", turns_taken([]) == 1)
    n = turns_taken(["--auto-continue", "3"])
    check("--auto-continue 3 answers three turn-ends", n == 4, f"got {n} turns")
    n = turns_taken(["--auto-continue", "3", "--done-cmd", "true"])
    check("a done-cmd that already passes stops it at once", n == 1, f"got {n} turns")
    n = turns_taken(["--auto-continue", "3", "--done-cmd", "false"])
    check("a done-cmd failing IDENTICALLY stops at the convergence limit (3), not the budget",
          n == 3, f"got {n} turns")
    with tempfile.TemporaryDirectory() as td:
        ctr = Path(td) / "n"
        progressing = f'n=$(cat {ctr} 2>/dev/null || echo 0); n=$((n+1)); echo $n > {ctr}; echo "gap $n"; exit 1'
        n = turns_taken(["--auto-continue", "3", "--done-cmd", progressing])
    check("a done-cmd whose output CHANGES (progress) runs the full budget", n == 4, f"got {n} turns")



def test_teamwork_draft_approval_does_not_end_the_run() -> None:
    """Measured: in --teamwork mode the driver broke the moment no teamwork agent was live. But
    /teamwork-preview's FIRST turn ends asking 'does this draft look good to run?' -- before
    any agent exists -- so every unattended teamwork run ended right there (1 invoke_subagent in
    100 turns). Nothing live is not the same as finished."""
    print("teamwork draft-approval turn-end:")
    n = turns_taken(["--teamwork"])
    check("teamwork without auto-continue: one turn, then the stall", n == 1, f"got {n}")
    n = turns_taken(["--teamwork", "--auto-continue", "2"])
    check("teamwork + auto-continue answers the approval question", n == 3, f"got {n} turns")
    n = turns_taken(["--teamwork", "--auto-continue", "2", "--done-cmd", "true"])
    check("...and the external done-cmd still stops it", n == 1, f"got {n} turns")


RELAY_FAKE = r"""#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
relay = Path(os.environ["FAKE_RELAY"]) if os.environ.get("FAKE_RELAY") else None
log = open(os.environ["FAKE_MSGS"], "a")
print(json.dumps({"event": "init", "conversation_id": "c", "init": {"cwd": os.getcwd(), "tools": [], "permission_mode": "yolo"}}), flush=True)
n = 0
for line in sys.stdin:
    n += 1
    log.write(json.dumps(json.loads(line)) + "\n"); log.flush()
    if relay is not None and n == 2:
        relay.write_text(relay.read_text() + "item 2: new finding\n")   # the monitor edits it
    if relay is not None and n == 3:
        relay.write_text(relay.read_text())                              # touched, NOT changed
    print(json.dumps({"event": "result", "result": {"status": "ok", "num_turns": n,
          "response": "Does this draft look good to run?"}}), flush=True)
"""


def relay_messages(with_relay: bool) -> list[str]:
    """Drive a 4-turn session and return the text of every user message the manager got."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        (tmp / "bin").mkdir()
        fake = tmp / "bin" / "agy"
        fake.write_text(RELAY_FAKE)
        fake.chmod(0o755)
        (tmp / "p.txt").write_text("read the relay first")
        relay = tmp / "monitor-relay.md"
        relay.write_text("item 1: old finding\n")
        msgs = tmp / "msgs.ndjson"
        extra = ["--relay-file", str(relay)] if with_relay else []
        subprocess.run([sys.executable, str(SESSION), "--prompt-file", str(tmp / "p.txt"),
                        "--run-root", str(tmp), "--poll-max", "0", "--auto-continue", "3", *extra],
                       capture_output=True, text=True, timeout=120,
                       env={**os.environ, "PATH": f"{tmp / 'bin'}:{os.environ['PATH']}",
                            "FAKE_MSGS": str(msgs), "FAKE_RELAY": str(relay)})
        out = []
        for line in msgs.read_text().splitlines() if msgs.is_file() else []:
            m = json.loads(line)
            c = m.get("message", {}).get("content", m)
            out.append(json.dumps(c))
        return out


def test_relay_changes_reach_the_manager() -> None:
    """The monitor relays findings by editing a file, and turn 1 is the only turn whose text the
    manager chose to read it in. Every later turn is text the driver injects, so a relay edit
    made mid-run was invisible unless the manager happened to remember the file (measured
    2026-09-24: a teamwork run started before two research docs landed, and nothing pointed
    it back). Both sides: a CONTENT change is announced exactly once; a touch that changes
    nothing is not news; no --relay-file, no note."""
    print("relay changes reach the manager:")
    got = relay_messages(True)
    check("4 turns ran", len(got) == 4, f"got {len(got)}")
    if len(got) == 4:
        says = ["CHANGED since your last turn" in m for m in got]
        check("unchanged relay: turn 2 carries no note", not says[1], got[1][:200])
        check("changed relay: turn 3 tells the manager to re-read it", says[2], got[2][:300])
        check("touched but identical: turn 4 carries no note (content, not mtime)",
              not says[3], got[3][:300])
    got = relay_messages(False)
    check("without --relay-file no turn mentions a relay",
          len(got) == 4 and not any("relay" in m for m in got[1:]), str(got)[:300])
    src = HOST.read_text()
    check("agy_host.sh forwards AGY_HOST_RELAY_FILE at both session call sites",
          src.count('--relay-file "$AGY_HOST_RELAY_FILE"') == 2)


# Modelled on a REAL quota death (2026-09-24, agy 1.2.7): two bare error lines, then a result event
# with status "ERROR" and the reset time; the next turn finds the process gone.
QUOTA_FAKE = r"""#!/usr/bin/env python3
import json, os, sys
mode = os.environ.get("FAKE_MODE", "quota")
print(json.dumps({"event": "init", "conversation_id": "c", "init": {"cwd": os.getcwd(), "model": "m", "tools": [], "permission_mode": "always-proceed"}}), flush=True)
for n, line in enumerate(sys.stdin, 1):
    if n > 1:
        sys.exit(1)            # the second turn finds agy already gone
    if mode == "quota":
        print("error: Individual quota reached. Please upgrade your subscription to increase your limits. Resets in 2h44m46s.", flush=True)
        print('AGY_ERROR: {"short_error":"RESOURCE_EXHAUSTED (code 429): Individual quota reached.","status":"RESOURCE_EXHAUSTED","error_code":429,"retryable":true}', flush=True)
        print(json.dumps({"event": "result", "result": {"conversation_id": "c", "status": "ERROR", "response": "", "error": "Individual quota reached. Resets in 2h44m46s.", "duration_seconds": 1.0, "num_turns": 1}}), flush=True)
    else:
        print(json.dumps({"event": "result", "result": {"conversation_id": "c", "status": "SUCCESS", "response": "ok", "duration_seconds": 1.0, "num_turns": 1}}), flush=True)
"""


def ended(mode: str, done_cmd: str) -> tuple[int, str]:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        (tmp / "bin").mkdir()
        fake = tmp / "bin" / "agy"
        fake.write_text(QUOTA_FAKE)
        fake.chmod(0o755)
        (tmp / "p.txt").write_text("do the work")
        cp = subprocess.run([sys.executable, str(SESSION), "--prompt-file", str(tmp / "p.txt"),
                             "--run-root", str(tmp), "--poll-max", "0", "--auto-continue", "3",
                             "--done-cmd", done_cmd, "--hold-file", str(tmp / "STOP"),
                             "--hold-max-s", "3"],
                            capture_output=True, text=True, timeout=120,
                            env={**os.environ, "PATH": f"{tmp / 'bin'}:{os.environ['PATH']}",
                                 "FAKE_MODE": mode})
        return cp.returncode, cp.stderr


def test_dead_is_not_done() -> None:
    """Measured 2026-09-24: 11 nested AGY instances hit a quota 429, exited after two turns, and
    the driver printed "local work done" and returned 0 -- with not one deliverable written. The
    external stop condition must decide the exit code, whatever ended the session."""
    print("a session that ends without the work is not done:")
    rc, err = ended("quota", "false")
    check("quota death -> rc 75 (retry after reset)", rc == 75, f"rc={rc}\n{err[-400:]}")
    check("...and the reset time is carried", "Resets in 2h44m46s" in err, err[-300:])
    check("...and it is NOT announced as done", "local work done" not in err and "NOT met" in err, err[-300:])
    rc, err = ended("plain", "false")
    check("ended without quota, stop condition failing -> rc 7", rc == 7, f"rc={rc}\n{err[-300:]}")
    rc, err = ended("plain", "true")
    check("stop condition met -> rc 0, announced as done", rc == 0 and "local work done" in err, f"rc={rc}\n{err[-300:]}")


MSG_FAKE = r"""#!/usr/bin/env python3
import json, os, sys
log = open(os.environ["FAKE_MSGS"], "a")
mode = os.environ.get("FAKE_MODE", "claims-done")
print(json.dumps({"event": "init", "conversation_id": "c", "init": {"cwd": os.getcwd(), "model": "m", "tools": [], "permission_mode": "always-proceed"}}), flush=True)
for n, line in enumerate(sys.stdin, 1):
    log.write(json.dumps(json.loads(line)) + "\n"); log.flush()
    if mode == "refused":
        print(json.dumps({"event": "result", "result": {"conversation_id": "", "status": "ERROR", "response": "", "error": "invalid model selection: --effort is not supported", "duration_seconds": 0, "num_turns": 0}}), flush=True)
    else:
        print(json.dumps({"event": "result", "result": {"conversation_id": "c", "status": "SUCCESS", "response": "The job is done.", "duration_seconds": 1.0, "num_turns": n}}), flush=True)
"""


def drive(mode: str, done_cmd: str, auto: str = "30") -> tuple[int, str, list[str]]:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        (tmp / "bin").mkdir()
        fake = tmp / "bin" / "agy"
        fake.write_text(MSG_FAKE)
        fake.chmod(0o755)
        (tmp / "p.txt").write_text("do the work")
        msgs = tmp / "msgs.ndjson"
        cp = subprocess.run([sys.executable, str(SESSION), "--prompt-file", str(tmp / "p.txt"),
                             "--run-root", str(tmp), "--poll-max", "0", "--auto-continue", auto,
                             "--done-cmd", done_cmd],
                            capture_output=True, text=True, timeout=120,
                            env={**os.environ, "PATH": f"{tmp / 'bin'}:{os.environ['PATH']}",
                                 "FAKE_MSGS": str(msgs), "FAKE_MODE": mode})
        got = [json.dumps(json.loads(l).get("message", {}).get("content", ""))
               for l in (msgs.read_text().splitlines() if msgs.is_file() else [])]
        return cp.returncode, cp.stderr, got


def test_continue_says_why_and_stops_when_stuck() -> None:
    """Measured 2026-09-24: a research manager reported "done" 30 times while its stop condition
    failed on thin notes, because every continue said only "continue" -- 30 turns of quota, no
    information. The continue must carry the stop condition's own output, and the same failure
    repeated CONVERGE_LIMIT times must stop the loop (SKILL §12), not spend the budget."""
    print("continue carries the gap; identical failures stop the loop:")
    rc, err, msgs = drive("claims-done", "echo 'notes.md: 4 distinct URLs < 12'; exit 1")
    check("the next turn is told the stop condition's output",
          len(msgs) >= 2 and "4 distinct URLs < 12" in msgs[1], str(msgs[1:2])[:300])
    check("a manager that only says 'done' is stopped after 3 identical failures, not 30",
          len(msgs) == 3 and "NOT CONVERGING" in err, f"turns={len(msgs)}\n{err[-300:]}")
    check("...exit 8 (not converging), never 0", rc == 8, f"rc={rc}")
    rc, err, msgs = drive("refused", "false")
    check("an invocation agy refused (ERROR, 0 turns) is not auto-continued",
          len(msgs) == 1 and "not auto-continuing" in err, f"turns={len(msgs)}\n{err[-300:]}")
    check("...exit 7, the work was never done", rc == 7, f"rc={rc}")


def main() -> int:
    test_builder_is_a_switch()
    test_flag_order_survives()
    test_reaches_the_binary()
    test_host_passes_it_through()
    test_hold_keeps_the_session_alive()
    test_no_hold_means_no_hold()
    test_hold_warns_when_it_is_pointless()
    test_the_driver_writes_its_own_run_marker()
    test_auto_continue_answers_the_stall_and_stops_on_the_fact()
    test_teamwork_draft_approval_does_not_end_the_run()
    test_relay_changes_reach_the_manager()
    test_dead_is_not_done()
    test_continue_says_why_and_stops_when_stuck()
    print()
    if FAILURES:
        print(f"FAILED ({len(FAILURES)}): " + ", ".join(FAILURES))
        return 1
    print("all remote-control controls passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
