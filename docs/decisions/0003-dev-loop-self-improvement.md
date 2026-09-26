---
status: proposed
date: 2026-09-26
decision-makers: [operator]
consulted:
  - "dev-loop design pass (45 proposals, P1..P6b) and its completeness critic (verdict: revise) -- condensed in the task brief; long form on the monitor's box only"
  - "mios-dev/-dev-loop origin/main 96e6578 (after #24 job-wrapper TERM fix and #25 native-UI questions); origin/claude/dev-loop-iv4399 666e35c (one commit ahead, unmerged)"
  - "mios-dev/MiOS main 96d7de8 (read-only, for P2j)"
informed: [monitor]
---
# dev-loop self-improvement

## Context and Problem Statement

A design pass scored 45 proposals for improving the dev-loop skill. A completeness critic then
returned **revise**: several premises were wrong, many controls passed on the unchanged tree, and
about twenty gaps had no row. This ADR is the revised plan. It does not implement anything.

Every premise was re-checked against `origin/main` **96e6578**. Every `file:line` below was
re-derived at that commit, unless it names another repo or ref. Main already carries #24
(job wrapper traps exit) and #25 (native-UI operator questions). One more commit sits unmerged on
`claude/dev-loop-iv4399`: 666e35c, "re-ask open questions every turn; agy 1.2.11 review-policy
spellings". It touches `hooks/stop-gate.sh`, `hooks/_chat_question.py`, `scripts/env/agy_settings.py`
and `AGENTS.md`, and items that edit those files must rebase onto it (item 9).

In the context of a multi-harness lane loop whose gates are only as strong as their controls,
facing premises that drifted and controls that proved nothing, we decided to re-plan as the
numbered items in the Decision Outcome, each with a positive control that is **red on 96e6578**
and a negative control whose failure text is dictated. We accept that items with no real captured
transcript stay **UNTESTED** until one exists.

## Decision Drivers

1. **A control that passes on the unchanged tree proves nothing** (critic). Every positive below
   is a new or extended test that FAILS on 96e6578 first. The implementer records that failure.
2. **Test doubles rule** (AGENTS.md, operator 2026-09-25). Controls replay REAL captured agy/claude
   transcripts. A scenario no real transcript contains is UNTESTED, never "proven".
3. **Minimal, one deliverable per lane** (critic: a multi-deliverable lane's single mutation
   negative proves one deliverable). An item with k deliverables is dispatched as k lanes.
4. **Model policy** (AGENTS.md). Heavy coding runs `opus --effort xhigh`, one at a time.
   Text/test-only lanes run `sonnet --effort medium`.
5. **Workers never edit `AGENTS.md`, `CLAUDE.md` or `.devloop/`.** Those rows are marked
   *monitor-owned* and go through `contract_updates`.

## Considered Options

1. **Implement the design pass as scored.** Rejected: 9 premises are wrong (see *Critic resolution*).
2. **Drop the whole pass.** Rejected: the verified gaps are real. Examples: no sibling-lane
   ownership check, no `--mutation`/`--full-gate` on nested lanes, a raw-text Bash guard, and 12
   stale line citations.
3. **Revise: re-verify, correct, split, and re-control every item** (chosen).

## Decision Outcome

Chosen option: **3**. The operator picks which numbered items to keep. The monitor asks through
the native question UI, and the questions are grouped at the end.

### Rules that bind every item

- **R1 red-before.** The positive control is a test that fails on 96e6578 and passes after the
  change. The implementer pastes the red run into the lane report.
- **R2 plants on copies.** Every negative control plants on a `mktemp -d` copy, or a `git worktree`
  of the change, never on the live tree. It must exit non-zero with the **exact text dictated
  here**, asserted verbatim (`assertIn(<text>, out)`). A line number shown as `<n>` is computed by
  the test, never hard-coded.
- **R3 what counts as a double.** Anything that plays a harness counts as a double: a fake
  `claude`/`agy` on PATH, or a hand-written transcript or `report.json`. Those replay a real
  capture from item 2. Inputs the dev-loop's *own* code consumes as data count as plain inputs, not
  doubles, and may be literal: a Python source file, a diff, a hook's stdin, a `lanes.json`, git
  repos built with `git init` in a temp dir. The one exception: when such an input claims to be
  harness output, it comes from a capture. `tests/test_claude_lane.py:30,72-84` still uses a
  FAKE `claude`, and no new control may extend it.
- **R4 one deliverable per lane.** Items marked *(k lanes)* are dispatched as k lanes, each with
  its own negative.
- **R5 dependencies are ordering, not enforcement.** Nothing enforces them until item 13 lands.
  The critic is right that `owned_problems` (`claude_lane.py:355-372`) checks only path shape and
  protected paths.

### Items

Legend: **Size** S/M/L · **Lane** the model class per AGENTS.md · **Deps** item numbers.

#### Group A: preconditions and hygiene

**1. Reconcile the ledger's unpushed claims** *(monitor-owned)*
- *What/why:* `.devloop/LEDGER.md:47-48` records "4-manager cap (live_managers.py, launcher refuses
  a 5th; both sides); quota probe/wait require the assigned tier (stub controls 6/6)". No
  `live_managers.py` exists in the tree or in any ref, and no quota stub test exists. Items 14 and
  18 would build the same things twice. The monitor pushes that work as a PR, or amends the
  ledger entry to "not pushed".
- *Files:* `skills/dev-loop/scripts/live_managers.py` + its test (if pushed), or `.devloop/LEDGER.md`.
- *Positive:* `git cat-file -e origin/main:skills/dev-loop/scripts/live_managers.py` exits 0, or the
  ledger line reads "not pushed".
- *Negative (red today):* the same command on 96e6578 exits 128 with
  `fatal: path 'skills/dev-loop/scripts/live_managers.py' does not exist in 'origin/main'`.
- *Size* S · *Lane* monitor · *Deps* none · blocks 14, 18.

