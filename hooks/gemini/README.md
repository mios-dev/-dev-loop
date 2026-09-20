# Gemini CLI hook wiring

Gemini keeps hooks **inside `settings.json`**, not in a separate hooks file. This
directory therefore ships a *fragment* -- just the `hooks` object -- and
`../register-hooks.sh` merges it into the settings file rather than overwriting it.
`${DEVLOOP_HOOKS}` is substituted with the absolute path of this repo's `hooks/`
directory; the adapter is referenced in place, not copied.

## Where it is installed

| scope | path |
|---|---|
| user | `~/.gemini/settings.json` |
| project | `<repo>/.gemini/settings.json` |

`~/.gemini/settings.json` is a DIFFERENT file from Antigravity's
`~/.gemini/config/hooks.json`, despite the shared `~/.gemini` prefix. The two
products do not share hook config. Writing one does not configure the other.

## What is wired

| Gemini event | dev-loop script | effect |
|---|---|---|
| `SessionStart` | `session-start.sh` | returns `hookSpecificOutput.additionalContext` |
| `BeforeTool` | `guard.sh`, then `no-env.sh` | `{"decision":"deny","reason":...}` |
| `AfterTool` | `format.sh` | surfaces an emptied or unparseable written file |
| `PreCompress` | `pre-compact.sh` | handoff ledger entry |

`timeout` is in **milliseconds** here. It is seconds in every other harness in this
repo. The values in the fragment are already scaled; do not copy them sideways.

## Confidence, stated plainly

* Gemini CLI is **not installed** in this container (`adapters.py probe`:
  `gemini MISSING`). Nothing here has been observed to fire.
* The event names, the settings shape, the `{"decision":"deny"}` output and the
  `SessionStart` `additionalContext` output are vendor-documented.
* The per-event **stdin field names are not pinned down** by that documentation, so
  the adapter looks for a command or a path under several plausible spellings
  (`tool_input.command`, `toolArgs.command`, `args.command`, ...) instead of
  committing to one. If Gemini uses none of them, the guard degrades to a no-op
  rather than to a false pass -- but it degrades silently, which is the known weak
  point of this row.

## Not wired, and why

* **There is no stop gate for Gemini.** `stop-gate.sh` is the dev-loop's re-arm
  mechanism, and it needs an event that can refuse a stop. Gemini's `AfterAgent`
  exists but no documented output of it blocks termination, and `SessionEnd` is
  observational. Rather than install a file that would appear to enforce the loop
  and would not, this row is left empty. That is the single biggest functional gap
  between Gemini and Claude Code / Antigravity / Codex / Copilot here.
* `BeforeToolSelection` can only restrict the toolset (`toolConfig.mode`), not
  inspect a call, so it cannot host `guard.sh`.
