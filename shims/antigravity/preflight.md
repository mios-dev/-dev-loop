# Antigravity Workflow: /workflows:preflight

Identifier: `preflight`
Purpose: Check that this environment can host a dev-loop run — harness binaries, the exact CLI
flags the lane command templates rely on, AGY auth and grants, repo conformance. Read-only:
installs nothing, logs in to nothing, dispatches nothing.

Input: an optional harness list; empty means probe every harness.

**Why:** harness CLI flags drift monthly, so a lane command template that worked last month can be
rejected by this month's binary. Never assume a tool, flag or subagent exists. Skipped, the failure
lands late — every lane dispatches, every lane dies on an unrecognised flag.

1. **Phase 1: Binaries and flags.**
   `python3 <skills dir>/dev-loop/scripts/adapters.py probe [--harness NAME NAME ...]`
   It resolves each binary AND runs its help (`exec --help` for codex, `run --help` for opencode),
   diffing out the flags the lane templates pass. Report the table verbatim.
   **Argument form:** space-separated canonical names — `claude-code` (binary `claude`), `codex`,
   `gemini-cli` (`gemini`), `antigravity` (`agy`), `copilot`, `opencode`, `cursor` (binary `agent`).
   A short name or a comma-joined token raises `KeyError` and prints a traceback (measured).
2. **Phase 2: Read the lines, never the exit code alone.** Measured: with no `--harness`, `probe`
   printed five `MISSING` harnesses and **exited 0**. Exit 1 fires only for a harness you NAMED
   being missing, or for DRIFT on any harness. Outcomes: `ok` · `MISSING` (cannot host a lane) ·
   `DRIFT: flags not in --help: [...]` — those flags are exactly what the lane template passes, so
   that template is **unsafe to dispatch** · `help failed: ...` (unusable, not ok).
3. **Phase 3: Repo conformance, dev-loop checkouts only.** When
   `skills/dev-loop/scripts/validate.sh` exists: `sh skills/dev-loop/scripts/validate.sh`. It gates
   the plugin's own tree, not an arbitrary project; elsewhere say so and skip it.
4. **Phase 4: AGY environment, only when `agy` is on PATH.**
   `bash <skills dir>/dev-loop/scripts/env/agy-doctor.sh` — PASS/WARN/FAIL with evidence, exits
   non-zero **only on FAIL** (a WARN still exits 0). Its grants check is decisive for native
   lanes: headless agy auto-denies any tool it cannot prompt for and **still reports SUCCESS**.
   `--probe` makes ONE real headless agy call and **costs a model turn** — offer it, state the
   cost, never run it unasked. A billed check described as free is the overclaiming defect.
5. **Phase 5: Conclude with three things.** Which harnesses can host a lane right now; which lane
   command templates are unsafe to dispatch (quote the drifted flags, plus any AGY FAIL); the
   one-line remedy per problem, for the operator to run —
   `bash <skills dir>/dev-loop/scripts/env/setup-antigravity.sh`,
   `bash <skills dir>/dev-loop/scripts/env/agy-login.sh`,
   `sh <skills dir>/dev-loop/scripts/install.sh --harness NAME --user`, or a correction to the
   adapter's flag table before that harness is used again.

**Two-sided verification applies to this command:** a preflight that can only print PASS is a
check that cannot fail and would certify a container where no lane can act. Positive control —
probe a harness visibly on PATH ⇒ `ok`, exit 0. Negative control — probe a harness known to be
absent ⇒ `MISSING` **and exit 1**; exit 0 there means you ran the no-argument form, whose exit
code ignores missing binaries.

**Not in scope:** `adapters.py secrets` and `adapters.py deps` are fronted by `/review`. This asks
whether the tools are usable, not whether the diff is shippable.
