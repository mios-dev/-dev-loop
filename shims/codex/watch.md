# /watch Prompt for OpenAI Codex

Report the state of a dev-loop run directory. **Read-only**: never dispatch a lane, never merge,
never kill a job. Argument is a run dir; empty means the newest `.devloop/run-*`.

1. **Enumerate lanes** — one id per `lane-<id>.json`.
2. **Report three sources per lane, side by side:**
   - `report-<id>.json` `.status` — the MODEL's claim (`done|partial|blocked|converged_stuck|budget|halted`).
   - `worker-<id>.exit` — the SHELL's receipt, appended by `devloop.sh` as `; echo $? > worker-<id>.exit`.
     `0` clean · `124` timeout · `125` never started / no receipt recovered · absent = nothing returned.
   - `worker-<id>.log` — tail for evidence.
   **Never call a lane done from the report when the receipt is absent or non-zero.** Completion is
   an artefact the shell writes, never a sentence the model says.
3. **Job liveness:** `python3 <skills dir>/dev-loop/scripts/job.py status --root <RUN>/jobs --json`.
   Vocabulary, used literally: `absent | running | done | lost | forged` (exit 2 = failed/not done,
   3 = lost/forged). `lost` means SIGKILLed wrapper, no receipt, possibly live grandchildren; note
   that kill goes by session id, not process group.
4. **Bounded waiting only, on request:** `job.py wait --root <RUN>/jobs --id ID --budget N
   --interval N`. Never an unbounded poll. An exhausted budget is PARTIAL, never done.
5. **Antigravity-hosted runs only:** if an NDJSON stream from `agy_session.py --events-out` exists
   (`.devloop/native/session-events.ndjson` or `$AGY_HOST_EVENTS`), run
   `python3 <skills dir>/dev-loop/scripts/agy_monitor.py <stream> --once` and honour exit 2
   (`vacuous` / `no_result` / `stalled`); it also exits 2 with verdict `no_stream` when the file is
   absent, so read the printed verdict, not the code alone. A Codex lane writes no such stream —
   there is no step-level view for it; say so.
6. **Output:** one line per lane (id, model status, receipt, job state, age), then anomalies —
   `done` claims without a clean receipt, `lost`/`forged` jobs, lanes with no report, stalls.
   Two-sided verification still governs: `pos-<id>.log` must pass and `neg-<id>.log` must show the
   seeded defect caught. A missing or passing negative control means unverified, not done.
