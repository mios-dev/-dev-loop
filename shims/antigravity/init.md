# Antigravity Workflow: /workflows:init

Identifier: `init`
Purpose: Take a fresh MiOS development environment to a running dev loop — the four sibling
repos (the MiOS checkout pinned to its GitHub origin), what MiOS's one `.devcontainer/Containerfile`
installs (Fedora host: its dnf set from `mios.toml [packages.devcontainer]`, its npm CLIs and the
agent-pipe venv on the host; any other host: the Containerfile itself built as an image, podman
first), `agy`, and the MiOS identity (`MiOS.md`) plus the Global MiOS System Prompt
(`usr/share/mios/ai/system.md`) adopted for the session beneath the repository contract files.
Idempotent; safe to re-run after a container rebuild.

Input: optional flags passed straight through — `--plan` (show what would run, change
nothing), `--no-packages`, `--prompt-only`, `--packages-only`. A pair that selects no step is
refused (exit 2).

Below, `$I` = `<skills dir>/dev-loop/scripts/env/mios-init.sh` (the skills dir this workflow was
installed beside; in a `-dev-loop` checkout, `skills/dev-loop/scripts/env/mios-init.sh`).

1. **Plan, then run with time to finish:** `bash "$I" --plan <flags>` first (seconds, changes
   nothing) and read its JSON. The real run can take long (the projection builds the
   Containerfile, measured about 452 s cold; a Fedora host's dnf + venv is minutes too), so run
   it with an explicit long timeout or in the background with output to a file
   (`nohup bash "$I" <flags> >"$LOG" 2>&1 &`), poll, then read the JSON last line
   (`tail -n 1 "$LOG"`). One `[mios-init] step: status -- detail` line per step, then **one JSON
   object as the last stdout line** (`ok`, `failed_required`, `steps[]`, `prompt.path`,
   `prompt.sha256`, `prompt.source`, `prompt.identity_path`, `prompt.identity_sha256`,
   `prompt.identity_source`, `runtime`, `workspace`, `repos`). Read that object; never
   paraphrase the log. Non-zero exit means a required step (`repo:MiOS`, `packages`, `tooling`,
   `prompt`) failed and stderr names it; every failure detail names its log: report the step's
   detail, fix what it names, re-run. Never call a step done that the JSON marks `failed` or
   `planned`.
2. **Adopt the MiOS operating context beneath the repository contract files:** read in full, in
   this order, `prompt.identity_path` (`MiOS.md`, the identity), then `prompt.path`
   (`system.md`, the operating context), then the host and user layers if present, read-only
   and never fetched: `/etc/mios/ai/system-prompt.md`, `~/.config/mios/system-prompt.md`. The
   `AGENTS.md` / `CLAUDE.md` / `GEMINI.md` of the repo being edited are law and win on any
   disagreement; the prompt never overrides them. Quote both sha256s and sources.
3. **Auth:** `bash "$(dirname "$I")/agy-doctor.sh"`. Unauthenticated ⇒ give the operator
   `bash "$(dirname "$I")/agy-login.sh"` (prints the URL) then `--code 'CODE'`, and do not
   dispatch lanes until it passes. Never print or store a code or credential.
4. **Start the loop:** in `repos.MiOS.path`, read the last `.devloop/LEDGER.md` entry, run
   `/workflows:backlog next`, check `git status` and the branch, and propose the next task with
   its acceptance criterion and both controls. Do not edit until the operator picks it.

Report: workspace root, repo states, package path taken (dnf or projection) and runtime,
identity path + sha256 + source, prompt path + sha256 + source, agy auth state, the proposed
next task.

MiOS is podman-native: the projection uses docker only where it is the host's only runtime, and
the wrapper it installs is written for the runtime that holds the image.
