#!/usr/bin/env python3
"""
Controls for the one-writer-per-worktree lock (git_lock.py claim/owner/check + hooks/owner.sh).

Measured failure this guards (MiOS run-20260919-200726): devloop.sh ran a lane worker in
.worktrees/srf-libexec while an AGY supervisor started a second `claude -p` in the same tree.
The second writer changed 63 files under the first, and during the gate its edits made the
negative control fail to restore the tree, so the run aborted and two lanes were never gated.

Positive: while a lane holds the lock, a second claim is refused (exit 75), the owner is
named, and the PreToolUse hook denies a session outside the lane's process tree but allows
one inside it. Negative: SIGKILL the holder and the worktree is free at once (the kernel
drops the flock), a new claim succeeds, and a leftover record naming a live but unrelated
pid does not count as an owner. Plus: a failing gate no longer ends devloop.sh under set -e.

Run: python3 tests/test_worktree_owner.py
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCK = ROOT / "skills" / "dev-loop" / "scripts" / "git_lock.py"
HOOK = ROOT / "hooks" / "owner.sh"
DEVLOOP = ROOT / "skills" / "dev-loop" / "scripts" / "devloop.sh"
FAILURES: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    print(f"  {'ok  ' if cond else 'FAIL'} {name}{'' if cond or not detail else ': ' + detail}")
    if not cond:
        FAILURES.append(name)


def sh(cmd: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["sh", "-c", cmd], cwd=cwd, capture_output=True, text=True, timeout=60)


def repo(tmp: Path) -> Path:
    main = tmp / "main"
    main.mkdir()
    sh("git init -q -b main && git -c user.email=t@t -c user.name=t commit -q --allow-empty -m init"
       " && git worktree add -q .worktrees/lane -b lane/x", cwd=main)
    return main / ".worktrees" / "lane"


def lock_path(wt: Path) -> str:
    return sh(f"python3 '{LOCK}' path --wt '{wt}'").stdout.strip()


def hold(wt: Path, extra: str = "sleep 30") -> subprocess.Popen:
    """A stand-in lane: claims the worktree on an inherited fd, then runs `extra`."""
    cmd = (f"exec 9>>'{lock_path(wt)}'; python3 '{LOCK}' claim --wt '{wt}' --fd 9 --who lane-A --pid $$"
           f" || exit 75; {extra}")
    p = subprocess.Popen(["sh", "-c", cmd], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                         start_new_session=True)
    for _ in range(100):
        if sh(f"python3 '{LOCK}' owner --wt '{wt}'").returncode == 1 or p.poll() is not None:
            break
        time.sleep(0.05)
    return p


def hook_input(wt: Path) -> str:
    return json.dumps({"tool_name": "Edit", "cwd": str(wt), "tool_input": {"file_path": str(wt / "a.txt")}})


def test_positive() -> None:
    with tempfile.TemporaryDirectory() as t:
        wt = repo(Path(t))
        a = hold(wt)
        try:
            own = sh(f"python3 '{LOCK}' owner --wt '{wt}' --json")
            check("owner reports the live lane", own.returncode == 1 and json.loads(own.stdout)["who"] == "lane-A",
                  own.stdout + own.stderr)
            b = sh(f"exec 9>>'{lock_path(wt)}'; python3 '{LOCK}' claim --wt '{wt}' --fd 9 --who lane-B --pid $$")
            check("a second claim is refused with 75", b.returncode == 75, f"rc={b.returncode} {b.stderr}")
            check("the refusal names the owner", "lane-A" in b.stderr, b.stderr)
            out = subprocess.run(["sh", str(HOOK)], input=hook_input(wt), capture_output=True, text=True)
            check("hook denies a session outside the lane tree", '"permissionDecision":"deny"' in out.stdout,
                  out.stdout + out.stderr)
        finally:
            os.killpg(a.pid, signal.SIGKILL); a.wait()
        inner = hold(wt, f"printf '%s' '{hook_input(wt)}' | sh '{HOOK}'")
        so, _ = inner.communicate(timeout=30)
        check("hook allows the lane's own tree", "deny" not in so and inner.returncode == 0, so)


def test_negative() -> None:
    with tempfile.TemporaryDirectory() as t:
        wt = repo(Path(t))
        a = hold(wt)
        os.killpg(a.pid, signal.SIGKILL); a.wait()
        free = sh(f"python3 '{LOCK}' owner --wt '{wt}'")
        check("SIGKILLed owner leaves the worktree free", free.returncode == 0, free.stdout)
        rec = Path(lock_path(wt)).with_name("devloop-owner.json")
        rec.write_text(json.dumps({"pid": os.getpid(), "start": "", "who": "stale"}))
        still = sh(f"python3 '{LOCK}' owner --wt '{wt}'")
        check("a stale record naming a live unrelated pid is not an owner", still.returncode == 0, still.stdout)
        out = subprocess.run(["sh", str(HOOK)], input=hook_input(wt), capture_output=True, text=True)
        check("hook allows edits once the owner is gone", "deny" not in out.stdout, out.stdout)
        b = hold(wt, "true")
        b.wait(timeout=30)
        check("a new claim succeeds after the owner died", b.returncode == 0, b.stderr.read() if b.stderr else "")


def test_gate_failure_does_not_end_the_run() -> None:
    src = DEVLOOP.read_text()
    check("gate rc is captured, not left to set -e", '|| rc=$?' in src and '--root "$ROOT"; rc=$?' not in src)
    # The shape itself: under set -eu a failing command followed by `; rc=$?` exits; `|| rc=$?` does not.
    old = sh('set -eu; f() { false; rc=$?; echo rc=$rc; }; f; echo after')
    new = sh('set -eu; f() { rc=0; false || rc=$?; echo rc=$rc; }; f; echo after')
    check("old shape really aborted", "after" not in old.stdout)
    check("new shape continues past a failing gate", "rc=1" in new.stdout and "after" in new.stdout, new.stdout)


if __name__ == "__main__":
    for fn in (test_positive, test_negative, test_gate_failure_does_not_end_the_run):
        print(fn.__name__)
        fn()
    print("FAILED: " + ", ".join(FAILURES) if FAILURES else "all ok")
    sys.exit(1 if FAILURES else 0)
