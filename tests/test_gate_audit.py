#!/usr/bin/env python3
"""
Two-sided controls for gate_audit.py (SKILL.md 7, "Checks That Cannot Fail").

A detector that never fires is itself a check that cannot fail, so every rule here is exercised
from BOTH sides:

  POSITIVE fixture   the vacuous gate the row describes -- the detector MUST fire (exit 1) and
                     MUST name its own rule id.
  NEGATIVE fixture   the same gate with the row's remediation applied -- the detector MUST stay
                     silent (exit 0). Without this side, a rule that matched every line would
                     pass the positive control.

Also controlled: "nothing audited" must never read as a pass (exit 2), and the reference doc's
coverage mapping must list every rule the CLI reports, so the claim stays auditable as detectors
are added.

Run: python3 tests/test_gate_audit.py
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "skills" / "dev-loop" / "scripts" / "gate_audit.py"
REFDOC = ROOT / "skills" / "dev-loop" / "references" / "gate-audit.md"

FAILURES: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name}{': ' + detail if detail else ''}")
        FAILURES.append(name)


def run(*args: str) -> tuple[int, str]:
    cp = subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)
    return cp.returncode, cp.stdout + cp.stderr


def audit(rule: str, filename: str, body: str) -> tuple[int, dict]:
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / filename
        f.write_text(body)
        cp = subprocess.run(
            [sys.executable, str(SCRIPT), str(f), "--only", rule, "--json"],
            capture_output=True, text=True,
        )
        try:
            return cp.returncode, json.loads(cp.stdout)
        except json.JSONDecodeError:
            return cp.returncode, {"findings": [], "raw": cp.stdout + cp.stderr}


# rule -> (filename, vacuous fixture, repaired fixture)
CASES: dict[str, tuple[str, str, str]] = {
    "SKIP_AS_PASS": ("gate.sh", """#!/bin/sh
set -eu
command -v shellcheck >/dev/null 2>&1 || { echo "PASS: lint clean"; exit 0; }
shellcheck ./tool.sh
""", """#!/bin/sh
set -eu
command -v shellcheck >/dev/null 2>&1 || { echo "shellcheck missing - gate cannot run"; exit 1; }
shellcheck ./tool.sh
"""),
    "SWALLOWED_FAILURE": ("lint.sh", """#!/bin/sh
lint_all . || true
grep -r TODO . | wc -l
""", """#!/usr/bin/env bash
set -euo pipefail
lint_all .
grep -rc TODO .
"""),
    "UNANCHORED_ALLOWLIST": ("policy.sh", """#!/usr/bin/env bash
set -euo pipefail
for f in $(list_files); do
  if grep -q "$f" allowlist.txt; then continue; fi
  check_one "$f"
done
""", """#!/usr/bin/env bash
set -euo pipefail
for f in $(list_files); do
  if grep -qE "^${f}$" allowlist.txt; then continue; fi
  check_one "$f"
done
"""),
    "COUNT_ONLY_RATCHET": ("ratchet.sh", """#!/usr/bin/env bash
set -euo pipefail
count=$(list_violations | wc -l)
if [ "$count" -le 12 ]; then echo ok; else exit 1; fi
""", """#!/usr/bin/env bash
set -euo pipefail
for f in $(list_violations); do
  grep -qxF "$f" .accepted-exceptions || exit 1
done
"""),
    "TIMEOUT_AS_PASS": ("suite.sh", """#!/usr/bin/env bash
set -euo pipefail
timeout 60 ./run-suite.sh || true
""", """#!/usr/bin/env bash
set -euo pipefail
if ! timeout 60 ./run-suite.sh; then
  rc=$?
  [ "$rc" = 124 ] && echo "suite timed out - FAIL"
  exit 1
fi
"""),
    "CHECK_WITHOUT_DIFF": ("render.py", '''import argparse, sys
from pathlib import Path

TARGET = Path("docs/schema.json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.check:
        render_all()
        print("schema: ok")
        return 0
    render_all()
    return 0
''', '''import argparse, sys
from pathlib import Path

TARGET = Path("docs/schema.json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.check:
        before = TARGET.read_text()
        render_all()
        if TARGET.read_text() != before:
            print("schema drift: regenerate", file=sys.stderr)
            return 1
        return 0
    render_all()
    return 0
'''),
    "SELF_COMPARISON": ("conform.sh", """#!/usr/bin/env bash
set -euo pipefail
./tools/render-config.sh --out generated/config.yaml
./tools/render-config.sh --out generated/config.expected.yaml
diff -u generated/config.yaml generated/config.expected.yaml
""", """#!/usr/bin/env bash
set -euo pipefail
tmp=$(mktemp -d)
./tools/render-config.sh --out "$tmp/config.yaml"
diff -u generated/config.yaml "$tmp/config.yaml"
"""),
}


# Extra controls for the causality rule in det_skip_as_pass: the early exit must be REACHED BY the
# miss path. These were real false positives / false negatives during authoring.
EXTRA_POSITIVE: list[tuple[str, str, str]] = [
    ("SKIP_AS_PASS", "neg_block.sh", """#!/usr/bin/env bash
set -euo pipefail
if ! command -v shellcheck >/dev/null 2>&1; then
  echo "shellcheck not installed - skipping lint (PASS)"
  exit 0
fi
shellcheck ./x.sh
"""),
    ("SKIP_AS_PASS", "else_branch.sh", """#!/usr/bin/env bash
set -euo pipefail
if [ -f schema.json ]; then
  validate schema.json
else
  echo "no schema - nothing to check"
  exit 0
fi
"""),
    ("SKIP_AS_PASS", "probe.py", """import shutil


def gate():
    if not shutil.which("cargo"):
        print("cargo missing, skipping audit")
        return 0
    return run_audit()
