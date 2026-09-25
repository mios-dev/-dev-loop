---
name: init
description: Bootstrap a fresh MiOS development environment and start a dev-loop cycle in it - locate or shallow-clone the sibling repos (MiOS, mios-bootstrap, -dev-loop, mios-micro), install the MiOS package set (dnf on a Fedora host from mios.toml packages.devcontainer, podman included; on any other host the identical Fedora userspace projected from the MiOS devcontainer), provision agy, fetch the Global MiOS System Prompt (usr/share/mios/ai/system.md) and adopt it for the session, report Antigravity auth, then orient on the MiOS ledger and propose the next task. Wraps scripts/env/mios-init.sh, which is idempotent and safe to re-run. Use as the first command in a newly built cloud container, devcontainer or Fedora box, after a container rebuild, or whenever the MiOS system prompt or package set must be refreshed before work begins.
argument-hint: "[--plan|--no-packages|--prompt-only]"
allowed-tools: Read, Grep, Glob, Bash, Skill
---
# /init — fresh environment to a running MiOS dev loop

_Name: in Claude Code this skill is `/dev-loop:init` (the plugin namespace); the bare `/init`
there is Claude Code's own built-in, which writes a CLAUDE.md and is unrelated. Antigravity
gets `/workflows:init` from `shims/antigravity/init.md`._

_Paths: the script is `${CLAUDE_PLUGIN_ROOT}/skills/dev-loop/scripts/env/mios-init.sh` in Claude
Code (equivalently `${CLAUDE_SKILL_DIR}/../dev-loop/scripts/env/mios-init.sh`). Fallback when
neither variable is set: `skills/dev-loop/scripts/env/mios-init.sh` inside a `-dev-loop` checkout
(for example `/home/user/-dev-loop` or `/workspaces/-dev-loop`), or `/opt/dev-loop/...` where the
plugin is installed. Below, `$I` = that script._

## 1. Run the bootstrap

```sh
bash "$I" $ARGUMENTS
```

`$ARGUMENTS` is passed through: empty for a full run, `--plan` to see what would run and change
nothing, `--no-packages` to skip installation, `--prompt-only` to refresh only the prompt.
The script prints one `[mios-init] step: status -- detail` line per step and, as the **last line
of stdout, one JSON object**: `ok`, `failed_required`, `steps[]`, `prompt.path`,
`prompt.sha256`, `prompt.source`, `runtime`, `workspace`, `repos`. Read that object; do not
paraphrase the log. What it does:

- **repos** — sibling checkouts under one workspace root (`$MIOS_WORKSPACES`, else the parent of
  an existing MiOS checkout, else `/workspaces`, else `$HOME`). Missing ones are shallow-cloned;
  existing ones are never fetched, checked out or switched.
- **packages** — Fedora host: `dnf install -y` of `[packages.devcontainer]` from MiOS
  `usr/share/mios/mios.toml`, resolved by MiOS `automation/lib/packages.sh` (never a copied
  list). Any other host (the stock cloud VM): `cloud-fedora-setup.sh` projects MiOS's one
  `.devcontainer/Containerfile`; an existing image is not rebuilt; enter it with `mios-dev`.
  MiOS is podman-native; docker is used only where it is the host's only runtime.
- **tooling** — `setup-antigravity.sh --quiet` (agy, keyring, headless grants, the skill).
- **prompt** — the Global MiOS System Prompt from the deployed `/usr/share/mios/ai/system.md`,
  else the local MiOS checkout, else MiOS `main` on GitHub, written to
  `${XDG_CACHE_HOME:-~/.cache}/mios/system.md`. An empty or non-markdown fetch fails loudly.

Exit is non-zero only when a **required** step failed (`repo:MiOS`, `packages`, `tooling`,
`prompt`); stderr names it. Report a failed step with its `detail` and log path, fix what it
names, re-run. Never claim a step succeeded that the JSON marks `failed` or `planned`.

## 2. Adopt the Global MiOS System Prompt

Read `prompt.path` **in full** (every line, not a skim) and adopt it as the governing MiOS system
prompt for this session: its architecture, laws and conventions apply to all MiOS work that
follows. Say which source it came from and quote its sha256. Precedence: the repository contract
files (`AGENTS.md`, `CLAUDE.md` of the repo being edited) still win wherever they are stricter;
the prompt never relaxes them.

## 3. Antigravity auth

```sh
bash "$(dirname "$I")/agy-doctor.sh"
```

Report PASS/FAIL lines for the binary, keyring and grants as printed. If it reports
unauthenticated (or agy cannot run its permissions check for an auth reason), give the operator
the one-line remedy and stop short of dispatching AGY lanes:

```sh
bash "$(dirname "$I")/agy-login.sh"   # prints the auth URL; then: agy-login.sh --code 'CODE'
```

Never print, echo or store a credential or an auth code. Until agy is authenticated, a Claude
Code session may host the loop (topology B) and must say so.

## 4. Start the dev-loop cycle

In the MiOS checkout (`repos.MiOS.path`), invoke the `dev-loop` skill to orient: read the last
ledger entry (`.devloop/LEDGER.md`), list what is ready (`/dev-loop:backlog next`), check
`git status` and the current branch, and **propose the next task** with its acceptance criterion
and both controls. Do not start editing until the operator (or the standing brief) picks it.

## Report

End with: workspace root, repo states, package path taken (dnf or projection) and runtime,
prompt path + sha256 + source, agy auth state, and the proposed next task.
