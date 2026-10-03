#!/usr/bin/env python3
"""Controls for task-file discovery in artifacts.py (stdlib only).

A project may keep its canonical task list at <root>/tasks.jsonl instead of the scaffold default
<root>/.devloop/tasks.jsonl. Every reader and writer must agree on ONE resolved file:

    --tasks FILE  >  $DEVLOOP_TASKS_FILE (relative to root)  >  <root>/tasks.jsonl  >  <root>/.devloop/tasks.jsonl

Cases (each in a throwaway git repo; this checkout is never touched):
  (a) .devloop only: reads and writes there (regression)
  (b) root only: next, set and render use <root>/tasks.jsonl and .devloop/ is not created
  (c) both present: the root file wins
  (d) DEVLOOP_TASKS_FILE and --tasks override both
  (e) hooks/prompt-context.sh shows the in_progress task from a root-only fixture
  (f) OpenAI plan-status dialect: `set X done` writes 'completed'; a legacy file still writes 'done'
  (g) render guard: a foreign-banner TASKS.md is left byte-identical; a '# TASKS' file is rewritten
  (h) widened id regex
  (i) next --limit
  plus: mutating ops wait on '<task file>.lock', and the lock file never dirties `git status`.

Negative control for the resolver: make tasks_path() always return root/.devloop/tasks.jsonl and
cases (b), (c) and (e) fail.

Run: python3 tests/test_tasks_path_resolution.py
"""
from __future__ import annotations

import fcntl
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "skills" / "dev-loop" / "scripts"
ART = SCRIPTS / "artifacts.py"
PROMPT_HOOK = REPO / "hooks" / "prompt-context.sh"
sys.dont_write_bytecode = True
sys.path.insert(0, str(SCRIPTS))
import artifacts  # noqa: E402


def rec(i, status="open", **kw):
    return {"id": i, "type": "task", "title": f"title {i}", "status": status, "depends_on": [], **kw}


def write(p: Path, records) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), "utf-8")


def read(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text("utf-8").splitlines() if l.strip()]


