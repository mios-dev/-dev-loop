#!/bin/sh
# Stop / SubagentStop: refuse to stop without a devloop_report, and refuse to stop on a
# NON-TERMINAL one. SKILL.md §1 says to re-arm the loop every cycle; this hook is the only
# thing in a position to do it. Terminal statuses map to §12's stop conditions (verified,
# external blocker, no convergence, budget, explicit halt); `partial` is none of those --
# it means work remains -- so it re-arms instead. Both paths are capped: a Stop hook that
# always blocks is an infinite loop that spends real money.
. "$(dirname "$0")/_lib.sh"; IN=$(cat)
[ "$(json_get "$IN" .stop_hook_active)" = "true" ] && exit 0                      # MANDATORY loop guard
T=$(json_get "$IN" .transcript_path); [ -f "$T" ] || exit 0
# only gate sessions that actually ran the loop (skill/agent mention in transcript)
grep -q 'dev-loop\|devloop' "$T" 2>/dev/null || exit 0

KEY=$(printf '%s' "$T" | cksum | cut -d' ' -f1)
CAP=${DEVLOOP_STOP_CAP:-3};  C="${TMPDIR:-/tmp}/devloop-stop-$KEY"                # no report at all
LCAP=${DEVLOOP_LOOP_CAP:-5}; L="${TMPDIR:-/tmp}/devloop-loop-$KEY"                # report says partial
_done() { rm -f "$C" "$L"; exit 0; }

# SKILL §5: operator questions go through the native question UI, never chat prose. Stop only
# (a lane has no UI and returns `blocked`); DEVLOOP_NATIVE_ASK=0 opts out for a UI-less host.
QCAP=${DEVLOOP_ASK_CAP:-2}; Q="${TMPDIR:-/tmp}/devloop-ask-$KEY"
QL=""
if [ "$(json_get "$IN" .hook_event_name)" != "SubagentStop" ] && [ "${DEVLOOP_NATIVE_ASK:-1}" != "0" ]; then
  QL=$(python3 "$(dirname "$0")/_chat_question.py" "$T" || :)                   # prints only on a hit
fi
if [ -n "$QL" ] && [ "$(cat "$Q" 2>/dev/null || echo 0)" -lt "$QCAP" ]; then
  echo $(( $(cat "$Q" 2>/dev/null || echo 0) + 1 )) > "$Q"
  R="dev-loop: your reply asks the operator a question in chat (\"$QL\"). SKILL §5: ask through the native question UI (AskUserQuestion) with 2-4 options, recommended first -- never in prose. Ask it now with the tool, then finish the turn."
  printf '{"decision":"block","reason":%s}\n' "$(printf '%s' "$R" | python3 -c 'import json,sys;print(json.dumps(sys.stdin.read()))')"
  exit 0
fi
rm -f "$Q"
LAST=$(tail -c 60000 "$T")
# transcript lines are JSONL: quotes inside message content are escaped as \" — accept both forms
_status() { printf '%s' "$LAST" | grep -Eo '\\?"status\\?"[[:space:]]*:[[:space:]]*\\?"[a-z_]+' | tail -1 | grep -Eo '[a-z_]+$'; }

if printf '%s' "$LAST" | grep -q 'devloop_report'; then
  S=$(_status)
  case "$S" in
    done|blocked|converged_stuck|budget|halted) _done ;;                          # a real stop condition
    partial)
      N=$(cat "$L" 2>/dev/null || echo 0)
      [ "$N" -ge "$LCAP" ] && _done                                               # bounded, never forever
      echo $((N+1)) > "$L"
      printf '{"decision":"block","reason":"dev-loop: status was partial, so the loop is NOT finished (SKILL §1: re-arm every cycle until acceptance criteria are met or a §12 stop condition is reached). Run the next cycle on the highest-value unblocked item, with both controls. If nothing can advance, say so with a TERMINAL status instead: blocked (needs the operator), converged_stuck (no net convergence), or budget."}\n'
      exit 0 ;;
  esac
fi
N=$(cat "$C" 2>/dev/null || echo 0)
[ "$N" -ge "$CAP" ] && _done
echo $((N+1)) > "$C"
printf '{"decision":"block","reason":"dev-loop: finish with the devloop_report JSON block (SKILL §13) stating a true status — done only if both controls were run and held; otherwise partial/blocked/budget with exactly what remains and what is unverified."}\n'
exit 0
