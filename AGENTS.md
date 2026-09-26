# AGENTS.md — constitution for this repository

Canonical contract file. `CLAUDE.md`, `GEMINI.md`, and `.agent/rules/00-agents.md` are pointers
to this file; loaders differ, so those files must stay pointers. Per the dev-loop skill
(`skills/dev-loop/SKILL.md` §0), this file is law: where it and the skill disagree, this file wins.

## What this repository is

The `dev-loop` plugin/skill set (see `README.md`), plus an environment layer (`skills/dev-loop/scripts/env/`, devcontainers in `.devcontainer/`)
that provisions Google Antigravity's CLI (`agy`) inside Claude Code on the web containers.

## Orchestration topology (binding)

- **L0 host / manager: Antigravity (`agy`), native-first.** All multi-lane dev-loop runs
  launched from this repository default to topology A of
  `skills/dev-loop/references/harness-adapters.md` §3 — AGY is the manager of all sub-agents and
  uses its NATIVE multi-agent machinery (subagents via `invoke_subagent` with
  `workspace: branch`, native workflows) for its own lanes by default. The dev-loop's reference
  orchestrator is how OTHER harnesses join the loop, not a replacement for AGY's native
  patterns. Launch with `sh skills/dev-loop/scripts/agy_host.sh <lanes.json>`.
  **Native lanes require a manager whose process outlives a turn.** `--session` holds a
  stream-json NDJSON session open across turns and is the unattended mode that keeps the
  native topology above; `--headless` is single-turn `agy -p` and routes every lane through
  the reference orchestrator instead, because a subagent that has not finished when the turn
  ends dies with the process. This is a lifetime constraint, not an availability one --
  `invoke_subagent` itself works headlessly (measured 1.2.6, four probes, including one with
  `settings.json` voided). Controls: `tests/test_agy_dispatch_rule.py`. The first `--session`
  run dispatched, gated and merged two native lanes in ONE turn, so the poll loop that keeps a
  session alive past a turn end is implemented but **not yet exercised** -- do not cite it as
  proven.
- **Remote control is a per-SESSION flag, not a daemon property.** `agy --remote-control`
  ("Create a remote connection for the CLI session on start up") is what puts a running
  manager in the Remote Control list at antigravity.google.com. The
  `agy remote-control serve` DAEMON is a different object: it registers the MACHINE (an
  instance name), not the sessions on it, so a healthy authenticated daemon is NOT evidence
  that any session can be seen or driven -- reading it as such is how a run gets reported
  live while being invisible. Measured 2026-09-20 on agy 1.2.6, two probes differing only in
  the flag: with it, `server.go:3565 "Remote control enabled, starting connection"` and
  `remote_control_v2.go:2037 "Connection status: Connected"`; without it,
  `server.go:3768 "[RemoteControl] Session toggle is off, staying disconnected"`. The
  connection lives exactly as long as the process (`server.go:3650 "Deleted session
  instance <id>-v2"` fires on exit), so it belongs to `--session` and never to `--headless`:
  a single-turn `agy -p` run is gone before an operator can attach. Carried by
  `agy_host.sh --session --remote-control`, which also passes `--hold-file`/`--hold-max-s`
  so the session stays attachable after its local work ends and is stopped with
  `touch <run>/.devloop/native/STOP`. Controls: `tests/test_agy_remote_control.py`.
- **Unattended `/teamwork-preview` needs an auto-proceed `artifactReviewPolicy`.** The built-in's
  own protocol forbids invoking the team "before explicit user approval", and a brief that says "do
  not ask" is not approval. Measured: a manager told not to ask did the whole job solo (100
  responses, 1 subagent). The auto-proceed policy is the approval; `agy_session.py
  --auto-continue` answers the draft turn. agy VALIDATES the value, and an unrecognized one makes
  it load DEFAULTS for everything, dropping every permission grant. The spellings changed under the
  same key: 1.2.7 took `turbo`; 1.2.11 (measured 2026-09-26) refuses it and takes
  `always-proceed` / `request-review` / `agent-decides`. So `scripts/env/agy_settings.py` is the
  one settings writer, reads the accepted set from the INSTALLED binary, and refuses anything
  else; `clear-review-policy` removes the key. **Operator decision (2026-09-26): no default** --
  the SessionStart hook no longer sets `turbo`, and the key stays removed until the operator
  chooses a policy (`DEVLOOP_AGY_ARTIFACT_REVIEW`). Until then unattended teamwork runs are not
  pre-approved. Controls: `tests/test_agy_settings.py`.
