---
status: proposed
date: 2026-09-20
decision-makers: [operator, dev-loop-architect]
consulted:
  - "Fedora Linux Packit, Testing Farm & tmt architecture (https://packit.dev, https://docs.testing-farm.io, https://tmt.readthedocs.io)"
  - "Fedora Bootc / Image Mode Testing patterns (Testing Farm MVP Image Mode)"
  - "OpenAI Autonomous Agent & Tool-Calling Standards (Model-Spec, strict schema validation)"
  - "MiOS Architectural Laws (USR-OVER-ETC, NO-MKDIR-IN-VAR, UNIFIED-AI-REDIRECTS, TARGET-LANGUAGES)"
  - "MiOS Legibility Ratchet (tools/drift-checks.py legibility-ratchet)"
informed: []
---

# Autonomous MiOS CI Sanitized Symbiosis: Upstream Driver, Downstream OS Substrate, and Fedora-Style Gating

## Context and Problem Statement

MiOS is an immutable, bootc/OCI-shaped Fedora workstation and self-replicating agentic AI OS. It enforces strict Architectural Laws and precise legibility ratchets (`max_tracked_files = 3071`, `max_tracked_mb = 204`) to ensure the entire OS remains minimal, reproducible, and verifiable. `-dev-loop` is a multi-harness autonomous engineering loop, verification engine, and worker orchestrator supporting Claude Code, Antigravity, Codex, and OpenAI-compatible runtimes.

Historically, ad-hoc execution led to workspace contamination: bundles, raw checkouts of `-dev-loop`, and test suites were placed directly into the `MiOS` tree. This inflated tracked repository sizes beyond ratchet ceilings, created circular coupling, and obscured ownership boundaries.

In the context of developing and maintaining MiOS autonomously, facing the hazard of repository contamination and image bloat, we decided to adopt a **sanitized, reciprocal symbiosis architecture** modeled after upstream **Fedora Linux (Packit + Testing Farm / tmt + Greenwave/Bodhi gating)** and OpenAI-compatible agentic workflows.

## Decision Drivers

1. **Absolute Repository Sanitization**: Zero cross-contamination. `MiOS` must never track `-dev-loop` code, test suites, or bundles. `-dev-loop` must never track `MiOS` system overlays, Containerfiles, or binaries.
2. **Fedora Upstream CI Model**: Strict separation of concerns between upstream automation/orchestration (`Packit` / `tmt` / `-dev-loop`) and the downstream distribution/OS image compose substrate (`Fedora` / `bootc` / `MiOS`).
3. **Reciprocal Symbiosis (Mutual Development)**:
   - `-dev-loop` drives `MiOS`: Orchestrates isolated worktree lanes, executes two-sided controls (`adapters.py gate`), enforces standing gates, logs receipts to `.devloop/LEDGER.md`, and safely merges verified tasks.
   - `MiOS` drives `-dev-loop`: Provides the real-world, high-consequence fitness functions (72 automation phases, 270 libexec verbs, strict FHS overlay rules, byte/file ratchets) that expose edge cases and drive continuous hardening of `-dev-loop`'s concurrency, locking, and adapters.
4. **Two-Sided Verification & Lossless Proofs**: Every autonomous task requires both a positive control (must pass) and a negative control (planted defect must fail naming the plant). No task is marked `done` without cryptographic commit evidence and verifiable test output.
5. **Ratchet Compliance & Task Half-Life**: Active sprint tasks remain bounded (20–50 tasks in `.devloop/tasks.jsonl`) to preserve the `tracked_mb = 204` ceiling in `MiOS`. Stale or completed tasks are folded into `.devloop/backlog_archive.jsonl` and `.devloop/HISTORICAL_BACKLOG.md` (gitignored in MiOS, fully tracked in `-dev-loop`), and evaluated for recycling every 25–50 commits.

## Considered Options

1. **Monorepo / In-Tree Vendoring (`-dev-loop` vendored inside `MiOS`)**:
   - *Rejected*: Instantly breaches the MiOS legibility ratchet (`max_tracked_files = 3071`, `max_tracked_mb = 204`). Bakes developer test harnesses into the production bootc immutable image, violating FHS cleanliness and the single-responsibility principle.
2. **Decoupled Repositories with Ad-Hoc Manual Promotion**:
   - *Rejected*: Lacks autonomous driving. Tasks desynchronize, gates are bypassed, verification is claimed in prose rather than proven on disk, and errors are not fed back into tooling improvements.
3. **Sanitized Reciprocal Symbiosis (The Fedora Linux Upstream CI Model)**:
   - *Chosen*: Independent git repositories in a unified multi-root devcontainer workspace (`/workspaces/MiOS`, `/workspaces/mios-bootstrap`, `/workspaces/-dev-loop`). Standardized file-based interfaces (`.devloop/tasks.jsonl`, `.devloop/LEDGER.md`, standing gates). `-dev-loop` acts as external driver (Packit/tmt runner) and gatekeeper (Bodhi/Greenwave) executing over isolated git worktrees.

## Decision Outcome

Chosen option: **Option 3: Sanitized Reciprocal Symbiosis**.

