# dev-loop — universal autonomous engineering loop (v7.6.0)

One repo, four things:

1. **A Claude Code plugin** — `.claude-plugin/plugin.json`, seven skills (`/dev-loop`, `/goal`, `/research`, `/review`, `/ship`, `/triage`, `/websearch`), five agents (`orchestrator`, `lane-worker` in an isolated worktree, `auditor`, `triage`, `researcher`), and enforcement hooks.
2. **A portable skill set** (Agent Skills open standard) plus thin command shims for Antigravity, Gemini CLI, Codex, Copilot, Cursor and OpenCode — and a skills-only install for agentskills.io-compatible gateways, which expose `/dev-loop` from the skill itself — installed by `skills/dev-loop/scripts/install.sh` / `.ps1`.
3. **An MCP server** (`skills/dev-loop/scripts/devloop_mcp.py`, registered by `.mcp.json`) so any MCP-capable host drives the orchestrator: `validate_lanes`, `run_lanes`, `gate`, `report`, `tasks_next`, `task_set`, `ledger`, `scaffold`, `probe`.
4. **Harness-neutral glue** in `skills/dev-loop/scripts/`: `adapters.py` (9 lane harnesses, gates, probe, ledger), `devloop.sh` / `DevLoop.ps1` (worktree lane orchestrators), `artifacts.py` (AGENTS.md, GOALS, ROADMAP, MADR ADRs, tasks.jsonl → TASKS.md, DoD, checklists, CHANGELOG, ledger), `goal.py`, `research.py`, `review.py`, `ship.py`, `triage.py`, `devloop_worker.py` (OpenAI-compatible worker), `contracts.py` (cross-lane interface exchange), `verify_harness.py`; docs in `references/`, schemas/templates in `assets/` (agentskills.io layout).

## Install

```sh
# Claude Code (plugin — recommended)
claude plugin marketplace add /path/to/dev-loop        # or a git URL
claude plugin install dev-loop@dev-loop-marketplace     # /dev-loop:goal etc., and bare /dev-loop /goal /research /review /ship /triage /websearch while unambiguous
# takes effect at the NEXT session start; in a running session run /reload-plugins
# local dev:  claude --plugin-dir /path/to/dev-loop

# Every OTHER harness (Claude Code is covered by the plugin above - do not register it twice), user scope, plus the canonical artifacts
sh skills/dev-loop/scripts/install.sh --harness antigravity,gemini,codex,cursor,copilot,opencode,hermes --user --scaffold
pwsh skills/dev-loop/scripts/install.ps1 -Harness antigravity,gemini,codex,cursor,copilot,opencode,hermes -User -Scaffold
# re-sync one harness after editing the repo (these installs are COPIES and go stale):
sh skills/dev-loop/scripts/install.sh --harness antigravity --user
```

### Gemini Spark (upload package): `dev-loop-web`

Spark has no install path: it takes a skill only as an uploaded `SKILL.md` or a `.zip` with `SKILL.md` at its
root, plain text only. `skills/dev-loop-web/` is the web-only variant of the loop (no shell, no checkout: fetch the
task's contract at a pinned commit, prove bytes by git blob SHA, check both ways, end on the contract's verdict line),
written in the portable Agent Skills subset and holding no project values. Package it, then upload
`dist/dev-loop-web.zip` on Spark's Skills page:

```sh
sh skills/dev-loop/scripts/install.sh --harness gemini-spark            # -> dist/dev-loop-web.zip (or --out PATH/dev-loop-web.zip)
python3 skills/dev-loop/scripts/skill_package.py check dist/dev-loop-web.zip   # the same gate validate.sh runs
```

The package is gated before it lands (portable keys only, description ≤ 1024, body < 500 lines, plain-text files
only, no `.pyc`, name = folder); controls: `tests/test_dev_loop_web_package.py`. Nothing in it has run on a live
Spark yet; its capability preflight (SKILL.md §2) is what the first run settles.

Required Claude Code settings: `"worktree": {"baseRef": "head"}`; version ≥ 2.1.219. Run `python3 skills/dev-loop/scripts/adapters.py probe` after installing or upgrading any harness CLI.

### Verify the install is registered *and current*

A directory in `~/.claude/skills/` or `~/.gemini/config/skills/` proves nothing: a stale copy looks exactly like a fresh one.

```sh
# Claude Code - enabled, and pointing at THIS tree. A directory-source marketplace loads IN PLACE,
# so the repo is the installed copy and cannot go stale; the inventory below is read live from it.
claude plugin list --json | python3 -c 'import json,sys; p=[x for x in json.load(sys.stdin) if x["id"]=="dev-loop@dev-loop-marketplace"]; assert p and p[0]["enabled"], p or "NOT INSTALLED"; print("enabled, version", p[0]["version"])'
python3 -c 'import json,os; s=json.load(open(os.path.expanduser("~/.claude/settings.json"))); print(s["extraKnownMarketplaces"]["dev-loop-marketplace"]["source"]["path"])'   # must print this repo
claude plugin details dev-loop@dev-loop-marketplace   # must read: Skills (7), Agents (5), Hooks (7), MCP servers (1)

# Antigravity - the install IS a copy, so rebuild a reference copy with the same installer and diff.
# (SKILL.md is frontmatter-stripped on the way in, so a plain `diff -r` against skills/ can never pass.)
REF=$(mktemp -d); HOME="$REF" sh skills/dev-loop/scripts/install.sh --harness antigravity --user >/dev/null 2>&1
diff -r -x __pycache__ "$REF/.gemini/config/skills" "$HOME/.gemini/config/skills" \
  && diff -r "$REF/.gemini/config/workflows" "$HOME/.gemini/config/workflows" \
  && echo "AGY install CURRENT"; rm -rf "$REF"
```

