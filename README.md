# dev-loop — universal autonomous engineering loop (v7.1.0)

One repo, three things:

1. **A Claude Code plugin** — `.claude-plugin/plugin.json`, seven skills (`/dev-loop`, `/goal`, `/research`, `/review`, `/ship`, `/triage`, `/websearch`), five agents (`orchestrator`, `lane-worker` in an isolated worktree, `auditor`, `triage`, `researcher`), and enforcement hooks.
2. **A portable skill set** (Agent Skills open standard) plus thin command shims for Antigravity, Gemini CLI, Codex, Copilot, Cursor, OpenCode, Hermes-Agent — installed by `skills/dev-loop/scripts/install.sh` / `.ps1`.
3. **An MCP server** (`skills/dev-loop/scripts/devloop_mcp.py`, registered by `.mcp.json`) so any MCP-capable host drives the orchestrator: `validate_lanes`, `run_lanes`, `gate`, `report`, `tasks_next`, `task_set`, `ledger`, `scaffold`, `probe`.
4. **Harness-neutral glue** in `skills/dev-loop/scripts/`: `adapters.py` (9 lane harnesses, gates, probe, ledger), `devloop.sh` / `DevLoop.ps1` (worktree lane orchestrators), `artifacts.py` (AGENTS.md, GOALS, ROADMAP, MADR ADRs, tasks.jsonl → TASKS.md, DoD, checklists, CHANGELOG, ledger), `goal.py`, `research.py`, `review.py`, `ship.py`, `triage.py`, `devloop_worker.py` (OpenAI-compatible worker), `contracts.py` (cross-lane interface exchange), `verify_harness.py`; docs in `references/`, schemas/templates in `assets/` (agentskills.io layout).

## Install

```sh
# Claude Code (plugin — recommended)
claude plugin marketplace add /path/to/dev-loop        # or a git URL
claude plugin install dev-loop@dev-loop-marketplace     # commands appear as /dev-loop:goal etc.
# local dev:  claude --plugin-dir /path/to/dev-loop

# Everything else (and Claude Code skills-only fallback), project scope, plus the canonical artifacts
sh skills/dev-loop/scripts/install.sh --all --scaffold
pwsh skills/dev-loop/scripts/install.ps1 -All -Scaffold
```

Required Claude Code settings: `"worktree": {"baseRef": "head"}`; version ≥ 2.1.219. Run `python3 skills/dev-loop/scripts/adapters.py probe` after installing or upgrading any harness CLI.

## Conformance
`sh skills/dev-loop/scripts/validate.sh` — agentskills.io validator on every skill (sub-skills as the six-key copies other harnesses receive), plugin/hook/agent shapes, schemas, syntax, and `claude plugin validate --strict` when the CLI is present. Details and sources: `skills/dev-loop/references/conformance.md`.

## Use

- `/dev-loop <objective>` — one task through the loop. `/dev-loop lanes:<lanes.json>` — parallel lanes in any mix of harnesses (schema: `assets/lane-schema.json`, example: `assets/lanes.example.json`).
- `/goal dev <objective>` — define stopping conditions, decompose into tasks, iterate until `goal.py eval` passes.
- `/research …` → `/dev-loop …` → `/review` → `/ship <branch>`; `/triage <failing cmd>` before touching code.

Any harness can be the host; any harness can run a lane (`references/harness-adapters.md`). State lives on disk (`.devloop/`), never in the context window (`references/artifacts.md`).

## Cloud environment: Google Antigravity in Claude Code on the web

This repo provisions Google Antigravity's CLI (`agy`) inside its Claude Code on the web
container. The SessionStart hook (`.claude/settings.json` → `.claude/hooks/session-start.sh`)
runs `environment/setup-antigravity.sh` on every remote session: it installs `agy` (official
installer → `~/.local/bin`), the keyring stack (`dbus`, `gnome-keyring`, `libsecret-tools`) that
lets the one-time login persist for the container's life, and the dev-loop skill into
Antigravity's user-scope skill/workflow directories.

One-time per container (there is no non-interactive Antigravity auth):

```sh
bash environment/agy-login.sh          # prints a Google authorization URL — open it in YOUR browser
bash environment/agy-doctor.sh --probe # verifies binary, keyring round-trip, and authenticated headless run
```

`agy-login.sh --tmux` runs the login inside a `tmux` session so an agent can capture the URL for
you and relay your responses. Containers are ephemeral: a brand-new container needs the login
again. The keyring is empty-password (credential recoverable by anyone with container access) —
acceptable for a single-user ephemeral session only.

## AGY as manager (topology A, this repo's default)

`AGENTS.md` (the constitution — law in every harness) makes Antigravity the L0 manager of all
dev-loop sub-agents in this repo. It dispatches any mix of lanes, including **multiple
concurrent Antigravity lanes** (separate `agy -p` processes) **and multiple concurrent Claude
Code lanes** (`claude -p`), each in its own git worktree with its own two-sided gate:

```sh
python3 skills/dev-loop/scripts/adapters.py probe                     # flags drift monthly — check first
sh skills/dev-loop/scripts/agy_host.sh my-lanes.json                  # interactive manager
sh skills/dev-loop/scripts/agy_host.sh my-lanes.json --headless       # unattended manager (JSON out)
```

Mixed-lane example: `skills/dev-loop/assets/lanes.agy-manager.example.json` (2 AGY lanes +
2 Claude Code lanes + an AGY auditor). The manager runs every merge gate itself; lanes never
commit, and a lane whose negative control passes is never merged.
