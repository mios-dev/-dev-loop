---
tracker:
  kind: github
  labels:
    - agent
  exclude_labels:
    - blocked
  assignee: "@me"

polling:
  interval_ms: 15000

agent:
  max_concurrent: 2
  max_turns: 3
  max_retry_backoff_ms: 60000
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
    git fetch origin main
  timeout_ms: 30000
---

You are working on issue #{{ issue.number }}: {{ issue.title }}

{{ issue.body }}

When done, commit, push, and create a PR.
