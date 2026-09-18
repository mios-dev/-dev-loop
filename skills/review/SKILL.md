---
name: review
description: SCOPE staged code review of a diff - contract preservation, invariant and security audit, suppression/threshold drift, dead code, and a verification-evidence check against the Definition of Done. Use before merging a lane, before /ship, or when asked to review changes.
argument-hint: "[target_ref|--staged]"
context: fork
agent: dev-loop:auditor
allowed-tools: Read, Grep, Glob, Bash
---
# /review — SCOPE review (read-only)

_Paths: `${CLAUDE_SKILL_DIR}/../dev-loop/scripts/` resolves in Claude Code; in other harnesses use `<skills dir>/dev-loop/scripts/` (the shims in `shims/<harness>/` already do)._

Target: `$ARGUMENTS` (default: staged changes, else HEAD).

1. `python3 ${CLAUDE_SKILL_DIR}/../dev-loop/scripts/review.py <target>` → `.devloop/review_*.json` + `REVIEW.md` (rubric: `assets/templates/REVIEW_RUBRIC.md`).
2. Manually verify what the tool cannot: does the diff widen types, loosen assertions, raise thresholds, add `# noqa`/`@skip`/baseline entries, or delete tests (SKILL §8)? Does every claim of "tested" cite a positive AND a negative control (§6)? Do the changed paths stay inside the task's scope?
3. Secrets: `python3 ${CLAUDE_SKILL_DIR}/../dev-loop/scripts/adapters.py secrets --wt .`; dependency change staged → `adapters.py deps --wt .`.
4. Verdict: PASSED | REVISE (list exact fixes with file:line) | BLOCKED (why). Never edit files in this skill; return the verdict and the report path.
