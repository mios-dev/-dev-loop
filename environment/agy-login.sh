#!/bin/bash
# One-time Google sign-in for the Antigravity CLI in this container.
#
# There is no browser here, and Antigravity documents no non-interactive auth:
# you authenticate once in an interactive `agy` session. In a remote/SSH-style
# context agy detects the missing browser and prints an authorization URL —
# open that URL on YOUR machine, sign in with Google, and follow agy's prompts.
# The credential is then cached in the container's keyring (see
# environment/agy-keyring.sh) and every later `agy` / `agy -p` launch — every
# lane, every manager — reuses it for the life of the container.
#
# Usage:
#   bash environment/agy-login.sh            # human at a real terminal: runs agy directly
#   bash environment/agy-login.sh --tmux     # agent-driven: agy runs in tmux session "agy-login"
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="$HOME/.local/bin:$PATH"
command -v agy >/dev/null 2>&1 || { echo "agy not installed — run: bash environment/setup-antigravity.sh" >&2; exit 1; }

# The keyring must be up BEFORE agy runs, or the fresh credential lands nowhere.
# shellcheck source=environment/agy-keyring.sh
. "$REPO_ROOT/environment/agy-keyring.sh"

SESSION=agy-login
if [ -t 0 ] && [ -t 1 ] && [ "${1:-}" != "--tmux" ]; then
    echo "Starting an interactive agy session for authentication."
    echo "It will show an authorization URL — open it in your own browser, sign in, done."
    exec agy
fi

# No TTY (an agent is driving): keep agy alive in tmux so the auth URL can be
# captured and any prompt answered with send-keys.
command -v tmux >/dev/null 2>&1 || { echo "no TTY and no tmux — rerun from a terminal" >&2; exit 1; }
tmux has-session -t "$SESSION" 2>/dev/null || tmux new-session -d -s "$SESSION" -x 220 -y 50 "agy"
sleep 10
echo "----- agy output (tmux session '$SESSION') -----"
tmux capture-pane -pt "$SESSION" -S -200 | sed -e 's/[[:space:]]*$//' | grep -v '^$' || true
cat <<'EOF'
------------------------------------------------
If an authorization URL is shown above: open it in your own browser and sign in.
Drive the session with:
  re-check output:   tmux capture-pane -pt agy-login -S -200
  type into agy:     tmux send-keys -t agy-login '<text>' Enter
  finish & verify:   tmux kill-session -t agy-login && bash environment/agy-doctor.sh --probe
EOF
