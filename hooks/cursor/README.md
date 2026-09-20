# Cursor Agent hook wiring

`hooks.json` here is the dev-loop entry for Cursor's hook file. `${DEVLOOP_HOOKS}`
is substituted with the absolute path of this repo's `hooks/` directory by
`../register-hooks.sh`; the adapter is referenced in place, not copied.
`"version": 1` is required by Cursor and is present.

## Where it is installed

| scope | path |
|---|---|
| user | `~/.cursor/hooks.json` |
| project | `<project-root>/.cursor/hooks.json` |

Cursor also reads an enterprise file at `/etc/cursor/hooks.json`; the installer
never writes there.

## What is wired

| Cursor event | dev-loop script | effect |
|---|---|---|
| `sessionStart` | `session-start.sh` | `{"additional_context": ...}` |
| `beforeShellExecution` | `guard.sh` | `{"permission":"deny", "agent_message": ...}` |
| `preToolUse` | `guard.sh`, then `no-env.sh` | same deny shape |
| `postToolUse` | `format.sh` | emptied/unparseable file reported as `additional_context` |
| `preCompact` | `pre-compact.sh` | handoff ledger entry |
| `stop`, `subagentStop` | `stop-gate.sh` | **advisory only** -- see below |

Every Cursor hook payload carries `transcript_path`, which is what `stop-gate.sh`
needs, so the gate has real input here -- unlike Copilot.

## The stop gate is advisory here, not enforcing

Cursor's `stop` hook accepts only `{"followup_message": ...}`. There is no
documented refusal. So where Claude Code's `{"decision":"block"}` and
Antigravity's `{"decision":"continue"}` genuinely re-arm the loop, Cursor gets a
message and stops anyway unless the harness chooses to continue on a followup --
which is **not** documented either way. Do not count Cursor in the set of
harnesses where the dev-loop can enforce its own re-arm.

The adapter also returns silently when `status` is `aborted` or `error`: those are
the operator interrupting, and nagging there is noise.

## Confidence, stated plainly

* Cursor is **not installed** in this container (`adapters.py probe`:
  `cursor agent MISSING`). Nothing here has been observed to fire.
* Config paths, the `version: 1` envelope, event names, per-event stdin field names
  and the permission/`followup_message`/`additional_context` output shapes are all
  vendor-documented.
* **Headless is unconfirmed and it is the mode lanes use.** The documentation does
  not state that `cursor-agent -p/--print` honours hooks. What it does state is
  that project-level `.cursor/hooks.json` is picked up by cloud agents while
  user-level `~/.cursor/hooks.json` is not, and that cloud agents support only
  `type: "command"`. Prefer `--project` scope for anything that must survive into a
  non-interactive run, and measure before relying on it.
* `failClosed` is left `false` on the two permission rows. A `failClosed: true`
  guard turns any adapter error -- a missing `python3`, a moved repo -- into a hard
  block on every shell command. That trade is the operator's to make, not this
  repo's default.
