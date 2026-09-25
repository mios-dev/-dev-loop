#!/usr/bin/env python3
"""
Control for the base-tree guard in agy_session.py.

The hole this closes
--------------------
Every gate in this repo reads a LANE'S WORKTREE: adapters.py owned/gate/secrets/deps takes
the lane json and the worktree path, and the merge is a merge of that worktree's branch. The
manager is not a lane, so nothing measured what the manager itself wrote.

Measured 2026-09-19: a manager run with `worktree_root` set never created a worktree. It
edited the base tree directly and, while planting negative-control fixtures, left a hardcoded
root password in a shipped boot script and a 99999 ratchet in the SSOT. Every lane gate
passed. The dispatch prompt already told it to use isolated workspaces -- the instruction was
there and nothing checked it, which is exactly the "check that cannot fail" class SKILL.md 7
is about, applied to the orchestrator.

So the guard: snapshot `git status --porcelain` before turn 1, re-read it at every turn end,
and treat any CHANGED path that is not .devloop/, AGENTS.md, TASKS.md or the lane plan's own
worktree_root as a base-tree edit -- warn the manager while the session is still alive, and
exit 6 if the run ends with one outstanding.

Three properties have to hold or the guard is theatre:
  * the baseline makes inherited dirt innocent (else every run on a dirty tree is a false red);
  * a missing git is reported as the guard being OFF, never as clean (Skip-as-Pass);
  * the allowlist is anchored -- ".devloop-scratch/x" must NOT be excused by ".devloop/".
"""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "skills" / "dev-loop" / "scripts"
spec = importlib.util.spec_from_file_location("agy_session", SCRIPTS / "agy_session.py")
AS = importlib.util.module_from_spec(spec)
spec.loader.exec_module(AS)

ALLOWED = AS.BASE_TREE_ALWAYS_ALLOWED + (".worktrees/",)


def git_repo():
    d = tempfile.mkdtemp(prefix="basetree-")
    subprocess.run(["git", "init", "-q", d], check=True)
    subprocess.run(["git", "-C", d, "config", "user.email", "t@e.st"], check=True)
    subprocess.run(["git", "-C", d, "config", "user.name", "t"], check=True)
    Path(d, "shipped.sh").write_text("echo hello\n")
    subprocess.run(["git", "-C", d, "add", "shipped.sh"], check=True)
    subprocess.run(["git", "-C", d, "commit", "-qm", "init"], check=True)
    return Path(d)


class TestBaseTreeState(unittest.TestCase):
    def test_a_clean_repo_reads_as_no_paths(self):
        d = git_repo()
        self.assertEqual(AS.base_tree_state(d), {})

    def test_a_modified_file_is_seen(self):
        d = git_repo()
        (d / "shipped.sh").write_text("echo hello\necho more\n")
        self.assertIn("shipped.sh", AS.base_tree_state(d))

    def test_an_untracked_file_is_seen(self):
        d = git_repo()
        (d / "new.sh").write_text("x\n")
        self.assertIn("new.sh", AS.base_tree_state(d))

    def test_a_non_repo_is_none_not_empty(self):
        """None means 'the instrument is missing'. {} would mean 'clean' and pass vacuously."""
        d = Path(tempfile.mkdtemp(prefix="notarepo-"))
        self.assertIsNone(AS.base_tree_state(d))


class TestStrayDetection(unittest.TestCase):
    def test_the_measured_incident_is_caught(self):
        d = git_repo()
        before = AS.base_tree_state(d)
        (d / "shipped.sh").write_text('echo hello\necho "Root:NOT-A-REAL-SECRET" | chpasswd\n')
        strays = AS.stray_base_edits(before, AS.base_tree_state(d), ALLOWED)
        self.assertEqual(strays, ["shipped.sh"])

    def test_inherited_dirt_is_not_blamed_on_the_manager(self):
        d = git_repo()
        (d / "shipped.sh").write_text("echo pre-existing edit\n")
        before = AS.base_tree_state(d)              # the run STARTS dirty
        self.assertEqual(AS.stray_base_edits(before, AS.base_tree_state(d), ALLOWED), [])

    def test_a_further_edit_to_an_already_dirty_path_is_still_caught(self):
        """Same porcelain code both times, so a path-set comparison would miss this."""
        d = git_repo()
        (d / "extra.sh").write_text("x\n")          # untracked, "??"
        before = AS.base_tree_state(d)
        subprocess.run(["git", "-C", str(d), "add", "extra.sh"], check=True)   # now "A "
        self.assertEqual(AS.stray_base_edits(before, AS.base_tree_state(d), ALLOWED), ["extra.sh"])

    def test_the_managers_own_shared_state_is_allowed(self):
        d = git_repo()
        before = AS.base_tree_state(d)
        os.makedirs(d / ".devloop", exist_ok=True)
        (d / ".devloop" / "LEDGER.md").write_text("entry\n")
        (d / "AGENTS.md").write_text("contract\n")
        (d / "TASKS.md").write_text("tasks\n")
        self.assertEqual(AS.stray_base_edits(before, AS.base_tree_state(d), ALLOWED), [])

    def test_a_lane_worktree_is_allowed(self):
        d = git_repo()
        before = AS.base_tree_state(d)
        os.makedirs(d / ".worktrees" / "lane-a", exist_ok=True)
        (d / ".worktrees" / "lane-a" / "f.py").write_text("x\n")
        self.assertEqual(AS.stray_base_edits(before, AS.base_tree_state(d), ALLOWED), [])

    def test_the_allowlist_is_anchored(self):
        """A prefix allowlist that is not anchored excuses more than it names."""
        d = git_repo()
        before = AS.base_tree_state(d)
        os.makedirs(d / ".devloop-scratch", exist_ok=True)
        (d / ".devloop-scratch" / "x").write_text("x\n")
        strays = AS.stray_base_edits(before, AS.base_tree_state(d), ALLOWED)
        # porcelain collapses a wholly-untracked directory to the directory itself,
        # so the reported path is ".devloop-scratch/", not the file inside it.
        self.assertEqual(strays, [".devloop-scratch/"],
                         ".devloop/ must not excuse .devloop-scratch/")

    def test_a_missing_instrument_reports_nothing_and_the_caller_says_so(self):
        """stray_base_edits(None) is empty BY DESIGN; main() prints the guard is OFF."""
        self.assertEqual(AS.stray_base_edits({}, None, ALLOWED), [])
        src = (SCRIPTS / "agy_session.py").read_text()
        self.assertIn("base-tree guard OFF", src,
                      "a disabled guard must announce itself, not pass silently")


