# Symphony-CC Design Document

## Overview

Symphony-CC is a Python daemon that polls GitHub Issues, creates git worktrees, and runs Claude Code CLI against each issue autonomously. It's designed to run project-local — one instance per repo, started from the project directory.

## Decisions

- **Language:** Python 3.11+
- **Issue Tracker:** GitHub Issues via `gh` CLI
- **Coding Agent:** Claude Code CLI (`claude -p`)
- **Workspaces:** Git worktrees (`.symphony/worktrees/<issue-number>/`)
- **Scale:** Solo developer, 1-3 concurrent agents
- **Verification:** Agent-driven via MCP servers (Playwright, etc.)
- **Skills:** Defined in WORKFLOW.md + per-issue overrides in issue body
- **Observability:** Terminal output + `symphony status` command via state file

## Architecture

```
WORKFLOW.md → Orchestrator → Worker (per issue)
                  │              │
                  │              ├─ git worktree create
                  │              ├─ hooks (before_run)
                  │              ├─ claude -p "<prompt>"
                  │              ├─ check issue state
                  │              └─ hooks (after_run)
                  │
                  ├─ Poller (gh issue list)
                  ├─ Dispatcher (concurrency control)
                  └─ Reconciler (stale run detection)
```

## WORKFLOW.md Format

```yaml
---
tracker:
  kind: github
  labels: ["agent"]           # optional filter
  exclude_labels: ["blocked"] # optional
  assignee: "@me"             # optional

polling:
  interval_ms: 30000

agent:
  max_concurrent: 3
  max_turns: 5
  max_retry_backoff_ms: 300000
  command: claude
  permission_mode: acceptEdits
  skills:
    - code-reviewer
  mcp_servers:
    - name: playwright
      command: npx @playwright/mcp@latest

hooks:
  after_create: |
    npm install
  before_run: |
    git fetch origin main && git rebase origin/main
  after_run: |
    echo "done"
  timeout_ms: 60000
---

Prompt template with {{ issue.number }}, {{ issue.title }}, {{ issue.body }}, {{ attempt }}
```

## Worker Lifecycle

1. Create/reuse worktree for issue
2. Run after_create hook (if new worktree)
3. Run before_run hook
4. Render prompt via Jinja2
5. Spawn `claude -p` with rendered prompt
6. On exit: check if issue still open
7. If open + turns remaining → continuation turn
8. Run after_run hook
9. Report result to orchestrator

## State Machine

- Unclaimed → Claimed → Running → RetryQueued → Released
- Normal exit: 1s retry delay (continuation check)
- Error exit: exponential backoff (10s, 20s, 40s... up to max)
- Issue closed: release + clean worktree
