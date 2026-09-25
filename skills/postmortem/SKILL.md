---
name: postmortem
description: Diagnose a lane that did not finish, from its run directory - separate a denied/empty harness turn, a lost worker with no receipt, an ownership stray, a vacuous gate, and a genuine defect, because each has a different remedy and only the last one is a code bug. Reads the receipts already on disk; runs nothing and never re-dispatches. Use when a lane comes back partial, blocked, budget, halted or with no report at all, or when a run claimed success and produced nothing.
argument-hint: "<lane-id> [run-dir]"
allowed-tools: Read, Grep, Glob, Bash
---
# /postmortem — why the lane did not finish (SKILL §6, §7, §11)

_Paths: `${CLAUDE_SKILL_DIR}/../dev-loop/scripts/` resolves in Claude Code; in other harnesses use `<skills dir>/dev-loop/scripts/` (the shims in `shims/<harness>/` already do)._ Below, `$S` = that scripts directory. Run-directory contract: `references/run-directory.md`. Class table: `references/postmortem.md`.

`$ARGUMENTS` is `<lane-id>` and optionally a run directory. Empty run dir ⇒ the newest `.devloop/run-*` (`ls -1d .devloop/run-* | tail -1`).

**A lane that did not finish is not automatically a broken codebase.** Four of the five causes below are infrastructure, and "fix the code" is the wrong remedy for all four. Guessing which one fired — and writing a confident diagnosis on top of the guess — is exactly the overclaiming defect §7 names.

**This command reads receipts. It does not run the lane's commands and it NEVER re-dispatches.** Re-run a check only when the worktree still exists *and* the operator asks for it.

## Classify in this order, stop at the first hit, name the class in the output

### 1. DENIED — the harness refused the tool calls
```sh
python3 $S/adapters.py denials <RUN>/worker-<id>.log      # or the envelope file
```
This is the headless-green trap: a fully-denied run can exit `0` with status `SUCCESS` and an empty response, and `cmd_denials` exists precisely because the exit code lies. Exit `0` = envelope clean. Exit `3` = **two different things — read the message, never the code alone**:
- `denials: harness denied N tool call(s)` / `the harness produced an EMPTY response` ⇒ genuinely denied or vacuous. **Remedy is permissions/allowlist, not code.**
- `no harness result envelope found in <file>` ⇒ the file carried no envelope at all. That is *absence of evidence*, not evidence of denial — a plain text log produces it. Say so and move to class 2.

An envelope is recognised only when it carries `permission_denials` / `denied_actions`, or `is_error`, or `status` **and** `usage` (agy), or `result` **and** `num_turns` (claude-code). Control: `tests/test_envelope_denials.py`.

### 2. LOST / NO RECEIPT — the worker never returned
`worker-<id>.exit` is the shell's receipt (`devloop.sh` appends `; echo $? > worker-<id>.exit`). Absent ⇒ nothing returned; `125` ⇒ never started / no receipt recovered; `124` ⇒ outer timeout.
```sh
python3 $S/job.py status --root <RUN>/jobs --id <id> --json
```
States: `absent | running | done | lost | forged`. Exit `0` all done · `2` not all done · `3` `lost`/`forged`. `lost` = no receipt and the pid is gone; **live grandchildren may remain**, and cleanup is by session id, never process group. `forged` = a receipt the wrapper did not write, or pid reuse — untrusted, not done.

**Remedy (SKILL §11): assume half-finished edits from every lane that did not report.** Inspect `lane-<id>.patch`, park it, restore, re-dispatch the lane — never commit its edits without its report. An exhausted budget or a timeout is `partial`, never `done`.

### 3. OWNERSHIP STRAY — the lane wrote outside its file set
```sh
python3 $S/adapters.py owned --lane <RUN>/lane-<id>.json --wt <worktree>     # 0 ok · 1 violation + path list
python3 $S/adapters.py base-audit --root . --before <RUN>/base-tree-before.json   # 0 ok · 6 stray · 64 bad args
```
`owned` reads `git status --porcelain -uall` in `--wt`, so the **worktree must still exist**, and *any* file sitting in it counts as a changed path — keep the lane JSON in the run directory, never copy it into the worktree, or the audit indicts itself. `base-audit` always allows `.devloop/`, `.git/`, `AGENTS.md`, `TASKS.md` and the worktree root.

**Remedy: park the diff, re-scope `owned_paths`, do not merge.** Controls: `tests/test_base_tree_guard.py`, `tests/test_lane_isolation_leakage.py`.

### 4. VACUOUS GATE — nothing was proven
Gate exit `2` recorded in the log, or re-run `python3 $S/adapters.py gate --lane <RUN>/lane-<id>.json --wt <worktree> --run <RUNDIR>` when the worktree survives. Then read `neg-<id>.log` and name which of the six fired: the sentinel already existed before the control ran · the control did not restore the tree · base-tree leakage · **the negative control PASSED** · it failed but did not match `negative_expect` · surviving mutants.

**Remedy: fix the CONTROL, not the code.** A check that cannot fail passes identically on correct and on broken code; a lane whose negative control passes is vacuous and must not merge. Never round a `2` to "mostly passing".

### 5. REAL DEFECT — and only now
Reachable only when 1–4 are clean and the **positive** command failed (gate exit `1`, honest red). Hand the failing command to `/triage` verbatim. Fix the cause, not the symptom (§8); do not weaken the check.

## Output

Name the class, the deciding command and its exact exit code, the line of the artefact that proves it, whether `lane-<id>.patch` exists (and that the work in it is parked, not lost), and **one** next action. When the evidence does not decide between two classes, say which two and what artefact would settle it — an honest "undetermined" beats a confident wrong class.

## Not /triage, and not /watch

- `/triage` (`$S/triage.py`) takes a failing **command** and reruns it N times to separate flake from deterministic bug. It cannot see denials, vacuity, ownership violations or a missing receipt — there is no command to rerun for any of them.
- `/watch` reports the state of a **whole run**, every lane side by side, while it is in flight.
- `/postmortem` takes one **lane** that already came back not-done, runs nothing by default, and names the cause.
