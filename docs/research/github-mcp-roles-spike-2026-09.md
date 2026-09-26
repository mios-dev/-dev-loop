# SPIKE: the GitHub MCP server behind the -dev-loop bridge, for the monitor and manager roles

- Status: proposed. This is a design only. No code was written, and every repo was only read (no git writes).
- Date: 2026-09-26
- Baselines (local HEADs, read-only):
  - MiOS `b448f03ae`
  - -dev-loop `bf010e4`
  - mios-bootstrap `37584c0`
- Upstream pins:
  - github-mcp-server `v1.12.2` = `85598ba6e1256f7ebf4867b95d63b833c4549264` (2026-09-16). A shallow clone is at `scratchpad/gmcp`.
  - MCP spec repo at `ab3a39c13bd23be691c2760e1c6c5c15a64582e1`, revision `2026-07-28`.
  - A2A `1.0.0`.
  - GitHub Docs pages fetched 2026-09-26. They are unversioned live pages.
- Companion document: `SPIKE-monitor-relay.md` (revision 2). This SPIKE plugs into its hub, its bridge and its auth model. It does not reopen any of them.
- Operator directive (verbatim, 2026-09-26): "integrate mentioned github mcp to MiOS development/-dev-loop's mcp/translation server for monitor(s) and manager(s) roles (or whatever the upstream patterns/naming conventions are for a meta harness(es)) research". It came with a screenshot of Copilot code review on mios-dev/MiOS#43: "Add a code-review agent skill or configure MCP servers for context-aware, tailored reviews".
- Evidence labels:
  - **READ**: I opened the file or page, and it is quoted.
  - **INFERRED**: my reasoning from READ facts.
  - **UNVERIFIED**: I neither read it nor measured it.

---

## 1. Role names aligned to upstream

### 1.1 Crosswalk

| Framework (READ source) | Our MANAGER (L0: breaks work down, dispatches, gates, merges lanes locally) | Our MONITOR (watches runs, sessions and PRs; relays, commits, opens PRs; never merges) | Our LANES |
|---|---|---|---|
| OpenAI Agents SDK, `openai.github.io/openai-agents-python/multi_agent/` | "manager agent" (agents-as-tools): "A manager agent keeps control of the conversation and calls specialist agents through `Agent.as_tool()`." | no term | "specialist agents" |
| Anthropic, *Building effective agents* | "orchestrator" (orchestrator-workers) | no role. The closest thing is an evaluator (evaluator-optimizer), which runs inside the loop | "workers" |
| Anthropic, *Multi-agent research system* | "lead agent" | no role. Watching is "production tracing" and observability | "subagents" |
| Claude Code, `code.claude.com/docs/en/agent-teams` | "Team lead" | "agent view" (`claude agents`), which is a surface for humans, not an agent | "teammates" / "subagents" |
| Google ADK, `adk.dev/workflows/collaboration/` | "coordinator agent" | no term | "subagents" |
| LangGraph (`langgraph-supervisor-py` README, main) | "supervisor" (supervisors can manage supervisors) | no term. **"supervisor" is already taken by the dispatcher** | "specialized agents" |
| AutoGen Magentic-One | "Orchestrator" (keeps the Task Ledger and the Progress Ledger) | no term. The Progress Ledger lives inside the orchestrator | named agents |
| CrewAI hierarchical process | "manager agent", which "delegates tasks, and validates outcomes" (that is our gate) | no term | agents |
| A2A 1.0.0 | toward the monitor: an **A2A Server (Remote Agent)** with an Agent Card. Toward lanes: an A2A Client | an **A2A Client** that uses Subscribe-to-Task streaming or registers a push-notification webhook | Remote Agents |
| MCP (architecture, 2025-06-18; unchanged in 2026-07-28) | an **MCP host** when it uses tool servers (AGY with the dev-loop and forge servers) | an **MCP host** (Claude Code) with one client per server: forge (via the bridge), mios-mcp, dev-loop | MCP servers expose tools only |
| GitHub (docs) | no term. "custom agents" is the nearest | "Copilot code review" is a separate reviewer, not our monitor | "Copilot cloud agent" |

### 1.2 Recommendation (INFERRED)

- **Keep "manager".** Two upstreams use the same word: OpenAI's "manager agent" and CrewAI's "manager agent", and CrewAI's version "validates outcomes", which is our gate. In prose, "orchestrator" is an allowed synonym.
- **Keep "monitor".** None of the nine frameworks defines a separate agent that watches other harnesses. All of them put progress tracking inside the orchestrator, so there is no upstream name to adopt. The monitor is therefore defined by its protocol identities:
  - an **MCP host** (holding the forge, mios-mcp and dev-loop clients);
  - an **A2A Client** of every manager (streaming, or push through its own webhook);
  - an **A2A Server** only for its own inbox (so that spokes and the operator can find the hub). See Q4.
