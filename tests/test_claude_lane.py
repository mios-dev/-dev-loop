#!/usr/bin/env python3
"""
Controls for scripts/claude_lane.py: nested Claude Code CLI subagents, run as full dev-loop
lanes, for an Antigravity /teamwork-preview manager.

The defect these guard
----------------------
An AGY teamwork run is lane-less, and its agents have a run_command tool, so the obvious way to
"use a Claude subagent" is `claude -p ...` from run_command. Every property the loop depends on
is missing from that: run_command backgrounds anything past ~10s (WaitMsBeforeAsync is clamped,
measured) and the background dies with the turn; the subagent edits the base tree with no owned
paths; and its "done" is a sentence. claude_lane.py gives it the lane contract instead, so the
controls below are about exactly those three properties, from both sides:

  LIFETIME   dispatch returns while the lane is still running (a fake that sleeps), the lane
             finishes without its dispatcher, and several lanes overlap in time. Nothing the
             lane started outlives it: a detached child is killed before the receipt, a setsid'd
             forger cannot rewrite the receipt, and a live straggler reads `running`, never
             `done` or `lost`.
  ISOLATION  an edit outside the owned paths fails the gate and is NAMED -- also when it was
             committed, staged, renamed, or hidden behind an index flag; a lane cannot rewrite
             its own gate definition, plant a git hook, own a contract file, or claim an id, a
             worktree or a branch that is already in use; an id cannot walk out of .devloop/.
  PROOF      `done` needs the shell-written receipt AND the adapter's report; a timeout -- the
             wait's budget or the lane's own --timeout-s -- is exit 3 and never a pass; a
             negative control that cannot fail is refused at dispatch, and one that passes at
             the gate is exit 2 (VACUOUS); a lane that did not reach done never has its controls
             run, so a destructive control cannot eat unstaged work.

The `claude` used here is a FAKE on PATH (a small python script): what is under test is the
lane machinery, not the model. A real nested `claude -p` was measured separately (it
authenticates in this container, rc 0, also with the parent session's identity stripped).

Run: python3 tests/test_claude_lane.py
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
CL = SCRIPTS / "claude_lane.py"
HOST = SCRIPTS / "agy_host.sh"
PROMPTS = SCRIPTS / "prompt.py"
TEMPLATE = ROOT / "skills" / "dev-loop" / "assets" / "templates" / "prompts" / "nested-claude-lanes.md"
sys.path.insert(0, str(SCRIPTS))

import prompt as P  # noqa: E402
import claude_lane as CLM  # noqa: E402
import job as JOB  # noqa: E402
import git_lock  # noqa: E402

FAILURES: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name}{': ' + detail if detail else ''}")
        FAILURES.append(name)


# A fake `claude` that speaks just enough of the measured `claude -p --output-format json`
# envelope for adapters.py to normalise. It works out its lane id from the lane prompt, records
# the argv it was given and the NAMES (never values) of the CLAUDE* variables it inherited, and
# then behaves according to:
#   FAKE_CLAUDE_MODE    ok (default) | stray (also edits README.md, which no lane owns) | hang
#   FAKE_CLAUDE_SLEEP   seconds to sleep first; the lane's [start, end] wall-clock span is then
#                       written to $FAKE_CLAUDE_LOG/<lane>.span, so a test can ask whether two lanes
#                       ran AT THE SAME TIME rather than infer it from a load-sensitive total
#   FAKE_CLAUDE_NOWORK  set: do NOT write DONE into src/<id>.txt
#   FAKE_CLAUDE_SH      a shell snippet run in the worktree (env: LANE, STATE = abs state dir)
#   FAKE_CLAUDE_PY      python exec'd in-process with `lane`, `state` (Path), json, Path
#   FAKE_CLAUDE_STATUS  the status it reports (default done)
FAKE_CLAUDE = r'''#!/usr/bin/env python3
import json, os, re, subprocess, sys, time
from pathlib import Path
argv = sys.argv[1:]
prompt = argv[argv.index("-p") + 1] if "-p" in argv else ""
m = re.search(r"lane id: (\S+)", prompt)
lane = m.group(1) if m else "unknown"
state = Path("../../native/claude/" + lane).resolve()
log = os.environ.get("FAKE_CLAUDE_LOG")
if log:
    Path(log).mkdir(parents=True, exist_ok=True)
    (Path(log) / (lane + ".argv.json")).write_text(json.dumps(argv))
    (Path(log) / (lane + ".env.json")).write_text(json.dumps(sorted(k for k in os.environ if k.startswith("CLAUDE"))))
mode = os.environ.get("FAKE_CLAUDE_MODE", "ok")
t_span0 = time.time()
time.sleep(float(os.environ.get("FAKE_CLAUDE_SLEEP", "0")))
if mode == "hang":
    time.sleep(3600)
if log:
    (Path(log) / (lane + ".span")).write_text(f"{t_span0} {time.time()}")
if not os.environ.get("FAKE_CLAUDE_NOWORK"):
    Path("src").mkdir(exist_ok=True)
    Path("src", lane + ".txt").write_text("DONE\n")
if mode == "stray":
    with open("README.md", "a") as f:
        f.write("an edit outside every owned path\n")
if os.environ.get("FAKE_CLAUDE_PY"):
    exec(os.environ["FAKE_CLAUDE_PY"], {"lane": lane, "state": state, "json": json, "Path": Path})
if os.environ.get("FAKE_CLAUDE_SH"):
    subprocess.run(["sh", "-c", os.environ["FAKE_CLAUDE_SH"]], env={**os.environ, "LANE": lane, "STATE": str(state)})
rep = {"status": os.environ.get("FAKE_CLAUDE_STATUS", "done"), "objective": "fake lane", "summary": "fake", "changed_paths": ["src/" + lane + ".txt"],
       "positive_controls": [], "negative_controls": [], "full_gate": {"cmd": "", "exit": 0},
       "phantoms_dismissed": [], "unverified": [], "contract_updates": [], "questions": [], "next": ""}
print(json.dumps({"type": "result", "subtype": "success", "is_error": False, "num_turns": 3,
                  "result": "ok", "structured_output": {"devloop_report": rep}}))
'''

# Waits for the lane's REAL receipt, then rewrites it and the report to read done. Started by a
# lane with setsid, so it is in a session of its own and outlives everything but a subreaper.
FORGER = r'''#!/bin/sh
st=$1
while [ ! -f "$st/job/exit" ]; do sleep 0.1; done
sleep 0.5
pid=$(cat "$st/job/pid")
printf '{"rc":0,"finished_at":1,"pid":%s}\n' "$pid" > "$st/job/done.json"
echo 0 > "$st/job/exit"
python3 -c "import json,sys;p=sys.argv[1]+'/report.json';d=json.load(open(p));d['status']='done';json.dump(d,open(p,'w'))" "$st"
touch "$st/FORGED"
'''


def git(repo: Path, *a: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(repo), *a], capture_output=True, text=True)


def make_repo(path: Path) -> Path:
    path.mkdir()
    g = lambda *a: subprocess.run(["git", "-C", str(path), *a], check=True,  # noqa: E731
                                  capture_output=True, text=True)
    g("-c", "init.defaultBranch=main", "init", "-q")
    g("config", "user.email", "t@example.invalid")
    g("config", "user.name", "t")
    (path / "README.md").write_text("fixture\n")
    (path / "AGENTS.md").write_text("the constitution\n")
    (path / "src").mkdir()
    (path / "src" / "seed.txt").write_text("seed\n")
    g("add", "README.md", "AGENTS.md", "src/seed.txt")
    g("commit", "-qm", "init")
    return path


class Ctx:
    def __init__(self, tmp: Path) -> None:
        self.tmp = tmp
        self.bin = tmp / "bin"
        self.bin.mkdir()
        fake = self.bin / "claude"
        fake.write_text(FAKE_CLAUDE)
        fake.chmod(0o755)
        self.forger = tmp / "forger.sh"
        self.forger.write_text(FORGER)
        self.forger.chmod(0o755)
        self.log = tmp / "argv"
        self.repo = make_repo(tmp / "repo")
        self.objective = tmp / "objective.md"
        self.objective.write_text("Write DONE into this lane's owned file so its positive control passes.\n")
        self.path_with_fake = f"{self.bin}{os.pathsep}{os.environ['PATH']}"
        self.pins: dict[str, str] = {}

    def run(self, *args: str, env: dict | None = None, path: str | None = None,
            timeout: int = 150) -> tuple[int, dict, float, str]:
        e = {**os.environ, "PATH": path if path is not None else self.path_with_fake,
             "FAKE_CLAUDE_LOG": str(self.log), **(env or {})}
        t0 = time.monotonic()
        cp = subprocess.run([sys.executable, str(CL), *args], capture_output=True, text=True,
                            env=e, timeout=timeout)
        el = time.monotonic() - t0
        try:
            doc = json.loads(cp.stdout)
        except json.JSONDecodeError:
            doc = {"_unparsed_stdout": cp.stdout[-500:]}
        return cp.returncode, doc, el, cp.stderr

    def dispatch(self, lid: str, *extra: str, env: dict | None = None, path: str | None = None,
                 owned: list[str] | None = None, positive: str | None = None,
                 negative: str | None = None, expect: str | None = None, root: Path | None = None):
        owned = owned if owned is not None else [f"src/{lid}.txt"]
        sent = "DEVLOOP-PLANTED-" + lid.upper()
        args = ["dispatch", "--root", str(root or self.repo), "--id", lid,
                "--objective-file", str(self.objective)]
        for o in owned:
            args += ["--owned", o]
        args += ["--positive", positive if positive is not None else f"grep -q DONE src/{lid}.txt",
                 "--negative", negative if negative is not None else f"grep -q DONE src/{sent}.txt",
                 "--negative-expect", expect if expect is not None else sent, *extra]
        out = self.run(*args, env=env, path=path)
        if out[0] == 0 and out[1].get("pin"):
            self.pins[lid] = out[1]["pin"]
        return out

    def wait(self, *ids: str, budget: int = 90, root: Path | None = None):
        a = ["wait", "--root", str(root or self.repo), "--budget-s", str(budget), "--interval-s", "0.3"]
        for i in ids:
            a += ["--id", i]
        return self.run(*a, timeout=budget + 60)

    def gate(self, lid: str, pin: bool = True):
        a = ["gate", "--root", str(self.repo), "--id", lid]
        if pin and lid in self.pins:
            a += ["--pin", self.pins[lid]]
        return self.run(*a)

    def lanes(self, specs: list[dict]) -> dict:
        """Dispatch every spec, THEN wait on all of them: the lanes run in parallel."""
        for s in specs:
            s = dict(s)
            lid = s.pop("id")
            rc, d, _, err = self.dispatch(lid, **s)
            check(f"{lid}: dispatched", rc == 0, f"rc={rc} {d} {err[-300:]}")
        rc, d, _, _ = self.wait(*[s["id"] for s in specs])
        return {"rc": rc, "doc": d}

    def artefacts(self, root: Path | None = None) -> tuple:
        root = root or self.repo
        st = root / ".devloop" / "native" / "claude"
        wt = root / ".devloop" / "worktrees"
        br = git(root, "for-each-ref", "refs/heads", "--format=%(refname:short)").stdout
        return (sorted(p.name for p in st.iterdir()) if st.is_dir() else [],
                sorted(p.name for p in wt.iterdir()) if wt.is_dir() else [],
                sorted(br.split()))

    def argv_of(self, lid: str) -> list[str]:
        f = self.log / f"{lid}.argv.json"
        return json.loads(f.read_text()) if f.is_file() else []

    def span_of(self, lid: str) -> tuple[float, float] | None:
        try:
            t0, t1 = (self.log / f"{lid}.span").read_text().split()
            return float(t0), float(t1)
        except (OSError, ValueError):
            return None

    def env_of(self, lid: str) -> list[str]:
        f = self.log / f"{lid}.env.json"
        return json.loads(f.read_text()) if f.is_file() else ["<fake never ran>"]

    def wt(self, lid: str) -> Path:
        return self.repo / ".devloop" / "worktrees" / f"claude-{lid}"

    def state(self, lid: str) -> Path:
        return self.repo / ".devloop" / "native" / "claude" / lid


def has_pair(argv: list[str], flag: str, val: str) -> bool:
    return any(argv[i] == flag and argv[i + 1] == val for i in range(len(argv) - 1))


def lane_of(doc: dict, lid: str) -> dict:
    return next((l for l in doc.get("lanes", []) if l.get("id") == lid), {})


def no_claude_path() -> str:
    return os.pathsep.join(d for d in os.environ["PATH"].split(os.pathsep)
                           if d and not os.access(os.path.join(d, "claude"), os.X_OK))


# ---------------------------------------------------------------- the hang lane (started first)
def test_timeout_is_not_a_pass_while_running(c: Ctx) -> None:
    """Started FIRST because its own --timeout-s is 30s (the lane schema's minimum): the other
    controls run while it hangs. Here: the WAIT's budget runs out on a live lane."""
    print("a wait that runs out of budget is a timeout, not a pass:")
    rc, d, el, err = c.dispatch("hang", "--timeout-s", "30", env={"FAKE_CLAUDE_MODE": "hang"})
    check("hang lane dispatched", rc == 0 and d.get("ok") is True, f"rc={rc} {d} {err[-300:]}")
    rc, d, _, _ = c.gate("hang")
    check("gate refuses a RUNNING lane (75), it does not audit a moving target",
          rc == 75 and "still running" in d.get("error", ""), f"rc={rc} {d}")
    rc, d, el, _ = c.run("wait", "--root", str(c.repo), "--id", "hang", "--budget-s", "3",
                         "--interval-s", "0.5")
    ln = lane_of(d, "hang")
    check("wait --budget-s 3 on a hanging lane exits 3", rc == 3, f"rc={rc} {d}")
    check("...reports state timeout", ln.get("state") == "timeout", str(ln))
    check("...and says the lane is STILL RUNNING (so nobody gates it)",
          ln.get("still_running") is True and d.get("wait_timed_out") is True, str(d))
    check("...and it really waited for its budget", el >= 2.5, f"returned after {el:.1f}s")
    check("...ok is false", d.get("ok") is False, str(d))
    rc, d, _, _ = c.run("status", "--root", str(c.repo), "--id", "hang")
    check("the wait did not kill the lane: status still running", d.get("state") == "running", str(d))
    own = subprocess.run([sys.executable, str(SCRIPTS / "git_lock.py"), "owner", "--wt", str(c.wt("hang"))],
                         capture_output=True, text=True)
    check("while it runs the lane HOLDS its worktree's owner lock (one writer per worktree)",
          own.returncode == 1 and "claude-lane:hang" in own.stdout, own.stdout + own.stderr)


# ---------------------------------------------------------------- positive side
IDENTITY = {"CLAUDECODE": "1", "CLAUDE_CODE_SESSION_ID": "parent-session-sentinel",
            "CLAUDE_CODE_REMOTE_SESSION_ID": "parent-remote-sentinel",
            "CLAUDE_CODE_MESSAGING_SOCKET": "/nonexistent/parent.sock",
            "CLAUDE_CODE_CHILD_SESSION": "1"}


def test_dispatch_is_non_blocking_and_lanes_overlap(c: Ctx) -> None:
    # Every timing property here is read off the lanes' own [start, end] spans, never off a
    # wall-clock total: under load (a validate.sh run beside live managers) dispatch overhead
    # grows, and a "serial would take >= 12s" budget went red on a correct tool.
    print("dispatch returns at once; lanes run in parallel; wait blocks until done:")
    rc, da, el_a, err = c.dispatch("alpha", env={"FAKE_CLAUDE_SLEEP": "6", **IDENTITY,
                                                 "CLAUDE_CODE_PASSTHROUGH_PROBE": "1"})
    ret_a = time.time()
    check("alpha dispatch exits 0", rc == 0 and da.get("ok") is True, f"rc={rc} {da} {err[-300:]}")
    rc, d, _, _ = c.run("status", "--root", str(c.repo), "--id", "alpha")
    check("right after dispatch the lane is RUNNING (it was not run inline)",
          d.get("state") == "running", str(d))
    rc, db, el_b, err = c.dispatch("beta", "--model", "sonnet", "--effort", "high",
                                   env={"FAKE_CLAUDE_SLEEP": "6"})
    ret_b = time.time()
    check("beta dispatch exits 0", rc == 0 and db.get("ok") is True, f"rc={rc} {db} {err[-300:]}")
    for key in ("id", "job", "worktree", "branch", "report", "log", "pin"):
        check(f"dispatch JSON carries {key}", key in da, str(sorted(da)))
    check("the pin is a sha256", len(str(da.get("pin", ""))) == 64, str(da.get("pin")))
    check("the lane runs under a subreaper supervisor", da.get("containment") == "subreaper",
          str(da.get("containment")))
    check("worktree follows the convention", str(da.get("worktree", "")).endswith(
        "/.devloop/worktrees/claude-alpha"), str(da.get("worktree")))
    check("branch follows the convention", da.get("branch") == "devloop/claude-alpha", str(da.get("branch")))

    rc, d, el_w, _ = c.run("wait", "--root", str(c.repo), "--id", "alpha", "--id", "beta",
                           "--budget-s", "90", "--interval-s", "0.5", timeout=150)
    ret_w = time.time()
    check("wait on both exits 0", rc == 0 and d.get("ok") is True, f"rc={rc} {d}")
    for lid in ("alpha", "beta"):
        ln = lane_of(d, lid)
        check(f"{lid}: state done, report status done",
              ln.get("state") == "done" and ln.get("report_status") == "done", str(ln))
    sa, sb = c.span_of("alpha"), c.span_of("beta")
    check("both lanes recorded their run span", sa is not None and sb is not None, f"{sa} {sb}")
    if sa and sb:
        check("alpha dispatch returned BEFORE its lane finished (non-blocking)", ret_a < sa[1],
              f"returned {ret_a - sa[1]:+.2f}s after the lane ended ({el_a:.2f}s)")
        check("beta dispatch returned BEFORE its lane finished (non-blocking)", ret_b < sb[1],
              f"returned {ret_b - sb[1]:+.2f}s after the lane ended ({el_b:.2f}s)")
        check("the two lanes OVERLAPPED: each started before the other ended",
              max(sa[0], sb[0]) < min(sa[1], sb[1]),
              f"alpha {sa[0]:.2f}-{sa[1]:.2f}, beta {sb[0]:.2f}-{sb[1]:.2f}")
        check("wait really blocked: it returned only after BOTH lanes ended",
              ret_w >= max(sa[1], sb[1]), f"returned {ret_w - max(sa[1], sb[1]):+.2f}s vs the last end "
              f"({el_w:.1f}s)")
    a, b = c.argv_of("alpha"), c.argv_of("beta")
    check("model policy default reached the binary: --model opus --effort xhigh",
          has_pair(a, "--model", "opus") and has_pair(a, "--effort", "xhigh"), str(a)[:300])
    check("a lower tier reached the binary: --model sonnet --effort high",
          has_pair(b, "--model", "sonnet") and has_pair(b, "--effort", "high"), str(b)[:300])
    check("the lane ran as `claude -p ... --output-format json` with the report schema",
          "-p" in a and has_pair(a, "--output-format", "json") and "--json-schema" in a, str(a)[:300])
    seen = c.env_of("alpha")
    leaked = sorted(set(IDENTITY) & set(seen))
    check("the nested lane did NOT inherit the parent session's identity", not leaked, str(leaked))
    check("...while an ordinary CLAUDE_* variable still reached it (not a blanket strip)",
          "CLAUDE_CODE_PASSTHROUGH_PROBE" in seen, str(seen))


def test_gate_collect_list(c: Ctx) -> None:
    print("gate / collect / list on a finished lane:")
    rc, d, _, _ = c.gate("alpha")
    check("gate --pin exits 0", rc == 0 and d.get("mergeable") is True, f"rc={rc} {json.dumps(d)[:600]}")
    check("...pinned, with no warning", d.get("pinned") is True and d.get("warnings") == [], str(d.get("warnings")))
    check("the audit, the ownership check AND the two-sided gate all ran and held",
          d.get("audit", {}).get("ok") is True and d.get("owned", {}).get("ok") is True
          and d.get("gate", {}).get("ok") is True, str(d)[:400])
    check("the gate saw the negative control fail for the named reason",
          "negative: FAILED for the expected reason" in d.get("gate", {}).get("output", ""), str(d)[:400])
    rc, d, _, _ = c.gate("beta", pin=False)
    check("gate without --pin still gates, but says it was not pinned",
          rc == 0 and d.get("pinned") is False and any("--pin" in w for w in d.get("warnings", [])),
          f"rc={rc} {d.get('warnings')}")
    rc, d, _, _ = c.run("collect", "--root", str(c.repo), "--id", "alpha")
    check("collect exits 0", rc == 0, f"rc={rc} {d}")
    check("collect's diff stat shows the lane's new file", "src/alpha.txt" in d.get("diff_stat", ""),
          repr(d.get("diff_stat")))
    check("collect carries the lane report", (d.get("report") or {}).get("status") == "done",
          str(d.get("report"))[:200])
    check("the lane did not commit (commits_ahead 0)", d.get("commits_ahead") == 0, str(d.get("commits_ahead")))
    check("collect never shows the pin", "pin" not in d and "pin" not in json.dumps(
        c.run("status", "--root", str(c.repo), "--id", "alpha")[1]))
    staged = git(c.wt("alpha"), "diff", "--cached", "--name-only").stdout.strip()
    check("collect did not stage anything in the lane's real index", staged == "", staged)
    rc, d, _, _ = c.run("list", "--root", str(c.repo))
    ids = {l.get("id"): l.get("state") for l in d.get("lanes", [])}
    check("list shows alpha and beta as done", ids.get("alpha") == "done" and ids.get("beta") == "done",
          str(ids))
    base = git(c.repo, "status", "--porcelain").stdout.strip()
    check("the base tree was never touched by a lane", base == "", base)
    merged = git(c.repo, "log", "--oneline", "--all").stdout.count("\n")
    check("and nothing was merged or committed for the manager", merged == 1, f"{merged} commits")


# ---------------------------------------------------------------- negative side: gate
def test_stray_edit_fails_the_gate_and_is_named(c: Ctx) -> None:
    print("an edit outside the owned paths:")
    rc, d, _, err = c.dispatch("stray", env={"FAKE_CLAUDE_MODE": "stray"})
    check("stray lane dispatched", rc == 0, f"rc={rc} {d} {err[-200:]}")
    rc, d, _, _ = c.wait("stray")
    check("the stray lane itself CLAIMS done (its report is not the proof)", rc == 0, f"rc={rc} {d}")
    rc, d, _, _ = c.gate("stray")
    check("gate exits 1", rc == 1, f"rc={rc} {json.dumps(d)[:500]}")
    check("and NAMES the stray path", "README.md" in d.get("owned", {}).get("violations", []),
          str(d.get("owned")))
    check("the controls are not run on a tree with strays", bool(d.get("gate", {}).get("skipped")),
          str(d.get("gate")))
    check("not mergeable", d.get("mergeable") is False, str(d)[:200])


def test_not_done_lane_is_never_touched(c: Ctx) -> None:
    """devloop.sh's rule, carried over: a lane that says partial is not merged even when every
    audit holds. And its controls are never RUN: measured before, a negative control that does
    not restore the tree deleted a partial lane's only (untracked) file, and the parked diff
    was empty."""
    print("a lane that did not reach done -- its controls are never run:")
    destroy = "rm -f src/{0}.txt; test -f src/{0}.txt"
    r = c.lanes([{"id": "partial", "env": {"FAKE_CLAUDE_STATUS": "partial"}},
                 {"id": "destroy", "negative": destroy.format("destroy"), "expect": "destroy",
                  "env": {"FAKE_CLAUDE_STATUS": "partial"}},
                 {"id": "parkdone", "negative": destroy.format("parkdone"), "expect": "parkdone"}])
    check("wait exits 1 when a lane is partial", r["rc"] == 1 and
          lane_of(r["doc"], "partial").get("state") == "failed", str(r))
    rc, d, _, _ = c.gate("partial")
    check("the audit holds on the partial lane", d.get("audit", {}).get("ok") is True
          and d.get("owned", {}).get("ok") is True, str(d)[:400])
    check("...and gate STILL exits 1: a lane that did not reach done is never merged",
          rc == 1 and d.get("mergeable") is False, f"rc={rc} {d.get('why')}")
    check("...without running its controls", d.get("gate", {}).get("rc") is None and
          "never run" in d.get("gate", {}).get("skipped", ""), str(d.get("gate")))
    rc, d, _, _ = c.gate("destroy")
    f = c.wt("destroy") / "src" / "destroy.txt"
    check("a destructive negative control on a partial lane: gate exits 1", rc == 1, f"rc={rc} {d.get('why')}")
    check("...and the lane's unstaged work SURVIVES the gate", f.is_file() and f.read_text() == "DONE\n",
          f"exists={f.exists()}")
    rc, d, _, _ = c.gate("parkdone")
    patch = c.state("parkdone") / "gate" / "lane-parkdone.patch"
    body = patch.read_text() if patch.is_file() else ""
    check("on a DONE lane the same control is caught: exit 2, did not restore the tree", rc == 2,
          f"rc={rc} {d.get('why')}")
    check("...and the parked patch holds the lane's UNTRACKED file (it is not lost)",
          "src/parkdone.txt" in body and "+DONE" in body, f"{len(body)} bytes: {body[:200]!r}")
    check("...and the gate says what it parked", "untracked files included" in
          d.get("gate", {}).get("output", ""), d.get("gate", {}).get("output", "")[-300:])


def test_vacuous_negative_at_gate_is_exit_2(c: Ctx) -> None:
    print("a negative control that passes at the gate:")
    rc, d, _, err = c.dispatch("vac", negative="grep -q DONE src/vac.txt || echo DEVLOOP-PLANTED-VAC",
                               expect="DEVLOOP-PLANTED-VAC")
    check("dispatched (not statically decidable)", rc == 0, f"rc={rc} {d} {err[-200:]}")
    c.wait("vac")
    rc, d, _, _ = c.gate("vac")
    check("gate exits 2 (VACUOUS), distinct from an ordinary failure", rc == 2, f"rc={rc} {json.dumps(d)[:500]}")
    check("and says so", d.get("gate", {}).get("vacuous") is True and "VACUOUS" in d.get("why", ""),
          str(d)[:400])


REWRITE = ("d = json.loads((state / 'lane.json').read_text()); d.update({upd}); "
           "(state / 'lane.json').write_text(json.dumps(d))")


def test_lane_cannot_rewrite_its_gate(c: Ctx) -> None:
    print("a lane that rewrites its own gate definition:")
    r = c.lanes([
        # writes NOT DONE, then makes its positive `true`
        {"id": "tpos", "env": {"FAKE_CLAUDE_PY": "Path('src/tpos.txt').write_text('NOT DONE\\n'); "
                                                 + REWRITE.format(upd="{'positive_cmd': 'true'}")}},
        # owns everything, edits README, does no work
        {"id": "selfown", "env": {"FAKE_CLAUDE_NOWORK": "1", "FAKE_CLAUDE_MODE": "stray",
                                  "FAKE_CLAUDE_PY": REWRITE.format(
                                      upd="{'owned_paths': ['*'], 'positive_cmd': 'true'}")}}])
    check("both lanes CLAIM done", r["rc"] == 0, str(r)[:300])
    for lid in ("tpos", "selfown"):
        for pinned in (True, False):
            rc, d, _, _ = c.gate(lid, pin=pinned)
            tag = "with" if pinned else "without"
            check(f"{lid} ({tag} --pin): gate exits 2 TAMPERED", rc == 2 and d.get("tampered") is True
                  and "TAMPERED" in d.get("why", ""), f"rc={rc} {str(d.get('why'))[:300]}")
            check(f"{lid} ({tag} --pin): no control was run", "gate" not in d and "audit" not in d, str(sorted(d)))
    # A lane that rewrites lane.json AND recomputes meta.json's pin consistently: only the pin the
    # MANAGER holds catches it. (Played by the test after the lane ends: same bytes on disk.)
    r = c.lanes([{"id": "forgemeta"}])
    st = c.state("forgemeta")
    lane = json.loads((st / "lane.json").read_text())
    lane["positive_cmd"] = "true"
    (st / "lane.json").write_text(json.dumps(lane))
    meta = json.loads((st / "meta.json").read_text())
    meta["pin"] = CLM.compute_pin(lane, meta["base"], json.loads((st / "baseline.json").read_text()))
    (st / "meta.json").write_text(json.dumps(meta))
    rc, d, _, _ = c.gate("forgemeta", pin=True)
    check("a CONSISTENT rewrite of lane.json + meta.json is caught by --pin (exit 2)",
          rc == 2 and d.get("tampered") is True, f"rc={rc} {str(d.get('why'))[:300]}")
    rc, d, _, _ = c.gate("forgemeta", pin=False)
    check("...and without --pin the gate warns that it could not tell",
          d.get("pinned") is False and any("--pin" in w for w in d.get("warnings", [])), str(d)[:300])


def test_committed_staged_and_hidden_edits(c: Ctx) -> None:
    print("edits git status cannot see -- committed, staged, renamed, index-flag-hidden:")
    r = c.lanes([
        {"id": "commitlane", "env": {"FAKE_CLAUDE_SH": "echo PWNED >> README.md; git add README.md; git commit -qm stray"}},
        # commits a stray, then restores the file in the worktree: the tree matches the base,
        # only the branch still carries it -- and the merge recipe merges the branch
        {"id": "commithide", "env": {"FAKE_CLAUDE_SH": "echo PWNED >> README.md; git commit -qam stray; "
                                                       "git show HEAD~1:README.md > README.md"}},
        {"id": "stagelane", "env": {"FAKE_CLAUDE_SH": "echo PWNED >> README.md; git add README.md"}},
        {"id": "skipwt", "positive": "grep -qx DONE src/skipwt.txt && grep -qx MAGIC README.md",
         "env": {"FAKE_CLAUDE_SH": "echo MAGIC >> README.md; git update-index --skip-worktree README.md"}},
        {"id": "assumeun", "env": {"FAKE_CLAUDE_SH": "echo X >> README.md; git update-index --assume-unchanged README.md"}},
        # a pure rename (content kept), so a rename-detecting diff WOULD pair the two paths and
        # report only the owned destination -- the audit must still see the source go
        {"id": "renlane", "owned": ["*.txt"], "env": {"FAKE_CLAUDE_NOWORK": "1",
                                                      "FAKE_CLAUDE_SH": "git mv -f README.md ren.txt"},
         "positive": "grep -qx fixture ren.txt"}])
    check("every one of them CLAIMS done", r["rc"] == 0, str(r)[:300])
    rc, d, _, _ = c.gate("commitlane")
    check("a COMMITTED stray fails the gate (exit 1)", rc == 1 and d.get("mergeable") is False, f"rc={rc} {d.get('why')}")
    check("...naming the moved branch AND the stray path",
          "moved its branch" in d.get("why", "") and "README.md" in d.get("audit", {}).get("violations", []),
          str(d.get("why"))[:300])
    rc, d, _, _ = c.gate("commithide")
    check("a stray committed and then hidden from the tree still fails (the branch moved)",
          rc == 1 and "moved its branch" in d.get("why", ""), f"rc={rc} {str(d.get('why'))[:300]}")
    rc, d, _, _ = c.gate("stagelane")
    check("a STAGED stray fails the gate, named as staged", rc == 1 and "staged README.md" in d.get("why", ""),
          f"rc={rc} {str(d.get('why'))[:300]}")
    rc, d, _, _ = c.gate("skipwt")
    check("an edit hidden by skip-worktree fails the gate (the positive depends on it)",
          rc == 1 and d.get("audit", {}).get("hidden_by_index_flags") == ["README.md"],
          f"rc={rc} {str(d.get('why'))[:300]}")
    rc, dc, _, _ = c.run("collect", "--root", str(c.repo), "--id", "skipwt")
    check("...and collect shows the hidden path", "README.md" in dc.get("changed_paths", []) and
          dc.get("hidden_by_index_flags") == ["README.md"], str(dc.get("changed_paths")))
    rc, d, _, _ = c.gate("assumeun")
    check("an edit hidden by assume-unchanged fails the gate too",
          rc == 1 and "README.md" in d.get("audit", {}).get("hidden_by_index_flags", []),
          f"rc={rc} {str(d.get('why'))[:300]}")
    rc, d, _, _ = c.gate("renlane")
    check("a rename OUT of a non-owned path fails, naming the source (owned '*.txt')",
          rc == 1 and "README.md" in d.get("audit", {}).get("violations", []),
          f"rc={rc} {str(d.get('why'))[:300]}")


def test_owned_patterns(c: Ctx) -> None:
    print("ownership patterns are matched per segment, and protected paths are never owned:")
    for pat in ("*", "**", ".", "./", "AGENTS.md", "*.md", ".git/hooks/pre-commit",
                ".gitattributes", ".devloop/tasks.jsonl", "docs/**/AGENTS.md", "../x", "/etc/passwd"):
        before = c.artefacts()
        rc, d, _, _ = c.dispatch("ownbad", owned=[pat])
        check(f"--owned {pat!r} refused (64) and created nothing", rc == 64 and c.artefacts() == before,
              f"rc={rc} {str(d.get('error'))[:200]}")
    cases = [("src/a/b/evil.txt", ["src/*.txt"], False), ("src/x.txt", ["src/*.txt"], True),
             ("src/a/b.txt", ["src/"], True), ("src/a/b.txt", ["src/**"], True),
             ("src/a/b.txt", ["src/*"], True), ("srcx/a", ["src"], False),
             ("a/b/test_x.py", ["**/test_*.py"], True), ("README.md -> src/done.txt", ["*.txt"], False)]
    for path, pats, want in cases:
        check(f"is_owned_path({path!r}, {pats}) is {want}", CLM.is_owned_path(path, pats) is want)
    c.lanes([{"id": "protsub", "owned": ["src/"], "env": {"FAKE_CLAUDE_SH": "echo '* diff' > src/.gitattributes"}},
             {"id": "segaware", "owned": ["src/*.txt"],
              "env": {"FAKE_CLAUDE_SH": "mkdir -p src/sub && echo evil > src/sub/evil.txt"}}])
    rc, d, _, _ = c.gate("protsub")
    check("a protected path under an owned subtree still fails the gate, named",
          rc == 1 and "src/.gitattributes" in d.get("audit", {}).get("protected", []),
          f"rc={rc} {str(d.get('why'))[:300]}")
    rc, d, _, _ = c.gate("segaware")
    check("owned 'src/*.txt' does NOT own src/sub/evil.txt: gate exits 1 naming it",
          rc == 1 and "src/sub/evil.txt" in d.get("audit", {}).get("violations", []),
          f"rc={rc} {str(d.get('why'))[:300]}")
    check("...a path adapters' whole-path fnmatch alone let through",
          d.get("owned", {}).get("rc") == 0, str(d.get("owned"))[:200])


def test_git_metadata_and_base_escape(c: Ctx) -> None:
    print("writes outside the worktree -- a shared git hook, the base tree:")
    hook = Path(git(c.repo, "rev-parse", "--path-format=absolute", "--git-common-dir").stdout.strip()) / "hooks" / "pre-commit"
    # One lane at a time, NOT in parallel: the hook lives in the git dir every lane shares, so a
    # second lane whose baseline was taken after the plant sees the cleanup below as its OWN git
    # metadata change -- and its gate rightly stops there, before base_moved is ever computed.
    # (Measured 2026-09-25: that order won in 2 of 3 full runs beside other test load.)
    c.lanes([{"id": "hooklane", "env": {"FAKE_CLAUDE_SH":
              'H=$(git rev-parse --path-format=absolute --git-common-dir)/hooks/pre-commit; '
              'printf "#!/bin/sh\\necho HOOK-RAN\\n" > "$H"; chmod +x "$H"'}}])
    try:
        check("precondition: the hook was planted", hook.is_file())
        rc, d, _, _ = c.gate("hooklane")
        check("a planted git hook fails the gate (exit 1)", rc == 1 and d.get("mergeable") is False,
              f"rc={rc} {str(d.get('why'))[:300]}")
        check("...naming it", "hooks/pre-commit" in d.get("git_meta_changed", []), str(d.get("git_meta_changed")))
        check("...before anything ran in the lane's worktree", "audit" not in d and "gate" not in d, str(sorted(d)))
    finally:
        hook.unlink(missing_ok=True)
    c.lanes([{"id": "escape", "env": {"FAKE_CLAUDE_SH": "echo ESCAPED >> ../../../README.md"}}])
    rc, d, _, _ = c.gate("escape")
    check("a lane that wrote into the BASE tree: base_moved names the path",
          "README.md" in d.get("base_moved", []), str(d.get("base_moved")))
    check("...and the gate warns in words the manager acts on",
          any("base_moved" in w and "README.md" in w for w in d.get("warnings", [])), str(d.get("warnings"))[:300])
    git(c.repo, "checkout", "--", "README.md")
    check("(base restored for the controls that follow)", git(c.repo, "status", "--porcelain").stdout.strip() == "")


def test_nothing_outlives_the_lane(c: Ctx) -> None:
    print("nothing the lane started outlives it:")
    orphan = "sh -c 'sleep 3; echo BROKEN > src/orph.txt; echo stray >> README.md' </dev/null >/dev/null 2>&1 &"
    forge = f'setsid {c.forger} "$STATE" </dev/null >/dev/null 2>&1 &'
    r = c.lanes([{"id": "orph", "env": {"FAKE_CLAUDE_SH": orphan}},
                 {"id": "forge", "env": {"FAKE_CLAUDE_SH": forge, "FAKE_CLAUDE_STATUS": "failed"}}])
    check("orph reads done, forge reads failed", lane_of(r["doc"], "orph").get("state") == "done" and
          lane_of(r["doc"], "forge").get("state") == "failed", str(r["doc"])[:400])
    rc, d, _, _ = c.gate("orph")
    check("orph gates clean", rc == 0, f"rc={rc} {str(d.get('why'))[:300]}")
    time.sleep(5)
    wt = c.wt("orph")
    check("a same-session child of the lane never wrote after done (it was killed)",
          (wt / "src" / "orph.txt").read_text() == "DONE\n" and
          git(wt, "status", "--porcelain").stdout.strip() == "?? src/orph.txt",
          git(wt, "status", "--porcelain").stdout)
    out = (c.state("orph") / "job" / "out").read_text()
    sup = [json.loads(l) for l in out.splitlines() if l.startswith("{") and '"supervise"' in l]
    check("the supervisor killed the straggler before the receipt",
          bool(sup) and sup[-1].get("stragglers_killed", 0) >= 1 and sup[-1].get("subreaper") is True, out[-300:])
    rc, d, _, _ = c.run("status", "--root", str(c.repo), "--id", "forge")
    check("a setsid'd forger could not rewrite the receipt: forge still NOT done",
          d.get("state") == "failed" and d.get("rc") == 1, str(d))
    check("...because it never ran to the end", not (c.state("forge") / "FORGED").exists())


def test_session_liveness(c: Ctx) -> None:
    print("a receipt, or a lost wrapper, with the lane's processes still alive:")
    unit = c.tmp / "unit"
    p = CLM.lane_paths(unit, "linger")
    p["state"].mkdir(parents=True)
    JOB.spawn(p["state"], CLM.JOB_ID, ["sh", "-c", "sleep 30 >/dev/null 2>&1 & exit 0"], unit, budget_s=60)
    t0 = time.time()
    while JOB.status(p["state"], CLM.JOB_ID)["state"] != "done" and time.time() - t0 < 10:
        time.sleep(0.1)
    p["report"].write_text(json.dumps({"status": "done", "_meta": {"timed_out": False}}))
    st = CLM.lane_status(unit, "linger", meta={})
    check("receipt rc 0 + report done + a live straggler in its session reads RUNNING",
          st["state"] == "running" and st.get("lingering", 0) >= 1, str(st))
    JOB.kill(p["state"], CLM.JOB_ID, "KILL")
    t0 = time.time()
    while CLM.lane_status(unit, "linger", meta={})["state"] == "running" and time.time() - t0 < 10:
        time.sleep(0.1)
    check("...and once the straggler is gone the same lane reads done",
          CLM.lane_status(unit, "linger", meta={})["state"] == "done")

    rc, d, _, _ = c.dispatch("wk", "--timeout-s", "60", env={"FAKE_CLAUDE_SLEEP": "30"})
    time.sleep(1.5)
    pid = int((c.state("wk") / "job" / "pid").read_text())
    os.kill(pid, signal.SIGKILL)
    time.sleep(1.5)
    rc, d, _, _ = c.run("status", "--root", str(c.repo), "--id", "wk")
    check("the job wrapper SIGKILLed alone, the lane tree alive: RUNNING, not lost",
          d.get("state") == "running" and d.get("job_state") == "lost" and "wrapper is gone" in d.get("why", ""),
          str(d))
    rc, d, _, _ = c.run("kill", "--root", str(c.repo), "--id", "wk", "--grace-s", "5")
    check("kill reaches the orphaned lane tree through its session", rc == 0 and d.get("state") == "lost", f"rc={rc} {d}")

    q = CLM.lane_paths(unit, "inflight")
    q["state"].mkdir(parents=True)
    q["meta"].write_text(json.dumps({"id": "inflight"}))
    q["marker"].write_text(json.dumps({"pid": os.getpid(), "start": git_lock._proc_start(os.getpid())}))
    st = CLM.lane_status(unit, "inflight", meta={})
    check("meta written, job not spawned yet, dispatcher alive: RUNNING, not lost",
          st["state"] == "running" and "in flight" in st.get("why", ""), str(st))
    dead = subprocess.Popen(["true"])
    dead.wait()
    q["marker"].write_text(json.dumps({"pid": dead.pid, "start": "0"}))
    st = CLM.lane_status(unit, "inflight", meta={})
    check("...and when that dispatcher died mid-dispatch: lost, saying so",
          st["state"] == "lost" and "dispatcher died" in st.get("why", ""), str(st))


def test_list_survives_a_bad_meta(c: Ctx) -> None:
    print("one unreadable meta.json does not hide the other lanes:")
    zz = c.repo / ".devloop" / "native" / "claude" / "zz-corrupt"
    zz.mkdir(parents=True)
    (zz / "meta.json").write_text('{"id": "zz-')
    try:
        rc, d, _, _ = c.run("list", "--root", str(c.repo))
        ids = {l.get("id"): l for l in d.get("lanes", [])}
        check("list still exits 0", rc == 0, f"rc={rc} {str(d)[:300]}")
        check("...the bad lane reads unknown, with the reason", ids.get("zz-corrupt", {}).get("state") == "unknown"
              and "unreadable" in ids.get("zz-corrupt", {}).get("error", ""), str(ids.get("zz-corrupt")))
        check("...and the others are still listed", ids.get("alpha", {}).get("state") == "done", str(sorted(ids)))
    finally:
        shutil.rmtree(zz)


def test_rollback_leaves_nothing(c: Ctx) -> None:
    print("a dispatch whose worktree add fails rolls back its branch too:")
    r2 = make_repo(c.tmp / "repo2")
    (r2 / ".devloop").mkdir()
    (r2 / ".devloop" / "worktrees").write_text("a file where the worktree root should be\n")
    rc, d, _, _ = c.dispatch("wtfail", root=r2)
    check("git worktree add fails -> 73", rc == 73 and "worktree add failed" in d.get("error", ""), f"rc={rc} {d}")
    check("...and no branch, no state dir is left", "devloop/claude-wtfail" not in c.artefacts(r2)[2]
          and "wtfail" not in c.artefacts(r2)[0], str(c.artefacts(r2)))
    (r2 / ".devloop" / "worktrees").unlink()
    rc, d, _, _ = c.dispatch("wtfail", root=r2)
    check("...so the same id dispatches once the cause is fixed", rc == 0, f"rc={rc} {d}")
    c.wait("wtfail", root=r2)


# ---------------------------------------------------------------- negative side: refusals
def test_refusals_create_nothing(c: Ctx) -> None:
    print("refusals happen before anything is created:")
    nopath = no_claude_path()
    check("precondition: the filtered PATH really has no claude",
          shutil.which("claude", path=nopath) is None and shutil.which("git", path=nopath) is not None,
          nopath)
    before = c.artefacts()
    rc, d, _, _ = c.dispatch("noclaude", path=nopath)
    check("no claude on PATH -> exit 127", rc == 127, f"rc={rc} {d}")
    check("...naming the missing binary", "claude" in d.get("error", ""), str(d))
    check("...and no state dir, worktree, branch or job was left", c.artefacts() == before,
          f"{before} -> {c.artefacts()}")

    for bad in ("../x", "x/../../y", "Upper", "-lead", "a" * 42, "", "a b"):
        before = c.artefacts()
        rc, d, _, _ = c.dispatch(bad)
        check(f"bad id {bad!r} refused with 64", rc == 64, f"rc={rc} {d}")
        check(f"bad id {bad!r} created nothing", c.artefacts() == before, f"{before} -> {c.artefacts()}")
    check("no traversal escaped .devloop/",
          not (c.repo / ".devloop" / "native" / "x").exists() and not (c.tmp / "x").exists()
          and not (c.repo / "x").exists())

    meta = c.state("alpha") / "meta.json"
    snap = meta.read_bytes() if meta.is_file() else b""
    before = c.artefacts()
    rc, d, _, _ = c.dispatch("alpha")
    check("a duplicate id is refused (73)", rc == 73, f"rc={rc} {d}")
    check("...the original lane is untouched", meta.is_file() and meta.read_bytes() == snap
          and c.artefacts() == before)
    rc, d, _, _ = c.run("status", "--root", str(c.repo), "--id", "alpha")
    check("...and still reads done", d.get("state") == "done", str(d))

    vac = [("false with no expect (adapters' own rule)", dict(negative="false", expect=""),
            "no real negative control"),
           ("a control that always exits 0", dict(negative="true", expect="X"), "always exits 0"),
           ("a regex that matches everything", dict(expect=".*"), "matches the empty string"),
           ("the positive control reused as the negative", dict(negative="grep -q DONE src/v5.txt",
                                                                 positive="grep -q DONE src/v5.txt"),
            "is the positive control"),
           ("an invalid regex", dict(expect="("), "not a valid regex"),
           ("a timeout below the schema's minimum", dict(), "minimum"),
           ("--max-turns below the floor", dict(), "below the minimum")]
    for i, (label, kw, needle) in enumerate(vac):
        before = c.artefacts()
        extra = (("--timeout-s", "5") if label.startswith("a timeout") else
                 ("--max-turns", "8") if label.startswith("--max-turns") else ())
        rc, d, _, _ = c.dispatch(f"v{i}", *extra, **kw)
        check(f"refused at dispatch (65): {label}", rc == 65, f"rc={rc} {d}")
        check(f"...in the right words: {needle!r}", needle in d.get("error", ""), d.get("error", "")[:300])
        check(f"...created nothing: {label}", c.artefacts() == before)

    before = c.artefacts()
    rc, d, _, _ = c.dispatch("noowned", owned=[])
    check("zero --owned refused (64)", rc == 64 and c.artefacts() == before, f"rc={rc} {d}")
    notgit = c.tmp / "notgit"
    notgit.mkdir()
    rc, d, _, _ = c.run("dispatch", "--root", str(notgit), "--id", "x", "--objective-file",
                        str(c.objective), "--owned", "a", "--positive", "p", "--negative", "n",
                        "--negative-expect", "N")
    check("a non-git root is refused (64)", rc == 64 and not (notgit / ".devloop").exists(), f"rc={rc} {d}")
    rc, d, _, _ = c.run("dispatch", "--root", str(c.repo), "--id", "x")
    check("a usage error is 64 with a JSON object -- never argparse's 2, which means VACUOUS",
          rc == 64 and d.get("ok") is False, f"rc={rc} {d}")
    rc, d, _, _ = c.run("status", "--root", str(c.repo), "--id", "nosuch")
    check("status of an unknown lane is 64", rc == 64, f"rc={rc} {d}")
    rc, d, _, _ = c.run("wait", "--root", str(c.repo), "--id", "alpha", "--id", "nosuch", "--budget-s", "1")
    check("wait naming an unknown lane is 64, not a partial pass", rc == 64, f"rc={rc} {d}")


# ---------------------------------------------------------------- the hang lane, finished
def test_lane_timeout_is_not_a_pass(c: Ctx) -> None:
    print("a lane that outruns its own --timeout-s:")
    rc, d, _, _ = c.run("wait", "--root", str(c.repo), "--id", "alpha", "--id", "hang",
                        "--budget-s", "120", "--interval-s", "1", timeout=180)
    ln = lane_of(d, "hang")
    check("wait exits 3 even though the other lane is done", rc == 3, f"rc={rc} {d}")
    check("hang: state timeout", ln.get("state") == "timeout", str(ln))
    check("hang: NOT still running -- the lane's own budget killed it",
          ln.get("still_running") is False and ln.get("timed_out") is True, str(ln))
    check("hang: the adapter recorded it as budget, not done", ln.get("report_status") == "budget", str(ln))
    rc, d, _, _ = c.gate("hang")
    check("a timed-out lane is never mergeable", rc != 0 and d.get("mergeable") is False, f"rc={rc} {d}"[:300])


def test_kill(c: Ctx) -> None:
    print("kill:")
    rc, d, _, _ = c.dispatch("killme", "--timeout-s", "600", env={"FAKE_CLAUDE_MODE": "hang"})
    check("dispatched", rc == 0, f"rc={rc} {d}")
    time.sleep(1.0)
    rc, d, _, _ = c.run("kill", "--root", str(c.repo), "--id", "killme", "--grace-s", "10")
    check("kill exits 0 and the lane is no longer running", rc == 0 and d.get("state") != "running",
          f"rc={rc} {d}")
    check("a killed lane is not done", d.get("state") in ("failed", "lost"), str(d))
    # Self-certification: the lane's report path is a plain file. Forge a done report for the
    # killed lane; without a receipt that agrees (rc 0), it must not read as done.
    rep = c.state("killme") / "report.json"
    rep.write_text(json.dumps({"status": "done", "objective": "forged", "_meta": {"timed_out": False}}))
    rc, d, _, _ = c.run("status", "--root", str(c.repo), "--id", "killme")
    check("a forged done report without a matching receipt is NOT done",
          d.get("state") != "done" and d.get("report_status") == "done", str(d))


# ---------------------------------------------------------------- the prompt and the launcher
def test_template_and_host(c: Ctx) -> None:
    print("the canned prompt reaches /teamwork-preview:")
    cp = subprocess.run([sys.executable, str(PROMPTS), "declare", "nested-claude-lanes"],
                        capture_output=True, text=True)
    check("nested-claude-lanes is a declared template", cp.returncode == 0 and
          "CLAUDE_LANE" in cp.stdout, cp.stdout + cp.stderr)

    def host(env: dict, path: str) -> subprocess.CompletedProcess:
        return subprocess.run(["sh", str(HOST), "--teamwork", "Build the thing", "--print-prompt"],
                              cwd=c.repo, capture_output=True, text=True, timeout=60,
                              env={**os.environ, "PATH": path, **env})

    on = host({}, c.path_with_fake)
    body = on.stdout
    check("with claude on PATH: renders", on.returncode == 0, on.stderr[-300:])
    check("the objective still leads", body.startswith("/teamwork-preview Build the thing\n"), body[:80])
    check("the section is appended", "# NESTED CLAUDE CODE LANES" in body, body[:200])
    check("with the ABSOLUTE tool path and this run's root",
          f"python3 {CL} dispatch --root {c.repo.resolve()} " in body, body[body.find("python3"):][:160])
    for phrase in ("EXCLUSIVE OWNED PATHS", "NO git add, commit or push",
                   "--model opus --effort xhigh", "Dispatch EVERY independent lane first",
                   "A timeout is never", "is NEVER merged", "the AGY MANAGER ONLY",
                   "--pin <pin", "it does NOT stop a raw write", "restore EVERY path it touches",
                   "It does NOT see files ignored", "give 20 or more", "core.hooksPath=/dev/null",
                   "base_moved"):
        check(f"states: {phrase!r}", phrase in body)
    for overstated in ("a second writer is refused rather than raced",
                       "the gate's ownership audit catches any edit outside the owned paths"):
        check(f"no longer overstates: {overstated!r}", overstated not in body)
    check("no placeholder survives", "{{" not in body)
    check("no shell variable survives", not P.SHELL_LEAK_RE.search(body),
          str(sorted(set(P.SHELL_LEAK_RE.findall(body)))[:5]))

    for v in ("0", "false", "no", "off", "FALSE", "Off"):
        off = host({"AGY_HOST_CLAUDE_LANES": v}, c.path_with_fake)
        check(f"AGY_HOST_CLAUDE_LANES={v} leaves it out", off.returncode == 0 and
              off.stdout == "/teamwork-preview Build the thing\n", repr(off.stdout[:120]))
    for v in ("1", "yes"):
        keep = host({"AGY_HOST_CLAUDE_LANES": v}, c.path_with_fake)
        check(f"AGY_HOST_CLAUDE_LANES={v} keeps it", "# NESTED CLAUDE CODE LANES" in keep.stdout,
              repr(keep.stdout[:120]))
    none = host({}, no_claude_path())
    check("no claude on PATH leaves it out (never offer a tool that cannot run)",
          none.returncode == 0 and "NESTED CLAUDE" not in none.stdout, repr(none.stdout[:200]))
    agents = (ROOT / "AGENTS.md").read_text()
    check("AGENTS.md names the tool and cites this control",
          "claude_lane.py" in agents and "tests/test_claude_lane.py" in agents)
    check("AGENTS.md does not claim a real AGY run proved it", "not yet observed" in agents)


def cleanup(c: Ctx) -> None:
    for root in (c.repo, c.tmp / "repo2"):
        if not root.is_dir():
            continue
        rc, d, _, _ = c.run("list", "--root", str(root))
        for l in d.get("lanes", []):
            if l.get("state") == "running":
                c.run("kill", "--root", str(root), "--id", l["id"], "--grace-s", "5")


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        c = Ctx(Path(td))
        try:
            test_timeout_is_not_a_pass_while_running(c)
            test_dispatch_is_non_blocking_and_lanes_overlap(c)
            test_gate_collect_list(c)
            test_stray_edit_fails_the_gate_and_is_named(c)
            test_not_done_lane_is_never_touched(c)
            test_vacuous_negative_at_gate_is_exit_2(c)
            test_lane_cannot_rewrite_its_gate(c)
            test_committed_staged_and_hidden_edits(c)
            test_owned_patterns(c)
            test_git_metadata_and_base_escape(c)
            test_nothing_outlives_the_lane(c)
            test_session_liveness(c)
            test_list_survives_a_bad_meta(c)
            test_rollback_leaves_nothing(c)
            test_refusals_create_nothing(c)
            test_kill(c)
            test_template_and_host(c)
            test_lane_timeout_is_not_a_pass(c)
        finally:
            cleanup(c)
    print()
    if FAILURES:
        print(f"FAILED ({len(FAILURES)}): " + ", ".join(FAILURES))
        return 1
    print("all nested-claude-lane controls passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
