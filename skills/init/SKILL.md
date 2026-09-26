---
name: init
description: Bootstrap a fresh MiOS development environment and start a dev-loop cycle in it - locate or shallow-clone the sibling repos (MiOS, mios-bootstrap, -dev-loop, mios-micro; the MiOS checkout is pinned to its GitHub origin), install what MiOS's one .devcontainer/Containerfile installs (Fedora host - its dnf set from mios.toml packages.devcontainer with weak deps off, its global npm CLIs and the agent-pipe venv; any other host - the Containerfile itself built as an image, podman first), provision agy, fetch the MiOS identity (MiOS.md) and the Global MiOS System Prompt (usr/share/mios/ai/system.md) and adopt them beneath the repository contract files, report Antigravity auth, then orient on the MiOS ledger and propose the next task. Wraps scripts/env/mios-init.sh, idempotent and safe to re-run. Use as the first command in a newly built cloud container, devcontainer or Fedora box, after a container rebuild, or whenever the MiOS prompt or package set must be refreshed before work begins.
argument-hint: "[--plan|--no-packages|--prompt-only|--packages-only]"
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

## 1. Plan first, then run with time to finish

```sh
bash "$I" --plan $ARGUMENTS    # what would run; changes nothing; finishes in seconds
```

Read the plan's JSON (the last stdout line, see below) before the real run. A full run can take
long: the projection builds MiOS's Containerfile (measured about 452 s cold) and a Fedora host's
`dnf install` plus the venv is minutes too, well past a tool call's default timeout. So run the
real thing either with an explicit long timeout (the Bash tool's `timeout` at its maximum,
600000 ms) or in the background with output to a file, and read the JSON last line afterwards:

```sh
LOG="${XDG_CACHE_HOME:-$HOME/.cache}/mios/mios-init.out"; mkdir -p "$(dirname "$LOG")"
nohup bash "$I" $ARGUMENTS >"$LOG" 2>&1 &
# poll (sleep 30 between looks) until the last line of $LOG starts with {"tool":"mios-init", then:
tail -n 1 "$LOG"
```

`--plan` and `--prompt-only` runs finish in seconds and may run in the foreground. `$ARGUMENTS`
is passed through: empty for a full run, `--plan` to see what would run and change nothing,
`--no-packages` to skip installation, `--prompt-only` to refresh only the prompt files,
`--packages-only` for the package path alone. A pair that selects no step (`--prompt-only` with
`--packages-only`, `--packages-only` with `--no-packages`) is refused with exit 2.

The script prints one `[mios-init] step: status -- detail` line per step and, as the **last line
of stdout, one JSON object**: `ok`, `failed_required`, `steps[]`, `prompt.path`, `prompt.sha256`,
`prompt.source`, `prompt.identity_path`, `prompt.identity_sha256`, `prompt.identity_source`,
`runtime`, `workspace`, `repos`. Read that object; do not paraphrase the log. What it does:

- **repos** — sibling checkouts under one workspace root (`$MIOS_WORKSPACES`, else the parent of
  a pinned MiOS checkout among the plugin's parent, `/workspaces`, `/home/user`, `$HOME`; the
  shell's cwd is never a candidate). Missing ones are shallow-cloned; existing ones are never
  fetched, checked out or switched. A directory counts as MiOS only when it is the root of a git
  work tree whose origin is `https://github.com/mios-dev/MiOS` (optional `.git`, or the ssh
  form); anything else carrying `mios.toml` + `packages.sh` is logged `ignored: origin is <url>`
  and skipped, because that checkout's `packages.sh` runs as root and its prompt is adopted.
  The pin is a trust statement, not a boundary: a directory at a candidate path whose origin is
  set to the MiOS URL is accepted, because a local checkout is the operator's own working copy,
  trusted exactly as its `packages.sh` already is. The deployed OS copy and GitHub `main` are the
  anchors when no such checkout exists.
- **packages** — what MiOS's one `.devcontainer/Containerfile` installs. Fedora host: the
  Containerfile's three installs on the host itself — its dnf set (`[packages.devcontainer]` of
  MiOS `usr/share/mios/mios.toml`, resolved by MiOS `automation/lib/packages.sh`, installed with
  `--setopt=install_weak_deps=False` as the Containerfile does; podman is in that set), its global
  npm CLIs (parsed from the Containerfile's `npm install -g` line, backslash continuations joined,
  never a copied list) and the agent-pipe venv (`python3.11 -m venv /usr/lib/mios/agents/.venv`
  + the `requirements.txt` the Containerfile's own `pip install -r` names, followed back to the
  MiOS tree through its COPY or staged path, skipped when the venv already holds every
  distribution that file names -- `pip freeze`, PEP 503 names, never a literal module list). Any
  other host (the stock cloud VM): the Containerfile itself, built as an image by
  `cloud-fedora-setup.sh` (podman first; docker where it is the host's only runtime); the runtime
  that holds the image is the setup script's own `--print-runtime` answer (it starts dockerd when
  needed, so a down daemon never reads as "image absent"); an existing image is not rebuilt, the
  wrapper (`$FEDORA_WRAPPER_DIR/mios-dev`, default `/usr/local/bin`) is installed for that
  runtime and verified to say so, and an existing wrapper that names the other runtime (or none)
  is rewritten the same way; enter it with `mios-dev`. `agy` is `setup-antigravity.sh`'s job on
  both paths.
- **tooling** — `setup-antigravity.sh --quiet` (agy, keyring, headless grants, the skill).
- **prompt** — two files, each from the deployed copy, else the pinned local MiOS checkout, else
  MiOS `main` on GitHub, written under `${XDG_CACHE_HOME:-~/.cache}/mios/`: the identity
  `MiOS.md` (deployed `/ctx/rootmd/MiOS.md`) and the Global MiOS System Prompt `system.md`
  (deployed `/usr/share/mios/ai/system.md`). An empty or non-markdown fetch fails loudly.

Exit is non-zero only when a **required** step failed (`repo:MiOS`, `packages`, `tooling`,
`prompt`); stderr names it. Every failure detail names its log (a fetch failure names its curl
stderr log, which holds curl's own message: a proxy refusal, a TLS or CA failure). URLs are logged
with their credentials redacted: userinfo and the value of a credential query parameter
(`?token=...`). When not root, forwarded variables reach `sudo` through a 0600 temp file, never
on its argv. Report a failed step with its `detail` and log path, fix what it names, re-run.
Never claim a step succeeded that the JSON marks `failed` or `planned`.

## 2. Adopt the MiOS operating context — beneath the repository contract files

Read **in full** (every line, not a skim), in this order:

1. `prompt.identity_path` — `MiOS.md`, the MiOS agent identity;
2. `prompt.path` — `system.md`, the operating context: architecture, laws and conventions;
3. the host and user prompt layers **if present**, read-only, never fetched and never created:
   `/etc/mios/ai/system-prompt.md`, then `~/.config/mios/system-prompt.md`.

Adopt them as the MiOS operating context **beneath** the repository contract files: the
`AGENTS.md` / `CLAUDE.md` / `GEMINI.md` of the repo being edited are law and win on any
disagreement; the prompt never overrides them. Say which source each file came from and quote
both sha256s (`prompt.identity_sha256`, `prompt.sha256`).

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
identity path + sha256 + source, prompt path + sha256 + source, agy auth state, and the proposed
next task.