- **Never call the monitor "supervisor" or "orchestrator".** Upstream, both words mean the role that dispatches and merges, which is our manager.
- **Lanes** are "workers" in prose and "remote agents" in A2A.
- **Copilot code review** is a third role: a *reviewer*. It is not the monitor. It runs on GitHub, reads the PR head, and cannot reach the mesh (§3).

### 1.3 Protocol-role table (what the bridge and hub must implement)

| Our role | MCP | A2A 1.0 | GitHub identity (via the bridge) |
|---|---|---|---|
| monitor (hub, a Claude Code session) | host; a client of `forge`, `mios-mcp` and `dev-loop` | Client of the managers; Server for its inbox (Agent Card) | bridge profile `monitor` |
| manager (AGY L0) | host; a client of `dev-loop` and of `forge` (profile `manager`) | Server (Remote Agent, Agent Card) toward the monitor; Client toward A2A lanes | bridge profile `manager` |
| lane (agy subagent / `claude -p`) | none for forge (see §2.6) | Remote Agent | none |
| bridge (-dev-loop, Rust) | a **server** to mesh clients (protected resource); a **client** of the github-mcp-server child it supervises | a Server that publishes a card for its adapters (companion SPIKE) | holds the upstream credential |
| reviewer (Copilot code review) | a client of GitHub's built-in GitHub MCP only | none | GitHub-managed, read-only, repo-scoped token |

---

## 2. The GitHub MCP server as an upstream fronted by the bridge

### 2.1 Shape

```
mesh client (monitor | manager)
   │  Streamable HTTP over mesh VPN, Authorization: Bearer <mesh-OIDC token, aud = bridge canonical URI>
   ▼
devloop-bridge (Rust static binary, -dev-loop OCI image)  ── MCP server = OAuth protected resource
   │  validates iss/aud/exp/scope → picks role profile → tool allowlist filter (tools/list + tools/call)
   │  stdio (one child per role profile)
   ▼
github-mcp-server v1.12.2 child   (flags fixed by the bridge; credential = bridge's own GitHub App token)
   ▼
api.github.com
```

- READ: github-mcp-server offers a `stdio` subcommand and an `http` subcommand (`cmd/github-mcp-server/main.go:264`, `httpCmd.Flags().Int("port", 8082, ...)`). Its image is `ghcr.io/github/github-mcp-server`, and the README says "The image is public".
- READ: "This authentication mode is not available for the `http` command. HTTP clients must continue to provide their own `Authorization` token." (`docs/github-app-auth.md`).
- INFERRED: the GitHub App credential must stay inside the bridge, so the bridge runs the child over **stdio**. Two cheaper options fail:
  - The child's `http` mode would require forwarding a GitHub token in every request.
  - Using the hosted `api.githubcopilot.com/mcp/` would put a GitHub token on the wire from the bridge. That is allowed, but it adds a remote dependency, and the self-hosted child satisfies Law 12 (BAKE-NOT-FETCH) inside the bridge image.
- INFERRED: the child is a Go binary. The Rust-static preference applies to our code (the bridge), not to an upstream server we vendor. Vendoring the upstream binary into the bridge image is the pragmatic choice. Q2 covers this.

### 2.2 Toolsets per role (flags the bridge sets; never taken from client headers)

READ (v1.12.2):
- `docs/server-configuration.md`: "read-only mode acts as a strict security filter that takes precedence over any other configuration", and "excluded tools takes precedence over toolsets and individual tools".
- `merge_pull_request` is in the **pull_requests** toolset (README.md:1264; `pkg/github/pullrequests.go:1530`), in the same toolset as `create_pull_request` (README.md:1239; `pullrequests.go:654`). **So choosing a toolset cannot remove merge.**
- `enable_pr_auto_merge` **does not exist in v1.12.2**. A grep of `pkg/` finds nothing. It shows up in this session's tool list, so it is a newer or hosted-only tool (INFERRED).

