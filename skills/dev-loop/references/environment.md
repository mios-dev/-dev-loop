# Environment — running Antigravity (`agy`) in headless containers

`scripts/env/` provisions any Linux container so Antigravity can be a dev-loop
host or lane. The package manager is **detected, not assumed** — dnf5 / dnf /
microdnf where present, apt-get otherwise; the reference devcontainer happens
to be Fedora, and nothing in the loop requires it. All scripts are
idempotent, non-interactive, and location-independent (they resolve paths
relative to themselves, so they work from a repo checkout or an installed
skill copy).

## Why any of this exists

Antigravity documents **no non-interactive authentication**: you sign in once
in an interactive `agy` session, and the credential is cached in the OS
keyring (Secret Service). A headless container has no keyring daemon, so
without one every `agy` / `agy -p` launch re-asks for auth — which stalls
every lane of a parallel run. The env scripts close exactly that gap.

## The scripts

| Script | Job |
|---|---|
| `setup-antigravity.sh [--quiet]` | OS packages (keyring stack + tmux/jq), official `agy` installer (download-then-run, → `~/.local/bin`), keyring bootstrap, dev-loop skill install into `~/.gemini/config/skills`, `$CLAUDE_ENV_FILE` persistence |
| `agy-keyring.sh` (source it) | Session D-Bus + **unencrypted** default keyring; env cached in `~/.config/agy-cloud/keyring.env` for reuse; `AGY_KEYRING_VERIFY=1` adds a store/lookup round-trip (an env var, not an argument — dash's `.` drops arguments) |
| `agy-login.sh` | First-run login driver (below) |
| `agy-doctor.sh [--probe]` | PASS/WARN/FAIL: binary, keyring round-trip, skill install; `--probe` runs one real headless `agy -p` and checks `status: SUCCESS` |

## First-run login: two commands

```sh
bash scripts/env/agy-login.sh                    # 1. prints the Google auth URL
bash scripts/env/agy-login.sh --code '<code>'    # 2. submits the code, finishes, verifies
```

Step 1 starts `agy` in tmux session `agy-login`, walks it to the OAuth screen,
extracts the URL (tmux `-J` join, so wrapping can't split it), and exits;
`agy` keeps waiting. Step 2 pastes the code and drives the remaining
first-run screens — color scheme (default), Terms of Service (the optional
"share Interactions data with Google" checkbox is turned **OFF** unless
`--telemetry`: that consent belongs to the human), workspace trust (**Yes**
unless `--no-trust`) — then quits the TUI and chains into
`agy-doctor.sh --probe` so success is *proven*, not assumed. Already
authenticated? Either step detects the main prompt and skips straight to the
probe. On an unrecognized screen (TUIs drift) it dumps the pane with manual
`tmux` instructions instead of guessing.

On a real terminal with no flags it just execs `agy` — the native flow is the
best UX for humans.

## Devcontainers

`.devcontainer/` at the repo root is the MiOS dev environment, **Fedora 44
only** (`.devcontainer/devcontainer.json` + `Containerfile`; there is no
Ubuntu variant -- every MiOS dev environment is Fedora). `Containerfile` is a
byte-identical mirror of MiOS's `.devcontainer/Containerfile`, the one MiOS
dev image, gated by `tests/test_devcontainer_mirror.py`: edit it in MiOS,
never here. The file is context-independent: built from this repo's root it
shallow-clones MiOS and resolves `[packages.devcontainer]` from that clone, so
no sibling checkout and no `initializeCommand` are needed. The image bakes the
keyring stack, tmux/jq, python3, Node + the agent CLIs and `agy` (fail-closed).
`postCreateCommand` runs MiOS's `setup-devcontainer.sh` (cloning MiOS to
`/workspaces/MiOS` when absent), which runs `setup-antigravity.sh`;
`postStartCommand` runs MiOS's `boot-mios-systems.sh` + `post-start.sh`, which
re-arm the keyring (daemons die with the container; the keyring *files*
survive in the home volume, so a restart needs no new login). Non-root
`mios-dev` user (uid 1000) with passwordless sudo.

## Security model, stated plainly

The keyring is created with **no password** (plaintext at rest): anyone with
access to the container can recover the cached credential. Accepted for an
ephemeral, single-user container; never copy this pattern to a shared or
persistent host. Never print the credential; assert presence with the doctor,
not with `secret-tool lookup` in a transcript.

## Claude Code on the web

The repo's SessionStart hook (`.claude/settings.json` →
`.claude/hooks/session-start.sh`) runs `setup-antigravity.sh --quiet` on every
remote session and persists PATH + keyring env via `$CLAUDE_ENV_FILE`.
Containers there are ephemeral: each brand-new container needs the two-command
login once.

