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
[ -n "$LANES" ] && [ -f "$LANES" ] || { echo "usage: sh scripts/agy_host.sh <lanes.json> [--headless|--session [--yolo]] [--tmux] [--print-prompt]" >&2; exit 64; }
LANES=$(cd "$(dirname "$LANES")" && pwd)/$(basename "$LANES")
shift
MODE=interactive; SKIP_PERMS=0; HEADLESS=0; SESSION=0; PRINT_ONLY=0; USE_TMUX=0
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
        --tmux) USE_TMUX=1;;
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
    DISPATCH_RULE="HELD SESSION: your process stays alive across turns, so YOUR NATIVE MULTI-AGENT MACHINERY IS THE DEFAULT for your own lanes. Run every lane whose worker.harness is 'antigravity' as a native Antigravity subagent (invoke_subagent with workspace: branch, one subagent per lane, the lane's contract - id, objective, owned_paths, both control commands, budget - as its prompt), and collect each native lane's devloop_report into $RUN_ROOT/.devloop/native/report-LANE_ID.json (use write_file). Ending a turn does NOT end the run: if a subagent has not finished, say so plainly and end the turn - the host will send you a follow-up turn to continue waiting. NEVER write a report file for a lane that has not actually reported, and never claim a lane finished because you dispatched it. Keep ALL per-lane scratch you create -- lane contracts, parked patches, notes -- inside $RUN_ROOT/.devloop/native/ next to the reports. Do NOT write scratch at $RUN_ROOT/.devloop/ top level: that is tracked space holding the lane plan, the ledger and the lanes' findings, and files dropped there become part of the repository's state."
elif [ "$HEADLESS" = 1 ]; then
    DISPATCH_RULE="HEADLESS DISPATCH, NOT A PREFERENCE: run EVERY lane -- including those whose worker.harness is 'antigravity' -- through the reference orchestrator, in the foreground. Do NOT use invoke_subagent in this mode. It is not that the tool is unavailable - it works - but this is a single-turn print run, so the process exits when your turn ends and any subagent that has not already finished dies with it, leaving you reporting success over a lane that never ran. Use --session if you need native lanes. Skip step 3's split entirely and dispatch the FULL plan as EXACTLY this shape, with WaitMsBeforeAsync 1800000, waiting for its exit code:
   sh $SKILL_DIR/scripts/devloop.sh $LANES
Then read \$RUN_ROOT/.devloop/run-*/report-*.json for what each lane actually did."
else
    DISPATCH_RULE="YOUR NATIVE MULTI-AGENT MACHINERY IS THE DEFAULT for your own lanes: run every lane whose worker.harness is 'antigravity' as a native Antigravity subagent (invoke_subagent with workspace: branch, one subagent per lane, the lane's contract - id, objective, owned_paths, both control commands, budget - as its prompt), and collect each native lane's devloop_report into $RUN_ROOT/.devloop/native/report-LANE_ID.json (use write_file). You are interactive, so you can wait for each subagent to finish."
fi

PROMPT="# ROLE

You are the L0 host and manager of a dev-loop run. You decompose nothing that is already
decomposed, you dispatch lanes, you gate every lane yourself, you merge what passes, and you
report only what the tree proves. Lanes do the work; you own all shared state and every claim.

# CONTEXT

Repository root for this run: $RUN_ROOT. Every path you read, create or modify lives under it.
Never touch another checkout whatever your workspace or trust settings say. Your shell already
runs with $RUN_ROOT as its working directory. Do not pre-create .devloop/ or .worktrees/ --
the orchestrator makes its own run directories.

