#!/usr/bin/env python3
"""
claude_lane.py -- nested Claude Code CLI lanes for an Antigravity manager (stdlib only).

  dispatch --root REPO --id ID --objective-file F --owned PATH [--owned PATH ...]
           --positive CMD --negative CMD --negative-expect REGEX
           [--model opus] [--effort xhigh] [--max-turns N] [--timeout-s S] [--base REF]
                                   worktree + branch + lane spec, then `adapters.py run` spawned
                                   DETACHED through job.py; returns at once with the lane's PIN
  status   --root REPO --id ID     {state: running|done|failed|timeout|lost, rc, report_status}
  wait     --root REPO --id ID [--id ID ...] [--budget-s S] [--interval-s S]
                                   block; exit 0 ONLY if every lane's report status is done
  gate     --root REPO --id ID [--pin SHA]
                                   pin check, git-state + ownership audit, then adapters owned +
                                   adapters gate on the lane worktree (controls only on a done lane)
  collect  --root REPO --id ID     the lane report + a diff stat of the worktree against its base
  list     --root REPO             every nested Claude lane and its state
  kill     --root REPO --id ID     stop a lane you dispatched and have decided to abandon
  supervise -- ARGV...             INTERNAL: the lane's process-tree supervisor (see below)

Every subcommand prints exactly ONE JSON object on stdout, including when it refuses.

Why this exists
---------------
An Antigravity /teamwork-preview run is LANE-LESS: a manager and its teamwork agents work in
the base tree, with no worktree gate (AGENTS.md, "The stray base-tree guard is scoped to lane
runs"). Those agents have a run_command tool and run with --dangerously-skip-permissions, so
nothing stops one from typing `claude -p ...` -- and every property the dev loop depends on
would be missing from what it got:

  * LIFETIME. run_command moves anything still running after WaitMsBeforeAsync to the
    background, that parameter is CLAMPED to about 10000 ms (measured 2026-09-19), and a
    background task dies when the agent's turn ends. A nested Claude lane runs for minutes,
    so a bare `claude -p` is killed half way through, while the agent reports it started.
  * ISOLATION. It would edit the same base tree the teamwork agents are editing, with no
    exclusive owned paths and no ownership audit.
  * PROOF. Its "done" would be a sentence it said, not two controls that were seen to hold.

So a nested Claude subagent gets the SAME lane contract devloop.sh gives an orchestrated lane,
built from the same parts rather than a copy of them:

  * adapters.py normalize_spec / validate_spec / merged_lane -- the lane spec, schema and the
    rule that a lane with no real negative control is refused;
  * adapters.py run -- the lane prompt, the claude-code argv (--model/--effort, the report
    schema), the outer timeout, the report normalisation, and the parent session's identity
    stripped from the lane's environment;
  * adapters.py owned + gate -- the ownership audit and the two-sided gate;
  * job.py -- setsid + closed stdin + a shell-written receipt, so the lane is an orphan by
    construction and outlives the run_command that dispatched it and the turn around it;
  * git_lock.py -- one writer per worktree, exactly as devloop.sh claims it.

What `done` means, and what it does not
---------------------------------------
A lane is `done` only when job.py's wrapper wrote a receipt with rc 0, adapters.py's normalised
report says status done, AND no process of the lane is still alive. The receipt is written
after `supervise` has killed every descendant of the lane: supervise is a Linux child SUBREAPER
(prctl PR_SET_CHILD_SUBREAPER), so a detached, double-forked or setsid'd child of the lane is
reparented to it rather than to init, and is SIGKILLed before the receipt exists. Measured
before this: a lane's setsid'd child waited for the real receipt and then rewrote the receipt
and the report, and a lane that ended partial read as done. lane_status also refuses `done` (and
`lost`) while any process in the lane's session is alive, so a wrapper killed on its own, or a
straggler on a box without a subreaper, reads `running`, never finished.

This is a boundary against a careless or confused lane, NOT against a hostile one. The lane runs
as the same uid as the manager, so nothing here is an OS permission boundary: a lane can ask a
process outside its tree to act for it (cron, at, systemd-run, a daemon, nsenter as root), edit
the base tree or these very scripts through an absolute path, or rewrite its own state dir.
What the gate does about the parts of that it can see:

  * THE GATE DEFINITION IS PINNED. dispatch returns `pin`, a sha256 over lane.json (owned paths,
    both controls, the regex), the base commit and the dispatch-time baseline. gate recomputes
    it and refuses (exit 2, TAMPERED, no control run) when lane.json/baseline.json no longer
    match meta.json's copy of the pin -- and, when the manager passes `--pin` from its own
    dispatch output, when they no longer match THAT. Measured before this: a lane set its own
    positive_cmd to `true`, or its owned_paths to ['*'], and was reported mergeable. Without
    --pin, a lane that rewrites lane.json AND meta.json consistently is not detected; the
    manager holding the pin is the only copy a same-uid lane cannot reach.
  * THE AUDIT COVERS THE WHOLE CHANGE, not `git status`: HEAD must still be the base commit on
    the lane's own branch (a lane that COMMITTED is refused -- measured before this: a committed
    README edit passed and would have been merged by `git merge devloop/claude-<id>`), the
    index must equal HEAD (nothing staged), no index entry may carry skip-worktree or
    assume-unchanged (both hide an edit from git status while the controls still run on it),
    and every path that differs from the base -- committed, staged, unstaged or untracked, a
    rename counted as BOTH its source and its destination -- must be owned, matched segment by
    segment (`src/*.txt` does not own `src/a/b.txt`), and must not be a contract file
    (AGENTS.md, CLAUDE.md, GEMINI.md), git metadata (.git, .gitattributes, .gitignore,
    .gitmodules) or dev-loop state (.devloop/). dispatch refuses owned patterns that would
    own any of those, or everything.
  * GIT METADATA IS BASELINED. <common-dir>/hooks, config and info/ are hashed at dispatch; a
    change by gate time fails the gate naming the file (measured before this: a lane planted
    .git/hooks/pre-commit and it ran during the manager's merge commit).
  * THE BASE TREE IS BASELINED, BUT ONLY REPORTED. Paths of the base tree whose content changed
    during the lane are listed as `base_moved`. In a teamwork run other agents edit the base
    tree on purpose, so this cannot be attributed to the lane and is a warning, not a failure.
  * NOT COVERED: files ignored by .gitignore (build outputs a positive control might depend
    on), writes outside the base repo, and anything done through a process outside the lane's
    tree.

A lane that did not reach `done` never has its controls run: a negative control that does not
restore the tree would destroy work nobody staged (measured: it deleted a partial lane's only
file, and the "parked" diff was empty because it held no untracked files).

What this tool does NOT do: merge. It never commits, stages, merges or edits AGENTS.md. The AGY
manager is the only writer to shared state (AGENTS.md, "The manager is the only writer to
shared state"); it gates each lane here and merges only what passed, the way devloop.sh does.

Layout
------
  <root>/.devloop/worktrees/claude-<ID>       the lane's worktree, on branch devloop/claude-<ID>
  <root>/.devloop/native/claude/<ID>/         meta.json objective.md lanes.json lane.json
                                              baseline.json report.json worker.log job/ gate/
                                              dispatching (only while dispatch is in flight)

Exit codes
----------
  0   ok (dispatch spawned; wait: every lane done; gate: every check passed AND the lane is done)
  1   not done / failed (wait: some lane failed or was lost; gate: an audit or a control
      failed, or the lane did not reach status done)
  2   gate only: VACUOUS or TAMPERED -- the negative control passed, did not name the plant, did
      not restore the tree, the base tree moved during the gate, or the gate definition no
      longer matches its pin; never merge
  3   wait only: TIMEOUT -- the wait budget ran out, or a lane outran its --timeout-s
  64  usage: bad id, bad or dangerous --owned, not a git repo, unknown lane, unreadable objective
  65  the lane spec is invalid, its negative control is vacuous, or --max-turns is below the
      floor (refused before anything was created)
  70  the lane could not be spawned (everything it created was rolled back, except the two
      generic, idempotent .git/info/exclude lines)
  73  the id is already in use (state dir, worktree or branch exists) or git refused it
  75  gate/kill: the lane is still running, or another writer owns its worktree
  127 no `claude` binary on PATH (refused before anything was created)
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import adapters  # noqa: E402  -- the one lane code path; reused, not copied
import job  # noqa: E402       -- turn-durable spawn + receipt
import git_lock  # noqa: E402  -- one writer per worktree

ADAPTERS = HERE / "adapters.py"
LOCK_PY = HERE / "git_lock.py"
SELF = Path(__file__).resolve()
SKILL = HERE.parent / "SKILL.md"

ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,40}$")
STATE_REL = Path(".devloop") / "native" / "claude"
WT_REL = Path(".devloop") / "worktrees"
BRANCH_PREFIX = "devloop/claude-"
JOB_ID = "job"
# adapters.py enforces the lane's own --timeout-s and writes a `budget` report; the job budget
# is only the backstop for a wrapper that outlives it, so it must fire LATER, never first.
JOB_GRACE_S = 120
TERMINAL = ("done", "failed", "timeout", "lost")
# Negative controls that exit 0 whatever the tree holds. A gate would catch these as vacuous
# after the whole lane had run; refusing them at dispatch costs nothing.
ALWAYS_TRUE = {"true", ":", "exit 0", "/bin/true", "/usr/bin/true", "test 1", "[ 1 ]"}
# Measured with the real harness: a trivial objective took 7 turns to finish done, and --max-turns
# 8 ended at 9 turns as `partial` with the work already written -- the lane contract and the
# plugin's Stop hook (it forces a devloop_report) cost turns of their own. Below this floor a
# lane records finished work as not done.
MIN_MAX_TURNS = 12
# Paths no lane may own, whatever it is dispatched with: the constitution and its pointers, git
# metadata (hooks, attributes and filters execute code in the manager's context), and the
# dev-loop state the manager alone writes.
PROTECTED_BASENAMES = ("AGENTS.md", "CLAUDE.md", "GEMINI.md", ".gitattributes", ".gitignore",
                       ".gitmodules")
# Dispatch refuses a pattern that owns one of these top-level paths (`*`, `**`, `*.md`, `.git*`)
# or names a protected file outright (`docs/AGENTS.md`). A subtree such as `src/` stays legal
# even though src/ COULD hold a nested .gitattributes: the gate's protected() check refuses
# that edit by name if the lane makes it.
PROTECTED_PROBES = ("AGENTS.md", "CLAUDE.md", "GEMINI.md", ".git", ".git/config",
                    ".git/hooks/pre-commit", ".gitattributes", ".gitignore", ".gitmodules",
                    ".devloop/tasks.jsonl")
PR_SET_CHILD_SUBREAPER, PR_GET_CHILD_SUBREAPER = 36, 37

EX_OK, EX_FAIL, EX_VACUOUS, EX_TIMEOUT = 0, 1, 2, 3
EX_USAGE, EX_DATAERR, EX_SOFTWARE, EX_CANTCREAT, EX_BUSY, EX_NOCLAUDE = 64, 65, 70, 73, 75, 127


# ---------------------------------------------------------------- output
def emit(obj: dict, code: int, indent: int | None = 2) -> None:
    obj.setdefault("exit", code)
    print(json.dumps(obj, indent=indent))
    sys.exit(code)


def fail(code: int, error: str, **extra) -> None:
    emit({"ok": False, "error": error, **extra}, code)


class _Parser(argparse.ArgumentParser):
    """argparse exits 2 on a usage error, and 2 means VACUOUS in `gate`: a typo in a flag must
    never read as a vacuous lane. Usage errors are 64, as one JSON object like every result."""

    def error(self, message: str) -> None:  # type: ignore[override]
        fail(EX_USAGE, f"{self.prog}: {message}")


def _atomic_write(path: Path, text: str) -> None:
    """tmp + rename on one filesystem, so a reader never sees half a file (job.py's rule)."""
    tmp = path.with_name(f".{path.name}.tmp.{os.getpid()}")
    tmp.write_text(text, "utf-8")
    os.replace(tmp, path)


# ---------------------------------------------------------------- git + paths
def _git(cwd: Path, *args: str, env: dict | None = None,
         input: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True,
                          input=input, env={**os.environ, **adapters.NONINTERACTIVE, **(env or {})})


def repo_root(root: str) -> Path:
    p = Path(root).resolve()
    cp = _git(p, "rev-parse", "--show-toplevel") if p.is_dir() else None
    if cp is None or cp.returncode != 0 or not cp.stdout.strip():
        fail(EX_USAGE, f"not a git repository: {root}")
    return Path(cp.stdout.strip()).resolve()


def git_common_dir(root: Path) -> Path | None:
    cp = _git(root, "rev-parse", "--git-common-dir")
    if cp.returncode != 0 or not cp.stdout.strip():
        return None
    c = Path(cp.stdout.strip())
    return c if c.is_absolute() else (root / c).resolve()


def lane_paths(root: Path, lid: str) -> dict:
    st = root / STATE_REL / lid
    return {"state": st, "worktree": root / WT_REL / f"claude-{lid}",
            "branch": f"{BRANCH_PREFIX}{lid}", "meta": st / "meta.json",
            "lane": st / "lane.json", "spec": st / "lanes.json", "report": st / "report.json",
            "baseline": st / "baseline.json", "marker": st / "dispatching",
            "log": st / "worker.log", "job": st / JOB_ID, "gate": st / "gate"}


def check_id(lid: str) -> None:
    # The id becomes a directory name and a branch name. Anything outside this pattern -- a
    # slash, a dot, `..` -- is how a lane id walks out of .devloop/ or forges a ref.
    if not ID_RE.fullmatch(lid or ""):
        fail(EX_USAGE, f"bad lane id {lid!r}: must match {ID_RE.pattern}")


def read_meta(root: Path, lid: str) -> tuple[dict | None, str]:
    """(meta, '') or (None, why) -- never exits, so one bad lane cannot hide the others."""
    try:
        d = json.loads(lane_paths(root, lid)["meta"].read_text("utf-8"))
    except OSError:
        return None, "meta.json is missing"
    except json.JSONDecodeError as e:
        return None, f"meta.json is unreadable: {e}"
    return (d, "") if isinstance(d, dict) else (None, "meta.json is not an object")


def load_meta(root: Path, lid: str) -> dict:
    check_id(lid)
    meta, why = read_meta(root, lid)
    if meta is None:
        fail(EX_USAGE, f"no nested Claude lane {lid!r} under {root / STATE_REL} ({why})")
    return meta or {}


def read_report(path: Path) -> dict | None:
    try:
        d = json.loads(path.read_text("utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return d if isinstance(d, dict) else None


def ensure_excluded(root: Path) -> None:
    """devloop.sh excludes its worktree root and run dirs from the base repo's status; do the
    same, so a nested lane's worktree is not an untracked directory in the tree it came from.
    The lines are generic and idempotent, so a rolled-back dispatch leaves them in place: taking
    them out again would change info/exclude under every other lane's baseline."""
    common = git_common_dir(root)
    if common is None:
        return
    ex = common / "info" / "exclude"
    try:
        ex.parent.mkdir(parents=True, exist_ok=True)
        have = ex.read_text("utf-8").splitlines() if ex.is_file() else []
        add = [e for e in (f"/{WT_REL.as_posix()}/", f"/{STATE_REL.as_posix()}/") if e not in have]
        if add:
            with ex.open("a", encoding="utf-8") as f:
                f.write("".join(e + "\n" for e in add))
    except OSError:
        pass  # cosmetic: an unexcluded dir sits under .devloop/, which the base guard allows


# ---------------------------------------------------------------- ownership
def _norm_path(p: str) -> str:
    p = p.replace("\\", "/")
    while p.startswith("./"):
        p = p[2:]
    return p.strip("/")


def _segs_match(pat: list[str], path: list[str]) -> bool:
    if not pat:
        return True  # the pattern named a directory: everything under it is owned
    if pat[0] == "**":
        return any(_segs_match(pat[1:], path[i:]) for i in range(len(path) + 1))
    return bool(path) and fnmatch.fnmatchcase(path[0], pat[0]) and _segs_match(pat[1:], path[1:])


def is_owned_path(path: str, owned: list[str]) -> bool:
    """Segment-aware ownership. adapters.is_owned uses fnmatch on the whole path, where `*`
    crosses `/` (so `src/*.txt` owned `src/a/b/evil.txt`), and saw a staged rename as ONE string
    `old -> new` (so `*.txt` owned the deletion of README.md). Here each segment is matched on
    its own, `**` spans any number of segments, and a matched directory owns its subtree
    (`src`, `src/`, `src/*` and `src/**` all own everything under src/)."""
    ps = [s for s in _norm_path(path).split("/") if s]
    if not ps:
        return False
    for o in owned:
        segs = [s for s in _norm_path(o).split("/") if s]
        if segs and _segs_match(segs, ps):
            return True
    return False


def protected(path: str) -> str:
    """'' if a lane may own `path`, else what it is."""
    ps = [s for s in _norm_path(path).split("/") if s]
    if not ps:
        return ""
    if ps[-1] in ("AGENTS.md", "CLAUDE.md", "GEMINI.md"):
        return "a contract file"
    if ".git" in ps or ps[-1] in PROTECTED_BASENAMES:
        return "git metadata"
    if ps[0] == ".devloop":
        return "dev-loop shared state"
    return ""


def owned_problems(owned: list[str]) -> list[str]:
    out = []
    for o in owned:
        n = _norm_path(o)
        if o.startswith(("/", "\\")) or ".." in n.split("/"):
            out.append(f"--owned {o!r} must be relative to the worktree, with no '..'")
        elif not n or n == ".":
            out.append(f"--owned {o!r} owns the whole tree: name the paths the lane needs")
        else:
            last = n.split("/")[-1]
            hits = [pr for pr in PROTECTED_PROBES if is_owned_path(pr, [o])]
            if not hits and protected(n) and not any(ch in last for ch in "*?["):
                hits = [n]
            if hits:
                out.append(f"--owned {o!r} would own {hits[0]} ({protected(hits[0])}): no lane "
                           "may own contract files, git metadata or dev-loop state -- name the "
                           "paths it needs")
    return out


# ---------------------------------------------------------------- vacuity at dispatch
def vacuous_reasons(positive: str, negative: str, expect: str) -> list[str]:
    """Statically decidable ways a negative control cannot fail or cannot name its plant.

    adapters.validate_spec already refuses the v1 shape (`false` with no expect); these are the
    shapes it lets through, each of which the gate would only discover after the lane ran."""
    out = []
    neg = " ".join(negative.split())
    if not neg:
        out.append("negative control is empty")
    elif neg in ALWAYS_TRUE:
        out.append(f"negative control {negative!r} always exits 0, so it can never fail")
    if neg and neg == " ".join(positive.split()):
        out.append("negative control is the positive control: it passes whenever the lane does")
    if not expect.strip():
        out.append("negative_expect is empty: ANY failure -- a typo, command-not-found -- would "
                   "count as the control firing, so it names nothing")
    else:
        try:
            rx = re.compile(expect)
        except re.error as e:
            out.append(f"negative_expect is not a valid regex: {e}")
        else:
            if rx.search(""):
                out.append(f"negative_expect /{expect}/ matches the empty string, so it matches "
                           "any output and cannot name the planted violation")
    return out


# ---------------------------------------------------------------- baseline + pin
def _sha_file(p: Path, big: int = 8 << 20) -> str:
    try:
        if p.is_symlink():
            return "link:" + os.readlink(p)
        st = p.stat()
        if p.is_dir():
            return "dir"
        if st.st_size > big:  # a model or an archive: size + mtime, not a full read
            return f"big:{st.st_size}:{st.st_mtime_ns}"
        return hashlib.sha256(p.read_bytes()).hexdigest()
    except OSError:
        return "absent"


def git_meta_digest(root: Path) -> dict[str, str]:
    """Hashes of what git EXECUTES or obeys from the shared common dir: hooks, config, info/
    (exclude hides untracked files from every worktree's audit). A lane's own git dir under
    worktrees/ is left out -- its index and HEAD are checked directly."""
    common = git_common_dir(root)
    out: dict[str, str] = {}
    if common is None:
        return out
    for rel in ("config", "hooks", "info"):
        q = common / rel
        files = [q] if q.is_file() else (
            sorted(x for x in q.rglob("*") if x.is_file() or x.is_symlink()) if q.is_dir() else [])
        for f in files:
            out[f.relative_to(common).as_posix()] = _sha_file(f)
    return out


def base_tree_digest(root: Path) -> dict[str, str]:
    """{path: content hash} for every path the base tree's `git status` names (tracked changes
    and untracked files), .devloop/ excluded. Content, not the XY status, so a file that was
    already modified and is modified AGAIN still shows up."""
    cp = _git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    out: dict[str, str] = {}
    if cp.returncode != 0:
        return out
    recs = cp.stdout.split("\0")
    i = 0
    while i < len(recs):
        r = recs[i]
        i += 1
        if len(r) < 4:
            continue
        xy, path = r[:2], r[3:]
        names = [path]
        if "R" in xy or "C" in xy:
            if i < len(recs):
                names.append(recs[i])
            i += 1
        for n in names:
            if n and not n.startswith(".devloop/"):
                out[n] = _sha_file(root / n)
    return out


def baseline_snapshot(root: Path) -> dict:
    return {"git_meta": git_meta_digest(root), "base_tree": base_tree_digest(root)}


def compute_pin(lane: dict, base: str | None, baseline: dict) -> str:
    blob = json.dumps({"lane": lane, "base": base, "baseline": baseline}, sort_keys=True,
                      separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _changed_keys(before: dict, now: dict) -> list[str]:
    return sorted(k for k in set(before) | set(now) if before.get(k) != now.get(k))


# ---------------------------------------------------------------- processes
def _proc_fields(pid: int) -> list[str]:
    try:
        return Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
    except (OSError, IndexError):
        return []


def _proc_start_epoch(pid: int) -> float | None:
    f = _proc_fields(pid)
    try:
        ticks = int(f[19])
        btime = next(int(l.split()[1]) for l in Path("/proc/stat").read_text().splitlines()
                     if l.startswith("btime "))
        return btime + ticks / os.sysconf("SC_CLK_TCK")
    except (IndexError, ValueError, OSError, StopIteration):
        return None


def lingering(sid: int, not_after: float | None = None) -> list[int]:
    """Live (non-zombie) processes still in the lane's session. `not_after` drops processes
    that started after the receipt: a recycled pid leading an unrelated session is not ours."""
    if not sid:
        return []
    out = []
    for p in job._session_pids(sid):
        f = _proc_fields(p)
        if not f or f[0] == "Z":
            continue
        if not_after is not None:
            s = _proc_start_epoch(p)
            if s is not None and s > not_after + 1:
                continue
        out.append(p)
    return out


def _libc():
    try:
        import ctypes
        lib = ctypes.CDLL(None, use_errno=True)
        return lib if hasattr(lib, "prctl") else None
    except (OSError, ImportError, AttributeError):
        return None


def containment() -> str:
    """'subreaper' when this kernel lets supervise adopt the lane's orphans, else 'none'."""
    lib = _libc()
    if lib is None:
        return "none"
    import ctypes
    v = ctypes.c_int(0)
    return "subreaper" if lib.prctl(PR_GET_CHILD_SUBREAPER, ctypes.byref(v), 0, 0, 0) == 0 else "none"


def _descendants(root_pid: int) -> list[tuple[int, str]]:
    kids: dict[int, list[tuple[int, str]]] = {}
    for d in Path("/proc").iterdir():
        if not d.name.isdigit():
            continue
        f = _proc_fields(int(d.name))
        if len(f) > 1:
            try:
                kids.setdefault(int(f[1]), []).append((int(d.name), f[0]))
            except ValueError:
                continue
    out, stack = [], [root_pid]
    while stack:
        for pid, st in kids.get(stack.pop(), []):
            out.append((pid, st))
            stack.append(pid)
    return out


def _reap() -> None:
    while True:
        try:
            pid, _ = os.waitpid(-1, os.WNOHANG)
        except ChildProcessError:
            return
        if pid == 0:
            return


def kill_descendants(limit_s: float = 10.0) -> int:
    """SIGKILL every live descendant until none is left. A process being SIGKILLed cannot fork,
    and whatever it forked first is reparented here (subreaper), so a later round sees it."""
    me, killed, t0 = os.getpid(), set(), time.time()
    while time.time() - t0 < limit_s:
        _reap()
        live = [p for p, st in _descendants(me) if st != "Z"]
        if not live:
            break
        for p in live:
            try:
                os.kill(p, signal.SIGKILL)
                killed.add(p)
            except OSError:
                pass
        time.sleep(0.05)
    _reap()
    return len(killed)


def cmd_supervise(a) -> None:
    """Run ARGV, then kill whatever of the lane is left, THEN let the wrapper write its receipt.

    Without this the receipt was written when adapters.py exited, and the lane's detached
    children kept running: one wrote into the worktree after the lane read done and passed its
    gate; a setsid'd one waited for the receipt and forged it. As a child subreaper this process
    inherits every orphan of the lane, setsid or not, and SIGKILLs them before it exits."""
    argv = list(a.argv)
    if argv and argv[0] == "--":
        argv = argv[1:]
    if not argv:
        fail(EX_USAGE, "supervise: no command after --")
    lib = _libc()
    sub = bool(lib is not None and lib.prctl(PR_SET_CHILD_SUBREAPER, 1, 0, 0, 0) == 0)

    def on_signal(signum, _frame):
        n = kill_descendants()
        print(json.dumps({"ok": False, "supervise": "signalled", "signal": signum,
                          "subreaper": sub, "stragglers_killed": n}), flush=True)
        os._exit(128 + signum)

    # Installed BEFORE the child exists: a TERM in between would kill this process with its
    # default action and hand the lane's orphans to init.
    for s in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(s, on_signal)
    proc = subprocess.Popen(argv)
    rc = proc.wait()
    rc = 128 - rc if rc < 0 else rc
    n = kill_descendants()
    # One line: this lands in the job's `out` log after adapters' own line.
    emit({"ok": rc == 0, "supervise": "exited", "rc": rc, "subreaper": sub,
          "stragglers_killed": n}, rc if 0 <= rc < 256 else EX_FAIL, indent=None)


# ---------------------------------------------------------------- state
def _dispatch_in_flight(p: dict) -> bool | None:
    """None: no dispatch marker. True: its dispatcher is alive. False: it died mid-dispatch."""
    try:
        m = json.loads(p["marker"].read_text("utf-8"))
    except OSError:
        return None
    except json.JSONDecodeError:
        return True  # written atomically, so unreadable means racing its own write
    return job._alive(int(m.get("pid") or 0), str(m.get("start") or ""))


def lane_status(root: Path, lid: str, meta: dict | None = None) -> dict:
    """State from the job receipt, adapters' report and /proc -- never from the agent's words.

    running  the job wrapper is alive, a dispatch is still in flight, or ANY process of the
             lane's session is still alive (a receipt with live stragglers is not finished)
    done     receipt rc 0 AND the normalised report says done AND no lane process is alive
    timeout  the lane outran --timeout-s (adapters killed it) or the job backstop fired (rc 124)
    failed   finished any other way: not done, killed, no report, or receipt/report disagree
    lost     no receipt and no process: hard-killed, or the box went away
    """
    meta = meta if meta is not None else load_meta(root, lid)
    p = lane_paths(root, lid)
    js = job.status(p["state"], JOB_ID)
    out = {"id": lid, "state": "lost", "rc": js.get("rc"), "report_status": None,
           "job_state": js["state"], "timed_out": False,
           "worktree": meta.get("worktree"), "branch": meta.get("branch"),
           "report": str(p["report"])}
    if js["state"] == "running":
        out["state"] = "running"
        return out
    if js["state"] in ("absent", "lost"):
        fl = _dispatch_in_flight(p)
        if fl is True:
            out["state"] = "running"
            out["why"] = "dispatch is still in flight: the lane is being created"
            return out
        if fl is False:
            out["why"] = "the dispatcher died before the lane was spawned"
    if js["state"] != "absent":
        done = {}
        try:
            done = json.loads((p["job"] / "done.json").read_text())
        except (OSError, json.JSONDecodeError):
            pass
        not_after = done.get("finished_at") if js["state"] == "done" else None
        alive = lingering(int(js.get("pid") or 0), not_after)
        if alive:
            out["state"] = "running"
            out["lingering"] = len(alive)
            out["why"] = (f"{len(alive)} process(es) of the lane's session are still alive"
                          + (" after its receipt: it is still writing" if js["state"] == "done"
                             else ": the job wrapper is gone but the lane tree is not"))
            return out
    if js["state"] != "done":
        return out  # absent / lost / forged: no trustworthy receipt
    rep = read_report(p["report"])
    rs = rep.get("status") if rep else None
    meta_rep = (rep or {}).get("_meta") or {}
    out["report_status"] = rs
    out["timed_out"] = bool(meta_rep.get("timed_out")) or js["rc"] == 124
    if out["timed_out"]:
        out["state"] = "timeout"
    elif rs == "done" and js["rc"] == 0:
        out["state"] = "done"
    else:
        out["state"] = "failed"
        if rep is None and js["rc"] == 75:
            out["why"] = ("the lane never started: another writer owned its worktree when it "
                          "tried to claim it (rc 75)")
        elif rep is None:
            out["why"] = "the job finished but adapters.py wrote no report"
        elif rs == "done":
            out["why"] = f"report says done but the receipt says rc {js['rc']}: not trusted"
    return out


# ---------------------------------------------------------------- dispatch
def cmd_dispatch(a) -> None:
    check_id(a.id)
    owned = [o.strip() for o in (a.owned or []) if o and o.strip()]
    if not owned:
        fail(EX_USAGE, "at least one --owned path is required: a lane with no exclusive paths "
                       "cannot be audited")
    bad = owned_problems(owned)
    if bad:
        fail(EX_USAGE, "; ".join(bad), problems=bad)
    if a.max_turns is not None and a.max_turns < MIN_MAX_TURNS:
        fail(EX_DATAERR, f"--max-turns {a.max_turns} is below the minimum of {MIN_MAX_TURNS}: "
                         "the lane contract and the forced final report cost turns of their own, "
                         "so a lower cap records finished work as partial (measured: 8 ended "
                         "partial with the work written). Use 20 or more for real work.")
    root = repo_root(a.root)
    try:
        objective = Path(a.objective_file).read_text("utf-8").strip()
    except OSError as e:
        fail(EX_USAGE, f"cannot read --objective-file: {e}")
    if not objective:
        fail(EX_USAGE, "--objective-file is empty")
    # BEFORE anything is created: a lane whose harness is missing would spawn, fail inside the
    # job, and leave a worktree and a branch behind for a run that could never have happened.
    claude = shutil.which("claude")
    if not claude:
        fail(EX_NOCLAUDE, "no `claude` binary on PATH; nothing was created")

    cp = _git(root, "rev-parse", "--verify", "--quiet", f"{a.base}^{{commit}}")
    if cp.returncode != 0 or not cp.stdout.strip():
        fail(EX_USAGE, f"--base {a.base!r} does not name a commit in {root}")
    base = cp.stdout.strip()

    p = lane_paths(root, a.id)
    in_use = []
    if p["state"].exists():
        in_use.append(f"state dir {p['state']}")
    if p["worktree"].exists():
        in_use.append(f"worktree {p['worktree']}")
    if _git(root, "show-ref", "--verify", "--quiet", f"refs/heads/{p['branch']}").returncode == 0:
        in_use.append(f"branch {p['branch']}")
    if in_use:
        fail(EX_CANTCREAT, f"lane id {a.id!r} is already in use ({'; '.join(in_use)}); ids are "
                           "never reused -- pick a fresh one")

    wt_rel = (WT_REL / f"claude-{a.id}").as_posix()
    worker = {"harness": "claude-code", "model": a.model, "effort": a.effort,
              "timeout_s": a.timeout_s}
    if a.max_turns is not None:
        worker["max_turns"] = a.max_turns
    spec = adapters.normalize_spec({
        "version": "2", "objective": objective, "base_ref": base,
        "worktree_root": WT_REL.as_posix(), "terminal_layout": "detached",
        "lanes": [{"id": a.id, "objective": objective, "owned_paths": owned,
                   "positive_cmd": a.positive, "negative_control_cmd": a.negative,
                   "negative_expect": a.negative_expect, "worktree": wt_rel,
                   "worker": worker}]})
    # adapters' own validator first, so its refusals (schema, the no-real-negative rule) read
    # in its own words; then the static vacuity shapes it does not cover.
    errs = adapters.validate_spec(spec) + vacuous_reasons(a.positive, a.negative, a.negative_expect)
    if errs:
        fail(EX_DATAERR, "lane refused before anything was created: " + "; ".join(errs),
             problems=errs)
    lane = adapters.merged_lane(spec, a.id)

    # ---- side effects start here; every failure below rolls back what it created
    try:
        p["state"].mkdir(parents=True, exist_ok=False)  # atomic claim of the id
    except FileExistsError:
        fail(EX_CANTCREAT, f"lane id {a.id!r} was claimed concurrently")

    def rollback() -> None:
        # The branch was verified absent above and the state-dir mkdir is the id's atomic claim,
        # so anything under this branch name was created by THIS dispatch -- including by a
        # `git worktree add -b` that created the branch and then failed. Always remove it.
        if p["worktree"].exists():
            _git(root, "worktree", "remove", "--force", str(p["worktree"]))
        _git(root, "worktree", "prune")
        _git(root, "branch", "-D", p["branch"])
        shutil.rmtree(p["state"], ignore_errors=True)

    try:
        # While this marker exists and its dispatcher lives, status reads `running`, not `lost`:
        # the lane has a meta.json but no job yet.
        _atomic_write(p["marker"], json.dumps({"pid": os.getpid(),
                                               "start": git_lock._proc_start(os.getpid())}))
        meta = {"schema": 2, "id": a.id, "branch": p["branch"], "worktree": str(p["worktree"]),
                "base": base, "base_ref": a.base, "created_at": int(time.time()),
                "model": a.model, "effort": a.effort, "max_turns": lane["worker"]["max_turns"],
                "timeout_s": a.timeout_s, "owned_paths": owned, "positive_cmd": a.positive,
                "negative_control_cmd": a.negative, "negative_expect": a.negative_expect,
                "claude": claude, "dispatcher_pid": os.getpid(), "pin": None}
        _atomic_write(p["meta"], json.dumps(meta, indent=2) + "\n")
        (p["state"] / "objective.md").write_text(objective + "\n", "utf-8")
        _atomic_write(p["spec"], json.dumps(spec, indent=2) + "\n")
        _atomic_write(p["lane"], json.dumps(lane, indent=2) + "\n")
        ensure_excluded(root)
        wt = adapters.git(root, "worktree", "add", "--quiet", "-b", p["branch"],
                          str(p["worktree"]), base)
        if wt.returncode != 0:
            rollback()
            fail(EX_CANTCREAT, f"git worktree add failed: {(wt.stderr or wt.stdout).strip()}")

        baseline = baseline_snapshot(root)
        _atomic_write(p["baseline"], json.dumps(baseline, indent=2, sort_keys=True) + "\n")
        pin = compute_pin(lane, base, baseline)
        meta["pin"] = pin
        _atomic_write(p["meta"], json.dumps(meta, indent=2) + "\n")

        lock = subprocess.run([sys.executable, str(LOCK_PY), "path", "--wt", str(p["worktree"])],
                              capture_output=True, text=True).stdout.strip()
        if not lock:
            rollback()
            fail(EX_SOFTWARE, "could not resolve the worktree owner lock path")
        q = shlex.quote
        py = q(sys.executable)
        # Same shape as devloop.sh's lane command: fd 9 on the owner lock is held by the lane
        # tree for as long as it runs, so a second dev-loop writer (or a gate) is refused, not
        # raced. `supervise` sits between the shell and adapters.py so that nothing the lane
        # started outlives it (see cmd_supervise).
        cmd = (f"exec 9>>{q(lock)}; "
               f"{py} {q(str(LOCK_PY))} claim --wt {q(str(p['worktree']))} --fd 9 "
               f"--who {q('claude-lane:' + a.id)} --pid $$ || exit 75; "
               f"{py} {q(str(SELF))} supervise -- "
               f"{py} {q(str(ADAPTERS))} run --lane {q(str(p['lane']))} "
               f"--wt {q(str(p['worktree']))} --report {q(str(p['report']))} "
               f"--log {q(str(p['log']))} --skill {q(str(SKILL))}; "
               f"rc=$?; exec 9>&-; exit $rc")
        job.spawn(p["state"], JOB_ID, ["sh", "-c", cmd], p["worktree"],
                  budget_s=int(a.timeout_s) + JOB_GRACE_S, label=f"claude lane {a.id}",
                  replay="fail")
        p["marker"].unlink(missing_ok=True)
    except SystemExit:
        raise
    except Exception as e:  # noqa: BLE001 -- anything here means the lane never started
        rollback()
        fail(EX_SOFTWARE, f"lane never started: {type(e).__name__}: {e}")

    dirty = bool(_git(root, "status", "--porcelain", "--untracked-files=no").stdout.strip())
    emit({"ok": True, "id": a.id,
          "pin": pin,
          "pin_note": ("pass this to `gate --pin`; it is the one copy of the gate definition a "
                       "lane cannot rewrite"),
          "job": {"root": str(p["state"]), "id": JOB_ID, "dir": str(p["job"])},
          "worktree": str(p["worktree"]), "branch": p["branch"], "base": base,
          "report": str(p["report"]), "log": str(p["log"]),
          "job_out": str(p["job"] / "out"), "job_err": str(p["job"] / "err"),
          "state_dir": str(p["state"]), "model": a.model, "effort": a.effort,
          "max_turns": lane["worker"]["max_turns"], "timeout_s": a.timeout_s,
          "containment": containment(),
          "base_tree_dirty": dirty,
          "note": ("the lane branched from commit " + base[:12] + "; uncommitted base-tree "
                   "edits are NOT in its worktree") if dirty else ""}, EX_OK)


# ---------------------------------------------------------------- status / wait / list
def cmd_status(a) -> None:
    root = repo_root(a.root)
    st = lane_status(root, a.id)
    emit({"ok": True, **st}, EX_OK)


def wait_exit(lanes: list[dict]) -> int:
    if lanes and all(l["state"] == "done" and l["report_status"] == "done" for l in lanes):
        return EX_OK
    if any(l["state"] == "timeout" for l in lanes):
        return EX_TIMEOUT
    return EX_FAIL


def cmd_wait(a) -> None:
    root = repo_root(a.root)
    ids = list(dict.fromkeys(a.id))
    metas = {i: load_meta(root, i) for i in ids}  # unknown id -> 64 before any waiting
    t0 = time.time()
    deadline = t0 + max(0, a.budget_s)
    while True:
        lanes = [lane_status(root, i, metas[i]) for i in ids]
        if all(l["state"] in TERMINAL for l in lanes):
            timed_out = False
            break
        if time.time() >= deadline:
            timed_out = True
            for l in lanes:
                if l["state"] not in TERMINAL:
                    # The WAIT ran out, the lane did not finish. Reported as timeout -- never as
                    # a pass -- and marked still_running so nobody gates a live worktree.
                    l["state"] = "timeout"
                    l["still_running"] = True
            break
        time.sleep(max(0.2, a.interval_s))
    for l in lanes:
        l.setdefault("still_running", False)
    code = wait_exit(lanes)
    emit({"ok": code == EX_OK, "lanes": lanes, "wait_timed_out": timed_out,
          "elapsed_s": round(time.time() - t0, 1), "budget_s": a.budget_s}, code)


def cmd_list(a) -> None:
    root = repo_root(a.root)
    base = root / STATE_REL
    lanes = []
    if base.is_dir():
        for d in sorted(base.iterdir()):
            if not (d.is_dir() and ID_RE.fullmatch(d.name) and (d / "meta.json").exists()):
                continue
            # One unreadable meta.json names that lane; it never hides the others.
            meta, why = read_meta(root, d.name)
            if meta is None:
                lanes.append({"id": d.name, "state": "unknown", "error": why})
                continue
            try:
                lanes.append(lane_status(root, d.name, meta))
            except Exception as e:  # noqa: BLE001 -- same rule for anything else on disk
                lanes.append({"id": d.name, "state": "unknown", "error": f"{type(e).__name__}: {e}"})
    emit({"ok": True, "root": str(root), "count": len(lanes), "lanes": lanes}, EX_OK)


# ---------------------------------------------------------------- audit
def _index_copy(wt: Path) -> tuple[str, Path | None]:
    ip = _git(wt, "rev-parse", "--git-path", "index").stdout.strip()
    idx = Path(ip) if Path(ip).is_absolute() else (wt / ip)
    fd, tmp = tempfile.mkstemp(prefix="claude-lane-index-")
    os.close(fd)
    if idx.is_file():
        shutil.copyfile(idx, tmp)
        return tmp, idx
    os.unlink(tmp)
    return tmp, None


def index_flagged(wt: Path) -> list[str]:
    """Paths whose index entry carries skip-worktree (S) or assume-unchanged (lowercase) AND
    exist in the worktree. Either flag makes git status -- and so every porcelain-based audit
    -- ignore an edit to the file, while the controls still run on it. A sparse-checkout entry
    is absent from the worktree, so it is not counted."""
    out = []
    for ent in _git(wt, "ls-files", "-v", "-z").stdout.split("\0"):
        if len(ent) < 3:
            continue
        tag, path = ent[0], ent[2:]
        if (tag == "S" or tag.islower()) and os.path.lexists(wt / path):
            out.append(path)
    return sorted(out)


def worktree_changes(wt: Path, base: str) -> dict:
    """Every path of the worktree that differs from `base` -- committed, staged, unstaged,
    untracked, and edits hidden behind index flags -- plus a diff stat, WITHOUT touching the
    lane's real index. A throwaway copy of the index (carrying the stat cache, so only changed
    files are hashed) has its flags cleared, is staged with --all and diffed against the base
    with --no-renames, so a rename counts as its source AND its destination."""
    hidden = index_flagged(wt)
    tmp, real = _index_copy(wt)
    env = {"GIT_INDEX_FILE": tmp}
    try:
        if real is None:
            _git(wt, "read-tree", "HEAD", env=env)
        if hidden:
            z = "".join(h + "\0" for h in hidden)
            # One flag per call: measured (git 2.43), --no-skip-worktree and
            # --no-assume-unchanged in ONE update-index call cleared only the last one.
            _git(wt, "update-index", "--no-skip-worktree", "-z", "--stdin", env=env, input=z)
            _git(wt, "update-index", "--no-assume-unchanged", "-z", "--stdin", env=env, input=z)
        _git(wt, "add", "--all", "--", ".", env=env)
        names = _git(wt, "diff", "--cached", "--name-only", "-z", "--no-renames",
                     "--no-textconv", "--no-ext-diff", base, env=env)
        stat = _git(wt, "diff", "--cached", "--stat", "--no-textconv", "--no-ext-diff", base,
                    env=env).stdout
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass
    return {"paths": sorted({n for n in names.stdout.split("\0") if n}), "stat": stat,
            "hidden": hidden, "ok": names.returncode == 0}


def git_state_problems(wt: Path, base: str, branch: str) -> tuple[list[str], int | None]:
    """A lane never commits, stages or switches branch. Anything else means the manager's merge
    recipe (stage the owned paths, commit, merge the branch) would carry something the audit
    did not see -- measured: a committed README edit, invisible to `git status`, merged."""
    out = []
    sym = _git(wt, "symbolic-ref", "-q", "HEAD").stdout.strip()
    if sym != f"refs/heads/{branch}":
        out.append(f"HEAD is {sym or 'detached'}, not refs/heads/{branch}: the lane switched branch")
    head = _git(wt, "rev-parse", "--verify", "--quiet", "HEAD").stdout.strip()
    ahead = None
    if head != base:
        a_ = _git(wt, "rev-list", "--count", f"{base}..HEAD").stdout.strip()
        b_ = _git(wt, "rev-list", "--count", f"HEAD..{base}").stdout.strip()
        ahead = int(a_) if a_.isdigit() else None
        out.append(f"the lane moved its branch: HEAD {head[:12] or '?'} is {a_ or '?'} commit(s) "
                   f"ahead of and {b_ or '?'} behind its base {base[:12]} -- a lane never "
                   "commits, and a committed edit is invisible to git status")
    else:
        ahead = 0
    staged = [s for s in _git(wt, "diff", "--cached", "--name-only", "-z", "HEAD").stdout.split("\0") if s]
    if staged:
        out.append("the lane staged " + ", ".join(staged[:10]) + " -- a lane never runs git add, "
                   "and the merge commit would carry whatever is staged")
    return out, ahead


# ---------------------------------------------------------------- gate / collect / kill
def _tail(s: str, n: int = 2000) -> str:
    return s[-n:] if s else ""


def load_gate_definition(p: dict, meta: dict, pin_arg: str | None) -> tuple[dict, dict, list[str]]:
    """The lane definition and baseline, verified against the pin. Never trusted unverified:
    lane.json sits two directories above the lane's own worktree, and a lane rewrote it."""
    problems = []
    try:
        lane = json.loads(p["lane"].read_text("utf-8"))
        baseline = json.loads(p["baseline"].read_text("utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return {}, {}, [f"lane.json or baseline.json is missing or unreadable ({e})"]
    now = compute_pin(lane, meta.get("base"), baseline)
    if not meta.get("pin"):
        problems.append("meta.json carries no pin")
    elif now != meta["pin"]:
        problems.append("lane.json, baseline.json or the base commit no longer match the pin "
                        "meta.json recorded at dispatch: the gate definition was rewritten")
    if pin_arg and now != pin_arg.strip():
        problems.append("lane.json, baseline.json or the base commit do not match the --pin the "
                        "dispatcher returned: the gate definition was rewritten")
    if lane.get("id") != meta.get("id"):
        problems.append(f"lane.json names lane {lane.get('id')!r}, not {meta.get('id')!r}")
    return lane, baseline, problems


def cmd_gate(a) -> None:
    root = repo_root(a.root)
    meta = load_meta(root, a.id)
    p = lane_paths(root, a.id)
    st = lane_status(root, a.id, meta)
    if st["state"] == "running":
        fail(EX_BUSY, f"lane {a.id} is still running: gating a worktree an agent is still "
                      "writing audits a moving target. wait for it, or kill it first.", lane=st)
    lane, baseline, tamper = load_gate_definition(p, meta, a.pin)
    common = {"id": a.id, "lane_state": st["state"], "report_status": st["report_status"],
              "worktree": str(p["worktree"]), "branch": p["branch"], "base": meta.get("base"),
              "pinned": bool(a.pin)}
    if tamper:
        emit({"ok": False, "mergeable": False, "tampered": True,
              "why": "TAMPERED: " + "; ".join(tamper) + " -- no control was run; never merge",
              "problems": tamper, **common}, EX_VACUOUS)
    wt = p["worktree"]
    if not wt.is_dir():
        fail(EX_FAIL, f"worktree {wt} is missing", lane=st)
    base = meta["base"]
    # FIRST, before any git command runs in the lane's worktree: git executes what hooks,
    # config (filter/textconv drivers, fsmonitor, hooksPath) and info/ tell it to, so a lane
    # that planted one would have the audit itself run its code in the manager's context.
    meta_changed = _changed_keys(baseline.get("git_meta") or {}, git_meta_digest(root))
    if meta_changed:
        emit({"ok": False, "mergeable": False, "tampered": False,
              "why": ("git metadata changed during the lane (hooks, config and info/ run or steer "
                      "the manager's git commands and merge): " + ", ".join(meta_changed)
                      + " -- nothing was run in the lane's worktree; never merge"),
              "git_meta_changed": meta_changed, **common}, EX_FAIL)
    lockp = subprocess.run([sys.executable, str(LOCK_PY), "path", "--wt", str(wt)],
                           capture_output=True, text=True).stdout.strip()
    if not lockp:
        fail(EX_FAIL, f"could not resolve the owner lock for {wt}", lane=st)
    lane_done = st["state"] == "done"
    # Hold the owner lock for the whole gate, as devloop.sh does: the negative control plants
    # and restores a file, and a second writer turns that into "control is broken".
    with open(Path(lockp), "a") as fh, tempfile.TemporaryDirectory(prefix="claude-lane-gate-") as td:
        if git_lock.claim(wt, fh.fileno(), f"claude-lane-gate:{a.id}", os.getpid()) != 0:
            fail(EX_BUSY, f"worktree {wt} is owned by another writer: {git_lock.owner(wt)}",
                 lane=st)
        # adapters reads the VERIFIED definition from a copy outside the lane's reach.
        trusted = Path(td) / "lane.json"
        trusted.write_text(json.dumps(lane, indent=2), "utf-8")
        p["gate"].mkdir(parents=True, exist_ok=True)

        git_problems, ahead = git_state_problems(wt, base, p["branch"])
        ch = worktree_changes(wt, base)
        owned_paths = lane.get("owned_paths") or []
        not_owned = [x for x in ch["paths"] if not is_owned_path(x, owned_paths)]
        prot = [x for x in ch["paths"] if protected(x)]
        violations = sorted(set(not_owned) | set(prot))
        audit = {"ok": not (git_problems or ch["hidden"] or violations) and ch["ok"],
                 "git_state": git_problems, "commits_ahead": ahead,
                 "hidden_by_index_flags": ch["hidden"], "violations": violations,
                 "protected": prot, "changed_paths": ch["paths"]}

        py = sys.executable
        ow = subprocess.run([py, str(ADAPTERS), "owned", "--lane", str(trusted), "--wt", str(wt)],
                            capture_output=True, text=True)
        m = re.search(r"OWNERSHIP VIOLATION: (.*)", ow.stderr + ow.stdout)
        ad_viol = [x.strip() for x in m.group(1).split(",") if x.strip()] if m else []
        owned = {"rc": ow.returncode, "ok": ow.returncode == 0 and not violations,
                 "violations": sorted(set(ad_viol) | set(violations)),
                 "output": _tail(ow.stdout + ow.stderr)}

        base_moved = _changed_keys(baseline.get("base_tree") or {}, base_tree_digest(root))

        clean = audit["ok"] and owned["ok"]
        if not lane_done:
            gate = {"rc": None, "ok": False, "skipped": (
                f"the lane's state is {st['state']} (report status {st['report_status']}): the "
                "controls are never run on a lane that did not reach done -- a negative control "
                "that does not restore the tree would destroy work nobody staged")}
        elif not clean:
            gate = {"rc": None, "ok": False, "skipped": (
                "the audit failed: the controls are not run on a tree that holds edits outside "
                "the lane's owned paths or git state the lane was not allowed to create")}
        else:
            gp = subprocess.run([py, str(ADAPTERS), "gate", "--lane", str(trusted), "--wt", str(wt),
                                 "--run", str(p["gate"]), "--root", str(root)],
                                capture_output=True, text=True)
            text = gp.stdout + gp.stderr
            gate = {"rc": gp.returncode, "ok": gp.returncode == 0,
                    "vacuous": gp.returncode == 2,
                    "base_leak": "BASE TREE LEAKAGE" in text,
                    "logs": str(p["gate"]), "output": _tail(text)}

    reasons = []
    if git_problems:
        reasons += git_problems
    if ch["hidden"]:
        reasons.append("index flags (skip-worktree / assume-unchanged) hide edits to "
                       + ", ".join(ch["hidden"]))
    if prot:
        reasons.append("the lane changed protected paths: " + ", ".join(prot))
    if owned["violations"]:
        reasons.append("ownership audit failed: " + ", ".join(owned["violations"]))
    if not ch["ok"]:
        reasons.append("git could not list the worktree's changes against its base")
    if reasons:
        code, why = EX_FAIL, "; ".join(reasons)
    elif not lane_done:
        code, why = EX_FAIL, (f"the lane's state is {st['state']} (report status "
                              f"{st['report_status']}): a lane that did not reach done is never "
                              "merged, and its controls were not run")
    elif gate["rc"] == 2:
        code, why = EX_VACUOUS, ("VACUOUS: " + ("the base tree moved during the gate"
                                              if gate["base_leak"] else
                                              "the negative control did not fail for the named "
                                              "reason, or did not restore the tree") +
                                 " -- never merge")
    elif gate["rc"] != 0:
        code, why = EX_FAIL, "two-sided gate failed"
    else:
        code, why = EX_OK, "ownership clean, positive passed, negative failed for the named reason"
    warnings = []
    if base_moved:
        warnings.append("base_moved: these base-tree paths changed while the lane ran: "
                        + ", ".join(base_moved[:20]) + ". Other agents editing the base tree "
                        "explain this; if none of them touched these paths, the lane wrote "
                        "outside its worktree -- do not merge.")
    if not a.pin:
        warnings.append("gate ran without --pin: a lane that rewrote lane.json AND meta.json "
                        "consistently would not be detected. Pass the pin dispatch returned.")
    emit({"ok": code == EX_OK, "mergeable": code == EX_OK, "why": why, "tampered": False,
          **common, "audit": audit, "owned": owned, "git_meta_changed": [],
          "base_moved": base_moved, "warnings": warnings, "gate": gate}, code)


def cmd_collect(a) -> None:
    root = repo_root(a.root)
    meta = load_meta(root, a.id)
    p = lane_paths(root, a.id)
    st = lane_status(root, a.id, meta)
    wt = p["worktree"]
    if not wt.is_dir():
        fail(EX_FAIL, f"worktree {wt} is missing", lane=st)
    base = meta.get("base", "HEAD")
    ahead = _git(wt, "rev-list", "--count", f"{base}..HEAD").stdout.strip()
    try:
        baseline = json.loads(p["baseline"].read_text("utf-8"))
    except (OSError, json.JSONDecodeError):
        baseline = {}
    meta_changed = _changed_keys(baseline.get("git_meta") or {}, git_meta_digest(root))
    # Staging a copy of the worktree runs clean filters; not while git's config may be planted.
    ch = (worktree_changes(wt, base) if not meta_changed else
          {"stat": "", "paths": [], "hidden": [], "ok": False})
    emit({"ok": True, "id": a.id, "state": st["state"], "report_status": st["report_status"],
          "git_meta_changed": meta_changed,
          "still_running": st["state"] == "running",
          "report": read_report(p["report"]),
          "diff_stat": ch["stat"],
          "changed_paths": ch["paths"],
          "hidden_by_index_flags": ch["hidden"],
          "commits_ahead": int(ahead) if ahead.isdigit() else None,
          "base": base, "branch": p["branch"], "worktree": str(wt),
          "log": str(p["log"])}, EX_OK)


def cmd_kill(a) -> None:
    root = repo_root(a.root)
    meta = load_meta(root, a.id)
    p = lane_paths(root, a.id)
    n = job.kill(p["state"], JOB_ID, "TERM")
    t0 = time.time()
    while time.time() - t0 < a.grace_s and lane_status(root, a.id, meta)["state"] == "running":
        time.sleep(0.5)
    if lane_status(root, a.id, meta)["state"] == "running":
        n += job.kill(p["state"], JOB_ID, "KILL")
        time.sleep(1)
    st = lane_status(root, a.id, meta)
    code = EX_OK if st["state"] != "running" else EX_BUSY
    emit({"ok": code == EX_OK, "signalled": n, **st}, code)


# ---------------------------------------------------------------- main
def main() -> None:
    ap = _Parser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("dispatch", help="create the lane and spawn it detached; returns at once")
    d.add_argument("--root", required=True); d.add_argument("--id", required=True)
    d.add_argument("--objective-file", required=True)
    d.add_argument("--owned", action="append", default=[])
    d.add_argument("--positive", required=True); d.add_argument("--negative", required=True)
    d.add_argument("--negative-expect", required=True)
    d.add_argument("--model", default="opus"); d.add_argument("--effort", default="xhigh")
    d.add_argument("--max-turns", type=int)
    d.add_argument("--timeout-s", type=int, default=1800)
    d.add_argument("--base", default="HEAD")
    d.set_defaults(f=cmd_dispatch)

    for name, f in (("status", cmd_status), ("gate", cmd_gate), ("collect", cmd_collect)):
        s = sub.add_parser(name); s.add_argument("--root", required=True)
        s.add_argument("--id", required=True); s.set_defaults(f=f)
        if name == "gate":
            s.add_argument("--pin", help="the pin dispatch returned for this lane")

    w = sub.add_parser("wait"); w.add_argument("--root", required=True)
    w.add_argument("--id", action="append", required=True)
    w.add_argument("--budget-s", type=int, default=5400)
    w.add_argument("--interval-s", type=float, default=2.0)
    w.set_defaults(f=cmd_wait)

    l = sub.add_parser("list"); l.add_argument("--root", required=True); l.set_defaults(f=cmd_list)

    k = sub.add_parser("kill"); k.add_argument("--root", required=True)
    k.add_argument("--id", required=True); k.add_argument("--grace-s", type=int, default=15)
    k.set_defaults(f=cmd_kill)

    sv = sub.add_parser("supervise", help="internal: run ARGV as the lane's process-tree supervisor")
    sv.add_argument("argv", nargs=argparse.REMAINDER)
    sv.set_defaults(f=cmd_supervise)

    a = ap.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
