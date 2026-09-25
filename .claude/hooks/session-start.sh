#!/bin/bash
# SessionStart hook for Claude Code on the web: provision the Antigravity CLI
# (agy), keyring, and dev-loop skill install so any session in this repo can
# host or run AGY + Claude Code lanes. Runs only in remote (web) sessions;
# idempotent, so cached containers pass through in a second or two.
set -uo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
    exit 0
fi

# Unattended /teamwork-preview must receive explicit approval of its draft (its own protocol
# forbids dispatching the team before it). `turbo` is agy's setting for that; an override wins.
export DEVLOOP_AGY_ARTIFACT_REVIEW="${DEVLOOP_AGY_ARTIFACT_REVIEW:-turbo}"
if bash "$CLAUDE_PROJECT_DIR/skills/dev-loop/scripts/env/setup-antigravity.sh" --quiet; then
    :
else
    echo "antigravity setup incomplete (see errors above) — run manually: bash skills/dev-loop/scripts/env/setup-antigravity.sh"
fi

# Fedora userspace: install the wrapper only (a second or two), and only when
# there is none yet. The image builds on first `fedora …` use, so a session that
# never touches it pays nothing. This path exists because a cloud environment's
# Setup script field is not always offered in the environment dialog — the hook
# needs no environment config.
# An existing wrapper is left alone: the environment's own setup script may
# have installed one in projection mode (mios-dev), baked for the runtime that
# holds its image, while this hook runs the setup script with whatever FEDORA_*
# the session exports (generic mode when none) and lets it pick the runtime.
# Rewriting the wrapper here could point it at another image or runtime, so the
# next `fedora` call would rebuild everything from scratch.
# FEDORA_WRAPPER_DIR is honoured here and by the setup script (default
# /usr/local/bin), so a test can point both at a scratch directory.
WRAPPER_DIR="${FEDORA_WRAPPER_DIR:-/usr/local/bin}"
if [ ! -e "$WRAPPER_DIR/fedora" ]; then
    bash "$CLAUDE_PROJECT_DIR/skills/dev-loop/scripts/env/cloud-fedora-setup.sh" --wrapper-only ||
        echo "fedora wrapper not installed — run manually: bash skills/dev-loop/scripts/env/cloud-fedora-setup.sh"
fi

exit 0
