# E2E Test Infra: -dev-loop Cross-Platform & PR #22 Parity

## Test Philosophy
- Opaque-box, requirement-driven. Derives from ORIGINAL_REQUEST.md.
- Methodology: Category-Partition + BVA + Pairwise + Workload Testing.
- Validates all 12 inventoried features across R1, R2, and R3.

## Feature Inventory
| # | Feature | Source | Tier 1 | Tier 2 | Tier 3 | Tier 4 |
|---|---------|--------|:------:|:------:|:------:|:------:|
| 1 | Portable System Information | ORIGINAL_REQUEST §R1.1 | 5 | 5 | ✓ | ✓ |
| 2 | Guarded POSIX Modules | ORIGINAL_REQUEST §R1.1 | 5 | 5 | ✓ | ✓ |
| 3 | Portable Process Termination | ORIGINAL_REQUEST §R1.1 | 5 | 5 | ✓ | ✓ |
| 4 | Deterministic Test Doubles | ORIGINAL_REQUEST §R1.2 | 5 | 5 | ✓ | ✓ |
| 5 | Shell Adapter Portability | ORIGINAL_REQUEST §R1.2 | 5 | 5 | ✓ | ✓ |
| 6 | CRLF Normalization & Cleanups | ORIGINAL_REQUEST §R1.2 | 5 | 5 | ✓ | ✓ |
| 7 | PR #22 Clean Rebase | ORIGINAL_REQUEST §R2.1 | 5 | 5 | ✓ | ✓ |
| 8 | `--conversation ID` Resume | ORIGINAL_REQUEST §R2.3 | 5 | 5 | ✓ | ✓ |
| 9 | PR #22 Two-Sided Controls | ORIGINAL_REQUEST §R2.2 | 5 | 5 | ✓ | ✓ |
| 10| 48 Test Suites Pass | ORIGINAL_REQUEST §R3.1 | 5 | 5 | ✓ | ✓ |
| 11| Multi-Repo Standing Gates | ORIGINAL_REQUEST §R3.2 | 5 | 5 | ✓ | ✓ |
| 12| Verified PR Branch | ORIGINAL_REQUEST §R3.3 | 5 | 5 | ✓ | ✓ |

## Test Architecture
- Test runner: `python tests/run_all_suites.py` and multi-repo verification harness.
- Verification mechanism: Exit code 0, standard JSON report, assertion validation.
- Output: `TEST_READY.md` upon completion.
