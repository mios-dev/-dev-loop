#!/usr/bin/env python3
"""
scripts/git_lock.py
Concurrency lock protection for git repository operations across lanes.
Supports both primary working trees and linked git worktrees (.git pointer file invariant).
"""
import os
import random
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional


def resolve_git_dir(cwd: Optional[Path] = None) -> Path:
    """
    Resolves the actual git directory for the current working tree.
    In standard git repos, this is <repo_root>/.git.
    In linked git worktrees, .git is an ASCII pointer file, and the real git directory
    is located at <main_repo>/.git/worktrees/<worker_id>.
    """
    try:
        git_dir = subprocess.check_output(
            ["git", "rev-parse", "--git-dir"],
            text=True,
            cwd=str(cwd) if cwd else None
        ).strip()
        p = Path(git_dir)
        if not p.is_absolute():
            p = ((cwd or Path.cwd()) / p).resolve()
        return p
    except Exception:
        # Fallback to walk-up
        cur = cwd or Path.cwd()
        for parent in [cur] + list(cur.parents):
            git_target = parent / ".git"
            if git_target.is_dir():
                return git_target.resolve()
            elif git_target.is_file():
                # Parse gitdir: pointer
                try:
                    content = git_target.read_text(encoding="utf-8").strip()
                    if content.startswith("gitdir:"):
                        ptr = content.split(":", 1)[1].strip()
                        ptr_path = Path(ptr)
                        if not ptr_path.is_absolute():
                            ptr_path = (parent / ptr_path).resolve()
                        return ptr_path
                except Exception:
                    pass
        return Path(".git").resolve()


def resolve_main_git_dir(cwd: Optional[Path] = None) -> Path:
    """
    Resolves the main repository's .git directory.
    For standard repos, this is identical to resolve_git_dir.
    For linked worktrees (<main>/.git/worktrees/<id>), this resolves to <main>/.git.
    """
    gd = resolve_git_dir(cwd)
    if gd.parent.name == "worktrees" and gd.parent.parent.name == ".git":
        return gd.parent.parent
    return gd


