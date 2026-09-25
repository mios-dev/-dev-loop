---
name: backlog
description: Work the task ledger that carries a repository between sessions - list what is unblocked right now, add a task with its acceptance criterion and both controls written before the code, flip a status with cited evidence, validate the file, re-render TASKS.md, and emit a lane object for /verify or /dev-loop. Wraps `artifacts.py tasks` (next|add|set|validate|render|lane) over `.devloop/tasks.jsonl`. Use at the start of a fresh session to answer "what is ready to work on", whenever a new unit of work is identified, and whenever a task changes state.
argument-hint: "[next|add|set|validate|render|lane] [args]"
allowed-tools: Read, Grep, Glob, Bash
---
# /backlog - the task ledger is the repo's memory across sessions

_Paths: `${CLAUDE_SKILL_DIR}/../dev-loop/scripts/` resolves in Claude Code; in other harnesses use `<skills dir>/dev-loop/scripts/` (the shims in `shims/<harness>/` already do)._ Below, `$S` = that scripts directory, and every command takes `--root .` (the repository root).

State lives on disk in `.devloop/tasks.jsonl` - one JSON object per line - never in the context window. `TASKS.md` is a **rendered view**; editing it by hand loses the edit on the next render. Route on the first word of `$ARGUMENTS`; default `next`.

## next - what is unblocked right now

```sh
python3 $S/artifacts.py tasks next --root .
```

Prints `<id>  <title>` for every task whose status is `open`, whose type is not `epic`, and whose `depends_on` are all `done` or `cancelled`. When nothing qualifies it prints `(nothing ready - check blocked/in_progress tasks and the ledger)` - that is a real answer, not an error: go read the blocked entries and the last ledger entry.

This is the first command of a fresh session, run right after reading the last `.devloop/LEDGER.md` entry.

## add - definition of done before the code

```sh
python3 $S/artifacts.py tasks add --root . --id T-0NN --title "..." \
  --ac "WHEN <trigger> THE SYSTEM SHALL <observable behaviour>" \
  --positive "<command that must PASS when the work is correct>" \
  --negative "<command that plants the defect, runs the same check, restores the tree, exits non-zero>" \
  --expect "<regex the negative output must match>" \
  [--type task|epic|bug] [--epic T-0NN] [--goal G-0NN] [--depends T-001,T-002] [--owner NAME]
```

- `--id` must match `^[A-Z]+-\d+$` (e.g. `T-014`, `BUG-3`). The task is created with status `open`.
- `--ac` is **repeatable** - pass it once per acceptance criterion. Write criteria in EARS form.
- The tool refuses a duplicate id, an unknown `--depends` id, and an unknown `--epic`.
- **The tool does NOT refuse a task with no acceptance criterion or no controls - you must.** Writing the acceptance check and both controls *before* the code is the rule (dev-loop SKILL §2); a task added without them is a task nobody can ever prove done, and `tasks lane` will later hand back the literal `<fill>`.

### The two controls, always both

A check that cannot fail passes identically on correct and on broken code. So every task carries:
- a **positive control** (`--positive`) - the check that must pass once the work is right; and
- a **negative control** (`--negative` + `--expect`) - plant the defect, run the same check, and it must **fail naming the plant**, then restore the tree.

Prefer an **organic** `--expect`: mutate real code and match the tool's own error (a compiler message, an assertion name). Only where the deliverable has no natural mutation - a document, a config - plant a sentinel, and then use exactly `DEVLOOP-PLANTED-<LANE_ID>`, one unique sentinel per task. A sentinel shared between tasks means either one's output satisfies the other's gate; an expect string that also appears in the fixture's own filename passes whether or not the plant landed. Convention enforced by `tests/test_planted_naming.py`.

## set - flip a status, with evidence

```sh
python3 $S/artifacts.py tasks set <id> <status> --root . [--evidence "..."]
```

Vocabulary: `open` | `in_progress` | `blocked` | `done` | `cancelled`. Anything else exits 1 naming the five.

