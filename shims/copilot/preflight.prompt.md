---
name: preflight
description: Check the environment before a run — harness binaries, the exact CLI flags the lane templates rely on, AGY auth and grants, repo conformance (read-only)
version: 1.0.0
---

# GitHub Copilot /preflight Workflow

Check whether this environment can host a dev-loop run. Harness list: `${input}` (empty = probe
every harness). **Read-only**: install nothing, log in to nothing, dispatch nothing.

Harness CLI flags drift monthly, so a lane command template that worked last month can be rejected
by this month's binary. Never assume a tool, flag or subagent exists. Skipped, the failure lands
late: every lane dispatches, every lane dies on an unrecognised flag.

- **Binaries and flags:** `python3 <skills dir>/dev-loop/scripts/adapters.py probe [--harness NAME NAME ...]`.
  It resolves each binary AND runs its help (`exec --help` for codex, `run --help` for opencode),
  diffing the flags the lane templates pass out of that help text. Report the table verbatim.
- **Argument form:** space-separated **canonical** names — `claude-code` (binary `claude`),
  `codex`, `gemini-cli` (`gemini`), `antigravity` (`agy`), `copilot`, `opencode`, `cursor`
  (binary `agent`). A short name or a comma-joined token raises `KeyError` and prints a traceback
  (measured). Translate what the operator typed first.
- **Read the lines; exit 0 is not "all good".** Measured: with no `--harness`, `probe` printed
  five `MISSING` harnesses and exited **0**. Exit 1 fires only for a harness you NAMED being
  missing, or DRIFT on any harness. Outcomes: `ok` · `MISSING` (cannot host a lane) ·
  `DRIFT: flags not in --help: [...]` — those flags are exactly what the lane template passes, so
  that template is **unsafe to dispatch** · `help failed: ...` (unusable, not ok).
- **Repo conformance, dev-loop checkouts only** (`skills/dev-loop/scripts/validate.sh` exists):
  `sh skills/dev-loop/scripts/validate.sh`. It gates the plugin's own tree, not an arbitrary
  project; elsewhere say so and skip it.
- **Antigravity, only when `agy` is on PATH:** `bash <skills dir>/dev-loop/scripts/env/agy-doctor.sh`
  — PASS/WARN/FAIL with evidence, exits non-zero **only on FAIL** (a WARN still exits 0). Its
  grants check is decisive unattended: headless agy auto-denies any tool it cannot prompt for and
  still reports SUCCESS. `--probe` makes ONE real headless agy call and **costs a model turn** —
  offer it, state the cost, never run it unasked.
- **Conclude with three things:** which harnesses can host a lane right now; which lane command
  templates are unsafe to dispatch (quote the drifted flags, plus any AGY FAIL); the one-line
  remedy per problem for the operator — `bash <skills dir>/dev-loop/scripts/env/setup-antigravity.sh`,
  `bash <skills dir>/dev-loop/scripts/env/agy-login.sh`, or
  `sh <skills dir>/dev-loop/scripts/install.sh --harness NAME --user`.
- **Two-sided verification:** a preflight that can only print PASS is a check that cannot fail.
  Positive control — probe a harness on PATH ⇒ `ok`, exit 0. Negative control — probe a harness
  known absent ⇒ `MISSING` **and exit 1**; exit 0 there means the no-argument form, whose exit
  code ignores missing binaries.
- **Not in scope:** `adapters.py secrets` and `adapters.py deps` are fronted by `/review`. A
  Copilot lane is probed like any other, but note its own flag set (`-p`, `--allow-tool`,
  `--deny-tool`, `--output-format`, `--add-dir`, `--no-ask-user`) is what DRIFT would name here.
