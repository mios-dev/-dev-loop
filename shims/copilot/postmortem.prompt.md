---
name: postmortem
description: Diagnose a lane that did not finish — denied tool calls, a lost worker, an ownership stray, a vacuous gate, or a genuine defect
version: 1.0.0
---

# GitHub Copilot /postmortem Workflow

A lane that came back not-done has five different causes with five different remedies, and only the last is a code bug. Guessing between them is itself the overclaiming defect. **Read the receipts already on disk. Run nothing by default. NEVER re-dispatch.** Re-run a check only when the worktree still exists *and* the operator asks.

`$S` = the dev-loop `scripts/` directory. `<RUN>` = the run dir (`${input:run-dir}`, or the newest `.devloop/run-*`). Classify in order and stop at the first hit.

1. **DENIED.** `python3 $S/adapters.py denials <RUN>/worker-<id>.log` — exit `0` clean, exit `3` hit. A fully-denied headless run can exit `0` with status `SUCCESS` and an empty response; the exit code lies, which is why this check exists. Exit `3` means two different things — **read the message**: `denied N tool call(s)` / `EMPTY response` ⇒ genuinely denied, remedy is **permissions/allowlist, not code**; `no harness result envelope found` ⇒ the file held no envelope at all (a plain text log does this) — absence of evidence, so fall through to 2. Envelopes are recognised by `permission_denials`/`denied_actions`, `is_error`, `status`+`usage`, or `result`+`num_turns`. Control: `tests/test_envelope_denials.py`.
2. **LOST / NO RECEIPT.** `worker-<id>.exit`: absent = nothing returned · `125` = never started · `124` = outer timeout. `python3 $S/job.py status --root <RUN>/jobs --id <id> --json` → `absent | running | done | lost | forged`; exit `0` all done · `2` not all done · `3` lost/forged. `lost` may leave live grandchildren (kill by session id, never process group); `forged` is untrusted, not done. Remedy: assume half-finished edits from every lane that did not report — inspect `lane-<id>.patch`, park, restore, re-dispatch. Exhausted budget or timeout is **partial**, never done.
3. **OWNERSHIP STRAY.** `python3 $S/adapters.py owned --lane <RUN>/lane-<id>.json --wt <worktree>` — `0` ok, `1` violation + paths. It reads `git status --porcelain -uall` in `--wt`, so the worktree must still exist and any file sitting there counts as changed — keep the lane JSON in the run dir or the audit indicts itself. `python3 $S/adapters.py base-audit --root . --before <RUN>/base-tree-before.json` — `0` ok, `6` stray, `64` bad args; `.devloop/`, `.git/`, `AGENTS.md`, `TASKS.md` and the worktree root are always allowed. Remedy: park the diff, re-scope `owned_paths`, **do not merge**. Controls: `tests/test_base_tree_guard.py`, `tests/test_lane_isolation_leakage.py`.
4. **VACUOUS GATE.** Gate exit `2` in the log, or re-run `python3 $S/adapters.py gate --lane <RUN>/lane-<id>.json --wt <worktree> --run <RUNDIR>`. Read `neg-<id>.log` and name which of six fired: sentinel pre-existed · tree not restored · base-tree leakage · **the negative control PASSED** · failed but did not match `negative_expect` · surviving mutants. Remedy: **fix the CONTROL, not the code** — a check that cannot fail passes identically on correct and broken code. Never round a `2` to "mostly passing".
5. **REAL DEFECT** — only when 1–4 are clean and the *positive* command failed (gate exit `1`). Only then hand that command verbatim to `/triage`.

Report: the class, the deciding command and its exact exit code, the artefact line proving it, whether `lane-<id>.patch` exists, and one next action. If the evidence does not decide, name both candidate classes and the artefact that would settle it.

**Not `/triage`, not `/watch`.** `/triage` (`$S/triage.py`) reruns a failing **command** N times to separate flake from deterministic bug — it cannot see denials, vacuity, ownership violations or a missing receipt, because none of them has a command to rerun. `/watch` reports a whole **run** in flight. `/postmortem` takes one **lane** that already came back not-done and names the cause.
