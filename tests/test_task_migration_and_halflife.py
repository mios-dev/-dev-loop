#!/usr/bin/env python3
"""tests/test_task_migration_and_halflife.py — Test suite for task migration, half-life decay, and archive distillation.

Verifies:
1. Parser fidelity on TASKS.md and AGY-TASKS.md (zero data loss, full context).
2. Status normalization to 5-word vocabulary (open, in_progress, blocked, done, cancelled).
3. Half-life decay math (commit drift, time decay, anchor sensors).
4. Lossless archiving to rolling historical backlog.
5. Strict OpenAI schema conformance.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills/dev-loop/scripts"
sys.path.insert(0, str(SCRIPTS))

import artifacts
import task_migration

FAILURES = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name}{': ' + detail if detail else ''}")
        FAILURES.append(name)


def test_status_normalization():
    print("Testing status normalization...")
    cases = [
        ("done-by-code", "done"),
        ("completed", "done"),
        ("retired", "done"),
        ("built-gated-off", "in_progress"),
        ("in-progress", "in_progress"),
        ("partial", "in_progress"),
        ("planned", "open"),
        ("pending", "open"),
        ("open", "open"),
        ("blocked", "blocked"),
        ("cancelled", "cancelled"),
    ]
    for raw, expected in cases:
        canonical, preserved = task_migration.normalize_status(raw)
        check(f"norm_{raw}", canonical == expected and preserved == raw, f"got {canonical}")


def test_parse_tasks_md():
    print("Testing parse_tasks_md...")
    sample = """# Master Tasks
| ID | Pri | Status | Domain | Title |
|---|---|---|---|---|
| T-101 | P0 | done-by-code | Security | Inbound Authentication Gate |
| T-102 | P1 | built-gated-off | Boot | OpenSCAP Image Compliance |

## T-101 -- Inbound Authentication Gate
**Status:** done-by-code
**Who:** security-team
**What:** Enforce token authentication on dispatch
**Where:** usr/libexec/mios/auth
**Done When:** Every inbound request without token is rejected with 401
**Verify:** bash tests/test-auth.sh

## T-102 -- OpenSCAP Image Compliance
**Status:** built-gated-off
**What:** Scans image against DISA-STIG
**Where:** automation/oscap.sh
**Done When:** Compliance report generated
"""
    tasks = task_migration.parse_tasks_md(sample)
    check("tasks_len", len(tasks) == 2, f"got {len(tasks)}")
    t101 = next(t for t in tasks if t["id"] == "T-101")
    check("t101_status", t101["status"] == "done", f"got {t101['status']}")
    check("t101_legacy_status", t101["legacy_status"] == "done-by-code")
    check("t101_evidence_present", bool(t101["verification_evidence"]))
    check("t101_owner", t101["owner"] == "security-team")

    t102 = next(t for t in tasks if t["id"] == "T-102")
    check("t102_status", t102["status"] == "in_progress", f"got {t102['status']}")


def test_parse_agy_tasks():
    print("Testing parse_agy_tasks...")
    sample = """## AGY-100..102 -- Image Building Epic
**Goal:** Complete bootc image pipeline
**Where:** automation/

### AGY-100 Build Containerfile
**Goal:** Build raw container
**What+How:** Run podman build
**Where:** Containerfile
**Verify:** podman image exists
**Why:** Base OS artifact
**Done When:** Container builds with exit 0
**Dep:** none

