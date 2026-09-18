#!/bin/bash
# Health check for the Antigravity cloud environment. Each check prints PASS,
# WARN, or FAIL with the evidence; exit is non-zero if any FAIL.
#
#   bash environment/agy-doctor.sh           # static checks only (free)
#   bash environment/agy-doctor.sh --probe   # + one real headless agy call
#                                            #   (verifies auth; costs one tiny model turn)
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="$HOME/.local/bin:$PATH"
FAILED=0
pass() { echo "PASS  $*"; }
warn() { echo "WARN  $*"; }
fail() { echo "FAIL  $*"; FAILED=1; }

# 1. binary
if command -v agy >/dev/null 2>&1; then
    pass "agy on PATH: $(command -v agy) ($(agy --version 2>/dev/null | head -1 || echo 'version query failed'))"
else
    fail "agy not on PATH — run: bash environment/setup-antigravity.sh"
fi

# 2. keyring (with a real store/lookup round-trip, not just process presence)
verify_out="$(AGY_KEYRING_VERIFY=1 . "$REPO_ROOT/environment/agy-keyring.sh" 2>&1)"
if printf '%s' "$verify_out" | grep -q 'agy-keyring: OK'; then
    pass "Secret Service keyring alive; store/lookup round-trip succeeded"
else
    fail "keyring not working — auth will not persist; run: bash environment/setup-antigravity.sh (${verify_out:-no output})"
fi

# 3. dev-loop skill visible to Antigravity (user scope)
if [ -f "$HOME/.gemini/config/skills/dev-loop/SKILL.md" ]; then
    pass "dev-loop skill installed for Antigravity: ~/.gemini/config/skills/dev-loop/"
else
    warn "dev-loop skill not in ~/.gemini/config/skills — run: sh skills/dev-loop/scripts/install.sh --harness antigravity --user"
fi

# 4. optional live probe: proves authentication AND the headless JSON envelope
if [ "${1:-}" = "--probe" ] && command -v agy >/dev/null 2>&1; then
    echo "probing headless agy (one small model call)..."
    out="$(timeout 180 agy -p 'Reply with exactly: DEVLOOP-PROBE-OK' --output-format json --print-timeout 2m 2>&1)"
    rc=$?
    status="$(printf '%s' "$out" | jq -r '.status // empty' 2>/dev/null)"
    if [ $rc -eq 0 ] && [ "$status" = "SUCCESS" ]; then
        pass "headless probe: exit 0, status SUCCESS — authenticated and working"
    elif printf '%s' "$out" | grep -qi 'authentication\|not authenticated\|sign in'; then
        fail "headless probe: NOT AUTHENTICATED — run: bash environment/agy-login.sh"
    else
        fail "headless probe: exit $rc, status '${status:-none}'. Output tail: $(printf '%s' "$out" | tail -c 400)"
    fi
fi

exit $FAILED
