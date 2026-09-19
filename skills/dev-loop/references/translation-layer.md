# The loop translation layer — design

Companion to ADR `docs/decisions/0001-loop-translation-layer-*.md` (status: proposed). The ADR
carries the decision and the rejected alternatives; this file carries the design.

Everything marked **(measured)** was probed against the tools installed in this container. Version
stamps are in §10. Nothing here is inferred from a vendor blog.

---

## 1. The reframe

"Translate AGY's API to Claude Code's API" is unbuildable as stated, because **neither harness
serves an API** (measured):

| Harness | What it serves | What it consumes |
|---|---|---|
| Antigravity (`agy`, SDK) | nothing — no `/v1/chat/completions`, `/v1/embeddings`, `/v1/models`; the only `serve` verb in `agy --help` is `mic-serve` | OpenAI-compatible endpoints via `LocalOpenAIAgentConfig.base_url` ("any external OpenAI-compatible completions API"), MCP servers |
| Claude Code | nothing | Anthropic Messages API via `ANTHROPIC_BASE_URL`, MCP servers |

Both are clients. The component in the middle is therefore **a server to both harnesses and a
client to both CLIs** — the inversion is the whole design. It occupies seams that already exist
and invents no protocol.

### Seam inventory (all first-party, all measured)

| Seam | Harness | Direction | Used by this design |
|---|---|---|---|
| MCP stdio / streamable HTTP | both | harness calls out | **yes — primary surface** |
| `LocalOpenAIAgentConfig.base_url` | AGY | AGY calls out | **yes — the only way AGY consumes a backend** |
| `ANTHROPIC_BASE_URL` | Claude Code | Claude calls out | deferred (§6.3) — CCR/LiteLLM's job |
| `--input-format stream-json` / `--output-format stream-json` NDJSON over stdio | `agy` | **caller drives** | **yes — lane transport (P1)** |
| `claude -p --output-format stream-json` | Claude Code | **caller drives** | **yes — same shape** |
| plugin tree `.claude-plugin/plugin.json` | Claude Code | harness loads in | `xlate` target |
| `.agents/` customization tree, `agy plugin import` | AGY | harness loads in | `xlate` target (import is one-way and lossy) |
| `agy remote-control {start,status,stop}` | `agy` | caller drives a daemon | **no — out of scope, §8.4** |

---

## 2. Scope refusals — what this layer does NOT build

Three quarters of the naive scope is shipped, tested, and maintained by other people. Building it
again is duplication with worse coverage.

