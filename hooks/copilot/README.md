# GitHub Copilot CLI hook wiring

Copilot reads a **directory** of hook files, not one fixed filename, so this ships
as its own `dev-loop.json` and coexists with anything else in that directory
without a merge. `${DEVLOOP_HOOKS}` is substituted with the absolute path of this
repo's `hooks/` directory by `../register-hooks.sh`; the adapter is referenced in
place, not copied.

## Where it is installed

| scope | path |
|---|---|
| user | `~/.copilot/hooks/dev-loop.json` (or `$COPILOT_HOME/hooks/`) |
| project | `.github/hooks/dev-loop.json` |

## What is wired

| Copilot event | dev-loop script | effect |
|---|---|---|
| `preToolUse` | `guard.sh`, then `no-env.sh` | `{"permissionDecision":"deny",...}` -- the only event that can deny |
| `postToolUse` | `format.sh` | reports an emptied or unparseable written file as `additionalContext` |
| `preCompact` | `pre-compact.sh` | handoff ledger entry |
| `agentStop`, `subagentStop` | `stop-gate.sh` | `{"decision":"block","reason":...}` |

Note the two different output shapes: the deny is **flat**
(`permissionDecision` at top level, no `hookSpecificOutput` wrapper), while the
stop block is Claude Code's shape. The adapter emits each one correctly; do not
assume one shape covers both.

## Confidence, stated plainly

* Copilot CLI is **not installed** in this container (`adapters.py probe`:
  `copilot MISSING`). Nothing here has been observed to fire.
* Paths, the `version: 1` envelope, the event names and the deny semantics are
  vendor-documented.
* **The stop gate may be inert.** `stop-gate.sh` decides by reading the session
  transcript, and Copilot's stop payload is not documented to carry a transcript
  path. If it does not, the adapter writes
  `dev-loop: stop gate inert -- no transcript path` to stderr and returns without a
  decision. It fails loudly rather than reporting a gate that never gated. Confirm
  against a real payload before relying on the loop re-arming under Copilot.
* **Copilot also reads `.claude/settings.json`.** That means hooks authored for
  Claude Code's event names and JSON contract get loaded by Copilot too, where the
  event names are camelCase and only `preToolUse` can block. Expect partial,
  silent cross-tool activation, and do not read a working Claude Code gate as
  evidence that the Copilot gate works.

## Not wired, and why

* `sessionStart` / `userPromptSubmitted`: Copilot performs **no output processing**
  for `sessionStart`, so `session-start.sh` has no way to return context through it.
  Rather than install a handler whose output is discarded, these rows are empty.
