# AGENTS.md — constitution for this repository

Canonical contract file. `CLAUDE.md`, `GEMINI.md`, and `.agent/rules/00-agents.md` are pointers
to this file; loaders differ, so those files must stay pointers. Per the dev-loop skill
(`skills/dev-loop/SKILL.md` §0), this file is law: where it and the skill disagree, this file wins.

## What this repository is

The `dev-loop` plugin/skill set (see `README.md`), plus a cloud-environment layer (`environment/`)
that provisions Google Antigravity's CLI (`agy`) inside Claude Code on the web containers.

## Orchestration topology (binding)

- **L0 host / manager: Antigravity (`agy`).** All multi-lane dev-loop runs launched from this
  repository default to topology A of `skills/dev-loop/references/harness-adapters.md` §3 — AGY
  is the manager of all sub-agents. Launch it with
  `sh skills/dev-loop/scripts/agy_host.sh <lanes.json>`.
- **Lanes: any mix, multiple instances allowed.** Multiple concurrent Antigravity lanes
  (separate `agy -p` processes) and multiple concurrent Claude Code lanes (`claude -p`) may run
  side by side; other harnesses stay available. Every lane keeps the dev-loop lane contract:
  exclusive `owned_paths`, its own two-sided gate, no `git add/commit/push`, no edits to this file.
- **The manager is the only writer to shared state** (`AGENTS.md`, `.devloop/`, merges). Lanes
  report `contract_updates`; the manager writes them here.
- **Fallback:** when `agy` is unavailable or unauthenticated, a Claude Code session may host the
  run (topology B) but must say so in its report; it does not silently become the standing manager.
- Reference example for a mixed AGY + Claude Code run:
  `skills/dev-loop/assets/lanes.agy-manager.example.json`.

## Cloud environment (Claude Code on the web)

- `bash environment/setup-antigravity.sh` — idempotent provisioning (also run by the
  SessionStart hook in `.claude/settings.json`).
- `bash environment/agy-login.sh` — one-time interactive Google sign-in per container
  (`--tmux` when an agent drives it). Headless `agy -p` needs this done first.
- `bash environment/agy-doctor.sh [--probe]` — health/auth verification.
- The keyring holds the AGY credential unencrypted-at-rest (empty-password keyring) — accepted
  for ephemeral single-user containers only. Never print or export the credential.

## Working rules

- Follow `skills/dev-loop/SKILL.md`: DoD before code, two-sided verification, explicit-path
  staging only (never `git add -A`), secrets scan before commit, ledger entry before ending.
- Gates for changes to this repo: `sh skills/dev-loop/scripts/validate.sh` must pass;
  shell edits get `bash -n` / `sh -n`; JSON edits must `json.load`.
- Harness CLI flags drift monthly: run `python3 skills/dev-loop/scripts/adapters.py probe`
  before relying on any lane command template.
