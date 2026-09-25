---
name: verify
description: Run the two-sided gate on work in progress - the positive control must pass, a planted negative control must FAIL naming the plant, and the tree must be restored unchanged. Wraps `adapters.py gate` so single-threaded work in any harness can reach the same gate an orchestrated lane gets, instead of asserting in prose that both controls passed. Also gates prose deliverables with `check_finding.py`. Use before claiming a task is done, before /review or /ship, or whenever someone says "tested" without showing a control that failed.
argument-hint: "[task-id|lane.json]"
allowed-tools: Read, Grep, Glob, Bash
---
# /verify — prove the check can fail (SKILL §6, §7, §11)

_Paths: `${CLAUDE_SKILL_DIR}/../dev-loop/scripts/` resolves in Claude Code; in other harnesses use `<skills dir>/dev-loop/scripts/` (the shims in `shims/<harness>/` already do)._ Below, `$S` = that scripts directory.

A passing test proves nothing on its own: a check that cannot fail passes identically on correct and broken code. Verification is two-sided — a **positive control** (the thing works) *and* a **negative control** (plant the defect; the same check must fail, and fail *naming what you planted*). This skill is the only way to run that gate outside an orchestrated lane. Never report "both controls passed" from prose alone; run it.

## 1. Get a lane object

`$ARGUMENTS` is a task id, a path to a lane JSON, or empty.

- **Task id** (e.g. `T-012`): `python3 $S/artifacts.py tasks lane T-012 --root . > RUNDIR/lane.json` (prints to stdout; there is no `--out`). It emits the lane from the task's `verification` block. **If any value comes back as the literal `<fill>`, the task defines no control — STOP.** Ask the operator for the positive command, the mutation, and the expect string. Never invent a negative control nobody defined.
- **Lane path**: use as given.
- **Empty**: build the minimum object yourself, from the task and the project gate — same rule, no invented controls:

```json
{ "id": "t-012",
  "positive_cmd": "<the project gate command that must pass>",
  "negative_control_cmd": "<plant the defect, run the same check, restore the tree, exit non-zero>",
  "negative_expect": "<regex the negative output must match>" }
```

Optional, also honoured by the gate: `mutation_cmd`, `full_gate_cmd`, `worker.timeout_s`, `worktree_root`.

## 2. Make a run directory — the gate will not create it

```sh
mkdir -p .devloop/run-verify-$(date +%s)
```

`adapters.py gate` requires `--lane`, `--wt` and `--run`, all three, and **writes its logs into `--run` without creating it**: a missing directory raises `FileNotFoundError` and exits 1. That traceback is *not* a failing positive control — read the output, not just the code.

The run directory must also be **git-ignored or outside the worktree**. The gate compares `git status --porcelain -uall` + `git diff` before and after the control, and it writes `neg-<id>.log` *before* taking the "after" snapshot — so a tracked run directory makes the gate's own log look like an unrestored tree and reports a false exit 2. Use the narrow exclude (`.devloop/run-*/` in `.git/info/exclude`), never `.devloop/` wholesale — excluding it hides lane deliverables and turns delivered work into a vacuous verdict (§11).

## 3. Run the gate

```sh
python3 $S/adapters.py gate --lane RUNDIR/lane.json --wt . --run RUNDIR   # [--root BASE] [--shell sh|pwsh]
```

`--wt` defaults to the working tree you are in (`.`). `--root` names the base repository for the leakage audit when `--wt` is a worktree.

## 4. Interpret the exit code exactly — this is the whole point

| Exit | Meaning | What you report |
|---|---|---|
| **0** | positive passed **and** negative failed for the named reason **and** the tree was restored (and `mutation_cmd` / `full_gate_cmd` passed if present) | Verified. Cite the logs. |
| **1** | `positive_cmd` failed, or `full_gate_cmd` failed | Honest red. The code is not done. Fix the cause (§8), do not weaken the check. |
| **2** | **REFUSED / VACUOUS** — nothing was proven | Name which one fired (below). Never call a 2 "mostly passing", "verified with a caveat", or round it to green. |

Exit 2 has six distinct causes; the gate prints which:

1. `negative control is VACUOUS BEFORE IT RAN` — the sentinel already exists in the worktree, so the planted citation would resolve and the control would pass. The gate refuses pre-emptively. Cause: work that created the very path its own control expected to be missing (the control text is visible to whoever wrote the code).
2. `negative control did not restore the tree` — the control is broken; the pre-control diff is parked as `lane-<id>.patch`.
3. `BASE TREE LEAKAGE DETECTED` — the control wrote outside the worktree; diff parked.
4. `negative control PASSED => VACUOUS LANE` — the check cannot fail. This is the defect this whole skill exists to catch.
5. `negative failed but did NOT name the planted violation` — it failed for some *other* reason, so it proves nothing about your plant.
6. `mutation gate: FAIL` — surviving mutants: the tests cannot fail.

## 5. Point at the artifacts

Always written into `--run`: `pos-<id>.log`, `neg-<id>.log`. Written when applicable: `mut-<id>.log`, `full-<id>.log`, and `lane-<id>.patch` — the pre-control diff, parked when the tree was not restored or leakage was found. Quote the line that proves the verdict; do not paraphrase.

## 6. Naming the plant

Prefer an **organic** expect string: mutate real code and match the tool's own error (a compiler message, an assertion name). Only where the deliverable has no natural mutation — a document, a config — plant a sentinel, and then use exactly `DEVLOOP-PLANTED-<LANE_ID>`, one unique sentinel per lane. A sentinel shared between lanes means either lane's output satisfies the other's gate; an expect string that also appears in the fixture's own filename passes whether or not the plant landed (a self-certifying predicate). Convention enforced by `tests/test_planted_naming.py`.

## 7. Document branch — prose deliverables

When the deliverable is a measurement rather than code, the gate is:

```sh
python3 $S/check_finding.py <repo_root> <findings_file>
```

Exit 0 requires all of: the seven sections `## VERDICT`, `## WHAT IS ACTUALLY TRUE`, `## NUMBERS`, `## PROPOSED FIX`, `## FILES TO CHANGE`, `## NEGATIVE CONTROL`, `## UNVERIFIED`; a verdict drawn from `CONFIRMED | PARTLY_CONFIRMED | REFUTED | STALE`; at least 3 `path:line` citations; and **every** citation resolving against the tree (the file exists and has at least that many lines). Non-zero names exactly which citation did not resolve. "The file exists" is not a measurement.

## 8. Do not cite these

`scripts/verify_harness.py` is an importable library (`run_two_sided_test(test_cmd, mutator, reverter, needle)` taking Python callables); its `__main__` only prints a readiness line and nothing imports it. `scripts/contracts.py` is the same shape. Neither is a runnable gate. Telling an operator to run them would be the overclaiming defect this repo keeps hitting — a description that promises more than the code does is itself a bug.

Return: the exit code, its exact meaning from the table, the artifact paths, and — on 0 — the one line of `neg-<id>.log` that shows the check failing for the planted reason.
