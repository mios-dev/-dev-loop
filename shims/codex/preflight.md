# /preflight Prompt for OpenAI Codex

Check whether this environment can host a dev-loop run. **Read-only**: install nothing, log in to
nothing, dispatch nothing. Argument is an optional harness list; empty means probe every harness.

Harness CLI flags drift monthly, so a lane command template that worked last month can be rejected
by this month's binary. Never assume a tool, flag or subagent exists. Skipped, the failure lands
late: every lane dispatches, every lane dies on an unrecognised flag, and you debug the codebase
instead of the CLI.

1. **Binaries and flags:**
   `python3 <skills dir>/dev-loop/scripts/adapters.py probe [--harness NAME NAME ...]`
   It resolves each binary AND runs its help (`exec --help` for codex, `run --help` for opencode),
   diffing the flags the lane templates pass out of the help text. Report the table verbatim.
   **`--harness` takes space-separated canonical names**, not a comma-joined token and not the
   short name: `claude-code` (binary `claude`), `codex`, `gemini-cli` (`gemini`), `antigravity`
   (`agy`), `copilot`, `opencode`, `cursor` (binary `agent`). Anything else raises `KeyError` and
   prints a traceback — measured.
2. **Read the lines; never infer "all good" from exit 0.** Measured: `probe` with no `--harness`
   printed five `MISSING` harnesses and exited **0**. It exits 1 only when a harness you NAMED is
   missing, or when any harness has DRIFTED. Four outcomes: `ok` · `MISSING` (that harness cannot
   host a lane) · `DRIFT: flags not in --help: [...]` (the named flags are exactly what the lane
   template passes — that template is **unsafe to dispatch**) · `help failed: ...` (the binary
   exists but would not answer; unusable, not ok).
3. **Repo conformance, dev-loop checkouts only** (`skills/dev-loop/scripts/validate.sh` exists):
   `sh skills/dev-loop/scripts/validate.sh`. It gates the plugin's own tree, not an arbitrary
   project's build — elsewhere say so and skip it rather than calling the absent file a failure.
4. **Antigravity, only when `agy` is on PATH:**
   `bash <skills dir>/dev-loop/scripts/env/agy-doctor.sh` — PASS/WARN/FAIL per check, exits
   non-zero **only on FAIL**, so a WARN still exits 0. Its grants check matters most unattended:
   headless agy auto-denies any tool it cannot prompt for and still reports SUCCESS.
   `--probe` makes ONE real headless agy call and **costs a model turn**: offer it, state the
   cost, never run it unasked. Calling a billed check free is itself the overclaiming defect.
5. **Conclude with three things:** which harnesses can host a lane right now; which lane command
   templates are unsafe to dispatch, quoting the drifted flags and any AGY FAIL; and the one-line
   remedy per problem for the operator to run — `bash <skills dir>/dev-loop/scripts/env/setup-antigravity.sh`,
   `bash <skills dir>/dev-loop/scripts/env/agy-login.sh`,
   `sh <skills dir>/dev-loop/scripts/install.sh --harness NAME --user`, or a correction to the
   adapter's flag table before that harness is used again.

**Two-sided verification governs this command too:** a preflight that can only print PASS is a
check that cannot fail. Positive control — probe a harness on PATH ⇒ `ok`, exit 0. Negative
control — probe a harness known absent ⇒ `MISSING` **and exit 1**. Exit 0 there means you ran the
no-argument form, whose exit code ignores missing binaries.

**Not in scope:** the staged-diff secret scan and supply-chain gate (`adapters.py secrets` /
`deps`) are fronted by `/review`.
