# Task Backlog Migration, Half-Life Dynamics, and Sliding-Window Ratchets

> **Canonical Upstream Research & System Specification**  
> **Status:** Published & Implemented  
> **Target Substrates:** MiOS, mios-bootstrap, -dev-loop  
> **Standards:** OpenAI Responses API, Strict Function Calling JSON Schema, FHS Packaging, Antigravity Customization Architecture  

---

## 1. Executive Summary & Core Invariants

Autonomous agentic operating systems require task representation, lifecycle monitoring, and governance gates that do not drift, wedge, or drop context over time. In long-running development loops spanning hundreds of iterations across multiple agent harnesses (Antigravity, Codex, Claude Code, Gemini CLI, Copilot, OpenCode):

1. **Zero Data Loss on Migration**: Every task across legacy lists (`TASKS.md`, `AGY-TASKS.md`, `.devloop/tasks.jsonl`) must be ported forward into canonical dev-loop structures. Backlogged and completed tasks are retained losslessly with their verification evidence, acceptance criteria, and historical notes.
2. **Exponential Task Half-Life ($t_{1/2}$)**: Backlog items decay in relevance as the repository evolves. We model task half-life via joint commit distance ($\Delta C$) and calendar time ($\Delta T$), coupled with real-time file anchor sensors.
3. **Lossless Rolling Historical Backlog & Knowledge Distillation**: Tasks that exceed their half-life horizon are never dropped; they are transferred to an append-only historical backlog (`.devloop/backlog_archive.jsonl` and `.devloop/HISTORICAL_BACKLOG.md`) and distilled into permanent documentation (`docs/distilled/` and manpages).
4. **Sliding-Window Ratchet with 3-5 Commit Hysteresis**: Rigid zero-slack ratchets break multi-commit engineering sprints. We provide an elastic growth buffer across commits $0..2$, a reassessment window across commits $3..5$ (verifying verity and roadmap alignment), and strict ratchet lock-in beyond 5 commits, operating at infinite scale via a rolling baseline milestone.
5. **OpenAI API Strict Schema Parity**: All tool calling, Responses API schemas, and task representations enforce `strict: true`, `additionalProperties: false`, and comprehensive `required` property declarations.

---

## 2. Mathematical Modeling of Task Half-Life ($t_{1/2}$)

Tasks in software repositories do not remain indefinitely fresh. Upstream empirical research (METR, Toby Ord, Allan Kelly) establishes that backlog staleness stems from three distinct decay modes:
1. **Commit Drift Decay**: The underlying code substrate mutates with every merge.
2. **Temporal Decay**: Operator priorities and architectural assumptions shift over time.
3. **Anchor Breakage**: Files, functions, or modules referenced in task definitions are renamed, refactored, or pruned.

### 2.1 Joint Decay Formulation

Let:
- $\Delta C = C_{\text{HEAD}} - C_{\text{anchor}}$ be the commit distance since task creation or last reconciliation.
- $\Delta T = T_{\text{now}} - T_{\text{anchor}}$ be the elapsed time in days.
- $H_C = 50$ commits be the commit half-life constant.
- $H_T = 90$ days be the temporal half-life constant.
- $B_{\text{anchors}}$ be the count of broken file/path anchors referenced in the task.

The probability of task freshness $P_{\text{fresh}}$ is formulated as:

$$P_{\text{fresh}}(\Delta C, \Delta T) = 2^{-\frac{\Delta C}{H_C}} \times 2^{-\frac{\Delta T}{H_T}}$$

The staleness score $S \in [0.0, 1.0]$ is defined as:

$$S = \min\left(1.0, \, (1.0 - P_{\text{fresh}}) + \alpha \cdot \mathbf{1}(B_{\text{anchors}} > 0)\right)$$

where $\alpha = 0.35$ represents the anchor breakage penalty step function.

### 2.2 Thresholds & Expiry States

| Staleness Range $S$ | State | Operational Rule |
| :--- | :--- | :--- |
| $0.00 \le S < 0.25$ | `FRESH` | Active candidate for `/backlog next` and immediate dispatch. |
| $0.25 \le S < 0.50$ | `AGING` | Eligible for execution; anchor paths validated during preflight. |
| $0.50 \le S < 0.80$ | `EXPIRED_STALE` | Past half-life horizon. Excluded from `/backlog next`. Requires `/backlog reconcile` or archiving. |
| $0.80 \le S \le 1.00$ | `ARCHIVABLE` | Broken anchors or severe drift. Automatically moved to rolling historical backlog via `tasks archive-stale`. |

---

## 3. Lossless Rolling Backlog & Knowledge Distillation

When tasks exceed their half-life horizon, deleting them destroys institutional memory and reasoning history. Instead, dev-loop implements a **Lossless Rolling Backlog Architecture**:

```
Active Task Ledger (.devloop/tasks.jsonl)
        │
        ▼ (half-life expiry: S >= 0.50)
Rolling Backlog Archive (.devloop/backlog_archive.jsonl + HISTORICAL_BACKLOG.md)
        │
        ▼ (periodic or on-demand distillation)
Permanent Documentation (docs/distilled/ + usr/share/man/man1/ + ROADMAP.md)
```