- **The stray base-tree guard is scoped to lane runs.** `agy_session.py` fails closed (exit 6)
  on a manager editing the base tree outside a lane worktree. That question presupposes
  worktrees, so a LANE-LESS session (one manager doing the work itself -- an AGY teamwork run)
  has none and every edit it makes is "outside every worktree" by construction, including the
  edits that are the run. There the guard reports instead of killing: every base edit is still
  named on every turn, prefixed `UNGATED`. The cost is real and is not hidden -- a lane-less
  run carries no worktree gate and its changes must be reviewed before they are trusted.
  Controls: `tests/test_base_tree_guard.py::TestGuardScope` (both sides).
- **AGY teamwork runs may spawn nested Claude Code CLI subagents** through
  `scripts/claude_lane.py`, each one a full dev-loop lane: its own worktree and branch
  (`.devloop/worktrees/claude-<id>`, `devloop/claude-<id>`), exclusive `owned_paths`,
  `adapters.py run` spawned detached through `job.py` so it outlives the agent's
  `run_command` and turn, and the two-sided gate. A bare `claude -p` from run_command does
  not qualify: it is backgrounded after ~10s and dies with the turn. The tool never merges;
  the AGY manager gates each lane (`claude_lane.py gate --pin <pin from dispatch>`) and merges
  only lanes that reached `done` -- a timeout is never a pass. The gate is a detector, not an
  OS boundary (a lane runs as the same uid): it refuses a rewritten gate definition, commits,
  staging, index-flag-hidden edits, unowned or protected paths and changed git hooks/config.
  `agy_host.sh --teamwork` appends the canned `nested-claude-lanes` prompt when `claude` is on
  PATH (`AGY_HOST_CLAUDE_LANES=0|false|no|off` opts out). Controls: `tests/test_claude_lane.py`
  (both sides, fake `claude`). A real AGY manager drove it end to end **once** (2026-09-25,
  run android-edge-node): four dispatches, one lane killed and re-dispatched, `wait`, then
  `gate --pin` with each dispatch's pin, and exactly the three lanes that reached `done` merged.
  That proves the protocol, not the work. The manager picked `--model sonnet --effort low` for
  multi-file coding lanes and wrote string-presence positive controls (`assert "socket" in c`);
  all three gates passed, and the merged code failed the monitor's review against its task spec
  (JSON sent to the mDNS multicast group, udev rules matching by driver instead of the NCM IDs,
  thresholds as literals). A gate is only as strong as the controls its manager writes: review
  every merged lane before trusting it.
- **Lanes: any mix, multiple instances allowed.** Native Antigravity subagents and multiple
  concurrent Claude Code lanes (`claude -p`) run side by side; other harnesses stay available
  through the orchestrator. Harness-native loop commands (`/dev-loop` shims, Claude Code's
  `/loop`-style commands, AGY workflows) are allowed inside lanes — they map onto loop stages
  and never replace the gates. Every lane keeps the dev-loop lane contract: exclusive
  `owned_paths`, its own two-sided gate, no `git add/commit/push`, no edits to this file.
- **Model policy (operator, 2026-09-25, from a sourced stats study:
  `reports/Coding agent model and harness stats.md` in the monitor's workspace).** Every Gemini tier
  draws ONE shared pool (Ultra plan; >= 4,192 responses per five-hour slot measured, while one
  teamwork tree burns 31-47 a minute), so tier choice sets quality and per-task tokens, never
  availability. AGY manager: `gemini-3.1-pro-high`; coding workers `gemini-3.8-flash-high`;
  general and research-synthesis runs `-medium` (research fan-out <= 3); harvest `-low`, solo. No
  `claude-*` through AGY. `gpt-oss-120b-medium` only as solo-harvest overflow while the Gemini
  pool is dry. Nested Claude Code lanes (Max 5x plan): heavy coding `opus --effort xhigh`, one at
  a time; research and read-only lanes `sonnet --effort low|medium`. No API lanes (subscription
  only).
- **Fleet limits (operator, 2026-09-25):** at most **4** AGY managers live at once on one box, and
  at most **2** of them teamwork trees (the rest solo); a held session counts. Waves launch right
  after a pool refill. Launchers refuse a fifth and callers wait for a slot. A held session is
  stopped (its STOP file, never a kill) as soon as the monitor has reviewed and committed its work.
- **Legibility drain (operator, 2026-09-26):** a separate `drain:` PR runs automatically per repo
  after every 3-5 commits to main (MiOS thresholds: `[legibility].drain_after_commits` /
  `drain_max_commits` once they exist): it re-measures the legibility ratchets, proposes
  consolidations with proof (callers, gates both sides), asks the operator every judgement call
  through the native question UI, and opens a ready-for-review PR labelled `drain`. It never raises
  a floor, deletes a test to shrink a count, or merges. Feature PRs do not offset ratchet growth
  themselves; the drain does. Carried by the Routine "Legibility drain (per repo, every 3-5
  commits)".
