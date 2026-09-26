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

## 2026-09-25 07:29 · f909dfe · cloud session: MiOS devcontainer projection
- objective: make a cloud session a Fedora container projected from MiOS's devcontainer, with a reusable setup script
- done: cloud-fedora-setup.sh FEDORA_DEVCONTAINER_REPO mode: shallow clone, unedited build of .devcontainer/Containerfile on a locally shadowed CA-trusting repo-pinned fedora:44 (FROM resolved to the shadow digest), inherited CA env incl. PIP_CERT, wrapper baked + installed as mios-dev and fedora, per-entry /home mounts (whole /home hid agy), concurrent cold-start race fixed. Measured 3m32s first run, 0.36s re-run, 1.45s cold, 3m14s first-use build from baked values. adapters.validate_spec fallback now enforces the schema's numeric worker bounds (host lacks jsonschema; test_claude_lane timeout check was red on HEAD). validate.sh rc 0
- next: operator: paste the script + the two FEDORA_DEVCONTAINER_* vars into a cloud environment and make it the default; decide whether validate.sh should also pass inside mios-dev (4 suites error there)
- blockers: -
- unverified: the platform snapshot of a pasted setup-script run was not observed from a fresh session; 3m32s leaves ~1.5 min of the ~5 min budget; node reached github.com with NODE_EXTRA_CA_CERTS unset, so that var is belt-and-braces there

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

## 2026-09-25 13:39 · 06445b1 · PR #17 review before ready
- objective: review PR #17 before marking it ready (operator: refine with AGY if needed)
- done: agy unauthenticated after the container restart -> reviewed as Claude Code (topology B fallback); no correctness findings in the script or adapters diff. Root-caused the 4 suites that error inside mios-dev: git commit exits 128 because the host signs commits via gpg.ssh.program=/tmp/code-sign (-> /opt/env-runner), which is not mounted; documented 'commit from the host'. Mounting the helper was denied by the permission classifier and not pursued. validate.sh rc 0
- next: operator: finish agy login (agy-login.sh --code) if an AGY review pass is still wanted; review and merge #17
- blockers: -
- unverified: no AGY review ran (no auth); signing inside the container untested (helper mount not permitted)

## 2026-09-25 14:54 · dc34601 · cloud session: dev-loop plugin commands
- objective: make /dev-loop:* commands available in cloud sessions of the MiOS Fedora environment
- done: cloud sessions load no marketplace, enabledPlugins or project skills-dir plugin (trust dialog never shown); CLAUDE_CODE_PLUGIN_DIRS=/opt/dev-loop + setup-script clone loads dev-loop@inline: 15 /dev-loop:* commands, 5 agents, plugin MCP connected (measured from init events, both sides, from an unrelated repo). Documented in environment.md with the setup snippet. validate.sh rc 0
- next: operator: add CLAUDE_CODE_PLUGIN_DIRS=/opt/dev-loop and the new setup script to the environment, then open a new session and type /dev-loop
- blockers: -
- unverified: not yet observed in a freshly started cloud session (verified with claude -p in this container); /opt/dev-loop refreshes only when the environment cache is rebuilt

## 2026-09-25 15:15 · 1d4d179 · partial
- objective: provision AGY in this cloud container (operator pick, topology A prerequisite)
- done: setup-antigravity.sh failed rc 126 'cannot execute binary file' twice: antigravity.google's CDN sends Content-Encoding: gzip unsolicited from one cache node (~1 in 3 responses; 2/6 measured) and plain curl -fsSL writes the gzip bytes. New scripts/env/fetch-installer.sh (curl --compressed + #! check) used by setup-antigravity.sh; .devcontainer/Dockerfile gets the same flag and check inline. tests/test_agy_installer_fetch.py: local always-gzip server; positive decodes byte-exact and runs; negatives (--compressed stripped, HTML body) fail naming 'not a shell script'; two mutants turn it red. Real CDN 6/6 identical via helper. agy 1.2.11 installed, keyring + grants + skill PASS. validate.sh rc 0
- next: operator: sign in at the agy-login URL and run agy-login.sh --code '<code>'; then agy-doctor.sh --probe; then pick the run objective
- blockers: agy authentication (operator)
- unverified: Dockerfile change not built (no image build here); install.sh's own tarball fetch is sha512-checked so it fails loudly, not silently, if gzip-encoded