POSIX-only for now; there is no PowerShell port of the env scripts
(`install.ps1` installs the skill but Windows keyring caching is untested).

## A different distro userland in a Claude Code *cloud environment* (worked example: Fedora)

When a project's toolchain needs a userland the cloud VM does not provide —
a different distro's package manager, a specific libc or compiler set — the
image cannot simply be swapped. A cloud environment (claude.ai/code, `claude
--cloud`, routines) is not a devcontainer: the VM is a fixed **Ubuntu 24.04
x86_64** image and, per
`code.claude.com/docs/en/cloud-environments`, *"replacing the base image
entirely isn't supported yet"*. There is no image, Dockerfile or devcontainer
field anywhere in the environment dialog — only name, network access,
environment variables and a setup script.

`scripts/env/cloud-fedora-setup.sh` is that setup script. Docker **is**
pre-installed on the VM, and the platform snapshots the filesystem once the
setup script has run and reuses it for every later session, so a Fedora image
built there is already on disk next time at no startup cost. The script builds
`dev-loop-fedora:44` from `registry.fedoraproject.org/fedora:44` and installs
`/usr/local/bin/fedora`:

```sh
fedora                  # interactive Fedora shell
fedora dnf install -y … # Fedora package management
fedora python3 -V       # anything, in Fedora
```

Host paths (`/home`, `/root`, `/workspace`, `/srv`) are bind-mounted at the
**same absolute path** and `$PWD` is preserved, so a path means the same thing
on both sides and no file is copied to cross the boundary.

Three details the script exists to get right:

- **The egress CA.** Cloud sessions leave through a TLS-terminating proxy. A
  container that does not trust its CA fails every https fetch with
  `self-signed certificate in certificate chain` — `dnf` first of all. The CA
  is baked into the image's trust store (never `verify=off`), and because the
  minimal Fedora image ships no `/etc/pki/tls/certs/ca-bundle.crt`, the script
  creates that compat symlink too and points `SSL_CERT_FILE` and friends at
  `/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem`, the file
  `update-ca-trust` actually writes.
- **`--network host`.** The proxy listens on the VM's `127.0.0.1`, which a
  bridged container cannot reach. Both the build and the container use host
  networking.
- **No metalink.** The repos are pinned to `dl.fedoraproject.org` instead of
  the default metalink, which hands `dnf` a different third-party mirror
  hostname on every run — something no network allowlist can cover.
  `gpgcheck` stays on.

Everything is idempotent and failure-tolerant: a setup script that exits
non-zero fails the whole session, so every step is guarded and the script ends
in an unconditional `exit 0` — a failed provision degrades to a plain Ubuntu
session with a log line. The wrapper is self-healing for the same reason the
snapshot needs it to be: the cache restores *files*, never running processes,
so `fedora` starts `dockerd` and re-creates the container itself on a cold
session.

**Measured (2026-09, Ubuntu 24.04 cloud VM, docker 29.3.1/overlayfs):** first
run 60s wall clock, well inside the ~5-minute budget the cache needs; re-run
0.25s; cold session, daemon down and container gone, `fedora <cmd>` back up in
1.4s. Fedora 44 with git 2.55, Python 3.14, Node 22, gcc 16; `dnf`, `pip` and
`curl` all verified through the proxy with TLS verification on.

### Projecting a repo's devcontainer (worked example: MiOS)

Set `FEDORA_DEVCONTAINER_REPO` and the same script turns the session into a
projection of that repo's devcontainer rather than the generic image:

```sh
FEDORA_DEVCONTAINER_REPO=https://github.com/mios-dev/MiOS
FEDORA_DEVCONTAINER_FILE=.devcontainer/Containerfile   # the default
```

