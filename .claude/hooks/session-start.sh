#!/bin/bash
# SessionStart hook for Claude Code on the web: provision the Antigravity CLI
# (agy), keyring, and dev-loop skill install so any session in this repo can
# host or run AGY + Claude Code lanes. Runs only in remote (web) sessions;
# idempotent, so cached containers pass through in a second or two.
set -uo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
    exit 0
fi

if bash "$CLAUDE_PROJECT_DIR/skills/dev-loop/scripts/env/setup-antigravity.sh" --quiet; then
    :
else
    echo "antigravity setup incomplete (see errors above) — run manually: bash skills/dev-loop/scripts/env/setup-antigravity.sh"
fi

exit 0
