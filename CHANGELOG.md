# Changelog
All notable changes to this project are documented here. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning: SemVer.

## [Unreleased]
### Added
- `skills/dev-loop-web/`: web-only variant of the loop for scheduled out-of-loop agents (Gemini Spark), portable Agent Skills subset, no project values; offline stdlib scripts (`bytes_proof`, `digest`, `jsonl_check`, `oci_closure`, `schema_check`, `secret_scan`), each with `--self-test` and `--two-sided`.
- `install.sh` / `install.ps1` `gemini-spark` package target and `skill_package.py` (pack + gate); `validate.sh` gates the emitted zip; controls in `tests/test_dev_loop_web_package.py`.
- `/dev-loop:init` (`skills/init/`, `scripts/env/mios-init.sh`): fresh MiOS environment to a running dev loop — sibling repos, the MiOS package set from `mios.toml [packages.devcontainer]` (dnf on Fedora, the projected MiOS devcontainer elsewhere), `agy`, the Global MiOS System Prompt adopted for the session; controls in `tests/test_mios_init.py`.
- `cloud-fedora-setup.sh`: provisions the cloud VM itself (`agy`, keyring, grants, skill); builds through the Dev Containers CLI (features included) and commits the `devcontainer.json` lifecycle into the image, with a status file, `FEDORA_SETUP_BUDGET_S` to defer it and `--lifecycle` to apply it later; `FEDORA_RUNTIME` (`auto`/`podman`/`docker`, podman first; `tests/test_cloud_runtime.py`).
- Plugin SessionStart hook revives `agy`'s keyring in every cloud session and exports its bus through `CLAUDE_ENV_FILE` (`tests/test_session_start_keyring.py`).
- README: the paste-able cloud-environment setup script and every variable, described, beside the install commands.
### Changed
- `agy_settings.py` reads the accepted `artifactReviewPolicy` spellings from the installed agy (1.2.11 refuses `turbo`; it takes `always-proceed`/`request-review`/`agent-decides`), warns on a stale value, and gains `clear-review-policy`; the SessionStart hook no longer defaults the policy to `turbo` (operator decision). `agy-doctor.sh --probe` names a spent plan quota instead of reporting "did nothing".
- The Stop hook also sends back a turn whose report is blocked on the operator without asking (open questions are re-asked every turn); links go in a file card before the question (SKILL.md §5).
- Operator questions go through the native question UI (SKILL.md §5): the Stop hook sends back a turn whose reply asks the operator a question in prose without calling `AskUserQuestion` (`hooks/_chat_question.py`; capped by `DEVLOOP_ASK_CAP`, off for lanes and with `DEVLOOP_NATIVE_ASK=0`). Controls in `tests/test_stop_gate.py` replay real captured turns (`tests/fixtures/transcripts/`).
- `goal.py`, `research.py`, `review.py`, `ship.py`, `triage.py` share one repo-root resolver, `scripts/repo_root.py`, instead of five copies. Outside a git work tree the scripts now exit 2 with one line instead of silently treating the current directory as the repository. `ship.py`, `triage.py` and `research.py template` take `--template-dir` (default: the shipped `assets/templates`). The implicit fallback to the target repo's `reference/templates` is gone, and a missing template is an error instead of a silent no-op in `ship.py`/`triage.py` (`tests/test_repo_root_helper.py`).
- `.devcontainer/Containerfile` is a byte-identical, test-gated mirror of MiOS's one dev image (context-independent: it shallow-clones MiOS when built here); `devcontainer.json` runs MiOS's lifecycle. The settings block carries only keys browser clients register (MiOS ADR-0024), fixing the Codespaces "not a registered configuration" error.
### Fixed
- `scripts/env/fetch-installer.sh`: the `agy` installer fetch decodes the CDN's unsolicited gzip and refuses a non-script payload (`tests/test_agy_installer_fetch.py`).
- `hooks/format.sh` parses `.sh` files with the interpreter their shebang names instead of always `sh -n` (`tests/test_format_hook.py`).
- `scripts/job.py`: the wrapper's TERM/INT traps now exit. A signal caught before `timeout` started wrote a 143 receipt and then ran the job for its whole budget, which made `test_job_receipt.py` flake about 1 run in 4 (`test_term_before_the_work_starts_stops_the_job`).
### Removed
- `.devcontainer/Dockerfile` and the Ubuntu variant `.devcontainer/ubuntu/`: superseded by MiOS's one image.

## [7.6.0]
### Added
- SCOPE staged review in `/review`; AGY session transport (`agy_host.sh --session`, `agy_session.py`, `agy_monitor.py`); loop translation-layer design (`references/translation-layer.md` + ADR-0001).
### Changed
- Lane dispatch rule re-keyed from 'headless' onto process lifetime; `git_lock.py` + stale `index.lock` sweep for multi-lane git contention.

_Releases before 7.6.0 predate this changelog._