### Architectural Topology

```
┌────────────────────────────────────────────────────────────────────────┐
│                        MiOS Multi-Repo Workspace                       │
│                                                                        │
│   ┌───────────────────────────┐      ┌──────────────────────────────┐  │
│   │         MiOS.git          │      │          -dev-loop           │  │
│   │   (Downstream OS Substrate│      │  (Upstream CI/Task Driver)   │  │
│   │    & bootc Containerfile) │      │                              │  │
│   ├───────────────────────────┤      ├──────────────────────────────┤  │
│   │ • FHS System Overlay      │      │ • adapters.py / devloop.sh   │  │
│   │ • 72 Automation Phases    │      │ • artifacts.py / tasks       │  │
│   │ • Legibility Ratchets     │      │ • Multi-Harness Adapters     │  │
│   │ • Standing Gates          │      │ • 219+ Unit / E2E Tests      │  │
│   │ • .devloop/tasks.jsonl    │◄─────┼── Drives tasks & worktrees   │  │
│   │ • .devloop/LEDGER.md      │◄─────┼── Writes receipts & proof    │  │
│   └─────────────┬─────────────┘      └──────────────▲───────────────┘  │
│                 │                                   │                  │
│                 └────── Stresses & Hardens ─────────┘                  │
│                        (Ratchet drift, concurrency,                    │
│                         lock contention, memoization)                  │
└────────────────────────────────────────────────────────────────────────┘
```

### The Autonomous Fedora-Style Workflow

1. **Discovery & Task Allocation (`Packit` Trigger Analog)**:
   `-dev-loop` queries `artifacts.py tasks next --root /workspaces/MiOS` to identify unblocked tasks whose dependencies are satisfied.
2. **Worktree Lane Isolation (`Testing Farm` Disposable Environment)**:
   A dedicated git worktree is provisioned (`git worktree add -b lane/<task_id> .devloop/wt/<task_id>`). All edits are strictly bounded to `owned_paths`.
3. **Two-Sided Verification Gate (`tmt` Test Plan)**:
   Autonomous execution runs `adapters.py gate`:
   - Positive control: The new feature or bug fix must pass tests.
   - Negative control: A planted mutation or defect must fail and explicitly name the expected plant signature.
   - Tree restore: Tree is restored to pristine state before proceeding.
4. **Standing Gate Verification (`Greenwave` / `Bodhi` Gating)**:
   `-dev-loop` invokes `MiOS` standing gates:
   - `python3 tools/drift-checks.py legibility-ratchet`
   - `python3 tools/check-tasks.py status-parity`
   - `python3 tools/check-tasks.py schema`
   - `bootc container lint` (when Containerfile or system units change)
5. **Receipt Logging & Safe Merge (`ship.py`)**:
   Once all gates return exit 0, `adapters.py ledger` records a receipt to `.devloop/LEDGER.md`, stages explicit paths, and merges `--no-ff` into `main`. The task state in `.devloop/tasks.jsonl` is updated to `done` with commit evidence.
6. **Task Half-Life, Folding, and Recycling**:
   - `MiOS` `.devloop/tasks.jsonl` contains active sprint tasks (~26 tasks, ~18 KB).
   - Inactive, stale, or completed tasks exceeding their half-life are folded into `backlog_archive.jsonl` and `HISTORICAL_BACKLOG.md` (gitignored in `MiOS`, tracked in `-dev-loop`).
   - Every 25–50 commits, `artifacts.py recycle` evaluates archived tasks against the current codebase state.

## Confirmation and Compliance

1. **Sanitization Gate**:
   - `git -C /workspaces/MiOS ls-files | grep dev-loop` must return 0 hits.
   - `git -C /home/mios-dev/.dev-loop ls-files | grep mios` must return 0 hits (except documentation references).
2. **Standing Gate Invariant**:
   - `python3 tools/drift-checks.py legibility-ratchet` in `MiOS` must hold at or below `tracked_files = 3071` and `tracked_mb = 204`.
3. **Test Suite Invariant**:
   - `python3 -m unittest discover -s tests` in `-dev-loop` must pass 100% without importing or accessing internal `MiOS` runtime state.

## Consequences

- **Good**:
  - Clean separation: `MiOS` remains a pure, unpolluted bootc OS deliverable.
  - `-dev-loop` operates as a universal, reusable agentic CI tool that can be applied to any codebase.
  - Development is 100% auditable with cryptographic commit receipts and two-sided verification.
  - Zero disk/byte ratchet violations in `MiOS`.
- **Bad**:
  - Developers and agents must remember to run commands with `--root /workspaces/MiOS` when invoking `-dev-loop` tools from outside the target repository.

## More Information

- [ADR 0001: Loop translation layer](0001-loop-translation-layer-serve-both-harnesses-translate-the-lo.md)
- [MiOS Architectural Laws](file:///workspaces/MiOS/usr/share/doc/mios/adr/)
- [Fedora Packit Documentation](https://packit.dev/docs/)
- [Fedora Testing Farm Documentation](https://docs.testing-farm.io/)
- [tmt Documentation](https://tmt.readthedocs.io/)
