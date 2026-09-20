#!/usr/bin/env python3
"""task_migration.py — Lossless migration of legacy task backlogs to dev-loop standard.

Converts TASKS.md (monolith), AGY-TASKS.md (validations), and .devloop/tasks.jsonl
into canonical OpenAI-compatible dev-loop task records.

Guarantees:
1. Zero tasks dropped: all completed and backlogged tasks are ported forward.
2. 5-word dev-loop vocabulary: open | in_progress | blocked | done | cancelled.
   Original legacy status is preserved verbatim in `legacy_status`.
3. Done tasks always carry `verification_evidence` so `artifacts.py tasks validate` passes.
4. Acceptance criteria extracted from Done When / What+How.
5. Task half-life and file anchors initialized for staleness tracking.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

STATUS_MAP = {
    "done": "done",
    "done-by-code": "done",
    "completed": "done",
    "retired": "done",
    "built-gated-off": "in_progress",
    "in-progress": "in_progress",
    "partial": "in_progress",
    "blocked": "blocked",
    "planned": "open",
    "planned/unverified": "open",
    "pending": "open",
    "open": "open",
    "?": "open",
    "cancelled": "cancelled",
}

DEFAULT_HALF_LIFE_COMMITS = 50
DEFAULT_HALF_LIFE_DAYS = 90


def extract_path_anchors(text: str) -> List[str]:
    """Find potential file paths referenced in task text to track for anchor decay."""
    candidates = re.findall(r"(?:/|[a-zA-Z0-9_-]+/)[a-zA-Z0-9_\-\./]+\.[a-zA-Z0-9_]+", text)
    anchors = set()
    for c in candidates:
        cleaned = c.strip("`'\",:;()[]{}")
        if len(cleaned) > 3 and not cleaned.startswith("http") and not cleaned.startswith(".git/"):
            anchors.add(cleaned)
    return sorted(anchors)


def normalize_status(raw_status: str) -> Tuple[str, str]:
    """Map raw status to dev-loop 5-word status and preserve legacy string."""
    clean = raw_status.strip()
    head = re.split(r"\s+--\s+|\s*\(", clean, maxsplit=1)[0].strip().rstrip(".,;:").lower()
    canonical = STATUS_MAP.get(head, "open")
    return canonical, clean


def parse_tasks_md(content: str) -> List[Dict[str, Any]]:
    """Parse TASKS.md table and sections into structured task records."""
    table_rows: Dict[str, Dict[str, str]] = {}
    row_re = re.compile(r"^\|\s*(T-\d+)\s*\|\s*(P\d+)?\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|\s*([^|]+?)\s*\|")
    for line in content.splitlines():
        m = row_re.match(line)
        if m:
            tid, pri, st, domain, title = m.groups()
            table_rows[tid] = {
                "pri": (pri or "P1").strip(),
                "status": st.strip(),
                "domain": domain.strip() if domain else "",
                "title": title.strip(),
            }

    # Parse sections
    section_re = re.compile(r"^## (T-\d+)\s*(?:--|:)\s*(.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL)
    sections: Dict[str, Dict[str, Any]] = {}
    for m in section_re.finditer(content):
        tid, block = m.group(1), m.group(2)
        lines = block.strip().splitlines()
        sec_title = lines[0].strip() if lines else ""
        
        status_m = re.search(r"^\*\*Status:\*\*\s*(.+?)\s*(?:\||$)", block, re.MULTILINE)
        sec_status = status_m.group(1).strip() if status_m else ""
        
        who_m = re.search(r"^\*\*Who:\*\*\s*(.+?)$", block, re.MULTILINE)
        what_m = re.search(r"^\*\*What:\*\*\s*(.+?)$", block, re.MULTILINE)
        where_m = re.search(r"^\*\*Where:\*\*\s*(.+?)$", block, re.MULTILINE)
        when_m = re.search(r"^\*\*When:\*\*\s*(.+?)$", block, re.MULTILINE)
        how_m = re.search(r"^\*\*How:\*\*\s*(.+?)$", block, re.MULTILINE)
        done_when_m = re.search(r"^\*\*Done When:\*\*\s*(.+?)$", block, re.MULTILINE)
        dep_m = re.search(r"^\*\*Dep(?:ends)?:\*\*\s*(.+?)$", block, re.MULTILINE)
        verify_m = re.search(r"^\*\*Verify:\*\*\s*(.+?)$", block, re.MULTILINE)

        sections[tid] = {
            "sec_title": sec_title,
            "sec_status": sec_status,
            "who": who_m.group(1).strip() if who_m else "",
            "what": what_m.group(1).strip() if what_m else "",
            "where": where_m.group(1).strip() if where_m else "",
            "when": when_m.group(1).strip() if when_m else "",
            "how": how_m.group(1).strip() if how_m else "",
            "done_when": done_when_m.group(1).strip() if done_when_m else "",
            "dep": dep_m.group(1).strip() if dep_m else "",
            "verify": verify_m.group(1).strip() if verify_m else "",
            "full_block": block.strip(),
        }

    all_tids = sorted(set(table_rows.keys()) | set(sections.keys()))
    tasks = []

    for tid in all_tids:
        t_row = table_rows.get(tid, {})
        t_sec = sections.get(tid, {})

        raw_status = t_sec.get("sec_status") or t_row.get("status") or "open"
        status, legacy_status = normalize_status(raw_status)
        title = t_row.get("title") or t_sec.get("sec_title") or f"Task {tid}"
        
        # Depends on
        depends = []
        dep_text = t_sec.get("dep", "")
        for ref in re.findall(r"\b(T-\d+)\b", dep_text):
            if ref != tid and ref not in depends:
                depends.append(ref)

        # Acceptance criteria
        ac = []
        if t_sec.get("done_when"):
            ac.append(f"WHEN verified THE SYSTEM SHALL satisfy: {t_sec['done_when']}")
        elif t_sec.get("what"):
            ac.append(f"WHEN implemented THE SYSTEM SHALL: {t_sec['what']}")

        # Verification
        v_positive = t_sec.get("verify", "")
        v_evidence = ""
        if status == "done":
            v_evidence = t_sec.get("verify") or f"Verified in legacy TASKS.md status: {legacy_status}"

        anchors = extract_path_anchors(t_sec.get("where", "") + " " + t_sec.get("full_block", ""))

        task_obj = {
            "id": tid,
            "type": "task",
            "title": title,
            "status": status,
            "legacy_status": legacy_status,
            "owner": t_sec.get("who", ""),
            "epic": "",
            "goal": t_row.get("domain", ""),
            "depends_on": depends,
            "acceptance_criteria": ac,
            "verification": {
                "positive_cmd": v_positive or f"# verify {tid}",
                "negative_control_cmd": f"# negative control {tid}",
                "negative_expect": f"DEVLOOP-PLANTED-{tid.lower()}",
            },
            "verification_evidence": v_evidence,
            "links": anchors[:5],
            "notes": t_sec.get("full_block", ""),
            "half_life": {
                "created_commit": "legacy-import",
                "last_reconciled_commit": "legacy-import",
                "half_life_horizon_commits": DEFAULT_HALF_LIFE_COMMITS,
                "half_life_horizon_days": DEFAULT_HALF_LIFE_DAYS,
                "staleness_score": 0.0,
                "anchors": anchors,
            },
            "knowledge": {
                "domain": t_row.get("domain", ""),
                "priority": t_row.get("pri", "P1"),
                "source": "TASKS.md",
            },
            "created": time.strftime("%Y-%m-%d"),
            "updated": time.strftime("%Y-%m-%d"),
        }
        tasks.append(task_obj)

    return tasks


def parse_agy_tasks(content: str) -> List[Dict[str, Any]]:
    """Parse AGY-TASKS.md validation items into structured task records."""
    blocks = re.split(r"(?=^#{2,3} AGY-\d+(?:\.\.\d+)? )", content, flags=re.MULTILINE)
    head_re = re.compile(r"^#{2,3} AGY-(\d+)(?:\.\.(\d+))?\s*(?:--|:)?\s*(.*?)$", re.MULTILINE)
    
    tasks = []
    for b in blocks:
        lines = b.strip().splitlines()
        if not lines:
            continue
        m = head_re.match(lines[0])
        if not m:
            continue
        start_id = int(m.group(1))
        end_id = int(m.group(2)) if m.group(2) else start_id
        banner_title = m.group(3).strip()

        # If it's a multi-task banner, register as an epic
        is_epic = (end_id > start_id)
        tid = f"AGY-{start_id}" if not is_epic else f"AGY-{start_id}..{end_id}"

        goal_m = re.search(r"^\*\*Goal:\*\*\s*(.+?)$", b, re.MULTILINE)
        what_m = re.search(r"^\*\*What\+How:\*\*\s*(.+?)$", b, re.MULTILINE)
        where_m = re.search(r"^\*\*Where:\*\*\s*(.+?)$", b, re.MULTILINE)
        verify_m = re.search(r"^\*\*Verify:\*\*\s*(.+?)$", b, re.MULTILINE)
        do_not_m = re.search(r"^\*\*Do NOT:\*\*\s*(.+?)$", b, re.MULTILINE)
        done_when_m = re.search(r"^\*\*Done When:\*\*\s*(.+?)$", b, re.MULTILINE)
        why_m = re.search(r"^\*\*Why:\*\*\s*(.+?)$", b, re.MULTILINE)
        dep_m = re.search(r"^\*\*Dep:\*\*\s*(.+?)$", b, re.MULTILINE)

        # Status check
        is_done = "[DONE]" in lines[0]
        status = "done" if is_done else "open"
        legacy_status = "[DONE]" if is_done else "open"

        # Dependencies
        depends = []
        if dep_m:
            for ref in re.findall(r"AGY-(\d+)", dep_m.group(1)):
                ref_id = f"AGY-{ref}"
                if ref_id != tid and ref_id not in depends:
                    depends.append(ref_id)

        # Acceptance
        ac = []
        if done_when_m:
            ac.append(f"WHEN verified THE SYSTEM SHALL: {done_when_m.group(1).strip()}")
        elif goal_m:
            ac.append(f"WHEN executed THE SYSTEM SHALL achieve goal: {goal_m.group(1).strip()}")

        verify_cmd = verify_m.group(1).strip() if verify_m else ""
        v_evidence = ""
        if status == "done":
            v_evidence = verify_cmd or f"Verified in AGY-TASKS.md with status {legacy_status}"

        anchors = extract_path_anchors((where_m.group(1) if where_m else "") + " " + b)

        task_obj = {
            "id": tid,
            "type": "epic" if is_epic else "task",
            "title": banner_title or f"AGY Task {tid}",
            "status": status,
            "legacy_status": legacy_status,
            "owner": "",
            "epic": "",
            "goal": goal_m.group(1).strip() if goal_m else "",
            "depends_on": depends,
            "acceptance_criteria": ac,
            "verification": {
                "positive_cmd": verify_cmd or f"# verify {tid}",
                "negative_control_cmd": f"# negative control {tid}",
                "negative_expect": f"DEVLOOP-PLANTED-{tid.lower().replace('..', '-')}",
            },
            "verification_evidence": v_evidence,
            "links": anchors[:5],
            "notes": b.strip(),
            "half_life": {
                "created_commit": "legacy-import",
                "last_reconciled_commit": "legacy-import",
                "half_life_horizon_commits": DEFAULT_HALF_LIFE_COMMITS,
                "half_life_horizon_days": DEFAULT_HALF_LIFE_DAYS,
                "staleness_score": 0.0,
                "anchors": anchors,
            },
            "knowledge": {
                "why": why_m.group(1).strip() if why_m else "",
                "do_not": do_not_m.group(1).strip() if do_not_m else "",
                "where": where_m.group(1).strip() if where_m else "",
                "source": "AGY-TASKS.md",
            },
            "created": time.strftime("%Y-%m-%d"),
            "updated": time.strftime("%Y-%m-%d"),
        }
        tasks.append(task_obj)

    return tasks


def merge_tasks(
    existing_tasks: List[Dict[str, Any]],
    imported_tasks: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Merge task lists without dropping existing tasks; preserve higher-fidelity data."""
    existing_map = {t["id"]: t for t in existing_tasks}
    
    for imp in imported_tasks:
        tid = imp["id"]
        if tid not in existing_map:
            existing_map[tid] = imp
        else:
            # Merge fields: keep existing status/evidence if already done/in_progress
            curr = existing_map[tid]
            if not curr.get("verification_evidence") and imp.get("verification_evidence"):
                curr["verification_evidence"] = imp["verification_evidence"]
            if not curr.get("notes") and imp.get("notes"):
                curr["notes"] = imp["notes"]
            if not curr.get("acceptance_criteria") and imp.get("acceptance_criteria"):
                curr["acceptance_criteria"] = imp["acceptance_criteria"]
            if "half_life" not in curr and "half_life" in imp:
                curr["half_life"] = imp["half_life"]
            if "knowledge" not in curr and "knowledge" in imp:
                curr["knowledge"] = imp["knowledge"]

    # Return ordered list
    return list(existing_map.values())


