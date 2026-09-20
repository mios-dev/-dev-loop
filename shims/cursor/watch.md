# Cursor Rule: Watch a Dev-Loop Run

Defines the `/watch` protocol: read-only reporting of a `.devloop/run-*` directory — the model's
`report-<id>.json` claim against the shell's `worker-<id>.exit` receipt, `job.py` liveness
(`absent|running|done|lost|forged`), bounded waits only, and AGY-only step detail from
`agy_monitor.py`.
