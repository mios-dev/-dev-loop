<!-- devloop-prompt
name: nested-claude-lanes
requires: CLAUDE_LANE, ADAPTERS, RUN_ROOT
summary: Appended to an Antigravity /teamwork-preview objective by agy_host.sh --teamwork when a
  `claude` binary is on PATH (opt out: AGY_HOST_CLAUDE_LANES=0, false, no or off). Tells the AGY
  manager and every teamwork agent how to run nested Claude Code CLI subagents as full dev-loop
  lanes through scripts/claude_lane.py: dispatch is detached and returns at once with a pin,
  wait blocks on a shell-written receipt, the gate is pinned, audited and two-sided, and only
  the AGY manager merges.
-->
# NESTED CLAUDE CODE LANES (available in this run)

A Claude Code CLI is installed on this machine, so any agent in this workflow -- the manager or
a teamwork agent -- may hand a well-bounded piece of work to a nested Claude Code subagent. Each
one is a FULL dev-loop lane: its own git worktree and branch, exclusive owned paths, a
two-sided gate, and a report written by the harness adapter, not by the agent. Use them for
work that splits cleanly by path; keep work that needs the whole picture inside the team.

Never start one with a bare `claude -p` from run_command. run_command moves anything still
running after about 10 seconds to the background (WaitMsBeforeAsync is CLAMPED to about
10000 ms, measured), background tasks die when your turn ends, and a Claude lane runs for
minutes. The tool below spawns each lane DETACHED, so it survives your run_command returning
and your turn ending, and it records completion as a receipt the shell writes.

## The tool

One script, absolute path, every subcommand prints ONE JSON object on stdout:

  python3 {{CLAUDE_LANE}} dispatch --root {{RUN_ROOT}} --id <id> \
      --objective-file <file> --owned <path-or-glob> [--owned ...] \
      --positive '<cmd>' --negative '<cmd>' --negative-expect '<regex>' \
      [--model opus] [--effort xhigh] [--max-turns N] [--timeout-s S] [--base REF]
  python3 {{CLAUDE_LANE}} status  --root {{RUN_ROOT}} --id <id>
  python3 {{CLAUDE_LANE}} wait    --root {{RUN_ROOT}} --id <id> [--id <id> ...] --budget-s 8
  python3 {{CLAUDE_LANE}} gate    --root {{RUN_ROOT}} --id <id> --pin <pin from dispatch>
  python3 {{CLAUDE_LANE}} collect --root {{RUN_ROOT}} --id <id>
  python3 {{CLAUDE_LANE}} list    --root {{RUN_ROOT}}
  python3 {{CLAUDE_LANE}} kill    --root {{RUN_ROOT}} --id <id>

- id: lowercase letters, digits and dashes, at most 40 characters. Ids are NEVER reused; a
  retry gets a fresh id. The lane's worktree is {{RUN_ROOT}}/.devloop/worktrees/claude-<id>
  on branch devloop/claude-<id>; its state is {{RUN_ROOT}}/.devloop/native/claude/<id>/.
- dispatch returns a `pin`. KEEP IT in your own notes and pass it to `gate --pin`: it is the
  only copy of the lane's gate definition (owned paths, both controls, the regex) that the
  lane itself cannot rewrite. A teamwork agent that dispatches a lane reports its id AND pin
  to the manager. `status`, `list` and `collect` never show it.
- Write each lane's objective to a file first (write_file), e.g.
  {{RUN_ROOT}}/.devloop/native/<id>.objective.md, and say in it exactly what done means.
- --timeout-s is the lane's wall-clock budget (minimum 30, default 1800).
- --max-turns: leave it at its default (40), or give 20 or more. Dispatch refuses anything
  below 12: the lane contract and the forced final report cost turns of their own, and a
  lane that runs out of turns is recorded partial even when its work is written (measured:
  8 turns ended partial on a trivial objective that finishes done in 7 when given 20).
- --owned is matched segment by segment: `src/lib/` or `src/lib/**` owns that whole subtree,
  `src/*.py` owns only the .py files directly in src/, `**/test_*.py` spans any depth. No
  lane may own AGENTS.md, CLAUDE.md, GEMINI.md, .git, .gitattributes, .gitignore, .gitmodules
  or anything under .devloop/; dispatch refuses a pattern that would, and a bare `*` or `**`.

## Dispatch, then wait -- so the lanes run in parallel

1. Dispatch EVERY independent lane first. Each dispatch returns within a second or two with
   its pin, worktree, branch, report path and job; the lane is already running.
2. Then wait on all of them together, with a SHORT budget so the call itself finishes inside
   run_command's foreground window:
     python3 {{CLAUDE_LANE}} wait --root {{RUN_ROOT}} --id a --id b --budget-s 8
   Exit 0: every lane reached status done. Exit 1: a lane failed or was lost. Exit 3: TIMEOUT.
   Read the JSON: a lane with still_running true has not finished yet -- call wait again
   later (another turn is fine; the lane keeps running without you). A lane with state
   timeout and still_running false ran out of its --timeout-s: it FAILED. A timeout is never
   a pass, whichever kind it is.