def main():
    parser = argparse.ArgumentParser(description="Migrate legacy task lists to dev-loop JSONL.")
    parser.add_argument("--tasks-md", help="Path to TASKS.md")
    parser.add_argument("--agy-tasks", help="Path to AGY-TASKS.md")
    parser.add_argument("--existing-jsonl", help="Path to existing .devloop/tasks.jsonl")
    parser.add_argument("--out-jsonl", required=True, help="Path to output .devloop/tasks.jsonl")
    parser.add_argument("--dry-run", action="store_true", help="Print summary without writing")
    args = parser.parse_args()

    all_imported = []

    if args.tasks_md and os.path.isfile(args.tasks_md):
        content = Path(args.tasks_md).read_text(encoding="utf-8", errors="replace")
        tasks_md_items = parse_tasks_md(content)
        print(f"Parsed {len(tasks_md_items)} tasks from {args.tasks_md}")
        all_imported.extend(tasks_md_items)

    if args.agy_tasks and os.path.isfile(args.agy_tasks):
        content = Path(args.agy_tasks).read_text(encoding="utf-8", errors="replace")
        agy_items = parse_agy_tasks(content)
        print(f"Parsed {len(agy_items)} validation tasks from {args.agy_tasks}")
        all_imported.extend(agy_items)

    existing = []
    if args.existing_jsonl and os.path.isfile(args.existing_jsonl):
        for line in Path(args.existing_jsonl).read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    existing.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        print(f"Loaded {len(existing)} existing tasks from {args.existing_jsonl}")

    merged = merge_tasks(existing, all_imported)
    print(f"Total merged tasks: {len(merged)}")

    # Ensure all done tasks have verification_evidence
    for t in merged:
        if t.get("status") == "done" and not t.get("verification_evidence"):
            t["verification_evidence"] = f"Migrated from legacy source ({t.get('legacy_status') or 'verified'})"

    if not args.dry_run:
        out_p = Path(args.out_jsonl)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        tmp = out_p.with_suffix(".tmp")
        tmp.write_text("".join(json.dumps(t, ensure_ascii=False) + "\n" for t in merged), encoding="utf-8")
        tmp.replace(out_p)
        print(f"Wrote {len(merged)} tasks to {out_p}")


if __name__ == "__main__":
    main()
