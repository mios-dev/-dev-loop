---
name: watch
description: Report the state of a dev-loop run from its run directory — per-lane model report, the shell-written exit receipt, job liveness and log tails — and name the anomalies (lost jobs, missing receipts, lanes with no report). Read-only; it never dispatches and never merges. Use when a multi-lane run is in flight, when a run's launching turn already ended, or before deciding whether a run is finished.
argument-hint: "[run-dir]"
allowed-tools: Read, Grep, Glob, Bash
---
# /watch — read the state of a dev-loop run

_Paths: `${CLAUDE_SKILL_DIR}/../dev-loop/scripts/` resolves in Claude Code; in other harnesses use
`<skills dir>/dev-loop/scripts/`. Run-directory contract: `references/run-directory.md`; the
doctrine behind this command: `references/watch.md`._

`$ARGUMENTS` is a run directory. Empty ⇒ the newest `.devloop/run-*` (`ls -1d .devloop/run-* | tail -1`).
Nothing here writes, dispatches, merges, or kills. If the run needs an action, say so and stop.

## The rule this command exists to enforce

**Completion is an artefact the shell writes, never a sentence the model says.**
`report-<id>.json` holds the *model's claim*. `worker-<id>.exit` holds the *shell's receipt* —
`devloop.sh` appends `; echo $? > worker-<id>.exit` to the lane command, so the receipt exists
only if the command actually returned. Never call a lane done when the receipt is absent or
non-zero, however confident the report reads. This is `job.py`'s founding doctrine, adopted after
four measured incidents in which a turn-bound agent reported work it had only started.

## Procedure

1. **Enumerate lanes** — one id per `lane-<id>.json` in the run dir.
2. **Three sources per lane, side by side, never collapsed into one verdict:**
   - `report-<id>.json` → `.status` — the model's claim: `done | partial | blocked | converged_stuck | budget | halted`. Missing file ⇒ **NO REPORT**.
   - `worker-<id>.exit` → the shell's receipt. `0` = returned clean · `124` = outer timeout · `125` = never started / no receipt recovered · absent = nothing returned yet.
   - `worker-<id>.log` → tail the last ~20 lines for the actual evidence.
3. **Job liveness** (jobs live at `<RUN>/jobs`):
   `python3 <skills dir>/dev-loop/scripts/job.py status --root <RUN>/jobs --json`
   Surface its vocabulary literally: `absent | running | done | lost | forged`.
   Exit codes: `0` ok · `2` job failed or not done · `3` lost/forged.
   Call out **`lost`** explicitly — no receipt and the pid is gone: the wrapper was hard-killed or
   the box rebooted, and **live grandchildren may remain**. Cleanup is by *session id*, never by
   process group (`kill -- -<pid>` reports "No such process" while descendants `timeout` moved into
   a new process group are still alive). Report it; do not kill anything from this command.
   **`forged`** = a receipt the wrapper did not write, or pid reuse — treat as untrusted, not done.
4. **Bounded waiting, only when asked, never unbounded:**
   `python3 <skills dir>/dev-loop/scripts/job.py wait --root <RUN>/jobs --id ID --budget 300 --interval 5`
   (`--id` takes one job id; repeat the call per lane, or wait on the lane that gates the rest.)
   An exhausted budget is **partial**, never done (SKILL §12: budget ⇒ stop and report the exact
   remaining work). Do not poll in a loop of your own devising.
5. **AGY-only step detail** — *this branch applies to Antigravity-hosted runs and no other harness.*
   `agy_monitor.py` reads an NDJSON stream written by `agy_session.py --events-out` (default
   `.devloop/native/session-events.ndjson`, or `$AGY_HOST_EVENTS`). If that file exists:
   `python3 <skills dir>/dev-loop/scripts/agy_monitor.py <stream> --once`
   Honour its exit **2** — it fires on verdicts `vacuous`, `no_result`, `stalled`: a run that
   claimed a result while doing nothing, or that announced a background wait whose work died with
   the turn. `in_progress` is not a failure. Measured caveat: `--once` **also** exits 2 with verdict
   `no_stream` when the file does not exist, so read the printed `verdict`, never the exit code
   alone — only run it once you have confirmed the stream exists. For a Claude Code, Codex, Copilot, Cursor or OpenCode
   host there is no such stream and therefore **no step-level view** — say that plainly rather than
   implying one exists.

## Output

One line per lane, then the anomalies:

```
LANE   report      receipt  job      age    evidence
L1     done        0        done     14m    pos ok / neg failed-as-expected
L2     done        (none)   running  14m    still executing — NOT done
L3     (no report) 125      lost     14m    never started; check for live grandchildren
```

Then, explicitly: lanes whose report says `done` but whose receipt is absent or non-zero (the
contradiction this command exists to catch), `lost`/`forged` jobs, lanes with no report, stalls,
and the AGY verdict when a stream existed. Close with the one next action — wait, inspect a named
log, or escalate — and stop.

## Two-sided verification still applies to the gate logs

A lane is gated by a positive control **and** a negative control that proves the check can fail
(SKILL §6). When reporting a lane, cite both: `pos-<id>.log` must show the suite passing, and
`neg-<id>.log` must show the seeded defect being *caught* with the expected signature. A lane whose
`neg-` log is missing or shows a pass has no evidence its checks can fail — report it as
unverified, not done, whatever `report-<id>.json` claims.