| Profile | Child flags (fixed at spawn) | Bridge allowlist (second filter; default deny) |
|---|---|---|
| `monitor` | `stdio --toolsets context,repos,pull_requests,actions,code_security,notifications --exclude-tools merge_pull_request,update_pull_request_branch,create_or_update_file,push_files,delete_file,create_branch,create_repository,fork_repository --lockdown-mode` | read: `get_me`, `get_file_contents`, `list_*`, `search_*`, `pull_request_read` (all methods), `get_job_logs`, `actions_list`, `actions_get`, `list_code_scanning_alerts`, `get_code_scanning_alert`, `list_notifications`, `get_notification_details`. review-reply: `add_reply_to_pull_request_comment`, `add_issue_comment`, `pull_request_review_write` (create / submit_pending with event COMMENT only; APPROVE and REQUEST_CHANGES are refused by argument inspection), `add_comment_to_pending_review`. notifications: `dismiss_notification`, `mark_all_notifications_read`. PR: `create_pull_request`, `update_pull_request` (title, body and draft only; `state` and `base` are refused) |
| `manager` | same toolsets and excludes as `monitor` | the monitor allowlist, **plus nothing** by default. The operator's brief says "manager adds PR create"; see the note below and Q3 |
| `reviewer-proxy` (optional, §3.3) | `stdio --read-only --toolsets repos,pull_requests,actions,code_security` | read tools only; every entry is re-annotated `readOnlyHint: true` |