It shallow-clones the repo to `/opt/dev-loop-fedora/src/<name>` and builds its
Containerfile **unedited**, with the repo root as context. The Containerfile's
hard-coded `FROM registry.fedoraproject.org/fedora:44` is made to resolve to a
base built first — upstream Fedora plus the egress CA, the pinned repos (every
other repo disabled, since a devcontainer's `dnf install` has no
`--disablerepo`) and `ENV SSL_CERT_FILE`/`CURL_CA_BUNDLE`/`REQUESTS_CA_BUNDLE`/
`NODE_EXTRA_CA_CERTS`/`PIP_CERT` — tagged locally under the upstream name.
Docker resolves `FROM` from the local store before any registry, so the build
lands on the shadow (the build log shows the base's digest), and every later
layer inherits the CA env: MiOS's `npm install -g`, its python3.11 venv `pip
install` and its Antigravity `curl` all run through the proxy with
verification on. The real upstream is kept as `dev-loop-fedora-upstream:<tag>`,
so a rebuild never bases the shadow on itself.

The wrapper is installed as `/usr/local/bin/<repo>-dev` (`mios-dev`) and as
`/usr/local/bin/fedora`, both entering the same container. Its image, mode and
build settings are baked in at install time, so a later session that sets
nothing still means the same image and a first-use build rebuilds the same
mode; the script caches itself at `/opt/dev-loop-fedora/cloud-fedora-setup.sh`
for that. Commands run as root by default because the bind-mounted workspace
is root-owned in a cloud session; `FEDORA_EXEC_USER=mios-dev` runs as the
devcontainer's own user instead. `/home` is mounted per entry, never whole —
mounting it whole hides the image's `/home/mios-dev/.local/bin`, where MiOS
installs `agy`.

**Commit from the host, not the container.** A cloud session signs commits
through a platform helper (`gpg.ssh.program=/tmp/code-sign`, a symlink into
`/opt/env-runner/`), and neither path is mounted into the container. So
`git commit` inside `mios-dev` fails (`cannot exec '/tmp/code-sign'`, exit
128), and so does any test suite that makes commits in a temp repo: this is
why `validate.sh` errors in four suites inside the container and passes on the
host. Build, test and run inside `mios-dev`; stage, commit and push on the
host, where the files are the same files.

Why the devcontainer and not MiOS's own image: `ghcr.io/mios-dev/mios:latest`
is a bootc OCI image of 22.8 GB compressed in 79 layers — too big for the
setup budget or the VM's disk. The devcontainer is MiOS's build and dev
userspace, which is what a session needs; the bootc image is what it produces.

**Measured (2026-09-25, same VM class):** setup script, nothing cached, 3m32s
wall clock (build 208s: dnf 54s, npm 18s, venv 17s, layer export 97s) —
inside the ~5-minute budget, with little room, so on a slow day prefer
`--wrapper-only`; re-run with the image present 0.36s; cold session (dockerd
down, container gone) 1.45s; first-use build through the wrapper with no
`FEDORA_DEVCONTAINER_*` in the environment 3m14s. Inside: Fedora 44, just
1.57.0, bootc 1.16.13, cargo 1.98.1, venv Python 3.11.16, agy 1.2.11, claude,
gemini, copilot, podman, ShellCheck, `MIOS_DEVCONTAINER=1`.

Trust was checked on both sides against a host the proxy actually intercepts:
the proxy MITMs only some hosts (`github.com` yes; `dl.fedoraproject.org`,
`pypi.org`, `registry.npmjs.org` and `registry.fedoraproject.org` pass through
to curl untouched), so a fetch from those proves nothing either way. From the
same Fedora 44 without the CA layer, `curl https://github.com/…` fails with
`(60) self-signed certificate in certificate chain`; inside `mios-dev`, curl,
the venv's Python and node all complete the handshake. With the CA step
disabled (`FEDORA_CA_BUNDLE=none`), the build's `dnf` fails the same way.

### When the dialog has no Setup script field

Observed 2026-09: an environment dialog showing only **Name**, **Network
access** and **Environment variables** — no Setup script box, though the docs
describe one. Pasting a script into the variables box fails loudly, because
that box validates `.env` format and reports every line of a shell script as
invalid.

For that case the script takes `--wrapper-only`: it installs
`/usr/local/bin/fedora` and skips the pull and build, so the first `fedora …`
call builds the image on demand instead. The repo's SessionStart hook
(`.claude/hooks/session-start.sh`) runs it that way, which needs no
environment configuration at all — at the cost of paying the ~60s build once
per fresh container rather than once per environment, and only in sessions
that check out this repo.

Two hazards that path has to handle, both of them found by hitting them:

- **A script must not rewrite itself while it runs.** The on-demand build
  re-runs this script, which would reinstall the wrapper that is *currently
  executing*; bash reads a script incrementally by byte offset, so truncating
  and rewriting it makes the shell resume mid-line (`ome/*|/root|…`). The
  wrapper is installed write-then-rename so the running shell keeps its open
  inode, and an autobuild skips reinstalling it entirely.
- **Build the image before reading container state.** The build's own
  verification call goes through the wrapper and can create the container, so
  any state read before the build is stale by the time it is used — which
  surfaced as a `container name already in use` failure.

`FEDORA_NO_AUTOBUILD=1` guards the recursion: the setup script verifies itself
through the wrapper, and a failed build must not bounce the two off each other
forever.

**Measured:** `--wrapper-only` install 0.016s; cold first use with no image, no
build cache and dockerd down, 60s; every call after that 0.18s.

### Creating the environment

The environment itself can only be created in the UI — there is no API for it,
and no settings page either: at claude.ai/code, use the cloud icon in the row
above the message box → **Add cloud environment**, paste the script into
**Setup script**, **Create environment**. The selector is also where an
environment is made the default: whichever one is ticked there is what new
sessions on web, mobile and Desktop use. The CLI keeps its own pick — set it
with `/remote-env` in a terminal session.

Network access: `registry.fedoraproject.org` and `dl.fedoraproject.org` both
resolved under this account's **Trusted** Default environment, though neither
appears in the published default allowlist. Under a **Custom** policy, allow
those two hosts explicitly (keeping the defaults on).

### The dev-loop plugin in a cloud session (`/dev-loop:*` commands)

A cloud session loads none of the ways this repo normally ships the plugin:
marketplace plugins and a repository's `enabledPlugins`/`extraKnownMarketplaces`
are not loaded, and adding a marketplace or loading a project-scope
`.claude/skills/<name>/.claude-plugin/` plugin both need the workspace trust
dialog, which a cloud session never shows (code.claude.com/docs/en/plugins/loading).
`~/.claude/skills/` is not read in cloud sessions either.

What does load is a plugin directory named in the `CLAUDE_CODE_PLUGIN_DIRS`
environment variable (Claude Code 2.1.280+; project settings cannot set it,
but a cloud environment's variables are the session's process environment).
So the environment clones the plugin to a fixed path and points the variable
at it, which works in sessions for any repository, not only this one:

Setup script:

```bash
#!/bin/bash
# MiOS Fedora dev environment + the dev-loop plugin (/dev-loop:*) in every session.
export FEDORA_DEVCONTAINER_REPO=https://github.com/mios-dev/MiOS
export FEDORA_DEVCONTAINER_FILE=.devcontainer/Containerfile
# dev-loop plugin checkout; loaded by CLAUDE_CODE_PLUGIN_DIRS=/opt/dev-loop
if [ -d /opt/dev-loop/.git ]; then
  git -C /opt/dev-loop pull -q --ff-only || true
else
  git clone -q --depth 1 https://github.com/mios-dev/-dev-loop /opt/dev-loop || true
fi
[ -f /opt/dev-loop/skills/dev-loop/scripts/env/cloud-fedora-setup.sh ] &&
  bash /opt/dev-loop/skills/dev-loop/scripts/env/cloud-fedora-setup.sh
exit 0
```

Environment variables:

```
FEDORA_DEVCONTAINER_REPO=https://github.com/mios-dev/MiOS
FEDORA_DEVCONTAINER_FILE=.devcontainer/Containerfile
CLAUDE_CODE_PLUGIN_DIRS=/opt/dev-loop
```

**Measured (2026-09-25, Claude Code 2.1.282),** reading the `init` event of
`claude -p --output-format stream-json`: without the variable, 0 `dev-loop:`
commands and no plugin; with it, from an unrelated repository, the plugin loads
as `dev-loop@inline` with 15 commands (`/dev-loop:dev-loop`, `/dev-loop:review`,
`/dev-loop:ship`, `/dev-loop:goal`, …), 5 agents (`dev-loop:auditor`, …) and its
MCP server `plugin:dev-loop:dev-loop` connected. Plugin commands carry the
`dev-loop:` prefix; there is no bare `/review`.

The checkout refreshes each time the setup script runs (a new environment
cache), not every session. The repo-root `.mcp.json` also reads as a
project MCP config in sessions of this repo, where `${CLAUDE_PLUGIN_ROOT}` is
empty and the `dev-loop` server fails to start; the plugin's copy is the one
that connects (see `scripts/register-mcp.sh` for per-harness registration).
