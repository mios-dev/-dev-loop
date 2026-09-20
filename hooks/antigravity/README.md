# Antigravity (`agy`) hook wiring

`hooks.json` here is the dev-loop entry for Antigravity's lifecycle-hook file.
`${DEVLOOP_HOOKS}` is substituted with the absolute path of this repo's `hooks/`
directory by `../register-hooks.sh`; the adapter is referenced in place, not copied,
so editing a hook script takes effect without reinstalling.

## Where it is installed

| scope | path |
|---|---|
| user | `~/.gemini/config/hooks.json` |
| project | `<workspace>/.agents/hooks.json` |

The top level of that file is keyed by **hook name**, not by event, so several
tools can coexist in it. The installer replaces only the `dev-loop` key.

`~/.gemini/antigravity-cli/hooks.json` is the WRONG path -- an upstream bug that
was fixed; the directory exists and is populated, which makes it an easy mistake.
Nothing is written there.

## What is wired

| agy event | dev-loop script | effect |
|---|---|---|
| `PreToolUse` matcher `run_command` | `guard.sh` | `{"decision":"deny"}` on sweeping `git add`, force-push, pipe-to-shell, secret printing |
| `PreToolUse` matcher `file_change\|propose_code\|edit_notebook\|write_blob` | `no-env.sh` | deny writes to secret-bearing files |
| `PreInvocation` | `session-start.sh` (first invocation) + `prompt-context.sh` | injects the constitution pointer, ledger tail and in-progress task as `ephemeralMessage` steps |
| `Stop` | `stop-gate.sh` | `{"decision":"continue"}` refuses the stop until a terminal `devloop_report` exists |

The `Stop` mapping is the interesting one: agy's `{"decision":"continue"}` blocks
the stop and re-enters the loop from *inside* the harness, which is a native answer
to the lifetime constraint in `AGENTS.md` (a subagent unfinished at turn end dies
with the process). It is bounded by `stop-gate.sh`'s own `DEVLOOP_STOP_CAP` /
`DEVLOOP_LOOP_CAP` counters, so it cannot loop forever.

## Confidence, stated plainly

* The file format, the five event names, the matcher rules and the full per-event
  stdin/stdout contract are **primary-source**: the vendor's own reference document
  ships embedded in the `agy` binary and was read verbatim from it (`agy` 1.2.7).
* **No agy hook has been observed to fire.** `agy` in this container is
  unauthenticated, so a firing probe never reached the agent loop. Runtime
  behaviour is UNVERIFIED.
* Two specific traps. (1) Workspace trust state affects whether
  `<workspace>/.agents/hooks.json` loads at all -- an upstream changelog records a
  period where it did not load after trusting a folder. (2) The args key that
  carries a file path on the write steps is not documented (only `run_command`'s
  `CommandLine` is), so `no-env.sh` is fed the first path-shaped argument value.
  Matcher names are derived from `CORTEX_STEP_TYPE_*` symbols in the binary; if a
  write step is named something else, that row silently never fires.
* On the allow path the adapter emits `{}`, not `{"decision":"allow"}`. Emitting
  `allow` would auto-approve every command and strip the operator's own permission
  prompts. The vendor doc calls `decision` required, so `{}` is the one unverified
  assumption in the mapping.

## Not wired, and why

* `PostToolUse` -> `format.sh`: skipped. `format.sh` needs the path of the file that
  was written, and agy's `PostToolUse` payload carries `stepIdx` and `error` but no
  documented argument echo.
* There is no compaction event in agy's five, so `pre-compact.sh` has nowhere to go.