Note on the brief ("monitor gets read + review-reply + notifications; manager adds PR create"). Read literally, it gives PR create to the manager and not to the monitor. But -dev-loop AGENTS.md says the monitor is the role that commits and opens PRs, and the operator merges ("verified work goes up as a PR ready for review; the operator reviews and merges from the GitHub app. The monitor never merges.", AGENTS.md:109-110). INFERRED, and left open as Q3: the recommendation is a **superset** order, `monitor` ⊂ `manager` in tool rights (the manager's profile = monitor + `create_pull_request`), while the monitor also keeps `create_pull_request` because it is today's PR opener. Neither profile ever gets merge.

**Nobody merges. It is enforced in four independent layers (INFERRED; defense in depth):**
1. The child runs with `--exclude-tools merge_pull_request,...`, which the upstream docs say wins over every other flag.
2. The bridge allowlist is default-deny, so a tool that a newer upstream adds (for example `enable_pr_auto_merge`) stays invisible until someone reviews it.
3. The GitHub App permissions omit **Contents: write**. UNVERIFIED against a pinned docs revision: the GitHub REST merge endpoint needs contents write, so the credential cannot merge even if layers 1 and 2 fail. The monitor pushes branches with its existing git credential, not through the bridge.
4. Branch protection / rulesets on `main` require an approving review from the operator (CODEOWNERS) and restrict who may merge. This is a GitHub setting, configured by the operator, not by an agent.

### 2.3 Auth (MCP authorization profile, 2026-07-28)

READ:
- `basic/authorization/security-considerations.mdx:124-126`: "MCP servers **MUST** only accept tokens specifically intended for themselves and **MUST** reject tokens that do not include them in the audience claim".
- `basic/authorization/index.mdx:283-286`: "The access token used at the upstream API is a separate token, issued by the upstream authorization server. The MCP server **MUST NOT** pass through the token it received from the MCP client."
- `index.mdx:215-222`: clients "**MUST** include the `resource` parameter ... canonical URI of the MCP server".
- `tutorials/security/security_best_practices.mdx:158-218`: an MCP proxy running a third-party flow "**MUST** ... Maintain a registry of approved `client_id` values per user ... Check this registry **before** initiating the third-party authorization flow".
- github-mcp-server `docs/streamable-http.md`: "The HTTP server is the OAuth protected resource, not the authorization server."
- github-mcp-server `docs/host-integration.md:127`: "Dynamic Client Registration is NOT supported by Remote GitHub MCP Server at this time."

Design (INFERRED):
- **Client leg (mesh to bridge).** The bridge serves `/.well-known/oauth-protected-resource`, which names the **mesh OIDC issuer** (companion SPIKE §4) as its authorization server. Clients get a per-session token with `resource=https://<bridge-mesh-name>/mcp`. On every request the bridge checks `iss`, that `aud == its canonical URI`, `exp`, and a `role` claim (`monitor` | `manager`). A mismatch returns 401 with `WWW-Authenticate` (resource_metadata). The role claim selects the child profile. Nothing a client sends can widen it: `X-MCP-Toolsets`, `X-MCP-Readonly` and `X-MCP-Tools` headers are **stripped** and never forwarded.
- **Upstream leg (bridge to GitHub).** The bridge holds **its own** credential, per the operator decision. Recommended: a GitHub App owned by the operator's account and installed on `mios-dev/{MiOS,mios-bootstrap}` and the -dev-loop repo. It has these permissions:
  - Pull requests: write
  - Issues: write (comments)
  - Contents: read
  - Actions: read
  - Checks: read
  - Code scanning alerts: read
  - Metadata: read

  The child uses GitHub App installation auth, which upstream supports on stdio only. The App private key reaches the bridge by bind-mount from the keyring (AGENTS.md:116-120) and is never baked into the image. The mesh token is never forwarded, and the GitHub token is never returned to a client.
- **Notifications caveat (INFERRED from READ scope facts).** `list_notifications` needs the user `notifications` scope. Installation tokens are app identities with no user inbox, so notifications either need a user-to-server token (a GitHub App user OAuth flow run once by the operator, with the refresh token kept in the bridge keyring) or they are dropped in favour of webhooks (§2.4). Q1.
- **Confused deputy.** When the bridge ever runs a user OAuth flow (the notifications option), it keeps the per-user approved `client_id` registry that the best-practices text requires.
- **Audit.** Every `tools/call` is logged by the bridge (tool, role, `sub`, repo, result class) into the relay's scrubbed-capture stream. Arguments are logged; tokens never are.

### 2.4 How PR, CI and review events reach the hub monitor (as A2A messages)

READ:
- The notifications toolset is **pull-based**. In v1.12.2 I found no webhook or push-stream code.
- MCP 2026-07-28 moves server-to-client streams to `subscriptions/listen` (`basic/patterns/subscriptions.mdx:7-9`).
- MiOS already parses GitHub webhooks: `usr/lib/mios/agent-pipe/mios_webhook.py:88` reads `X-GitHub-Event`.
- INFERRED: `subscribe_pr_activity` in this session is a Claude Code remote host feature, not an upstream GitHub MCP tool. The design must not depend on it.

| Option | Path | Latency | Needs | Verdict |
|---|---|---|---|---|
| A. Webhook to bridge (recommended) | A GitHub App webhook (`pull_request`, `pull_request_review`, `pull_request_review_comment`, `issue_comment`, `check_suite`, `check_run`, `workflow_run`) goes to a **public ingress** on the bridge. The bridge verifies `X-Hub-Signature-256` with the App webhook secret, normalizes the payload, and sends A2A `message/send` to the hub monitor's inbox | seconds | one publicly reachable HTTPS endpoint. INFERRED: a tailnet Funnel-style ingress or a small relay, since the mesh is userspace and has no inbound path. Q1 | best fidelity. It is the same App as §2.3 |
| B. Poll from the bridge | The bridge polls on a timer: `list_notifications` (user token) or `pull_request_read get_status/get_check_runs` for open PRs it knows about (installation token). It diffs against its last state and emits A2A messages | 30-120 s, and it spends API quota | no ingress | the fallback, and the only option with no public endpoint |
| C. Monitor-side polling via MCP | the monitor calls forge tools itself on its own loop | turn-bound | nothing new | today's behaviour. A cloud session's container is reclaimed when idle (AGENTS.md cloud note), so this is not durable |

- A2A shape (INFERRED, following the companion SPIKE's envelope). A `Message` has `role: "agent"`, `contextId` = `forge:<owner>/<repo>#<pr>`, and one `DataPart` holding an OpenAI Responses-shaped item `{type:"forge.event", event:"check_run.completed", repo, pr, head_sha, conclusion, url}`. **No GitHub payload body is copied through beyond those fields**, because the relay records scrubbed captures. The hub monitor then decides whether to call `forge` tools (for example `get_job_logs failed_only:true`) inside a turn.
- Vendor-name boundary: the event names above are GitHub's, and they appear only inside the -dev-loop bridge. What MiOS sees is a function-named `forge.event` type.

### 2.5 Registration surfaces (READ, then INFERRED placement)

- -dev-loop `.mcp.json:1-9` registers only the stdio `dev-loop` server. `register-mcp.sh:62-69` writes entries for claude and antigravity (verified) and for five other harnesses (unverified). INFERRED: add a `forge` entry there, of type `http` with the URL set to the bridge's mesh name. The token comes from a per-session helper, never a literal.
- MiOS agent-pipe `mios_mcp.py:85-89,237-271` merges vendor, `/etc`, user and `mios.toml [mcp.servers]` entries and expands `${ENV}` in headers. That supports a static bearer but has no OAuth client flow. INFERRED: MiOS gets a short-lived token from the mesh issuer through a helper that writes an env file. Q-level detail is in lane M-FORGE.

### 2.6 Lanes never see forge

READ: no lane launcher passes an MCP config (the only `mcp` match is a comment at `agy_host.sh:109`), so lanes inherit the user-scope config. INFERRED: registering forge at user scope would hand lanes PR-create rights, which breaks the lane contract (no push). Countermeasures:
1. Register `forge` only in the monitor's and manager's session config, never at user scope.
2. The bridge rejects any token without `role ∈ {monitor, manager}`. Lane sessions get no such token, because the mesh issuer mints role claims only for the hub and L0 identities.

---

## 3. Copilot code review tailoring in each repo

### 3.1 What upstream reads (READ, docs.github.com, fetched 2026-09-26)

- Code review reads, from the **PR head branch**:
  - `.github/copilot-instructions.md`
  - `.github/instructions/**/*.instructions.md` (with `applyTo`, and optionally `excludeAgent`)
  - the root `AGENTS.md` (or a single root `CLAUDE.md`/`GEMINI.md`)
  - skills under `.github/skills/`, `.claude/skills/` or `.agents/skills/`. Code review picks a skill up "Automatic when relevant (e.g. review-focused skills such as `code-review`)".
- Skill format: `SKILL.md` with required frontmatter `name` (lowercase and hyphenated) and `description`, and optional `license` and `allowed-tools`.
- MCP for code review:
  - It is configured in **repository web settings** (Settings > Copilot > MCP servers), not in a repo file.
  - "The GitHub MCP server and Playwright MCP server are enabled by default."
  - Code review supports **tools only**.
  - It is "not ... remote MCP servers that leverage OAuth".
  - "each tool in the MCP server's `tools/list` response must set `annotations.readOnlyHint` to `true`".
  - Secrets must be `COPILOT_MCP_*`.
- Repo state (READ): no repo has `.github/copilot-instructions.md`, `.github/instructions/` or any `.github/skills`. MiOS has `.github/ai-instructions.md` (filename not read by Copilot) and `.github/agents/dev-loop.agent.md:6`, which points at a non-existent `.github/skills/dev-loop/SKILL.md`. -dev-loop has no `.github/` at all. mios-bootstrap `.github/` holds only `workflows/`.

### 3.2 Per-repo files (INFERRED design)

| Repo | `.github/copilot-instructions.md` | `.github/skills/code-review/SKILL.md` | `.github/instructions/*.instructions.md` |
|---|---|---|---|
| MiOS | A short pointer: "AGENTS.md and CLAUDE.md are law. Review against the sixteen laws in `usr/share/mios/mios.toml [laws]`." It names the ones a reviewer most often misses: **Law 5** (no vendor names/URLs, retired ports), **Law 7** (no literal port, model or IP; values go through the mios.toml cascade), **Law 8** (a derived file changed without its generator, or a generator changed without the regenerate-and-diff check), **Law 15** (the same surface mirrored in mios-bootstrap is updated too, or the divergence is justified in the PR), **Law 16** (a new file of a templated type must come from `usr/share/mios/templates/`). It also carries -dev-loop's rule that every claimed test has a **negative control that fails**. Replaces or absorbs `.github/ai-instructions.md` (Q4) | A checklist skill. Steps: (1) map changed paths to the laws' `applies_to`; (2) Law 5 grep patterns (vendor product names, cloud AI hosts, `[docs].retired_ports`); (3) Law 7 literals in `automation/`, Quadlets and `usr/lib/mios/`; (4) Law 8: a diff touching a derived file without its generator; (5) Law 15: name the twin path in mios-bootstrap; (6) Law 16: a new file of a templated type; (7) two-sided controls: a test with no failing plant is reported as unproven. `allowed-tools` limited to read tools. It also fixes the dangling `dev-loop.agent.md` reference (Q4) | `automation.instructions.md` (`applyTo: automation/**`: bash is thin glue, Law 2 no mkdir in /var, Law 10 install.env form); `quadlets.instructions.md` (`applyTo: **/*.container`: Law 3 and Law 6) |
| mios-bootstrap | A pointer to its AGENTS.md and CLAUDE.md. It emphasizes **Law 15** (never double-track paths with mios.git; the ownership table), TOML-first (Law 7), and Law 5 in docs and commit messages | The same skill body, with a bootstrap path map (installer scripts, `etc/skel/`, `usr/share/mios/ai/`) and the known drift items (READ: `etc/mios/profile.toml:71` points at `/usr/share/mios/ai/mcp.json`, while MiOS ships `ai/v1/mcp.json`) | `powershell.instructions.md` (`applyTo: **/*.ps1`: Law 14 says no new PowerShell-as-program) |
| -dev-loop | Generated by its own `artifacts.py:42` pointer text ("Follow `AGENTS.md` ..."), plus: controls must be two-sided; no hand-written fakes (replay real transcripts); "untested" rather than "proven"; lane contract (owned_paths, no git add/commit/push); `validate.sh` gate | `code-review` skill: two-sided controls present, and the negative control actually fails; a new detection path without a real-transcript test is labelled untested; AGENTS.md claims carry a date and a measurement; shell `bash -n`/`sh -n`; JSON loads. **Placement:** `.github/skills/` (not `skills/`, which is the plugin payload, and not `.claude/skills/`, which the plugin loader might also pick up) | none needed |

Law 5 and `.github/` (INFERRED): `.github/` is a forge-mandated path that MiOS already uses (`workflows/`, `agents/`). The file *names* are fixed by GitHub. The *content* must avoid naming vendor agent products in MiOS, so the text says "the reviewer" and "the forge", not a product name. mios-bootstrap is bound the same way by its "OpenAI-API-only" rule. -dev-loop may name vendors.

Law 16 (INFERRED): Markdown instructions and skills are a file type. Either `usr/share/mios/templates/` gains a `[templates.review-skill]` entry and the MiOS/bootstrap files are scaffolded through `mios new`, or the operator exempts `.github/` forge-control files from Law 16. This is Q4.

### 3.3 MCP config for Copilot code review

- Default (recommended): keep the built-in GitHub MCP, which already has "read-only access to the current repository". Add **no** custom MCP server. The skill plus the instructions carry the tailoring.
- A custom MCP for review would have to satisfy all of these (READ constraints):
  - no OAuth, so a static `COPILOT_MCP_*` header;
  - reachable from GitHub-hosted infrastructure, which the userspace mesh is not;
  - every tool `readOnlyHint: true`.

  That contradicts the operator's mesh-OIDC-only decision. If it is ever wanted, the bridge's `reviewer-proxy` profile (§2.2) would be exposed on a **separate** public listener with a static, revocable, read-only secret, and that listener would carry **only** MiOS-context tools (for example a law-lookup tool reading `[laws]`), not GitHub tools, which the built-in server already has. Q2 covers this.
- The bridge must set `annotations.readOnlyHint` correctly on **every** tool it re-exports, in all profiles. It is also missing from -dev-loop's own `devloop_mcp.py` (READ: grep finds no `readOnlyHint`). That is a small fix: annotate the read tools `probe`, `tasks_next`, `report` and `validate_lanes`.

---

## 4. Law 5: nothing vendor-named in MiOS paths

READ:
- `usr/share/doc/mios/reference/upstream-registry.md:893-900` says vendor cloud hosts such as "`api.githubcopilot.com`, etc. are forbidden in the deployed image and fail audit".
- `mios.toml:3511-3512` holds only `[mcp] protocol_version = "2025-11-25"`.
- agent-pipe already reads `[mcp.servers]` (`mios_mcp.py:85-89`).
- MiOS's own forge is Forgejo (the `mios-forge.container` Quadlet, `FORGE_HTTP`/`FORGE_SSH` ports).

Design (INFERRED):
- MiOS consumes one function-named MCP server id, **`forge`**. Its SSOT keys go in `usr/share/mios/mios.toml`:
  ```toml
  [mcp.servers.forge]
  enabled   = false                 # opt-in; degrades open (Law 12)
  transport = "http"
  url       = ""                    # host/user overlay sets the bridge mesh URL; empty = off
  audience  = ""                    # canonical URI checked by the bridge; defaults to url
  token_env = "MIOS_FORGE_MCP_TOKEN" # short-lived mesh-OIDC token, written by the token helper
  tier      = "rare"                # keep off fan-out workers (worker_mcp_tools=true at mios.toml:3085)
  taint     = "untrusted-content"   # forge text is prompt-injection surface
  role      = "monitor"             # requested role claim
  ```
  These are the key names only. The vendor host, the GitHub App identity and the upstream server name live in -dev-loop.
- The Quadlet that runs the bridge on MiOS-DEV is function-named, for example `mios-forge-bridge.container`, and it pulls the -dev-loop image by a digest set in `mios.toml [images]`. The image **name** is -dev-loop's, which Law 5 must tolerate as an image reference (the same class as other upstream image refs in `[images]`). If the registry rejects it, mirror the image under a neutral name. Q2.
- One forge id can serve **either** backend: the -dev-loop bridge (GitHub), or later a Forgejo MCP pointed at `mios-forge`. The consumer does not change.
- The bridge advertises `serverInfo.name = "forge"` to MiOS clients. The upstream child's name is overridden with `GITHUB_MCP_SERVER_NAME`/`GITHUB_MCP_SERVER_TITLE` (README "Overriding Server Name and Title"), so the vendor name does not leak into agent-pipe's `mcp.forge.<tool>` namespace or into memory.
- Tool names such as `pull_request_read` are generic. `request_copilot_review` and the `copilot*` toolsets are excluded from every profile. That keeps them out of MiOS logs, and none of them is needed.
- Drift check (Law 8 style): extend `automation/98-drift-checks.sh` with a check that no string from `[docs]`'s vendor list appears in the `[mcp.servers.*]` values of vendor TOML.

---

## 5. Lanes (exclusive owned_paths, two-sided controls)

Each lane follows the dev-loop lane contract: no git add, commit or push, and no edits to AGENTS.md. The manager merges locally, the monitor opens the PR, and the operator merges.

| id | repo | owned_paths | objective | positive control | negative control |
|---|---|---|---|---|---|
| DL-BRIDGE-FORGE | -dev-loop | `bridge/src/forge/**`, `bridge/tests/forge/**`, `bridge/profiles/forge.toml` | Forge module in the Rust bridge: supervise the github-mcp-server stdio child per role; default-deny allowlist; argument guards (review event COMMENT only; `update_pull_request` without state/base); strip `X-MCP-*` headers; `serverInfo.name=forge`; audit log | `cargo test -p bridge forge::` replays a captured `tools/list` from github-mcp-server v1.12.2 and asserts that the monitor profile lists `create_pull_request` and `pull_request_read`, and no `merge_pull_request` | Plant: add `merge_pull_request` to the monitor allowlist. The test `forge::no_merge_in_any_profile` must FAIL, naming the tool. A second plant (submit_pending with `event:"APPROVE"`) must be refused |
| DL-BRIDGE-AUTH | -dev-loop | `bridge/src/auth/**`, `bridge/tests/auth/**` | Protected-resource metadata; mesh-OIDC JWT validation (iss/aud/exp/role); never forward the client token; upstream credential only from the bind-mounted keyring path | Test: a token with the right aud and `role=monitor` gets 200 and the monitor tool list; the child environment contains the App credential but not the client bearer (asserted by inspecting the spawned env) | Plant: a token with `aud` = another server. It must be rejected with 401 plus a `WWW-Authenticate` resource_metadata header. Plant: a bearer copied into the child env; the passthrough test must FAIL |
| DL-BRIDGE-EVENTS | -dev-loop | `bridge/src/forge_events/**`, `bridge/tests/forge_events/**` | Webhook ingress (HMAC-SHA256 verify) plus a polling fallback; normalize to the A2A `forge.event` DataPart; scrub bodies | Replay a captured webhook delivery (real, redacted). It yields one A2A message with the expected contextId and conclusion | Plant: flip one byte of the body. The signature check must reject it, and no A2A message may be emitted |
| DL-REVIEW-DOCS | -dev-loop | `.github/copilot-instructions.md`, `.github/skills/code-review/SKILL.md`, `skills/dev-loop/scripts/devloop_mcp.py` (annotations only), `tests/test_review_skill.py` | Copilot review tailoring for -dev-loop; `readOnlyHint` on devloop_mcp read tools | Test: SKILL.md frontmatter has a hyphenated `name` and a `description`; `tools/list` from devloop_mcp marks `probe`, `tasks_next`, `report` and `validate_lanes` as readOnlyHint=true and `run_lanes` as false; `validate.sh` passes | Plant: mark `run_lanes` readOnlyHint=true. The test must FAIL naming it. Plant: drop `name` from the frontmatter; the test must FAIL |
| DL-REGISTER | -dev-loop | `skills/dev-loop/scripts/register-mcp.sh`, `tests/test_register_mcp.py` | A `--forge-url` option adds a `forge` http entry for claude/agy session scope only, with the token taken from a helper command | Test: in a temp HOME, register writes the `forge` entry; other servers are untouched; the JSON loads | Plant: the entry is written to user scope with no role token. The test asserting "lanes do not inherit forge" must FAIL |
| M-FORGE | MiOS | `usr/share/mios/mios.toml` (`[mcp.servers.forge]` block only), `usr/lib/mios/agent-pipe/test_mios_forge_mcp.py`, `automation/98-drift-checks.sh` (new `check_forge_vendor_neutral` function only) | SSOT keys for the forge consumer; a drift check that no vendor host or name appears in `[mcp.servers.*]` | `python3 test_mios_forge_mcp.py`: the resolver produces `mcp.forge` disabled by default; with url and token env set, the header renders `Bearer ${MIOS_FORGE_MCP_TOKEN}`; `just drift-gate` passes | Plant: `url = "https://api.githubcopilot.com/mcp/"` in vendor TOML. `check_forge_vendor_neutral` must FAIL naming the key |
| M-REVIEW-DOCS | MiOS | `.github/copilot-instructions.md`, `.github/skills/code-review/SKILL.md`, `.github/instructions/automation.instructions.md`, `.github/instructions/quadlets.instructions.md`, `.github/agents/dev-loop.agent.md` (fix the dangling ref), `tests/test-review-skill.py` | Copilot review tailoring citing Laws 5/7/8/15/16 and two-sided controls; vendor-neutral content | Test: the files exist, frontmatter parses, every law cited appears in `[laws]` by id, and a Law 5 lint over these files passes | Plant: the product name of a vendor agent in copilot-instructions.md. The Law 5 lint must FAIL on that line. Plant: cite "Law 17"; the test must FAIL (not in `[laws]`) |
| B-REVIEW-DOCS | mios-bootstrap | `.github/copilot-instructions.md`, `.github/skills/code-review/SKILL.md`, `.github/instructions/powershell.instructions.md`, `tests/test-review-skill.py` | The same for bootstrap, with the Law 15 twin map | Same shape as M-REVIEW-DOCS | Same plants |

Order: DL-BRIDGE-AUTH before DL-BRIDGE-FORGE, before DL-BRIDGE-EVENTS. The three REVIEW-DOCS lanes and M-FORGE are independent and can run in parallel. The Law 15 mirror between M-REVIEW-DOCS and B-REVIEW-DOCS is reviewed together by the monitor before either PR is opened.

Test-double note (AGENTS.md, operator 2026-09-25): the controls above replay **real** captures (a github-mcp-server `tools/list`, a redacted real webhook delivery). Scenarios no capture contains are untested and must be labelled so. Examples are a forged JWT with a valid signature, or an upstream that suddenly adds a merge-like tool.

---

## 6. Operator questions (recommended option first)

1. **How do PR, CI and review events reach the hub monitor?**
   - (a) GitHub App webhook to a bridge public ingress, then A2A (recommended)
   - (b) the bridge polls PR status with the installation token (no ingress)
   - (c) the bridge polls notifications with a user-to-server token
   - (d) the monitor polls inside its own turns (status quo)
2. **Where does the upstream GitHub MCP server run?**
   - (a) the pinned `ghcr.io/github/github-mcp-server` binary vendored into the bridge image as a stdio child (recommended)
   - (b) the hosted remote endpoint, called by the bridge with its own token
   - (c) port the needed tools into the Rust bridge natively
3. **Which GitHub tool rights does each role get?**
   - (a) monitor = read + review-reply (COMMENT only) + notifications + create_pull_request; manager = the same; nobody merges (recommended; matches AGENTS.md "monitor opens PRs")
   - (b) literally as briefed: monitor has no PR create, manager adds PR create
   - (c) manager read-only and monitor as in (a)
4. **Copilot code review tailoring and Law 16/Law 5 scope**
   - (a) add `.github/copilot-instructions.md` + `.github/skills/code-review/SKILL.md` in all three repos, exempt `.github/` forge-control files from Law 16, content vendor-neutral in MiOS/bootstrap, fix MiOS's dangling `.github/skills/dev-loop` ref, keep only the built-in GitHub MCP for review (recommended)
   - (b) same files, but add `[templates.review-skill]` and scaffold via `mios new`
   - (c) also expose a public static-secret read-only MCP listener for review (conflicts with mesh-OIDC-only)

## 7. Open items not settled by this SPIKE

- The monitor's `list_notifications` needs a user inbox, and an installation token has none (Q1 option c).
- Whether GitHub's merge endpoint strictly needs Contents: write needs confirming on a pinned docs revision (layer 3 of §2.2 is UNVERIFIED).
- Whether `--dynamic-toolsets` was removed deliberately after v0.20.0. This design does not use it.
- MiOS `[ports].mcp` comment drift (`mios.toml:6933` says hermes-agent serves the port, while `mios-mcp.service` serves it through `mcp-server-runner`). mios-bootstrap `build-mios.ps1:3390` hardcodes `8460`. This is a Law 15/7 finding outside this SPIKE.
- The upstream role-name quotes for the OpenAI practical guide came from a search summary and should be pinned to the PDF before anyone cites them.
