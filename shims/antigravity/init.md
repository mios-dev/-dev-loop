# Antigravity Workflow: /workflows:init

Identifier: `init`
Purpose: Take a fresh MiOS development environment to a running dev loop — the four sibling
repos, the MiOS package set from `mios.toml [packages.devcontainer]`, `agy`, and the Global
MiOS System Prompt (`usr/share/mios/ai/system.md`) adopted for the session. Idempotent; safe to
re-run after a container rebuild.

Input: optional flags passed straight through — `--plan` (show what would run, change
nothing), `--no-packages`, `--prompt-only`.

Below, `$I` = `<skills dir>/dev-loop/scripts/env/mios-init.sh` (the skills dir this workflow was
installed beside; in a `-dev-loop` checkout, `skills/dev-loop/scripts/env/mios-init.sh`).

1. **Run it:** `bash "$I" <flags>`. One `[mios-init] step: status -- detail` line per step, then
   **one JSON object as the last stdout line** (`ok`, `failed_required`, `steps[]`, `prompt.path`,
   `prompt.sha256`, `prompt.source`, `runtime`, `workspace`, `repos`). Read that object; never
   paraphrase the log. Non-zero exit means a required step (`repo:MiOS`, `packages`, `tooling`,
   `prompt`) failed and stderr names it: report the step's detail, fix what it names, re-run.
   Never call a step done that the JSON marks `failed` or `planned`.
2. **Adopt the prompt:** read `prompt.path` in full and treat it as the governing MiOS system
   prompt for this session; quote its sha256 and source. `AGENTS.md` / `GEMINI.md` of the repo
   being edited still win wherever they are stricter.
3. **Auth:** `bash "$(dirname "$I")/agy-doctor.sh"`. Unauthenticated ⇒ give the operator
   `bash "$(dirname "$I")/agy-login.sh"` (prints the URL) then `--code 'CODE'`, and do not
   dispatch lanes until it passes. Never print or store a code or credential.
4. **Start the loop:** in `repos.MiOS.path`, read the last `.devloop/LEDGER.md` entry, run
   `/workflows:backlog next`, check `git status` and the branch, and propose the next task with
   its acceptance criterion and both controls. Do not edit until the operator picks it.

Report: workspace root, repo states, package path taken (dnf or projection) and runtime, prompt
path + sha256 + source, agy auth state, the proposed next task.

MiOS is podman-native: the projection uses docker only where it is the host's only runtime.
