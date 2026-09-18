#!/usr/bin/env sh
# agy_host.sh — launch Google Antigravity (agy) as the L0 manager of a dev-loop
# run (topology A in references/harness-adapters.md §3): AGY decomposes, owns
# shared state, dispatches the lanes in <lanes.json> through scripts/devloop.sh
# (any mix of harnesses — multiple antigravity AND multiple claude-code lanes
# side by side), runs the two-sided merge gates itself, merges, reports.
#
#   sh scripts/agy_host.sh <lanes.json>                          # interactive manager
#   sh scripts/agy_host.sh <lanes.json> --headless [--yolo]      # unattended manager
#   sh scripts/agy_host.sh <lanes.json> --print-prompt           # just emit the manager prompt
#
# Requirements: `agy` installed and authenticated once on this machine
# (in the cloud container: environment/setup-antigravity.sh + agy-login.sh),
# and — for parallel lanes — a live Secret Service keyring so every spawned
# `agy -p` lane reuses the cached credential instead of re-asking.
# The agy flag surface drifts monthly; run `python3 scripts/adapters.py probe` first.
set -eu

SKILL_DIR=$(cd "$(dirname "$0")/.." && pwd)
LANES=${1:-}
[ -n "$LANES" ] && [ -f "$LANES" ] || { echo "usage: sh scripts/agy_host.sh <lanes.json> [--headless [--yolo]] [--print-prompt]" >&2; exit 64; }
LANES=$(cd "$(dirname "$LANES")" && pwd)/$(basename "$LANES")
shift
MODE=interactive; SKIP_PERMS=0
while [ $# -gt 0 ]; do
    case "$1" in
        --headless) MODE=headless;;
        --yolo) SKIP_PERMS=1;;
        --print-prompt) MODE=print;;
        *) echo "unknown flag: $1" >&2; exit 64;;
    esac
    shift
done

# Validate the lane file before handing it to a model: fail here, not mid-run.
python3 "$SKILL_DIR/scripts/adapters.py" validate "$LANES" >/dev/null || { echo "lane file failed validation: $LANES" >&2; exit 65; }

PROMPT="You are the L0 host/manager of the dev-loop skill. Load the skill (dev-loop, in ~/.gemini/config/skills or .agents/skills) and follow SKILL.md sections 11-13 exactly.

Manager duties, in order:
1. Orient: read AGENTS.md, the last .devloop/LEDGER.md entry, and TASKS.md. AGENTS.md is law.
2. You manage ALL sub-agents for this run. The lane plan is $LANES (already schema-validated). Lanes may include several 'antigravity' lanes and several 'claude-code' lanes concurrently; each runs as its own headless process in its own git worktree.
3. Dispatch every lane through the reference orchestrator, not by hand: run_command -> sh $SKILL_DIR/scripts/devloop.sh $LANES  (watch progress with /tasks; reports land in .devloop/run-*/report-*.json).
4. Gate every lane yourself; never trust a lane's own claim: python3 $SKILL_DIR/scripts/adapters.py owned/gate/secrets/deps. A lane whose negative control passes is vacuous and is never merged.
5. Merge --no-ff lane by lane; on conflict abort and keep the worktree. Run the integration command on base after merging.
6. Close tasks with evidence, write contract_updates into AGENTS.md, append a ledger entry, and end with the devloop_report JSON block (status must be true: partial work is 'partial', never 'done').

You are the only writer to shared state; lanes never git add/commit/push and never edit AGENTS.md."

case "$MODE" in
    print)
        printf '%s\n' "$PROMPT"
        ;;
    headless)
        command -v agy >/dev/null 2>&1 || { echo "agy not installed" >&2; exit 69; }
        set -- -p "$PROMPT" --output-format json --print-timeout 60m
        [ "$SKIP_PERMS" = 1 ] && set -- "$@" --dangerously-skip-permissions
        # Outer wall-clock timeout: no harness is trusted to stop itself (SKILL.md §10).
        exec timeout 4h agy "$@"
        ;;
    interactive)
        command -v agy >/dev/null 2>&1 || { echo "agy not installed" >&2; exit 69; }
        echo "Starting interactive agy. Paste the manager prompt below (or run /dev-loop lanes:$LANES):"
        echo "--------------------------------------------------------------------------"
        printf '%s\n' "$PROMPT"
        echo "--------------------------------------------------------------------------"
        exec agy
        ;;
esac
