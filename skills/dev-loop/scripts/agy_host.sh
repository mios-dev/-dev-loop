#!/usr/bin/env sh
# agy_host.sh — launch Google Antigravity (agy) as the L0 manager of a dev-loop
# run (topology A in references/harness-adapters.md §3): AGY decomposes, owns
# shared state, dispatches the lanes in <lanes.json> through scripts/devloop.sh
# (any mix of harnesses — multiple antigravity AND multiple claude-code lanes
# side by side), runs the two-sided merge gates itself, merges, reports.
#
#   sh scripts/agy_host.sh <lanes.json>                          # interactive manager
#   sh scripts/agy_host.sh <lanes.json> --headless [--yolo]      # unattended, SINGLE-TURN
#   sh scripts/agy_host.sh <lanes.json> --session  [--yolo]      # unattended, HELD SESSION
#   sh scripts/agy_host.sh <lanes.json> --print-prompt           # just emit the manager prompt
#
# --headless vs --session is about PROCESS LIFETIME, not about being unattended.
# --headless is `agy -p`: one turn, then the process exits and anything it started
# that had not finished dies with it. --session holds a stream-json NDJSON session
# open across turns (scripts/agy_session.py), so native subagent lanes survive the
# turn that dispatched them and the host can poll until they report.
#
# Requirements: `agy` installed and authenticated once on this machine
# (scripts/env/setup-antigravity.sh + scripts/env/agy-login.sh),
# and — for parallel lanes — a live Secret Service keyring so every spawned
# `agy -p` lane reuses the cached credential instead of re-asking.
# The agy flag surface drifts monthly; run `python3 scripts/adapters.py probe` first.
set -eu

SKILL_DIR=$(cd "$(dirname "$0")/.." && pwd)
LANES=${1:-}
[ -n "$LANES" ] && [ -f "$LANES" ] || { echo "usage: sh scripts/agy_host.sh <lanes.json> [--headless|--session [--yolo]] [--print-prompt]" >&2; exit 64; }
LANES=$(cd "$(dirname "$LANES")" && pwd)/$(basename "$LANES")
shift
MODE=interactive; SKIP_PERMS=0; HEADLESS=0; SESSION=0; PRINT_ONLY=0
# Three axes, tracked separately on purpose, because folding them together makes the
# behaviour depend on the ORDER the flags were typed in:
#   MODE       - which executor runs the prompt (interactive / headless / session)
#   HEADLESS   - which dispatch rule the prompt must carry
#   PRINT_ONLY - a sticky override: preview the prompt, execute nothing
# PRINT_ONLY is deliberately NOT a MODE value. When it was, `--print-prompt --headless`
# set MODE=print and then MODE=headless and LAUNCHED the manager the operator was only
# trying to preview -- a dry-run flag that runs the thing is the worst kind of surprise,
# and adding --session made it worse. --print-prompt now wins wherever it appears.
while [ $# -gt 0 ]; do
    case "$1" in
        --headless) MODE=headless; HEADLESS=1;;
        --session) MODE=session; HEADLESS=1; SESSION=1;;
        --yolo) SKIP_PERMS=1;;
        --print-prompt) PRINT_ONLY=1;;
        *) echo "unknown flag: $1" >&2; exit 64;;
    esac
    shift
done
[ "$PRINT_ONLY" = 1 ] && MODE=print

# Validate the lane file before handing it to a model: fail here, not mid-run.
python3 "$SKILL_DIR/scripts/adapters.py" validate "$LANES" >/dev/null || { echo "lane file failed validation: $LANES" >&2; exit 65; }

# The run's repository root: everything the manager creates lives under it.
# (An agy manager perceives its TRUSTED WORKSPACE as home and, unanchored,
# invents paths in the wrong checkout — observed live 2026-09.)
RUN_ROOT=$(cd "$(dirname "$LANES")" && git rev-parse --show-toplevel 2>/dev/null || dirname "$LANES")

# Cloud containers keep the keyring's bus address in this env file; without it
# agy (and every agy -p lane it spawns) cannot see the cached credential and
# stalls on authentication. No-op where the file does not exist.
[ -f "$HOME/.config/agy-cloud/keyring.env" ] && . "$HOME/.config/agy-cloud/keyring.env"