## 2026-09-25 16:18 · 8c552ef · done
- objective: every MiOS dev environment builds MiOS's one SSOT image; the cloud env comes fully provisioned (operator, 2026-09-25)
- done: MiOS Containerfile resolves its dnf set from mios.toml [packages.devcontainer] (69/69 equal to the old list) and bakes agy fail-closed; bootstrap + -dev-loop devcontainers build it from a sibling checkout via initializeCommand and run MiOS's lifecycle; their copies and the Ubuntu variant are deleted. cloud-fedora-setup.sh: provisions the host (agy/keyring/grants/skill), builds with the Dev Containers CLI (features), commits the devcontainer.json lifecycle (miosd, overlay, /opt/mios/bin), status file + wrapper warning, FEDORA_SETUP_BUDGET_S defer + --lifecycle (both sides tested). Plugin SessionStart revives the keyring into CLAUDE_ENV_FILE in any repo; format.sh parses by shebang. Identity: cloud image vs mios-bootstrap devcontainer build, 574-line census identical; the plain build differed by 16 RPMs. validate.sh rc 0; MiOS manpages + manual ledger regenerated and green
- next: operator: review and merge the three PRs (MiOS first, since bootstrap/-dev-loop build its Containerfile); rebuild the cloud environment's cache and watch whether a 452s setup still snapshots, and set FEDORA_SETUP_BUDGET_S if it does not
- blockers: -
- unverified: platform behaviour of a setup script over ~5 min; Codespaces honouring initializeCommand + out-of-repo build context; Windows cmd.exe initializeCommand; Cloud Shell path; MiOS gate tier is red on main for pre-existing checks (legibility ratchet already over: +1 file/+27 shell lines added, not raised)

## 2026-09-25 17:33 · c41efb2 · partial
- objective: /dev-loop:init + podman-first cloud projection, review-fixed; ports SSOT fix in MiOS/bootstrap; Codespaces web-safe settings; -dev-loop self-improvement research (operator, 2026-09-25)
- done: -dev-loop: init skill (skills/init, mios-init.sh, 32 tests), FEDORA_RUNTIME auto/podman/docker with image-home + usability rule (27 tests), hook no longer clobbers the projection wrapper, plugin SessionStart revives the keyring, format.sh parses by shebang; adversarial review round applied (F1-F12, R1-R4); validate.sh rc 0; pushed c41efb2, draft PR opened. MiOS/bootstrap: whisper/piper ports registered in the SSOT (97-ssot-lint 0 orphans, lint tier 6/6, verifier not refuted), PRs #36/#9 ready. Workflows used for every substantive step (lanes with exclusive owned_paths + adversarial reviewers)
- next: re-review verdict -> mark the -dev-loop PR ready; Codespaces lane (worktrees /root/.cache/wt on lane/dotfiles-web: desktop-only VS Code keys out of the API-applied surfaces) -> merge, push, PRs; research SPIKE -> backlog the accepted items and run implementation lanes; operator: agy-login.sh --code with a fresh code
- blockers: agy authentication (operator code expired; fresh URL issued)
- unverified: re-review of the fix commits; projection under podman end to end; a bare Fedora install path; the ~5 min cache budget overrun behaviour

## 2026-09-25 18:05 · e96e695 · pre-compact
- objective: context compaction
- done: see git log -5
- next: re-read AGENTS.md, TASKS.md, this ledger; continue the in_progress task
- blockers: -
- unverified: anything not yet committed: 7 dirty path(s)

## 2026-09-25 23:00 · e96e695 · partial
- objective: Codespaces web-safe settings, /dev-loop:init round-2, Fedora devcontainer restore, images design
- done: Codespaces verifier read: surfaces clean but lane refuted (mode-dropping _write_atomic, over-cap hints, untracked census); all four workflows died on the 22:40Z subagent quota; relaunched at 22:47Z: codespaces-fixup wf_e666a6f3-422 (wt /root/.cache/wt lane/dotfiles-web), init/runtime round-2 resume wf_14e9b24b-848 (partial edits in this tree; tests pass 50+35), restore resume wf_d46f9bf9-422 (wt2 lane/fedora-devcontainers); MiOS branch fast-forwarded to origin/main a7de8f4 (operator dash/ux commit touching mios.toml, mios.code-workspace, setup-devcontainer.sh, manual-corpus.tsv: expect merge work on both lane branches)
- next: on each workflow result: gate, merge lane branch into claude/dev-loop-iv4399, regenerate (sync-generated.sh), commit explicit paths, push, PR, subscribe; then resume images design wf_cee03fe3-78d and research critic wf_94707d27-6df (verdict revise; synthesize:revised never ran); check-in trig_01BTo49SoVmngTzBLRWKCAVQ 00:15Z
- blockers: agy authentication (operator code expired; fresh code needed); subagent quota window
- unverified: the 8 dirty -dev-loop paths are the round-2 lane's in-flight edits (not gated yet); PR #21 head e96e695 has no CI check runs on this repo

