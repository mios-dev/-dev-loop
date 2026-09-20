# OpenCode /preflight Command

Check whether this environment can host a dev-loop run (argument: optional harness list; empty =
probe every harness). Read-only: installs nothing, logs in to nothing, dispatches nothing.

Harness CLI flags drift monthly: a lane command template that worked last month can be rejected by
this month's binary. Never assume a tool, flag or subagent exists.

1. Binaries and flags: `python3 <skills dir>/dev-loop/scripts/adapters.py probe [--harness NAME NAME ...]`.
   It resolves each binary AND runs its help (`exec --help` for codex, `run --help` for opencode),
   diffing the flags the lane templates pass out of the help text. Report the table verbatim.
   `--harness` takes **space-separated canonical names**, never a comma-joined token and never a
   short name: `claude-code` (binary `claude`), `codex`, `gemini-cli` (`gemini`), `antigravity`
   (`agy`), `copilot`, `opencode`, `cursor` (binary `agent`). Anything else raises `KeyError` and
   prints a traceback (measured).
2. **Read the lines, not the exit code.** Measured: with no `--harness`, `probe` printed five
   `MISSING` harnesses and exited **0**. Exit 1 fires only when a harness you NAMED is missing, or
   when any harness has DRIFTED. Outcomes: `ok` · `MISSING` (cannot host a lane) ·
   `DRIFT: flags not in --help: [...]` — those flags are exactly what the lane template passes, so
   that template is **unsafe to dispatch** · `help failed: ...` (unusable, not ok).
3. Repo conformance, dev-loop checkouts only (`skills/dev-loop/scripts/validate.sh` exists):
   `sh skills/dev-loop/scripts/validate.sh`. It gates the plugin's own tree, not an arbitrary
   project; elsewhere say so and skip it.
4. Antigravity, only when `agy` is on PATH: `bash <skills dir>/dev-loop/scripts/env/agy-doctor.sh`
   — PASS/WARN/FAIL with evidence, exits non-zero **only on FAIL** (a WARN still exits 0). Its
   grants check is the decisive one for unattended runs: headless agy auto-denies any tool it
   cannot prompt for and still reports SUCCESS. `--probe` makes ONE real headless agy call and
   **costs a model turn** — offer it, state the cost, never run it unasked.
5. Conclude with three things: which harnesses can host a lane right now; which lane command
   templates are unsafe to dispatch (quote the drifted flags, plus any AGY FAIL); the one-line
   remedy per problem for the operator — `bash <skills dir>/dev-loop/scripts/env/setup-antigravity.sh`,
   `bash <skills dir>/dev-loop/scripts/env/agy-login.sh`, or
   `sh <skills dir>/dev-loop/scripts/install.sh --harness NAME --user`.

Two-sided verification applies to this command as well: a preflight that can only print PASS is a
check that cannot fail. Positive control — probe a harness on PATH ⇒ `ok`, exit 0. Negative
control — probe a harness known absent ⇒ `MISSING` **and exit 1**; exit 0 there means the
no-argument form, whose exit code ignores missing binaries.

Not in scope: `adapters.py secrets` and `adapters.py deps` are fronted by `/review`.
