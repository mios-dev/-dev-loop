# Dev Loop ledger (handoff notes; newest last)

## 2026-09-19 02:21 · the design-audit merge (SHA squashed away; see .devloop/findings/DESIGN-AUDIT.md) · done
- objective: Run acp-p6 and design-audit lanes to research ACP transport and audit design
- done: acp-p6 evaluated agy-acp transport and design-audit audited loop translation layer design against vacuous-check taxonomy. Both lanes gated and merged.
- next: -
- blockers: -
- unverified: -

## 2026-09-19 04:24 · 58d61dc · pre-compact
- objective: context compaction
- done: see git log -5
- next: re-read AGENTS.md, TASKS.md, this ledger; continue the in_progress task
- blockers: -
- unverified: anything not yet committed: 0 dirty path(s)

## 2026-09-19 04:45 · 5f475f6 · 5f475f6
- objective: wire job.py through the orchestrator and close its self-certification hole
- done: devloop.sh wave dispatch + reap; agy_host --jobs-root; job.py liveness>receipt; 5 new control suites
- next: run one real agent lane through the job dispatch; decide whether to reopen a PR for the 16 unmerged commits
- blockers: -
- unverified: -

## 2026-09-24 22:16 · 71866e6 · monitor session (AGY manages MiOS)
- objective: keep an unattended AGY /teamwork-preview manager running on MiOS; relay monitor findings
- done: system prompt template + `prompt.py emit` (5e179b5..bfc1df5); agy_session auto-continue/done-cmd; teamwork draft-approval fix (ca38d3d); placeholder-aware .agents guard (4c236ee); agy_settings.py validated writer, turbo review policy (f3dc6c4); --relay-file change notice (71866e6). validate.sh rc 0 each time
- next: launch the next AGY manager with AGY_HOST_RELAY_FILE=<run>/.devloop/native/monitor-relay.md; exercise the held-session poll loop past a turn end (still unproven)
- blockers: -
- unverified: --relay-file has never run against real agy (only the fake); the live manager was started before it existed

## 2026-09-25 01:45 · d261371+1 · monitor session: test_claude_lane.py flake
- objective: make tests/test_claude_lane.py pass reliably under load (validate.sh went red intermittently)
- done: the real flake was a test race, not timing -- hooklane planted a hook in the git dir both
  lanes share while escape ran, so escape's gate stopped at git_meta_changed before computing
  base_moved (failed 2 of 3 full runs); the two lanes now run one after the other. Timing checks
  now read each lane's own [start, end] span from the fake: dispatch returns before its lane
  ends, the lanes' spans overlap, wait returns after both end
- controls: mutants red for the named reason (dispatch that blocks 9s: +2.82s after the lane
  ended; flock-serialised lanes: alpha end == beta start); 4 full runs, 2 at a time, 245/245
  each; validate.sh rc 0
- next: role-symmetry build on the robust gate; F16 once Gemini quota is back
- blockers: -
- unverified: no mutant for the wait-blocked span check (the rc/state checks also catch an early wait)

## 2026-09-25 02:50 · c6266e7 · monitor session: operator decisions, caps, PRs
- objective: act on the operator's 24 answers (decisions file: ~/.devloop-runtime/operator-decisions-2026-09-25.md)
- done: 4-manager cap (live_managers.py, launcher refuses a 5th; both sides); quota probe/wait
  require the assigned tier (stub controls 6/6); -dev-loop main squashed to 46b325c (tree
  identical) and #14 replaced by #15 (GitHub closed #14 on the base rewrite); AGENTS.md records
  the decisions; MiOS#32 (generated ARTIFACT-PROMPT.md + run 4 ToC + T-1104..T-1111, drift
  236 -> 217 vs a same-binaries baseline) and mios-bootstrap#7; 4-hourly routine armed
- next: replay-only revision of the role-symmetry build (wf_e487f7e3-399), then its AGY build;
  rewrite the existing tests to replay real transcripts (task #8); run 3 relaunch is queued
- blockers: -
- unverified: F16 (a real AGY agent driving claude_lane.py) -- a live-harness run, on demand only

## 2026-09-25 07:49 · 48e0f49+1 · dev-loop-web: the Spark skill, its package target and gate
- objective: a web-only dev-loop skill the operator uploads to Gemini Spark for the MiOS daily out-of-loop
  artifact task (design: research note devloop_spark_skill_design.md Q4), packaged and gated here
- done: skills/dev-loop-web/ (SKILL.md 258-line body, portable keys only, no project values; references
  verification.md, fetch-paths.md, reply-skeleton.md; six offline stdlib scripts, each --self-test and
  --two-sided); skill_package.py pack/check; install.sh + install.ps1 `--harness gemini-spark` ->
  dist/dev-loop-web.zip (37620 bytes, sha256 12ff547c..., reproducible); validate.sh 1b gates the EMITTED
  zip (section 1 strips Claude-only keys from sub-skills first, so alone it passes `context: fork`)
- controls: tests/test_dev_loop_web_package.py -- 17 plants into a copy of the emitted zip, each grepped
  back out and failing by name; 1024 chars / 499 lines pass; 12 gate mutants all turn the suite red; real
  validate.sh with `context: fork` planted into the real SKILL.md rc 1 naming it, restored (sha256 equal);
  scripts on real MiOS main data (contract blob 4017c85d proven, exemplar datasets, the contract's strict
  schema, a two-build OCI layout byte-identical); validate.sh rc 0
- next: operator uploads dist/dev-loop-web.zip; first live Spark run records preflight A-D and the fetch
  path table; MiOS-side template rewording + optional [artifacts.daily] task_skill (proposed, not made)
- blockers: -
- unverified: everything on a live Spark (bundled scripts run? bytes reach the runner unchanged? which
  GitHub URL forms are readable? binary attachment?); install.ps1 target never executed (no pwsh here);
  the agentskills.io reference validator (skills-ref) is not installed -- structural checks only

## 2026-09-25 08:10 · fedbd2c+1 · codex lanes: approval policy as a config override
- objective: every codex lane died at argument parsing -- `codex exec` (codex-cli 0.155.1) rejects
  `--ask-for-approval` ("unexpected argument", rc 2); it is a top-level `codex` flag. Found by the
  upstream-APIs report (defect D1); `adapters.py probe --harness codex` already reported the drift (rc 1)
- done: build_argv passes `-c approval_policy=<permission_mode, default never>`; PROBE_FLAGS for codex
  now names the exec flags actually used (--config, --ephemeral); harness-adapters.md row and the
  lane-schema permission_mode description updated
- controls: tests/test_codex_argv.py against the REAL binary (`--help` in the prompt's place, so no model
  call): the adapter argv parses rc 0; the old flag spliced back in fails and names it. Mutant (old flag
  restored in adapters.py) turns 4 tests red. Config layer, both sides: `-c approval_policy=bogus` ->
  "unknown variant `bogus` ... in `approval_policy`"; `never` loads and starts a thread. probe rc 0
- next: -
- blockers: -
- unverified: a real codex turn with this argv (no codex auth here; live-harness runs are on demand only)
