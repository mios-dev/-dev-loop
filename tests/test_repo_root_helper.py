#!/usr/bin/env python3
"""Behavioural gate for the shared repo-root helper and the explicit --template-dir (stdlib only).

Properties under test, each both ways:
  * scripts/repo_root.py is the ONE resolver: it finds the work-tree top from a nested
    directory (git present, and by the `.git` walk when git is absent -- including a linked
    worktree's `.git` pointer FILE), and outside a repository it FAILS instead of silently
    returning the current directory. The CLIs turn that into one clean line and exit 2.
  * ship.py / triage.py / research.py copy templates from exactly one directory: the
    skill's shipped assets/templates, or the one named by --template-dir. A
    `reference/templates` directory in the TARGET repo is read only when it is passed
    explicitly -- never as a fallback, even when the shipped templates are missing.
  * goal.py / research.py / review.py / ship.py / triage.py each still run `--help` by path.

Run directly:  python3 tests/test_repo_root_helper.py
"""

import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "skills" / "dev-loop" / "scripts"
SHIPPED = REPO / "skills" / "dev-loop" / "assets" / "templates"
FIVE = ("goal.py", "research.py", "review.py", "ship.py", "triage.py")

# (script, argv that scaffolds, template it reads, file it writes)
SCAFFOLDERS = (
    ("ship.py", ["--init"], "RELEASE_CHECKLIST.md", "RELEASE_CHECKLIST.md"),
    ("triage.py", ["--init"], "TRIAGE_INCIDENT.md", "INCIDENT_TRIAGE.md"),
    ("research.py", ["template", "spike"], "SPIKE.md", "SPIKE.md"),
)

FOREIGN = "FOREIGN reference/templates content -- must never be read implicitly\n"
CUSTOM = "CUSTOM --template-dir content\n"


