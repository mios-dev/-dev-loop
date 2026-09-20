# Antigravity Workflow: /workflows:verify

Identifier: `verify`
Purpose: Run the two-sided gate on work in progress — positive control passes, planted negative control FAILS naming the plant, tree restored
Input: `[task-id|lane.json]`

# /verify: Two-Sided Verification Gate

Target: `the workflow input` — a task id (`T-0NN`), a path to a lane JSON, or empty.

Below, `$S` = the dev-loop `scripts/` directory (`<skills dir>/dev-loop/scripts/`).

A check that cannot fail passes identically on correct and on broken code. Verification is two-sided: a **positive control** (it works) AND a **negative control** (plant the defect; the same check must fail, naming what you planted). Do not assert in prose that both controls passed — run the gate.

## Protocol

1. **Lane object.** Task id → `python3 $S/artifacts.py tasks lane <id> --root . > RUNDIR/lane.json` (it prints to stdout; there is no `--out`). Lane path → use as given. Empty → build `{id, positive_cmd, negative_control_cmd, negative_expect}` from the task. **A value that comes back as the literal `<fill>` means the task defines no control: STOP and ask the operator. Never invent a negative control nobody defined.**
2. **Run dir.** `mkdir -p .devloop/run-verify-$(date +%s)` — `adapters.py gate` requires `--lane`, `--wt` and `--run`, all three, and writes into `--run` **without creating it** (a missing dir raises `FileNotFoundError` and exits 1 — that traceback is not a failing positive control). The run dir must be git-ignored or outside the worktree: the gate writes `neg-<id>.log` before taking its "after" tree snapshot, so a tracked run dir reports a false exit 2. Use the narrow exclude `.devloop/run-*/` in `.git/info/exclude`, never `.devloop/` wholesale.
3. **Gate.** `python3 $S/adapters.py gate --lane RUNDIR/lane.json --wt . --run RUNDIR` (optional `--root BASE`, `--shell sh|pwsh`).
4. **Read the exit code exactly.**
   - `0` — positive passed AND negative failed for the named reason AND the tree was restored (plus `mutation_cmd` / `full_gate_cmd` if the lane sets them). Verified.
   - `1` — `positive_cmd` (or `full_gate_cmd`) failed. Honest red: the code is not done. Fix the cause; do not weaken the check.
   - `2` — **REFUSED / VACUOUS: nothing was proven.** Report which of these the gate printed: the sentinel already existed in the worktree before the control ran (refused pre-emptively); the tree was not restored; base-tree leakage; the negative control PASSED; it failed but did not match `negative_expect`; or the mutation gate found surviving mutants. **Never summarise a 2 as "mostly passing".**
5. **Artifacts.** Point at `pos-<id>.log` and `neg-<id>.log`, plus `mut-<id>.log`, `full-<id>.log` and `lane-<id>.patch` when present — the patch is the pre-control diff, parked when the tree was not restored or leakage was found. Quote the proving line; do not paraphrase.
6. **Naming the plant.** Prefer an organic expect string (mutate real code, match the tool's own error). Only where nothing mutates naturally, plant exactly `DEVLOOP-PLANTED-<LANE_ID>`, one unique sentinel per lane. A shared sentinel lets either lane satisfy the other's gate; an expect string that also appears in the fixture's own filename passes whether or not the plant landed.
7. **Prose deliverables.** When the deliverable is a measurement rather than code: `python3 $S/check_finding.py <repo_root> <findings_file>`. Exit 0 requires the seven sections (`## VERDICT`, `## WHAT IS ACTUALLY TRUE`, `## NUMBERS`, `## PROPOSED FIX`, `## FILES TO CHANGE`, `## NEGATIVE CONTROL`, `## UNVERIFIED`), a verdict from `CONFIRMED | PARTLY_CONFIRMED | REFUTED | STALE`, at least 3 `path:line` citations, and every citation resolving against the tree.

## Do not cite

`scripts/verify_harness.py` and `scripts/contracts.py` are importable libraries whose `__main__` only prints a readiness line; nothing imports them. They are not runnable gates. Promising behaviour the code does not implement is itself a defect.

Return the exit code, its exact meaning, the artifact paths, and — on 0 — the line of `neg-<id>.log` showing the check failing for the planted reason.
