# Project: -dev-loop Test Suite Refactor, PR #22 Rebase, and Multi-Repo Gate Parity

## Architecture
- **Core Orchestration & Harness**: `skills/dev-loop/scripts/` (`job.py`, `devloop_serverd.py`, `agy_host.sh`, `agy_session.py`, `adapters.py`, `claude_lane.py`, `skill_package.py`).
- **Test Framework**: `tests/` containing 48 test suites across unit, integration, adversarial, and gate verification.
- **Cross-Repo System Boundaries**:
  - `c:\-dev-loop`: Harness, test doubles, session lifecycle, dev-loop scripts.
  - `c:\MiOS`: 401 registered CI suites (`tools/ci-suites.py --check`), 6 standing Rust gates (`mios-gate.exe`), projection sync (`tools/sync-generated.sh`).
  - `c:\mios-micro`: Resident miniature neural layer (12 unit tests across dataset, eval, package).
  - `c:\mios-bootstrap`: Installer, autounattend presets, profile templates, shell scripts.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Portable System Information | Replace `os.uname().nodename` with `platform.node()` across scripts and test suites | M1 | ORIGINAL_REQUEST §R1.1 |
| 2 | Guarded POSIX Modules | Graceful degradation for `pwd` (`try/except ImportError`) in user detection | M1 | ORIGINAL_REQUEST §R1.1 |
| 3 | Portable Process Group & Signal Termination | Replace `os.killpg`/`signal.SIGKILL` with cross-platform termination | M1 | ORIGINAL_REQUEST §R1.1 |
| 4 | Deterministic Test Doubles & CLI Mocks | Replace extensionless fake `agy`/`claude` with `.cmd` wrappers, `os.pathsep`, and strict execution bounds | M1 | ORIGINAL_REQUEST §R1.2, §R1.3 |
| 5 | Shell Adapter Portability | Prefer POSIX shell (`sh`) when available on Windows in `adapters.py` to support POSIX syntax | M1 | ORIGINAL_REQUEST §R1.2 |
| 6 | CRLF Normalization & Cleanups | Fix CRLF frontmatter parsing and replace `rm -rf` with `shutil.rmtree` | M1 | ORIGINAL_REQUEST §R1.2 |
| 7 | PR #22 Clean Rebase | Rebase PR #22 branch cleanly onto `origin/main` (`2429f7a`), dropping merge commits | M2 | ORIGINAL_REQUEST §R2.1 |
| 8 | `--conversation ID` Resume Mechanics | Forward `--conversation <id>` in `session_argv` and replace `/teamwork-preview` with resume note | M2 | ORIGINAL_REQUEST §R2.3 |
| 9 | PR #22 Two-Sided Verification | Verify positive & negative controls across all 4 modified files | M2 | ORIGINAL_REQUEST §R2.2 |
| 10| 48 Test Suites Clean Execution | Ensure all 48 test suites in `-dev-loop/tests` execute in <10s each and exit 0 | M3 | ORIGINAL_REQUEST §R3.1 |
| 11| Multi-Repo Standing Gates Parity | Confirm `c:\MiOS` (401 suites), `c:\mios-micro` (12 tests), `c:\mios-bootstrap` pass clean | M3 | ORIGINAL_REQUEST §R3.2 |
| 12| Verified PR Branch Ready for Review | Push rebased branch and prepare PR for operator review | M3 | ORIGINAL_REQUEST §R3.3 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Cross-Platform Test Refactor | Fix `os.uname`, `pwd`, `os.killpg`, fake CLI mocks, PATH separators, shell routing | none | IN_PROGRESS |
| M2 | PR #22 Rebase & Resume Verification | Rebase onto 2429f7a, verify `--conversation ID` prompt omission, two-sided controls | M1 | PLANNED |
| M3 | Multi-Repo Parity & PR Finalization | Run all 48 tests, check MiOS/micro/bootstrap gates, prepare PR for operator review | M1, M2 | PLANNED |
| E2E | E2E Testing Suite | Requirements-driven 4-tier E2E testing harness for dev-loop & multi-repo parity | none | IN_PROGRESS |

## Interface Contracts
### Test Double Contract (`agy`, `claude`)
- Mock binaries MUST generate both extensionless and `.cmd` variants on Windows (`fake.cmd`).
- `PATH` modifications MUST use `os.pathsep` (`;` on Windows, `:` on POSIX).
- Mock scripts MUST execute deterministically without network access, completing within 0.1s.
- `subprocess.Popen` in callers MUST resolve via `shutil.which` or explicit binary arguments to prevent falling through to host-installed binaries.

### Session Resume Contract (`agy_host.sh` ↔ `agy_session.py`)
- When `AGY_HOST_CONVERSATION` is provided:
  - `agy_host.sh` writes a resume note and strictly omits `/teamwork-preview` and initial planning prompts.
  - `session_argv` receives `conversation="<id>"` and appends `["--conversation", "<id>"]` before `-p=`.
- When `AGY_HOST_CONVERSATION` is empty:
  - Normal kickoff prompt and `/teamwork-preview` are written.
  - `--conversation` is omitted from `session_argv`.

## Code Layout
- `skills/dev-loop/scripts/job.py`: Host identification (`platform.node()`), process sessions.
- `skills/dev-loop/scripts/devloop_serverd.py`: Host identification (`platform.node()`).
- `skills/dev-loop/scripts/adapters.py`: Shell selection and command routing.
- `skills/dev-loop/scripts/claude_lane.py`: Process termination, mock execution.
- `skills/dev-loop/scripts/skill_package.py`: Frontmatter parsing.
- `skills/dev-loop/scripts/agy_host.sh`: Session prompt file writing, resume note handling.
- `skills/dev-loop/scripts/agy_session.py`: CLI arguments and `session_argv`.
- `tests/`: 48 test suites across all components.
