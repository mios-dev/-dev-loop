#!/bin/bash
# Health check for the Antigravity cloud environment. Each check prints PASS,
# WARN, or FAIL with the evidence; exit is non-zero if any FAIL.
#
#   bash agy-doctor.sh           # static checks only (free)
#   bash agy-doctor.sh --probe   # + one real headless agy call
#                                #   (verifies auth; costs one tiny model turn)
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PATH="$HOME/.local/bin:$PATH"
FAILED=0
pass() { echo "PASS  $*"; }
warn() { echo "WARN  $*"; }
fail() { echo "FAIL  $*"; FAILED=1; }

# 1. binary
if command -v agy >/dev/null 2>&1; then
    pass "agy on PATH: $(command -v agy) ($(agy --version 2>/dev/null | head -1 || echo 'version query failed'))"
else
    fail "agy not on PATH — run: bash $SCRIPT_DIR/setup-antigravity.sh"
fi

# 2. keyring (with a real store/lookup round-trip, not just process presence)
verify_out="$(AGY_KEYRING_VERIFY=1 . "$SCRIPT_DIR/agy-keyring.sh" 2>&1)"
if printf '%s' "$verify_out" | grep -q 'agy-keyring: OK'; then
    pass "Secret Service keyring alive; store/lookup round-trip succeeded"
else
    fail "keyring not working — auth will not persist; run: bash $SCRIPT_DIR/setup-antigravity.sh (${verify_out:-no output})"
fi

# 3. dev-loop skill visible to Antigravity (user scope)
# Presence is not currency: compare the tree, and say so when this script IS the copy.
AGY_SKILL_COPY="$HOME/.gemini/config/skills/dev-loop"
if [ ! -f "$AGY_SKILL_COPY/SKILL.md" ]; then
    warn "dev-loop skill not in ~/.gemini/config/skills — run: sh $SCRIPT_DIR/../install.sh --harness antigravity --user"
elif [ "$(cd "$SCRIPT_DIR/../.." && pwd)" = "$(cd "$AGY_SKILL_COPY" && pwd)" ]; then
    warn "dev-loop skill present, but this doctor IS the installed copy — currency unverifiable here; re-run from the repo checkout"
elif diff -rq -x __pycache__ -x '*.pyc' "$SCRIPT_DIR/../.." "$AGY_SKILL_COPY" >/dev/null 2>&1; then
    pass "dev-loop skill installed for Antigravity and identical to this checkout: ~/.gemini/config/skills/dev-loop/"
else
    warn "dev-loop skill in ~/.gemini/config/skills DIFFERS from this checkout (stale) — refresh: sh $SCRIPT_DIR/../install.sh --harness antigravity --user"
fi

# 3b. permission grants. Headless agy auto-denies any tool it cannot prompt for, so a
# missing or malformed grant makes every lane do nothing while still reporting SUCCESS.
# `/permissions` is the CLI's own machine-readable view (tab-separated: scope action rule)
# and is the only honest way to see what is ACTIVE: agy silently discards grant strings it
# does not recognise ("unknown action") into its log, so settings.json is not evidence.
if command -v agy >/dev/null 2>&1; then
    [ -f "$HOME/.config/agy-cloud/keyring.env" ] && . "$HOME/.config/agy-cloud/keyring.env"
    grant_err="$(mktemp)"
    grants="$(timeout 120 agy -p '/permissions' --print-timeout 2m 2>"$grant_err")"; grants_rc=$?
    # First non-blank line only, whitespace collapsed, URLs elided and the whole thing capped:
    # agy prints a full OAuth consent URL here whenever a keyring is present, and a 700-char
    # per-invocation URL buries the one sentence that says what is wrong. agy-login.sh is what
    # prints the URL for real, so the diagnosis points there instead of reproducing it.
    grant_diag="$(grep -v '^[[:space:]]*$' "$grant_err" 2>/dev/null | head -1 \
        | sed -e 's#https\{0,1\}://[^[:space:]]*#<auth URL omitted; agy-login.sh prints it>#g' \
        | tr -s '[:space:]' ' ' | cut -c1-200)"
    rm -f "$grant_err"
    missing=""
    # read_file/write_file take a TARGET and do NOT glob over paths: `read_file(/repo/**)`
    # is accepted and then matches nothing. `(*)` is the working universal form. GrepSearch
    # also resolves to read_file, so without it an agent cannot search at all.
    for need in 'read_file(*)' 'write_file(*)' 'command(sh)' 'command(git)' 'command(python3)'; do
        printf '%s' "$grants" | grep -qF "$need" || missing="$missing $need"
    done
    # Empty output has TWO causes that need OPPOSITE remedies, and the only things that tell
    # them apart are the exit status and stderr -- both of which this check used to discard.
    # `/permissions` prints one record per active rule, so nothing printed CAN mean nothing is
    # granted; but it prints nothing just the same when the CLI never ran at all
    # (unauthenticated, crashed, timed out), and agy then exits non-zero and names its own
    # remedy on stderr. Throwing both away turned "could not ask" into a confident "nothing is
    # granted" and sent the operator to setup-antigravity.sh, which rewrites grants that were
    # already correct and therefore changes nothing, while the actual remedy went unnamed.
    # Measured in a cloud container (agy 1.2.7): 22 grants written, stdout empty, exit 1,
    # stderr "Error: authentication required. Run 'agy' to log in, then retry."
    # settings.json remains NOT evidence that a grant is ACTIVE -- agy silently discards rules
    # it cannot parse -- so it is reported as what was WRITTEN and never converted into a PASS.
    settings="$HOME/.gemini/antigravity-cli/settings.json"
    written='unknown'
    if [ -f "$settings" ] && command -v python3 >/dev/null 2>&1; then
        written="$(python3 -c 'import json,sys
