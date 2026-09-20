#!/usr/bin/env python3
"""
Unit tests for native /teamwork-preview multi-agent workflow support in dev-loop.

Covers:
1. Harness specification parity and build_argv for antigravity-teamwork
2. Layout compliance linter for .agents/ directory (metadata only)
3. Receipt harvesting from 5-component teamwork handoffs to .devloop/LEDGER.md
4. Base-tree guard and anchor enforcement for .agents/
5. scan_teamwork_state parsing, heartbeat tracking, and terminal role detection
6. Objective sanitization to prevent request accumulation bug
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "skills" / "dev-loop" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import adapters
import agy_session


def init_git_repo(d: Path) -> Path:
    subprocess.run(["git", "init", "-q", str(d)], check=True)
    subprocess.run(["git", "-C", str(d), "config", "user.email", "test@example.com"], check=True)
    subprocess.run(["git", "-C", str(d), "config", "user.name", "Test Runner"], check=True)
    (d / "README.md").write_text("# Repo\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(d), "add", "README.md"], check=True)
    subprocess.run(["git", "-C", str(d), "commit", "-qm", "initial commit"], check=True)
    return d


class TestTeamworkHarness(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="tw-harness-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_harness_registered(self):
        self.assertIn("antigravity-teamwork", adapters.HARNESSES)
        self.assertEqual(adapters.BINARY.get("antigravity-teamwork"), "agy")
        self.assertEqual(adapters.V1_HARNESS.get("teamwork"), "antigravity-teamwork")
        self.assertEqual(adapters.V1_HARNESS.get("antigravity-teamwork"), "antigravity-teamwork")
        flags = adapters.PROBE_FLAGS.get("antigravity-teamwork", [])
        self.assertIn("-p", flags)
        self.assertIn("--output-format", flags)
        self.assertIn("--print-timeout", flags)
        self.assertIn("--dangerously-skip-permissions", flags)

    def test_build_argv_formats_teamwork_prompt(self):
        lane = {
            "id": "tw-1",
            "objective": "Build milestone 1 native teamwork",
            "worker": {
                "harness": "antigravity-teamwork",
                "timeout_s": 1200,
                "max_turns": 10,
                "model": "gemini-3.1-pro-high",
                "effort": "high",
                "sandbox": "workspace-write"
            }
        }
        pf = self.tmp / "prompt.md"
        pf.write_text(lane["objective"], encoding="utf-8")
        argv = adapters.build_argv(lane, self.tmp / "wt", self.tmp / "report.json",
                                  self.tmp / "lane.json", adapters.SKILL_DEFAULT, pf)
        self.assertEqual(argv[0], "agy")
        self.assertEqual(argv[1], "-p")
        self.assertEqual(argv[2], "/teamwork-preview Build milestone 1 native teamwork")
        self.assertIn("--output-format", argv)
        self.assertIn("json", argv)
        self.assertIn("--print-timeout", argv)
        self.assertIn("1200s", argv)
        self.assertIn("--dangerously-skip-permissions", argv)
        self.assertIn("--model", argv)
        self.assertIn("gemini-3.1-pro-high", argv)
        self.assertIn("--effort", argv)
        self.assertIn("high", argv)
        self.assertIn("--sandbox", argv)
        self.assertIn("workspace-write", argv)

    def test_build_argv_avoids_duplicate_slash_command(self):
        lane = {
            "id": "tw-2",
            "objective": "/teamwork-preview Already prefixed prompt",
            "worker": {
                "harness": "antigravity-teamwork",
                "timeout_s": 600,
                "max_turns": 5
            }
        }
        pf = self.tmp / "prompt.md"
        pf.write_text(lane["objective"], encoding="utf-8")
        argv = adapters.build_argv(lane, self.tmp / "wt", self.tmp / "report.json",
                                  self.tmp / "lane.json", adapters.SKILL_DEFAULT, pf)
        self.assertEqual(argv[2], "/teamwork-preview Already prefixed prompt")

    def test_build_argv_handles_leading_whitespace_without_duplicate_prefix(self):
        lane = {
            "id": "tw-3",
            "objective": "   /teamwork-preview Whitespace prefixed prompt  ",
            "worker": {
                "harness": "antigravity-teamwork",
                "timeout_s": 600,
                "max_turns": 5
            }
        }
        pf = self.tmp / "prompt.md"
        pf.write_text(lane["objective"], encoding="utf-8")
        argv = adapters.build_argv(lane, self.tmp / "wt", self.tmp / "report.json",
                                  self.tmp / "lane.json", adapters.SKILL_DEFAULT, pf)
        self.assertEqual(argv[2], "/teamwork-preview Whitespace prefixed prompt")

        lane_unprefixed = {
            "id": "tw-4",
            "objective": "   Whitespace prompt without slash command  ",
            "worker": {
                "harness": "antigravity-teamwork",
                "timeout_s": 600,
                "max_turns": 5
            }
        }
        pf2 = self.tmp / "prompt2.md"
        pf2.write_text(lane_unprefixed["objective"], encoding="utf-8")
        argv2 = adapters.build_argv(lane_unprefixed, self.tmp / "wt", self.tmp / "report.json",
                                   self.tmp / "lane.json", adapters.SKILL_DEFAULT, pf2)
        self.assertEqual(argv2[2], "/teamwork-preview Whitespace prompt without slash command")



class TestLayoutLinter(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="layout-linter-"))
        init_git_repo(self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_clean_agents_metadata_passes(self):
        agents_dir = self.tmp / ".agents"
        worker_dir = agents_dir / "worker_1"
        worker_dir.mkdir(parents=True, exist_ok=True)
        (agents_dir / "ORIGINAL_REQUEST.md").write_text("# Request\n", encoding="utf-8")
        (worker_dir / "DISPATCH.md").write_text("# Dispatch\n", encoding="utf-8")
        (worker_dir / "BRIEFING.md").write_text("# Briefing\n", encoding="utf-8")
        (worker_dir / "progress.md").write_text("# Progress\n", encoding="utf-8")
        (worker_dir / "handoff.md").write_text("# Handoff\n", encoding="utf-8")
        (worker_dir / "state.json").write_text("{}", encoding="utf-8")
        (worker_dir / "config.toml").write_text("k = 'v'\n", encoding="utf-8")
        (worker_dir / "meta.yaml").write_text("k: v\n", encoding="utf-8")
        (worker_dir / "diff.patch").write_text("diff\n", encoding="utf-8")
        (worker_dir / "run.log").write_text("log\n", encoding="utf-8")

        violations = adapters.validate_agents_metadata_layout(self.tmp)
        self.assertEqual(violations, [])

    def test_unauthorized_source_in_agents_detected(self):
        agents_dir = self.tmp / ".agents" / "rogue_agent"
        agents_dir.mkdir(parents=True, exist_ok=True)
        (agents_dir / "DISPATCH.md").write_text("# Dispatch\n", encoding="utf-8")
        (agents_dir / "planted_code.py").write_text("print('planted')\n", encoding="utf-8")
        (agents_dir / "planted_test.rs").write_text("fn test() {}\n", encoding="utf-8")
        (agents_dir / "malicious.sh").write_text("#!/bin/sh\n", encoding="utf-8")

        violations = adapters.validate_agents_metadata_layout(self.tmp)
        self.assertEqual(len(violations), 3)
        self.assertIn(".agents/rogue_agent/planted_code.py", violations)
        self.assertIn(".agents/rogue_agent/planted_test.rs", violations)
        self.assertIn(".agents/rogue_agent/malicious.sh", violations)

    def test_cmd_base_audit_fails_closed_on_agents_leakage(self):
        agents_dir = self.tmp / ".agents" / "worker_1"
        agents_dir.mkdir(parents=True, exist_ok=True)
        (agents_dir / "leak.py").write_text("# leaked source\n", encoding="utf-8")

        snap_file = self.tmp / "snap.json"
        class Args:
            root = str(self.tmp)
            before = None
            save = str(snap_file)
            lanes = None

        with self.assertRaises(SystemExit) as cm:
            adapters.cmd_base_audit(Args())
        self.assertEqual(cm.exception.code, 6)

    def test_cmd_base_audit_clean_repo_exits_zero(self):
        agents_dir = self.tmp / ".agents" / "worker_1"
        agents_dir.mkdir(parents=True, exist_ok=True)
        (agents_dir / "DISPATCH.md").write_text("# Dispatch\n", encoding="utf-8")

        class Args:
            root = str(self.tmp)
            before = None
            save = None
            lanes = None

        adapters.cmd_base_audit(Args())


class TestReceiptHarvesting(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="receipt-harvest-"))
        init_git_repo(self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_harvest_receipt_appends_ralph_ledger_entry(self):
        auditor_dir = self.tmp / ".agents" / "auditor_1"
        auditor_dir.mkdir(parents=True, exist_ok=True)
        handoff_file = auditor_dir / "handoff.md"
        handoff_file.write_text(
            "# Handoff Report: Auditor Turn\n\n"
            "## 1. Observation\n"
            "All units green. Git status clean.\n\n"
            "## 2. Logic Chain\n"
            "Evidence confirms zero leakage and all unit tests passed.\n\n"
            "## 3. Caveats\n"
            "Requires bare-metal validation for NTFS mounts.\n\n"
            "## 4. Conclusion\n"
            "Native teamwork preview verified with zero regressions.\n\n"
            "## 5. Verification Method\n"
            "python3 -m unittest tests/test_teamwork_adapter.py\n",
            encoding="utf-8"
        )

        prompt_file = self.tmp / ".devloop" / "teamwork-prompt.txt"
        prompt_file.parent.mkdir(parents=True, exist_ok=True)
        prompt_file.write_text("/teamwork-preview Implement Milestone 1\n", encoding="utf-8")

        agy_session.harvest_teamwork_receipt(self.tmp, handoff_file, prompt_file)

        ledger_file = self.tmp / ".devloop" / "LEDGER.md"
        self.assertTrue(ledger_file.is_file(), "LEDGER.md was not created")
        ledger_text = ledger_file.read_text(encoding="utf-8")

        self.assertIn("teamwork-done", ledger_text)
        self.assertIn("Implement Milestone 1", ledger_text)
        self.assertIn("Native teamwork preview verified with zero regressions.", ledger_text)
        self.assertIn("Requires bare-metal validation for NTFS mounts.", ledger_text)
        self.assertIn("python3 -m unittest tests/test_teamwork_adapter.py", ledger_text)

    def test_harvest_receipt_fallback_to_prefixed_original_request(self):
        auditor_dir = self.tmp / ".agents" / "auditor_1"
        auditor_dir.mkdir(parents=True, exist_ok=True)
        handoff_file = auditor_dir / "handoff.md"
        handoff_file.write_text(
            "# Handoff Report: Auditor Turn\n\n"
            "## 4. Conclusion\n"
            "Autonomous cycle verified.\n\n"
            "## 5. Verification Method\n"
            "pytest\n",
            encoding="utf-8"
        )

        orig_req = self.tmp / ".agents" / "ORIGINAL_REQUEST.md"
        orig_req.write_text(
            "# Original User Request\n\n"
            "## Initial Request — 2026-09-19T16:39:02Z\n\n"
            "First historical request\n\n"
            "## Follow-up — 2026-09-20T16:12:25Z\n"
            "Implement inherent Antigravity /teamwork-preview multi-agent workflow orchestration\n",
            encoding="utf-8"
        )

        agy_session.harvest_teamwork_receipt(self.tmp, handoff_file, prompt_file=None)

        ledger_file = self.tmp / ".devloop" / "LEDGER.md"
        self.assertTrue(ledger_file.is_file(), "LEDGER.md was not created")
        ledger_text = ledger_file.read_text(encoding="utf-8")

        self.assertIn("Implement inherent Antigravity /teamwork-preview", ledger_text)
        self.assertNotIn("Teamwork execution\n", ledger_text)

    def test_harvest_receipt_matches_real_antigravity_headers(self):
        auditor_dir = self.tmp / ".agents" / "auditor_1"
        auditor_dir.mkdir(parents=True, exist_ok=True)
        handoff_file = auditor_dir / "handoff.md"
        handoff_file.write_text("## 4. Conclusion\nDone\n## 5. Verification Method\ncheck\n", encoding="utf-8")

        (self.tmp / ".agents" / "ORIGINAL_REQUEST.md").write_text(
            "# Original User Request\n\n## 2026-09-19T20:00:00Z\n\nImplement inherent Antigravity /teamwork-preview\n",
            encoding="utf-8",
        )
        agy_session.harvest_teamwork_receipt(self.tmp, handoff_file, prompt_file=None)
        ledger_text = (self.tmp / ".devloop" / "LEDGER.md").read_text(encoding="utf-8")
        self.assertIn("Implement inherent Antigravity", ledger_text)


class TestBaseTreeGuardWithAgents(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="basetree-agents-"))
        init_git_repo(self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_agents_allowed_in_always_allowed(self):
        self.assertIn(".agents/", adapters.BASE_TREE_ALWAYS_ALLOWED)
        self.assertIn(".agents/", agy_session.BASE_TREE_ALWAYS_ALLOWED)

    def test_metadata_in_agents_is_not_stray(self):
        before = agy_session.base_tree_state(self.tmp)
        agents_dir = self.tmp / ".agents" / "worker_1"
        agents_dir.mkdir(parents=True, exist_ok=True)
        (agents_dir / "progress.md").write_text("# Progress\n", encoding="utf-8")

        allowed = agy_session.BASE_TREE_ALWAYS_ALLOWED + (".worktrees/",)
        now = agy_session.base_tree_state(self.tmp)
        strays = agy_session.stray_base_edits(before, now, allowed)
        self.assertEqual(strays, [], "Edits under .agents/ must be permitted by base-tree guard")

    def test_base_tree_outside_agents_still_caught(self):
        before = agy_session.base_tree_state(self.tmp)
        (self.tmp / "stray.txt").write_text("leaked file\n", encoding="utf-8")

        allowed = agy_session.BASE_TREE_ALWAYS_ALLOWED + (".worktrees/",)
        now = agy_session.base_tree_state(self.tmp)
        strays = agy_session.stray_base_edits(before, now, allowed)
        self.assertEqual(strays, ["stray.txt"])

    def test_allowlist_anchoring_prevents_agents_scratch(self):
        before = agy_session.base_tree_state(self.tmp)
        scratch_dir = self.tmp / ".agents-scratch"
        scratch_dir.mkdir(parents=True, exist_ok=True)
        (scratch_dir / "unauthorized.txt").write_text("rogue\n", encoding="utf-8")

        allowed = agy_session.BASE_TREE_ALWAYS_ALLOWED + (".worktrees/",)
        now = agy_session.base_tree_state(self.tmp)
        strays = agy_session.stray_base_edits(before, now, allowed)
        self.assertEqual(strays, [".agents-scratch/"])


class TestScanTeamworkState(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="teamwork-state-"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_scan_empty_agents_dir(self):
        st = agy_session.scan_teamwork_state(self.tmp / ".agents", time.time())
        self.assertFalse(st["live"])
        self.assertEqual(st["agents"], {})
        self.assertIsNone(st["terminal_handoff"])

    def test_scan_subagents_and_heartbeats(self):
        agents_dir = self.tmp / ".agents"
        now = time.time()
        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now))

        w1 = agents_dir / "worker_impl_1"
        w1.mkdir(parents=True, exist_ok=True)
        (w1 / "progress.md").write_text(
            f"# Progress\n\n- **Last visited**: {now_iso}\n- **Status**: in-progress\n- **Current Step**: coding\n",
            encoding="utf-8"
        )

        st = agy_session.scan_teamwork_state(agents_dir, now)
        self.assertTrue(st["live"])
        self.assertIn("worker_impl_1", st["agents"])
        self.assertEqual(st["agents"]["worker_impl_1"]["status"], "in-progress")
        self.assertEqual(st["agents"]["worker_impl_1"]["current_step"], "coding")
        self.assertFalse(st["agents"]["worker_impl_1"]["has_handoff"])
        self.assertIsNone(st["terminal_handoff"])

    def test_scan_detects_terminal_auditor_handoff(self):
        agents_dir = self.tmp / ".agents"
        now = time.time()

        aud = agents_dir / "auditor_1"
        aud.mkdir(parents=True, exist_ok=True)
        (aud / "progress.md").write_text("- **Last visited**: 2026-09-20T16:00:00Z\n- **Status**: done\n", encoding="utf-8")
        handoff_file = aud / "handoff.md"
        handoff_file.write_text("## 4. Conclusion\nDone\n## 5. Verification Method\npytest\n", encoding="utf-8")

        st = agy_session.scan_teamwork_state(agents_dir, now)
        self.assertEqual(st["terminal_handoff"], handoff_file)


class TestObjectiveSanitization(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="obj-sanit-"))
        init_git_repo(self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_objective_accumulation_prevented_by_archiving(self):
        agents_dir = self.tmp / ".agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        orig_req = agents_dir / "ORIGINAL_REQUEST.md"
        orig_req.write_text("# Request\n\n## 2026-09-18T10:00:00Z\nOld dead objective\n", encoding="utf-8")

        # Simulate cmd_teamwork request writing logic
        if orig_req.is_file():
            archive_path = agents_dir / f"ORIGINAL_REQUEST_ARCHIVE_{int(time.time())}.md"
            shutil.move(str(orig_req), str(archive_path))

        now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        new_obj = "Fresh isolated objective"
        orig_req.write_text(f"# Original User Request\n\n## {now_iso}\n\n{new_obj}\n", encoding="utf-8")

        # Verify old request archived and new request clean
        archives = list(agents_dir.glob("ORIGINAL_REQUEST_ARCHIVE_*.md"))
        self.assertEqual(len(archives), 1)
        self.assertIn("Old dead objective", archives[0].read_text("utf-8"))

        content = orig_req.read_text("utf-8")
        self.assertIn("Fresh isolated objective", content)
        self.assertNotIn("Old dead objective", content)


if __name__ == "__main__":
    unittest.main()
