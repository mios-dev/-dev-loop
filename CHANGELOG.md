# Changelog
All notable changes to this project are documented here. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning: SemVer.

## [Unreleased]
### Added
- `skills/dev-loop-web/`: web-only variant of the loop for scheduled out-of-loop agents (Gemini Spark), portable Agent Skills subset, no project values; offline stdlib scripts (`bytes_proof`, `digest`, `jsonl_check`, `oci_closure`, `schema_check`, `secret_scan`), each with `--self-test` and `--two-sided`.
- `install.sh` / `install.ps1` `gemini-spark` package target and `skill_package.py` (pack + gate); `validate.sh` gates the emitted zip; controls in `tests/test_dev_loop_web_package.py`.
### Changed
### Fixed
### Removed

## [7.6.0]
### Added
- SCOPE staged review in `/review`; AGY session transport (`agy_host.sh --session`, `agy_session.py`, `agy_monitor.py`); loop translation-layer design (`references/translation-layer.md` + ADR-0001).
### Changed
- Lane dispatch rule re-keyed from 'headless' onto process lifetime; `git_lock.py` + stale `index.lock` sweep for multi-lane git contention.

_Releases before 7.6.0 predate this changelog._