def run_git_safe(args: list, max_retries: int = 8, base_delay: float = 0.25, cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
    """Executes a git command with retry backoff against index.lock contention."""
    git_dir = resolve_git_dir(cwd)
    main_git_dir = resolve_main_git_dir(cwd)
    lock_files = [git_dir / "index.lock"]
    if main_git_dir != git_dir:
        lock_files.append(main_git_dir / "index.lock")

    env = {**os.environ, "CI": "1", "GIT_TERMINAL_PROMPT": "0", "GIT_PAGER": "cat", "PAGER": "cat", "NO_COLOR": "1"}

    for attempt in range(max_retries):
        for lock_file in lock_files:
            if lock_file.exists():
                try:
                    mtime = lock_file.stat().st_mtime
                    # If lockfile is older than 45 seconds, assume abandoned worker process and clean it
                    if time.time() - mtime > 45:
                        lock_file.unlink(missing_ok=True)
                except OSError:
                    pass

        proc = subprocess.run(
            (["git", "-C", str(cwd)] + args) if cwd else (["git"] + args),
            capture_output=True,
            text=True,
            cwd=str(cwd) if cwd else None,
            env=env
        )
        if proc.returncode == 0 or "index.lock" not in proc.stderr or attempt == max_retries - 1:
            return proc

        sleep_time = (base_delay * (2 ** attempt)) + random.uniform(0.05, 0.2)
        time.sleep(sleep_time)

    return proc


# --- One owner per worktree -------------------------------------------------------------
#
# Two dispatchers (devloop.sh and an AGY teamwork supervisor) each started a `claude -p` in the
# same lane worktree; the second clobbered the first's edits and broke its gate's negative
# control (measured 2026-09-19, MiOS run-20260919-200726). index.lock never fired because the
# writers edit files, not the index, and `git worktree lock` only blocks prune/remove.
#
# The owner lock is a kernel flock(2) on <worktree git-dir>/devloop-owner.lock. A dispatcher
# opens that file on an fd its whole lane process tree inherits and calls `claim --fd N`:
# flock locks belong to the open file description, so the lock outlives this helper and is
# released only when the last process holding the fd exits -- crash, OOM and SIGKILL
# included. Liveness is therefore the lock itself, never a pid lookup, so pid reuse cannot
# fake an owner and nobody ever has a reason to signal a peer. The JSON record next to it is
# for humans and for the hook's ancestry check; it is trusted only while the lock is held.
OWNER_LOCK = "devloop-owner.lock"
OWNER_REC = "devloop-owner.json"
EX_BUSY = 75  # EX_TEMPFAIL: someone else owns the worktree


def _owner_paths(wt: Path) -> tuple:
    gd = resolve_git_dir(wt)
    return gd / OWNER_LOCK, gd / OWNER_REC


def _proc_start(pid: int) -> str:
    try:
        # field 22 (starttime) -- the comm field may contain spaces, so split after ")"
        return Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[19]
    except (OSError, IndexError):
        return ""


def _ancestors(pid: int) -> list:
    out = []
    while pid > 1 and len(out) < 64:
        out.append(pid)
        try:
            stat = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
            pid = int(stat[1])
        except (OSError, IndexError, ValueError):
            break
    return out


def owner(wt: Path):
    """The live owner record of `wt`, or None when nobody holds the lock."""
    import fcntl
    import json
    lock, rec = _owner_paths(wt)
    if not lock.exists():
        return None
    with open(lock, "a") as f:
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            try:
                return json.loads(rec.read_text())
            except (OSError, ValueError):
                return {"pid": 0, "who": "unknown (record unreadable)"}
        fcntl.flock(f, fcntl.LOCK_UN)
    return None


def claim(wt: Path, fd: int, who: str, pid: int) -> int:
    """Lock `wt` on the caller's inherited fd `fd`; 0 on success, EX_BUSY if already owned."""
    import fcntl
    import json
    lock, rec = _owner_paths(wt)
    try:
        if os.path.realpath(f"/proc/self/fd/{fd}") != os.path.realpath(lock):
            print(f"claim: fd {fd} is not {lock}", file=sys.stderr)
            return 64
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        cur = owner(wt) or {}
        print(f"refusing: {wt} is owned by {cur.get('who', '?')} (pid {cur.get('pid', '?')}, "
              f"since {cur.get('since', '?')}); one writer per worktree", file=sys.stderr)
        return EX_BUSY
    except OSError as e:
        print(f"claim: {e}", file=sys.stderr)
        return 64
    tmp = rec.with_suffix(".tmp")
    tmp.write_text(json.dumps({"pid": pid, "start": _proc_start(pid), "who": who,
                               "wt": str(Path(wt).resolve()),
                               "since": time.strftime("%Y-%m-%dT%H:%M:%S%z")}) + "\n")
    os.replace(tmp, rec)
    return 0


def check(path: Path, me: int) -> str:
    """Hook helper: '' if `me` may write under `path`, else the reason it may not."""
    d = Path(path)
    while not d.exists() and d != d.parent:
        d = d.parent
    if d.is_file():
        d = d.parent
    try:
        top = subprocess.run(["git", "-C", str(d), "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, timeout=5).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""
    if not top:
        return ""
    cur = owner(Path(top))
    if not cur:
        return ""
    pid = int(cur.get("pid") or 0)
    if pid in _ancestors(me) and _proc_start(pid) == cur.get("start"):
        return ""
    return (f"dev-loop: {top} is owned by {cur.get('who', '?')} (pid {pid}, since "
            f"{cur.get('since', '?')}). One writer per worktree: do not edit it, do not start "
            f"another agent in it, and never signal the owner. Report back instead.")


def _main(argv: list) -> int:
    import argparse
    import json
    ap = argparse.ArgumentParser(prog="git_lock.py", description="worktree owner lock")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("claim", help="flock the worktree on an inherited fd")
    c.add_argument("--wt", required=True); c.add_argument("--fd", type=int, required=True)
    c.add_argument("--who", required=True); c.add_argument("--pid", type=int, default=os.getppid())
    o = sub.add_parser("owner", help="print the live owner; exit 1 when owned, 0 when free")
    o.add_argument("--wt", required=True); o.add_argument("--json", action="store_true")
    k = sub.add_parser("check", help="hook helper: exit 2 with the reason when --path is owned by a non-ancestor")
    k.add_argument("--path", required=True); k.add_argument("--me", type=int, default=os.getppid())
    sub.add_parser("path", help="print the lock file path for --wt").add_argument("--wt", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "claim":
        return claim(Path(a.wt), a.fd, a.who, a.pid)
    if a.cmd == "owner":
        cur = owner(Path(a.wt))
        print(json.dumps(cur) if a.json else (f"owned by {cur.get('who')} pid {cur.get('pid')}" if cur else "free"))
        return 1 if cur else 0
    if a.cmd == "check":
        why = check(Path(a.path), a.me)
        if why:
            print(why)
            return 2
        return 0
    print(_owner_paths(Path(a.wt))[0])
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
