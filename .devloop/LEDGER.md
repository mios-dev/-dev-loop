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

## 2026-09-25 07:29 · f909dfe · cloud session: MiOS devcontainer projection
- objective: make a cloud session a Fedora container projected from MiOS's devcontainer, with a reusable setup script
- done: cloud-fedora-setup.sh FEDORA_DEVCONTAINER_REPO mode: shallow clone, unedited build of .devcontainer/Containerfile on a locally shadowed CA-trusting repo-pinned fedora:44 (FROM resolved to the shadow digest), inherited CA env incl. PIP_CERT, wrapper baked + installed as mios-dev and fedora, per-entry /home mounts (whole /home hid agy), concurrent cold-start race fixed. Measured 3m32s first run, 0.36s re-run, 1.45s cold, 3m14s first-use build from baked values. adapters.validate_spec fallback now enforces the schema's numeric worker bounds (host lacks jsonschema; test_claude_lane timeout check was red on HEAD). validate.sh rc 0
- next: operator: paste the script + the two FEDORA_DEVCONTAINER_* vars into a cloud environment and make it the default; decide whether validate.sh should also pass inside mios-dev (4 suites error there)
- blockers: -
- unverified: the platform snapshot of a pasted setup-script run was not observed from a fresh session; 3m32s leaves ~1.5 min of the ~5 min budget; node reached github.com with NODE_EXTRA_CA_CERTS unset, so that var is belt-and-braces there
