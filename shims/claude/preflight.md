---
description: Check the environment before a run — harness binaries, the exact CLI flags the lane templates rely on, AGY auth and grants, repo conformance (read-only)
argument-hint: [harness ...]
allowed-tools: Read, Glob, Grep, Bash
---
Load the `preflight` skill (SKILL.md — project `.claude/skills/preflight/` or `~/.claude/skills/preflight/`) and check whether this environment can host a dev-loop run:

$ARGUMENTS

Empty argument means probe every harness. **Read-only**: install nothing, log in to nothing, dispatch nothing. Name the remedy and stop.

Scripts below live at `${CLAUDE_PLUGIN_ROOT}/skills/dev-loop/scripts/` under a plugin install, or `<skills dir>/dev-loop/scripts/` otherwise.

**Why this exists:** harness CLI flags drift monthly, so a lane command template that worked last month can be rejected by this month's binary. Never assume a tool, flag or subagent exists (SKILL §0). Skip this and the failure lands late: every lane dispatches, every lane dies on an unrecognised flag, and you debug the codebase instead of the CLI.

1. **Binaries + flags:** `python3 <scripts>/adapters.py probe [--harness NAME NAME ...]`. It resolves each binary AND runs its help (`exec --help` for codex, `run --help` for opencode), diffing the flags the lane command templates pass out of that help text. **Report the table verbatim, one line per harness.**
   - `--harness` takes **space-separated canonical names**, never a comma-joined token and never the short name: `claude-code` (binary `claude`), `codex`, `gemini-cli` (`gemini`), `antigravity` (`agy`), `copilot`, `opencode`, `cursor` (binary `agent`). Anything else raises `KeyError` and prints a traceback — measured. Translate what the operator typed before running it.
   - **READ THE LINES. Never infer "all good" from exit 0.** Measured: `probe` with no `--harness` printed five `MISSING` harnesses and exited **0**. It exits 1 only when a harness you NAMED is missing, or when any harness has DRIFTED.
   - Four outcomes, all meaningful: `<path> ok` · `MISSING` (no binary; that harness cannot host a lane) · `DRIFT: flags not in --help: [...]` (the named flags are exactly what the lane template passes — that template is **unsafe to dispatch**) · `help failed: ...` (exists but would not answer — unusable, not ok).
2. **Repo conformance, only when the cwd is a dev-loop checkout** (`skills/dev-loop/scripts/validate.sh` exists): `sh skills/dev-loop/scripts/validate.sh`. This gates the *plugin's own tree*, not an arbitrary project's build — in an ordinary repo say so and skip it, rather than reporting the absent file as a failure.
3. **Antigravity, only when `agy` is on PATH:** `bash <scripts>/env/agy-doctor.sh`. PASS/WARN/FAIL per check; it exits non-zero **only on FAIL**, so a `WARN` (e.g. a stale installed skill copy) still exits 0 — read the lines. Its grants check is the one that matters unattended: headless agy auto-denies any tool it cannot prompt for and **still reports SUCCESS**.
   **`--probe` is billed.** It makes one real headless `agy` call that must use a tool, proving auth and that grants work. Offer it, state the cost, **never run it unasked** — calling a billed check free is the overclaiming defect this repo treats as a bug.
4. **Conclude with three things:** (a) which harnesses can host a lane right now; (b) which lane command templates are unsafe to dispatch, quoting the drifted flags and any AGY FAIL; (c) the one-line remedy per problem, run by the operator, not by you — `bash <scripts>/env/setup-antigravity.sh` (agy missing/unprovisioned), `bash <scripts>/env/agy-login.sh` (not authenticated), `sh <scripts>/install.sh --harness NAME --user` (stale skill copy), or a correction to the adapter's flag table before that harness is used again.

**Two-sided verification applies here too (§7):** a preflight that can only print PASS is a check that cannot fail, and would certify a container where no lane can do anything. Positive control — probe a harness you can see on PATH ⇒ `ok`, exit 0. Negative control — probe a harness you know is absent ⇒ `MISSING` **and exit 1**. Exit 0 there means you are in the no-argument form, whose exit code ignores missing binaries.

**Not in scope:** the staged-diff secret scan and the supply-chain gate (`adapters.py secrets` / `deps`) belong to `/review`. This command asks whether the *tools* are usable, not whether the *diff* is shippable.

Harness command templates: `skills/dev-loop/references/harness-adapters.md`. Environment layer: `references/environment.md`.
