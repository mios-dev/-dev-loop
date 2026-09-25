#!/bin/sh
# SessionStart: inject the constitution pointer, last ledger entry, and unblocked tasks (stdout becomes context)
R=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
[ -f "$R/AGENTS.md" ] && printf 'dev-loop: project constitution is %s/AGENTS.md (read it before acting).\n' "$R"
[ -f "$R/.devloop/LEDGER.md" ] && { printf '\n## Last dev-loop ledger entry\n'; awk '/^## /{b=""} {b=b $0 "\n"} END{printf "%s", b}' "$R/.devloop/LEDGER.md" | tail -n 12; }
[ -f "$R/.devloop/tasks.jsonl" ] && command -v python3 >/dev/null && { printf '\n## Unblocked tasks\n'; python3 "${CLAUDE_PLUGIN_ROOT:-$(dirname "$0")/..}/skills/dev-loop/scripts/artifacts.py" tasks next --root "$R" 2>/dev/null | head -10; }
# Cloud sessions: agy keeps its credential in a keyring whose daemon is a process, so it is gone on
# every cold start while agy itself survives in the environment snapshot. Revive it and hand its bus
# address to every later tool call through CLAUDE_ENV_FILE, whatever repo the session is in.
if [ "${CLAUDE_CODE_REMOTE:-}" = true ] && [ -x "$HOME/.local/bin/agy" ] && [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  K="${CLAUDE_PLUGIN_ROOT:-$(dirname "$0")/..}/skills/dev-loop/scripts/env/agy-keyring.sh"
  KE="${AGY_CLOUD_DIR:-$HOME/.config/agy-cloud}/keyring.env"
  [ -r "$K" ] && (. "$K") >/dev/null 2>&1 && [ -r "$KE" ] && cat "$KE" >> "$CLAUDE_ENV_FILE"
fi
exit 0
