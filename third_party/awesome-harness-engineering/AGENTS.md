# AGENTS.md

> Instructions for AI agents contributing to this repository.

## What this repo is

A curated list of resources, patterns, and templates for building reliable AI agent harnesses. The primary artifact is `README.md`.

## Conventions

- All content in `README.md` is in English.
- Each resource entry follows the format: `- [Title](URL) — 1–2 sentence note explaining why it's worth including.`
- Notes should be opinionated: explain *why* the resource matters, not just what it is.
- Do not add resources without a note.
- Sections in `README.md` are organized by the *problem being solved*, not by vendor or model.

## What belongs

Resources that address a specific harness engineering problem:
- Context delivery and compaction
- Tool design and MCP
- Planning artifacts and task decomposition
- Permissions and sandboxing
- Memory and state management
- Verification and evals
- Agent loop structure and orchestration

## What doesn't belong

- General AI/ML papers not specific to agent harnesses
- Model capability benchmarks unrelated to harness design
- Product marketing without technical substance
- Tutorials on using a model (vs. building scaffolding around it)

## Templates

Files in `templates/` are reusable starting points. When editing templates, preserve the comment structure — the comments are the value.

## Verification

Before any PR:
- [ ] All URLs are reachable
- [ ] All entries have a 1–2 sentence explanatory note
- [ ] No section has more than ~10 entries without a clear reason
- [ ] `README.md` renders correctly as Markdown