class TestWorktreeRoot(unittest.TestCase):
    def test_the_lane_plans_root_is_used(self):
        d = Path(tempfile.mkdtemp(prefix="lanes-"))
        p = d / "lanes.json"
        p.write_text('{"worktree_root": "build/wt", "lanes": []}')
        self.assertEqual(AS.worktree_root_of(p), "build/wt/")

    def test_a_missing_plan_falls_back_to_the_documented_default(self):
        self.assertEqual(AS.worktree_root_of(Path("/nonexistent/lanes.json")), ".worktrees/")


class TestExitCode(unittest.TestCase):
    def test_six_is_reserved_and_documented(self):
        src = (SCRIPTS / "agy_session.py").read_text()
        self.assertIn("return 6", src)
        self.assertIn("6 the manager left the base tree dirty", src)


# A fake `agy` that EDITS THE REPO it is run in, then reports a finished turn. That is the
# behaviour the scope decision turns on: for a lane run it is a stray to fail closed on, for
# a lane-less run it is the output.
EDITING_FAKE = r'''#!/usr/bin/env python3
import json, os, sys
open(os.path.join(os.environ["FAKE_AGY_REPO"], "touched.txt"), "w").write("edited by the manager\n")
print(json.dumps({"event": "init", "conversation_id": "fake",
                  "init": {"cwd": os.getcwd(), "tools": [], "permission_mode": "yolo"}}), flush=True)
for _ in sys.stdin:
    print(json.dumps({"event": "result", "result": {"status": "ok", "num_turns": 1}}), flush=True)
'''


class TestGuardScope(unittest.TestCase):
    """END-TO-END, both sides of the one judgement call in this guard.

    The guard asks "did the manager edit the base tree INSTEAD OF a lane worktree?". With no
    lanes there are no worktrees, so the answer is yes for every edit a lane-less manager makes
    -- including the ones that ARE the run. Failing closed there kills the run at its first
    real change while measuring nothing (SKILL.md 7).

    So: lanes -> still fails closed (the original incident must stay caught). No lanes -> the
    run survives AND every edit is still named, prefixed UNGATED. The second assertion is the
    one that matters: the cost of this scope is silence, and silence is what is forbidden."""

    def _run(self, with_lanes: bool):
        tmp = Path(tempfile.mkdtemp(prefix="scope-"))
        repo = tmp / "repo"
        repo.mkdir()
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-q", "--allow-empty", "-m", "base"],
                       check=True, env={**os.environ, "GIT_AUTHOR_NAME": "t",
                                        "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
                                        "GIT_COMMITTER_EMAIL": "t@t"})
        bindir = tmp / "bin"
        bindir.mkdir()
        fake = bindir / "agy"
        fake.write_text(EDITING_FAKE)
        fake.chmod(0o755)
        prompt = tmp / "p.txt"
        prompt.write_text("go")
        argv = [sys.executable, str(SCRIPTS / "agy_session.py"), "--prompt-file", str(prompt),
                "--run-root", str(repo), "--poll-max", "0"]
        if with_lanes:
            lanes = tmp / "lanes.json"
            lanes.write_text(json.dumps({"lanes": [{"id": "n1", "worker": {"harness": "antigravity"}}]}))
            argv += ["--lanes", str(lanes)]
        cp = subprocess.run(argv, capture_output=True, text=True, timeout=180,
                            env={**os.environ, "PATH": f"{bindir}:{os.environ['PATH']}",
                                 "FAKE_AGY_REPO": str(repo)})
        return cp.returncode, cp.stderr

    def test_with_lanes_it_still_fails_closed(self):
        rc, err = self._run(with_lanes=True)
        self.assertEqual(rc, 6, f"a lane run must still fail closed on a base edit: {err[-400:]}")
        self.assertIn("failing closed", err)

    def test_without_lanes_the_run_survives(self):
        rc, err = self._run(with_lanes=False)
        self.assertNotEqual(rc, 6, f"a lane-less run was killed by a guard that cannot apply: {err[-400:]}")

    def test_without_lanes_the_edit_is_still_named(self):
        """The whole cost of the scope. If this goes quiet, the scope became a Skip-as-Pass."""
        rc, err = self._run(with_lanes=False)
        self.assertIn("UNGATED", err, f"base edits went unreported in a lane-less run: {err[-400:]}")
        self.assertIn("touched.txt", err, "the guard must name the files, not just the fact")


if __name__ == "__main__":
    unittest.main()
