# Cursor Rule: The Task Ledger

Defines the `/backlog` protocol: work `.devloop/tasks.jsonl` — the task state that carries a repository between sessions — through `artifacts.py tasks` (`next` | `add` | `set` | `validate` | `render` | `lane`). Lists what is unblocked right now, adds a task with its acceptance criterion and both controls written before the code, flips a status only with cited evidence, validates the ledger, regenerates `TASKS.md`, and emits a lane object for the verification gate, instead of hand-editing a generated file or calling a task done from prose.
