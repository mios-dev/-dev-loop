# Upstream patterns — multi-harness, multi-agent "dev-loop-like" systems

Survey as of 2026-09-18. Sources: web research (cited inline), the official
Agent Skills spec (agentskills.io), harness vendor docs, and the three
permissively-licensed projects vendored (docs-only) under `third_party/`
(ccswarm MIT, awesome-harness-engineering CC0, baton MIT — pinned SHAs in
`third_party/README.md`). Everything here is data for judgment, not law:
AGENTS.md and this skill's gates win on conflict.

## Patterns the ecosystem has converged on (and where this skill stands)

1. **Orchestrator–worker beats peer-to-peer as the first topology.** The
   manager holds user contract and task-level state; workers get narrow briefs
   and isolated contexts and return only final outputs plus artifact refs
   (Modern Agent Harness Blueprint 2026; ccswarm's master-orchestrator +
   specialist agents). *This skill:* §11 L0/L1/L2 — already aligned. Lane
   prompts stay narrow; reports are the only thing a host consumes.

2. **State on disk, context resets, structured handoffs.** The Ralph loop
   re-injects the goal into a fresh context each iteration and reads all state
   from the filesystem; harness engineering adds phase gates and handoff
   artifacts so work stays coherent across context windows (Addy Osmani,
   "Agent Harness Engineering"; NxCode/Augment guides). *This skill:*
   `.devloop/LEDGER.md`, `tasks.jsonl`, `devloop_report` — aligned; the ledger
   IS the handoff artifact.

3. **Worktree isolation per worker is the standard fence.** ccswarm, baton,
   Helmor (Apache-2.0), Sandcastle (MIT) all isolate each agent in a git
   worktree or sandbox and merge back through review gates. *This skill:*
   §11 worktree laws — aligned; our addition is the **two-sided gate run by
   the host** (positive + negative control), which none of the surveyed
   projects enforce mechanically. Keep it: it is this skill's differentiator.

4. **Event/issue-driven loops are the growing entry point.** baton polls
   GitHub Issues and turns each into an isolated worktree run; enterprise
   variants are event-driven (arXiv 2606.20058). *This skill:* lanes.json is
   the unit; an issue→lanes.json adapter is a natural, small future addition.

5. **Phase-gated single agents with human checkpoints outperform free-form
   swarms in production.** Plan–Execute–Verify with rigid gates and narrow
   tool access is what teams actually ship (Augment/NxCode 2026 guides;
   Google's June-2026 A2A production pattern routes failures to manual
   review). *This skill:* §1 lifecycle + §5 operator protocol — aligned; keep
   subagent counts low and gates rigid by default.

6. **Deterministic control planes around stochastic agents.** A2A-style
   shared session state, fail-safe routing, deterministic dispatch (arXiv
   2606.26924). *This skill:* the reference orchestrators are exactly that
   control plane; the 2026-09 live e2e reinforced it — determinism must
   extend to the manager's own dispatch (verbatim foreground command, scoped
   permission rules), because print-mode managers die with their children.

## Live-verified lessons folded back into this skill (2026-09-18)

From the mixed-lane e2e (`tests/e2e-mixed-lanes/`, AGY manager + AGY/Claude
lanes, all verified against git ground truth, never a manager's self-report):

- A headless print-mode manager that backgrounds the orchestrator reports
  SUCCESS while its exit kills every child (fixed: foreground-only dispatch in
  the manager prompt).
- Headless permission auto-denials can surface as `status: SUCCESS` with an
  empty response (`denied_actions` in the agy envelope; `permission_denials`
  in Claude's). Normalize downgrades both to `partial`.
- Scoped allowlists must match the model's habits: prefix rules match the
  first token only, and models prefix with `cd … &&`.
- Negative controls restore by copy-back; `git checkout --` restores from the
  index and destroys uncommitted lane work. The gate parks the pre-control
  diff first.

## Future patterns to track

- **Workflows → skills convergence** (Antigravity retires workflows
  2026-11-01; `/name` resolves from skills dirs). Shims are bridges only.
- **Agent Skills spec stewardship** under the Agentic AI Foundation: unknown
  frontmatter keys are ignored by conformant runtimes — expect richer
  optional metadata rather than new required keys.
- **A2A / cross-vendor session state** for lane-to-lane interface sync
  (today: `contracts.py` file exchange; A2A could replace polling).
- **Issue/event-driven lane generation** (baton pattern) on top of
  `lanes.json`.

Sources: [Modern Agent Harness Blueprint 2026](https://gist.github.com/amazingvince/52158d00fb8b3ba1b8476bc62bb562e3),
[Agent Harness Engineering — Addy Osmani](https://addyosmani.com/blog/agent-harness-engineering/),
[awesome-harness-engineering](https://github.com/ai-boost/awesome-harness-engineering),
[ccswarm](https://github.com/nwiizo/ccswarm), [baton](https://github.com/mraza007/baton),
[Augment: Harness Engineering](https://www.augmentcode.com/guides/harness-engineering-ai-coding-agents),
[Open-source agent orchestrators 2026](https://www.augmentcode.com/tools/open-source-agent-orchestrators),
[arXiv 2606.20058](https://arxiv.org/pdf/2606.20058), [arXiv 2606.26924](https://arxiv.org/pdf/2606.26924),
[Agent Skills spec](https://agentskills.io/home).
