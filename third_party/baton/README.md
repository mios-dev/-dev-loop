<p align="center"><img src="assets/logo.svg" width="200" /></p>

<h1 align="center">Baton</h1>

An autonomous coding agent orchestrator that polls GitHub Issues, creates isolated git worktrees, and runs Claude Code CLI against each issue — hands-free.

Inspired by [OpenAI's Symphony spec](https://github.com/openai/symphony/blob/main/SPEC.md), rebuilt from scratch for Claude Code.

## How It Works

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

Baton runs **project-local** — one instance per repo, started from the project directory. It polls GitHub Issues matching your configured filters, spins up isolated git worktrees, and lets Claude Code work on each issue autonomously with multi-turn retries.

## Quick Start

```bash
# Install
pip install -e .

# Copy the example workflow
cp WORKFLOW.md.example WORKFLOW.md

# Edit WORKFLOW.md to configure labels, concurrency, prompt template, etc.

# Start the orchestrator
baton start
```

## WORKFLOW.md

A single file controls everything — YAML front matter for config, Markdown body for the prompt template:

```yaml
---
tracker:
  kind: github
  labels: ["agent"]
  exclude_labels: ["blocked"]

polling:
  interval_ms: 30000

agent:
  max_concurrent: 3
  max_turns: 5
  command: claude
  permission_mode: acceptEdits
  mcp_servers:
    - name: playwright
      command: npx @playwright/mcp@latest

hooks:
  before_run: |
    git fetch origin main && git rebase origin/main
  timeout_ms: 60000
---

You are an autonomous software engineer working on issue #{{ issue.number }}: {{ issue.title }}.

{{ issue.body }}

When done, commit, push, and create a PR linking to #{{ issue.number }}.
```

### Config Reference

| Key | Default | Description |
|-----|---------|-------------|
| `tracker.kind` | `github` | Issue tracker (currently only GitHub) |
| `tracker.labels` | `[]` | Filter issues by these labels |
| `tracker.exclude_labels` | `[]` | Skip issues with these labels |
| `tracker.assignee` | `null` | Filter by assignee (`@me` for yourself) |
| `polling.interval_ms` | `30000` | Poll interval in milliseconds |
| `agent.max_concurrent` | `3` | Max parallel agents |
| `agent.max_turns` | `5` | Max Claude turns per issue |
| `agent.command` | `claude` | Agent CLI command |
| `agent.permission_mode` | `acceptEdits` | Claude Code permission mode |
| `agent.mcp_servers` | `[]` | MCP servers to pass to Claude |
| `hooks.after_create` | `null` | Run after worktree creation (e.g., `npm install`) |
| `hooks.before_run` | `null` | Run before each agent turn |
| `hooks.after_run` | `null` | Run after each agent turn |
| `hooks.timeout_ms` | `60000` | Hook timeout |

### Prompt Template Variables

| Variable | Description |
|----------|-------------|
| `{{ issue.number }}` | Issue number |
| `{{ issue.title }}` | Issue title |
| `{{ issue.body }}` | Issue body |
| `{{ issue.labels }}` | List of label names |
| `{{ issue.url }}` | Issue URL |
| `{{ attempt }}` | Retry attempt number (null on first run) |

### Per-Issue Skills

Add a `## Skills` section to any issue body to activate additional skills for that issue:

```markdown
## Skills
- playwright
- accessibility-checker
```

## CLI

```bash
# Start the orchestrator
baton start                    # uses ./WORKFLOW.md
baton start -w my-workflow.md  # custom workflow file
baton start -v                 # verbose logging

# Check status
baton status

# Stop
# Ctrl+C in the terminal, or kill the process
baton stop
```

## Architecture

| Module | Purpose |
|--------|---------|
| `symphony/config.py` | WORKFLOW.md YAML parser with typed defaults |
| `symphony/tracker.py` | GitHub Issues client via `gh` CLI |
| `symphony/workspace.py` | Git worktree lifecycle manager |
| `symphony/hooks.py` | Shell hook executor with timeout |
| `symphony/prompt.py` | Jinja2 template renderer |
| `symphony/worker.py` | Claude Code CLI subprocess runner |
| `symphony/state.py` | In-memory state with JSON persistence |
| `symphony/orchestrator.py` | Poll-dispatch-reconcile event loop |
| `symphony/cli.py` | Click CLI entry point |
| `symphony/log.py` | Color-coded terminal logging |

### State Machine

```
Unclaimed → Claimed → Running → RetryQueued → Released
                                     ↑            │
                                     └────────────┘
```

- **PR created:** Release claim immediately, move to next issue
- **Normal exit (no PR):** 1s retry delay (continuation check)
- **Error exit:** Exponential backoff (10s, 20s, 40s... up to configured max)
- **Issue closed:** Release claim + clean up worktree

## Real-World Example: Building a Todo App

We tested Baton by having it autonomously build a complete todo app from scratch. We created 3 GitHub Issues, ran `baton start`, and walked away. Here's what happened:

**Setup:**
```bash
mkdir todo-app && cd todo-app && git init
gh repo create todo-app --public --source=. --push
gh label create baton --color "6366f1"
```

**Created 3 issues labeled `baton`:**
1. Create basic todo app HTML structure
2. Add JavaScript to create and delete todos
3. Add localStorage persistence

**WORKFLOW.md with [agent-browser](https://github.com/vercel-labs/agent-browser) verification:**
```yaml
---
tracker:
  kind: github
  labels: [baton]
agent:
  max_concurrent: 1
  max_turns: 3
  command: claude
  permission_mode: bypassPermissions
---

You are an autonomous software engineer working on issue #{{ issue.number }}: {{ issue.title }}.

{{ issue.body }}

## Verification (REQUIRED before creating PR)

Use agent-browser to verify your work:
  agent-browser open http://localhost:3456
  agent-browser snapshot -i
  agent-browser click, fill, type to test interactions

If verification fails, fix the issues before proceeding.
```

**Result:** Baton picked up each issue sequentially, created isolated worktrees, wrote the code, launched a local server, used agent-browser to visually verify the acceptance criteria, then committed, pushed, and opened PRs — all without human intervention.

Each PR included verification results in the description:

> **Verification with agent-browser**
> - Opened `http://localhost:3456` and confirmed the page renders correctly
> - Took screenshot verifying centered card layout with styled input and button
> - Ran `agent-browser snapshot -i` confirming interactive elements: textbox and button

3 issues created. 3 PRs opened and merged. Zero manual coding.

## Requirements

- Python 3.11+
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) (`claude`)
- [GitHub CLI](https://cli.github.com/) (`gh`) — authenticated
- Git

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## Blog Post

Read the full write-up on how and why Baton was built: [I Built an Orchestrator That Watches GitHub Issues and Sends Agents to Fix Them](https://mraza007.github.io/blog/building-baton-autonomous-agent-orchestrator)

## License

MIT
