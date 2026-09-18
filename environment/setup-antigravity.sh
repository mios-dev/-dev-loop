#!/bin/bash
# Provision this cloud container with everything needed to run Google
# Antigravity's CLI (`agy`) as a dev-loop host and/or lane harness:
#
#   1. OS packages for credential caching (dbus, gnome-keyring, libsecret-tools)
#   2. The Antigravity CLI itself (official installer → ~/.local/bin/agy)
#   3. A running Secret Service keyring (environment/agy-keyring.sh)
#   4. The dev-loop skill + /dev-loop workflow installed into Antigravity's
#      user-scope directories (~/.gemini/config/skills, ~/.gemini/antigravity/workflows)
#   5. PATH / keyring env persisted into $CLAUDE_ENV_FILE for the session
#
# Idempotent and non-interactive: every step no-ops when already satisfied.
# Usage:  bash environment/setup-antigravity.sh [--quiet]
set -euo pipefail

QUIET=0
[ "${1:-}" = "--quiet" ] && QUIET=1
log() { [ "$QUIET" = 1 ] || echo "[antigravity-setup] $*"; }
warn() { echo "[antigravity-setup] WARN: $*" >&2; }

export DEBIAN_FRONTEND=noninteractive GIT_TERMINAL_PROMPT=0 PIP_NO_INPUT=1
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# --- 1. keyring OS packages --------------------------------------------------
missing=()
command -v dbus-daemon         >/dev/null 2>&1 || missing+=(dbus)
command -v gnome-keyring-daemon >/dev/null 2>&1 || missing+=(gnome-keyring)
command -v secret-tool          >/dev/null 2>&1 || missing+=(libsecret-tools)
if [ ${#missing[@]} -gt 0 ]; then
    if command -v apt-get >/dev/null 2>&1; then
        SUDO=""
        [ "$(id -u)" = 0 ] || SUDO="sudo -n"
        log "installing OS packages: ${missing[*]}"
        $SUDO apt-get update -qq || warn "apt-get update failed; attempting install with existing indexes"
        $SUDO apt-get install -y -qq "${missing[@]}" \
            || warn "could not install ${missing[*]} — agy will re-ask for authentication on every launch"
    else
        warn "apt-get not available; skipping keyring packages (${missing[*]})"
    fi
fi

# --- 2. Antigravity CLI (agy) -----------------------------------------------
export PATH="$HOME/.local/bin:$PATH"
if ! command -v agy >/dev/null 2>&1; then
    log "installing the Antigravity CLI from antigravity.google (→ ~/.local/bin/agy)"
    tmpdir="$(mktemp -d)"
    trap 'rm -rf "$tmpdir"' EXIT
    # Download-then-run (never pipe-to-shell) so a truncated transfer fails loudly.
    curl -fsSL --retry 4 --retry-delay 2 https://antigravity.google/cli/install.sh -o "$tmpdir/install.sh"
    [ -s "$tmpdir/install.sh" ] || { echo "[antigravity-setup] ERROR: downloaded installer is empty" >&2; exit 1; }
    bash "$tmpdir/install.sh"
fi
command -v agy >/dev/null 2>&1 || { echo "[antigravity-setup] ERROR: agy still not on PATH after install" >&2; exit 1; }
AGY_VERSION="$(agy --version 2>/dev/null | head -1 || echo 'installed (version query failed)')"
log "agy: $AGY_VERSION"

# --- 3. keyring bootstrap ----------------------------------------------------
# shellcheck source=environment/agy-keyring.sh
if . "$REPO_ROOT/environment/agy-keyring.sh"; then
    log "keyring: Secret Service running (env cached in ~/.config/agy-cloud/keyring.env)"
else
    warn "keyring bootstrap failed — authentication will not persist across launches"
fi

# --- 4. dev-loop skill + /dev-loop workflow into Antigravity (user scope) ----
if sh "$REPO_ROOT/skills/dev-loop/scripts/install.sh" --harness antigravity --user >/dev/null 2>&1; then
    log "dev-loop skill installed for Antigravity (user scope)"
else
    warn "dev-loop skill install for Antigravity reported errors; run it manually: sh skills/dev-loop/scripts/install.sh --harness antigravity --user"
fi

# --- 5. persist session environment -------------------------------------------
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
    grep -qs 'agy-cloud/keyring.env' "$CLAUDE_ENV_FILE" 2>/dev/null || {
        echo 'export PATH="$HOME/.local/bin:$PATH"'
        echo '[ -f "$HOME/.config/agy-cloud/keyring.env" ] && . "$HOME/.config/agy-cloud/keyring.env"'
    } >> "$CLAUDE_ENV_FILE"
fi

# --- status -------------------------------------------------------------------
if [ "$QUIET" = 1 ]; then
    echo "antigravity: $AGY_VERSION — if this container has not been authenticated yet, run: bash environment/agy-login.sh (one-time Google sign-in)"
else
    log "done. Next (one-time per container): bash environment/agy-login.sh"
    log "then verify with:                    bash environment/agy-doctor.sh --probe"
fi
