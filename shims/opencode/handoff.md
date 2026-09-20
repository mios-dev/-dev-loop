---
description: End a session on disk — flip the task with evidence, park uncommitted work as a patch, append a ledger entry pinned to HEAD stating what is still unverified
argument-hint: [task-id] [status note]
---

# /handoff: End the Session on Disk

Target: `$ARGUMENTS` — a task id and a free-text status note; either may be empty.

Below, `$S` = the dev-loop `scripts/` directory (`<skills dir>/dev-loop/scripts/`).

The loop's first step reads `AGENTS.md`, **the last `.devloop/LEDGER.md` entry**, `TASKS.md` and recent history. This command writes those. End without it and the next session gets a stale board plus no record of what was claimed but never measured.

**Never merge, commit, push, or `git add`.** This is for stopping with work *unfinished* — the common case.

## Protocol — four steps, this order

1. **Flip the task.** `python3 $S/artifacts.py tasks set <T-0NN> <status> --root . --evidence "pos: <cmd> -> passed; neg: <plant> -> <cmd> failed naming <expect>"`. Status ∈ `open · in_progress · blocked · done · cancelled` (anything else: `status must be one of [...]`, exit 1; unknown id: `no task <id>`, exit 1). `done` with no evidence is **refused**, exit 1, verbatim: `done requires --evidence (both controls, exact commands)`. That is the two-sided rule in code — a check that cannot fail passes identically on correct and broken code, so `done` needs a positive control that passed *and* a negative control that failed naming the plant. Cannot cite both? Write `in_progress` or `blocked`. Do not work around the refusal. **Measured caveat:** the guard accepts `--evidence` *or* an already-stored `verification_evidence`, so a task that carried evidence from an earlier flip can be re-set to `done` with none — stale evidence rubber-stamps new work. Pass fresh evidence every time.
2. **Re-render.** `python3 $S/artifacts.py tasks render --root .` — rewrites `TASKS.md` from `.devloop/tasks.jsonl` and refuses an invalid JSONL, naming the errors. `TASKS.md` is generated; never hand-edit it.
3. **Park the work.** `mkdir -p .devloop/run-handoff-$(date +%Y%m%d-%H%M%S)` then `git diff HEAD > .devloop/run-<stamp>/<task-id>.patch`, then `git status --porcelain -uall`. Measured coverage: `git diff` carries tracked-unstaged only, `git diff HEAD` adds staged, and **untracked files are in neither** — list them and name them in the ledger, or the next session restores the patch and loses them. Exclude run dirs narrowly (`.devloop/run-*/` in `.git/info/exclude`), **never `.devloop/` wholesale**: `LEDGER.md` and `tasks.jsonl` live there and are the handoff itself.
4. **Append the ledger.** `python3 $S/adapters.py ledger --root . --status "<partial|blocked|budget|converged_stuck|halted|done>" --objective "<what this session was for>" --done "<proven, with the proving command>" --next "<the exact first command next session runs>" --blockers "<who/what is waited on>" --unverified "<claimed but not measured>"`. `--status` and `--objective` are required (missing ⇒ argparse exit 2); the other four are optional and omitted ones are written as `-`, so a partial call is still well formed. The entry appends **newest last** under a heading stamped with `git rev-parse --short HEAD` — pinned to a commit, not a remembered one. Each field is one markdown list item: keep values single-line. With no commits (or outside a repo) the commit field is written **empty** and git prints `fatal: not a git repository` to stderr while the command still exits 0 — an entry with a blank commit is unanchored; say so.

## `--unverified` is the point

It takes **content — what was claimed but not measured** — never a count. "The retry path was never exercised; no test covers it." "The fix is asserted from reading the code; the failing reproduction was never re-run." A number of dirty paths is a proxy, and a proxy lets an unproven claim travel another session as fact. `-` means nothing outstanding — not "did not check".

The plugin's `PreCompact` hook (`hooks/hooks.json` → `hooks/pre-compact.sh`) calls this same `adapters.py ledger`, but writes a **stub**: `--done "see git log -5"`, `--unverified` a *count* of dirty paths. It is Claude-Code-only — `install.sh` installs skills and shims, never hooks — so the other six harnesses have no such hook. That automatic entry is a floor, not a substitute.

## Not /ship

`/ship` merges a finished branch into trunk and writes `CHANGELOG.md` for humans reading releases, only after `/review` passed. `/handoff` is the unfinished case and merges nothing.

Return: the task id and new status, the refusal text if `done` was refused, the patch path and the untracked files it does not contain, the ledger heading line written (date · commit · status), and the `--unverified` value verbatim.
