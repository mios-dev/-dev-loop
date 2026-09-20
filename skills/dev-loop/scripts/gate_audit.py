#!/usr/bin/env python3
"""
gate_audit.py - find gates that cannot fail (stdlib only, Linux/macOS/Windows).

Audits STANDING gate machinery - a CI workflow, a Makefile/justfile recipe, a lint or gate
script, a test directory - against the mechanically decidable half of the SKILL.md section 7
"Checks That Cannot Fail" taxonomy.

  gate_audit.py <path> [--target NAME] [--only RULE,...] [--json] [--quiet]
  gate_audit.py --list-rules

  <path>        file or directory. Recognised: shell (.sh/.bash/.zsh/shebang), PowerShell (.ps1),
                Python, YAML (CI workflows), Makefile/*.mk, justfile, JS/TS. A directory is walked
                (.git, node_modules, __pycache__, .venv, dist, build, target are skipped).
  --target      a Makefile or justfile recipe name; only that recipe's body is scanned (as a
                shell-shaped body, so the whole-file `set -euo pipefail` rule does not apply).
  --only        comma-separated rule ids to run (default: all seven).
  --json        machine-readable report on stdout.
  --quiet       findings only, no trailing summary paragraph.

SEVEN RULES, one per mechanically decidable taxonomy row (`--list-rules` prints them):
  SKIP_AS_PASS  SWALLOWED_FAILURE  UNANCHORED_ALLOWLIST  COUNT_ONLY_RATCHET
  TIMEOUT_AS_PASS  CHECK_WITHOUT_DIFF  SELF_COMPARISON

NOT DETECTED - six taxonomy rows need a reader, and this script never claims them:
  Measuring the Wrong Property, Self-Certifying Predicate, Empty-Set Pass, Mock-Only Coverage,
  Assertion-Free Test, Snapshot Rubber-Stamp. They are agent prompts in skills/gate-audit/SKILL.md.
  A clean exit 0 means "no pattern matched", never "this gate can fail" - only planting the
  violation the gate claims to catch proves that.

Exit codes:
  0  scanned successfully, no vacuous gate matched
  1  vacuous gate(s) found
  2  target unreadable, unsupported, or empty of scannable files (nothing was audited)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

# rule id -> (SKILL.md section 7 row, remediation from that row's Remediation column)
RULES: dict[str, tuple[str, str]] = {
    "SKIP_AS_PASS": (
        "Skip-as-Pass",
        "A missing optional dev tool may warn; a missing tracked deliverable, SSOT file or "
        "fixture must fail. Never print a success line on a skip path.",
    ),
    "SWALLOWED_FAILURE": (
        "Swallowed Failure",
        "set -euo pipefail / $ErrorActionPreference='Stop'; evaluate every stage's exit code.",
    ),
    "UNANCHORED_ALLOWLIST": (
        "Unanchored Allowlist",
        "Anchor the pattern (^...$) or compare exact paths.",
    ),
    "COUNT_ONLY_RATCHET": (
        "Count-Only / Raisable Ratchet",
        "Itemised lists or SHA-256 hashes of accepted exceptions; ratchets only shrink.",
    ),
    "TIMEOUT_AS_PASS": (
        "Timeout-as-Pass",
        "Timeout is failure; assert the terminal state explicitly.",
    ),
    "CHECK_WITHOUT_DIFF": (
        "Check-Without-Diff",
        "Evaluate the diff explicitly; non-empty diff => non-zero exit.",
    ),
    "SELF_COMPARISON": (
        "Self-Comparison",
        "Render into an empty location from the source of truth; check the generator's exit status.",
    ),
}

AGENT_JUDGMENT_ROWS = [
    "Measuring the Wrong Property",
    "Self-Certifying Predicate",
    "Empty-Set Pass",
    "Mock-Only Coverage",
    "Assertion-Free Test",
    "Snapshot Rubber-Stamp",
]

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", "target", ".mypy_cache", ".pytest_cache"}
SHELL_SUFFIX = {".sh", ".bash", ".zsh", ".ksh"}
JS_SUFFIX = {".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx"}
MAKE_NAMES = {"makefile", "gnumakefile"}
JUST_NAMES = {"justfile", ".justfile"}


@dataclass
class Finding:
    rule: str
    row: str
    path: str
    line: int
    excerpt: str
    detail: str
    remediation: str


# ---------------------------------------------------------------- language detection


def language(path: Path, text: str) -> str:
    n, sfx = path.name.lower(), path.suffix.lower()
    if sfx in SHELL_SUFFIX:
        return "shell"
    if sfx == ".ps1":
        return "powershell"
    if sfx == ".py":
        return "python"
    if sfx in (".yml", ".yaml"):
        return "yaml"
    if sfx == ".mk" or n in MAKE_NAMES:
        return "make"
    if sfx == ".just" or n in JUST_NAMES:
        return "just"
    if sfx in JS_SUFFIX:
        return "js"
    head = text[:200]
    if head.startswith("#!") and re.search(r"\b(sh|bash|zsh|dash)\b", head.splitlines()[0]):
        return "shell"
    if head.startswith("#!") and "python" in head.splitlines()[0]:
        return "python"
    return "unsupported"


def indent_of(line: str) -> int:
    return len(line) - len(line.lstrip())


# ---------------------------------------------------------------- shared regexes

RE_MISSING_PROBE = re.compile(
    r"(command -v|which\s+\w|hash\s+\w|\[\s*!?\s*-[efdxrs]\s|\[\[\s*!?\s*-[efdxrs]\s"
    r"|shutil\.which\([^)]*\)|os\.path\.exists\([^)]*\)|Path\([^)]*\)\.exists\(\)"
    r"|Get-Command\s|Test-Path\s)"
)
RE_BLOCK_OPEN = re.compile(r"(;\s*then\s*$|\bthen\s*$|\{\s*$|:\s*$|\bdo\s*$)")
RE_NEGATED = re.compile(r"(!|(^|\s)not\s|is\s+None|==\s*None|-z\s)")
RE_EXIT_ZERO = re.compile(r"(\bexit\s+0\b|\breturn\s+0\b|sys\.exit\(0\)|\breturn\s*$|\breturn\s+True\b|\bexit\b\s*$)")
RE_SUCCESS_LINE = re.compile(r"(?i)(echo|printf|print|write-host|write-output)[^#\n]*\b(pass(ed)?|ok\b|success|green|all good|clean)\b")
RE_SWALLOW = re.compile(r"(\|\|\s*(true|:)\s*(#|$)|\|\|\s*true\b|\|\|\s*:\s*$|;\s*true\s*$|\bset \+e\b|--exit-zero\b|\|\|\s*exit\s+0\b)")
RE_EXCEPT_PASS = re.compile(r"^\s*except\b[^:]*:\s*(pass|continue)?\s*$")
RE_EMPTY_CATCH = re.compile(r"\.catch\(\s*(\([^)]*\)|function\s*\([^)]*\))\s*=?>?\s*\{\s*\}\s*\)|catch\s*\([^)]*\)\s*\{\s*\}")
RE_CONTINUE_ON_ERROR = re.compile(r"^\s*continue-on-error\s*:\s*true\b")
RE_ALLOW_CONTEXT = re.compile(r"(?i)\b\w*(allow|whitelist|exempt|ignore|skip|exclude|permit|waiver|suppress)\w*\b")
RE_ANCHORED = re.compile(r"(\^|\$\)|\$\"|\$'|\$/|\\A|\\Z|-x\b|--fixed-strings|-F\b)")
RE_LOOSE_MATCH = re.compile(r"(grep\b|egrep\b|re\.(search|match|fullmatch)\(|\.includes\(|\.indexOf\(|any\([^)]*\bin\b|Select-String\b|\.startswith\(|\.contains\(|fnmatch\.)")
RE_COUNT_SUBJECT = re.compile(r"(?i)(\bcount\b|\blen\(|wc -l|\bn_\w+|\bnum\w*|\btotal\b|threshold|baseline|\blimit\b|\bmax_\w+|\bMAX\b|violations|failures|errors|warnings|budget)")
RE_NUM_COMPARE = re.compile(r"(-(le|lt|ge|gt|eq|ne)\s+\d+|[<>]=?\s*\d+|==\s*\d+|!=\s*\d+|\d+\s*[<>]=?)")
RE_TIMEOUT = re.compile(r"(\btimeout\b\s|\btimeout\d*\b|timeout=|timeout-minutes|Wait-Process|--timeout\b|TimeoutExpired)")
RE_TIMEOUT_SWALLOW = re.compile(r"\btimeout\b[^\n#]*(\|\|\s*(true|:)|\|\|\s*exit\s+0)")
RE_TIMEOUT_EXCEPT = re.compile(r"^\s*except\s+[\w.]*TimeoutExpired[^:]*:")
RE_BENIGN_TIMEOUT_BODY = re.compile(r"(raise|sys\.exit\(\s*[1-9]|return\s+(False|1)\b|fail)")
RE_CHECK_BRANCH = re.compile(
    r"(--check\b|--verify\b|^\s*(el)?if\s+[^:]*\b(args\.)?(check|verify|check_mode|verify_mode|dry_run)\b[^:]*:"
    r"|=\s*['\"]?(check|verify)['\"]?\s*\]|\bcase\b.*--check)"
)
RE_COMPARE_TOKEN = re.compile(
    r"(\bdiff\b|\bcmp\b|filecmp|hashlib|sha256|sha1sum|md5sum|shasum|==|!=|-eq\b|-ne\b|\bassert\b"
    r"|\bcompare\w*\(|\w*(check|verify|compare|diff)\w*\s*\(|differs|mismatch|expected|golden|Compare-Object)"
)
RE_DIFF_CALL = re.compile(r"(^|[;&|(\s])(diff|cmp)\s+([^\n]+)|filecmp\.cmp\(([^)]*)\)|Compare-Object\s+([^\n]+)")
RE_TEMPY = re.compile(r"(?i)(mktemp|\$\{?tmp|/tmp\b|tmpdir|temporarydirectory|tempfile\.|new-temporaryfile|\$env:temp|\.tmp\b)")
RE_WRITE_OUT = re.compile(r"(>\s*(\S+)|--out(?:put|-file)?[= ](\S+)|-o\s+(\S+)|write_text\(|\.write\()")
RE_GENERATOR = re.compile(r"(?i)(render|generate|gen\b|emit|build|scaffold|format\b|fmt\b|codegen|template)")


def _window(lines: list[str], i: int, n: int) -> list[str]:
    return lines[i : min(len(lines), i + n)]


def _block(lines: list[str], i: int, lang: str, cap: int = 30) -> list[str]:
    """Body of the branch opened on line i, by indentation (python-ish) or terminator (shell-ish)."""
    base = indent_of(lines[i])
    out: list[str] = []
    for line in lines[i + 1 : i + 1 + cap]:
        if not line.strip():
            out.append(line)
            continue
        if lang in ("python", "yaml"):
            if indent_of(line) <= base:
                break
        else:
            if re.match(r"^\s*(fi|;;|esac|\}|done)\b", line) and indent_of(line) <= base:
                break
            if indent_of(line) < base and line.strip():
                break
        out.append(line)
    return out


# ---------------------------------------------------------------- detectors


def det_skip_as_pass(path: str, lines: list[str], lang: str) -> list[Finding]:
    """An early success exit REACHED BY the miss path of a tool/file probe.

    The exit must be causally attached to the miss - same line after `||` (or `&&`/`then` when the
    probe is negated), or inside the branch the probe opens. An `exit 0` that merely happens to sit
    a few lines below a probe is not this defect and is not reported.
    """
    found = []
    for i, raw in enumerate(lines):
        line = raw.rstrip("\n")
        if line.lstrip().startswith(("#", "//")):
            continue
        body = line if lang == "python" else line.split("#")[0]
        m = RE_MISSING_PROBE.search(body)
        if not m:
            continue
        neg = bool(RE_NEGATED.search(body[: m.end()]))
        tail = body[m.end() :]
        scope: list[str] | None = None
        detail = ""
        conn = re.search(r"(&&|;\s*then|\bthen\b)", tail) if neg else re.search(r"\|\|", tail)
        if conn and RE_EXIT_ZERO.search(tail[conn.end() :]):
            scope = [tail[conn.end() :]]
            detail = "the miss path reaches a success exit on the same line"
        if scope is None and RE_BLOCK_OPEN.search(body):
            blk = _block(lines, i, lang)
            clean = [b if lang == "python" else b.split("#")[0] for b in blk]
            if neg:
                if any(RE_EXIT_ZERO.search(b) for b in clean):
                    scope = blk
                    detail = "a negated tool/path probe branches straight to a success exit"
            else:
                els = next((j for j, b in enumerate(clean) if re.match(r"^\s*(else|elif\b|\*\))", b.strip() or "x")), None)
                if els is not None and any(RE_EXIT_ZERO.search(b) for b in clean[els:]):
                    scope = blk[els:]
                    detail = "the else branch of a tool/path probe reaches a success exit"
        if scope is None:
            continue
        if any(RE_SUCCESS_LINE.search(s_) for s_ in scope):
            detail += " AND prints a success line on the skip path"
        found.append(Finding("SKIP_AS_PASS", RULES["SKIP_AS_PASS"][0], path, i + 1, line.strip(), detail, RULES["SKIP_AS_PASS"][1]))
    return found


def det_swallowed_failure(path: str, lines: list[str], lang: str) -> list[Finding]:
    found = []
    for i, raw in enumerate(lines):
        line = raw.rstrip("\n")
        body = line.split("#")[0] if lang != "python" else line
        stripped = line.lstrip()
        if stripped.startswith("#") or stripped.startswith("//"):
            continue
        detail = ""
        if RE_SWALLOW.search(body):
            detail = "the command's exit status is discarded"
        elif RE_CONTINUE_ON_ERROR.match(line):
            detail = "continue-on-error: true - the step cannot turn the job red"
        elif lang == "python" and RE_EXCEPT_PASS.match(line):
            detail = "bare except swallows the failure"
        elif lang == "python" and re.match(r"^\s*except\b[^:]*:\s*$", line):
            nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""
            if nxt in ("pass", "continue"):
                detail = "except body is `%s` - the failure is swallowed" % nxt
        elif lang in ("js", "yaml") and RE_EMPTY_CATCH.search(line):
            detail = "empty catch - the rejection is swallowed"
        elif lang == "make" and re.match(r"^\t-", raw):
            detail = "make recipe line prefixed with '-' - errors are ignored"
        if detail:
            found.append(Finding("SWALLOWED_FAILURE", RULES["SWALLOWED_FAILURE"][0], path, i + 1, line.strip(), detail, RULES["SWALLOWED_FAILURE"][1]))
    # file-level strict mode
    text = "".join(lines)
    if lang == "shell":
        if not re.search(r"^\s*set\s+-[a-zA-Z]*e|set\s+-o\s+errexit", text, re.M):
            found.append(Finding("SWALLOWED_FAILURE", RULES["SWALLOWED_FAILURE"][0], path, 1, (lines[0].strip() if lines else ""), "shell gate with no `set -e` family line: a failing stage does not stop the script", RULES["SWALLOWED_FAILURE"][1]))
        pipeline = any(re.search(r"[^|]\|[^|]", ln.split("#")[0]) for ln in lines)
        if pipeline and "pipefail" not in text:
            found.append(Finding("SWALLOWED_FAILURE", RULES["SWALLOWED_FAILURE"][0], path, 1, (lines[0].strip() if lines else ""), "pipeline present but no `set -o pipefail`: PIPESTATUS is masked, only the last stage's status survives", RULES["SWALLOWED_FAILURE"][1]))
    if lang == "powershell" and not re.search(r"ErrorActionPreference\s*=\s*['\"]Stop", text):
        found.append(Finding("SWALLOWED_FAILURE", RULES["SWALLOWED_FAILURE"][0], path, 1, (lines[0].strip() if lines else ""), "PowerShell gate with no $ErrorActionPreference='Stop': non-terminating errors do not fail the run", RULES["SWALLOWED_FAILURE"][1]))
    return found


def det_unanchored_allowlist(path: str, lines: list[str], lang: str) -> list[Finding]:
    found = []
    for i, raw in enumerate(lines):
        line = raw.rstrip("\n")
        stripped = line.lstrip()
        if stripped.startswith("#") or stripped.startswith("//"):
            continue
        if not RE_ALLOW_CONTEXT.search(line) or not RE_LOOSE_MATCH.search(line):
            continue
        if RE_ANCHORED.search(line):
            continue
        found.append(Finding("UNANCHORED_ALLOWLIST", RULES["UNANCHORED_ALLOWLIST"][0], path, i + 1, line.strip(), "allow/ignore match with no ^...$ anchor and no exact-path compare - it exempts more than intended", RULES["UNANCHORED_ALLOWLIST"][1]))
    return found


def det_count_only_ratchet(path: str, lines: list[str], lang: str) -> list[Finding]:
    found = []
    for i, raw in enumerate(lines):
        line = raw.rstrip("\n")
        stripped = line.lstrip()
        if stripped.startswith("#") or stripped.startswith("//"):
            continue
        if not RE_COUNT_SUBJECT.search(line):
            continue
        if not RE_NUM_COMPARE.search(line):
            continue
        if re.search(r"(-eq\s+0\b|==\s*0\b|[<>]=?\s*0\b|!=\s*0\b|-ne\s+0\b|-gt\s+0\b)", line):
            continue  # comparing against zero is an itemised "none allowed", not a raisable ratchet
        found.append(Finding("COUNT_ONLY_RATCHET", RULES["COUNT_ONLY_RATCHET"][0], path, i + 1, line.strip(), "a numeric threshold on a count: swapping one violation for another still passes, and the number can be raised", RULES["COUNT_ONLY_RATCHET"][1]))
    return found


def det_timeout_as_pass(path: str, lines: list[str], lang: str) -> list[Finding]:
    found = []
    for i, raw in enumerate(lines):
        line = raw.rstrip("\n")
        if RE_TIMEOUT_SWALLOW.search(line.split("#")[0]):
            found.append(Finding("TIMEOUT_AS_PASS", RULES["TIMEOUT_AS_PASS"][0], path, i + 1, line.strip(), "a timed-out step yields exit 0", RULES["TIMEOUT_AS_PASS"][1]))
        if lang == "python" and RE_TIMEOUT_EXCEPT.match(line):
            body = _block(lines, i, "python", cap=6)
            if not any(RE_BENIGN_TIMEOUT_BODY.search(b) for b in body):
                found.append(Finding("TIMEOUT_AS_PASS", RULES["TIMEOUT_AS_PASS"][0], path, i + 1, line.strip(), "TimeoutExpired is caught and the handler neither raises nor fails - the kill is invisible", RULES["TIMEOUT_AS_PASS"][1]))
    text = "".join(lines)
    if lang in ("shell", "recipe", "make", "just", "yaml") and re.search(r"(^|[;&|(\s])timeout\s+\d", text, re.M):
        if not re.search(r"\b124\b|\$\?|returncode|exit_code|PIPESTATUS", text):
            first = next((j for j, ln in enumerate(lines) if re.search(r"(^|[;&|(\s])timeout\s+\d", ln)), 0)
            found.append(Finding("TIMEOUT_AS_PASS", RULES["TIMEOUT_AS_PASS"][0], path, first + 1, lines[first].strip(), "`timeout` is used but the file never inspects an exit status or the 124 kill code - nothing asserts the terminal state", RULES["TIMEOUT_AS_PASS"][1]))
    return found


def det_check_without_diff(path: str, lines: list[str], lang: str) -> list[Finding]:
    found = []
    for i, raw in enumerate(lines):
        line = raw.rstrip("\n")
        stripped = line.lstrip()
        if stripped.startswith("#") or stripped.startswith("//"):
            continue
        if not RE_CHECK_BRANCH.search(line):
            continue
        if re.search(r"add_argument|\bhelp=|usage|argument-hint", line):
            continue
        body = _block(lines, i, lang)
        if not body or not any(b.strip() for b in body):
            continue
        if any(RE_COMPARE_TOKEN.search(b) for b in body):
            continue
        found.append(Finding("CHECK_WITHOUT_DIFF", RULES["CHECK_WITHOUT_DIFF"][0], path, i + 1, line.strip(), "a --check/--verify branch whose body contains no comparison at all - it reports without ever looking", RULES["CHECK_WITHOUT_DIFF"][1]))
    return found


def _operands(line: str) -> list[str]:
    m = RE_DIFF_CALL.search(line)
    if not m:
        return []
    tail = next((g for g in m.groups()[2:] if g), "")
    toks = [t for t in re.split(r"[\s,]+", tail.strip()) if t and not t.startswith("-")]
    return [t.strip("'\"()") for t in toks][:2]


def det_self_comparison(path: str, lines: list[str], lang: str) -> list[Finding]:
    found = []
    for i, raw in enumerate(lines):
        line = raw.rstrip("\n")
        stripped = line.lstrip()
        if stripped.startswith("#") or stripped.startswith("//"):
            continue
        ops = _operands(line)
        if len(ops) < 2:
            continue
        back = lines[max(0, i - 10) : i]
        for prev in back:
            p = prev.split("#")[0]
            if not RE_GENERATOR.search(p):
                continue
            hit = next((o for o in ops if o and o in p), None)
            if hit is None:
                continue
            if RE_TEMPY.search(p) or RE_TEMPY.search(line) or any(RE_TEMPY.search(b) for b in back):
                continue  # rendered into a temp location: that is the remediation, not the defect
            found.append(Finding("SELF_COMPARISON", RULES["SELF_COMPARISON"][0], path, i + 1, line.strip(), "`%s` is regenerated in the same tree %d line(s) above and then compared against itself - the comparison cannot fail" % (hit, i - back.index(prev)), RULES["SELF_COMPARISON"][1]))
            break
    return found


DETECTORS = {
    "SKIP_AS_PASS": det_skip_as_pass,
    "SWALLOWED_FAILURE": det_swallowed_failure,
    "UNANCHORED_ALLOWLIST": det_unanchored_allowlist,
    "COUNT_ONLY_RATCHET": det_count_only_ratchet,
    "TIMEOUT_AS_PASS": det_timeout_as_pass,
    "CHECK_WITHOUT_DIFF": det_check_without_diff,
    "SELF_COMPARISON": det_self_comparison,
}


# ---------------------------------------------------------------- target resolution


def recipe_lines(lines: list[str], target: str, lang: str) -> list[str] | None:
    """Blank every line outside the named Makefile/justfile recipe, keeping line numbers."""
    pat = re.compile(r"^%s\b[^=]*:" % re.escape(target))
    start = next((i for i, ln in enumerate(lines) if pat.match(ln)), None)
    if start is None:
        return None
    out = [""] * len(lines)
    for j in range(start + 1, len(lines)):
        ln = lines[j]
        if ln.strip() and indent_of(ln) == 0 and not ln.startswith("\t"):
            break
        out[j] = ln.lstrip("\t") if lang == "make" else ln
    return out


def collect(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    files: list[Path] = []
    for p in sorted(target.rglob("*")):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        files.append(p)
    return files


def audit(target: Path, target_name: str | None, only: list[str]) -> tuple[list[Finding], list[str]]:
    findings: list[Finding] = []
    scanned: list[str] = []
    for p in collect(target):
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        lang = language(p, text)
        if lang == "unsupported":
            continue
        lines = text.splitlines(keepends=True)
        if target_name:
            if lang not in ("make", "just"):
                continue
            sub = recipe_lines(lines, target_name, lang)
            if sub is None:
                continue
            lines, lang = sub, "recipe"  # shell-shaped body, but not a script: no file-level strict-mode rule
        scanned.append(str(p))
        for rid in only:
            findings.extend(DETECTORS[rid](str(p), lines, lang))
    findings.sort(key=lambda f: (f.path, f.line, f.rule))
    return findings, scanned


# ---------------------------------------------------------------- reporting


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", nargs="?", help="CI workflow, gate script, Makefile/justfile, or test directory")
    ap.add_argument("--target", dest="recipe", help="Makefile/justfile recipe name; scan only that recipe's body")
    ap.add_argument("--only", help="comma-separated rule ids (default: all seven)")
    ap.add_argument("--json", action="store_true", help="machine-readable report")
    ap.add_argument("--quiet", action="store_true", help="findings only, no trailing summary")
    ap.add_argument("--list-rules", action="store_true", help="print implemented rules and the rows left to agent judgment")
    a = ap.parse_args()

    if a.list_rules:
        print("DETECTED (one rule per mechanically decidable SKILL.md section 7 row):")
        for rid, (row, rem) in RULES.items():
            print(f"  {rid:<22} {row}\n      fix: {rem}")
        print("\nNOT DETECTED - agent judgment, prompted by skills/gate-audit/SKILL.md:")
        for row in AGENT_JUDGMENT_ROWS:
            print(f"  {row}")
        return 0

    if not a.target:
        ap.error("a target path is required (or --list-rules)")

    only = list(RULES)
    if a.only:
        only = [r.strip().upper() for r in a.only.split(",") if r.strip()]
        bad = [r for r in only if r not in RULES]
        if bad:
            print(f"gate-audit: unknown rule id(s): {', '.join(bad)}", file=sys.stderr)
            return 2

    t = Path(a.target)
    if not t.exists():
        print(f"gate-audit: target does not exist: {t}", file=sys.stderr)
        return 2

    findings, scanned = audit(t, a.recipe, only)

    if not scanned:
        why = f"no recipe named {a.recipe!r}" if a.recipe else "no file of a supported language"
        print(f"gate-audit: NOTHING AUDITED - {why} under {t}. This is not a pass.", file=sys.stderr)
        return 2

    if a.json:
        print(json.dumps({
            "target": str(t), "recipe": a.recipe, "files_scanned": scanned,
            "rules_run": only, "rules_agent_judgment": AGENT_JUDGMENT_ROWS,
            "findings": [asdict(f) for f in findings],
            "verdict": "vacuous_gates_found" if findings else "no_pattern_matched",
        }, indent=2))
        return 1 if findings else 0

    print(f"gate-audit: {t}" + (f" [recipe {a.recipe}]" if a.recipe else ""))
    for f in findings:
        print(f"  {f.path}:{f.line}  {f.rule}  ({f.row})")
        print(f"      > {f.excerpt[:140]}")
        print(f"      why: {f.detail}")
        print(f"      fix: {f.remediation}")
    n_files = len({f.path for f in findings})
    if findings:
        print(f"== gate-audit: {len(findings)} vacuous-gate pattern(s) in {n_files} of {len(scanned)} file(s) scanned")
    else:
        print(f"== gate-audit: no pattern matched in {len(scanned)} file(s) scanned")
    if not a.quiet:
        print("   NOT PROVEN by this run: " + ", ".join(AGENT_JUDGMENT_ROWS) + " - those rows need a reader.")
        print("   A clean run means 'no pattern matched', not 'this gate can fail'. Prove each cleared")
        print("   gate by planting the violation it claims to catch and requiring it to go red.")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
