# Changelog
All notable changes to this project are documented here. Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versioning: SemVer.

## [Unreleased]
### Added
### Changed
### Fixed
### Removed

## [7.6.0]
### Added
- SCOPE staged review in `/review`; AGY session transport (`agy_host.sh --session`, `agy_session.py`, `agy_monitor.py`); loop translation-layer design (`references/translation-layer.md` + ADR-0001).
### Changed
- Lane dispatch rule re-keyed from 'headless' onto process lifetime; `git_lock.py` + stale `index.lock` sweep for multi-lane git contention.

_Releases before 7.6.0 predate this changelog._