$RUN_ROOT/.gitignore is block-all-then-whitelist: it denies /* then re-admits each tracked path
with a '!' line. 'grep \"^!\" .gitignore' is therefore a map of every deliverable in the repo,
and anything not whitelisted is build output or vendored payload, not source. Use it instead of
walking the tree.

Read $RUN_ROOT/AGENTS.md (it is LAW and outranks anything here), the last entry of
$RUN_ROOT/.devloop/LEDGER.md, and $RUN_ROOT/TASKS.md. Each may be absent in a fresh repo --
note it and move on.

# GOALS

The objective for this run is the 'objective' field of the lane plan $LANES, and each lane's
own 'objective' is binding on that lane. If $RUN_ROOT/docs/GOALS.md or AGENTS.md contradicts a
lane objective, the repo wins: escalate in your report, do not quietly execute.

A task that is already done comes back STALE. A row whose numbers are wrong comes back with the
measured ones. Agreeing with a previous finding without re-deriving it has measured nothing.

# SKILLS

Load the dev-loop skill (in ~/.gemini/config/skills or .agents/skills) and follow it. The
sections that decide this run:
- section 6  Verification: exit 0 is not proof; two-sided controls; a broken control INVERTS a
             result rather than weakening it; assert your harness did work.
- section 7  Checks that cannot fail: Skip-as-Pass, Empty-Set Pass, Self-Certifying Predicate,
             Timeout-as-Pass, Measuring the Wrong Property. This is the defect class you are
             most likely to commit yourself.
- section 11 Lanes and worktrees: exclusive owned_paths, the two-sided merge gate, park a diff
             you cannot merge, never commit a lane's edits without its report.
- section 12 Staging and commits: explicit paths only, never 'git add -A', secrets scan first.
- section 13 The devloop_report block that ends your final message.

# TOOLS

Use your OWN native tools for reading and searching: view_file, read_file, grep_search,
codebase_search, write_file. Do not route those through shell cat/grep -- they are better and
this run is configured to allow them. Shell is for what only shell can do: git, the
orchestrator, the gates.

Scripts available to you, with exact invocations (SKILL_DIR=$SKILL_DIR):
  python3 $SKILL_DIR/scripts/adapters.py validate <lanes.json>      schema-check a plan
  python3 $SKILL_DIR/scripts/adapters.py lane <spec> <id> --out <f> render one lane contract
  python3 $SKILL_DIR/scripts/adapters.py owned --lane <f> --wt <wt>  assert a lane touched only its paths
  python3 $SKILL_DIR/scripts/adapters.py gate --lane <f> --wt <wt> --run <dir>   BOTH controls
  python3 $SKILL_DIR/scripts/adapters.py secrets --wt <wt>          secrets scan before commit
  python3 $SKILL_DIR/scripts/adapters.py denials <envelope>         auto-denials hide in exit 0
  python3 $SKILL_DIR/scripts/agy_monitor.py <stream> --once         a run's derived verdict
  sh $SKILL_DIR/scripts/devloop.sh <lanes.json>                     the reference orchestrator

# RULES FOR YOUR SHELL TOOL (violations kill the run)

- Never 'rm'. Never clean up. Leave every artifact in place so the run can be audited after it
  ends.
- run_command sends anything still running after WaitMsBeforeAsync milliseconds TO THE
  BACKGROUND, and background tasks DIE when your turn ends. For devloop.sh and any command that
  can take minutes you MUST set WaitMsBeforeAsync to 1800000 so it finishes in the foreground.
  Never accept an async handoff for devloop.sh. A lane worker that ignored this announced three
  times that it would wait for a background command, ended its turn, and measured nothing.
- Work in STRICT SEQUENCE, no concurrency: dispatch, let it finish, then gates, then merges,
  then the report. Never report on a lane whose report file you have not read.

# MEASURED FACTS ABOUT YOUR OWN HARNESS

These were measured on agy 1.2.6, not assumed. They are why the rules above exist.
- A report is a CLAIM, not an artifact. adapters.py writes an honest fallback report for a lane
  that emitted nothing -- status partial, changed_paths empty, full_gate exit -1. A lane has
  delivered only when its OWNED PATH changed in its worktree. Check the file, not the report.
- A lane can read its own negative_control_cmd, so it knows the path its control expects to be
  MISSING. Creating that path makes the control pass and the gate vacuous. The host refuses to
  gate a lane whose DEVLOOP-PLANTED-* sentinel already exists; do not create one either.
- invoke_subagent works headlessly and is not gated by the permission grammar (its five actions
  are read_file, write_file, command, url, mcp -- invoke_subagent is none of them).
- Your own denials do not fail the run: a headless turn whose tools were auto-denied still
  exits 0 with status SUCCESS and an empty response. Check denied_actions.

# DUTIES, IN ORDER

1. Orient: AGENTS.md, the last LEDGER entry, TASKS.md, and the lane plan $LANES (already
   schema-validated).
2. Dispatch. $DISPATCH_RULE Native workflows and each harness's own loop commands are allowed
   inside lanes; they map onto loop stages and never replace the gates.
3. Other harnesses join through the reference orchestrator: write the non-antigravity lanes
   (claude-code, codex, gemini-cli, copilot, opencode, cursor, openai-compatible, custom)
   unchanged -- same version/base_ref/worktree_root/integration_cmd envelope -- into
   $RUN_ROOT/lanes.external.json with write_file, then run SYNCHRONOUSLY IN THE FOREGROUND, as
   EXACTLY this shape, starting with 'sh', no 'cd' prefix, no shell operators before it:
   sh $SKILL_DIR/scripts/devloop.sh $RUN_ROOT/lanes.external.json
   NEVER background it and NEVER respond while it runs; when your process ends every child lane
   dies with it. It can take many minutes. Wait for its exit code.
4. Model tiers are yours: claude-code lanes default to Opus at xhigh effort; assign lower tiers
   (worker.model 'sonnet' or a haiku id, worker.effort high) to light lanes when writing
   lanes.external.json.
5. GATE EVERY LANE YOURSELF before merging it -- adapters.py owned/gate/secrets/deps with the
   lane json and worktree -- then merge --no-ff exactly as devloop.sh does. Never trust a lane's
   own claim over the gates. A lane whose negative control PASSES is vacuous and is never
   merged. A lane whose owned path did not change did not deliver, whatever its report says.
6. On a merge conflict abort the merge and KEEP the worktree; report it, never resolve inside a
   lane.
7. Close tasks with evidence, write contract_updates into AGENTS.md, append a ledger entry, and
   end with the devloop_report JSON block reflecting the ACTUAL gate results, exit codes and
   report files on disk. status must be true: partial work is 'partial', never 'done'. A
   response that describes what you started, without that block grounded in the finished run,
   is a failed run.

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
        EVENTS_FILE=${AGY_HOST_EVENTS:-$RUN_ROOT/.devloop/native/session-events.ndjson}
        mkdir -p "$(dirname "$EVENTS_FILE")"
        set -- --prompt-file "$PROMPT_FILE" --lanes "$LANES" --run-root "$RUN_ROOT" \
               --envelope-out "$ENV_FILE" --events-out "$EVENTS_FILE" \
               --model "${AGY_HOST_MODEL:-gemini-3.1-pro-high}" \
               --effort "${AGY_HOST_EFFORT:-high}" \
               --poll-max "${AGY_HOST_POLL_MAX:-8}"
        [ "$SKIP_PERMS" = 1 ] && set -- "$@" --yolo
        # A run marker, so a monitor can tell "quiet because it is thinking" from "finished".
        # Staleness alone calls a manager inside a long run_command dead (measured: 128s silent).
        STATUS_FILE=$(dirname "$EVENTS_FILE")/session.status
        printf '{"state":"running","pid":%s,"events":"%s","started_at":%s}\n' "$$" "$EVENTS_FILE" "$(date +%s)" > "$STATUS_FILE"
        trap 'printf "{\"state\":\"finished\"}\n" > "$STATUS_FILE"' EXIT INT TERM
        if [ "$USE_TMUX" = 1 ] && command -v tmux >/dev/null 2>&1; then
            # A manager with no panes is a manager you cannot watch. devloop.sh has had a tmux
            # grid since the beginning (devloop.sh:52); the AGY path never used it, so an
            # operator's only signal was the envelope, at the end. Pane 0 runs the manager,
            # pane 1 tails the SAME event stream through agy_monitor.py.
            TSESS=${AGY_HOST_TMUX_SESSION:-devloop-agy-$$}
            tmux new-session -d -s "$TSESS" -c "$RUN_ROOT" \
                "timeout ${AGY_HOST_TIMEOUT:-4h} python3 '$SKILL_DIR/scripts/agy_session.py' $(for x in "$@"; do printf "'%s' " "$x"; done); echo; echo '[manager exited rc='\$?']'; exec sh"
            tmux split-window -t "$TSESS:0" -c "$RUN_ROOT" \
                "python3 '$SKILL_DIR/scripts/agy_monitor.py' '$EVENTS_FILE' --follow; exec sh"
            tmux select-layout -t "$TSESS:0" even-horizontal >/dev/null 2>&1 || true
            echo "agy_host: manager running in tmux session '$TSESS' (attach: tmux attach -t $TSESS)"
            echo "agy_host: event stream $EVENTS_FILE"
            echo "agy_host: status snapshot: python3 $SKILL_DIR/scripts/agy_monitor.py $EVENTS_FILE --once"
            # Wait for the manager pane so this script's exit still means what it meant before.
            while tmux has-session -t "$TSESS" 2>/dev/null && [ "$(tmux list-panes -t "$TSESS:0" -F 1 2>/dev/null | wc -l)" -gt 0 ]; do
                [ -s "$ENV_FILE" ] && break
                sleep 5
            done
            RC=0
            [ -s "$ENV_FILE" ] || RC=3
        else
            [ "$USE_TMUX" = 1 ] && echo "agy_host: tmux not found; running without panes" >&2
            timeout "${AGY_HOST_TIMEOUT:-4h}" python3 "$SKILL_DIR/scripts/agy_session.py" "$@"
            RC=$?
        fi
        rm -f "$PROMPT_FILE"
        # DEFAULT, not opt-in: a run with a transcript gets a UI element for it. The stream is
        # NDJSON in a scratch directory, which nothing will ever open; the rendered page is what
        # an operator (or a client) actually shows for the task. Rendered from the same State
        # the pane and the JSON report use, so the three cannot disagree.
        TRANSCRIPT=$(dirname "$EVENTS_FILE")/transcript.html
        REPORT_JSON=$(dirname "$EVENTS_FILE")/monitor-report.json
        TASKS_JSON=$(dirname "$EVENTS_FILE")/tasks.json
        python3 "$SKILL_DIR/scripts/agy_monitor.py" "$EVENTS_FILE" --once \
            --report-out "$REPORT_JSON" --html "$TRANSCRIPT" \
            --tasks-out "$TASKS_JSON" --lanes "$LANES" >/dev/null 2>&1
        [ -s "$TASKS_JSON" ] && echo "agy_host: task records $TASKS_JSON (mirror into the host's native task list)"
        [ -s "$TRANSCRIPT" ] && echo "agy_host: transcript $TRANSCRIPT"
        [ -s "$REPORT_JSON" ] && echo "agy_host: monitor report $REPORT_JSON"

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
