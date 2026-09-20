---
name: gate-audit
description: Audit standing gates against the "Checks That Cannot Fail" taxonomy, then plant the violation each cleared gate claims to catch and require it to go red
version: 2.0.0
---

# GitHub Copilot /gate-audit Workflow

A gate that cannot fail is worse than a missing one: everyone believes the rule is enforced. This audits the **standing** gate machinery whether or not it changed — unlike `/review`, which audits a diff.

`$S` = the dev-loop `scripts/` directory. Target: a CI workflow, a gate/lint script, a `Makefile`/`justfile`, or a test directory.

1. **Detector half.** `python3 $S/gate_audit.py <target> [--target RECIPE] [--only RULE,...] [--json]`. It detects **seven** mechanically decidable taxonomy rows and no others: `SKIP_AS_PASS`, `SWALLOWED_FAILURE`, `UNANCHORED_ALLOWLIST`, `COUNT_ONLY_RATCHET`, `TIMEOUT_AS_PASS`, `CHECK_WITHOUT_DIFF`, `SELF_COMPARISON`. `--list-rules` prints those and the rows it does not detect.
2. **Exit codes.** `0` = no pattern matched — *not* proof the gate can fail. `1` = vacuous gate(s) found, each with its row, line, reason and remediation. `2` = **nothing was audited** (unreadable, unsupported, no scannable file, no such recipe); never report a `2` as clean.
3. **Triage.** Findings are pattern matches, not verdicts. Read the surrounding gate; cite the detector limit from `$S/../references/gate-audit.md` when you dismiss one.
4. **Judgment half.** Six rows need a reader and the script never claims them: Measuring the Wrong Property, Self-Certifying Predicate, Empty-Set Pass, Mock-Only Coverage, Assertion-Free Test, Snapshot Rubber-Stamp. Work each against SKILL.md §7.
5. **Plant and prove.** For every gate the audit CLEARS: plant the violation it claims to catch, run the gate unchanged, require it to FAIL naming the plant. Stays green ⇒ **vacuous regardless of how it reads**. Restore the tree; never `git add` or commit a plant. Prefer the tool's own error; otherwise `DEVLOOP-PLANTED-<TARGET-ID>`, never a string that also appears in the fixture's filename or the gate's prompt.
6. **Blast radius.** A repaired gate was silently passing real violations, so it makes the pipeline redder — say what it will start catching before arming it. Narrow an over-claimed scope rather than widen the check. **Honest red beats green that lies.**

Report per gate: path · row (or CLEARED) · evidence · plant-and-prove receipt or **VACUOUS** · remediation · blast radius. Then what was **not** audited.
