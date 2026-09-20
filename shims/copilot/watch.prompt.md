---
name: watch
description: Read-only status of a dev-loop run directory — per-lane reports, shell-written exit receipts, job liveness
version: 2.0.0
---

# GitHub Copilot /watch Workflow

Report the state of the run directory in `${input}` (empty = newest `.devloop/run-*`).
**Read-only**: never dispatch a lane, never merge, never kill a job.

- **Lanes:** one id per `lane-<id>.json`.
- **Three sources per lane, side by side:** `report-<id>.json` `.status` (the MODEL's claim),
  `worker-<id>.exit` (the SHELL's receipt — `0` clean, `124` timeout, `125` never started, absent =
  nothing returned) and the tail of `worker-<id>.log`.
  **Never call a lane done from the report when the receipt is absent or non-zero.**
- **Liveness:** `python3 <skills dir>/dev-loop/scripts/job.py status --root <RUN>/jobs --json` →
  `absent | running | done | lost | forged` (exit 2 = failed/not done, 3 = lost/forged). Flag `lost`
  explicitly: no receipt, pid gone, possible live grandchildren; kill by session id, not process group.
- **Bounded waiting only, on request:** `job.py wait --root <RUN>/jobs --id ID --budget N --interval N`.
  An exhausted budget is PARTIAL, never done.
- **Antigravity-hosted runs only:** when an NDJSON stream from `agy_session.py --events-out` exists,
  `python3 <skills dir>/dev-loop/scripts/agy_monitor.py <stream> --once`, honouring exit 2
  (`vacuous` / `no_result` / `stalled`); it also exits 2 with verdict `no_stream` when the file is
  absent, so read the printed verdict, not the code alone. A Copilot lane writes no such stream —
  no step-level view.
- **Output:** one line per lane (id, status, receipt, job state, age), then the anomalies. Cite
  `pos-<id>.log` and `neg-<id>.log` together; a missing or passing negative control means unverified.
