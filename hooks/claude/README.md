# Claude Code hook wiring

This directory holds **no manifest**, on purpose. `../hooks.json` is already a
complete and correct Claude Code manifest, and duplicating it here would create
exactly the drift this repo exists to catch. `../register-hooks.sh` derives the
settings wiring from it: it reads `../hooks.json`, substitutes
`${CLAUDE_PLUGIN_ROOT}` with this repo's root, and merges the resulting `hooks`
object into the settings file, leaving every other setting and every non-dev-loop
hook in place.

## Two independent ways Claude Code can load these hooks

1. **As a plugin.** `../hooks.json` is the plugin manifest. `${CLAUDE_PLUGIN_ROOT}`
   resolves only in this mode, which is why the file is written that way.
2. **As settings.** `register-hooks.sh` writes absolute paths into a settings file:

   | scope | path |
   |---|---|
   | user | `~/.claude/settings.json` |
   | project | `<repo>/.claude/settings.json` |

Route 2 exists because route 1 is currently in doubt -- see below. Running both is
harmless in effect but doubles each hook; pick one.

## Open question that this directory cannot resolve

`.claude-plugin/plugin.json` in this repo has **no `hooks` key**. The plugins
reference states that plugin hooks are declared through that key (a path, an array
of paths, or inline config) and are *not* auto-discovered from `hooks/hooks.json`
by path convention the way skills are. The hooks reference, meanwhile, presents
`hooks/hooks.json` as the plugin location with no such caveat. **The two official
pages read inconsistently**, and it cannot be settled from documentation.

If the plugins reference is right, this repo's entire enforcement manifest is
dormant whenever dev-loop is installed as a plugin -- a silent, load-bearing
failure of precisely the kind the dev-loop doctrine targets.

To settle it, run `claude --debug hooks` (or `--include-hook-events`) against a real
plugin install, before and after adding `"hooks": "./hooks/hooks.json"` to the
manifest. `.claude-plugin/plugin.json` is owned by another workflow and was not
touched here; this is a handoff, not a fix.

## A correction worth recording

`.claude/hooks/session-start.sh` in this repo is **not** a divergent copy of
`../session-start.sh`, despite the similar names and different lengths. They do
unrelated jobs: the 7-line plugin script injects the constitution pointer, the
ledger tail and unblocked tasks as context; the 25-line local one provisions the
`agy` CLI and the Fedora wrapper and exits immediately unless `CLAUDE_CODE_REMOTE`
is set. Merging them would destroy one of the two behaviours. What *is* true is
that `.claude/settings.json` wires only `SessionStart`, so the project scope gets
no guard, no format check and no stop gate -- which is what `register-hooks.sh
--project --harness claude` fixes.

## Confidence, stated plainly

Claude Code is **installed and measured here** (2.1.278). `claude --help` exposes
`--include-hook-events`, `--bare` ("skip hooks"), and a documented `hooks` debug
category. The manifest in `../hooks.json` is the one hook configuration in this
repo that predates this wiring and is known-good in the plugin shape. The settings
merge performed by `register-hooks.sh` has been exercised against a sandboxed
`HOME` (installed / unchanged / refreshed, with foreign hooks preserved); it has
**not** been observed driving a live Claude Code session from the settings route.