class Base(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="tasks-path-"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        self.env = {k: v for k, v in os.environ.items() if k != artifacts.TASKS_FILE_ENV}

    def art(self, *args, env=None, check=True):
        cp = subprocess.run([sys.executable, str(ART), "tasks", *args, "--root", str(self.root)],
                            capture_output=True, text=True, env=env or self.env, cwd=self.root)
        if check:
            self.assertEqual(cp.returncode, 0, f"{args}: rc={cp.returncode}\n{cp.stdout}\n{cp.stderr}")
        return cp

    @property
    def top(self): return self.root / "tasks.jsonl"

    @property
    def dl(self): return self.root / ".devloop" / "tasks.jsonl"


class Resolution(Base):
    def test_a_devloop_only_regression(self):
        write(self.dl, [rec("T-001"), rec("T-002")])
        self.assertEqual(self.art("path").stdout.strip(), str(self.dl))
        self.assertIn("T-001", self.art("next").stdout)
        self.art("set", "T-001", "done", "--evidence", "pos+neg")
        self.assertEqual(read(self.dl)[0]["status"], "done")
        self.assertFalse(self.top.exists(), "a root task file was created")

    def test_b_root_only(self):
        write(self.top, [rec("T-001"), rec("T-002", depends_on=["T-001"])])
        self.assertEqual(self.art("path").stdout.strip(), str(self.top))
        self.assertEqual(self.art("next").stdout.split(), ["T-001", "title", "T-001"])
        self.art("set", "T-001", "done", "--evidence", "pos+neg")
        self.assertEqual(read(self.top)[0]["status"], "done")
        self.assertIn("T-002", self.art("next").stdout)
        self.art("render")
        md = (self.root / "TASKS.md").read_text("utf-8")
        self.assertIn("Rendered from `tasks.jsonl`", md)
        self.assertIn("T-002", md)
        self.assertFalse((self.root / ".devloop").exists(), ".devloop/ was created for a root-only project")
        # the lock file the set took must not dirty the tree (a dirty base tree halts the orchestrator)
        st = subprocess.run(["git", "status", "--porcelain", "-uall"], cwd=self.root, capture_output=True, text=True).stdout
        self.assertNotIn("tasks.jsonl.lock", st)
        self.assertIn("tasks.jsonl", st)

    def test_b2_scaffold_does_not_mint_a_second_task_file(self):
        write(self.top, [rec("T-001")])
        subprocess.run([sys.executable, str(ART), "scaffold", "--root", str(self.root)], check=True,
                       capture_output=True, env=self.env)
        self.assertFalse(self.dl.exists(), "scaffold created .devloop/tasks.jsonl beside <root>/tasks.jsonl")

    def test_c_both_present_root_wins(self):
        write(self.top, [rec("T-100")])
        write(self.dl, [rec("T-200")])
        self.assertEqual(self.art("path").stdout.strip(), str(self.top))
        out = self.art("next").stdout
        self.assertIn("T-100", out); self.assertNotIn("T-200", out)
        self.art("set", "T-100", "in_progress")
        self.assertEqual(read(self.top)[0]["status"], "in_progress")
        self.assertEqual(read(self.dl)[0]["status"], "open", "the .devloop file was written")
        self.assertNotEqual(self.art("set", "T-200", "in_progress", check=False).returncode, 0)

    def test_d_env_and_flag_override(self):
        write(self.top, [rec("T-100")])
        write(self.dl, [rec("T-200")])
        write(self.root / "alt" / "list.jsonl", [rec("T-300")])
        write(self.root / "flag.jsonl", [rec("T-400")])
        env = {**self.env, artifacts.TASKS_FILE_ENV: "alt/list.jsonl"}
        self.assertEqual(self.art("path", env=env).stdout.strip(), str(self.root / "alt" / "list.jsonl"))
        self.assertIn("T-300", self.art("next", env=env).stdout)
        self.art("set", "T-300", "in_progress", env=env)
        self.assertEqual(read(self.root / "alt" / "list.jsonl")[0]["status"], "in_progress")
        flag = str(self.root / "flag.jsonl")
        self.assertEqual(self.art("path", "--tasks", flag, env=env).stdout.strip(), flag)
        out = self.art("next", "--tasks", flag, env=env).stdout
        self.assertIn("T-400", out); self.assertNotIn("T-300", out)
        self.assertEqual([read(self.top)[0]["status"], read(self.dl)[0]["status"]], ["open", "open"])

    def test_e_prompt_context_hook_root_only(self):
        write(self.top, [rec("T-001", status="in_progress"), rec("T-002")])
        env = {**self.env, "CLAUDE_PLUGIN_ROOT": str(REPO)}
        cp = subprocess.run(["sh", str(PROMPT_HOOK)], cwd=self.root, capture_output=True, text=True, env=env)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertIn("T-001 title T-001", cp.stdout, "in-progress task from <root>/tasks.jsonl not attached")
        self.assertNotIn("T-002", cp.stdout)

    def test_e2_prompt_context_hook_silent_without_task_file(self):
        env = {**self.env, "CLAUDE_PLUGIN_ROOT": str(REPO)}
        cp = subprocess.run(["sh", str(PROMPT_HOOK)], cwd=self.root, capture_output=True, text=True, env=env)
        self.assertEqual((cp.returncode, cp.stdout), (0, ""))


class Dialect(Base):
    def test_f_openai_dialect_round_trip(self):
        write(self.top, [rec("T-001", status="pending"), rec("T-002", status="completed", verification_evidence="e"),
                         rec("T-003", status="incomplete")])
        self.assertIn("T-001", self.art("next").stdout)   # pending reads as open
        self.art("validate")                                # completed reads as done, with evidence
        self.art("set", "T-001", "done", "--evidence", "pos+neg")
        self.assertEqual([r["status"] for r in read(self.top)], ["completed", "completed", "incomplete"])
        self.art("set", "T-001", "blocked")
        self.assertEqual(read(self.top)[0]["status"], "incomplete")
        self.art("set", "T-001", "pending")                # input in the file's own dialect is accepted too
        self.assertEqual(read(self.top)[0]["status"], "pending")
        line = self.top.read_text("utf-8").splitlines()[0]
        self.assertIn('"status": "pending"', line, "serialization changed (separators)")

    def test_f_legacy_file_keeps_legacy_words(self):
        write(self.dl, [rec("T-001"), rec("T-002", status="done", verification_evidence="e")])
        self.art("set", "T-001", "completed", "--evidence", "pos+neg")   # either dialect accepted as input
        self.assertEqual([r["status"] for r in read(self.dl)], ["done", "done"])
        self.art("set", "T-001", "incomplete")
        self.assertEqual(read(self.dl)[0]["status"], "blocked")

    def test_f_completed_without_evidence_is_invalid(self):
        write(self.top, [rec("T-001", status="completed")])
        cp = self.art("validate", check=False)
        self.assertEqual(cp.returncode, 1); self.assertIn("T-001: done without verification_evidence", cp.stderr)


class RenderGuard(Base):
    def test_g_foreign_tasks_md_left_alone(self):
        write(self.top, [rec("T-001")])
        foreign = "<!-- generated by another tool; do not edit -->\n# Tasks\n\nkeep me\n"
        (self.root / "TASKS.md").write_bytes(foreign.encode())
        cp = self.art("render")
        self.assertIn("TASKS.md owned by another renderer; skipped", cp.stdout)
        self.assertEqual((self.root / "TASKS.md").read_bytes(), foreign.encode())

    def test_g_own_banner_rewritten(self):
        write(self.top, [rec("T-001")])
        (self.root / "TASKS.md").write_text("# TASKS\n\nstale\n", "utf-8")
        self.art("render")
        md = (self.root / "TASKS.md").read_text("utf-8")
        self.assertNotIn("stale", md); self.assertIn("T-001", md)


class Ids(Base):
    def test_h_widened_id_regex(self):
        for good in ("T-001", "AGY-106..122", "AGY-503..AGY-510", "G-TASK 1", "T-031#2", "T-1-2"):
            self.assertEqual(artifacts.validate([rec(good)]), [], good)
        for bad in ("", "t-1", "T-1 ", " T-1", "T--1", "T-1#", "T-1\n", None):
            errs = artifacts.validate([rec(bad)])
            self.assertTrue(any("id must look like" in e for e in errs), repr(bad))

    def test_h_cli_validate_accepts_widened_ids(self):
        write(self.top, [rec("AGY-503..AGY-510"), rec("G-TASK 1"), rec("T-031#2", depends_on=["G-TASK 1"])])
        self.assertIn("tasks.jsonl ok: 3 tasks", self.art("validate").stdout)


class Limit(Base):
    def test_i_next_limit(self):
        write(self.top, [rec(f"T-{n:03d}") for n in range(1, 6)])
        out = self.art("next", "--limit", "2").stdout.splitlines()
        self.assertEqual(out, ["T-001  title T-001", "T-002  title T-002", "(+3 more)"])
        self.assertEqual(len(self.art("next").stdout.splitlines()), 5)       # default: unlimited
        self.assertEqual(len(self.art("next", "--limit", "5").stdout.splitlines()), 5)


class Lock(Base):
    def test_set_waits_for_the_lock(self):
        write(self.top, [rec("T-001")])
        lock = self.top.with_name("tasks.jsonl.lock")
        with open(lock, "a+") as fh:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
            p = subprocess.Popen([sys.executable, str(ART), "tasks", "set", "T-001", "in_progress", "--root", str(self.root)],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=self.env)
            time.sleep(1.0)
            self.assertIsNone(p.poll(), "set ran while another holder had the lock")
            self.assertEqual(read(self.top)[0]["status"], "open")
        self.assertEqual(p.wait(timeout=30), 0)
        self.assertEqual(read(self.top)[0]["status"], "in_progress")


class StickyDialect(Base):
    """Defect 1: the dialect is decided once and kept, even after the last openai-only word leaves the file."""
    def test_dialect_survives_losing_its_last_openai_word(self):
        write(self.top, [rec("T-001", "pending"), rec("T-002", "in_progress")])
        self.art("set", "T-001", "in_progress")   # no record says pending/completed/incomplete any more
        self.art("set", "T-002", "done", "--evidence", "pos+neg")
        st = {r["id"]: r["status"] for r in read(self.top) if "id" in r}
        self.assertEqual(st["T-002"], "completed", "an openai-dialect file was written a legacy word")
        self.assertEqual(st["T-001"], "in_progress")
        self.art("set", "T-001", "open")
        st = {r["id"]: r["status"] for r in read(self.top) if "id" in r}
        self.assertEqual(st["T-001"], "pending")
        self.assertIn("ok: 2 tasks", self.art("validate").stdout)    # the marker line is not a task

    def test_explicit_marker_wins(self):
        self.top.write_text(json.dumps({"_dialect": "openai"}) + "\n" + json.dumps(rec("T-001", "in_progress")) + "\n", "utf-8")
        self.art("set", "T-001", "blocked")
        self.assertEqual([r["status"] for r in read(self.top) if "id" in r], ["incomplete"])
        self.assertEqual(self.top.read_text("utf-8").splitlines()[0], json.dumps({"_dialect": "openai"}))

    def test_legacy_file_gets_no_marker(self):
        write(self.top, [rec("T-001"), rec("T-002", "in_progress")])
        before = self.top.read_text("utf-8").splitlines()
        self.art("set", "T-001", "in_progress")
        after = self.top.read_text("utf-8").splitlines()
        self.assertEqual(len(after), 2); self.assertEqual(after[1], before[1])


class OnlyTheTarget(Base):
    """Defect 2: a mutating op rewrites only the record it targets; every other line keeps its bytes."""
    def test_mixed_file_set_touches_one_line(self):
        # Hand-written lines: odd spacing and key order no serialiser would produce, both dialects mixed.
        lines = ['{"id": "T-001", "status": "pending",  "title": "a", "type": "task"}',
                 '{"title":"b","id":"T-002","status":"open","type":"task"}',
                 '{"id": "T-003", "status": "completed", "verification_evidence": "x", "title": "c", "type": "task"}',
                 '{"id": "T-004", "status": "done", "verification_evidence": "x", "title": "d", "type": "task"}',
                 '{"id": "T-005", "status": "incomplete", "title": "\u00e9", "type": "task"}']
        self.top.write_bytes(("\n".join(lines) + "\n").encode())
        self.art("set", "T-002", "in_progress")
        after = self.top.read_bytes().decode().splitlines()
        self.assertEqual(len(after), len(lines))
        for i, (b, a) in enumerate(zip(lines, after)):
            if i == 1:
                self.assertNotEqual(a, b); self.assertEqual(json.loads(a)["status"], "in_progress")
            else:
                self.assertEqual(a.encode(), b.encode(), f"untouched line {i + 1} was rewritten")

    def test_add_appends_without_rewriting(self):
        lines = ['{"id":"T-001","status":"pending","title":"a"}', '', '{"id":"T-002","status":"open","title":"b"}']
        self.top.write_bytes(("\n".join(lines) + "\n").encode())
        self.art("add", "--id", "T-003", "--title", "c")
        after = self.top.read_bytes().decode().splitlines()
        self.assertEqual(after[:3], lines)
        self.assertEqual(json.loads(after[3])["id"], "T-003")


def snapshot(root: Path) -> dict:
    return {str(p.relative_to(root)): (p.read_bytes() if p.is_file() else None)
            for p in root.rglob("*") if ".git" not in p.relative_to(root).parts}


class FailedOpLeavesNoTrace(Base):
    """Defect 3: a refused mutating op creates no directory, no lock file, nothing."""
    def test_set_without_task_file(self):
        before = snapshot(self.root)
        cp = self.art("set", "T-1", "done", check=False)
        self.assertNotEqual(cp.returncode, 0)
        self.assertEqual(snapshot(self.root), before)
        self.assertFalse((self.root / ".devloop").exists())

    def test_refusals_with_a_task_file(self):
        write(self.top, [rec("T-001")])
        before = snapshot(self.root)
        for args in (("set", "T-999", "open"), ("set", "T-001", "bogus"), ("set", "T-001", "done"),
                     ("reconcile", "T-999"), ("add", "--id", "T-001", "--title", "dup"),
                     ("add", "--id", "bad id", "--title", "x"), ("add", "--id", "T-002", "--title", "x", "--depends", "T-404")):
            cp = self.art(*args, check=False)
            self.assertNotEqual(cp.returncode, 0, args)
            self.assertEqual(snapshot(self.root), before, f"{args} left a trace")

    def test_fold_without_task_file_creates_nothing(self):
        before = snapshot(self.root)
        self.art("fold-stale")
        self.assertEqual(snapshot(self.root), before)


class Overrides(Base):
    """Defect 4: TASKS.md carries an operator overrides block that render keeps and readers apply."""
    def test_block_kept_and_applied(self):
        write(self.top, [rec("T-001"), rec("T-002")])
        self.art("render")
        md = (self.root / "TASKS.md").read_text("utf-8")
        self.assertIn(artifacts.OVERRIDES_BEGIN, md); self.assertIn(artifacts.OVERRIDES_END, md)
        block = ["Operator note: T-001 waits on an outside party.", "```jsonl",
                 '{"id": "T-001", "status": "blocked", "owner": "ops"}', "```"]
        b, e = md.index(artifacts.OVERRIDES_BEGIN), md.index(artifacts.OVERRIDES_END)
        md = md[:b] + artifacts.OVERRIDES_BEGIN + "\n" + "\n".join(block) + "\n" + md[e:]
        (self.root / "TASKS.md").write_text(md, "utf-8")
        store = self.top.read_bytes()
        self.assertEqual(self.art("next").stdout.splitlines(), ["T-002  title T-002"])   # applied on read
        self.art("render")
        md2 = (self.root / "TASKS.md").read_text("utf-8")
        self.assertIn(artifacts.OVERRIDES_BEGIN + "\n" + "\n".join(block) + "\n" + artifacts.OVERRIDES_END, md2)
        self.assertIn("**T-001** title T-001 **[blocked]** @ops", md2)
        self.assertEqual(self.top.read_bytes(), store, "reading overrides must not write the store")
        lane = json.loads(self.art("lane", "T-001").stdout)
        self.assertIsInstance(lane, dict)

    def test_unknown_or_malformed_override_is_an_error(self):
        write(self.top, [rec("T-001")])
        self.art("render")
        md = (self.root / "TASKS.md").read_text("utf-8")
        e = md.index(artifacts.OVERRIDES_END)
        (self.root / "TASKS.md").write_text(md[:e] + '{"id": "T-404", "status": "done"}\n' + md[e:], "utf-8")
        cp = self.art("validate", check=False)
        self.assertNotEqual(cp.returncode, 0); self.assertIn("T-404", cp.stderr)
        (self.root / "TASKS.md").write_text(md[:e] + '{"id": "T-001", \n' + md[e:], "utf-8")
        self.assertNotEqual(self.art("next", check=False).returncode, 0)

    def test_foreign_tasks_md_has_no_overrides(self):
        write(self.top, [rec("T-001")])
        (self.root / "TASKS.md").write_text("# Other\n<!-- overrides:begin -->\n{\"id\": \"T-001\", \"status\": \"blocked\"}\n<!-- overrides:end -->\n", "utf-8")
        self.assertEqual(self.art("next").stdout.splitlines(), ["T-001  title T-001"])


class GoalImport(unittest.TestCase):
    def test_goal_py_inserts_its_dir_once(self):
        src = (SCRIPTS / "goal.py").read_text("utf-8")
        self.assertEqual(src.count("sys.path.insert("), 1)


if __name__ == "__main__":
    os.chdir(tempfile.gettempdir())
    unittest.main(verbosity=2)
