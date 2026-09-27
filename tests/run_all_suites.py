#!/usr/bin/env python3
"""
run_all_suites.py — Master test suite runner for -dev-loop.

Executes all test suites in -dev-loop/tests/, times each suite with high
precision, enforces per-suite execution budgets, and verifies exit code 0.
Outputs formatted console summaries and optional JSON/Markdown reports.

Usage:
  python tests/run_all_suites.py
  python tests/run_all_suites.py --baseline-only
  python tests/run_all_suites.py --suite test_agy_dispatch_rule
  python tests/run_all_suites.py --timeout 10.0 --json report.json
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Optional

ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = ROOT / "tests"

# The 48 canonical test suites present in the baseline test inventory
BASELINE_48_SUITES: list[str] = [
    "test_adversarial_challenger_2.py",
    "test_adversarial_concurrency.py",
    "test_adversarial_m4_challenger_2.py",
    "test_agy_dispatch_rule.py",
    "test_agy_installer_fetch.py",
    "test_agy_monitor.py",
    "test_agy_remote_control.py",
    "test_agy_session_poll.py",
    "test_agy_settings.py",
    "test_base_tree_guard.py",
    "test_challenger_adversarial_probes.py",
    "test_challenger_lane_stress.py",
    "test_claude_lane.py",
    "test_cloud_runtime.py",
    "test_codex_argv.py",
    "test_dev_loop_web_package.py",
    "test_devcontainer_mirror.py",
    "test_devloop_exclude.py",
    "test_devloop_jobs.py",
    "test_devloop_serverd.py",
    "test_dispatch_fanout.py",
    "test_e2e_lane_isolation.py",
    "test_e2e_tier5_hardening.py",
    "test_envelope_denials.py",
    "test_format_hook.py",
    "test_gate_audit.py",
    "test_global_monitor.py",
    "test_goal_criteria.py",
    "test_guard_hooks.py",
    "test_job_receipt.py",
    "test_lane_isolation_leakage.py",
    "test_lane_prompt.py",
    "test_loop_envelope.py",
    "test_mios_init.py",
    "test_planted_naming.py",
    "test_prompt_templates.py",
    "test_ratchet_window.py",
    "test_register_mcp.py",
    "test_repo_root_helper.py",
    "test_report_schema_parity.py",
    "test_sentinel_guard.py",
    "test_session_start_keyring.py",
    "test_stale_refs.py",
    "test_stop_gate.py",
    "test_system_prompt.py",
    "test_task_migration_and_halflife.py",
    "test_teamwork_adapter.py",
    "test_worktree_owner.py",
]


@dataclass
class SuiteResult:
    name: str
    path: str
    returncode: int
    duration_s: float
    budget_s: float
    passed: bool
    timed_out: bool
    stdout: str
    stderr: str

    @property
    def budget_exceeded(self) -> bool:
        return self.duration_s > self.budget_s


@dataclass
class RunSummary:
    total: int
    passed: int
    failed: int
    timed_out: int
    budget_exceeded: int
    total_duration_s: float
    all_passed: bool
    results: list[SuiteResult]


def discover_suites(baseline_only: bool = False, pattern: Optional[str] = None) -> list[Path]:
    """Discover test suites to execute."""
    if baseline_only:
        candidates = [TESTS_DIR / s for s in BASELINE_48_SUITES]
    else:
        candidates = sorted(TESTS_DIR.glob("test_*.py"))

    # Exclude runner itself if accidentally named test_
    candidates = [p for p in candidates if p.is_file() and p.name != "run_all_suites.py"]

    if pattern:
        candidates = [p for p in candidates if pattern.lower() in p.name.lower()]

    return candidates


def run_suite(suite_path: Path, budget_s: float, timeout_s: float, verbose: bool = False) -> SuiteResult:
    """Run a single test suite in an isolated subprocess."""
    name = suite_path.name
    cmd = [sys.executable, str(suite_path)]
    t0 = time.perf_counter()
    timed_out = False
    returncode = -1
    stdout = ""
    stderr = ""

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
        t1 = time.perf_counter()
        duration_s = t1 - t0
        returncode = proc.returncode
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
    except subprocess.TimeoutExpired as exc:
        t1 = time.perf_counter()
        duration_s = t1 - t0
        timed_out = True
        returncode = -999
        stdout = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout.decode("utf-8", "replace") if exc.stdout else "")
        stderr = (exc.stderr if isinstance(exc.stderr, str) else (exc.stderr.decode("utf-8", "replace") if exc.stderr else "")) + f"\n[TIMEOUT] Exceeded execution ceiling of {timeout_s:.1f}s"
    except Exception as exc:
        t1 = time.perf_counter()
        duration_s = t1 - t0
        returncode = -1
        stderr = f"Execution error: {exc}"

    passed = (returncode == 0) and not timed_out

    return SuiteResult(
        name=name,
        path=str(suite_path),
        returncode=returncode,
        duration_s=round(duration_s, 4),
        budget_s=budget_s,
        passed=passed,
        timed_out=timed_out,
        stdout=stdout,
        stderr=stderr,
    )


def execute_all(
    suites: list[Path],
    budget_s: float = 10.0,
    timeout_s: float = 12.0,
    verbose: bool = False,
) -> RunSummary:
    """Execute all provided test suites sequentially to ensure git lock isolation."""
    results: list[SuiteResult] = []
    total_start = time.perf_counter()

    for idx, suite in enumerate(suites, 1):
        res = run_suite(suite, budget_s=budget_s, timeout_s=timeout_s, verbose=verbose)
        results.append(res)

        status_tag = "PASS" if res.passed else ("TIMEOUT" if res.timed_out else "FAIL")
        budget_flag = " [BUDGET-EXCEEDED]" if res.budget_exceeded else ""
        print(f"[{idx:02d}/{len(suites):02d}] {status_tag:7} ({res.duration_s:6.2f}s / {res.budget_s:4.1f}s) {res.name}{budget_flag}")

        if not res.passed or verbose:
            if res.stderr.strip():
                lines = res.stderr.strip().splitlines()
                preview = "\n".join("    | " + l for l in lines[-6:])
                print(f"    Stderr tail:\n{preview}")
            elif res.stdout.strip() and not res.passed:
                lines = res.stdout.strip().splitlines()
                preview = "\n".join("    | " + l for l in lines[-6:])
                print(f"    Stdout tail:\n{preview}")

    total_duration = time.perf_counter() - total_start
    passed_count = sum(1 for r in results if r.passed)
    failed_count = sum(1 for r in results if not r.passed and not r.timed_out)
    timed_out_count = sum(1 for r in results if r.timed_out)
    budget_exceeded_count = sum(1 for r in results if r.budget_exceeded)

    return RunSummary(
        total=len(results),
        passed=passed_count,
        failed=failed_count,
        timed_out=timed_out_count,
        budget_exceeded=budget_exceeded_count,
        total_duration_s=round(total_duration, 3),
        all_passed=(passed_count == len(results)),
        results=results,
    )


def render_markdown(summary: RunSummary) -> str:
    """Generate Markdown report."""
    md = [
        "# Test Suite Execution Report",
        "",
        f"- **Timestamp**: {time.strftime('%Y-%m-%d %H:%M:%SZ', time.gmtime())}",
        f"- **Total Suites**: {summary.total}",
        f"- **Passed**: {summary.passed}",
        f"- **Failed**: {summary.failed}",
        f"- **Timed Out**: {summary.timed_out}",
        f"- **Budget Exceeded (>10s)**: {summary.budget_exceeded}",
        f"- **Total Elapsed**: {summary.total_duration_s:.2f}s",
        f"- **Status**: {'ALL PASSED' if summary.all_passed else 'FAILURES DETECTED'}",
        "",
        "## Detailed Results",
        "",
        "| # | Suite | Status | Exit Code | Time (s) | Budget (s) |",
        "|---|-------|:------:|:---------:|:--------:|:----------:|",
    ]
    for idx, r in enumerate(summary.results, 1):
        st = "PASS" if r.passed else ("TIMEOUT" if r.timed_out else "FAIL")
        md.append(f"| {idx} | `{r.name}` | {st} | {r.returncode} | {r.duration_s:.2f} | {r.budget_s:.1f} |")

    return "\n".join(md) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run all dev-loop test suites")
    parser.add_argument("--baseline-only", action="store_true", help="Run only the 48 baseline test suites")
    parser.add_argument("--suite", "-s", type=str, default=None, help="Filter suites by substring pattern")
    parser.add_argument("--budget", type=float, default=10.0, help="Per-suite execution budget in seconds (default: 10.0)")
    parser.add_argument("--timeout", type=float, default=15.0, help="Hard process timeout in seconds (default: 15.0)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print verbose details on all suites")
    parser.add_argument("--json", type=str, default=None, help="Path to write JSON report")
    parser.add_argument("--markdown", type=str, default=None, help="Path to write Markdown report")
    args = parser.parse_args()

    suites = discover_suites(baseline_only=args.baseline_only, pattern=args.suite)
    if not suites:
        print(f"No test suites found matching filter (baseline_only={args.baseline_only}, pattern={args.suite!r})", file=sys.stderr)
        return 1

    print(f"=== Running {len(suites)} Test Suites (Budget: {args.budget}s, Hard Timeout: {args.timeout}s) ===")
    summary = execute_all(suites, budget_s=args.budget, timeout_s=args.timeout, verbose=args.verbose)

    print("\n" + "=" * 60)
    print(f"Summary: {summary.passed}/{summary.total} suites passed ({summary.total_duration_s:.2f}s total)")
    if summary.failed > 0:
        print(f"  Failures: {summary.failed}")
    if summary.timed_out > 0:
        print(f"  Timeouts: {summary.timed_out}")
    if summary.budget_exceeded > 0:
        print(f"  Budget Exceeded: {summary.budget_exceeded}")
    print("=" * 60)

    if args.json:
        out_path = Path(args.json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        report_data = {
            "total": summary.total,
            "passed": summary.passed,
            "failed": summary.failed,
            "timed_out": summary.timed_out,
            "budget_exceeded": summary.budget_exceeded,
            "total_duration_s": summary.total_duration_s,
            "all_passed": summary.all_passed,
            "results": [asdict(r) for r in summary.results],
        }
        out_path.write_text(json.dumps(report_data, indent=2), encoding="utf-8")
        print(f"JSON report written to: {out_path}")

    if args.markdown:
        out_path = Path(args.markdown)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(render_markdown(summary), encoding="utf-8")
        print(f"Markdown report written to: {out_path}")

    return 0 if summary.all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