try:
    d = json.load(open(sys.argv[1]))
except Exception:
    print("unreadable"); raise SystemExit
a = (d.get("permissions") or {}).get("allow")
print("%d rule(s)" % len(a) if isinstance(a, list) else "no allow list")' "$settings" 2>/dev/null || echo unknown)"
    fi
    if [ -z "$grants" ] && [ "$grants_rc" -ne 0 ]; then
        fail "'agy -p /permissions' could not run (exit $grants_rc), so the ACTIVE grants are UNVERIFIED — this is NOT evidence that they are missing ($written written in $settings). Re-running setup-antigravity.sh will not help; fix the cause named here and re-run this doctor: ${grant_diag:-no stderr}. When that cause is authentication, run: bash $SCRIPT_DIR/agy-login.sh"
    elif [ -z "$grants" ]; then
        fail "'agy -p /permissions' ran (exit 0) and returned no rules — NO grants are active; every headless lane will be auto-denied and still report SUCCESS. Run: bash $SCRIPT_DIR/setup-antigravity.sh"
    elif [ -n "$missing" ]; then
        fail "headless grants missing:$missing — lanes will be auto-denied and still report SUCCESS. Run: bash $SCRIPT_DIR/setup-antigravity.sh"
    else
        pass "headless grants active: $(printf '%s' "$grants" | grep -c .) rule(s), including read_file(*), write_file(*) and the command set"
    fi
fi

# 4. optional live probe: proves authentication AND the headless JSON envelope
if [ "${1:-}" = "--probe" ] && command -v agy >/dev/null 2>&1; then
    # The check above verified the keyring in a subshell; agy here needs the
    # bus address in THIS shell or it cannot see the cached credential.
    [ -f "$HOME/.config/agy-cloud/keyring.env" ] && . "$HOME/.config/agy-cloud/keyring.env"
    echo "probing headless agy (one small model call that MUST use a tool)..."
    # The probe has to EXERCISE a tool. A prompt the model can answer from the prompt alone
    # passes with every grant broken, which is a check that cannot fail (SKILL.md §7): it
    # would certify a container where no lane can read a byte.
    probe_file="$(mktemp)"; printf 'DEVLOOP-PROBE-OK\n' > "$probe_file"
    out="$(timeout 180 agy -p "Read the file $probe_file and reply with only its contents." \
            --output-format json --print-timeout 2m 2>&1)"
    rc=$?
    rm -f "$probe_file"
    # status SUCCESS + exit 0 is exactly what a FULLY DENIED run reports, so neither is
    # evidence. Ask the shared normaliser, which reads denied_actions/permission_denials
    # and treats an empty response as the failure it is.
    envfile="$(mktemp)"; printf '%s' "$out" > "$envfile"
    denials="$("${PYTHON:-python3}" "$SCRIPT_DIR/../adapters.py" denials "$envfile" 2>&1)"; drc=$?
    rm -f "$envfile"
    quota="$(printf '%s' "$out" | grep -oE '[A-Za-z ]*quota reached[^"]*' | head -1)"
    if [ -n "$quota" ]; then
        fail "headless probe: authenticated, but the plan's quota is spent, so tool use is UNVERIFIED: $quota"
    elif printf '%s' "$out" | grep -qi 'not authenticated\|sign in\|authentication'; then
        fail "headless probe: NOT AUTHENTICATED — run: bash $SCRIPT_DIR/agy-login.sh"
    elif [ $drc -ne 0 ]; then
        fail "headless probe: the run reported success but did nothing — $(printf '%s' "$denials" | head -2 | tr '\n' ' ')"
    elif printf '%s' "$out" | grep -q 'DEVLOOP-PROBE-OK'; then
        pass "headless probe: read a file and returned its contents — authenticated, granted, and working"
    else
        fail "headless probe: exit $rc, no denial reported but the file contents did not come back. Tail: $(printf '%s' "$out" | tail -c 400)"
    fi
fi

exit $FAILED
