---
name: handoff
description: End a session on disk instead of in prose - flip the task with evidence, park uncommitted work as a patch, and append a ledger entry pinned to HEAD that states what is still unverified. Wraps `artifacts.py tasks set/render` and `adapters.py ledger` so the next session starts from files rather than from a remembered summary, in any harness. Use when stopping with work unfinished - budget exhausted, blocked, converged-stuck, context nearly full, or simply ending the session. Never merges, commits or pushes.
argument-hint: "[task-id] [status note]"
allowed-tools: Read, Grep, Glob, Bash
---
# /handoff — end the session on disk (SKILL §1.1, §11, §12)

_Paths: `${CLAUDE_SKILL_DIR}/../dev-loop/scripts/` resolves in Claude Code; in other harnesses use `<skills dir>/dev-loop/scripts/` (the shims in `shims/<harness>/` already do)._ Below, `$S` = that scripts directory.

`$ARGUMENTS` is a task id and a free-text status note; either may be empty.

The loop's first step (§1.1 Orient) reads `AGENTS.md`, **the last `.devloop/LEDGER.md` entry**, `TASKS.md` and recent history. This command is what writes those. A session that ends without it hands the next one a stale board and no record of what was claimed but never measured — the next session then re-derives, or worse, trusts a `done` nobody proved.

**This command never merges, commits, pushes, or runs `git add`.** It is for stopping with work *unfinished*, which is the common case.

## Run these four, in this order

### 1. Flip the task — the tool refuses an unproven `done`

```sh
python3 $S/artifacts.py tasks set <T-0NN> <status> --root . --evidence "pos: <cmd> -> passed; neg: <plant> -> <cmd> failed naming <expect>"
```

`<status>` ∈ `open · in_progress · blocked · done · cancelled` (anything else: `status must be one of [...]`, exit 1). An unknown id: `no task <id>`, exit 1.

`done` without evidence is refused — measured output, exit 1:

```
done requires --evidence (both controls, exact commands)
```

That refusal is the §6 rule in code: a check that cannot fail passes identically on correct and on broken code, so `done` means a **positive** control passed *and* a **negative** control failed naming the plant. If you cannot cite both, the honest status is `in_progress` or `blocked`. **Do not work around the refusal** — and note the one way it can be worked around by accident:

> **Measured caveat.** The guard is `--evidence` *or* an already-stored `verification_evidence`. A task that carried evidence from an earlier flip can be set back to `done` with no `--evidence` and no refusal — stale evidence rubber-stamps new work. Pass fresh `--evidence` on every flip.

### 2. Re-render the board

```sh
python3 $S/artifacts.py tasks render --root .
```

Rewrites `TASKS.md` from `.devloop/tasks.jsonl`; it refuses to render an invalid JSONL and names the errors. `TASKS.md` is generated — never hand-edit it, or step 2 silently discards your edit next time.

### 3. Park uncommitted work as a patch (§11)

```sh
mkdir -p .devloop/run-handoff-$(date +%Y%m%d-%H%M%S)
git diff HEAD > .devloop/run-<stamp>/<task-id>.patch
git status --porcelain -uall
```

**Know what the patch does and does not carry** (measured): `git diff` captures tracked-and-unstaged changes only; `git diff HEAD` also captures staged ones; **untracked files appear in neither**. List them from `git status --porcelain -uall` and name them in the ledger, or the next session restores a patch and quietly loses the new files.

Keep run directories out of the index with the narrow exclude `.devloop/run-*/` in `.git/info/exclude` — **never `.devloop/` wholesale**: `.devloop/LEDGER.md` and `.devloop/tasks.jsonl` are the handoff itself and are meant to be tracked.

No `git add`, no `git add -A`, no `commit`, no `push`. Parked is not lost; committed-without-a-report is (§11).

### 4. Append the ledger entry

```sh
python3 $S/adapters.py ledger --root . \
  --status "<partial|blocked|budget|converged_stuck|halted|done>" \
  --objective "<what this session was for>" \
  --done "<what is proven, with the command that proves it>" \
  --next "<the exact first command the next session should run>" \
  --blockers "<what is waiting on whom, or '-'>" \
  --unverified "<what was claimed but not measured>"
```

`--status` and `--objective` are **required** (argparse errors with exit 2 if missing); the other four are optional and any you omit are written as `-`, so a partial call is still well formed. The entry is appended **newest last** under a heading stamped with `git rev-parse --short HEAD`, so it is pinned to a commit rather than a remembered one:

```
## 2026-01-01 09:15 · 9ca8e1b · partial
- objective: …
- done: …
- next: …
- blockers: …
- unverified: …
```

Each field becomes one markdown list item — keep every value to a single line. In a repo with no commits (or outside a repo) the commit field is written **empty** and git prints `fatal: not a git repository` to stderr while the command still exits 0; an entry with a blank commit field is unanchored, so say so rather than treating it as pinned.

## 5. `--unverified` is the point of the whole command

It takes **content — what was claimed but not measured** — not a count. Write the specific claim and why it is unproven: *"the retry path was never exercised — no test covers it"*, *"the fix is asserted from reading the code; the failing reproduction was never re-run"*. §7 calls the alternative Measuring the Wrong Property: a number of dirty paths is a proxy, and proxies let an unproven claim travel one session further as fact.

If everything genuinely was measured, write what the measurement was. `-` means "nothing outstanding" — do not use it to mean "did not check".

### The automatic entry is a floor, not a substitute

This plugin ships one Claude-Code-only `PreCompact` hook (`hooks/hooks.json` → `hooks/pre-compact.sh`), which calls the same `adapters.py ledger` with a **stub**: `--done "see git log -5"` and `--unverified` set to a *count* of dirty paths. `install.sh` installs skills and shims only — never hooks — so the other six harnesses have no such hook at all. A pointer at `git log` is not a statement of what is done, and a count is not a statement of what is unverified. Run this command yourself; a stub entry sitting in the ledger is not evidence that a handoff happened.

## Not /ship

`/ship` merges a finished branch into trunk and writes `CHANGELOG.md` for humans reading releases; it runs only after `/review` passed. `/handoff` is the opposite case — stopping with work unfinished — and merges nothing. If the work is finished and verified, `/ship` it and let step 4 record the result.

## Return

The task id and its new status, the refusal text if `done` was refused, the patch path and the untracked files it does **not** contain, the ledger file and the exact heading line written (date · commit · status), and the `--unverified` value verbatim.