def load_helper():
    spec = importlib.util.spec_from_file_location("repo_root_under_test", SCRIPTS / "repo_root.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Base(unittest.TestCase):
    def tmp(self) -> Path:
        d = Path(tempfile.mkdtemp(prefix="repo-root-gate-")).resolve()
        self.addCleanup(shutil.rmtree, d, True)
        return d

    def env(self, **extra):
        # GIT_CEILING_DIRECTORIES keeps git from climbing out of the temp dir into
        # whatever checkout happens to contain it.
        e = {**os.environ, "GIT_CEILING_DIRECTORIES": tempfile.gettempdir()}
        e.update(extra)
        return e

    def git_repo(self) -> Path:
        d = self.tmp() / "target"
        d.mkdir()
        subprocess.run(["git", "init", "-q", str(d)], check=True, env=self.env())
        return d

    def run_script(self, script: Path, args, cwd: Path, **env):
        return subprocess.run([sys.executable, str(script), *args], cwd=str(cwd),
                              capture_output=True, text=True, timeout=120, env=self.env(**env))


class FindRepoRoot(Base):
    @classmethod
    def setUpClass(cls):
        cls.h = load_helper()

    def test_finds_root_from_a_nested_dir(self):
        repo = self.git_repo()
        nested = repo / "a" / "b" / "c"
        nested.mkdir(parents=True)
        self.assertEqual(self.h.find_repo_root(nested), repo)

    def test_outside_a_repo_raises_instead_of_returning_cwd(self):
        outside = self.tmp() / "not-a-repo" / "deeper"
        outside.mkdir(parents=True)
        old = os.environ.get("GIT_CEILING_DIRECTORIES")
        os.environ["GIT_CEILING_DIRECTORIES"] = tempfile.gettempdir()
        try:
            with self.assertRaises(self.h.RepoRootError) as caught:
                self.h.find_repo_root(outside)
        finally:
            if old is None:
                os.environ.pop("GIT_CEILING_DIRECTORIES", None)
            else:
                os.environ["GIT_CEILING_DIRECTORIES"] = old
        self.assertIn(str(outside), str(caught.exception))

    def test_walk_fallback_without_git_on_path(self):
        """No git binary: the `.git` walk still finds the top, a pointer FILE counts (linked
        worktree), and a tree with no `.git` anywhere still raises."""
        base = self.tmp()
        wt = base / "wt"
        (wt / "x" / "y").mkdir(parents=True)
        (wt / ".git").write_text("gitdir: /nowhere/.git/worktrees/wt\n")   # pointer file
        bare = base / "bare" / "z"
        bare.mkdir(parents=True)
        probe = (
            "import sys, importlib.util as u\n"
            f"s=u.spec_from_file_location('h', {str(SCRIPTS / 'repo_root.py')!r}); h=u.module_from_spec(s); s.loader.exec_module(h)\n"
            "print(h.find_repo_root(sys.argv[1]))\n"
            "try:\n    h.find_repo_root(sys.argv[2]); print('NO-RAISE')\n"
            "except h.RepoRootError: print('RAISED')\n"
        )
        p = subprocess.run([sys.executable, "-c", probe, str(wt / "x" / "y"), str(bare)],
                           capture_output=True, text=True, timeout=60, env=self.env(PATH=""))
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(p.stdout.splitlines(), [str(wt), "RAISED"])

    def test_cli_outside_a_repo_fails_cleanly(self):
        outside = self.tmp() / "not-a-repo"
        outside.mkdir()
        for script in FIVE:
            args = {"research.py": ["search", "x"], "goal.py": ["eval"]}.get(script, [])
            with self.subTest(script=script):
                p = self.run_script(SCRIPTS / script, args, outside)
                self.assertEqual(p.returncode, 2, p.stdout + p.stderr)
                self.assertIn("error: not inside a git repository", p.stderr)
                self.assertNotIn("Traceback", p.stderr)
                self.assertNotIn("fatal:", p.stderr)
                self.assertFalse((outside / ".devloop").exists(),
                                 "nothing may be written into a directory that is not a repo")


class OneResolver(Base):
    def test_no_script_defines_its_own_resolver(self):
        for script in FIVE:
            with self.subTest(script=script):
                src = (SCRIPTS / script).read_text()
                self.assertNotIn("def _find_repo_root", src)
                self.assertNotIn("--show-toplevel", src)
                self.assertRegex(src, r"(?m)^from repo_root import .*\bfind_repo_root\b")

    def test_no_script_names_reference_templates(self):
        for script in FIVE:
            with self.subTest(script=script):
                src = (SCRIPTS / script).read_text()
                self.assertIsNone(re.search(r"[\"']reference[\"']\s*\)?\s*/\s*[\"']templates[\"']", src),
                                  f"{script} builds a reference/templates path")

    def test_each_script_runs_help_by_path(self):
        outside = self.tmp()      # --help must not need a repository either
        for script in FIVE:
            with self.subTest(script=script):
                p = self.run_script(SCRIPTS / script, ["--help"], outside)
                self.assertEqual(p.returncode, 0, p.stderr)
                self.assertIn("usage:", p.stdout)


class TemplateDir(Base):
    def target_with_foreign_templates(self) -> Path:
        repo = self.git_repo()
        ref = repo / "reference" / "templates"
        ref.mkdir(parents=True)
        for _, _, tmpl, _ in SCAFFOLDERS:
            (ref / tmpl).write_text(FOREIGN)
        return repo

    def test_default_reads_the_shipped_templates(self):
        repo = self.target_with_foreign_templates()
        for script, args, tmpl, out in SCAFFOLDERS:
            with self.subTest(script=script):
                p = self.run_script(SCRIPTS / script, args, repo)
                self.assertEqual(p.returncode, 0, p.stderr)
                self.assertEqual((repo / out).read_bytes(), (SHIPPED / tmpl).read_bytes())

    def test_template_dir_overrides(self):
        repo = self.git_repo()
        custom = self.tmp() / "custom"
        custom.mkdir()
        for script, args, tmpl, out in SCAFFOLDERS:
            (custom / tmpl).write_text(CUSTOM)
            with self.subTest(script=script):
                p = self.run_script(SCRIPTS / script, [*args, "--template-dir", str(custom)], repo)
                self.assertEqual(p.returncode, 0, p.stderr)
                self.assertEqual((repo / out).read_text(), CUSTOM)

    def test_template_dir_that_lacks_the_template_fails_and_does_not_fall_back(self):
        repo = self.target_with_foreign_templates()
        empty = self.tmp() / "empty"
        empty.mkdir()
        for script, args, tmpl, out in SCAFFOLDERS:
            with self.subTest(script=script):
                p = self.run_script(SCRIPTS / script, [*args, "--template-dir", str(empty)], repo)
                self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
                self.assertIn("not found", p.stderr)
                self.assertFalse((repo / out).exists(),
                                 f"{out} written from somewhere other than --template-dir")

    def test_target_reference_templates_not_read_when_shipped_templates_are_missing(self):
        """The audit's case: a scripts/ copy with no assets/templates next to it (a partial
        install), run inside a foreign repo that happens to carry reference/templates. The
        old fallback silently read the foreign file; now it must fail and write nothing."""
        repo = self.target_with_foreign_templates()
        lone = self.tmp() / "lone-skill" / "scripts"
        lone.mkdir(parents=True)
        for f in ("repo_root.py", "ship.py", "triage.py", "research.py", "review.py"):
            shutil.copy2(SCRIPTS / f, lone / f)
        for script, args, tmpl, out in SCAFFOLDERS:
            with self.subTest(script=script):
                p = self.run_script(lone / script, args, repo)
                self.assertNotEqual(p.returncode, 0, p.stdout + p.stderr)
                self.assertFalse((repo / out).exists() and (repo / out).read_text() == FOREIGN,
                                 f"{script} read the target's reference/templates implicitly")
                self.assertFalse((repo / out).exists(), f"{out} was written")

    def test_target_reference_templates_read_when_passed_explicitly(self):
        repo = self.target_with_foreign_templates()
        for script, args, tmpl, out in SCAFFOLDERS:
            with self.subTest(script=script):
                p = self.run_script(SCRIPTS / script,
                                    [*args, "--template-dir", str(repo / "reference" / "templates")], repo)
                self.assertEqual(p.returncode, 0, p.stderr)
                self.assertEqual((repo / out).read_text(), FOREIGN)


if __name__ == "__main__":
    os.chdir(tempfile.gettempdir())   # never resolve the repo root from CWD
    unittest.main(verbosity=2)
