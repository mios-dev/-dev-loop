# Failed-Lane Postmortem Specification (`/postmortem`)

A lane that comes back not-done is not automatically a broken codebase. Four of the five causes
below are infrastructure, and "fix the code" is the wrong remedy for all four. No single tool
distinguishes them, so an agent that skips the classification guesses — and a confident diagnosis
written on top of a guess is exactly the overclaiming defect SKILL §7 names.

`/postmortem` is the classifier. It reads the receipts the run already wrote
(`references/run-directory.md` is the on-disk contract), runs nothing by default, and **never
re-dispatches**. A check is re-run only when the lane's worktree still exists *and* the operator
asks for it.

---

## 1. The five classes

Classify in this order and stop at the first hit. The order is not arbitrary: a denied turn
produces a missing receipt, a missing receipt produces an unaudited worktree, and an unaudited
worktree produces a gate result nobody can trust — diagnosing bottom-up attributes an
infrastructure failure to the code.

| # | Class | Symptom | Deciding command | Exit | Remedy |
|---|---|---|---|---|---|
| 1 | **DENIED** | run "succeeded" but produced nothing; log shows auto-denial notices | `adapters.py denials <RUN>/worker-<id>.log` | `0` clean · `3` denied, empty response, **or no envelope found** | permissions / allowlist — **not code** |
| 2 | **LOST / NO RECEIPT** | `worker-<id>.exit` absent, `124` or `125`; job `lost`/`forged` | `job.py status --root <RUN>/jobs --id <id> --json` | `0` all done · `2` not all done · `3` lost/forged | park `lane-<id>.patch`, restore, re-dispatch |
| 3 | **OWNERSHIP STRAY** | the lane wrote outside `owned_paths`, or touched the base tree | `adapters.py owned --lane <RUN>/lane-<id>.json --wt <wt>` · `adapters.py base-audit --root . --before <RUN>/base-tree-before.json` | `1` violation · `6` base-tree leakage (`64` bad args) | park the diff, re-scope `owned_paths`, **do not merge** |
| 4 | **VACUOUS GATE** | gate refused; nothing was proven | `adapters.py gate --lane … --wt … --run …` | `2` | fix the **control**, not the code |
| 5 | **REAL DEFECT** | 1–4 clean and the *positive* command failed | the same gate | `1` (honest red) | hand the failing command to `/triage` |

---

## 2. Class 1 — DENIED, the headless-green trap

`cmd_denials` exists because **the exit code lies**: a fully-denied headless run can exit `0` with
status `SUCCESS` and an empty response. A host that trusts the exit code records a success for a
turn that did nothing.

Exit `3` is overloaded and the message, not the code, decides:

| Printed | Means | Next |
|---|---|---|
| `denials: harness denied N tool call(s) (…)` | tool calls were auto-denied | class 1 confirmed — fix permissions |
| `denials: the harness produced an EMPTY response over N turn(s)` | it reported success while doing nothing | class 1 confirmed |
| `no harness result envelope found in <file>` | the file carried **no envelope at all** | *absence of evidence*, not evidence of denial — say so and fall through to class 2 |

A text-only worker log produces the third line. An envelope is recognised only when some JSON
object in the stream carries `permission_denials` or `denied_actions`, or `is_error`, or `status`
**and** `usage` (agy), or `result` **and** `num_turns` (claude-code). The scan is by brace balance
rather than `json.loads`, so a stderr notice sharing the stream does not hide the envelope.
Control: `tests/test_envelope_denials.py`.

---

## 3. Class 2 — LOST / NO RECEIPT

**Completion is an artefact the shell writes, never a sentence the model says.** `devloop.sh`
appends `; echo $? > worker-<id>.exit` to the lane command, so the receipt exists only if the
command actually returned.

| `worker-<id>.exit` | Meaning |
|---|---|
| `0` | returned clean |
| `124` | outer wall-clock timeout |
| `125` | never started / no receipt recovered |
| *absent* | nothing has returned — "unknown", not "running" and not "done" |