- **Pull requests (operator, 2026-09-25):** verified work goes up as a PR ready for review; the
  operator reviews and merges from the GitHub app. The monitor never merges.
- **Test doubles (operator, 2026-09-25):** tests replay REAL captured agy/claude transcripts;
  hand-written fakes are being removed, and live-harness runs happen on demand only. Scenarios
  no real transcript contains (a lane that tampers with its gate, hangs, or forges a receipt) are
  dropped with the fakes, so the detection code they exercised becomes **untested** -- say so
  wherever it is described, never "proven".
- **Claude Code <-> AGY translation bridge (operator, 2026-09-25):** an MCP server written as a
  Rust static binary, source and OCI image in THIS repo (vendor names are allowed here; MiOS runs
  the image through a vendor-neutral, function-named Quadlet). Credentials reach it by
  bind-mounting the existing agy/claude keyring and config directories; it is reachable across
  the MiOS mesh VPN, authenticated per the MCP authorization spec.
- **The manager is the only writer to shared state** (`AGENTS.md`, `.devloop/`, merges). Lanes
  report `contract_updates`; the manager writes them here.
- **Fallback:** when `agy` is unavailable or unauthenticated, a Claude Code session may host the
  run (topology B) but must say so in its report; it does not silently become the standing manager.
- **Permissions for the headless manager (operator decision, 2026-09-18):** `--yolo`
  (`--dangerously-skip-permissions`) is authorized whenever the run is requested via a
  `/dev-loop`-style command. Scoped `permissions.allow` rules remain the default elsewhere; note
  that models habitually prefix dispatch commands with `cd … &&`, and prefix rules match only the
  first token, so a scoped allowlist needs `command(cd)` too.
- Reference example for a mixed AGY + Claude Code run:
  `skills/dev-loop/assets/lanes.agy-manager.example.json`.

## Environments (devcontainer default: Fedora; also Claude Code on the web)

Canonical scripts: `skills/dev-loop/scripts/env/` (docs: `references/environment.md`; there is
no other copy — no wrappers). Distro-aware: Fedora/RHEL dnf first, Debian/Ubuntu apt.
`.devcontainer/Containerfile` is a byte-identical mirror of **MiOS's one dev image** (gated by
`tests/test_devcontainer_mirror.py`; edit it in MiOS, never here). It is context-independent: built
from this repo's root it shallow-clones MiOS and resolves `[packages.devcontainer]` from the clone,
and `devcontainer.json` runs MiOS's lifecycle from `/workspaces/MiOS`. Operator decision
(2026-09-25): every MiOS dev environment -- the three repos' devcontainers, Codespaces, Cloud Shell,
the cloud-session projection -- builds those same bytes. The Ubuntu variant was removed.

- `bash skills/dev-loop/scripts/env/setup-antigravity.sh` — idempotent provisioning (also run
  by the SessionStart hook in `.claude/settings.json` and devcontainer `postCreateCommand`).
- `bash skills/dev-loop/scripts/env/agy-login.sh` — first-run login, two steps: no args prints
  the Google auth URL; `--code '<code>'` finishes onboarding (telemetry consent OFF unless
  `--telemetry`; workspace trust YES unless `--no-trust`) and chains into the live probe.