## Conformance
`sh skills/dev-loop/scripts/validate.sh` — agentskills.io validator on every skill (sub-skills as the six-key copies other harnesses receive), plugin/hook/agent shapes, schemas, syntax, and `claude plugin validate --strict` when the CLI is present. Details and sources: `skills/dev-loop/references/conformance.md`.

## Use

- `/dev-loop <objective>` — one task through the loop. `/dev-loop lanes:<lanes.json>` — parallel lanes in any mix of harnesses (schema: `assets/lane-schema.json`, example: `assets/lanes.example.json`).
- `/goal dev <objective>` — define stopping conditions, decompose into tasks, iterate until `goal.py eval` passes.
- `/research …` → `/dev-loop …` → `/review` → `/ship <branch>`; `/triage <failing cmd>` before touching code.

Any harness can be the host; any harness can run a lane (`references/harness-adapters.md`). State lives on disk (`.devloop/`), never in the context window (`references/artifacts.md`).

## Environments: devcontainers + Claude Code on the web

The environment layer ships **inside the skill** (`skills/dev-loop/scripts/env/`, docs in
`references/environment.md`), so every dev-loop install carries it. It detects the host's
package manager (dnf5/dnf/microdnf, else apt-get) rather than assuming one — idempotent, and
location-independent.

**Devcontainers:** `.devcontainer/devcontainer.json` is **Fedora 44** (this repo's default
image); `.devcontainer/ubuntu/` is the Ubuntu 24.04 variant. Both bake the keyring stack plus
Node + Claude Code for `claude-code` lanes, provision at `postCreateCommand`, and re-arm the
keyring at `postStartCommand` — after a container restart no new login is needed.

**Claude Code on the web:** the SessionStart hook (`.claude/settings.json` →
`.claude/hooks/session-start.sh`) runs the same provisioning on every remote session.

**First-run login — two commands, from any of these environments** (Antigravity has no
non-interactive auth; the driver walks agy's entire first-run TUI and *proves* the result with a
live headless probe):

```sh
bash skills/dev-loop/scripts/env/agy-login.sh                  # 1. prints the Google auth URL
bash skills/dev-loop/scripts/env/agy-login.sh --code '<code>'  # 2. finishes onboarding + verifies
```

Defaults chosen for you (flags to override): Google's "share Interactions data" checkbox OFF
(`--telemetry` to opt in — that consent belongs to the human), workspace trust YES
(`--no-trust`). Already signed in? Either command detects it and skips straight to the
verification probe. Containers are ephemeral: a brand-new container needs the login once. The
keyring is empty-password (credential recoverable by anyone with container access) — acceptable
for a single-user ephemeral session only.

## AGY as manager (topology A, this repo's default)

`AGENTS.md` (the constitution — law in every harness) makes Antigravity the L0 manager of all
dev-loop sub-agents in this repo. It dispatches any mix of lanes, including **multiple
concurrent Antigravity lanes** (separate `agy -p` processes) **and multiple concurrent Claude
Code lanes** (`claude -p`), each in its own git worktree with its own two-sided gate:

```sh
python3 skills/dev-loop/scripts/adapters.py probe                     # flags drift monthly — check first
sh skills/dev-loop/scripts/agy_host.sh my-lanes.json                  # interactive manager
sh skills/dev-loop/scripts/agy_host.sh my-lanes.json --headless       # unattended manager (JSON out)
```

The manager is **native-first**: Antigravity's own multi-agent machinery (subagents via
`invoke_subagent` with `workspace: branch`, native workflows) runs its own lanes by default;
the reference orchestrator is how Claude Code and other harnesses join the loop. Harness-native
loop commands inside lanes are allowed and never replace the gates.

Model defaults (operator policy, 2026-09): Claude Code lanes run `--model opus --effort xhigh`
(the alias tracks the newest Opus release; the manager assigns lower tiers — sonnet/haiku,
lower effort — to light lanes); Antigravity lanes default to `gemini-3.8-flash-high`; the
headless manager runs `gemini-3.1-pro-high` (`AGY_HOST_MODEL` / `AGY_HOST_EFFORT` override;
per-lane `worker.model` / `worker.effort` win). Verified live: the full AGY-managed mixed-lane
e2e (`tests/e2e-mixed-lanes/`) passes end to end under scoped agy permission rules. Upstream
pattern survey, with patterns copied and credited at pinned commits (nothing vendored):
`skills/dev-loop/references/upstream-patterns.md`.

Mixed-lane example: `skills/dev-loop/assets/lanes.agy-manager.example.json` (2 AGY lanes +
2 Claude Code lanes + an AGY auditor). The manager runs every merge gate itself; lanes never
commit, and a lane whose negative control passes is never merged.

## SCOPE staged review (v7.6.0, merged from the dev-loop v2.x lineage)

`/review` now runs the full **SCOPE** oversight model (Staged Code Oversight with Proportional
Escalation, after Greiler's staged-review work): Stage 1 agent review (severity × dimension
findings; secret scan covers keyword assignments AND bare token formats — AKIA/ghp_/sk-/AIza/
xox), Stage 2 steering-developer ownership with Agent-Dev Loop sizing (≤ 600 lines / ≤ 20
files), Stage 3 proportional peer escalation (Understanding Need × Change Risk × Established
Assurance → escalation tier), recorded in a Living Oversight Record
(`OVERSIGHT_RECORD.md` + `.devloop/scope_review_*.json`). The goal/ship/research/triage engines
took the same lineage's refinements, and `scripts/git_lock.py` plus a stale-`index.lock`
sweep in the adapters' git retry protect multi-lane git contention.
