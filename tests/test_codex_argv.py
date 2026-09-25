#!/usr/bin/env python3
"""The codex lane argv must parse under the REAL `codex exec`.

codex-cli 0.155.1 rejects `--ask-for-approval` after `exec` ("unexpected argument", rc 2): it is a
top-level flag. The adapter passed it there, so every codex lane died before its first turn. The
policy now goes in as `-c approval_policy=<value>`.

Controls, both against the installed binary (no model call: `--help` replaces the prompt, and clap
parses every flag before printing help):
  positive  the adapter's argv parses (rc 0)
  negative  the same argv with the old flag spliced back in fails (rc != 0) and names the flag
Skipped, not passed, when `codex` is not on PATH.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "skills" / "dev-loop" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import adapters  # noqa: E402


def codex_argv(tmp: Path, permission_mode: str | None = None) -> list[str]:
    worker = {"harness": "codex", "timeout_s": 60, "max_turns": 5}
    if permission_mode:
        worker["permission_mode"] = permission_mode
    lane = {"id": "codex-argv-01", "objective": "noop", "worker": worker}
    wt = tmp / "wt"; wt.mkdir(exist_ok=True)
    prompt = tmp / "prompt.txt"; prompt.write_text("noop", encoding="utf-8")
    lane_json = tmp / "lane.json"; lane_json.write_text(json.dumps(lane), encoding="utf-8")
    return adapters.build_argv(lane, wt, tmp / "report.json", lane_json, SCRIPTS.parent / "SKILL.md", prompt)


class CodexArgvShape(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory(); self.tmp = Path(self._td.name)

    def tearDown(self):
        self._td.cleanup()

    def test_policy_is_a_config_override_not_the_top_level_flag(self):
        argv = codex_argv(self.tmp)
        self.assertEqual(argv[:2], ["codex", "exec"])
        self.assertNotIn("--ask-for-approval", argv)
        i = argv.index("-c")
        self.assertEqual(argv[i + 1], "approval_policy=never")

    def test_worker_permission_mode_carries_through(self):
        argv = codex_argv(self.tmp, "on-request")
        self.assertEqual(argv[argv.index("-c") + 1], "approval_policy=on-request")


@unittest.skipUnless(shutil.which("codex"), "codex not on PATH")
class CodexArgvParsesUnderRealBinary(unittest.TestCase):
    def setUp(self):
        self._td = tempfile.TemporaryDirectory(); self.tmp = Path(self._td.name)

    def tearDown(self):
        self._td.cleanup()

    def parse(self, argv: list[str]) -> subprocess.CompletedProcess:
        # the prompt is the last element; --help in its place parses every flag, runs nothing
        return subprocess.run([*argv[:-1], "--help"], capture_output=True, text=True, timeout=60)

    def test_adapter_argv_parses(self):
        r = self.parse(codex_argv(self.tmp))
        self.assertEqual(r.returncode, 0, r.stderr[-400:])

    def test_old_flag_is_rejected_by_name(self):
        argv = codex_argv(self.tmp)
        i = argv.index("-c")
        old = argv[:i] + ["--ask-for-approval", "never"] + argv[i + 2:]
        r = self.parse(old)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("--ask-for-approval", r.stderr)


if __name__ == "__main__":
    unittest.main()
