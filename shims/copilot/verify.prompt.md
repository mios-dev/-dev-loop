---
name: verify
description: Two-sided verification gate — positive control passes, planted negative control fails naming the plant, tree restored
version: 2.0.0
---

# GitHub Copilot /verify Workflow

A check that cannot fail passes identically on correct and broken code. Verify both sides; never assert in prose that both controls passed.

`$S` = the dev-loop `scripts/` directory.

1. **Lane object.** From a task: `python3 $S/artifacts.py tasks lane <T-0NN> --root . > RUNDIR/lane.json` (prints to stdout; no `--out`). A value returned as the literal `<fill>` means no control is defined — stop and ask; never invent a negative control.
2. **Run dir first.** `mkdir -p RUNDIR` — the gate does **not** create `--run` and crashes (`FileNotFoundError`, exit 1) if it is missing. Keep it git-ignored (`.devloop/run-*/` in `.git/info/exclude`, never `.devloop/` wholesale) or outside the worktree, or the gate's own `neg-<id>.log` counts as an unrestored tree and reports a false exit 2.
3. **Gate.** `python3 $S/adapters.py gate --lane RUNDIR/lane.json --wt . --run RUNDIR` — all three flags are mandatory.
4. **Exit codes.** `0` = positive passed, negative failed for the named reason, tree restored. `1` = the positive (or full) gate failed — honest red. `2` = REFUSED/VACUOUS, nothing proven: sentinel already existed, tree not restored, base-tree leakage, negative control PASSED, expect-string mismatch, or surviving mutants. Never call a `2` "mostly passing".
5. **Artifacts.** `pos-<id>.log`, `neg-<id>.log`, and when present `mut-<id>.log`, `full-<id>.log`, `lane-<id>.patch` (the parked pre-control diff). Quote the proving line.
6. **Plant naming.** Prefer the tool's own error on a real mutation; otherwise exactly `DEVLOOP-PLANTED-<LANE_ID>`, unique per lane.
7. **Prose deliverables.** `python3 $S/check_finding.py <repo_root> <findings_file>` — 7 required sections, a verdict from CONFIRMED/PARTLY_CONFIRMED/REFUTED/STALE, ≥ 3 `path:line` citations, all resolving.

Do **not** cite `scripts/verify_harness.py` or `scripts/contracts.py`: both are importable libraries whose `__main__` only prints a readiness line, imported by nothing. Promising behaviour the code does not implement is itself a defect.