## 2026-09-26 04:14 · e96e695 · partial
- objective: Edge-to-edge terminals globally
- done: global inventory (21 surfaces) + design SPIKE-edge-to-edge-global.md (critic: revise); operator decisions: code-server in dev image with patched workbench, ModernUI on, density compact, bake-time bundle patch for the 10px scrollbar reserve (fail if anchor moves), Ptyxis via GTK CSS only, fastfetch logo inset 0; Fedora devcontainer restore merged (MiOS#38, mios-bootstrap#10)
- next: fix the critic's items in the design, then run edge lanes after lane/dotfiles-web merges; integrate round-2 init + -dev-loop restore part onto PR #21
- blockers: codespaces-fixup wf_e666a6f3-422 and round-2 wf_14e9b24b-848 running
- unverified: Ptyxis flatpak dconf/gtk path; code-server bundle patch anchor; github.dev stays unreachable by design

## 2026-09-26 11:48 · ee959c4 · blocked
- objective: Edge-to-edge terminals globally; MiOS CI stall
- done: edge waves 1+2 on MiOS#40 (0ca442e) and mios-bootstrap#12 (384ca11): SSOT inset, renderer Law 13, WT/code-server/GTK/fastfetch/Hyprland/Sway/Alacritty/WSL/tmux/Portal/ttyd rendered+gated, code-server baked with two fail-loud bundle patches, mios-edge-status; three adversarial reviews; -dev-loop#23 mirrors the Containerfile and the projected endpoint/ports. CI stall root-caused: tests/test-socket-swap.sh leaks a mock worker holding the captured stdout pipe; 9-line fix validated both ways, posted on MiOS#40
- next: operator decisions below; then push the socket-swap fix, watch CI finish, drive #40/#12/#23 to merged; backlog: test_job_receipt.py flake (race in job.kill/status), test-socket-swap asserts retired port 8642
- blockers: operator: push test-socket-swap fix (#40 or own PR); accept ratchet growth (+272 python lines, +11 files); merge order #12 -> #40 -> #23
- unverified: live code-server/Hyprland/Ptyxis/WT sessions; WSL profileTemplate on wsl --import; patched suite on the hosted runner

## 2026-09-26 · 9b2a83f · job-wrapper-term
- objective: root-cause the test_job_receipt.py flake (1 in 4 on main)
- done: the wrapper's TERM trap wrote a receipt and fell through into the job when the signal landed before `timeout` started; traps now exit. A regression test widens the window on a wrapper copy; the negative control (trap without exit) fails it by name. validate.sh passes; 18 repeat runs green.
- next: MiOS CI green (ci-green workflow in flight); -dev-loop self-improvement SPIKE; images core profile
- blockers: agy auth needs a fresh code from the operator
- unverified: the flake's original trigger timing on a loaded box (reproduced deterministically, not statistically)

## 2026-09-26 · c918084 · native-ask
- objective: operator (2026-09-26): questions come through the app's native question UI, never chat prose; part of dev-loop's native mechanisms
- done: SKILL §5 rule + harness matrix row + AGENTS.md working rule; Stop hook sends back a reply that asks in prose without AskUserQuestion (hooks/_chat_question.py; lanes exempt; DEVLOOP_NATIVE_ASK=0 opt-out; DEVLOOP_ASK_CAP=2). Controls replay two real captured turns (tests/fixtures/transcripts/); disabled detector fails 2 tests by name. validate.sh passes.
- next: install the plugin copy so running sessions pick up the hook; MiOS CI green (ci-green lane); worker-session prompt launch pending the operator
- blockers: -
- unverified: agy/Gemini/Codex native question surfaces (matrix says not yet probed); detector is a heuristic ("?" ending a prose sentence) and can false-positive on a rhetorical question in a report

## 2026-09-26 · 196894c · re-ask + agy 1.2.11
- objective: operator: re-ask open questions every turn via the native UI; links clickable; sign agy in
- done: Stop hook sends back a report blocked on the operator from a turn that never asked (real fixture open-blocker.jsonl); links go in a file card (SendUserFile) before the question. agy signed in (headless auth verified; quota spent, resets ~13:58Z). agy 1.2.11 refuses artifactReviewPolicy "turbo" (new spellings always-proceed/request-review/agent-decides): agy_settings.py reads the set from the installed binary, warns on stale values, gains clear-review-policy; SessionStart no longer defaults turbo; operator chose to remove the key. agy-doctor names a spent quota. Negative controls: re-ask detector off fails 1 test by name; legacy-only spellings fail 4 checks by name. validate.sh passes.
- next: worker 2 for Task #8 (SPIKE revision); operator's policy choice for unattended teamwork; MiOS CI green lane
- blockers: -
- unverified: doctor quota branch has no test (live-observed both ways: before = "did nothing", after = quota named); agy-login.sh on 1.2.11 when truly signed out

## 2026-09-26 · c918084+ · monitor-relay kickoff
- objective: operator: monitor+relay inside every MiOS image (cloud sessions, Codespaces, Cloud Shell), relaying subagents over OpenAI/upstream patterns; ADR 0003 dispositions from upstream research (kept 1,3,4; dropped 2)
- done: AGENTS.md dangling wait_done.py -> scripts/job.py wait (ADR 0003 item 4 contract update); research+design workflow wf_a82fc37e-22b launched
- next: operator questions from the relay SPIKE and dispositions; implementation lanes
- blockers: -
- unverified: everything in the relay design (not yet written)
