---
name: team
description: Launch full-teamwork multi-agent workflows where every harness participates - Claude Code, Antigravity/AGY, Codex, Gemini, Copilot, Cursor, OpenCode, and ANY OpenAI-compatible agent - coordinated through the dev-loop lane discipline and the loop-translation bridge. Distills the AGY teamwork protocol (orchestrator, explorer, worker, reviewer, challenger, auditor with binary veto, sentinel) into portable patterns: exclusive file ownership, reserved-file fences, BRIEFING/DISPATCH/progress/handoff artifacts, parent-conversation addressing, retry ladder, and succession. Use when work is wide enough for parallel agents or when the operator asks for a team, swarm, or cross-harness workflow.
argument-hint: "GOAL | lanes N | audit SCOPE"
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, WebSearch, WebFetch, Agent, SendMessage, TaskOutput
---

# Team: full cross-harness teamwork on one loop

`/dev-loop:team` runs §11's lane discipline with the AGY-derived role protocol on
top, so agents from *different* harnesses work one objective without clobbering
each other. Every lane keeps dev-loop's non-negotiables: DoD before code,
two-sided gates, explicit-path git, audited merges.

## 1. The wire: how agents talk (A2A over MCP + the bridge)

Two local transports, both loopback, no credentials ever forwarded:

- **MiOS-MCP** (`usr/libexec/mios/mios-mcp-server`, mcp SDK 2.1.1 line,
  protocol 2026-07-28): the shared tool surface - task store, gates, repos.
  Any harness that speaks MCP joins as a first-class worker.
- **The loop-translation bridge** (`devloop-bridge serve` on 127.0.0.1:8765):
  `POST /translate` with `source:"auto"` normalizes any harness's frames -
  AGY stream JSON, Claude print-mode JSON, OpenAI Responses/Codex items, and
  any OpenAI-compatible Chat Completions dialect (vLLM, llama.cpp, LM Studio,
  Ollama, OpenRouter, OpenWebUI, custom agents) - into ordered `loop.v1`
  events and Responses items, so one lane's transcript is readable evidence
  in every other harness. `POST /mcp` (or `devloop-bridge stdio`) exposes the
  same as the `translate_frames` MCP tool.

Bridge honesty rules that the team inherits, not re-invents: credential fields
are refused by name before any translation; a terminal `delivered` requires
two-sided gate evidence and otherwise demotes to `unverified`/`vacuous`;
missing terminals are `errored`. An agent's success word is never evidence.

## 2. Roles (distilled from the AGY teamwork protocol)

| Role | Owns | Hard rule |
|---|---|---|
| **Orchestrator** | Decomposition, dispatch, merge gates, reporting | NEVER writes source code or runs builds itself; dispatches everything |
| **Explorer** | Read-only investigation, briefings | Produces BRIEFING.md + handoff.md; no repo mutations |
| **Worker** | One lane's exclusive file set | No `git add`/commit/generators inside lanes; parks diffs with its report |
| **Reviewer** | Diffs of completed lanes | Audits against the lane's own DoD, both controls |
| **Challenger** | Adversarial edge cases | Attacks assumptions: casing, unicode, partial state, vacuous passes |
| **Auditor** | Final verdict per lane | **Binary veto** - an APPROVE is required to merge; one rejection kills the lane |
| **Sentinel** | Supervision, upstream watch | Receives orchestrator reports; owns escalation to the operator |

## 3. Lane artifacts (the AGY briefing protocol, portable)

Each agent gets `.agents/teamwork/<role>_<round>/` with:

- `BRIEFING.md` - mission, identity, roles, working dir, parent conversation
  ID, hard constraints, work items with status, current phase.
- `DISPATCH.md` (orchestrator→worker) - the exclusive file list, DoD, both
  controls, and the fence: which paths are RESERVED to other lanes.
- `progress.md` - the running log; the last block states the next action.
- `handoff.md` - written at limits/failure: state, parked diff path, what the
  successor must re-verify. Succession passes the parent conversation ID.

Inter-agent messages: small, structured, actionable - mission, lane id, the
one question or verdict, evidence path. Address by conversation/agent id, not
by name assumptions.

## 4. Coordination rules (field-tested, keep them)

1. **Shard by file, never by topic** - two agents "fixing the gates" corrupt
   each other; the DISPATCH file list is exclusive ownership.
2. **Reserved-file fences** - active integration lanes publish the paths they
   own; other workers READ them and file handoff requests, never edit.
3. **Retry ladder** - Retry → Replace worker → Skip (non-essential only) →
   Redistribute → Redesign. Auditor failure is a hard veto, not a retry.
4. **Fresh spawn per round** - handed-off subagents are retired; successors
   inherit handoff.md plus the parent id, nothing else.
5. **Auto-detect, don't assume** - on the bridge use `source:"auto"`; in
   audits verify seams against the real binary/docs (the recovered
   DESIGN-AUDIT findings: `artifactReviewPolicy`, not `toolPermission`;
   `agy remote-control serve`, not `start|status|stop`; claims labeled
   "measured" must carry the command that measured them).
6. **ACP is refuted for lanes** - NDJSON/stream dialects over the bridge are
   the transport; see `.devloop/findings/ACP-P6.md` before proposing an ACP
   rewrite.

## 5. Launch checklist

1. Read AGENTS.md, TASKS.md, ROADMAP; `git worktree list`; pick the base
   commit and record it.
2. One worktree + branch per lane (`git worktree add`), roles per §2.
3. Write DISPATCH.md per worker: exclusive files, DoD, both controls, fence.
4. Start the bridge once (`devloop-bridge serve`) if lanes span harnesses.
5. Merge gates: auditor APPROVE + two-sided controls + parked-diff audit for
   any lane that died (§11 rules for partial completion apply unchanged).
6. Report per §13 with per-lane evidence; prune worktrees after merge.