**2. A real-run fixture corpus and a scrubbing capture tool** (P1a, generalised)
- *What/why:* R3 needs real captures. `tests/fixtures/transcripts/` holds only two Stop-hook turns
  (`chat-question.jsonl`, `native-ask.jsonl`), plus `open-blocker.jsonl` on the iv4399 branch. No
  `claude -p` usage-limit transcript exists (repo-wide grep for "usage limit|limit reached|hit your
  limit" returns nothing). Add `tests/fixtures/capture.py`. It copies a `claude_lane` state dir, a
  `devloop.sh` run dir or an agy session log into `tests/fixtures/runs/<name>/`, scrubs home paths
  and hostnames, writes a `MANIFEST.json` (sha256 per file, source harness and `--version`), and
  **refuses** on any secret-pattern hit. Seed captures, supplied by the monitor from its box:
  - the android-edge-node run (four dispatches, the three merged lanes' diffs, `gate --pin` logs);
  - the next real `claude -p` usage-limit exit, when one occurs (`worker.log`, `report.json`, job
    receipt, `claude --version`). It cannot be produced on demand.
- *Files:* `tests/fixtures/capture.py`, `tests/test_fixture_capture.py`, `tests/fixtures/runs/**`.
- *Positive:* `python3 -m unittest tests.test_fixture_capture`. It captures a real run dir into a
  temp output and checks that every file's sha256 matches its manifest.
- *Negative:* the test copies that run dir and appends the line `sk-ant-DEVLOOP-PLANTED-CAPTURE`
  to the copy's `worker.log`. capture.py must exit 1 with
  `SECRET IN CAPTURE: worker.log:<n> matches sk-ant-; refusing to write the fixture`.
- *Size* M · *Lane* sonnet medium · *Deps* the monitor supplies the run dirs.

**3. Stale line citations of the launcher** (P3f, widened)
- *What/why:* P3f named one stale citation. Every `devloop.sh:NN` in
  `references/run-directory.md` is stale. :16 cites `:29` (actually 40), :30 `:62` (89), :37 `:46`
  (64-65), :39 `:210` (328), :41 `:45` (63), :52 `:140` (178), :53 `:72,:94,:127,:148`
  (99,122,165,186), and :64 `:31` (42). More stale citations sit in `harness-adapters.md:182`,
  `agy_monitor.py:9` and `agy_host.sh:303` (`devloop.sh:52`), and `job.py:20-21` (`devloop.sh:49,:58`).
  Replace each with a symbol anchor (``devloop.sh `launch()` ``, `` `BASE_SNAP` ``), and forbid
  numeric citations of files that move.
- *Files:* the five above, plus a new `tests/test_line_citations.py`.
- *Positive:* `python3 -m unittest tests.test_line_citations`. It is red on 96e6578, naming 12
  citations.
- *Negative:* the test writes a copy of `run-directory.md` into a temp tree and appends the text
  `devloop.sh:46`. It must fail with
  `STALE LINE CITATION: devloop.sh:46 in skills/dev-loop/references/run-directory.md:<n> -- cite a symbol, not a line`.
- *Size* S · *Lane* sonnet medium · *Deps* none.

**4. Dangling script names in AGENTS.md** (P5h, corrected)
- *What/why:* `AGENTS.md:178`, inside the cloud-reclaim paragraph at :173-179 (the design pass's
  citation had moved), cites `wait_done.py`, which exists nowhere in the repo. The critic is right
  that a scan of `scripts/` alone flags legitimate names. At 96e6578 AGENTS.md cites 13 `.py`
  names: 7 in `tests/`, 1 in `scripts/env/` (`agy_settings.py`), 4 in `scripts/`, and
  `wait_done.py` in no directory. The test therefore resolves each `<name>.py` token against the
  basenames of **all** tracked files (`git ls-files`). On 96e6578 it flags exactly `wait_done.py`.
  The AGENTS.md fix is a `contract_updates` entry: it names the real blocking command, or drops
  the parenthetical.
- *Files:* `tests/test_contract_refs.py` (worker); `AGENTS.md:178` (monitor).
- *Positive:* `python3 -m unittest tests.test_contract_refs`. It is red today with
  `DANGLING SCRIPT REFERENCE: wait_done.py (AGENTS.md:178) matches no tracked file`, and green after
  the monitor's edit.
- *Negative:* a temp copy of AGENTS.md with the appended line `see not_a_script.py` must fail with
  `DANGLING SCRIPT REFERENCE: not_a_script.py (AGENTS.md:<n>) matches no tracked file`.
- *Size* S · *Lane* sonnet medium · *Deps* none.

**5. Retire `scripts/contracts.py`** (split out of P4b; critic: the shims fell outside its paths)
- *What/why:* `contracts.py` (47 lines) is an unused polling file bus: `import contracts` finds
  nothing, and `__main__` only prints "[dev-loop] Contracts bus ready." It is cited in **seven**
  shims, not six: `shims/{claude,codex,antigravity,opencode}/verify.md`, `shims/gemini/verify.toml`,
  `shims/copilot/verify.prompt.md`, and `shims/cursor/verify.mdc:18`. It is also cited in
  `README.md:8`, `skills/dev-loop/SKILL.md:9`, `skills/verify/SKILL.md:85` and
  `references/upstream-patterns.md:113`. The critic is right that the design pass's controls used
  `tests/test_stale_refs.py`, which only builds synthetic temp trees (`tmp_tree()`, :58-72) and
  never scans the repo. The new test scans the real tracked tree.
- *Files:* delete `skills/dev-loop/scripts/contracts.py`; edit the 11 citing files; add
  `tests/test_retired_names.py`, with `RETIRED = {"contracts.py": "item 5"}`.
- *Positive:* `python3 -m unittest tests.test_retired_names` passes. Red today, it names all 11 citations.
- *Negative:* a temp copy of `shims/cursor/verify.mdc` with the appended line `contracts.py` must fail with
  `RETIRED NAME: contracts.py cited at shims/cursor/verify.mdc:<n>`.
- *Size* S · *Lane* sonnet medium · *Deps* none.

#### Group B: the lane contract and the report

**6. One canonical lane contract, word-for-word on all five surfaces** (P5c, corrected)
- *What/why:* the design pass's sentence, "NEVER WRITE TO ANOTHER CHECKOUT: no file write in any
  directory outside your worktree", forbids the `mktemp` copies every negative control plants on,
  and the temp sandboxes that 39 of the 47 test files build. The rule also exists on **five**
  surfaces, not four, and they already disagree:
  - `adapters.lane_prompt` (`adapters.py:207-229`);
  - `devloop_worker.build_system` (`devloop_worker.py:177-179`);
  - `agents/lane-worker.md:13` (forbids `checkout` too; lane_prompt does not);
  - `assets/templates/prompts/nested-claude-lanes.md:76-93`;
  - `SKILL.md` §11 (:415-417).

  Parity tests today cover only lane_prompt (`tests/test_lane_prompt.py:60-87`) and the nested
  template (`tests/test_claude_lane.py:815-845`). Put the canonical lines in
  `skills/dev-loop/assets/lane-contract.txt`, and have each surface carry them verbatim.
  The corrected sentence:
  > NEVER WRITE OUTSIDE YOUR WORKTREE AND SCRATCH: no write inside another git checkout (a
  > directory whose `git rev-parse --show-toplevel` is not your worktree) and none to host state
  > (home-directory config, keyrings, service units, /etc). Scratch is allowed: `mktemp -d` under
  > `$TMPDIR`, which is where negative controls plant their copies.

  Whether this binds the monitor session is an open question (Q-C). As written, it binds lanes only.
- *Files:* `assets/lane-contract.txt`, `adapters.py`, `devloop_worker.py`, `agents/lane-worker.md`,
  `nested-claude-lanes.md`, `SKILL.md`, and a new `tests/test_lane_contract_parity.py`.
- *Positive:* `python3 -m unittest tests.test_lane_contract_parity` passes. It is red today on all five surfaces.
- *Negative:* a temp copy of `agents/lane-worker.md` with that line deleted must fail with
  `LANE CONTRACT DRIFT: agents/lane-worker.md lacks canonical line 'NEVER WRITE OUTSIDE YOUR WORKTREE AND SCRATCH'`.
- *Size* M · *Lane* sonnet medium (text only; the schema change is item 7) · *Deps* none.

**7. Report fields `host_state_changes` and `shared_interfaces`** (P5d)
- *What/why:* neither field exists (a repo-wide grep returns 0 hits). A lane that edits host state
  has no field to say so, and the gate cannot warn. Add both fields to the `report` tool: its
  properties and its `required` list (`openai-tools.json:283-298`, `strict: true`). Also add them to
  `REPORT_KEYS` and the defaults (`adapters.py:67-68,454-455`), to `devloop_worker.py:261`, and to
  the SKILL §13 example (:533-543). `collect` prints both. The gate prints
  `WARN host_state_changes: <list>` when the list is non-empty; it is never a pass/fail input.
- *Files:* the four above, plus `tests/test_report_schema_parity.py` and `tests/test_lane_prompt.py`.
- *Positive:* `python3 -m unittest tests.test_report_schema_parity`, extended: it is red today
  because §13 lacks the keys. A `normalize_report` case fills `[]` for a report missing them. Its
  input is a real `report.json` from item 2, not a hand-written one.
- *Negative:* in a temp copy of `openai-tools.json`, drop `host_state_changes` from `required`. The
  test must fail with `REPORT SCHEMA DRIFT: host_state_changes is in SKILL.md §13 but not required by openai-tools.json report`.
- *Size* M · *Lane* opus xhigh (touches 4 code/schema surfaces) · *Deps* 2, 6.

**8. A consumer for `contract_updates`** (critic MISSING)
- *What/why:* nothing reads the field back. It appears only in schemas and prompts
  (`openai-tools.json:283,390`, `system.md:117`, `manager.md:144`, `SKILL.md:172,540`), in defaults
  (`adapters.py:68,454`; `devloop_worker.py:261`), and in a deny message (`hooks/no-env.sh:5`), so
  the lane-to-host channel is write-only. `claude_lane.py collect` and `devloop.sh`'s end-of-run
  step will append every non-empty `contract_updates` to `<run>/contract-updates.md`, one line per
  update, in the form `- [<lane id>] <text> (report: <path>)`. The manager still edits AGENTS.md
  itself; the file is its to-do list.
- *Files:* `claude_lane.py` (collect), `adapters.py` (a `contract-updates` subcommand that
  devloop.sh calls), `devloop.sh`, and a new `tests/test_contract_updates.py`.
- *Positive:* over a real report from item 2 that carries a non-empty `contract_updates`, the file
  holds that line. Red today: the subcommand does not exist. If item 2 yields no such report, this
  control is **UNTESTED** and the item waits.
- *Negative:* on a copy of that report with `contract_updates` set to `[]`, the test asserts the
  update line is absent and the tool prints `contract-updates: 0 from 1 report(s)`. The test's
  planted-failure mode reverts the append and must fail with
  `CONTRACT UPDATES LOST: 1 in reports, 0 in contract-updates.md`.
- *Size* S · *Lane* sonnet medium · *Deps* 2.

**9. `blocked` means "outside this session's control"** (P5e)
- *What/why:* SKILL §12 (:510) defines `blocked` as "Blocker requires operator". §5 (:217) makes it
  the lane's question channel. `agents/lane-worker.md` never mentions `blocked` (only `budget` and
  `converged_stuck`, :17). `system.md` (:147) says "blocked on a decision, a credential, or an
  external system". The Stop hook's partial re-arm text (`hooks/stop-gate.sh:45`) says "blocked
  (needs the operator)". MiOS's `usr/share/mios/ai/system.md` has no `blocked` at all; that gap is
  a cross-repo row in item 26. Use one definition on all four in-repo surfaces: "`blocked`: the
  next step is outside this session's control (the operator, a credential, an external event);
  `next` names the event and the command that polls it". Rebase onto 666e35c first, because it
  edits `stop-gate.sh`.
- *Files:* `SKILL.md`, `hooks/stop-gate.sh`, `agents/lane-worker.md`,
  `assets/templates/prompts/system.md`, and a new `tests/test_status_vocabulary.py` (absent today).
- *Positive:* `python3 -m unittest tests.test_status_vocabulary`. It is red today on all four surfaces.
- *Negative:* a temp copy of `system.md` without the definition must fail with
  `STATUS VOCABULARY DRIFT: skills/dev-loop/assets/templates/prompts/system.md does not define blocked`.
- *Size* S · *Lane* sonnet medium · *Deps* 666e35c merged; 6 (same files, serialise).

#### Group C: guards and dispatch-time refusals

**10. `guard.sh` scans only the text that executes** (P5a)
- *What/why:* `hooks/guard.sh:3-9` greps the raw command. It does no heredoc or quote stripping
  (`_lib.sh` holds only `json_get` and `deny`), so a commit message or a heredoc body that mentions
  `git add -A` is denied. Add `exec_text` to `_lib.sh`. It drops the bodies of quoted-terminator
  heredocs (`<<'EOF'`) and single-quoted strings. It keeps unquoted heredocs and `$(...)`. On any
  parse doubt it returns the raw text (fail closed).
- *Files:* `hooks/_lib.sh`, `hooks/guard.sh`, `tests/test_guard_hooks.py`.
- *Positive:* a PreToolUse stdin whose command is a real captured Bash `tool_use` (item 2) that
  carries `git add -A` inside a `<<'EOF'` commit-message body is allowed. It is red today (denied).
  With no such capture, this case is **UNTESTED**, and the item's shipped control is the negative
  only.
- *Negative:* the stdin command `sh <<EOF\ngit add -A\nEOF` (unquoted, so it executes) must still
  be denied with the existing text, verbatim:
  `dev-loop: explicit-path staging only — never git add -A / . / -u (SKILL §12). Use git add <path>.`
  A second case uses an unbalanced quote. It must be denied by the raw fallback with the same text.
- *Size* M · *Lane* opus xhigh · *Deps* 2 (for the positive).

**11. A git-verb fence for lanes** (P5b, corrected)
- *What/why:* premise corrected. `tests/test_mios_init.py` does **not** fetch into the operator's
  sibling checkout: its only `git fetch --depth 1` runs in a fresh temp dir, behind
  `MIOS_INIT_LIVE=1`, and asserts the operator's `.git/shallow` and `FETCH_HEAD` are unchanged
  (:365-384). `mios-init.sh` clones missing siblings only and leaves existing ones as they are
  (:283, :295). The real motivation: "no git add/commit/push/rebase/reset" (`adapters.py:216`,
  `lane-worker.md:13`) is prose, and `guard.sh` fences only `add -A` and `push --force` (:4-5).
  - `adapters.cmd_run` and `claude_lane` supervise will export `DEVLOOP_LANE_ROOT=<worktree>`.
    `DEVLOOP_LANE_ROOT` is absent from the repo today; `cmd_run`'s env is `adapters.py:767-770`.
  - With it set, guard.sh denies git write verbs: add, commit, push, reset, rebase, checkout,
    switch, merge, stash, clean, worktree add/remove, and clone into a target.
  - **Scratch carve-out** (critic): the deny is lifted when the resolved target is under
    `${TMPDIR:-/tmp}`, so `git init` sandboxes and planted copies still work.
  - Read verbs are always allowed, and the fence is inert when the variable is unset.
- *Files:* `hooks/guard.sh`, `hooks/_lib.sh`, `adapters.py`, `claude_lane.py`, `tests/test_guard_hooks.py`.
- *Positive:* with `DEVLOOP_LANE_ROOT` set, `git -C "$(mktemp -d)" init` and `git status` are
  allowed. With it unset, `git commit` is allowed. Red today: no variable, no fence.
- *Negative:* with `DEVLOOP_LANE_ROOT=<wt>` set, `git -C <wt> commit -m x` must be denied with
  `dev-loop: lanes never run git commit (lane contract); the host commits. Scratch under $TMPDIR is exempt.`
- *Size* M · *Lane* opus xhigh · *Deps* 10 (parses exec_text), 6.
  **UNTESTED** for agy lanes: hooks run only where the harness runs them.

**12. Exclusive `owned_paths` across live nested lanes** (critic MISSING)
- *What/why:* `claude_lane.py cmd_dispatch` (:695-846) checks only its own id. It never reads a
  sibling's `meta.json`, and only `cmd_list` (:892-909) iterates the state dirs. Dispatch will read
  every sibling whose branch `devloop/claude-<id>` still exists and whose tip is not an ancestor of
  `--base`, and refuse any overlap. Two patterns overlap when one literal (pre-glob) prefix is a
  segment prefix of the other, which is the conservative rule. This runs before the spawn.
- *Files:* `claude_lane.py`, `nested-claude-lanes.md` (lines 78-79 become enforced), and a new
  `tests/test_claude_lane_ownership.py`.
- *Positive:* one sibling state dir holds a real `meta.json` from item 2, and the test gives its
  branch a real commit with `git`. A dispatch whose `--owned` is disjoint from it is not refused.
  The test uses a `--check-only` flag, added by this item, which runs every pre-spawn check and
  exits before the spawn, so no harness runs. Red today: the flag does not exist.
- *Negative:* `--owned src/net` against a sibling owning `src/net/**` must exit 65 with
  `OWNERSHIP OVERLAP: --owned 'src/net' overlaps live lane '<id>' ('src/net/**'); serialise with --requires or wait`.
- *Size* M · *Lane* opus xhigh · *Deps* 2.

**13. `--requires <id>`: dependencies enforced at dispatch** (critic WRONG: "nothing enforces it")
- *What/why:* dispatch refuses unless lane `<id>`'s branch tip is an ancestor of `--base`
  (`git merge-base --is-ancestor`). The tool never merges (`claude_lane.py:103`), so ancestry is
  the only merge evidence it has.
- *Files:* `claude_lane.py`, `nested-claude-lanes.md`, and `tests/test_claude_lane_ownership.py`
  (shared with 12).
- *Positive:* in a temp git repo, lane `a`'s branch is merged into base and
  `--requires a --check-only` exits 0. Red today: unknown flag, rc 64.
- *Negative:* the same with `a` unmerged must exit 65 with
  `REQUIRES UNMET: lane 'a' (devloop/claude-a @ <sha12>) is not in base <sha12>`.
- *Size* S · *Lane* opus xhigh (the same lane as 12, serialised) · *Deps* 12.

**14. Heavy-model admission control, one knob** (P4a, corrected)
- *What/why:* the only throttle today is `devloop.sh` `MAX_CONCURRENT` (default 4, :302-313), which
  counts only that run's jobs. `claude_lane.py` has no cap. The design pass spread one policy over
  three names (`max_heavy`, `MAX_HEAVY`, `DEVLOOP_HEAVY_MODELS`/`DEVLOOP_HEAVY_MAX`). One
  definition in `adapters.py`:
  - *heavy* = worker model ∈ `DEVLOOP_HEAVY_MODELS` (default `opus`).
  - The cap resolves in this order: CLI `--max-heavy`, then lanes.json run-level `max_heavy`, then
    `DEVLOOP_HEAVY_MAX`, then the default 1. The name `MAX_HEAVY` is dropped.
  - `claude_lane.py dispatch` refuses with rc 75, which already means busy there (`EX_BUSY`,
    `claude_lane.py:194`). `devloop.sh` waits instead, the way `MAX_CONCURRENT` does.

  Whether this also counts the AGY fleet (4 managers, 2 teamwork) is Q-C.
- *Files:* `adapters.py`, `claude_lane.py`, `devloop.sh`, `lane-schema.json`, `tests/test_admission.py`.
- *Positive:* no live heavy lane, so `--check-only` exits 0. Red today: unknown flag.
- *Negative:* with one live sibling whose real `meta.json` (item 2) says `model: opus`, a second
  opus dispatch must exit 75 with
  `ADMISSION REFUSED: 1 heavy lane live (<id>, opus); DEVLOOP_HEAVY_MAX=1. Nothing was created.`
  The test then asserts that the lane's state dir does not exist.
- *Size* M · *Lane* opus xhigh · *Deps* 1, 2, 12.

**15. `--mutation` and `--full-gate` on `claude_lane.py dispatch`** (P2g)
- *What/why:* the dispatch parser (`claude_lane.py:1207-1217`) has neither flag, and the spec it
  builds (:740-750) carries neither key. `adapters.py cmd_gate` runs both when a lane sets them
  (:863-886), so nested Claude lanes never get either gate.
- *Files:* `claude_lane.py`, `nested-claude-lanes.md`, `tests/test_claude_lane_ownership.py`.
- *Positive:* `dispatch --check-only --full-gate 'true'` writes `full_gate_cmd` into `lane.json`.
  Red today: unknown flag.
- *Negative:* `adapters.py gate` run on the `lane.json` that dispatch wrote with
  `--full-gate 'exit 3'`, in a temp worktree whose positive and negative hold, must exit 1 with
  the existing text `full gate: FAIL (exit 3)`.
- *Size* S · *Lane* opus xhigh · *Deps* 12 (`--check-only`).

**16. Close the `|| true` gap in the vacuous-negative refusal** (P2i, corrected)
- *What/why:* P2i "already-exists" is half right. `claude_lane.py` refuses statically at dispatch
  (`ALWAYS_TRUE` :173, `vacuous_reasons` :376, called at :753), but the check is a whitespace-
  normalised exact match, so `cmd || true` passes. The only static check in `adapters.py` is the
  pre-run sentinel check (:839-845). Every other vacuity is caught only after the lane ran
  (:859). Add the tail forms `|| true`, `|| :`, `; true`, `; exit 0`, and `|| exit 0` to
  `vacuous_reasons`, and add the same rule to `adapters.validate_spec`.
- *Files:* `claude_lane.py`, `adapters.py`, `tests/test_claude_lane.py` (pure-function cases only,
  no fake claude).
- *Positive:* `vacuous_reasons("pytest", "pytest tests/x.py -k plant", "PLANT")` returns `[]`. It
  already passes, so this is not the red-before test; the negative is.
- *Negative (red today):* `vacuous_reasons("pytest", "pytest -k plant || true", "PLANT")` must return
  `["negative control 'pytest -k plant || true' ends in '|| true', so it can never fail"]`.
- *Size* S · *Lane* sonnet medium · *Deps* none.

#### Group D: static invariants in the gate (P2a-P2f, split per R4)

Critic W3, "who is flagged", re-derived. `claude_lane.py cmd_gate` runs
`adapters.py gate` as a subprocess of the **manager's** process (`claude_lane.py:1105-1107`), and
`adapters` runs the controls with `cwd=<worktree>`. The invariant pass therefore scans the
**lane's** added lines (worktree diff against the pinned base) and flags the lane's code. The
manager is only the process that runs it. Waivers are read from the **base commit**
(`git show <base>:.devloop/invariants.json`), never from the worktree or the manager's uncommitted
tree: `.devloop/` is protected from lane ownership (`owned_problems`, :365-371), and a base-commit
read also shuts out an uncommitted edit. `assertion_helpers` defaults to `[]`, so nothing has to
be written before dispatch.

**17. `lane_invariants.py`: added-line scoper plus the facade-test family** (P2a, extended)
- *What/why:* the incident the design pass cites is string-presence tests
  (`assert "socket" in c` over a file's text). The proposed rules (ASSERTION_FREE,
  CONSTANT_ONLY_ASSERT, MOCK_ONLY_ASSERT, NO_SUBJECT, UNPARSEABLE) have no rule for that shape, so
  add **SOURCE_TEXT_ASSERT**: a test reads a source file as text and asserts substring presence.
  The scope is the added lines of Python test files.
- *Files:* `skills/dev-loop/scripts/lane_invariants.py`, `tests/test_lane_invariants.py`.
- *Positive:* exit 0 over a real, good test diff: commit 196894c's additions to
  `tests/test_stop_gate.py`. Red today: the script does not exist.
- *Negative:* over the android-edge-node lanes' real test files (item 2), it must exit 1 with a line
  `SOURCE_TEXT_ASSERT <file>:<n>: asserts a substring of a source file's text; call the code instead`.
- *Size* M · *Lane* opus xhigh · *Deps* 2.

**18. `lane_invariants.py`: literal family** (P2b, P2j corrected)
- *What/why:* P2j "already-exists" is **wrong as stated**. MiOS has a Python check,
  `tools/drift-checks.py:1711` `check_no_bare_port_literals`, called by
  `automation/98-drift-checks.sh:851`. It bans only 6 ports (11450, 11441, 11440, 11451, 11434,
  11435), scans only 3 directories, and exempts 11 filenames. The Rust port,
  `src/mios-rs/miosd/src/drift/ports.rs:19-29`, returns
  `Verdict::Skip("NOT IMPLEMENTED: No bare port literals")`. So a lane's `full_gate_cmd` catches a
  bare port only if it calls the shell/Python runner, only for those 6 ports, and only in those 3
  directories. The literal family is therefore needed in the gate:
  - BARE_PORT: fail, in port context or URL form only.
  - HARDCODED_IP: fail, with the built-in allowlist printed (loopback, and the IANA multicast
    groups that protocols such as mDNS fix).
  - HARDCODED_HOST: warn. DATE_LITERAL: off.
  - Scope: added non-test lines. An optional `port_ssot` lets a repo name its SSOT.
- *Files:* `lane_invariants.py`, `tests/test_lane_invariants.py`.
- *Positive:* exit 0 over the real added lines of a -dev-loop commit that has no literals
  (e.g. 219049e). Red today: the family does not exist.
- *Negative:* in a temp copy, add `sock.connect(("10.0.0.7", 8443))` to a non-test file. The check
  must exit 1 with two lines:
  `BARE_PORT <file>:<n>: 8443 in port context; read it from the repo's port SSOT` and
  `HARDCODED_IP <file>:<n>: 10.0.0.7 is not in the builtin allowlist`.
- *Size* M · *Lane* opus xhigh · *Deps* 17.

**19. Wire invariants into both gates, before the controls** (P2c)
- *What/why:* `adapters.py cmd_gate` runs the pass after the ownership check and before the
  positive control (:822). On findings it exits 1 and writes `inv-<id>.log`. `claude_lane.py`
  `gate.skipped` (:1096-1103) gains
  `"invariants: <n> finding(s) (see inv-<id>.log): the controls were not run"`. There is no
  `--no-invariants` flag; waivers are the only escape (item 20).
- *Files:* `adapters.py`, `claude_lane.py`, `tests/test_lane_invariants.py`.
- *Positive:* gating a temp worktree with a clean real diff (item 17's positive) still prints
  `positive: PASS`. Red: the invariants line `invariants: 0 finding(s)` is asserted and is absent today.
- *Negative:* the same worktree plus a planted `assert "x" in open(__file__).read()` in a test
  file must exit 1 with `invariants: 1 finding(s) (see inv-<id>.log): the controls were not run`,
  and `pos-<id>.log` must not exist.
- *Size* S · *Lane* opus xhigh · *Deps* 17, 18.

**20. Waivers v1: `.devloop/invariants.json` at the base commit** (P2d)
- *What/why:* itemised entries `{rule, path, line_text_sha256, reason}`. The gate prints
  `waivers_used`/`waivers_unused`. An unused waiver fails the repo's own test, so stale waivers
  cannot pile up. The file lives under `.devloop/`, so **the monitor writes it**; the worker
  delivers the reader and the test. P2e (lane-pinned waivers) stays do-later.
- *Files:* `lane_invariants.py`, `tests/test_lane_invariants.py`; `.devloop/invariants.json` (monitor).
- *Positive:* a finding covered by a waiver in the base commit exits 0 and prints
  `waivers_used: 1`. Red today: no waiver support.
- *Negative:* a base-commit waiver whose sha256 matches no added line must fail with
  `STALE WAIVER: BARE_PORT <path> (<reason>) matched nothing; delete it`. A waiver present only in
  the worktree must be ignored, and the finding must fail as in item 18.
- *Size* S · *Lane* opus xhigh · *Deps* 19.

**21. Coverage map, and a `gate_audit.py --diff` decision** (P2f; critic MISSING: --diff)
- *What/why:* add a third table to `references/gate-audit.md` (today: the mechanical table
  :14-22, the judgment table :32-39, and "Keeping this file honest" :41) that maps the §7 judgment
  rows lane_invariants now detects on added lines: Assertion-Free Test, Mock-Only Coverage, and
  Measuring the Wrong Property via SOURCE_TEXT_ASSERT. Rewrite the "NOT DETECTED" text at
  `gate_audit.py:24-28` to name them. The `--list-rules` parity test covers both scripts.
  **Decision on `--diff`:** do-later. It would reuse item 17's scoper, but gate_audit's target is
  standing gates, not lane diffs, so no current caller needs it.
- *Files:* `references/gate-audit.md`, `gate_audit.py` (docstring only), `tests/test_gate_audit.py`.
- *Positive:* the extended parity test passes. Red today: there is no third table.
- *Negative:* a temp copy of `gate-audit.md` with the SOURCE_TEXT_ASSERT row deleted must fail with
  `COVERAGE MAP DRIFT: lane_invariants rule SOURCE_TEXT_ASSERT has no row in references/gate-audit.md`.
- *Size* S · *Lane* sonnet medium · *Deps* 17.

#### Group E: freshness and merging

**22. Freshness at dispatch, never touching the base working tree** (P3a, corrected)
- *What/why:* the critic is right that a dirty base is a NOTE, not a refusal
  (`claude_lane.py:832-846`, `base_tree_dirty`, rc 0). In a teamwork run other agents edit the
  base, so "fast-forward the base" must never touch ROOT's working tree. The dev-loop has no fetch
  anywhere today. `claude_lane.py dispatch --fresh` works like this:
  1. Resolve `--base`. If it is a branch with an upstream, `git fetch` that upstream.
  2. If the local tip is an ancestor of the upstream tip, cut the lane from the upstream tip.
     Otherwise cut it from the local tip, and record `diverged`.
  3. When `--base` is a SHA or HEAD is detached, record `freshness: "n/a: base is a commit"`
     (critic: pull-latest target).
  4. A failed fetch is recorded, never blocking. No `--depth`.

  The result goes in `meta.json` under `freshness`
  (`{fetched, behind, cut_from, note}`). `devloop.sh` gets the same behaviour through
  `DEVLOOP_FRESH=1`. Default: off, pending Q-B.
- *Files:* `claude_lane.py` (a pure `freshness(root, base)` function, so the control needs no
  harness), `devloop.sh`, `tests/test_freshness.py`.
- *Positive:* in a temp repo with a bare `origin` one commit ahead, `freshness()` returns
  `behind: 1` and a `cut_from` equal to the origin tip. Red today: the function does not exist.
- *Negative:* with the local branch diverged from origin, the plant is a test variant that
  (wrongly) cuts from origin anyway. It must fail with
  `FRESHNESS: local main is not an ancestor of origin/main (diverged); refusing to cut from origin`.
  A second case with a detached base must return `n/a: base is a commit`.
- *Size* M · *Lane* opus xhigh · *Deps* none.

**23. Merge preview at gate time, and a git-version probe** (P3b; critic MISSING: git ≥ 2.38)
- *What/why:* `git merge-tree --write-tree` (git ≥ 2.38) computes the merge without touching any
  tree. Measured today: the cloud VM host has **git 2.43.0**, and the MiOS dev image
  (`mios-dev:base`, Fedora 44) has **git 2.55.0** (`git-core-2.55.0-1.fc44`). The devcontainer is
  that same image (`.devcontainer/Containerfile:22`). `adapters.py probe` does not report git
  today (`cmd_probe` :960-974). Add it there, and have the preview refuse below 2.38.
  `claude_lane.py gate` adds `merge_preview: {behind, conflicts, both_touched}` and exits 1 on
  conflict. `--fresh` fetches first, opt-in.
- *Files:* `adapters.py` (probe and a `merge-preview` subcommand), `claude_lane.py`, `devloop.sh`
  (preview before `merge_lane`, :257), `tests/test_freshness.py`.
- *Positive:* two temp branches touching different files give `conflicts: []` and rc 0. Red today:
  no subcommand.
- *Negative:* two branches editing the same line must exit 1 with
  `MERGE PREVIEW: conflict in a.txt against main@<sha12>; not merging`. A second case sets
  `DEVLOOP_GIT_VERSION_OVERRIDE=2.37.0`, a test seam added by this item, and must exit 64 with
  `git >= 2.38 required for merge-tree --write-tree (found 2.37.0)`.
- *Size* M · *Lane* opus xhigh · *Deps* 22.

**24. Launcher base hygiene: ROOT branch, stale reused branches, PowerShell parity** (P3c; critic MISSING)
- *What/why:*
  1. `devloop.sh` never checks that ROOT has `base_ref` checked out; a repo-wide search for
     `symbolic-ref`/`abbrev-ref` finds nothing. `merge_lane` merges into whatever ROOT has checked out (:273).
  2. It attaches to a pre-existing `lane/<id>` branch without resetting it to BASE (:84), and says
     nothing about how far behind that branch is.
  3. `DevLoop.ps1:39` reuses an existing worktree without cleaning it, and has no owner-lock refusal
     (devloop.sh has one, :73-78).

  The fix: refuse on a branch mismatch when `base_ref` is a branch name. Print the behind-count of
  a reused branch, and refuse when it is behind unless `DEVLOOP_REUSE_STALE=1`. Port the clean and
  the owner lock to PowerShell. The checks run before the `DRY` return, so `--dry-run` exercises
  them without a harness.
- *Files:* `devloop.sh`, `DevLoop.ps1`, `tests/test_launcher_base.py`.
- *Positive:* in a temp repo on `main` with `base_ref: main`, `devloop.sh --dry-run` exits 0 and
  prints `== lane x`. Red: the assertion on the new line `base main checked out at <sha12>` fails today.
- *Negative:* ROOT on branch `other` must exit 64 with
  `refusing: ROOT has other checked out but base_ref is main`. A stale `lane/x` two commits behind
  must exit 64 with `refusing: lane/x is 2 commit(s) behind main (set DEVLOOP_REUSE_STALE=1 to reuse)`.
  **UNTESTED** for DevLoop.ps1 where `pwsh` is absent (the test skips, and says so).
- *Size* M · *Lane* opus xhigh · *Deps* 23.

**25. A base for `isolation: worktree` lanes** (critic MISSING)
- *What/why:* `agents/lane-worker.md` (frontmatter `isolation: worktree`, :5) says nothing about
  the base ref or freshness. A harness-native worktree forks from whatever the session has checked
  out. The first step of lane-worker becomes: record `git -C . rev-parse HEAD` as `base_sha` in the
  report (a new report key, added with item 7). `agents/orchestrator.md` refuses to merge when
  `base_sha` differs from the base it planned.
- *Files:* `agents/lane-worker.md`, `agents/orchestrator.md`, `openai-tools.json`, `adapters.py`.
- *Positive:* a real captured Claude Code `Agent(isolation: worktree)` lane transcript (item 2)
  normalises to a report whose `base_sha` equals the fork point. **UNTESTED** until such a capture
  exists. This worker session has the Agent tool with worktree isolation, so the monitor can capture one.
- *Negative:* the same report with `base_sha` edited on a copy must make the orchestrator check fail
  with `BASE MISMATCH: lane forked from <sha12>, plan expected <sha12>; not merging`.
- *Size* S · *Lane* sonnet medium · *Deps* 2, 7.

**26. Typed gate verdict instead of a substring** (critic MISSING: stringly-typed `base_leak`)
- *What/why:* `claude_lane.py:1111` derives `base_leak` as
  `"BASE TREE LEAKAGE" in (stdout + stderr)`, from the text `adapters.py` prints at :857-858,
  :872-873 and :884-885. Have `adapters.py gate` write `<run>/gate-<id>.json`
  `{rc, verdict: pass|fail|vacuous|leak|broken_control|invariants, reason, strays}`, and
  have claude_lane read that file. Remove the substring match.
- *Files:* `adapters.py`, `claude_lane.py`, `tests/test_lane_isolation_leakage.py`.
- *Positive:* when a manager-supplied negative control edits a base-tree file (the manager's own
  command, not a harness double), `gate-<id>.json` has `verdict: "leak"` and claude_lane reports
  `base_leak: true`. Red today: there is no file.
- *Negative:* the negative control's `negative_expect` is the literal text `BASE TREE LEAKAGE`,
  and the tree has no leak. The gate prints that text in its "did NOT name" message. claude_lane
  must report `base_leak: false`. The planted revert, back to the substring match, must fail with
  `TYPED VERDICT IGNORED: base_leak true but gate-<id>.json verdict is vacuous`.
- *Size* S · *Lane* opus xhigh · *Deps* 19 (same function; serialise).

#### Group F: interfaces and documentation

**27. Declared interfaces and a pre-merge integration check** (P4b without the retirement; critic MISSING: review.py)
- *What/why:* lanes declare `provides`/`consumes`; neither exists in `lane-schema.json`, whose lane
  properties are listed at :163-238. The run declares `interfaces.check_cmd`. Before a wave
  merges, `adapters.py integrate` merges the wave's branches into a throwaway worktree and runs the
  check. If it fails, **no** lane of that coupled wave merges. `review.py:312-317` currently
  escalates on the substrings `"class "`, `"interface "`, `"schema"`, `"API"` and `"Contract"` in
  the raw diff. It will read `provides`/`consumes` when a lane has them, and keep the substring
  check as a fallback labelled `heuristic` in its reasons. P5g (claude_lane integrate) is folded
  into this item.
- *Files:* `lane-schema.json`, `adapters.py`, `devloop.sh`, `review.py`, `tests/test_integrate.py`.
- *Positive:* two temp branches, where `b` consumes the function `a` provides, pass
  `check_cmd = python3 -c 'import a; a.f()'` and both merge. Red today: no subcommand.
- *Negative:* `a` renames `f` on a copy, so the check fails. It must exit 1 with
  `INTEGRATION FAILED: interfaces.check_cmd exit 1 on wave 1 (a, b); no lane of this wave merged`,
  and neither branch may be merged.
- *Size* L *(2 lanes: adapters/devloop, then review.py)* · *Lane* opus xhigh · *Deps* 5, 23.

**28. Document the proposer shape that works today, and the Workflow-tool host** (critic MISSING; P4f)
- *What/why:* research lanes plus `depends_on` plus `read_paths` (`lane-schema.json:197`, already
  used in `lanes.agy-manager.example.json:21,59`) already give propose-then-apply. Document that
  shape in `harness-adapters.md` §3, with `assets/lanes.proposer.example.json`. Add a paragraph on
  a Claude Code **Workflow**-tool host: §3 has no entry for it today (a grep for "Workflow tool"
  returns 0 hits). The tool is observed in this cloud worker session's tool list; in AGY and in
  other cloud sessions it is unverified (Q-C). P4c/P4d (proposer and gatekeeper roles) stay
  do-later, behind item 27.
- *Files:* `references/harness-adapters.md`, `assets/lanes.proposer.example.json`, `tests/test_prompt_templates.py`.
- *Positive:* `python3 skills/dev-loop/scripts/adapters.py validate skills/dev-loop/assets/lanes.proposer.example.json`
  exits 0. Red today: the file does not exist.
- *Negative:* a temp copy whose `depends_on` names `ghost` must fail with the existing text,
  verbatim: `lane apply: depends_on unknown lane ghost` (`adapters.py:167`).
- *Size* S · *Lane* sonnet medium · *Deps* none.

**29. Make `adapters.is_owned` segment-aware for globs** (P4g, promoted from do-later)
- *What/why:* the premise is narrower than the design pass said. For plain directories,
  `adapters.is_owned` is already segment-aware (`adapters.py:703-709`; `src` does not own
  `srcfoo/x`). **Globs are not**, because fnmatch's `*` crosses `/`: `src/*.txt` owns
  `src/a/b/evil.txt`. `claude_lane.is_owned_path` (:325-338) matches segment by segment, and
  `cmd_gate` unions the two results (:1089). Delegate `is_owned` to one shared function.
- *Files:* `adapters.py`, `claude_lane.py` (the function moves to a shared module),
  `tests/test_lane_isolation_leakage.py`.
- *Positive:* `owned=["src/*.txt"]`, where the lane changed only `src/a.txt`, passes
  `adapters.py owned`. It already passes, so the negative is the red-before test.
- *Negative (red today):* the lane changed `src/a/b/evil.txt`. It must exit 1 with the existing
  text `OWNERSHIP VIOLATION: src/a/b/evil.txt`.
- *Size* S · *Lane* opus xhigh · *Deps* 12 (shared module).

#### Group G: quota (do-later: blocked on a real capture)

**30. Detect and surface a Claude usage limit** (P1b + P1c + P1d + P1e, one row)
- *What/why:* agy already has this (P1f is **already-exists**, verified). `agy_session.py` has the
  `Resets in` parser (:415-424), `quota_in_result` (:427-434), `fatal_result` with
  `wait_max_s=300` (:437-455), a short-reset wait (:779-784), and rc 75 on a long reset
  (:865-868). `agy_host.sh` passes it via `AGY_HOST_QUOTA_WAIT_MAX_S` (:193, :282). Its own
  docstring marks the wait path **UNTESTED** (:444-446). For Claude lanes, nothing exists
  (`claude_lane.py`/`adapters.py` grep: none). **Exit code:** claude_lane already uses 75 for
  `EX_BUSY` (:194), so a quota exit there uses **69**, and agy_session keeps 75. The collision
  across the two tools is documented, not changed. Then, in order:
  1. `normalize_report` sets `_meta.quota {reset_at}` and status `budget`. P1g, a `paused` status,
     stays rejected: the enum's 6 values (`adapters.py:69`, `openai-tools.json:291-298`) stay as
     they are.
  2. `lane_status`/`wait`/`list` expose `quota_reset_at`, and `wait` exits 69.
  3. The postmortem gains a QUOTA row.
  4. Dispatch refuses while a sibling's `reset_at` is in the future.
  5. `--resume` pause, bounded by `--quota-wait-max-s`.
- *Files:* `adapters.py`, `claude_lane.py`, `references/postmortem.md`, `nested-claude-lanes.md`, tests.
- *Positive:* **UNTESTED until item 2 holds a real usage-limit capture.** Then `normalize_report`
  over that capture yields `status: budget` and `_meta.quota.reset_at`. Red today: no detection.
- *Negative:* the test's planted revert of the detector, run over the same capture, must fail with
  `QUOTA MISSED: <fixture> carries a usage-limit envelope but _meta.quota is absent`.
- *Size* L *(4 lanes, steps 1-4 as listed; step 5 do-later)* · *Lane* opus xhigh · *Deps* 1, 2.

#### Group H: monitor-owned records and cross-repo rows

**31. Backlog rows and the 429 forensic record** (P6a, P6b; *monitor-owned*)
- *What/why:* `.devloop/` is monitor-only. `tasks.jsonl` uses only the `T-` and `AGY-` id prefixes
  (0 `DL-` ids), so the monitor adds rows with `artifacts.py tasks add`, using whatever id prefix
  the tool assigns, one per item the operator keeps. `.devloop/findings/RUN-429-FORENSIC.md` is
  written with `VERDICT: UNVERIFIED`. Cross-repo rows filed in MiOS:
  1. miosd `BarePortLiteralsCheck` is a Skip stub (`ports.rs:28`).
  2. The Python check covers 6 ports in 3 directories.
  3. MiOS `usr/share/mios/ai/system.md` has no `blocked` definition (item 9).
- *Files:* `.devloop/tasks.jsonl`, `.devloop/TASKS.md`, `.devloop/findings/RUN-429-FORENSIC.md` (monitor); MiOS backlog (cross-repo).
- *Positive:* `python3 skills/dev-loop/scripts/artifacts.py tasks validate` exits 0 after the adds.
- *Negative:* a temp copy of `tasks.jsonl` with one row missing `acceptance` must fail
  `tasks validate`, with the tool's existing message for that field, quoted verbatim by the monitor
  when it writes the row.
- *Size* S · *Lane* monitor · *Deps* operator's selection.

### Proposal disposition (every design-pass proposal)

| Proposal | Design score | Revised | Where / why |
|---|---|---|---|
| P1 as phrased | reject | reject | agreed; replaced by 2 + 30 |
| P1a | do | **item 2** | generalised to a corpus |
| P1b-P1e | do-later | **item 30** | blocked on a real capture |
| P1f | already-exists | already-exists (verified) | agy_session.py:415-455,779-784,865-868; wait path UNTESTED (:444-446) |
| P1g | reject | reject | status enum unchanged (adapters.py:69) |
| P2 | do | split into 17-21 | R4 |
| P2a | do | **item 17** | + SOURCE_TEXT_ASSERT (the real incident's shape) |
| P2b | do | **item 18** | |
| P2c | do | **item 19** | |
| P2d | do | **item 20** | waivers read from the base commit |
| P2e | do-later | do-later | |
| P2f | do | **item 21** | + `--diff` decision (do-later) |
| P2g | do | **item 15** | premise verified |
| P2h | reject | reject | agreed: positive-control shape is judgment; 17 covers the test body |
| P2i | already-exists | **item 16** | half-exists; `|| true` gap |
| P2j | already-exists | **corrected** -> 18 + 31 | MiOS Rust check is a Skip stub; Python check covers 6 ports in 3 dirs |
| P3 | reject | reject | agreed: rebasing a live lane rewrites a branch the lane owns |
| P3a | do | **item 22** | never touches ROOT; dirty stays a note |
| P3b | do | **item 23** | + git version probe |
| P3c | do | **item 24** | + stale reused branch |
| P3d | do-later | do-later | |
| P3e | already-exists | already-exists | devloop.sh merge_lane :282-283 abort-and-keep; base-audit :268 |
| P3f | do | **item 3** | 12 stale citations, not 1 |
| P4 | reject | reject | agreed |
| P4a | do | **item 14** | one knob; deps on 1 |
| P4b | do | **items 5 + 27** | retirement split out; real-repo control |
| P4c, P4d | do-later | do-later | after 27 |
| P4e | do-later | do-later | needs a measurement; 13 covers the claude_lane side |
| P4f | do-later | **item 28** | |
| P4g | do-later | **item 29** | glob case is a real hole |
| P5a | do | **item 10** | |
| P5b | do | **item 11** | premise corrected; scratch carve-out |
| P5c | do | **item 6** | sentence corrected; 5 surfaces |
| P5d | do | **item 7** | |
| P5e | do | **item 9** | rebase on 666e35c |
| P5f | reject | reject | agreed |
| P5g | do-later | folded into 27 | |
| P5h | do | **item 4** | name resolution repo-wide |
| P5i | do-later | **already-exists** | `register-hooks.sh --project` exists (:4, :33); running it is an operator choice |
| P6a, P6b | do | **item 31** | monitor-owned |

### Critic resolution

| Critic item | Resolution |
|---|---|
| W: P2j already-exists | **Upheld.** Item 18 (evidence: MiOS `ports.rs:19-29` Skip; `drift-checks.py:1711` 6 ports / 3 dirs). |
| W: test_mios_init fetches into the sibling | **Upheld.** Premise dropped (`test_mios_init.py:365-384`); item 11 re-motivated. |
| W: manager must write invariants.json first | **Upheld.** The lane's lines are flagged; waivers come from the base commit; default `[]` (Group D preamble). |
| W: NEVER WRITE TO ANOTHER CHECKOUT vs mktemp | **Upheld.** Sentence rewritten with a scratch carve-out (item 6), and the same carve-out in item 11. |
| W: P3a dirty tree refused | **Upheld.** It stays a note (`claude_lane.py:832-846`), and ROOT is never touched (item 22). |
| W: sonnet medium for a heavy lane | **Upheld.** Split: text-only item 6 is sonnet; schema/code item 7 is opus xhigh. |
| W: stale AGENTS.md citations | **Upheld.** Re-derived: `AGENTS.md:178`, paragraph :173-179 (item 4). |
| W: stale-refs scan flags tests/*.py | **Upheld.** Names resolve repo-wide via `git ls-files`; only `wait_done.py` is flagged (item 4). |
| W: contracts.py controls don't exercise the repo | **Upheld.** The new test scans the real tree (item 5). |
| W: lane 4 must fail closed if lane 2 unmerged | **Upheld.** Nothing enforces it today; item 13 adds `--requires`; R5. |
| W: positives pass on the unchanged tree | **Upheld.** R1. Where a positive already passes (16, 29), the negative is the red-before test and is labelled as such. |
| M: exclusive owned_paths across live lanes | Item 12. |
| M: six shims cite contracts.py | Seven (cursor too); item 5. |
| M: base_leak substring | Item 26. |
| M: gate_audit --diff | Decided do-later (item 21). |
| M: reused lane/<id> branch behind-count | Item 24. |
| M: isolation:worktree base | Item 25. |
| M: git >= 2.38 | Measured 2.43.0 / 2.55.0; probe added (item 23). |
| M: review.py keyword grep | Item 27 (fallback kept, labelled heuristic). |
| M: contract_updates has no consumer | Item 8. |
| M: proposer shape that works today | Item 28. |
| M: LEDGER claims unpushed | **Verified** (`LEDGER.md:47-48`; no `live_managers.py` in any ref); item 1 gates 14 and 30. |
| M: OQs not surfaced | Q-C below. |
| M: negative print style undictated | Every negative above dictates its exact text (R2). |
| M: parity covers 2 of 4 surfaces | There are 5 surfaces; all are covered (item 6). |
| M: one knob, three names | Item 14: one definition and a stated precedence. |
| M: multi-deliverable single negative | R4; items 27 and 30 are multi-lane. |
| M: pull-latest target for SHA/detached; manager ff | Item 22 records `n/a`; the manager never fast-forwards ROOT (PRs merge in this repo). |
| M: no scratch carve-out | Items 6 and 11. |

### Confirmation

This ADR adds no code. Compliance is checked per item by the controls it lists. The file itself is
gated by `sh skills/dev-loop/scripts/validate.sh`.

### Consequences

- Good: every kept item has a red-before positive and a dictated negative. Wrong premises are gone,
  and each untestable scenario is labelled rather than claimed.
- Bad: items 8, 10 (positive), 25 and 30 wait on real captures (item 2) that cannot be produced
  on demand. Items 12, 14 and 15 add a `--check-only` flag that exists mainly for tests.

## Open questions for the operator

- **Q-A (scope):** which items to keep. Grouped below for the question UI.
- **Q-B (freshness default):** `--fresh` default off (recommended), or on when the base has an upstream?
- **Q-C (policy):**
  1. Should admission control (item 14) also count live AGY managers under the 4/2 fleet caps?
  2. Does the item-6 lane sentence bind the monitor session too?
  3. Is the Workflow tool available to AGY and other cloud sessions, so that item 28 documents it
     as a host?

## More Information

- Baselines: -dev-loop `origin/main` 96e6578; `origin/claude/dev-loop-iv4399` 666e35c; MiOS 96d7de8.
- git measured 2026-09-26: cloud VM host 2.43.0; `mios-dev:base` 2.55.0 (`git-core-2.55.0-1.fc44`).
- AGENTS.md rules applied: test doubles (operator 2026-09-25), model policy, PRs ready for review,
  and workers never editing `AGENTS.md`/`.devloop/`.