# How the manager dispatches its OWN lanes. This is decided by PROCESS LIFETIME, not by
# whether a human is watching, and it is not a preference.
#
# `agy -p` is single-turn print mode: the turn ends when the model stops speaking, and the
# process exits. Observed live (agy 1.2.6): the manager wrote lanes.external.json,
# provisioned all three worktrees, invoked the first native lane, and ended its turn saying
# it was "waiting" for the lane to report -- leaving three worktrees at dirty=0
# commits_ahead=0, no .devloop/native/ reports, and no agy process alive. It cannot detect
# this, because from inside the turn the dispatch succeeded.
#
# What that observation does and does not establish (measured 1.2.6, three probes, two of
# which refuted the first explanation): invoke_subagent is NOT unavailable headlessly. It
# succeeds under single-shot -p, inside a held session, and with no prior define_subagent,
# all with denied_actions absent -- and it still succeeds when an invalid toolPermission
# voids settings.json and permission_mode degrades to request-review, which eliminates the
# leading suspect. It is ungated by construction: the permission grammar has five actions
# (read_file, write_file, command, url, mcp) and invoke_subagent is not one of them.
# Every subagent in those probes finished INSIDE the dispatching turn.
#
# So the real constraint is lifetime, exactly as the original comment argued: a subagent
# that has not finished when the turn ends is lost. Single-shot mode therefore still routes
# everything through the foreground orchestrator. A HELD session does not have that problem
# -- the process outlives any single turn -- so --session is allowed native lanes and
# agy_session.py polls until each one has written its report.
if [ "$SESSION" = 1 ]; then
    DISPATCH_RULE="HELD SESSION: your process stays alive across turns, so YOUR NATIVE MULTI-AGENT MACHINERY IS THE DEFAULT for your own lanes. Run every lane whose worker.harness is 'antigravity' as a native Antigravity subagent (invoke_subagent with workspace: branch, one subagent per lane, the lane's contract - id, objective, owned_paths, both control commands, budget - as its prompt), and collect each native lane's devloop_report into \$RUN_ROOT/.devloop/native/report-LANE_ID.json (use write_file). Ending a turn does NOT end the run: if a subagent has not finished, say so plainly and end the turn - the host will send you a follow-up turn to continue waiting. NEVER write a report file for a lane that has not actually reported, and never claim a lane finished because you dispatched it. Keep ALL per-lane scratch you create -- lane contracts, parked patches, notes -- inside \$RUN_ROOT/.devloop/native/ next to the reports. Do NOT write scratch at \$RUN_ROOT/.devloop/ top level: that is tracked space holding the lane plan, the ledger and the lanes' findings, and files dropped there become part of the repository's state."
elif [ "$HEADLESS" = 1 ]; then
    DISPATCH_RULE="HEADLESS DISPATCH, NOT A PREFERENCE: run EVERY lane -- including those whose worker.harness is 'antigravity' -- through the reference orchestrator, in the foreground. Do NOT use invoke_subagent in this mode. It is not that the tool is unavailable - it works - but this is a single-turn print run, so the process exits when your turn ends and any subagent that has not already finished dies with it, leaving you reporting success over a lane that never ran. Use --session if you need native lanes. Skip step 3's split entirely and dispatch the FULL plan as EXACTLY this shape, with WaitMsBeforeAsync 1800000, waiting for its exit code:
   sh \$SKILL_DIR/scripts/devloop.sh \$LANES
Then read \$RUN_ROOT/.devloop/run-*/report-*.json for what each lane actually did."
else
    DISPATCH_RULE="YOUR NATIVE MULTI-AGENT MACHINERY IS THE DEFAULT for your own lanes: run every lane whose worker.harness is 'antigravity' as a native Antigravity subagent (invoke_subagent with workspace: branch, one subagent per lane, the lane's contract - id, objective, owned_paths, both control commands, budget - as its prompt), and collect each native lane's devloop_report into \$RUN_ROOT/.devloop/native/report-LANE_ID.json (use write_file). You are interactive, so you can wait for each subagent to finish."
fi

PROMPT="You are the L0 host/manager of the dev-loop skill. Load the skill (dev-loop, in ~/.gemini/config/skills or .agents/skills) and follow SKILL.md sections 11-13 exactly.

THE REPOSITORY ROOT FOR THIS RUN IS: $RUN_ROOT
Every path you read, create, or modify lives under $RUN_ROOT - the lane plan, lanes.external.json, .devloop/, .worktrees/, every merge. Never touch any other checkout, whatever your workspace or trust settings say; your shell commands already execute with $RUN_ROOT as the working directory. Do not pre-create .devloop/ or .worktrees/ - the orchestrator makes its own run directories.

USE YOUR OWN NATIVE TOOLS. Read with view_file/read_file, search with grep_search and
codebase_search, write with write_file. (How you dispatch LANES is duty 2 below, and it is
not yours to choose - it depends on whether this run can outlive your turn.)
Do NOT route reading or searching through shell 'cat'/'grep' - your native tools are better
at it and the run is configured (toolPermission auto) to let you use them. Shell is for the
things only shell can do: git, the orchestrator, the gates.

RULES FOR YOUR SHELL TOOL (violations kill the whole run):
- Never 'rm'. Never clean up; leave lanes.external.json and every artifact in place, so the
  run can be audited after it ends.