### AGY-101 Configure Network [DONE]
**Goal:** Network setup
**What+How:** Render chrony config
**Where:** etc/chrony.conf
**Verify:** test -f etc/chrony.conf
**Done When:** chrony starts
**Dep:** AGY-100
"""
    tasks = task_migration.parse_agy_tasks(sample)
    check("agy_len", len(tasks) == 3, f"got {len(tasks)}")
    
    banner = next(t for t in tasks if t["id"] == "AGY-100..102")
    check("banner_type", banner["type"] == "epic")
    
    t101 = next(t for t in tasks if t["id"] == "AGY-101")
    check("t101_status", t101["status"] == "done")
    check("t101_dep", "AGY-100" in t101["depends_on"])
    check("t101_evidence", bool(t101["verification_evidence"]))


def test_half_life_staleness_calculation():
    print("Testing half-life staleness calculation...")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        # Create an existing file
        existing_file = root / "valid_file.txt"
        existing_file.write_text("ok", "utf-8")

        # Task 1: Fresh task
        fresh_task = {
            "id": "T-001",
            "title": "Fresh Task",
            "created": time.strftime("%Y-%m-%d"),
            "updated": time.strftime("%Y-%m-%d"),
            "half_life": {
                "created_commit": "HEAD",
                "half_life_horizon_commits": 50,
                "half_life_horizon_days": 90,
                "anchors": ["valid_file.txt"]
            }
        }
        st_fresh = artifacts.compute_task_staleness(root, fresh_task)
        check("fresh_staleness_zero", st_fresh["staleness"] < 0.1, f"got {st_fresh['staleness']}")
        check("fresh_not_expired", not st_fresh["expired"])

        # Task 2: Task with broken anchor
        broken_task = {
            "id": "T-002",
            "title": "Broken Anchor Task",
            "created": time.strftime("%Y-%m-%d"),
            "updated": time.strftime("%Y-%m-%d"),
            "half_life": {
                "created_commit": "HEAD",
                "half_life_horizon_commits": 50,
                "half_life_horizon_days": 90,
                "anchors": ["nonexistent_path/lost_file.rs"]
            }
        }
        st_broken = artifacts.compute_task_staleness(root, broken_task)
        check("broken_anchor_detected", len(st_broken["broken_anchors"]) == 1)
        check("broken_anchor_penalty", st_broken["staleness"] >= 0.35, f"got {st_broken['staleness']}")

        # Task 3: Aged task (180 days old = 2 half-lives)
        old_task = {
            "id": "T-003",
            "title": "Old Task",
            "created": "2025-01-01",
            "updated": "2025-01-01",
            "half_life": {
                "half_life_horizon_commits": 50,
                "half_life_horizon_days": 90,
                "anchors": []
            }
        }
        st_old = artifacts.compute_task_staleness(root, old_task)
        check("old_task_expired", st_old["expired"], f"got {st_old['staleness']}")
        check("old_task_high_staleness", st_old["staleness"] >= 0.5)


def test_archive_stale_and_distill():
    print("Testing archive_stale and distill...")
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        devloop_dir = root / ".devloop"
        devloop_dir.mkdir(parents=True)
        
        # Set up tasks.jsonl with 1 fresh and 1 expired task
        tasks = [
            {
                "id": "T-001",
                "type": "task",
                "title": "Active Fresh",
                "status": "open",
                "owner": "",
                "epic": "",
                "goal": "Core",
                "depends_on": [],
                "acceptance_criteria": ["WHEN ready SHALL pass"],
                "verification": {"positive_cmd": "true", "negative_control_cmd": "false", "negative_expect": "fail"},
                "verification_evidence": "",
                "links": [],
                "notes": "fresh note",
                "created": time.strftime("%Y-%m-%d"),
                "updated": time.strftime("%Y-%m-%d"),
            },
            {
                "id": "T-002",
                "type": "task",
                "title": "Ancient Stale",
                "status": "open",
                "owner": "",
                "epic": "",
                "goal": "Legacy",
                "depends_on": [],
                "acceptance_criteria": ["WHEN archaic SHALL fade"],
                "verification": {"positive_cmd": "true", "negative_control_cmd": "false", "negative_expect": "fail"},
                "verification_evidence": "",
                "links": ["missing/path.c"],
                "notes": "archaic reasoning context",
                "created": "2024-01-01",
                "updated": "2024-01-01",
            }
        ]
        artifacts.save_tasks(root, tasks)

        # Run archive-stale via fake args
        from types import SimpleNamespace
        args = SimpleNamespace(
            op="archive-stale",
            root=str(root),
            threshold=0.5,
            id=None,
            status=None,
            evidence=None,
            id_flag=None,
            title=None,
            type="task",
            owner=None,
            epic=None,
            goal=None,
            depends=None,
            ac=None,
            positive=None,
            negative=None,
            expect=None,
        )

        artifacts.cmd_tasks(args)

        # Check that T-002 was archived and T-001 survives
        survivors = artifacts.load_tasks(root)
        check("survivors_count", len(survivors) == 1 and survivors[0]["id"] == "T-001")
        
        archive_file = root / ".devloop" / "backlog_archive.jsonl"
        check("archive_file_exists", archive_file.exists())
        archived = [json.loads(line) for line in archive_file.read_text("utf-8").splitlines()]
        check("archived_task_found", len(archived) == 1 and archived[0]["id"] == "T-002")

        hist_md = root / ".devloop" / "HISTORICAL_BACKLOG.md"
        check("historical_md_exists", hist_md.exists())
        check("historical_md_contains_notes", "archaic reasoning context" in hist_md.read_text("utf-8"))

        # Run distill
        args.op = "distill"
        artifacts.cmd_tasks(args)

        distill_out = root / "docs" / "distilled" / "knowledge_distillation.md"
        check("distill_out_exists", distill_out.exists())
        check("distill_contains_theme", "Legacy" in distill_out.read_text("utf-8"))


def test_openai_schema_conformance():
    print("Testing OpenAI schema conformance...")
    from io import StringIO
    from types import SimpleNamespace
    import sys

    old_stdout = sys.stdout
    sys.stdout = StringIO()
    try:
        args = SimpleNamespace(
            op="export-openai",
            root=".",
            threshold=0.5,
            id=None,
            status=None,
            evidence=None,
            id_flag=None,
            title=None,
            type="task",
            owner=None,
            epic=None,
            goal=None,
            depends=None,
            ac=None,
            positive=None,
            negative=None,
            expect=None,
        )
        artifacts.cmd_tasks(args)
        output = sys.stdout.getvalue()
    finally:
        sys.stdout = old_stdout

    data = json.loads(output)
    check("has_function", "function" in data)
    fn = data["function"]
    check("strict_true", fn.get("strict") is True)
    params = fn["parameters"]
    check("additionalProperties_false", params.get("additionalProperties") is False)
    check("all_required_declared", set(params["properties"].keys()) == set(params["required"]))


def main():
    test_status_normalization()
    test_parse_tasks_md()
    test_parse_agy_tasks()
    test_half_life_staleness_calculation()
    test_archive_stale_and_distill()
    test_openai_schema_conformance()

    if FAILURES:
        print(f"\nFAILED {len(FAILURES)} checks: {FAILURES}")
        sys.exit(1)
    print("\nALL TESTS PASSED.")
    sys.exit(0)


if __name__ == "__main__":
    main()