`job.py status` derives its state from the filesystem and `/proc`, never from anything an agent
wrote: `absent | running | done | lost | forged`, with exit `0` (all done), `2` (not all done),
`3` (`lost` or `forged`). `lost` means no receipt and the pid is gone — the wrapper was
hard-killed or the box rebooted, and **live grandchildren may remain**; cleanup is by *session id*,
never by process group, because `timeout` moves its child into a new process group that still
shares the session. `forged` means a receipt the wrapper did not write, or pid reuse: untrusted.

Remedy is SKILL §11: assume half-finished edits from every lane that did not report. Inspect the
parked diff, restore, re-dispatch. **Never commit a lane's edits without its report.** An
exhausted budget or a timeout is `partial`, never `done`.

---

## 4. Class 3 — OWNERSHIP STRAY

`owned` compares `git status --porcelain --untracked-files=all` in the worktree against the lane's
`owned_paths`, exits `1`, and lists every path outside the set. Two consequences worth stating:
the **worktree must still exist** for this check to mean anything, and *any* file sitting in the
worktree counts as a changed path — copy the lane JSON into the worktree and the audit indicts
itself. Keep it in the run directory, which is git-excluded.

`base-audit` compares the base tree against `base-tree-before.json` and exits `6` on stray edits,
`64` on bad arguments. `.devloop/`, `.git/`, `AGENTS.md`, `TASKS.md`, the worktree root and the
snapshot file itself are always allowed.

A stray is not merged and not quietly reverted: park the diff, re-scope `owned_paths`, and say
which lane crossed into whose files. Controls: `tests/test_base_tree_guard.py`,
`tests/test_lane_isolation_leakage.py`.

---

## 5. Class 4 — VACUOUS GATE

A check that cannot fail passes identically on correct and on broken code, so a lane whose
negative control *passes* has proved nothing and must not merge. Gate exit `2` is
**REFUSED / VACUOUS**, with six distinct causes the gate prints:

1. the sentinel already existed in the worktree before the control ran (refused pre-emptively);
2. the negative control did not restore the tree — the control is broken, diff parked;
3. base-tree leakage — the control wrote outside the worktree, diff parked;
4. the negative control **PASSED** — the check cannot fail;
5. it failed but did not match `negative_expect` — it failed for some *other* reason, proving
   nothing about the plant;
6. surviving mutants.

All six are defects in the **control**, not in the code under test. Fixing the code cannot clear
any of them, and no exit `2` is ever reported as "mostly passing" or rounded to green.

---

## 6. Class 5 — REAL DEFECT

Reachable only when 1–4 are clean and `positive_cmd` (or `full_gate_cmd`) failed: gate exit `1`,
honest red. That, and only that, is a code bug. Hand the failing command verbatim to `/triage`,
which reruns it to separate flake from deterministic bug. Fix the cause, not the symptom
(SKILL §8); never weaken the check to clear the red.

---

## 7. Boundaries

| Command | Input | Runs things? | Sees |
|---|---|---|---|
| `/triage` | a failing **command** | yes — N reruns | flake vs deterministic bug, phantom environment failures |
| `/watch` | a **run directory** | no | every lane's report, receipt, job state, side by side, in flight |
| `/postmortem` | one **lane** that came back not-done | no, by default | which of the five classes fired, and the remedy |

`/triage` structurally cannot see classes 1–4: a denial, a missing receipt, an ownership stray and
a vacuous gate have no command to rerun. `/watch` reports *that* a lane is anomalous;
`/postmortem` says *why*.

---

## 8. Reporting rule

Name the class, the deciding command, its exact exit code, the line of the artefact that proves
it, whether `lane-<id>.patch` exists (the work is parked, not lost), and **one** next action.

Where the evidence does not decide between two classes, name both and the artefact that would
settle it. An honest "undetermined" is a correct result; a confident wrong class is the defect
this command exists to prevent.
