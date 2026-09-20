---
description: Audit the repo's STANDING gates against the "Checks That Cannot Fail" taxonomy, then plant the violation each cleared gate claims to catch and require it to go red
argument-hint: [ci-file|script|target|test-dir]
---

# /gate-audit: Can This Gate Fail?

Target: `$ARGUMENTS` — a CI workflow, a gate/lint script, a `Makefile`/`justfile` (one recipe via `--target NAME`), or a test directory. Empty: list the repo's real gates first and say which you are auditing.

Below, `$S` = the dev-loop `scripts/` directory (`<skills dir>/dev-loop/scripts/`).

A gate that cannot fail is worse than a missing one — everyone believes the rule is enforced. This audits the **standing** machinery whether or not it changed, unlike `/review`, which audits a diff. Read SKILL.md §7 for the taxonomy; the coverage map is `$S/../references/gate-audit.md`.

## Protocol

1. **Detector half.** `python3 $S/gate_audit.py <target> [--target RECIPE] [--only RULE,...] [--json]`. It detects **seven** mechanically decidable §7 rows and nothing else: `SKIP_AS_PASS`, `SWALLOWED_FAILURE`, `UNANCHORED_ALLOWLIST`, `COUNT_ONLY_RATCHET`, `TIMEOUT_AS_PASS`, `CHECK_WITHOUT_DIFF`, `SELF_COMPARISON`. `--list-rules` prints them, plus the rows it does not detect.
2. **Exit codes, exactly.** `0` = no pattern matched — *not* "the gate can fail"; step 4 is still owed. `1` = vacuous-gate pattern(s) found, each with its §7 row, line, reason and remediation. `2` = **nothing was audited** (unreadable, unsupported, no scannable file, no such recipe) — never report a `2` as clean.
3. **Triage every finding.** They are pattern matches, not verdicts. Open the surrounding gate and say whether it is real; when you dismiss one, cite the detector limit from the coverage map.
4. **Judgment half — six rows no script decides**, and the script never claims them: Measuring the Wrong Property (proxy vs property), Self-Certifying Predicate (evidence containing the subject's own name or prompt text), Empty-Set Pass (run the gate on an empty input set), Mock-Only Coverage, Assertion-Free Test, Snapshot Rubber-Stamp. Work each against the §7 row text.
5. **Plant and prove — the two-sided step.** For every gate the audit CLEARS: state what it claims to catch, plant exactly that violation in a real input, run the gate unchanged, and require it to FAIL **naming the plant**. A failure for another reason proves nothing; a gate that stays green is **vacuous regardless of how it reads**. Restore the tree (`git status --porcelain` empty); never `git add` or commit a plant. Prefer the tool's own error on a real mutation; otherwise plant `DEVLOOP-PLANTED-<TARGET-ID>` — never a string that also appears in the fixture's filename or the gate's own prompt.
6. **Blast radius before arming a repair.** A repaired gate was silently passing real violations, so repairing it makes the pipeline redder. Tell the operator what it will start catching, how much is pre-existing debt, and offer the order (land red and fix forward, or fix the backlog first). A vacuous check often over-claims its scope: narrow the claim rather than widen the check. **Honest red beats green that lies.**

## Report

Per gate: path · §7 row (or CLEARED) · one-line evidence · plant-and-prove receipt (plant, command, failing line) or **VACUOUS: stayed green under its own violation** · remediation · blast-radius estimate. Then what was **not** audited: targets out of scope, rows left to judgment, detector limits relied on. Never let "no pattern matched" read as "verified".
