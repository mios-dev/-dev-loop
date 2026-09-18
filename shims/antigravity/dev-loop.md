---
description: Run the Dev Loop (verify-hard, two-sided controls, worktree lanes) on an objective. Antigravity may host lanes run by Antigravity subagents, Claude Code, Codex, Gemini CLI, or any OpenAI-compatible worker.
---
Load the `dev-loop` skill from `.agent/skills/dev-loop/SKILL.md` (or the global skills dir) and execute its lifecycle (§1) for the objective given after this command.

Orient first: `AGENTS.md`, the last entry of `.devloop/LEDGER.md`, `TASKS.md`; if the canonical artifacts are missing run `python3 scripts/artifacts.py scaffold` (§3). Flip the task in `.devloop/tasks.jsonl` and append a ledger entry before you stop.
1. Write the Definition of Done (§2) into the Implementation Plan artifact AND the repo's own plan file (§3).
2. Track work in the Task List artifact; the repo doc is the record.
3. Run both controls before claiming done (§6); put the exact commands and outputs in the Walkthrough.
4. Explicit-path staging only; never `git add -A` (§12).
5. Parallel work: read `references/harness-adapters.md` §3 (topology A — you are the manager of all sub-agents). Same-vendor lanes → `invoke_subagent` with `workspace: branch`, each given the lane prompt and its `owned_paths` — or, for several concurrent Antigravity lanes, list them as `harness: antigravity` in `lanes.json` so each runs as its own `agy -p` process (needs cached credentials — a live keyring). Cross-vendor lanes (Claude Code, Codex, Gemini CLI, OpenAI-compatible) → run `sh scripts/devloop.sh <lanes.json>` (or `pwsh scripts/DevLoop.ps1 -Lanes <lanes.json>`) with terminal policy "Proceed in Sandbox" and `claude`/`codex`/`gemini`/`agy`/`python3`/`git` on the Allow list; watch with `/tasks`; collect `.devloop/run-*/report-*.json`. Mixed multi-AGY + multi-Claude example: `assets/lanes.agy-manager.example.json`; unattended manager launch: `sh scripts/agy_host.sh <lanes.json> --headless`.
6. End with the `devloop_report` JSON block (§13).