| Naive component | Already solved by | Verdict |
|---|---|---|
| Model-wire translation (Anthropic Messages ↔ OpenAI/Gemini) | Claude Code Router (MIT, 37k★); LiteLLM | **Do not build.** Documented, mature, and their open streaming tool-call bugs (litellm #39796, #17246, #20975) are exactly what a rewrite re-discovers. |
| "Claude Code delegates a task to `agy`" | ≥6 community plugins (`iicmaster/antigravity-plugins`, `yuting0624/antigravity-for-claude-code`, …) | **Do not build.** Fork one if delegation is what you want. |
| Agentic transport fidelity: streaming, permission prompts, diffs, terminals, session resume | ACP (Agent Client Protocol) — 40+ agents; Zed's Claude adapter Apache-2.0; `jiridanek/agy-acp` | **Adopt the lesson, defer the dependency** (§8.5, P6). |
| A2A / AGNTCY ACP / IBM ACP | — | **Wrong layer or absorbed.** A2A is cross-organisational networked delegation with Agent Cards and payments; semantically wrong for two local CLIs. The other two folded into A2A. |

**What nobody has built:** a translator for the *loop*. ACP models an editor driving one agent
turn by turn. It has no notion of a lane contract with exclusive `owned_paths`, a two-sided gate, a
negative control that must fail *for the planted reason*, an idempotence assertion, or a status
meaning "reported SUCCESS and changed nothing". That vocabulary is `SKILL.md` §6–§7's, and it is
exactly what must survive a harness crossing.

---

## 3. Components

### 3.1 `loopd` — the loop daemon (runtime)

One process. Serves three dialects of one loop; drives both CLIs as subprocesses.

### 3.2 `xlate` — the static format converter

`.claude-plugin/` ↔ AGY `.agents/` customization tree. Pure transform, no runtime. Google ships
`agy plugin import` (two importers over a `common.Stager`: `StageAgents, StageCommands, StageHooks,
StageMCPServers, StageSkills`) but it is **one-way, lossy, and has no import symbol for Claude's
`settings.json` permission model** (measured). There is no export verb. `xlate` closes the return
path and handles the permission gap the only safe way: **by refusing** (§5.3).

---

## 4. Process model

Constraints in tension: the Antigravity SDK is Python-only and its runtime ships as a **closed
compiled binary** inside six platform wheels (no sdist), with `max_subagent_depth` defaulting to
**1**. MiOS's standing directive is Rust static binaries.

Resolution:

- **`loopd` core drives CLIs, not SDKs.** No `google-antigravity` dependency, no
  `claude-agent-sdk` dependency. The NDJSON stdio channel gives the same caller-held session
  without pinning the layer to Python or to a closed wheel.
- **Language:** P0–P3 land as Python in this repo (its existing language, alongside
  `adapters.py`/`devloop_mcp.py`). The Rust-static-binary directive applies when/if `loopd` moves
  into MiOS `tools/native/`; the ports, the schema and the mapping table are the portable parts and
  the HTTP/stdio plumbing is the throwaway part. Stated plainly rather than pretended.
- **Lane execution:** one subprocess per lane, **stdin held open**:
  - AGY lane — `agy -p --input-format stream-json --output-format stream-json --json-schema <report.schema.json> --print-timeout 0`
  - Claude lane — `claude -p --output-format stream-json --json-schema <report.schema.json>`

  This replaces today's shell-out-and-die model in `adapters.py`. It is the root fix for the
  observed "manager reports SUCCESS while nothing merges": today `agy_host.sh` compensates with a
  prompt instruction (run `devloop.sh` synchronously in the foreground) because print mode answers
  once and exits, killing backgrounded children. A held session removes the reason for that
  instruction instead of restating it.
- **Concurrency:** one `loopd`, N lane subprocesses, **one shared credential** in the keyring —
  so the keyring must be up before fan-out or every lane re-auths and burns its budget hanging
  (`scripts/env/agy-keyring.sh`).

---

## 5. The four translations, and the one refusal

### 5.1 Envelope normalisation

Three real shapes, **zero shared field names** (measured):

```
agy --output-format json
  {conversation_id, status, response, num_turns, denied_actions[], …}

agy --output-format stream-json      # NDJSON: {"event":"<t>","<t>":{…}}; terminal line:
  {"event":"result","result":{conversation_id, status, response, error,
                              duration_seconds, num_turns,
                              usage:{input_tokens, output_tokens, thinking_tokens,
                                     cache_read_tokens, total_tokens}}}

claude -p --output-format json
  {result, num_turns, permission_denials[], …}
```

Canonical `loop.v1` envelope — one schema, OpenAI-shaped per the global directive:

```json
{
  "run_id": "…", "lane_id": "…", "harness": "antigravity|claude-code|…",
  "status": "delivered|refused|vacuous|gate_failed|control_invalid|errored|timed_out",
  "text": "…", "turns": 0, "denials": [], "usage": {}, "duration_s": 0.0, "error": null,
  "evidence": {"diff_bytes": 0, "positive": null, "negative": null}
}
```

| `loop.v1` | from AGY json | from AGY stream-json | from Claude json |
|---|---|---|---|
| `text` | `response` | `result.response` | `result` |
| `turns` | `num_turns` | `result.num_turns` | `num_turns` |
| `denials` | `denied_actions[]` | `result.denied_actions[]` | `permission_denials[]` |
| `usage` | *(absent)* | `result.usage` | *(harness-specific; normalise or omit)* |
| `duration_s` | *(absent — wall-clock from the caller)* | `result.duration_seconds` | *(caller)* |
| `error` | *(absent)* | `result.error` | *(absent)* |
| `status` | **not** `status` — see §5.2 | **not** `result.status` | **not** exit code |

Two things this table must never do: trust the harness's own `status` field, and trust exit 0.
`denied_actions` is **undocumented but real** (measured), which is why `adapters.py.find_envelope()`
locates the envelope by brace balance rather than `json.loads` on the whole stream.

### 5.2 Status vocabulary — representing "reported SUCCESS but did nothing"

The reason to have a middle at all. Both harnesses return exit 0 with an empty response over N
turns, and `{"status":"SUCCESS","response":"","num_turns":1,"denied_actions":[…]}` is a shape that
was observed live. Only a component that sees **both the envelope and the worktree** can tell the
difference. Neither harness can do that about itself; neither can a wire gateway.

| `loop.v1.status` | Decided from evidence, never from the harness's word |
|---|---|
| `delivered` | envelope ok **and** worktree diff non-empty **and** both controls ran |
| `refused` | `denials` non-empty — the harness declined work |
| `vacuous` | envelope claims success, `denials` empty, **diff empty** — the silent-failure case |
| `gate_failed` | positive control failed, **or** negative control passed (failed to fail), **or** failed for the wrong reason |
| `control_invalid` | negative control did not restore the tree, or the baseline was already broken — `SKILL.md` §6's *"a broken control does not weaken your proof; it inverts it"*; exit 2 today |
| `errored` | non-zero exit, or `error` set |
| `timed_out` | wall-clock exceeded. **Never** collapsed into success (§7 Timeout-as-Pass) |

`vacuous` is the point. Today `adapters.py denials` prints a warning; in `loop.v1` it is a
first-class terminal status the orchestrator must handle and that cannot be mistaken for
`delivered`.

### 5.3 Permission mapping — the layer must **refuse** to auto-translate

Measured asymmetry. AGY's permission grammar has exactly five live actions — `read_file`,
`write_file`, `command`, `url`, `mcp` (plus deprecated `unsandboxed`). Everything else
(`edit_file`, `list_dir`, `grep_search`, `run_command`, `invoke_subagent`, …) is rejected as
"unknown action" **into the log only**. `command(x)` prefix-matches **the first token only**.
`read_file(*)` is universal; `read_file(/repo/**)` is *accepted and matches nothing*. Claude Code
uses a different algebra entirely (`Bash(git:*)`, `Read`, `Write`, `Edit`, `Glob`, `Grep`, …).

There is no total function between them:

| Pair | Why it is not an equivalence |
|---|---|
| `command(git)` → `Bash(git:*)` | AGY's rule also matches `git-anything`; and `cd x && git push` is matched by `command(cd)`, **not** `command(git)`. Wider in one direction, blind in another. |
| `Bash(git:*)` → `command(git)` | Claude's rule does not grant `cd`. The working AGY equivalent needs `command(cd)` too — which grants **every** command after `&&`. |
| `Read` scoped to a path → `read_file(<path>)` | AGY has no path globbing. The honest translation of a scoped Claude read is the **universal** `read_file(*)`: a silent widening. |
| anything → `invoke_subagent` | Not an action name at all. Accepted into the log, enforced nowhere. |

**Design rule: the mapper is partial and fails closed.** `loopd` ships a declared, hand-audited
table with a verdict per pair — `exact | widens | narrows | none`. A lane whose requested grants map
to `widens` or `none` is **rejected at validate time with the offending pair named**, never
silently translated. Rationale: a wrong mapping does not crash. It hands an agent a capability the
operator refused, invisibly. That is the worst failure mode in the design and the only one where
refusing beats guessing.

One more measured trap the mapper must encode: `toolPermission` takes exactly
`always-proceed | request-review | strict`, and **an unrecognised value voids the entire settings
file** — silently discarding `permissions.allow`, `trustedWorkspaces` and
`allowNonWorkspaceAccess`. A mapper that emits a plausible-but-invalid value disables every grant
it just wrote. `xlate` must validate the enum against the binary's accepted set, not against a doc.

### 5.4 Subagent depth and fan-out asymmetry

| Context | Depth | Fan-out |
|---|---|---|
| Claude Code | nesting depth 3 (plugin-shipped agents) | 20 concurrent subagents |
| AGY interactive | `invoke_subagent`, `workspace: branch`, ≤ 10 | native |
| AGY headless `-p` | `invoke_subagent` **fails** (measured) | via `devloop.sh` dispatch |
| AGY Python SDK | `max_subagent_depth` default **1** | flat delegation |

`loopd` normalises by declaring `max_depth` in the lane contract and **refusing** a lane whose
declared depth exceeds what the target harness *and mode* can serve — rather than letting it
silently flatten. A headless AGY lane with `max_depth > 0` is rejected at validate, pointing at the
interactive path or at `devloop.sh` dispatch. This promotes `agy_host.sh`'s current mode-dependent
`$DISPATCH_RULE` from prompt text into a validated contract field, where it can be tested.

---

## 6. Interfaces

### 6.1 MCP — primary surface

Extends the nine tools `devloop_mcp.py` already serves (`validate_lanes`, `run_lanes`, `gate`,
`probe`, `tasks_next`, `task_set`, `ledger`, `report`, `scaffold`). Stateless-by-call stays; the
session handle is explicit:

| Tool | In | Out |
|---|---|---|
| `lane_open` | `{lane_path, worktree}` | `{session_id}` — starts a held NDJSON session |
| `lane_send` | `{session_id, message}` | `loop.v1` envelope for that turn |
| `lane_close` | `{session_id}` | final `loop.v1` envelope; prunes the worktree |
| `xlate` | `{src, src_format, dst_format, dry_run}` | `{written[], refusals[]}` |

Both harnesses consume MCP natively, so this surface needs no translation at all — which is why it
is primary.

### 6.2 OpenAI-compatible `/v1` — the surface AGY can consume as a backend

- `GET /v1/models` → one id per lane role: `dev-loop/orchestrator`, `dev-loop/lane-worker`,
  `dev-loop/auditor`, `dev-loop/researcher`, `dev-loop/triage`.
- `POST /v1/chat/completions` → runs a loop turn. Tool calls surface as OpenAI function calls from
  the existing `assets/openai-tools.json`. `stream: true` supported (SSE).
- AGY points `LocalOpenAIAgentConfig.base_url` here and a **lane appears to AGY as a model**. This
  is the only direction AGY natively supports, which is what makes the façade worth building at all.
- Auth: bearer token read from a 0600 file. **Never an env var** — Law 11 shape
  (`SECRETS-NEVER-IN-ENV`), and Law 10 forbids it in `install.env` regardless.

### 6.3 Anthropic Messages `/v1/messages` — deferred

The seam `ANTHROPIC_BASE_URL` occupies. Only needed for "Claude Code's own loop runs on a Gemini
model", which is Claude Code Router's and LiteLLM's job. Ship only if the operator prefers one
process over two, and gate it behind `[surfaces].messages` so `validate.sh` can assert it is absent
by default (a smuggled model gateway is scope creep with a known bug surface).

---

## 7. Worktree isolation is the server's, exclusively

`agy` 1.2.6 has **no worktree flag** — `--add-dir` adds a directory to the workspace, it does not
branch (measured). Claude Code has native `isolation: worktree`.

Therefore **`loopd` owns isolation for every lane in every harness**: it creates the worktree,
passes it as cwd / `--add-dir`, runs both controls in it, and prunes it. A harness's native
worktree support is an optimisation used only when the server is *not* already isolating — never a
second source of truth.

Rationale: two isolation owners means two answers to "where is this lane's diff", and the entire
`vacuous` detector (§5.2) depends on there being exactly one.

---

## 8. Deliberate non-adoptions

1. **`google-antigravity` SDK** — closed compiled runtime, no sdist, `max_subagent_depth` 1, pins
   the layer to Python. The NDJSON CLI channel gives the same caller-held session.
2. **`claude-agent-sdk`** — purpose-built for one vendor; hosting another vendor's agent is an open
   upstream issue. We drive the CLI.
3. **A2A / AGNTCY ACP / IBM ACP** — wrong layer, or absorbed into A2A.
4. **`agy remote-control`** — a real daemon (`start|status|stop`, measured) but undocumented flags,
   unknown failure mode, and it registers with a remote service: a privacy and ToS surface. Out of
   scope by default; explicit operator decision only.
5. **ACP as a foundation** — right *shape*, wrong *time*. `agy` has no native `--acp`
   (antigravity-cli issue #31, opened 2026-05-20, assigned, unanswered, no milestone); every
   adapter today needs a separate `agy_acp_server` binary with interactive OAuth that cannot be
   automated. Kept as P6, a swappable transport. The envelope, status vocabulary, permission mapper
   and worktree ownership are all transport-independent and survive the swap — which is why
   transport is the last thing this design commits to.

---

## 9. Phasing — each phase independently verifiable, two-sided

| Phase | Deliverable | Positive control | Negative control (must fail, by name) |
|---|---|---|---|
| **P0** | `loop.v1` JSON Schema + the AGY/Claude mapping table | recorded real envelopes (incl. the stream-json result line in §5.1) normalise correctly | a mutated field fails naming **that field**, not a generic parse error |
| **P1** | Held NDJSON sessions replace shell-out-and-die | a two-turn lane where turn 2 depends on turn 1's state completes | the same lane run through a single-shot adapter **must fail** |
| **P2** | `vacuous` wired to diff-emptiness | a lane that edits a file returns `delivered` | a lane whose worker is `true` returns `vacuous` — asserting `delivered` fails the suite |
| **P3** | Permission mapper, failing closed | a lane whose grants map `exact` validates | a fixture lane mapping `widens`/`none` is **rejected**, naming the pair; acceptance fails the suite |
| **P4** | `/v1` façade | an AGY lane configured via `LocalOpenAIAgentConfig` completes a turn through `loopd` | façade with no backing lane returns an error, not an empty 200 |
| **P5** | `xlate` | round-trip a plugin; structure preserved | the permission block is **refused**, not translated; a silent translation fails the suite |
| **P6** | *(optional)* ACP transport | same lane passes over ACP | envelope/status/permissions unchanged across transports |

Sequencing note: P0–P2 deliver the whole value of the middle (one vocabulary, silent-failure
detection) and depend on nothing external. P3 is the safety phase. P4 onward is reach.

---

## 10. Provenance

All version-stamped; probed in this container unless marked otherwise.

- `agy` **1.2.6** — `--help` surface, `--input-format`/`--output-format stream-json`,
  `--json-schema`, `--print-timeout 0`, `remote-control` subcommand, absence of any worktree flag,
  absence of a serve verb other than `mic-serve`; the stream-json terminal event shape; the
  permission grammar (5 live actions, first-token prefix match, no path globbing); the
  `toolPermission` enum and its file-voiding behaviour; `invoke_subagent` failing under `-p`;
  `denied_actions` in the envelope.
- `google-antigravity` PyPI **0.1.17**, Apache-2.0, `requires_python >=3.10`, six platform wheels,
  no sdist; `LocalOpenAIAgentConfig`; `max_subagent_depth` default 1. *(docs + package metadata)*
- Claude Code — plugin auto-discovery, declaration merge/replace semantics, depth 3 / 20
  concurrent subagents, `permission_denials` envelope key.
- MCP revision **2026-07-28** (the version `devloop_mcp.py` already negotiates).
- Prior art and licences: `research_notes/AGY Claude Code translation server/prior_art_and_protocols.md`.
- Round-1 notes: `research_notes/Native AGY and Claude Code patterns/` (6 files).

**Two upstream sources are contradicted by measurement.** antigravity-cli issue #31 and the pi-go
write-up both state `agy` has only three modes and offers no programmatic orchestration. The
installed binary has a documented bidirectional NDJSON session channel. Design against the binary.

---

## 11. Open questions for the operator

Carried forward, unanswered:

1. **`ratchet.md` prescribes `git reset --hard HEAD`** (v8 artifact port). That is on the
   confirm-before list and destroys uncommitted lane work. Proposal: park the diff as a patch per
   `SKILL.md` §11 instead. Confirm the substitution?
2. **`critic.py`'s maker-checker panel vs the existing `review` skill** — merge the panel into
   `review`, or keep them as separate stages? They overlap on DRY/KISS/SRP/security.

New, raised by this design:

3. **`agy remote-control`** — out of scope by default (§8.4). Confirm, or investigate?
4. **AGY auth has lapsed in this container** (`authentication failed or timed out` — measured
   today). Re-login needs your Google OAuth code through `scripts/env/agy-login.sh`. Nothing in
   this design is blocked by it; P1's probes are.
5. **Build vs adopt on transport** — this design takes ACP's lesson but not its dependency. Want
   `jiridanek/agy-acp` evaluated as an alternative lane transport at P6, or is the NDJSON channel
   sufficient?
