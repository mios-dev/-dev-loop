#!/usr/bin/env python3
"""Behavioural gate for goal.py's criterion evaluation (stdlib only).

The property under test: a criterion that was not actually measured must never
report PASSED. SKILL.md §7 calls this Skip-as-Pass, and goal.py is where it
matters most -- evaluate() is what flips a goal to COMPLETED.

Run directly:  python3 tests/test_goal_criteria.py
"""

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GOAL_PY = REPO / "skills" / "dev-loop" / "scripts" / "goal.py"
ARTIFACTS_PY = REPO / "skills" / "dev-loop" / "scripts" / "artifacts.py"


def load_goal_module():
    spec = importlib.util.spec_from_file_location("goal_under_test", GOAL_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class CriterionEvaluation(unittest.TestCase):
    """Each test builds a throwaway git repo so nothing touches this checkout."""

    @classmethod
    def setUpClass(cls):
        cls.goal = load_goal_module()

    def make_repo(self):
        d = Path(tempfile.mkdtemp(prefix="goal-gate-"))
        self.addCleanup(subprocess.run, ["rm", "-rf", str(d)])
        subprocess.run(["git", "init", "-q", str(d)], check=True)
        for k, v in (("user.email", "t@t"), ("user.name", "t")):
            subprocess.run(["git", "-C", str(d), "config", k, v], check=True)
        (d / "README.md").write_text("")
        subprocess.run(["git", "-C", str(d), "add", "README.md"], check=True)
        subprocess.run(["git", "-C", str(d), "commit", "-qm", "init"], check=True)
        scripts = d / "skills" / "dev-loop" / "scripts"
        scripts.mkdir(parents=True)
        (scripts / "artifacts.py").write_text(ARTIFACTS_PY.read_text())
        return d

    def evaluate(self, repo, criteria):
        engine = self.goal.GoalEngine(str(repo))
        engine.init_goal("gate", "true", criteria=criteria)
        engine.evaluate()
        state = json.loads((repo / ".devloop" / "goal_state.json").read_text())
        return {c["id"]: c for c in state["criteria"]}

    # --- the skip-as-pass cases -------------------------------------------------

    def test_invariant_with_failing_command_fails(self):
        """`invariant` is the default type for caller-supplied criteria; it must run."""
        got = self.evaluate(self.make_repo(),
                            [{"description": "must hold", "type": "invariant", "command": "exit 7"}])
        self.assertFalse(got["C-01"]["passed"])
        self.assertIn("7", got["C-01"]["details"])

    def test_unknown_criterion_type_is_refused_at_init(self):
        with self.assertRaises(SystemExit) as caught:
            self.evaluate(self.make_repo(),
                          [{"description": "typo", "type": "invarient", "command": "true"}])
        self.assertIn("unknown type", str(caught.exception))

    def test_command_type_without_a_command_is_refused(self):
        for ctype in ("test", "invariant"):
            with self.subTest(ctype=ctype), self.assertRaises(SystemExit):
                self.evaluate(self.make_repo(), [{"description": "x", "type": ctype}])

    def test_non_empty_without_target_path_is_refused(self):
        with self.assertRaises(SystemExit):
            self.evaluate(self.make_repo(), [{"description": "x", "type": "non_empty"}])

    def test_artifact_criterion_fails_when_there_is_nothing_to_validate(self):
        """`tasks validate` reports "ok: 0 tasks" on an absent file -- an empty-set pass."""
        got = self.evaluate(self.make_repo(), [{"description": "artifacts", "type": "artifact"}])
        self.assertFalse(got["C-01"]["passed"])
        self.assertIn("tasks.jsonl", got["C-01"]["details"])

    def test_artifact_criterion_fails_on_broken_tasks(self):
        repo = self.make_repo()
        (repo / ".devloop").mkdir(exist_ok=True)
        (repo / ".devloop" / "tasks.jsonl").write_text(
            '{"id":"T-001","title":"x","status":"open","type":"task"}\n'
            '{"id":"T-001","title":"y","status":"open","type":"task"}\n')
        got = self.evaluate(repo, [{"description": "artifacts", "type": "artifact"}])
        self.assertFalse(got["C-01"]["passed"])

    # --- positive controls: these must pass, and for the right reason ------------

    def test_invariant_that_holds_passes(self):
        got = self.evaluate(self.make_repo(),
                            [{"description": "holds", "type": "invariant", "command": "true"}])
        self.assertTrue(got["C-01"]["passed"])
        # "Exit code 0" and not "Manual check verified": the command was actually run.
        self.assertIn("Exit code 0", got["C-01"]["details"])

    def test_artifact_criterion_passes_over_valid_tasks(self):
        repo = self.make_repo()
        (repo / ".devloop").mkdir(exist_ok=True)
        (repo / ".devloop" / "tasks.jsonl").write_text(
            '{"id":"T-001","title":"x","status":"open","type":"task"}\n')
        got = self.evaluate(repo, [{"description": "artifacts", "type": "artifact"}])
        self.assertTrue(got["C-01"]["passed"])

    def test_default_criteria_require_a_stopping_condition(self):
        """No --stop used to silently become `pytest`, gating the goal on a foreign runner."""
        repo = self.make_repo()
        engine = self.goal.GoalEngine(str(repo))
        with self.assertRaises(SystemExit):
            engine.init_goal("gate", "")


if __name__ == "__main__":
    os.chdir(tempfile.gettempdir())   # never resolve the repo root from CWD
    unittest.main(verbosity=2)