3. Do not report a lane as finished because you dispatched it. It is finished when wait or
   status says so. `done` means the receipt is rc 0, the report says done, and no process of
   the lane is still alive: a lane is supervised, and anything it started is killed before
   its receipt is written (`containment: subreaper` in the dispatch JSON).

## The lane contract (binding on every nested lane)

- EXCLUSIVE OWNED PATHS. No two concurrent lanes -- nested Claude lanes or teamwork agents --
  own the same path.
- NEVER TOUCH A RUNNING LANE'S WORKTREE. Its owner lock refuses other dev-loop tools (a second
  lane, a gate); it does NOT stop a raw write -- the lock is advisory, so write_file or a shell
  command into {{RUN_ROOT}}/.devloop/worktrees/claude-<id> succeeds and corrupts the lane.
- NO git add, commit or push inside a lane, and no edits to AGENTS.md. The lane prompt says so,
  and the gate refuses a lane that did any of it.
- BOTH CONTROLS ARE MANDATORY. --positive must pass on the finished worktree. --negative must
  FAIL, print text matching --negative-expect that names the planted violation, and leave
  the tree exactly as it found it -- it must restore EVERY path it touches, because a lane
  never stages, so a control that deletes a new file destroys work that exists nowhere else.
  Prefer the tool's own error for a real mutation; for a synthetic plant use the sentinel
  DEVLOOP-PLANTED-<ID> (the id uppercased), which must not exist anywhere in the tree.
  Dispatch refuses a vacuous control before anything is created: one that always exits 0,
  one identical to the positive, an empty regex, or a regex that matches everything.
- A lane branches from a COMMIT (--base, default HEAD). Uncommitted edits in the base tree
  are NOT in its worktree; commit what a lane depends on first, or put it in the objective.
- Every lane ends with a devloop_report; the adapter normalises it and it is the lane's claim,
  not proof. The gate is the strongest evidence this run has -- and it is not an OS boundary:
  a lane runs as the same user as you, so the gate detects the tampering it names below, it
  does not make tampering impossible.

## Model policy

Claude lanes default to --model opus --effort xhigh (the newest Opus). The manager may assign
lower tiers to light lanes: --model sonnet --effort high for routine edits, a haiku model for
mechanical ones. Say in your report which tier each lane ran.

## Gate, then merge -- the AGY MANAGER ONLY

The tool never stages, commits or merges. The AGY manager is the only writer to shared state.
A teamwork agent that dispatched a lane reports its id and pin to the manager; the manager
decides.

1. A lane whose state is not done is NEVER merged: failed, timeout and lost are all not-done,
   whatever its diff looks like and whatever its report claims. The gate does not even run
   its controls.
2. Run the gate yourself on every lane before merging it, with the pin from its dispatch:
     python3 {{CLAUDE_LANE}} gate --root {{RUN_ROOT}} --id <id> --pin <pin>
   What it checks, in order: the gate definition still matches the pin; git's hooks, config
   and info/ are unchanged since dispatch; the lane's branch still points at its base (no
   commit), nothing is staged, no index entry hides an edit (skip-worktree/assume-unchanged);
   every path that differs from the base -- committed, staged, unstaged or untracked, both
   sides of a rename -- is owned and is not a protected path; then the positive and the
   negative control. It does NOT see files ignored by .gitignore, writes outside the repo, or
   anything done through a process outside the lane.
   Exit 0: every check held and the lane is done. Exit 1: a check or a control failed, or the
   lane did not reach done -- do not merge. Exit 2: TAMPERED (the lane rewrote its own gate
   definition) or VACUOUS (the negative control passed, did not name the plant, or did not
   restore the tree) -- never merge. If the JSON says base_leak, the base tree changed while
   the control ran (another agent was editing {{RUN_ROOT}}); gate again when it is quiet.
   Exit 75: the lane is still running or another writer owns its worktree; wait first.
   Read `warnings`: `base_moved` lists base-tree paths that changed while the lane ran. Your
   team explains most of them; a path NO agent of this run touched means the lane wrote
   outside its worktree -- do not merge it.
3. Read `collect` -- the report and the diff stat against the lane's base -- and read the
   changed files themselves. A lane has delivered only when its owned paths changed.
4. Merge exactly as devloop.sh does, one lane at a time: in the lane worktree stage each owned
   path explicitly (git -C <worktree> add -- <path>; never add -A), run
   python3 {{ADAPTERS}} secrets --wt <worktree>, commit with hooks off
   (git -C <worktree> -c core.hooksPath=/dev/null commit -m '<message>'), then in {{RUN_ROOT}}
   run git merge --no-ff devloop/claude-<id>. On a conflict: git merge --abort, keep the
   worktree, and report it. Never resolve a conflict inside a lane.
5. Leave worktrees and lane state in place after the merge so the run can be audited. Use
   kill only on a lane you dispatched and have decided to abandon; never signal another
   agent's lane.