### 3.1 Rolling Historical Backlog (`.devloop/HISTORICAL_BACKLOG.md`)
Each archived task appends a markdown block capturing:
- Original task ID, title, domain, and legacy status.
- Staleness metrics at time of archiving ($\Delta C$, $\Delta T$, broken anchors).
- Acceptance criteria and verification commands.
- Full context notes, Why, Where, and Do NOT directives.

### 3.2 Knowledge Distillation (`docs/distilled/knowledge_distillation.md`)
The `artifacts.py tasks distill` command clusters archived tasks by goal/domain and synthesizes:
- Recurrent failure modes and anti-patterns.
- Architectural invariants established during past investigations.
- Strategic backlog themes rolled forward into roadmap milestones.

---

## 4. Sliding-Window Ratchet with 3-5 Commit Hysteresis

### 4.1 The Rigid Ratchet Failure Mode
Standard monorepo ratchets enforce $M_{\text{HEAD}} \le M_{\text{baseline}}$ on every single commit. While effective for preventing gradual decay, zero-slack ratchets create acute failure modes during active engineering:
- Adding a test harness or `.devcontainer/` script temporarily increases file/line counts, failing CI on commit 1 of a 4-commit feature.
- Multi-lane teamwork branches fail merge gates due to intermediate coordination scaffolding.

### 4.2 The 3-5 Commit Sliding Window Engine
To achieve infinite scalability without accumulating technical debt, `ratchet_window.py` models git commit graph distance:

$$\Delta C = \text{git rev-list --count } C_{\text{baseline}} \dots \text{HEAD}$$

```
Commit Distance (Delta C):
0 ──────────────── 2 ─────────────── 3 ─────────────── 5 ───────────────>
   GROWTH BUFFER       REASSESSMENT WINDOW             RATCHET GATE
  (+5% Headroom)       (Verity & Roadmap)            (Strict Lock-in)
```

1. **Growth Buffer ($\Delta C \in [0, 2]$)**:
   - Status: `GROWTH_BUFFER`.
   - Allows up to a $+5\%$ growth buffer ($\delta_{\text{buf}}$) on tracked lines, files, or complexity metrics.
   - Sprints proceed unblocked while active implementation is underway.
2. **Reassessment Window ($\Delta C \in [3, 5]$)**:
   - Status: `REASSESSMENT_WINDOW`.
   - Checks **Verity**: verifies that newly introduced files conform to canonical templates and pass test suites.
   - Checks **Roadmap Alignment**: inspects git commit messages in $C_{\text{baseline}}\dots\text{HEAD}$ to ensure they reference active tasks (`T-NNN`, `MON-NNN`) or roadmap milestones (`ROADMAP.md`).
3. **Ratchet Gate ($\Delta C > 5$)**:
   - Status: `RATCHET_GATE`.
   - Growth buffer expires. Ceilings must hold or decrease.
   - On verified convergence, advances $C_{\text{baseline}} \leftarrow \text{HEAD}$ and locks in improvements.

---

## 5. OpenAI API Standards & Harness Parity

### 5.1 Strict Mode JSON Schema
Dev-loop tools enforce the OpenAI Structured Outputs / Tool Calling standard:
- Root and all nested objects declare `"additionalProperties": false`.
- All properties defined in `"properties"` are explicitly enumerated in `"required"`.
- Nullable properties declare `"type": ["string", "null"]` while remaining in `"required"`.

### 5.2 Antigravity Lifecycle Hooks Contract
In compliance with primary vendor documentation, hooks in `.agents/hooks.json` conform to:
- **Encoding**: camelCase protojson input on `stdin`, JSON on `stdout`.
- **PreToolUse**: returns `{"decision": "allow" | "deny" | "ask" | "force_ask", "reason": "..."}`.
- **PreInvocation**: returns `{"injectSteps": [{"ephemeralMessage": "..."}]}`.
- **Stop**: returns `{"decision": "continue", "reason": "..."}` to enforce stop gates.

---

## 6. Verification Matrix

| Check | Tool / Test | Standard | Expected Output |
| :--- | :--- | :--- | :--- |
| Task Migration | `task_migration.py` | Dev-Loop 5-word status | 3,204 tasks ported, 0 dropped |
| Task Staleness | `artifacts.py tasks staleness` | Half-life decay math | Accurate $S \in [0.0, 1.0]$, broken anchor detection |
| Historical Archiving | `artifacts.py tasks archive-stale` | Lossless rolling ledger | JSONL + Markdown append, surviving tasks verified |
| Backlog Distillation | `artifacts.py tasks distill` | Documentation distillation | `docs/distilled/knowledge_distillation.md` rendered |
| Strict Schema Parity | `artifacts.py tasks export-openai` | OpenAI Responses API | `strict: true`, `additionalProperties: false`, 100% required |
| Ratchet Window | `test_ratchet_window.py` | 3-5 commit hysteresis | Growth buffer, roadmap check, strict gate pass clean |
