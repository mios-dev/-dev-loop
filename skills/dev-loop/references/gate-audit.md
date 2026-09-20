# `/gate-audit` coverage map — SKILL §7 row → detector or agent judgment

This file exists so the command's coverage claim stays **auditable**. `gate_audit.py` implements
part of the SKILL.md §7 "Checks That Cannot Fail" taxonomy; the rest is prompted judgment. A shim
that blurred the two would be exactly the over-claiming defect §7 is about.

Do not copy the taxonomy text here — the rows, their mechanisms and their remediations are
**SKILL.md §7**, which is the single source. This file records only the mapping, and the mapping
is asserted by `tests/test_gate_audit.py` (every rule id `--list-rules` prints must appear below,
and every judgment row must be recorded as judgment).

## Mechanically decidable — implemented in `skills/dev-loop/scripts/gate_audit.py`

| §7 row | Rule id | What the detector actually matches | Known limits |
|---|---|---|---|
| Skip-as-Pass | `SKIP_AS_PASS` | a tool/file probe (`command -v`, `which`, `[ -f ]`, `shutil.which`, `os.path.exists`, `Test-Path`, `Get-Command`) whose **miss path** reaches `exit 0` / `return 0` / `sys.exit(0)` — same line after `\|\|` (or `&&`/`then` when the probe is negated), or inside the branch the probe opens, including its `else`. Appends "AND prints a success line" when the skip path echoes pass/ok/success. | Causality is syntactic. A miss path that reaches success through a called function, or a probe whose result is stored in a variable and tested later, is not matched. |
| Swallowed Failure | `SWALLOWED_FAILURE` | `\|\| true`, `\|\| :`, `\|\| exit 0`, trailing `; true`, `set +e`, `--exit-zero`; `continue-on-error: true`; `except…: pass/continue`; empty `.catch(() => {})` / `catch (e) {}`; a `-`-prefixed make recipe line; file-level: a shell script with no `set -e` family line, a shell pipeline with no `pipefail`, a `.ps1` with no `$ErrorActionPreference='Stop'`. | Does not evaluate whether a swallowed stage mattered. A gate that checks `$?` by hand after `set +e` is still reported. |
| Unanchored Allowlist | `UNANCHORED_ALLOWLIST` | a line naming an allow/ignore/skip/exempt/exclude/whitelist/waiver/suppress identifier **and** performing a loose match (`grep`, `re.search`/`match`, `.includes(`, `.indexOf(`, `.startswith(`, `any(… in …)`, `fnmatch`, `Select-String`) with no `^…$` anchor, `-x`/`-F`, or exact compare. | `x in SET` (membership in a set of exact strings) is deliberately **not** flagged — it is an exact compare. A pattern anchored in a variable defined elsewhere reads as unanchored. |
| Count-Only / Raisable Ratchet | `COUNT_ONLY_RATCHET` | a numeric comparison (`-le 12`, `<= 12`, `== 3`, `> 5`) against a count-ish subject (`count`, `len(`, `wc -l`, `total`, `threshold`, `baseline`, `limit`, `max_*`, `violations`, `failures`). Comparisons against `0` are skipped — "none allowed" is itemised, not raisable. | Cannot tell a shrink-only ratchet from a raisable one; the row's remediation is itemised lists or hashes either way. |
| Timeout-as-Pass | `TIMEOUT_AS_PASS` | `timeout …` whose failure is swallowed (`\|\| true`, `\|\| exit 0`); a Python `except …TimeoutExpired:` handler that neither raises nor returns a failure; file-level: a file that runs `timeout N` but never inspects `$?`, `PIPESTATUS`, a return code, or the `124` kill code. | A watcher in another process, or a timeout enforced by the CI platform rather than the script, is invisible here. |
| Check-Without-Diff | `CHECK_WITHOUT_DIFF` | a `--check`/`--verify`/`dry_run` branch whose body contains **no** comparison token at all — no `diff`, `cmp`, `filecmp`, hash, `==`/`!=`/`-eq`, `assert`, `Compare-Object`, and no call whose name contains check/verify/compare/diff. `add_argument` lines are excluded. | Body is bounded (≤ 30 lines, to the dedent/terminator). A comparison performed deeper inside a helper with an unrelated name reads as missing. |
| Self-Comparison | `SELF_COMPARISON` | a `diff`/`cmp`/`filecmp.cmp`/`Compare-Object` whose operand was **written by a generator** (`render`, `generate`, `emit`, `build`, `scaffold`, `fmt`, `codegen`, `template`) within the preceding 10 lines, into the tree rather than a temp location. Suppressed when `mktemp`/`$TMPDIR`/`TemporaryDirectory`/`tempfile` appears in the generate line, the diff line, or the window. | Window-bounded. A regenerate step far above the compare, or one hidden in a called target, is not matched. |

Exit codes: `0` no pattern matched · `1` vacuous gate(s) found · `2` target unreadable, unsupported,
or containing no scannable file (**nothing audited is never a pass**).

## Agent judgment — prompted by `skills/gate-audit/SKILL.md`, never claimed by the script

These six rows need a reader who knows what the gate is *for*. `gate_audit.py` does not detect them
and does not pretend to; `--list-rules` prints them under "NOT DETECTED".

| §7 row | Why no detector | What the agent is asked |
|---|---|---|
| Measuring the Wrong Property | "proxy vs property" is semantic. | Name the property the gate claims to enforce, then the property it measures. If they differ, say so. |
| Self-Certifying Predicate | Requires knowing which text the subject was *given*. | Ask whether the evidence includes the subject's own name, filename or prompt text. |
| Empty-Set Pass | Needs the runtime collection, not the source. | Run the gate against an empty input set; if it passes, it has no non-empty assertion. |
| Mock-Only Coverage | Requires knowing which collaborators are real boundaries. | Ask which boundary is exercised for real; one integration-shaped test per boundary. |
| Assertion-Free Test | Every framework spells assertions differently; a detector here becomes its own proxy check. | Read the test bodies the gate runs; a test that executes and asserts nothing is vacuous. |
| Snapshot Rubber-Stamp | Needs review history, not source. | Ask whether goldens were updated wholesale (`-u`) in the same commit as a behaviour change. |

## Keeping this file honest

When a detector is added, move its row up, give it a rule id, and record the limits — the table is
the coverage claim. When a detector is removed, move the row back down. `tests/test_gate_audit.py`
fails if a rule id is advertised by the CLI and missing here, or if a judgment row disappears.