`done` is refused unless `--evidence` is given (or the task already carries `verification_evidence`). That refusal is the feature. **Do not route around it** by hand-editing the JSONL: cite both controls - the exact positive command and its result, and the exact negative command with the line showing it failing for the planted reason. "Tests pass" is not evidence; a check that was never shown to fail proves nothing.

`set` stamps `updated` with today's date.

## validate - is the ledger coherent

```sh
python3 $S/artifacts.py tasks validate --root .
```

Checks: ids unique and well-shaped; `status` in the five-word vocabulary; `type` in `task|epic|bug`; every `depends_on` and `epic` resolving to a real id; no dependency cycles; and every `done` task carrying `verification_evidence`. Prints `tasks.jsonl ok: N tasks`, or exits 1 listing each problem.

## render - regenerate TASKS.md

```sh
python3 $S/artifacts.py tasks render --root .
```

Validates first and **refuses to render an invalid file** - fix what `validate` reports, do not hand-edit the output. Writes `TASKS.md` at the root: grouped by epic (then `## Unassigned`), `- [x]` done, `- [-]` cancelled, `- [ ]` otherwise, with `**[blocked]**` / `**[in_progress]**` markers, `@owner`, `← dependencies`, and an `N/M done` footer. Run it after any `add` or `set`, and commit the result with the change.

## lane - the bridge to verification and parallel work

```sh
python3 $S/artifacts.py tasks lane <id> --root .
```

Prints a v2 lane object to **stdout** (there is no `--out`; redirect it). It carries `id` (the task id lowercased), `task_id`, `objective` (title plus the acceptance criteria), `owned_paths`, the three control fields from the task's `verification` block, and `depends_on`.

- `owned_paths` always comes back as `["<fill: exclusive globs>"]` - **you** fill in the exclusive globs this lane may write, before handing it to a parallel run.
- Any control field that comes back as the literal `<fill>` means the task defines no control. **Stop and ask.** Never invent a negative control nobody defined.

Feed the completed object to `/verify` (`adapters.py gate --lane ...`) for a single task, or collect several into a `lanes.json` for `/dev-loop`.

## staleness - monitor task half-life decay and anchor drift

```sh
python3 $S/artifacts.py tasks staleness --root . [--threshold 0.5]
```

Computes exponential half-life decay ($P_{\text{fresh}} = 2^{-\Delta C / H_C} \cdot 2^{-\Delta T / H_T}$) and broken path anchor penalties. Flags tasks that have crossed the half-life threshold ($S \ge 0.5$).

## reconcile - re-anchor a task to current HEAD

```sh
python3 $S/artifacts.py tasks reconcile <id> --root .
```

Re-anchors the task to current git HEAD, verifies referenced paths, updates timestamps, and resets the staleness score to 0.0.

## archive-stale - lossless rolling backlog preservation

```sh
python3 $S/artifacts.py tasks archive-stale --root . [--threshold 0.5]
```

Losslessly appends expired open tasks to `.devloop/backlog_archive.jsonl` and `.devloop/HISTORICAL_BACKLOG.md` with complete reasoning context, acceptance criteria, and historical notes preserved.

## distill - synthesize archived tasks into permanent documentation

```sh
python3 $S/artifacts.py tasks distill --root .
```

Synthesizes archived tasks into permanent documentation (`docs/distilled/knowledge_distillation.md`), preserving lessons learned and architectural invariants.

## export-openai - strict OpenAI JSON Schema

```sh
python3 $S/artifacts.py tasks export-openai --root .
```

Emits strict OpenAI JSON Schema tool definition (`strict: true`, `additionalProperties: false`, all fields in required array) for OpenAI function calling and Responses API.

## Boundaries

- **Not `/goal`.** `/goal` owns the objective, its stopping conditions and the eval loop, and decomposes a goal into tasks *at definition time*. `/backlog` is the day-to-day ledger afterwards.
- The dev loop already flips a task's status automatically on a successful merge. `/backlog` is for everything outside that path.
- `/backlog` never runs `git add`, `git commit` or `git push`; it edits `.devloop/tasks.jsonl` and `TASKS.md` only.

Return: the exact command run, its output, and - for `set <id> done` - the two cited controls.

