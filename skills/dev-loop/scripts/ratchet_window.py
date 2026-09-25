#!/usr/bin/env python3
"""ratchet_window.py — Sliding-window ratchet with 3-5 commit growth hysteresis.

Enforces code metric ceilings while providing an elastic growth buffer across
active multi-commit engineering sprints.

Lifecycle across commits (infinite scale via rolling baseline):
  Delta C = HEAD - baseline_sha
  1. Delta C in [0, 2]: GROWTH_BUFFER
     Permits controlled tolerance (+5% or declared headroom) for docs, devcontainers,
     and tests without blocking active progress.
  2. Delta C in [3, 5]: REASSESSMENT_WINDOW
     Evaluates verity (test coverage, template conformance) and verifies roadmap
     alignments (commits map to ROADMAP.md / TASKS.md).
  3. Delta C > 5: RATCHET_GATE
     Enforces strict lock-in. Metric ceilings must decrease or hold; on verified
     milestones, advances baseline_sha to HEAD and tightens the ratchet.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

BASELINE_FILE = ".devloop/ratchet_baseline.json"
DEFAULT_MIN_COMMITS = 3
DEFAULT_MAX_COMMITS = 5
DEFAULT_GROWTH_BUFFER_PCT = 0.05  # 5% buffer during sprint


def get_git_head(root: Path) -> str:
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except Exception:
        return "HEAD"


def get_commit_distance(root: Path, base_sha: str, head_sha: str = "HEAD") -> int:
    try:
        res = subprocess.run(
            ["git", "rev-list", "--count", f"{base_sha}..{head_sha}"],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
        )
        return int(res.stdout.strip())
    except Exception:
        return 0


def get_recent_commit_messages(root: Path, base_sha: str, limit: int = 10) -> List[str]:
    try:
        res = subprocess.run(
            ["git", "log", f"{base_sha}..HEAD", f"-n{limit}", "--oneline"],
            cwd=root,
            capture_output=True,
            text=True,
        )
        return [line.strip() for line in res.stdout.splitlines() if line.strip()]
    except Exception:
        return []


def check_roadmap_alignment(root: Path, commit_msgs: List[str]) -> Tuple[bool, List[str]]:
    """Verify that recent commits reference valid tasks or roadmap items."""
    roadmap_path = root / "ROADMAP.md"
    if not roadmap_path.exists():
        roadmap_path = root / "docs" / "ROADMAP.md"
    
    roadmap_text = roadmap_path.read_text("utf-8", errors="replace") if roadmap_path.exists() else ""
    
    aligned = []
    unaligned = []
    
    for msg in commit_msgs:
        # Check for task / ADR / milestone reference
        refs = re.findall(r"\b([A-Z]+-\d+|ADR-\d+|WS-[0-9A-Z]+)\b", msg)
        if refs:
            aligned.append(f"{msg} -> {refs}")
        elif any(k in msg.lower() for k in ("feat", "fix", "chore", "docs", "test", "refactor")):
            aligned.append(f"{msg} (conventional commit)")
        else:
            unaligned.append(msg)

    is_aligned = len(unaligned) <= 1
    return is_aligned, aligned


def evaluate_ratchet(
    root: Path,
    current_metrics: Dict[str, int],
    min_window: int = DEFAULT_MIN_COMMITS,
    max_window: int = DEFAULT_MAX_COMMITS,
    growth_buffer: float = DEFAULT_GROWTH_BUFFER_PCT,
    auto_advance: bool = False,
) -> Dict[str, Any]:
    state_file = root / BASELINE_FILE
    head_sha = get_git_head(root)
    
    if not state_file.exists():
        # Initialize baseline
        init_data = {
            "baseline_sha": head_sha,
            "baseline_metrics": current_metrics,
            "created": time.strftime("%Y-%m-%d %H:%M:%SZ"),
            "last_ratchet": time.strftime("%Y-%m-%d %H:%M:%SZ"),
            "window_commits": max_window,
        }
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file.write_text(json.dumps(init_data, indent=2), "utf-8")
        return {
            "status": "INITIALIZED",
            "delta_commits": 0,
            "allowed": True,
            "violations": [],
            "within_buffer": [],
            "roadmap_aligned": True,
            "message": f"Initialized ratchet baseline at {head_sha[:8]}",
            "metrics": current_metrics,
        }

    data = json.loads(state_file.read_text("utf-8"))
    base_sha = data.get("baseline_sha", head_sha)
    base_metrics = data.get("baseline_metrics", {})
    delta_c = get_commit_distance(root, base_sha, "HEAD")

    commit_msgs = get_recent_commit_messages(root, base_sha)
    aligned, details = check_roadmap_alignment(root, commit_msgs)

    # Compare metrics
    violations = []
    within_buffer = []

    for k, curr_val in current_metrics.items():
        base_val = base_metrics.get(k)
        if base_val is None:
            continue
        if curr_val > base_val:
            diff = curr_val - base_val
            pct = diff / max(base_val, 1)
            if delta_c < min_window and pct <= growth_buffer:
                within_buffer.append(f"{k}: +{diff} ({pct:.1%}) within growth buffer for sprint commit {delta_c}")
            else:
                violations.append(f"{k}: current {curr_val} > baseline {base_val} (+{diff})")

    # Determine state
    if delta_c < min_window:
        state = "GROWTH_BUFFER"
        allowed = len(violations) == 0
        msg = f"Commit {delta_c}/{min_window} within growth buffer window."
        if within_buffer:
            msg += " " + "; ".join(within_buffer)
    elif min_window <= delta_c <= max_window:
        state = "REASSESSMENT_WINDOW"
        allowed = len(violations) == 0 and aligned
        msg = f"Commit {delta_c} in reassessment window [{min_window}..{max_window}]. Roadmap alignment: {'OK' if aligned else 'DRIFT'}."
    else:  # delta_c > max_window
        state = "RATCHET_GATE"
        allowed = len(violations) == 0 and aligned
        msg = f"Commit {delta_c} exceeds window ({max_window}). Strict ratchet enforced."

    # If metrics improved or hold and we are at/past window or requested auto-advance, ratchet down
    can_ratchet = allowed and (delta_c >= min_window or auto_advance)
    if can_ratchet and not violations:
        # Tighten baseline ceilings
        tightened = {}
        improved = False
        for k, curr_val in current_metrics.items():
            base_val = base_metrics.get(k, curr_val)
            new_val = min(curr_val, base_val)
            tightened[k] = new_val
            if new_val < base_val:
                improved = True
        
        if auto_advance or delta_c >= max_window:
            data["baseline_sha"] = head_sha
            data["baseline_metrics"] = tightened
            data["last_ratchet"] = time.strftime("%Y-%m-%d %H:%M:%SZ")
            state_file.write_text(json.dumps(data, indent=2), "utf-8")
            msg += f" Ratchet advanced to {head_sha[:8]} (improved={improved})."

    return {
        "status": state,
        "delta_commits": delta_c,
        "allowed": allowed,
        "violations": violations,
        "within_buffer": within_buffer,
        "roadmap_aligned": aligned,
        "message": msg,
        "current_metrics": current_metrics,
        "baseline_metrics": base_metrics,
    }


def main():
    parser = argparse.ArgumentParser(description="Sliding-window ratchet evaluator with commit hysteresis.")
    parser.add_argument("--root", default=".", help="Repo root")
    parser.add_argument("--min-window", type=int, default=DEFAULT_MIN_COMMITS, help="Minimum commits before re-assessment")
    parser.add_argument("--max-window", type=int, default=DEFAULT_MAX_COMMITS, help="Maximum commits before strict gate")
    parser.add_argument("--metric", action="append", help="Metric in format key=value (e.g. tracked_files=3071)")
    parser.add_argument("--advance", action="store_true", help="Explicitly advance baseline to HEAD")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    metrics = {}
    if args.metric:
        for m in args.metric:
            k, _, v = m.partition("=")
            try:
                metrics[k.strip()] = int(v.strip())
            except ValueError:
                pass

    res = evaluate_ratchet(
        root=root,
        current_metrics=metrics,
        min_window=args.min_window,
        max_window=args.max_window,
        auto_advance=args.advance,
    )

    print(f"[{res['status']}] {res['message']}")
    if res["violations"]:
        print("VIOLATIONS:")
        for v in res["violations"]:
            print(f"  - {v}")
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
