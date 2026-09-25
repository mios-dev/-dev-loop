# Antigravity Workflow: /workflows:watch

Identifier: `watch`
Purpose: Read-only status of a dev-loop run directory. Never dispatches, merges, or kills.

Input: a run dir; empty means the newest `.devloop/run-*`.

1. **Phase 1: Enumerate:** one lane id per `lane-<id>.json` in the run dir.
2. **Phase 2: Three sources per lane:** `report-<id>.json` `.status` (the MODEL's claim),
   `worker-<id>.exit` (the SHELL's receipt — `0` clean, `124` timeout, `125` never started,
   absent = nothing returned), and the tail of `worker-<id>.log`.
   **Rule: a lane is never done from the report alone when the receipt is absent or non-zero.**
3. **Phase 3: Liveness:** `python3 <skills dir>/dev-loop/scripts/job.py status --root <RUN>/jobs --json`.
   States are `absent | running | done | lost | forged`; exit 2 = failed/not done, 3 = lost/forged.
   Report `lost` explicitly: no receipt, pid gone, possible live grandchildren — cleanup goes by
   session id, not process group.
4. **Phase 4: Bounded wait, only on request:** `job.py wait --root <RUN>/jobs --id ID --budget N
   --interval N`. Never unbounded. An exhausted budget is PARTIAL.
5. **Phase 5 (native AGY runs only): step detail.** `agy_host.sh` tees the session stream to
   `.devloop/native/session-events.ndjson` (or `$AGY_HOST_EVENTS`). Run
   `python3 <skills dir>/dev-loop/scripts/agy_monitor.py <stream> --once` and honour exit 2
   (verdicts `vacuous` / `no_result` / `stalled`); it also exits 2 with verdict `no_stream` when
   the file is absent, so read the printed verdict, not the code alone. Lanes run under other
   harnesses write no such stream and get no step detail — state that instead of implying coverage.
6. **Phase 6: Report:** one line per lane (id, status, receipt, job state, age), then the anomalies.
   Cite `pos-<id>.log` and `neg-<id>.log` together — a missing or passing negative control means
   unverified, not done.
