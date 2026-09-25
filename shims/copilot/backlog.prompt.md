---
name: backlog
description: Work the task ledger — what is unblocked now, add a task with its acceptance check and both controls, flip status with cited evidence, validate, re-render TASKS.md, emit a lane
version: 1.0.0
---

# GitHub Copilot /backlog Workflow

Task state is the repository's memory across sessions. It lives in `.devloop/tasks.jsonl` (one JSON object per line), never in the context window. `TASKS.md` is a **rendered view** — hand-editing it loses the edit on the next render.

`$S` = the dev-loop `scripts/` directory. Every command takes `--root .`. Mode comes from the first argument; default `next`.

1. **`next`** — `python3 $S/artifacts.py tasks next --root .` prints `<id>  <title>` for each task that is `open`, is not an `epic`, and has every `depends_on` already `done` or `cancelled`. `(nothing ready — check blocked/in_progress tasks and the ledger)` is an answer, not an error. Run this first in a fresh session, right after the last `.devloop/LEDGER.md` entry.

2. **`add`** — `python3 $S/artifacts.py tasks add --root . --id T-0NN --title "..." --ac "WHEN … THE SYSTEM SHALL …" --positive CMD --negative CMD --expect REGEX [--type task|epic|bug] [--epic ID] [--goal ID] [--depends a,b] [--owner NAME]`. `--id` must match `^[A-Z]+-\d+$`; the task starts `open`. `--ac` is repeatable, once per criterion. The tool refuses a duplicate id, an unknown `--depends` and an unknown `--epic` — but it **accepts** a task with no acceptance criterion and no controls, so refuse that yourself: the definition of done is written *before* the code, and a task without it can never be proven done (`tasks lane` will return the literal `<fill>`).

3. **`set`** — `python3 $S/artifacts.py tasks set <id> <status> --root . [--evidence "..."]`. Vocabulary `open | in_progress | blocked | done | cancelled`; anything else exits 1 naming the five. **`done` is refused without `--evidence`** unless the task already carries `verification_evidence` — that refusal is the feature; never route around it by editing the JSONL. Evidence cites both controls: the exact positive command and its result, and the exact negative command with the line showing it failing for the planted reason. "Tests pass" is not evidence.

4. **`validate`** — `python3 $S/artifacts.py tasks validate --root .`: ids unique and well-shaped, status/type vocabulary, `depends_on` and `epic` resolvable, no cycles, every `done` task carrying evidence. Prints `tasks.jsonl ok: N tasks` or exits 1 listing each problem.

5. **`render`** — `python3 $S/artifacts.py tasks render --root .` validates first and **refuses to render an invalid file**. Writes `TASKS.md` grouped by epic with `- [x]` / `- [-]` / `- [ ]` boxes, `**[blocked]**` markers, `@owner`, `← dependencies`, `N/M done` footer. Run after any `add` or `set`.

6. **`lane`** — `python3 $S/artifacts.py tasks lane <id> --root .` prints a v2 lane object to **stdout** (no `--out`; redirect it): `id`, `task_id`, `objective`, `owned_paths`, the three control fields, `depends_on`. `owned_paths` always comes back as `["<fill: exclusive globs>"]` — you supply the exclusive globs. A control field returned as the literal `<fill>` means the task defines no control: **stop and ask; never invent a negative control nobody defined.** Feed the result to `/verify`, or collect several into a `lanes.json` for `/dev-loop`.

**Both controls, always.** A check that cannot fail passes identically on correct and on broken code. Every task carries a positive control (it works) and a negative control (plant the defect; the same check must fail *naming the plant*, tree restored). Prefer an organic expect string — mutate real code, match the tool's own error. Only where nothing mutates naturally, plant exactly `DEVLOOP-PLANTED-<LANE_ID>`, one unique sentinel per task; a shared sentinel lets either task satisfy the other's gate, and an expect string that also appears in the fixture's own filename passes whether or not the plant landed.

**Boundaries.** Not `/goal` — `/goal` owns the objective, its stopping conditions and the eval loop, and decomposes a goal into tasks at definition time; `/backlog` is the day-to-day ledger afterwards. The dev loop already flips status on a successful merge. `/backlog` never runs `git add`, `git commit` or `git push`.

Return the exact command run, its output, and — for `set <id> done` — the two cited controls.