- `bash skills/dev-loop/scripts/env/agy-doctor.sh [--probe]` — health/auth verification.
- `skills/dev-loop/scripts/env/cloud-fedora-setup.sh` — **cloud environments** (claude.ai/code,
  `claude --cloud`, routines) are not devcontainers: the VM is a fixed Ubuntu 24.04 image and
  replacing the base image is unsupported, so this is the setup script to paste into the
  environment dialog. It builds `dev-loop-fedora:44` and installs `/usr/local/bin/fedora`
  (same paths, same `$PWD`). Measured 60s first run, 1.4s cold-session self-heal.
  With `FEDORA_DEVCONTAINER_REPO=https://github.com/mios-dev/MiOS` it instead projects MiOS's
  `.devcontainer/Containerfile` (built unedited on a locally shadowed, CA-trusting fedora:44)
  and installs `/usr/local/bin/mios-dev` (+ `fedora`). Measured 3m32s first run, 1.45s cold.
  It now also provisions the HOST (agy, keyring, grants; the plugin's SessionStart hook revives
  the keyring per session). It builds with the Dev Containers CLI (features included) and commits
  the devcontainer.json lifecycle into the image (miosd, root overlay). Measured 452s cold, over the
  ~5 min budget; `FEDORA_SETUP_BUDGET_S` defers the lifecycle if that stops the cache building.
  Its image and a mios-bootstrap `devcontainer build` compared identical (574-line package census).
- **Operator principle (2026-09-25): ALL MiOS images are equivalent and are full MiOS systems.**
  A devcontainer, the cloud-session projection, the WSL2 dev machine, a Codespace, an OCI artifact:
  each is the same MiOS system built by the one SSOT-driven pipeline, not a toolchain image with its
  own package list. Where container storage limits (cloud) constrain it, the same pipeline yields
  the CORE MiOS components first and the rest degrades open. Everything is rendered from SSOT
  mechanisms (`mios.toml`) controlled by static Rust binaries plus Python, hosted by the local
  server/container (miosd, agent-pipe), and backed by the MiOS database systems (the pgvector
  datastore; `check_db_seed_coverage` requires every SSOT section seeded). Every MiOS repo carries
  the same devcontainer definition, byte-identical and gated, buildable from its own root -- no
  sibling-checkout pointer (restored 2026-09-26: MiOS#38, mios-bootstrap#10, and this repo's
  mirror; the Ubuntu variant stays removed). The hand-authored
  `[packages.devcontainer]` list and `FEDORA_PACKAGES` in `cloud-fedora-setup.sh` are interim and
  must give way to the core profile of the real pipeline. Design: task #11 (SPIKE in flight).
  Details: `references/environment.md` § Fedora in a Claude Code *cloud environment*.
- **In a cloud session, a detached job does not outlive the container.** `job.py spawn` survives
  the monitor's turn, but not the container, and an idle session's container is reclaimed.
  Measured once (2026-09-25): a few minutes after the monitor's turn ended, the egress proxy
  refused connections (11:35:42Z) and three live AGY managers died mid-tool. The session resumed at 12:25Z on a
  restarted VM with the disk intact and no processes. So an AGY run in a cloud session lives only
  while a turn is open (the monitor blocks on `scripts/job.py wait`), and a check-in that finds a dead
  run must read its driver's log before calling it a quota death.
- The keyring holds the AGY credential unencrypted-at-rest (empty-password keyring) — accepted
  for ephemeral single-user containers only. Never print or export the credential.

## Working rules

- Follow `skills/dev-loop/SKILL.md`: DoD before code, two-sided verification, explicit-path
  staging only (never `git add -A`), secrets scan before commit, ledger entry before ending.
- **Questions to the operator go through the native question UI, never chat prose** (operator,
  2026-09-26). In Claude Code that is `AskUserQuestion`; the Stop hook sends back a reply that
  asks in prose (SKILL.md §5, `tests/test_stop_gate.py`). A lane or worker session with no UI
  reports `status: blocked` with the question, and the monitor asks it natively. Every open
  question is re-asked EVERY turn until answered (the hook also sends back a report blocked on the
  operator from a turn that never asked). A link the operator must open goes in a file card
  (`SendUserFile`) sent before the question, because the question UI does not render links.
- Gates for changes to this repo: `sh skills/dev-loop/scripts/validate.sh` must pass;
  shell edits get `bash -n` / `sh -n`; JSON edits must `json.load`.
- Harness CLI flags drift monthly: run `python3 skills/dev-loop/scripts/adapters.py probe`
  before relying on any lane command template.
