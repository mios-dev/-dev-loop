# OpenCode hook wiring

OpenCode has **no declarative hook file**. Lifecycle extension is a JS/TS module
that exports an async plugin function returning event handlers. A `hooks.json`
written here would be silently ignored -- present at review time, absent at run
time -- so this directory ships `dev-loop.js` instead.

Unlike the JSON manifests in the sibling directories, this file is **copied** into
the plugins directory, so `../register-hooks.sh` rewrites the `DEVLOOP_HOOKS`
constant at the top to the absolute path of this repo's `hooks/` directory. Moving
the repo means re-running the installer for OpenCode.

## Where it is installed

| scope | path |
|---|---|
| user | `~/.config/opencode/plugins/dev-loop.js` |
| project | `<project>/.opencode/plugins/dev-loop.js` |

Plugins in those directories are loaded without registration. The `"plugin": []`
array in `opencode.json` is for npm-published plugins only and is not used here.

## What is wired

| OpenCode event | dev-loop script | effect |
|---|---|---|
| `tool.execute.before` | `guard.sh`, then `no-env.sh` | throws, which aborts the tool call |

Routing is by the shape of `output.args` -- a `command` goes to `guard.sh`, a
`filePath`/`file_path`/`path` goes to `no-env.sh` -- so it does not depend on
guessing OpenCode's tool names.

## Confidence, stated plainly

* OpenCode is **not installed** in this container (`adapters.py probe`:
  `opencode MISSING`). Nothing here has been observed to fire. The file parses
  (`node --check`) and that is the full extent of what has been verified.
* The plugin directories, the export shape, the `tool.execute.before` signature
  (`input.tool`, `output.args`) and throw-to-abort are vendor-documented.
* The plugin returns a plain object of handlers and uses only `node:child_process`
  and `node:fs`, both of which the runtime provides. It imports no OpenCode SDK
  types, so there is nothing to go stale in a type definition.

## Not wired, and why

* **No stop gate.** `session.idle` is the nearest event, and it carries a session
  id, not a transcript path. `stop-gate.sh` decides by reading the transcript, so
  there is nothing to feed it. The dev-loop's re-arm cannot be enforced under
  OpenCode; do not assume otherwise from the presence of this plugin.
* **No session-start context and no format check.** `session.created` and
  `file.edited` exist, but their handler argument shapes are not documented to the
  level `tool.execute.before`'s are, and a handler that reads the wrong property is
  an inert handler. Only the event whose signature is published is wired.
