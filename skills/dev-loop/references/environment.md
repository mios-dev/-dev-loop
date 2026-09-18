# Environment — running Antigravity (`agy`) in headless containers

`scripts/env/` provisions any Linux container so Antigravity can be a dev-loop
host or lane: **Fedora/RHEL family first** (dnf5 / dnf / microdnf — the
reference devcontainer is Fedora), Debian/Ubuntu (apt) second. All scripts are
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

`.devcontainer/` at the repo root: **Fedora 44 is the default config**
(`.devcontainer/devcontainer.json` + `Dockerfile`); an Ubuntu 24.04 variant
lives in `.devcontainer/ubuntu/`. Both bake the keyring stack, tmux/jq,
python3, and Node + Claude Code (for `claude-code` lanes), run
`setup-antigravity.sh` at `postCreateCommand`, and re-arm the keyring at
`postStartCommand` (daemons die with the container; the keyring *files*
survive in the home volume, so a restart needs no new login). `agy` installs
per-user at postCreate. Non-root `dev` user with passwordless sudo.

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
