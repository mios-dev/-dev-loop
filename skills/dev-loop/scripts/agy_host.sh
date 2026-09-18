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
# (scripts/env/setup-antigravity.sh + scripts/env/agy-login.sh),
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

# Cloud containers keep the keyring's bus address in this env file; without it
# agy (and every agy -p lane it spawns) cannot see the cached credential and
# stalls on authentication. No-op where the file does not exist.
[ -f "$HOME/.config/agy-cloud/keyring.env" ] && . "$HOME/.config/agy-cloud/keyring.env"

PROMPT="You are the L0 host/manager of the dev-loop skill. Load the skill (dev-loop, in ~/.gemini/config/skills or .agents/skills) and follow SKILL.md sections 11-13 exactly.

Manager duties, in order:
1. Orient: read AGENTS.md, the last .devloop/LEDGER.md entry, and TASKS.md. AGENTS.md is law.
2. You manage ALL sub-agents for this run. The lane plan is $LANES (already schema-validated). YOUR NATIVE MULTI-AGENT MACHINERY IS THE DEFAULT for your own lanes: run every lane whose worker.harness is 'antigravity' as a native Antigravity subagent (invoke_subagent with workspace: branch, one subagent per lane, the lane's contract - id, objective, owned_paths, both control commands, budget - as its prompt, reports written into .devloop/run-*/report-LANE_ID.json). Native workflows and each harness's own loop commands (/dev-loop and equivalents) are allowed inside lanes; they map onto loop stages, they never replace the gates.
3. Other harnesses join the loop through the reference orchestrator: write the non-antigravity lanes (claude-code, codex, gemini-cli, copilot, opencode, cursor, openai-compatible, custom) unchanged into lanes.external.json in the workspace root, then run SYNCHRONOUSLY IN THE FOREGROUND, as EXACTLY this shape - starting with 'sh', no 'cd' prefix, no shell operators before it (your working directory is already the workspace root, and a scoped permission rule matches this command only as written):
   sh $SKILL_DIR/scripts/devloop.sh lanes.external.json
   NEVER background this command and NEVER respond while it is still running - when your process ends, every child lane dies with it. It can take many minutes; wait for its exit code. If native subagents are unavailable in this mode, fall back to dispatching the FULL plan the same way: sh $SKILL_DIR/scripts/devloop.sh $LANES
4. Model tiers are yours to manage: claude-code lanes default to Opus at xhigh effort; assign lower tiers (worker.model 'sonnet' or a haiku id, worker.effort high) to light lanes (docs, lint, small fixes) when writing lanes.external.json.
5. Gate every native lane YOURSELF before merging it - python3 $SKILL_DIR/scripts/adapters.py owned/gate/secrets/deps with the lane json and worktree - then merge --no-ff exactly as devloop.sh does for external lanes. Never trust a lane's own claim over the gates; a lane whose negative control passes is vacuous and is never merged. After devloop.sh exits, read .devloop/run-*/report-*.json and 'git log --oneline' and confirm each external merge really happened.
6. On a merge conflict abort the merge and keep the worktree - report it, do not resolve inside a lane.
7. Close tasks with evidence, write contract_updates into AGENTS.md, append a ledger entry, and end with the devloop_report JSON block reflecting the ACTUAL gate results, exit codes, and reports on disk (status must be true: partial work is 'partial', never 'done'). A response that only describes what you started, without that block grounded in the finished run, is a failed run.

You are the only writer to shared state; lanes never git add/commit/push and never edit AGENTS.md."

case "$MODE" in
    print)
        printf '%s\n' "$PROMPT"
        ;;
    headless)
        command -v agy >/dev/null 2>&1 || { echo "agy not installed" >&2; exit 69; }
        # Manager defaults to the deepest-reasoning model at high effort (the manager
        # gates and merges everything — reasoning quality dominates its cost);
        # override with AGY_HOST_MODEL / AGY_HOST_EFFORT (`agy models` lists slugs).
        set -- -p "$PROMPT" --output-format json --print-timeout "${AGY_HOST_PRINT_TIMEOUT:-60m}" \
               --model "${AGY_HOST_MODEL:-gemini-3.1-pro-high}" --effort "${AGY_HOST_EFFORT:-high}"
        [ "$SKIP_PERMS" = 1 ] && set -- "$@" --dangerously-skip-permissions
        # Outer wall-clock timeout: no harness is trusted to stop itself (SKILL.md §10).
        exec timeout "${AGY_HOST_TIMEOUT:-4h}" agy "$@"
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
