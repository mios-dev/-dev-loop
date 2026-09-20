# Cursor Rule: End the Session on Disk

Defines the `/handoff` protocol for stopping with work unfinished: flip the task with `artifacts.py tasks set` (which refuses `done` without two-sided evidence), re-render `TASKS.md`, park uncommitted work as a patch, and append an `adapters.py ledger` entry pinned to `git rev-parse --short HEAD` whose `--unverified` field states what was claimed but never measured. Merges nothing, commits nothing — the next session starts from disk instead of from a remembered summary.
