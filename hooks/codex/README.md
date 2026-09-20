# Codex hook wiring

`hooks.json` here is the dev-loop hook manifest for Codex. `${DEVLOOP_HOOKS}` is
substituted with the absolute path of this repo's `hooks/` directory by
`../register-hooks.sh`; the adapter is referenced in place, not copied.

## Where it is installed

| scope | path |
|---|---|
| user | `~/.codex/hooks.json` |
| project | `<repo>/.codex/hooks.json` |

The same hooks can instead be written as inline `[[hooks.EventName]]` tables in
`config.toml`. The installer uses the JSON file, which is the same hook layered
the simpler of the two ways. An administrator can set `allow_managed_hooks_only =
true` in `requirements.toml`, which makes Codex ignore user and project hook
config entirely -- if that is set, nothing here runs and nothing reports that.

## What is wired

| Codex event | dev-loop script | effect |
|---|---|---|
| `SessionStart` | `session-start.sh` | constitution pointer, ledger tail, unblocked tasks |
| `UserPromptSubmit` | `prompt-context.sh` | in-progress task |
| `PreToolUse` | `guard.sh`, then `no-env.sh` | deny sweeping `git add`, force-push, pipe-to-shell, secret printing, secret-file writes |
| `PostToolUse` | `format.sh` | non-truncation + parse check on the written file |
| `PreCompact` | `pre-compact.sh` | handoff ledger entry |
| `Stop`, `SubagentStop` | `stop-gate.sh` | refuse to stop without a terminal `devloop_report` |

## Confidence, stated plainly

* Codex is **not installed** in this container (`adapters.py probe`: `codex
  MISSING`). Every path, event name and payload field here is vendor-documented,
  not measured. Nothing in this directory has been observed to fire.
* **The matchers are `.*` on purpose.** Codex's tool names are not documented, and a
  matcher naming a tool that does not exist is silently inert -- present at review
  time, absent at run time. The adapter therefore routes on the shape of
  `tool_input` rather than on a guessed tool name. The cost is that the adapter
  starts on every tool call; the scripts it fronts are grep and parse checks, and
  it exits without running anything when neither a command nor a path is present.
* **Headless is the open question and it is the one that matters.** The dev-loop
  lane template drives Codex through `codex exec`, and the vendor docs do not state
  whether hooks fire in that mode. Until someone measures it, treat headless hook
  enforcement under Codex as unproven -- a gate that is present interactively and
  absent in every lane is worse than no gate, because it passes review on a
  developer's machine.
