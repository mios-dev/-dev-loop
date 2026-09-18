#!/bin/sh
# Stop / SubagentStop: refuse to stop without a devloop_report block; loop-guard via stop_hook_active; hard cap via counter file.
. "$(dirname "$0")/_lib.sh"; IN=$(cat)
[ "$(json_get "$IN" .stop_hook_active)" = "true" ] && exit 0                      # MANDATORY loop guard
T=$(json_get "$IN" .transcript_path); [ -f "$T" ] || exit 0
CAP=${DEVLOOP_STOP_CAP:-3}; C="${TMPDIR:-/tmp}/devloop-stop-$(printf '%s' "$T" | cksum | cut -d' ' -f1)"
N=$(cat "$C" 2>/dev/null || echo 0); [ "$N" -ge "$CAP" ] && { rm -f "$C"; exit 0; }  # hard cap: never loop forever
# only gate sessions that actually ran the loop (skill/agent mention in transcript)
grep -q 'dev-loop\|devloop' "$T" 2>/dev/null || exit 0
LAST=$(tail -c 60000 "$T")
if printf '%s' "$LAST" | grep -q 'devloop_report'; then
  # transcript lines are JSONL: quotes inside message content are escaped as \" — accept both forms
  printf '%s' "$LAST" | grep -Eq '\\?"status\\?"[[:space:]]*:[[:space:]]*\\?"(done|partial|blocked|converged_stuck|budget|halted)' && { rm -f "$C"; exit 0; }
fi
echo $((N+1)) > "$C"
printf '{"decision":"block","reason":"dev-loop: finish with the devloop_report JSON block (SKILL §13) stating a true status — done only if both controls were run and held; otherwise partial/blocked/budget with exactly what remains and what is unverified."}\n'
exit 0
