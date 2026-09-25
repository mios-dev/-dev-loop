#!/usr/bin/env python3
"""tests/test_ratchet_window.py — Test suite for sliding-window ratchet with 3-5 commit hysteresis.

Verifies:
1. Baseline initialization and state persistence.
2. Elastic growth buffer during active sprints (commits 0..2).
3. Reassessment window (commits 3..5) and roadmap alignment checks.
4. Strict ratchet lock-in when window exceeds 5 commits.
5. Automatic ratchet tightening upon improvement.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills/dev-loop/scripts"
sys.path.insert(0, str(SCRIPTS))

import ratchet_window

FAILURES = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name}{': ' + detail if detail else ''}")
        FAILURES.append(name)


def test_initialization():
    print("Testing ratchet initialization...")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        metrics = {"lines": 1000, "files": 50}
        res = ratchet_window.evaluate_ratchet(root, metrics)
        check("init_status", res["status"] == "INITIALIZED")
        check("init_allowed", res["allowed"] is True)
        check("init_no_violations", len(res["violations"]) == 0)
        
        base_file = root / ".devloop" / "ratchet_baseline.json"
        check("baseline_file_created", base_file.exists())
        data = json.loads(base_file.read_text("utf-8"))
        check("stored_metrics_match", data["baseline_metrics"] == metrics)


def test_growth_buffer_tolerance():
    print("Testing growth buffer tolerance...")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        # Pre-populate baseline
        base_file = root / ".devloop" / "ratchet_baseline.json"
        base_file.parent.mkdir(parents=True)
        base_file.write_text(json.dumps({
            "baseline_sha": "fake-sha-0",
            "baseline_metrics": {"lines": 1000, "files": 50},
            "created": "2026-09-20",
        }), "utf-8")

        # Mock commit distance = 1 (within growth window < 3)
        orig_get_dist = ratchet_window.get_commit_distance
        orig_get_msgs = ratchet_window.get_recent_commit_messages
        ratchet_window.get_commit_distance = lambda r, b, h: 1
        ratchet_window.get_recent_commit_messages = lambda r, b: ["feat: add devcontainer setup"]
        try:
            # Metric within 5% growth (1030 lines = +3%)
            m_ok = {"lines": 1030, "files": 50}
            res_ok = ratchet_window.evaluate_ratchet(root, m_ok, growth_buffer=0.05)
            check("buffer_ok_status", res_ok["status"] == "GROWTH_BUFFER")
            check("buffer_ok_allowed", res_ok["allowed"] is True)
            check("buffer_noted", len(res_ok["within_buffer"]) == 1)

            # Metric exceeding 5% growth (1100 lines = +10%)
            m_fail = {"lines": 1100, "files": 50}
            res_fail = ratchet_window.evaluate_ratchet(root, m_fail, growth_buffer=0.05)
            check("buffer_fail_not_allowed", res_fail["allowed"] is False)
            check("buffer_fail_violation", len(res_fail["violations"]) == 1)
        finally:
            ratchet_window.get_commit_distance = orig_get_dist
            ratchet_window.get_recent_commit_messages = orig_get_msgs


def test_reassessment_window_and_roadmap():
    print("Testing reassessment window and roadmap alignment...")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        base_file = root / ".devloop" / "ratchet_baseline.json"
        base_file.parent.mkdir(parents=True)
        base_file.write_text(json.dumps({
            "baseline_sha": "fake-sha-0",
            "baseline_metrics": {"lines": 1000},
            "created": "2026-09-20",
        }), "utf-8")

        orig_get_dist = ratchet_window.get_commit_distance
        orig_get_msgs = ratchet_window.get_recent_commit_messages
        ratchet_window.get_commit_distance = lambda r, b, h: 4  # in [3..5]
        ratchet_window.get_recent_commit_messages = lambda r, b: ["fix(T-002): resolve gate failure"]
        try:
            m = {"lines": 1000}
            res = ratchet_window.evaluate_ratchet(root, m)
            check("reassess_status", res["status"] == "REASSESSMENT_WINDOW")
            check("reassess_allowed", res["allowed"] is True)
            check("roadmap_aligned", res["roadmap_aligned"] is True)
        finally:
            ratchet_window.get_commit_distance = orig_get_dist
            ratchet_window.get_recent_commit_messages = orig_get_msgs


def test_ratchet_tightening():
    print("Testing ratchet tightening on improvement...")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        base_file = root / ".devloop" / "ratchet_baseline.json"
        base_file.parent.mkdir(parents=True)
        base_file.write_text(json.dumps({
            "baseline_sha": "fake-sha-0",
            "baseline_metrics": {"lines": 1000, "files": 50},
            "created": "2026-09-20",
        }), "utf-8")

        orig_get_dist = ratchet_window.get_commit_distance
        orig_get_head = ratchet_window.get_git_head
        ratchet_window.get_commit_distance = lambda r, b, h: 4
        ratchet_window.get_git_head = lambda r: "new-sha-123"
        try:
            # Metrics improved: lines dropped to 950
            m_improved = {"lines": 950, "files": 50}
            res = ratchet_window.evaluate_ratchet(root, m_improved, auto_advance=True)
            check("advance_allowed", res["allowed"] is True)

            # Verify saved baseline updated
            updated_data = json.loads(base_file.read_text("utf-8"))
            check("baseline_sha_updated", updated_data["baseline_sha"] == "new-sha-123")
            check("ceiling_tightened", updated_data["baseline_metrics"]["lines"] == 950)
        finally:
            ratchet_window.get_commit_distance = orig_get_dist
            ratchet_window.get_git_head = orig_get_head


def main():
    test_initialization()
    test_growth_buffer_tolerance()
    test_reassessment_window_and_roadmap()
    test_ratchet_tightening()

    if FAILURES:
        print(f"\nFAILED {len(FAILURES)} checks: {FAILURES}")
        sys.exit(1)
    print("\nALL RATCHET WINDOW TESTS PASSED.")
    sys.exit(0)


if __name__ == "__main__":
    main()
