# Antigravity Workflow: /workflows:postmortem

Identifier: `postmortem`
Purpose: Diagnose a lane that did not finish, from its run directory — denied tool calls, a lost worker, an ownership stray, a vacuous gate, or a genuine defect
Input: `[lane-id] [run-dir]`

# /postmortem: Failed-Lane Diagnosis

Target: `the workflow input` — a lane id, and optionally a run directory. Empty run dir ⇒ the newest `.devloop/run-*` (`ls -1d .devloop/run-* | tail -1`).

Below, `$S` = the dev-loop `scripts/` directory (`<skills dir>/dev-loop/scripts/`).

A lane that came back not-done has five genuinely different causes with five different remedies, and only the last is a code bug. Guessing between them and writing a confident diagnosis on the guess is the overclaiming defect itself. **Read the receipts that already exist. Run nothing by default. NEVER re-dispatch.** Re-run a check only when the worktree still exists *and* the operator asks.

## Classify in this order — stop at the first hit, and name the class

1. **DENIED — the harness refused the tool calls.**
   `python3 $S/adapters.py denials <RUN>/worker-<id>.log` (or the envelope file; `-` reads stdin).
   The headless-green trap: a fully-denied run can exit `0` with status `SUCCESS` and an empty response — the exit code lies, which is why this check exists. Exit `0` = envelope clean. Exit `3` means **one of two different things; read the message, never the code alone**: `harness denied N tool call(s)` or `produced an EMPTY response` ⇒ genuinely denied/vacuous, and the remedy is **permissions/allowlist, not code**; `no harness result envelope found in <file>` ⇒ the file carried no envelope at all (a plain text log does this) — absence of evidence, not evidence of denial, so say so and go to 2. An envelope is recognised only when it carries `permission_denials`/`denied_actions`, or `is_error`, or `status`+`usage` (agy), or `result`+`num_turns` (claude-code). Control: `tests/test_envelope_denials.py`.

2. **LOST / NO RECEIPT — the worker never returned.**
   `worker-<id>.exit` is the shell's receipt: absent ⇒ nothing returned · `125` ⇒ never started / no receipt recovered · `124` ⇒ outer timeout.
   `python3 $S/job.py status --root <RUN>/jobs --id <id> --json` → state `absent | running | done | lost | forged`; exit `0` all done · `2` not all done · `3` lost/forged. `lost` = no receipt and the pid is gone, and **live grandchildren may remain** (cleanup is by session id, never process group). `forged` = a receipt the wrapper did not write, or pid reuse — untrusted, not done.
   Remedy (SKILL §11): assume half-finished edits from every lane that did not report — inspect `lane-<id>.patch`, park it, restore, re-dispatch. An exhausted budget or a timeout is **partial**, never done.

3. **OWNERSHIP STRAY — the lane wrote outside its file set.**
   `python3 $S/adapters.py owned --lane <RUN>/lane-<id>.json --wt <worktree>` — exit `0` ok, `1` violation plus the offending paths. It reads `git status --porcelain -uall` inside `--wt`, so the worktree must still exist, and *any* file sitting there counts as changed — keep the lane JSON in the run directory, never copy it into the worktree, or the audit indicts itself.
   `python3 $S/adapters.py base-audit --root . --before <RUN>/base-tree-before.json` — exit `0` ok, `6` stray edits to the base tree, `64` bad arguments. `.devloop/`, `.git/`, `AGENTS.md`, `TASKS.md` and the worktree root are always allowed.
   Remedy: park the diff, re-scope `owned_paths`, **do not merge**. Controls: `tests/test_base_tree_guard.py`, `tests/test_lane_isolation_leakage.py`.

4. **VACUOUS GATE — nothing was proven.**
   Gate exit `2` recorded in the log, or re-run `python3 $S/adapters.py gate --lane <RUN>/lane-<id>.json --wt <worktree> --run <RUNDIR>` when the worktree survives. Read `neg-<id>.log` and name which of the six fired: the sentinel already existed before the control ran · the control did not restore the tree · base-tree leakage · **the negative control PASSED** · it failed but did not match `negative_expect` · surviving mutants.
   Remedy: **fix the CONTROL, not the code.** A check that cannot fail passes identically on correct and on broken code; a lane whose negative control passes is vacuous and must not merge. Never round a `2` to "mostly passing".

5. **REAL DEFECT — only when 1–4 are clean** and the *positive* command failed (gate exit `1`, honest red). Only then hand the failing command, verbatim, to `/triage`.

## Output

The class, the deciding command and its exact exit code, the artefact line that proves it, whether `lane-<id>.patch` exists (the work is parked, not lost), and **one** next action. Where the evidence does not decide between two classes, say which two and what artefact would settle it — an honest "undetermined" beats a confident wrong class.

## Not /triage, and not /watch

`/triage` (`$S/triage.py`) takes a failing **command** and reruns it N times to separate flake from deterministic bug; it structurally cannot see denials, vacuity, ownership violations or a missing receipt, because none of those has a command to rerun. `/watch` reports a **whole run**, all lanes side by side, while it is in flight. `/postmortem` takes one **lane** that already came back not-done, runs nothing by default, and names the cause.
