---
description: Report the state of a dev-loop run from its run directory — per-lane reports, shell-written exit receipts and job liveness (read-only)
argument-hint: [run-dir]
allowed-tools: Read, Glob, Grep, Bash
---
Load the `watch` skill (SKILL.md — project `.claude/skills/watch/` or `~/.claude/skills/watch/`) and report the state of this run directory:

$ARGUMENTS

Empty argument means the newest run: `ls -1d .devloop/run-* | tail -1`.
**Read-only.** Never dispatch a lane, never merge, never kill a job. If the run needs an action, name it and stop.

Scripts below live at `${CLAUDE_PLUGIN_ROOT}/skills/dev-loop/scripts/` under a plugin install, or `<skills dir>/dev-loop/scripts/` otherwise.

1. **Lanes** — one id per `lane-<id>.json` in the run dir.
2. **Three sources per lane, reported side by side:**
   - `report-<id>.json` `.status` — the MODEL's claim (`done|partial|blocked|converged_stuck|budget|halted`).
   - `worker-<id>.exit` — the SHELL's receipt (`devloop.sh` appends `; echo $? > worker-<id>.exit`). `0` clean · `124` timeout · `125` never started / no receipt · absent = nothing returned yet.
   - `worker-<id>.log` — tail for the actual evidence.
   **Core rule: never call a lane done from `report-<id>.json` when `worker-<id>.exit` is absent or non-zero.** Completion is an artefact the shell writes, never a sentence the model says.
3. **Job liveness:** `python3 <scripts>/job.py status --root <RUN>/jobs --json` (jobs live at `<RUN>/jobs`). Report its vocabulary literally: `absent | running | done | lost | forged`; exit `2` = failed/not done, `3` = lost/forged. Flag **`lost`** explicitly — the wrapper was SIGKILLed, left no receipt, and may have live grandchildren; cleanup goes by session id, not process group.
4. **Bounded waiting only, and only if asked:** `python3 <scripts>/job.py wait --root <RUN>/jobs --id ID --budget N --interval N` (`--id` takes one id). Never an unbounded poll. An exhausted budget is PARTIAL, never done (§§11–12).
5. **ANTIGRAVITY-HOSTED RUNS ONLY:** if an NDJSON event stream written by `agy_session.py --events-out` exists (default `.devloop/native/session-events.ndjson`, or `$AGY_HOST_EVENTS`), run `python3 <scripts>/agy_monitor.py <stream> --once` and honour its exit 2 — verdicts `vacuous` / `no_result` / `stalled`, a run that claimed a result while doing nothing. It also exits 2 with verdict `no_stream` when the file is absent, so read the printed `verdict`, not the exit code alone. No other harness writes that stream, so a Claude Code, Codex, Copilot, Cursor or OpenCode lane has no step-level view; say so rather than implying one.
6. **Output:** one line per lane (id, model status, receipt, job state, age), then the anomalies — `done` claims without a clean receipt, `lost`/`forged` jobs, lanes with no report (diff parked at `lane-<id>.patch`), stalls. Cite `pos-<id>.log` and `neg-<id>.log` together: a negative control that never ran, or that passed, means unverified, not done (§6).

Run-directory contract: `skills/dev-loop/references/run-directory.md`. Doctrine: `references/watch.md`.
Newest run for orientation: !`ls -1d .devloop/run-* 2>/dev/null | tail -1`