"""),
]

EXTRA_NEGATIVE: list[tuple[str, str, str]] = [
    # a `return 0` further down the function is NOT on the miss path of this probe
    ("SKIP_AS_PASS", "unattached.sh", """#!/usr/bin/env bash
set -euo pipefail
ensure_daemon() {
    daemon_info >/dev/null 2>&1 && return 0
    command -v daemond >/dev/null 2>&1 || die "daemond is not installed"
    start_daemon
    daemon_info >/dev/null 2>&1 && return 0
}
"""),
    # membership in a set of exact strings is an exact compare, not a substring allowlist
    ("UNANCHORED_ALLOWLIST", "exact.py", """ALLOWED = {"name", "description", "license"}


def ok(key):
    return key in ALLOWED
"""),
]


def main() -> int:
    print(__doc__.strip().splitlines()[0])

    check("gate_audit.py exists", SCRIPT.is_file(), str(SCRIPT))
    if not SCRIPT.is_file():
        return 1

    rc, out = run("--list-rules")
    check("--list-rules exits 0", rc == 0, f"exit {rc}")
    rule_ids = list(CASES)
    for rid in rule_ids:
        check(f"--list-rules advertises {rid}", rid in out)

    print("\nPOSITIVE controls - the vacuous gate must be caught:")
    for rid, (fname, bad, _good) in CASES.items():
        code, rep = audit(rid, fname, bad)
        rules = {f["rule"] for f in rep.get("findings", [])}
        check(f"{rid}: fires on the vacuous fixture", code == 1 and rid in rules,
              f"exit {code}, rules={sorted(rules) or rep.get('raw', '')[:120]}")

    print("\nNEGATIVE controls - the remediated gate must NOT be flagged:")
    for rid, (fname, _bad, good) in CASES.items():
        code, rep = audit(rid, fname, good)
        rules = {f["rule"] for f in rep.get("findings", [])}
        detail = "; ".join(f"{f['line']}: {f['detail']}" for f in rep.get("findings", []))
        check(f"{rid}: silent on the remediated fixture", code == 0 and not rules, f"exit {code}, {detail}")

    print("\nExtra positive controls (causality shapes that must still be caught):")
    for rid, fname, bad in EXTRA_POSITIVE:
        code, rep = audit(rid, fname, bad)
        rules = {f["rule"] for f in rep.get("findings", [])}
        check(f"{rid}: fires on {fname}", code == 1 and rid in rules, f"exit {code}, rules={sorted(rules)}")

    print("\nExtra negative controls (shapes that must NOT be flagged):")
    for rid, fname, good in EXTRA_NEGATIVE:
        code, rep = audit(rid, fname, good)
        detail = "; ".join(f"{f['line']}: {f['detail']}" for f in rep.get("findings", []))
        check(f"{rid}: silent on {fname}", code == 0, f"exit {code}, {detail}")

    print("\nNothing-audited must never read as a pass:")
    rc, out = run(str(ROOT / "no-such-path-DEVLOOP"))
    check("missing target exits 2", rc == 2, f"exit {rc}")
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "notes.txt").write_text("not a gate\n")
        rc, out = run(d)
        check("directory with no scannable file exits 2, not 0", rc == 2, f"exit {rc}")
        check("and says nothing was audited", "NOTHING AUDITED" in out, out[:120])
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "justfile").write_text("lint:\n    lint_all . || true\n\nbuild:\n    cargo build\n")
        rc, out = run(d, "--target", "build", "--only", "SWALLOWED_FAILURE")
        check("--target scopes to one recipe (build is clean)", rc == 0, f"exit {rc}: {out[:160]}")
        rc, out = run(d, "--target", "lint", "--only", "SWALLOWED_FAILURE")
        check("--target catches the vacuous recipe (lint)", rc == 1, f"exit {rc}: {out[:160]}")
        rc, out = run(d, "--target", "nope", "--only", "SWALLOWED_FAILURE")
        check("--target with an unknown recipe exits 2", rc == 2, f"exit {rc}")

    print("\nThe coverage claim stays auditable:")
    check("reference doc exists", REFDOC.is_file(), str(REFDOC))
    if REFDOC.is_file():
        doc = REFDOC.read_text()
        for rid in rule_ids:
            check(f"reference doc maps {rid}", rid in doc)
        for row in ("Measuring the Wrong Property", "Self-Certifying Predicate", "Empty-Set Pass",
                    "Mock-Only Coverage", "Assertion-Free Test", "Snapshot Rubber-Stamp"):
            check(f"reference doc records '{row}' as agent judgment", row in doc)

    print("\nThe shims must not claim the judgment rows are detected:")
    surfaces = [
        ROOT / "skills" / "gate-audit" / "SKILL.md",
        ROOT / "shims" / "claude" / "gate-audit.md",
        ROOT / "shims" / "antigravity" / "gate-audit.md",
        ROOT / "shims" / "codex" / "gate-audit.md",
        ROOT / "shims" / "opencode" / "gate-audit.md",
        ROOT / "shims" / "gemini" / "gate-audit.toml",
        ROOT / "shims" / "copilot" / "gate-audit.prompt.md",
        ROOT / "shims" / "cursor" / "gate-audit.md",
        ROOT / "shims" / "cursor" / "gate-audit.mdc",
    ]
    for s in surfaces:
        check(f"{s.relative_to(ROOT)} exists", s.is_file())
        if s.is_file():
            check(f"{s.relative_to(ROOT)} separates detected from judgment",
                  "judgment" in s.read_text().lower())

    print()
    if FAILURES:
        print(f"== test_gate_audit: FAIL ({len(FAILURES)}): {', '.join(FAILURES)}")
        return 1
    print("== test_gate_audit: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
