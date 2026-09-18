# SCOPE Staged Code Review Specification (`/review`, `/rv`)

The Staged Code Review engine enforces quality and safety gates based on the SCOPE assurance model prior to branch merge.

---

## 1. Audit Dimensions

1. **Security & Secrets:** Blocks hardcoded API tokens, credentials, private keys, and unsanitized shell executions.
2. **Contract Preservation:** Verifies API schema invariants and interface compatibility against `GOALS.md` and `DOD.md`.
3. **Hygiene & Simplification:** Flags leftover debug prints, orphaned test mocks, and dead code.

---

## 2. Execution CLI

```bash
# Review recent commit or branch diff
python3 scripts/review.py HEAD

# Scaffold formal review rubric
python3 scripts/review.py --init
```
