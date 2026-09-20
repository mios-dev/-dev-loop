---
name: preflight
description: Check the environment before a run — which harness binaries exist, whether the exact CLI flags the lane command templates rely on are still in their --help output, Antigravity authentication and grants when agy is installed, and repo conformance when the cwd is a dev-loop checkout. Use before dispatching any lane, after upgrading or installing a harness CLI, when a lane died on an unrecognised flag or returned an empty result, and at the start of any multi-lane run. Read-only; it installs nothing and changes nothing, it names the one-line remedy instead.
argument-hint: "[harness ...]"
allowed-tools: Read, Grep, Glob, Bash
---
# /preflight — check the environment before dispatching lanes

_Paths: `${CLAUDE_SKILL_DIR}/../dev-loop/scripts/` resolves in Claude Code; in other harnesses use
`<skills dir>/dev-loop/scripts/`. Harness command templates: `references/harness-adapters.md`.
Environment layer: `references/environment.md`._

**The rule this command exists to enforce.** Harness CLI flags drift monthly, so a lane command
template that worked last month can be rejected by this month's binary. Never assume a tool, flag
or subagent exists (dev-loop SKILL §0) — verify it, then dispatch. Without this check the failure
arrives late and expensive: every lane dispatches, every lane dies on an unrecognised flag or
returns nothing, and the operator debugs the codebase instead of the CLI.

Nothing here installs, logs in, edits or dispatches. It reports, and names the remedy.

`$ARGUMENTS` is an optional harness list. Empty ⇒ probe all of them.

## 1. Harness binaries and flags

```
python3 <skills dir>/dev-loop/scripts/adapters.py probe [--harness NAME NAME ...]
```

`probe` resolves each binary with `which` **and** runs its help (`--help`; `exec --help` for
codex, `run --help` for opencode), then diffs the flags the adapter's lane command templates rely
on out of that help text. Report the table **verbatim**, one line per harness.

**Argument form, measured — get this wrong and it crashes.** `--harness` takes
**space-separated canonical names**, not a comma-joined list, and the names are the adapter's
internal keys, not the short ones people say:

| canonical name | binary probed |
|---|---|
| `claude-code` | `claude` |
| `codex` | `codex` |
| `gemini-cli` | `gemini` |
| `antigravity` | `agy` |
| `copilot` | `copilot` |
| `opencode` | `opencode` |
| `cursor` | `agent` |

Anything else — `claude`, `gemini`, or `claude-code,codex` passed as one comma-joined token —
raises `KeyError` and prints a Python traceback (measured). Translate what the operator typed
into these names before you run it.

**Read the lines; never infer "all good" from the exit code.** Measured in a container with
`claude` and `agy` installed: `probe` with no `--harness` printed five `MISSING` harnesses and
**exited 0**. The exit code is 1 only when a harness you *named* is missing, or when any harness
has **drifted**. Four outcomes per line, all meaningful:

- `<path>  ok` — binary found, every relied-on flag present in its help.
- `MISSING` — binary not on PATH. Lanes cannot run under it.
- `DRIFT: flags not in --help: [...]` — the binary moved under us. **The named flags are the
  ones the lane command template passes**, so that template is unsafe to dispatch until the
  adapter is updated. This is the case the command exists for.
- `help failed: ...` — the binary exists but would not answer; treat as unusable, not as ok.

## 2. Repo conformance (dev-loop checkouts only)

```
sh skills/dev-loop/scripts/validate.sh
```

This is the gate for **the dev-loop plugin's own tree** — skill frontmatter, plugin manifest,
hook shapes, schemas, python/shell syntax, its behavioural tests. Run it only when the cwd is a
dev-loop checkout (`skills/dev-loop/scripts/validate.sh` exists). In an ordinary project it is
not the project's gate; say so and skip it rather than reporting a missing file as a failure.

## 3. Antigravity environment (only when `agy` is on PATH)

```
bash <skills dir>/dev-loop/scripts/env/agy-doctor.sh
```

Prints `PASS` / `WARN` / `FAIL` per check with the evidence, and exits non-zero only if some
check **FAILed** — a `WARN` (for example a stale installed copy of the skill) exits 0, so again
read the lines. It covers the binary, the credential keyring round-trip, whether the installed
skill copy matches this checkout, and — the check that matters most for unattended runs —
whether the headless permission grants are **active**, because a headless agy auto-denies any
tool it cannot prompt for and then still reports SUCCESS.

`--probe` is a separate, **billed** step: it makes one real headless `agy` call that must use a
tool, which proves authentication and that grants actually work. **Offer it, state the cost, and
never run it unasked.** Describing a check that bills as if it were free is the overclaiming
defect this repo treats as a bug in its own right.

## 4. Conclude with three things, always

1. **Which harnesses can host a lane right now** — the `ok` lines, named.
2. **Which lane command templates are unsafe to dispatch** — every `MISSING`, `DRIFT` and
   `help failed` line, with the drifted flags quoted, plus any AGY `FAIL`.
3. **The one-line remedy per problem**, and nothing run on the operator's behalf:
   - `agy` missing or unprovisioned ⇒ `bash <skills dir>/dev-loop/scripts/env/setup-antigravity.sh`
   - agy not authenticated ⇒ `bash <skills dir>/dev-loop/scripts/env/agy-login.sh`
   - skill copy stale for a harness ⇒ `sh <skills dir>/dev-loop/scripts/install.sh --harness NAME --user`
   - a drifted flag ⇒ the adapter's flag table must be corrected before that harness is used;
     re-probe after any CLI upgrade.

## Two-sided verification applies to this command too

A preflight that can only print PASS is a check that cannot fail (dev-loop SKILL §7) — and it
would certify a container in which no lane can do anything. Prove the check can fail before you
trust a clean run:

- **Positive control:** `probe --harness` naming a harness you can see on PATH ⇒ `ok`, exit 0.
- **Negative control:** `probe --harness` naming a harness you know is absent ⇒ that line reads
  `MISSING` **and the exit code is 1**. If it exits 0, you are reading the no-argument form,
  whose exit code ignores missing binaries — go back to the lines.

Do the same for the environment: a doctor run that prints only PASS on a box you have not logged
into is not evidence of auth; the grants check and `--probe` are what can fail.

## Scope

Pre-commit scanning is **not** here: the staged-diff secret scan (`adapters.py secrets`) and the
supply-chain gate (`adapters.py deps`) are fronted by `/review`. This command is about whether
the *tools* are usable, not whether the *diff* is shippable.

Named `preflight` rather than `doctor` deliberately — `/doctor` is a built-in command in at least
one host harness and would collide.
