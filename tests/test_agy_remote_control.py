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


def main() -> int:
    test_builder_is_a_switch()
    test_flag_order_survives()
    test_reaches_the_binary()
    test_host_passes_it_through()
    test_hold_keeps_the_session_alive()
    test_no_hold_means_no_hold()
    test_hold_warns_when_it_is_pointless()
    test_the_driver_writes_its_own_run_marker()
    print()
    if FAILURES:
        print(f"FAILED ({len(FAILURES)}): " + ", ".join(FAILURES))
        return 1
    print("all remote-control controls passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