- run_command sends any command still running after WaitMsBeforeAsync milliseconds TO THE BACKGROUND, and background tasks DIE when your turn ends. For devloop.sh (and any command that can run minutes) you MUST set WaitMsBeforeAsync to 1800000 so it completes in the foreground. Never accept an async handoff for devloop.sh.
- Work in STRICT SEQUENCE, no concurrency: dispatch as duty 2 directs and let it run to completion, then gates and merges, then the report. Never report on a lane you have not read a report file for.

THE TRACKED SURFACE IS MAPPED FOR YOU. $RUN_ROOT/.gitignore is block-all-then-whitelist: it
denies /* and then re-admits each tracked path with a '!' line. So 'grep \"^!\" .gitignore' is
a directory map of everything this repository owns - read it first and you will know where
every deliverable lives without walking the tree. Anything not whitelisted there is build
output or vendored payload, not source.

Manager duties, in order:
1. Orient: read $RUN_ROOT/AGENTS.md, the last entry of $RUN_ROOT/.devloop/LEDGER.md, and $RUN_ROOT/TASKS.md (each may be absent in a fresh repo - note it and move on). AGENTS.md is law.
2. You manage ALL sub-agents for this run. The lane plan is $LANES (already schema-validated). $DISPATCH_RULE Native workflows and each harness's own loop commands (/dev-loop and equivalents) are allowed inside lanes; they map onto loop stages, they never replace the gates.
3. Other harnesses join the loop through the reference orchestrator: write the non-antigravity lanes (claude-code, codex, gemini-cli, copilot, opencode, cursor, openai-compatible, custom) unchanged (same version/base_ref/worktree_root/integration_cmd envelope) into $RUN_ROOT/lanes.external.json with write_file, then run SYNCHRONOUSLY IN THE FOREGROUND, as EXACTLY this shape - starting with 'sh', no 'cd' prefix, no shell operators before it (a scoped permission rule matches this command only as written):
   sh $SKILL_DIR/scripts/devloop.sh $RUN_ROOT/lanes.external.json
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
        # NOT exec: a headless run whose tools were auto-denied still exits 0 with
        # status SUCCESS and an empty response (agy 1.2.6, observed live), so exec'ing
        # would hand the caller that 0 as if the manager had done the work. Capture the
        # envelope, show it, and put it through the same denial check adapters.py
        # applies to every lane (SKILL.md §10, "headless green can hide denials").
        ENV_FILE=${AGY_HOST_ENVELOPE:-$(mktemp)}
        timeout "${AGY_HOST_TIMEOUT:-4h}" agy "$@" >"$ENV_FILE" 2>&1
        RC=$?
        cat "$ENV_FILE"
        if ! python3 "$SKILL_DIR/scripts/adapters.py" denials "$ENV_FILE"; then
            echo "agy_host: manager run rejected — see the denial lines above; envelope kept at $ENV_FILE" >&2
            [ "$SKIP_PERMS" = 1 ] || echo "agy_host: headless auto-denies tools it cannot prompt for; re-run with --yolo, or add the allow-rule the notice names to settings.json" >&2
            [ "$RC" = 0 ] && RC=3
        fi
        exit "$RC"
        ;;
    session)
        command -v agy >/dev/null 2>&1 || { echo "agy not installed" >&2; exit 69; }
        # Held stream-json session: the process outlives each turn, so native subagent
        # lanes survive their dispatch and agy_session.py polls until every antigravity
        # lane in $LANES has written .devloop/native/report-<id>.json. Same denial check
        # as the single-shot path -- a held session can be auto-denied just as quietly.
        PROMPT_FILE=$(mktemp)
        printf '%s\n' "$PROMPT" > "$PROMPT_FILE"
        ENV_FILE=${AGY_HOST_ENVELOPE:-$(mktemp)}
        set -- --prompt-file "$PROMPT_FILE" --lanes "$LANES" --run-root "$RUN_ROOT" \
               --envelope-out "$ENV_FILE" \
               --model "${AGY_HOST_MODEL:-gemini-3.1-pro-high}" \
               --effort "${AGY_HOST_EFFORT:-high}" \
               --poll-max "${AGY_HOST_POLL_MAX:-8}"
        [ "$SKIP_PERMS" = 1 ] && set -- "$@" --yolo
        timeout "${AGY_HOST_TIMEOUT:-4h}" python3 "$SKILL_DIR/scripts/agy_session.py" "$@"
        RC=$?
        rm -f "$PROMPT_FILE"
        if [ -s "$ENV_FILE" ] && ! python3 "$SKILL_DIR/scripts/adapters.py" denials "$ENV_FILE"; then
            echo "agy_host: manager session rejected — see the denial lines above; envelope kept at $ENV_FILE" >&2
            [ "$SKIP_PERMS" = 1 ] || echo "agy_host: headless auto-denies tools it cannot prompt for; re-run with --yolo, or add the allow-rule the notice names to settings.json" >&2
            [ "$RC" = 0 ] && RC=3
        fi
        exit "$RC"
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
