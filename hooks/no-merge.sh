#!/bin/sh
# PreToolUse(mcp): the monitor and managers never merge; the operator merges (AGENTS.md, operator 2026-09-26)
. "$(dirname "$0")/_lib.sh"; IN=$(cat); TOOL=$(json_get "$IN" .tool_name)
echo "$TOOL" | grep -Eq '^mcp__.+__(merge_pull_request|enable_pr_auto_merge|update_pull_request_branch)$' \
  && deny "dev-loop: $TOOL is a merge path; the operator merges (AGENTS.md). Leave the PR ready for review."
exit 0
