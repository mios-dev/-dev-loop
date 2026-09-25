---
description: Work the task ledger — list what is unblocked now, add a task with its acceptance check and both controls, flip a status with cited evidence, validate, re-render TASKS.md, emit a lane
argument-hint: [next|add|set|validate|render|lane] [args]
---

# /backlog: The Task Ledger

Input: `$ARGUMENTS` — a mode (`next` | `add` | `set` | `validate` | `render` | `lane`) plus its arguments. Default mode: `next`.

Below, `$S` = the dev-loop `scripts/` directory (`<skills dir>/dev-loop/scripts/`). Every command takes `--root .`.

Task state is the repository's memory across sessions. It lives on disk in `.devloop/tasks.jsonl` (one JSON object per line), never in the context window. `TASKS.md` is a **rendered view** — hand-editing it loses the edit on the next render.

## Modes

1. **`next`** — `python3 $S/artifacts.py tasks next --root .`
   Prints `<id>  <title>` for each task that is `open`, is not an `epic`, and has every `depends_on` already `done` or `cancelled`. When nothing qualifies it prints `(nothing ready — check blocked/in_progress tasks and the ledger)` — that is an answer, not an error. **Run this first in a fresh session, right after reading the last `.devloop/LEDGER.md` entry.**

2. **`add`** — the definition of done, written before the code:
   ```sh
   python3 $S/artifacts.py tasks add --root . --id T-0NN --title "..." \
     --ac "WHEN <trigger> THE SYSTEM SHALL <observable behaviour>" \
     --positive "<check that must PASS when the work is correct>" \
     --negative "<plant the defect, run the same check, restore the tree, exit non-zero>" \
     --expect "<regex the negative output must match>" \
     [--type task|epic|bug] [--epic ID] [--goal ID] [--depends T-001,T-002] [--owner NAME]
   ```
   `--id` must match `^[A-Z]+-\d+$`; the task starts `open`. `--ac` is **repeatable** (once per criterion, EARS form). The tool refuses a duplicate id, an unknown `--depends`, and an unknown `--epic`. **It does NOT refuse a task with no acceptance criterion or no controls — you must.** A task added without them can never be proven done, and `tasks lane` will hand back the literal `<fill>`.

3. **`set`** — `python3 $S/artifacts.py tasks set <id> <status> --root . [--evidence "..."]`
   Vocabulary: `open` | `in_progress` | `blocked` | `done` | `cancelled`; anything else exits 1 naming the five. **`done` is refused without `--evidence`** (unless the task already carries `verification_evidence`). That refusal is the feature — do not route around it by hand-editing the JSONL. Evidence cites *both* controls: the exact positive command and its result, and the exact negative command with the line showing it failing for the planted reason. "Tests pass" is not evidence.

4. **`validate`** — `python3 $S/artifacts.py tasks validate --root .`
   Ids unique and well-shaped; `status` and `type` in vocabulary; every `depends_on` and `epic` resolving; no dependency cycles; every `done` task carrying evidence. Prints `tasks.jsonl ok: N tasks`, or exits 1 listing each problem.

5. **`render`** — `python3 $S/artifacts.py tasks render --root .`
   Validates first and **refuses to render an invalid file**; fix what `validate` reports rather than editing the output. Writes `TASKS.md` grouped by epic, `- [x]` done / `- [-]` cancelled / `- [ ]` otherwise, with `**[blocked]**` markers, `@owner`, `← dependencies`, and an `N/M done` footer. Run after any `add` or `set`.

6. **`lane`** — `python3 $S/artifacts.py tasks lane <id> --root .`
   Prints a v2 lane object to **stdout** (there is no `--out` — redirect it): `id`, `task_id`, `objective` (title + acceptance criteria), `owned_paths`, the three control fields, `depends_on`. `owned_paths` always returns `["<fill: exclusive globs>"]` — you fill in the exclusive globs this lane may write. **Any control field returned as the literal `<fill>` means the task defines no control: STOP and ask. Never invent a negative control nobody defined.** Feed the completed object to `/verify`, or collect several into a `lanes.json` for `/dev-loop`.

## Both controls, always

A check that cannot fail passes identically on correct and on broken code. Every task therefore carries a **positive control** (it works) AND a **negative control** (plant the defect; the same check must fail, *naming what you planted*, and the tree must be restored). Prefer an organic `--expect`: mutate real code and match the tool's own error. Only where nothing mutates naturally, plant exactly `DEVLOOP-PLANTED-<LANE_ID>`, one unique sentinel per task — a shared sentinel lets either task satisfy the other's gate, and an expect string that also appears in the fixture's own filename passes whether or not the plant landed.

## Boundaries

- Not `/goal`: `/goal` owns the objective, its stopping conditions and the eval loop, and decomposes a goal into tasks at definition time. `/backlog` is the day-to-day ledger afterwards.
- The dev loop already flips a task's status on a successful merge; `/backlog` covers everything outside that path.
- `/backlog` never runs `git add`, `git commit` or `git push`. It writes `.devloop/tasks.jsonl` and `TASKS.md` only.

Return the exact command run, its output, and — for `set <id> done` — the two cited controls.
