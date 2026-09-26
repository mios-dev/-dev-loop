# SPIKE: monitor + relay for every MiOS image, with the GitHub MCP behind the bridge (revision 5)

- Status: proposed. This is a design only. No code was written, and every repo was only read (no git writes).
- Date: 2026-09-26
- Baselines (current `origin/main`, read with `git show origin/main:<path>` after `git fetch`):
  - MiOS `02f0f5e` (unchanged tip).
  - -dev-loop **`cd87715`** (re-baselined in revision 4: merge of PR #30, head `244ad99`). `git diff --stat f05f60b cd87715` = `AGENTS.md | 8 ++++++++`, the legibility-drain bullet inserted at `:109-116`. Every -dev-loop `AGENTS.md` cite at or after `:109` therefore moves by +8 (revision 3's `:116-120` is now `:124-128`, `:177-183` is `:185-191`, `:182` is `:190`). Every other -dev-loop cite is unchanged.
  - mios-bootstrap `37584c0` (unchanged tip).
  - **Not on main:** -dev-loop commit `846164c` ("feat(hooks): enforce 'the monitor never merges'") is on `origin/claude/dev-loop-iv4399` only. READ, GitHub API: PR #30 is closed with head `244ad99`, so `846164c` landed after the merge and no PR carries it (`git log origin/main..origin/claude/dev-loop-iv4399` lists exactly `846164c`). The task framing "already enforced now by ... PR mios-dev/-dev-loop#30" is therefore **false for main**. This SPIKE treats the merge of `846164c` as monitor action **P-2** (section 11.2). This matches `ADR0003-dispositions.md:10-15` (rev 4).
  - **Revision 5 re-check (2026-09-26, `git fetch` in all three repos):** every `origin/main` tip is unchanged (MiOS `02f0f5e`, -dev-loop `cd87715`, mios-bootstrap `37584c0`). The local checkouts sit on branch `claude/dev-loop-iv4399` (MiOS `cfa98ab03`, mios-bootstrap `6eed348`). That branch is **not** a baseline. A cite checked there as well says so.
  Every `file:line` below is on those commits unless it says otherwise.
- Upstream pins added in revision 4:
  - github-mcp-server `v1.12.2` = `85598ba6e1256f7ebf4867b95d63b833c4549264` (shallow clone at `scratchpad/gmcp`).
  - GitHub Docs pages were fetched 2026-09-26 through the docs article API. The source repo `github/docs` main was `18945a31a4f2` at that time. Local copies: `scratchpad/ghperm-body.md` (permissions for GitHub Apps), `scratchpad/ghwh.md` (validating webhook deliveries), `scratchpad/ghappauth.md` (about authentication with a GitHub App), and `scratchpad/ghdocs/*` (code review, custom instructions).
  - headscale `v0.29.4` = `8106636c7f8d` (`docs/about/features.md`).
  - Tailscale KB 1223 Funnel (last validated Jan 20, 2026).
- Operator directives (verbatim, 2026-09-26):
  - "update /dev-loop monitor and mios containers/devcontainers to include the monitor+relay to OpenAi/Claude/Google APIs/Upstream patterns—all MiOS images include everything MiOS; ... relay messages between Claude Code Cloud sessions/containers, Codespaces, GCE Shell's, etc-etc as a monitor and relay of all subagents to OpenAi patterns and upstream APIs"
  - "integrate mentioned github mcp to MiOS development/-dev-loop's mcp/translation server for monitor(s) and manager(s) roles (or whatever the upstream patterns/naming conventions are for a meta harness(es)) research"
- Evidence labels:
  - **READ**: I opened the file or page, and it is quoted or cited.
  - **MEASURED**: I ran it in this session. The artifacts are under `scratchpad/ts/`, or the command is named.
  - **INFERRED**: my reasoning from READ or MEASURED facts.
  - **UNVERIFIED**: not read and not measured.
  - **UNTESTED**: a control whose input is a real capture that does not exist yet (AGENTS.md:119-123, "Test doubles").
  Upstream URLs are pinned to a version wherever the publisher offers one. Tailscale KB pages and GitHub Docs pages have no versions, so they carry a "last validated" or fetch date.

### What revision 5 changes (critique of revision 4)

| Critique item | Change |
|---|---|
| W1: `[profiles.dev]` also covers devcontainer, cloud and Codespace (ADR-0025 `adr/0025-core-image-profile.md:141-146`), so "bridge in `[profiles.dev]` only" puts the bridge Quadlet and its Law 3 link into every container render | **Accepted.** New profile `dev-host` (`extends = ["dev"]`), listed only for the booted dev targets: `[profiles.targets].wsl2` and `[variants.entries.mios-dev].profile`. The bridge Quadlet is in `dev-host` only. **A Law 3 bound image counts as baked**: READ, `99-postcheck.sh:608-652` fails any bound image that is not in the baked `bound-images.tsv`. So the bridge goes into the existing firstboot tier instead (`[build.bake].firstboot_tokens`, `mios.toml:7623`; `miosd/src/main.rs:1156,1159`; `99-postcheck.sh:450-461`). It is pulled by digest on first start and never bound. New M8 controls check the `dev` render and every bound-images set. D8 gets a second, runtime check (dev-host profile **and** systemd present). Section 9.3. |
| W2: the tag→role map leaves spoke-hosted and hub-hosted monitors and managers without their forge roles | **Accepted.** New section 4.3. A forge role belongs to a tailnet **node** and is set by exactly one role tag. `tag:mios-spoke` grants membership only and **no** role. Monitor and manager keys carry `tag:mios-spoke` plus one role tag (P-5). On the hub host, each role runs its own node through templated `mios-mesh@<i>`/`mios-spoke@<i>` instances (`hub`→reader, `monitor`, `manager`). The monitor container is therefore its own node (`tag:mios-monitor`). New D1 controls: a spoke-only caller is refused, and the checked-in tailnet policy maps `tag:mios-spoke` to no role. P0 row h measures two userspace nodes on one host. |
| W3: `schema-init.sql` session comment is at `:202`, CREATE TABLE at `:200` | **Rejected with evidence.** `git show 02f0f5e:usr/share/mios/postgres/schema-init.sql \| grep -n -e 'CREATE TABLE IF NOT EXISTS session' -e 'hermes \| cron'` prints `201:` and `203:`. The same command at the branch tip `cfa98ab03` prints the same lines (the file is not in `git diff --stat 02f0f5e cfa98ab03`). `:200` is the `-- ── session:` banner comment. The cites `:201-210` and `:203` stand. |
| Missing 1: the vendor CLI installs in MiOS `.devcontainer/Containerfile:69,103-110` and ADR-0025's planned `dev-userspace` phase (`:135`) were not dispositioned. D7/B2 mirror them, and M2's scope does not cover `.devcontainer/` | **Accepted.** Section 2.3 records both as Law 5 debt. M2 extends the Law 5 gates to `.devcontainer/Containerfile`, with hash-anchored debt entries that fail if the debt grows or goes stale. A filed change to ADR-0025 L1/L4 keeps vendor CLIs out of `automation/` and `mios.toml`. The disposition is operator question **QC**. The recommended answer adds lanes **D15** (a -dev-loop devcontainer Feature) and **M15**, which drops the lines after M8 and M12. M9/D9/B3 reference the Feature by a function name. The order relative to ADR-0025 L1 and L4 is stated. |
| Missing 2: the stdio-child fallback edits `bridge/Containerfile`, which D11 does not own | **Accepted.** New conditional lane **D11b-forge-stdio**, run only if P0 row g fails. It owns `bridge/Containerfile` (after D10) and one new file, `bridge/src/forge/upstream_stdio.rs` (after D11). |
| Missing 3: on a `full`-profile booted host, the workspace has no path to the harnesses | **Accepted.** M12's workspace launcher reports `unavailable: no bridge on this host (profile <p>)` and never omits the harnesses silently. New M12 control `HARNESS SILENTLY ABSENT`. Section 5.4. |
| New finding (rev 5) | MiOS `ae9fa7ec6` and mios-bootstrap `6eed348` add a project `.claude/settings.json` `permissions.deny` for the three merge-class GitHub MCP tools. READ, `git branch -r --contains`: both exist only on `origin/claude/dev-loop-iv4399`, not on main. They join P-2 and barrier 3. |

### What revision 4 changes

| Input | Change |
|---|---|
| Relay decision: hosted tailnet coordinator now (ephemeral tagged keys, tsidp pinned for OIDC, HTTPS serve); headscale on a Blade replaces it when T-986 lands | Former Q1 closed (section 3). New READ fact: headscale `v0.29.4` does **not** implement Serve or Funnel (`docs/about/features.md:43-44`, both unchecked). So at T-986 the hub's HTTPS publishing, tsidp, and the webhook ingress must change too, not only the spokes' login server. That is new open question QA (section 15). |
| Bridge = pinned container on booted hosts in the DEV profile only, never baked | Former Q2 closed. Revision 3's container-kind install (`~/.cache/dev-loop/agent-bridge/`) is **withdrawn**. D8 writes only the booted-host drop-in. Container kinds send untranslated harness frames to the hub, where the bridge translates them (sections 1, 6, 9). |
| Blades kernel-mode tailscaled; Blade guests use their Blade's route (T-986 as written); every other image runs the userspace mesh service with `Conflicts=tailscaled` | Former Q3 closed (section 9.1). |
| A2O war-room MIGRATES | Former Q4 closed. M12 is unconditional. A new -dev-loop lane D10 takes the vendor keys and CLI installs, and M12 depends on D10, so no setting is lost in transit. |
| GitHub MCP, folded in as its own section | Section 10. Every item of its critique (`w032p06ep.output` "crit", 15 wrong + 10 missing) is resolved in section 10.10. Its eight lanes are re-scoped onto the bridge lanes, with no owned_paths collisions (section 11.4). |
| ADR 0003 item 1: amend `.devloop/LEDGER.md` to "not pushed"; build the manager counter as lane `dl-h-manager-counter` | Monitor action P-1 (section 11.2). Fleet slots in D5 are item 1's counter mirrored, not item 14 (section 7). |
| Captures: EXTEND MiOS T-040 hash-chained `session` rows with kinds `relay_msg` / `relay_tool_io`; no `relay_capture` table | M1 drops the `relay_capture` DDL. M3 records through the existing chained writer (sections 5.2 and 8). |
| `ADR0003-dispositions.md` rev 4, §0.1 and §6 (changes filed for this SPIKE) | All nine filed changes are applied: item 4 line, ties 5-8, fleet slots, item 30, D4 texts and pattern parity, D1 egress refusal, the §3.8 routing hop and final hop, the capture store, and the M2 `redact.py:6` note (sections 7, 8, 11, 12). |
| `critic_relay` (`w1ypid9bh.output`, 12 wrong + 6 missing) | Revision 3 resolved these. Section 14 re-verifies each one against the rev 4 baselines, and says where rev 4 changed the resolution. |

---

## 0. Binding operator decisions applied

| Decision (2026-09-26) | Effect |
|---|---|
| Envelope: A2A 1.0 carrying OpenAI Responses-shaped items. Tools use MCP. | Settled. |
| Hub core: EXTEND MiOS's A2A federation (`federation/a2a.py`, `agent_inbox`, a new `agent_outbox`) and `mios-mcp`. No new relayd hub. | Section 5. |
| -dev-loop ships only the vendor **bridge** (Rust static binary + OCI image): the harness adapters, the OpenAI/Anthropic/Google adapters, the translation ported from `provider_translate.py`, and now the forge (GitHub) module. | Vendor names live only in -dev-loop (section 2). |
| Reachability: mesh VPN in USERSPACE mode for every image that is neither a Blade nor a Blade guest. Hub on MiOS-DEV, reached by mesh name. | Sections 3 and 9.1. |
| **Coordinator: a hosted tailnet now** (ephemeral tagged keys, tsidp pinned for OIDC, HTTPS serve). Headscale on a Blade replaces it when T-986 lands. | Section 3. Section 15 QA covers what headscale lacks. |
| Auth: the mesh OIDC issuer mints per-session, audience-bound tokens (MCP authorization profile; no passthrough; no long-lived secret baked into an image). | Section 4. |
| **Bridge: a pinned container on booted hosts in the DEV profile only; never baked into any image.** | Sections 2, 9.3 (rev 5): rendered only for the `dev-host` profile (the booted dev targets). It is kept out of Law 3 binding through the firstboot tier, because a bound image is a baked image. |
| **Mesh modes:** Blades run kernel-mode tailscaled; Blade guests use their Blade's route (T-986 as written); every other image runs the userspace mesh service with `Conflicts=tailscaled`. | Section 9.1. |
| **A2O war-room migrates:** MiOS keeps a function-named workspace (code-server + tmux) that reaches vendor harnesses only through the bridge. Vendor keys and CLI installs move to -dev-loop. | Lanes M12 and D10. |
| Supervisor: extend `miosd daemon` for container kinds; systemd on booted hosts. | Lane M7. |
| Monitor: ONE hub monitor, thin spokes. A silent spoke is BLIND, never clean. | Sections 6 and 7. |
| **Captures:** the relay records relayed messages and tool I/O as **T-040 `session` rows** (kinds `relay_msg`, `relay_tool_io`), scrubs home paths and hostnames, refuses on a secret-pattern hit. Agent-facing controls stay UNTESTED until a real capture exists. | Section 8. |
| **GitHub MCP:** upstream = GitHub's hosted MCP endpoint, called by the bridge with its own token; PR author = a MiOS GitHub App bot (least privilege; no Contents:write); events = App webhooks, HMAC-verified, into the bridge over the mesh, normalised to A2A `forge.event` for the hub monitor; Copilot review tailoring = `AGENTS.md` only; monitor and manager get read + COMMENT-only review reply + checks/CI read + create PR; the MiOS runtime agent (agent-pipe) is read-only; **nobody merges**. Role names: "manager" (OpenAI Agents SDK / CrewAI manager agent), "monitor" (MCP host + A2A client), reviewer = Copilot code review. | Section 10. |
| ADR 0003: item 1 = ledger amend + `dl-h-manager-counter`; items 3, 4 kept; 2 dropped into the recorder; 5-8 kept with a MiOS tie; 9-31 per `ADR0003-dispositions.md`. | Section 12. |
| ADR-0025: fedora-bootc core base, rendered thin-shim devcontainer, `[profiles.core]` / `[profiles.dev]` (`adr/0025-core-image-profile.md:108-132`), postgresql+pgvector under miosd. | Sections 9 and 13. Rev 5 files two shape changes for L1/L4: a `dev-host` profile (9.3), and a `dev-userspace` phase without vendor CLIs (2.3). |

---

## 1. The roles

| Role | Where it runs | What it is | Language | Repo |
|---|---|---|---|---|
| **Hub** | MiOS-DEV; later a Blade | agent-pipe `a2a.py` + `agent_inbox`/`agent_outbox`, `mios-mcp`, the events hub, the hub recorder (T-040 `session` rows) | Python | MiOS |
| **Mesh issuer** | the hub only | tsidp `v0.0.15`, pinned by digest, run by the function-named Quadlet `mios-mesh-issuer.container`; its own tailnet node | upstream image | MiOS SSOT pin + Quadlet |
| **Bridge** | booted dev hosts only: the `dev-host` profile (9.3); in practice the hub (MiOS-DEV) | vendor harness adapters, vendor API translation, the forge module (GitHub hosted MCP, App webhooks), an MCP `lane_*` surface | Rust static binary + OCI image | -dev-loop `bridge/`, run by MiOS's function-named `mios-agent-bridge.container` |
| **Hub monitor** | the hub only | `global_monitor.py --relay`; reads loopback HTTP with a host-local scoped key (section 7). Its forge identity is its own tailnet node, `tag:mios-monitor`, through the hub's `monitor` spoke instance (4.3) | Python now; Rust later | -dev-loop image, run by `mios-agent-monitor.container` |
| **Spoke** | every image; on the hub host, one instance per role node (4.3) | `mios-spoke`: heartbeat, bounded spool, relay to the hub, directives back, and a loopback forward for SSOT-listed hub resources (section 6) | Rust static binary | MiOS `tools/native/mios-spoke` |
| **Mesh client** | every image (baked); runs per section 9.1 | `tailscaled` (userspace service, or the vendor kernel unit on Blades) | upstream package | MiOS `[packages.mesh]` |
| **Reviewer** | GitHub | Copilot code review. It reads the PR head's `AGENTS.md` and cannot reach the mesh (section 10.8). | n/a | n/a |

Data path (INFERRED):
- Where a bridge runs (DEV hosts): vendor harness → bridge adapter (vendor frame to Responses items) → spoke loopback ingress → spool → hub `/a2a`.
- Everywhere else (cloud session, Codespace, Cloud Shell, and every host whose profile set lacks `dev-host`): the -dev-loop hook (D6) hands the spoke an **untranslated harness frame**, carried as an opaque DataPart that the spoke does not parse. It is secret-scanned, spooled, sent over the mesh (userspace SOCKS5) to hub `/a2a`, and the hub routes it to the hub-side bridge's `/translate` endpoint. The bridge returns Responses items, which the hub ingests. The spoke never contains vendor logic.
- Directives travel the reverse path on the spoke's `SubscribeToTask` stream (section 5.1, G-A4).

---

## 2. Law 5: where vendor names may and may not appear

READ, Law 5 in MiOS: "No vendor cloud URLs, no vendor-specific agent/product names" (MiOS `CLAUDE.md`, law 5). -dev-loop `AGENTS.md:124-128` reserves the bridge seat: "source and OCI image in THIS repo (vendor names are allowed here; MiOS runs the image through a vendor-neutral, function-named Quadlet)", with credentials "by bind-mounting the existing agy/claude keyring and config directories" (`:126-127`).

Rules for new work:
- **Everything vendor-specific is in -dev-loop.** That means adapters, upstream base URLs (including the GitHub hosted MCP host), key schemas, translation tables, vendor credential paths, the GitHub App identity, webhook event names, and the A2O engine/model/effort settings (D10).
  - Upstream URLs and credential paths live in `-dev-loop/bridge/config/defaults.toml` and `bridge/config/forge.toml`, never in `mios.toml`.
- **MiOS names the bridge by function and carries no vendor path.**
  - `mios-agent-bridge.container`: Image = `[bridge].image` (digest). It is rendered only in the `dev-host` profile and is unbound, in the Law 3 firstboot tier (9.3). Its only credential mount is the function-named, empty-by-default `Volume=/var/lib/mios/agent-bridge/credentials:/run/agent-bridge/credentials:ro,Z` (tmpfiles, Law 2).
  - The vendor bind mounts (agy/claude keyrings, the GitHub App private key, the webhook secret) arrive as the admin drop-in `/etc/containers/systemd/mios-agent-bridge.container.d/50-credentials.conf`, written on the host by -dev-loop's installer (D8). READ, podman v5.2.0 `podman-systemd.unit.5.md:52-61`: "`foo.container.d` will be scanned for files with a `.conf` extension, which are then merged into the base file in alphabetical order". MiOS precedent: `mios-hermes-firstboot:865` writes `/etc/containers/systemd/mios-open-webui.container.d/99-enable-signup-once.conf`.
  - One bridge Quadlet serves both the relay and the forge. The GitHub draft's second Quadlet, `mios-forge-bridge.container`, is **dropped** (critique "missing" #4).
- **The bridge binary is never installed under a MiOS FHS path and never baked into any image** (decision). Revision 3's container-kind install is withdrawn.
- **The MiOS forge consumer is function-named.** The MCP server id is `forge`, the role requested is `reader`, the token is a file, not an env var (section 10.7). The bridge advertises `serverInfo.name = "forge"` in **its own** `initialize` response. It never relays the upstream's `serverInfo` (with a hosted upstream, `GITHUB_MCP_SERVER_NAME` cannot be set, `pkg/github/server.go:111`).
- **Copilot review tailoring lives only in `AGENTS.md`** (decision). No `.github/copilot-instructions.md`, `.github/instructions/`, or `.github/skills/` is added to MiOS or mios-bootstrap. MiOS's review text says "the reviewer" and "the forge".
- **Mesh client naming is not a Law 5 matter** (`mios.toml:8237` `MIOS_URL_TAILSCALE_REPO`; `06-enable-external-repos.sh:122`). Law 5 governs AI vendors.

### 2.1 The Law 5 URL gate: extend it, do not duplicate it

READ:
- The same literal regex exists twice: `automation/98-drift-checks.sh:1256` (`check_vendor_urls`, run at `:3777`) and `automation/99-postcheck.sh:296`. The regex already matches the GitHub hosted-MCP host. That is why the GitHub draft's second `check_forge_vendor_neutral` would have duplicated it (critique "wrong" #5).
- The scan scope is `SCAN_DIRS` (`98-drift-checks.sh:39-45`) and `_law5_dirs` (`99-postcheck.sh:290-296`). Neither covers `usr/share/mios/mios.toml`. Both loops skip non-directories (`98-drift-checks.sh:1259`, `99-postcheck.sh:299`). `SCAN_DIRS` is also used at `:232` and `:255`.
- The existing negative builds its URL by concatenation, so the test file carries no literal (`tests/drift-gate-negatives.sh:4804-4827`).

Lane M2:
1. Move the pattern into `automation/lib/law5.sh`, sourced by both gates, and by M14 and B4 (read-only).
2. Add a separate file list, `LAW5_SCAN_FILES=(usr/share/mios/mios.toml)`, with its own loop. A missing entry is a violation (`LAW5 SCAN TARGET MISSING: <path>`). `usr/lib/mios/mios.d` joins the directory list. This also covers every `[mcp.servers.*]` value, so no forge-specific check is needed.
3. Note filed by `ADR0003-dispositions.md` §3.31 row 6: if M2 extends the scan to `.py` files and key-shape patterns, MiOS's own `mios_pipe/redact.py:6` vendor key prefix is flagged. M2 must choose either a narrow anchored allowlist entry for `redact.py:4-10` (secret *detectors*) or no key-shape patterns at all. The recommendation is the anchored entry, because refusing to detect is worse than naming the shape.

### 2.2 Existing Law 5 debt and its disposition

| Where | What | Disposition |
|---|---|---|
| `mios.toml:1100-1146` (`[units."mios-agents.service"]`) | "Claude CLI + agy/Gemini"; `MIOS_A2O_{CLAUDE,AGY,GEMINI}_EFFORT_FLAG` | **M12 removes** (after D10 carries the values) |
| `mios.toml:5560-5590` (`[frontier]`) | `orch_engine = "claude"`, vendor model names, effort flags | **M12 removes** (after D10) |
| `mios.toml:6818-6826` (`[packages.ai]`), `usr/libexec/mios/install-ai-clis.sh:1-60` | vendor CLI installs | **M12 removes** (after D10) |
| `usr/share/mios/agents/Containerfile:28` (`npm install -g` of the vendor CLI), `:36` (agy install), `:60` (`MIOS_A2O_ENGINE=agy`), and the rest of `usr/share/mios/agents/**` | the war-room image hosting vendor CLIs | **M12 migrates.** It keeps the `code-server` base (`:6`) and `tmux` (`:13`), drops the vendor installs and engine defaults, and routes lane work to the bridge's MCP `lane_*` surface. |
| `.github/agents/dev-loop.agent.md:6` | names vendor products ("Claude Code CLI subagents", "parallel Copilot subagents", `/teamwork-preview`) and loads a non-existent `.github/skills/dev-loop/SKILL.md` | **M14 deletes it** (recommended; section 15 QB). Critique "wrong" #8. |
| `mios_pipe/redact.py:4-10` | vendor-prefixed key shapes | kept (a detector); section 2.1 note 3 |
| `routing/provider_translate.py:3`, `routing/remote_adapter.py:3,31,52` | the OpenAI/Anthropic/Gemini translator and its only caller | **M10 retires** |
| `mios-mcp-server:9-19` | docstring naming vendor products | **M5 rewrites** |
| MiOS `.devcontainer/Containerfile:69` (`RUN npm install -g` of three vendor CLI packages) and `:103-110` (the agy installer, fetched from a vendor URL at `:108`), at `02f0f5e`; D7 and B2 byte-mirror them into -dev-loop and mios-bootstrap | vendor CLI installs in the one shared dev image | **Open: QC** (section 15). Hash-anchored debt in M2 until it is answered (2.3). |
| ADR-0025 `adr/0025-core-image-profile.md:135`, `phases = ["dev-userspace"]   # new NN-dev-userspace.sh: npm CLIs, venv, code-server, agy` | a planned phase that would move those installs into `automation/` (and their names into `[packages.*]`), both inside Law 5 scope | **Filed change to ADR-0025 L1/L4** (2.3): the phase installs the venv and code-server only |

M12 adds `check_vendor_names` to `law5.sh`, scoped to active `mios.toml` lines and to `.devcontainer/Containerfile` (the latter under 2.3's debt entries). It excludes the `[laws]`, `[docs]` and file-list keys that name repo files (`CLAUDE.md`, `GEMINI.md`, `AGY-*` ids; measured at `mios.toml:2238,11391,11486,11661-11662,11800-11801,11977,12167-12169`).

### 2.3 Vendor CLI installs in the shared dev image (rev 5)

READ, at `02f0f5e`:
- `.devcontainer/Containerfile:69` `RUN npm install -g` names three vendor CLI packages.
- `:103-110` runs `mios-fetch-installer` against a vendor URL (`:108`) and checks `agy --version` (`:110`).
- The -dev-loop constitution requires that every MiOS repo carry "the same devcontainer definition, byte-identical and gated" (-dev-loop `AGENTS.md`, Environments; `tests/test_devcontainer_mirror.py`). D7 and B2 therefore spread these lines to all three repos.
- ADR-0025 `:135` plans a MiOS phase `NN-dev-userspace.sh` for "npm CLIs, venv, code-server, agy". `[packages.devcontainer]` (`mios.toml:6157`) lists only `"nodejs", "npm"` (`:6165`) today, with no vendor package names.
- M2's rev 4 scan scope (`mios.toml`, `mios.d`, the `SCAN_DIRS`) does not include `.devcontainer/`, so the vendor URL at `:108` is ungated.

The migration decision ("vendor keys and CLI installs move to -dev-loop") names the A2O war-room. Whether it also covers the shared dev image is a scope call for the operator, so it is **QC**. What this SPIKE does regardless of the answer:
1. **Gate the debt now (M2).** `LAW5_SCAN_FILES` gains `.devcontainer/Containerfile`. Known debt lines are listed in `automation/lib/law5.sh` as `LAW5_DEBT=("<sha256 of the exact line>  .devcontainer/Containerfile")`, one per line (`:69`, `:108`), so no vendor literal is written into `automation/`.
   - A hit whose line hash is not listed fails `check_vendor_urls` (or `check_vendor_names` after M12) and names the file and line.
   - A listed hash that matches no line fails `LAW5 DEBT STALE: <hash> .devcontainer/Containerfile`. Removing the debt therefore forces the entry out, and a count ratchet cannot be gamed.
2. **Keep vendor CLIs out of MiOS's pipeline (filed change to ADR-0025 L1 and L4).** `dev-userspace` installs the venv and code-server only. L1 adds no vendor package name to any `[packages.*]` section. L4's rendered shim carries lines `:69` and `:103-110` verbatim, still under the debt entries. It does not move them into `automation/`.
3. **If QC is answered (a), the recommended answer:**
   - Lane **D15** publishes a -dev-loop devcontainer Feature. The id is function-named, `ghcr.io/mios-dev/devloop-features/harness-clis` (illustrative: a ghcr path segment cannot start with `-`). It installs the same CLIs, and vendor names are allowed there.
   - M9, D9 and B3 each add that id under `features` in their `devcontainer.json`. `features` is not an owned projection key: only `forwardPorts` and the `containerEnv` keys are owned (`mios.toml:10363-10368`), and unowned keys merge (`sync-dotfiles.py:286`).
   - Lane **M15** then drops `:69` and `:103-110` from the shim and removes the two `LAW5_DEBT` entries in the same change. D7 and B2 mirror the result.
4. **Order:** ADR-0025 L1 → M1 → M2 (debt entries) → ADR-0025 L4 (shim rendered; lines carried verbatim) → M8 → D15 published → M9 / D9 / B3 (`features` entry) → M15, after M12 as well (lines dropped and debt entries removed in one change) → D7 / B2 (each after its own repo's `features` entry). Until M15 lands, an environment installs the CLIs twice, which is harmless. The rule: no environment loses a CLI before the Feature that replaces it is published.

---

## 3. Mesh join per environment (hosted tailnet now)

### 3.1 What userspace mode is (READ)

- https://tailscale.com/kb/1112/userspace-networking (last validated Nov 12, 2025): "Userspace networking mode lets you run Tailscale where you don't have access to create a VPN tunnel device." Example: `tailscaled --tun=userspace-networking --socks5-server=localhost:1055 --outbound-http-proxy-listen=localhost:1055`.
- Consequence (INFERRED): applications reach tailnet names through tailscaled's SOCKS5/HTTP proxy. The spoke dials the hub with `socks5h://127.0.0.1:<[ports].mesh_socks5>` and never uses the ambient `HTTPS_PROXY`. MEASURED (`scratchpad/ts/derp.err`): the cloud session's `no_proxy` includes `100.64.0.0/10`, so a direct dial to a tailnet IP would bypass the egress proxy and, with no TUN, have no route.
- Ephemeral nodes, https://tailscale.com/kb/1111/ephemeral-nodes: "auto-removed ... from 30 to 60 minutes after the last activity"; `--state=mem:` "registers the node as an ephemeral node".
- Auth keys, https://tailscale.com/kb/1085/auth-keys: "one-off" or "reusable", optionally "Ephemeral", "Pre-approved", "Tags"; expiry "between 1 and 90 inclusive" days.
- **Funnel** (for the webhook ingress, section 10.6), https://tailscale.com/kb/1223/funnel (last validated Jan 20, 2026): it requires "HTTPS enabled and valid HTTPS certificates for your tailnet", "MagicDNS enabled", and a `funnel` node attribute in the tailnet policy. "Funnel can only listen on ports `443`, `8443`, and `10000`." It needs "Tailscale v1.38.3 or later". The page says nothing about userspace mode or tsnet, so **Funnel in userspace is UNVERIFIED** (P0 row f).
- **Headscale gap** (READ, headscale `v0.29.4` `docs/about/features.md:43-44`): `- [ ] Funnel` and `- [ ] Serve`, both unchecked. Pre-auth keys, ephemeral nodes, tags and an embedded DERP are checked (`:10`, `:25`, `:26`).
- **Inbound in userspace is UNVERIFIED.** Spokes need none. The hub publishes `/a2a`, `/mcp` and `/forge/mcp` through `tailscale serve` HTTPS (decision). Whether `serve` works in userspace is P0 row b.

### 3.2 Per-environment table

| Environment | Mesh mode (section 9.1) | Coordinator reachable? | Data path | Lifetime / idle rule | Spool that survives | Role |
|---|---|---|---|---|---|---|
| **Claude Code cloud session** | userspace | **MEASURED 2026-09-26** (`scratchpad/ts/tsd.log:60-72`): tailscaled 1.102.4 through the TLS-re-terminating proxy got `CONNECT ... controlplane.tailscale.com:443 ... 200`, the control key, and `RegisterReq: got response; ... authURL=true`. No join was completed. | `curl` measured a DERP 101 upgrade (`scratchpad/ts/derp.err`). tailscaled's own DERP client through the proxy is **UNVERIFIED** (P0 row d). UDP was not measured. | AGENTS.md:185-191: reclaimed a few minutes after the turn ends; resumed "on a restarted VM with the disk intact and no processes" (one measurement) | `[relay].spool_dir` `/var/lib/mios/spoke` (tmpfiles); INFERRED to survive | spoke, alive while a turn is open |
| same, projection container | userspace | INFERRED identical (`--network host`, inherits `HTTPS_PROXY` and the CA: `cloud-fedora-setup.sh:420-433`) | same | same | same | spoke |
| **GitHub Codespaces** | userspace | UNVERIFIED. Tailscale's recipe uses kernel TUN (https://tailscale.com/kb/1160/github-codespaces, `--device=/dev/net/tun`); userspace needs neither. | UNVERIFIED | default 30 min, range 5-240; "Terminal activity, either input or output, also resets the idle timeout period"; on rebuild "Changes you have made outside the `/workspaces` directory are cleared" (GitHub Docs, URLs in section 17) | `${containerWorkspaceFolder}/.work/spool` via each repo's `containerEnv` (M9, D9, B3) | spoke |
| **Google Cloud Shell** | userspace | UNVERIFIED | UNVERIFIED | "Non-interactive sessions are ended automatically after 40 minutes ... capped at 12 hours"; `$HOME` is "5 GB of free persistent disk storage" (https://docs.cloud.google.com/shell/docs/limitations) | the opened repo's workspace, via the same `containerEnv` entry | spoke |
| **MiOS-DEV** (WSL2) | userspace | UNVERIFIED; outbound only, so NAT needs no forward (INFERRED) | DERP or direct | systemd, durable while the PC is awake | `/var/lib/mios/…` | **hub + bridge + monitor + issuer** |
| **Blade** (bare metal) | kernel (vendor `tailscaled.service`) | UNVERIFIED | direct | durable | `/var/lib/mios/…` | spoke; later the hub (T-986) |
| **Blade guest** (NIC-less) | none; routed over its Blade (T-986, `TASKS.md:10738`) | n/a | through the Blade | durable | `/var/lib/mios/…` | spoke |

**No keep-alive (binding).** Nothing may manufacture "activity indicative of a user's presence". The spoke never writes to a terminal, because Codespaces counts terminal output as activity. A spoke in Codespaces or Cloud Shell lives as long as the user's session, then goes BLIND, then LOST.

---

## 4. Token bootstrap: mesh identity first, then per-session, audience-bound tokens

Two credentials, never confused: (1) the **mesh join credential**, which gives network membership only, and (2) a **per-session access token**, minted from the mesh identity and audience-bound to one resource.

READ, MCP 2025-11-25 authorization (https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization): servers "MUST implement OAuth 2.0 Protected Resource Metadata (RFC9728)"; the `resource` parameter "MUST be included in both authorization requests and token requests"; servers "MUST validate that access tokens were issued specifically for them as the intended audience"; "MUST NOT accept or transit any other tokens"; "MUST NOT pass through the token it received from the MCP client"; authorization servers "SHOULD issue short-lived access tokens"; endpoints "MUST be served over HTTPS".

### 4.1 Join credential per environment (no secret in any image)

| Environment | Join method | Where it lives |
|---|---|---|
| Claude Code cloud session | reusable, ephemeral, pre-approved, tagged auth key; `--state=mem:`. The key kind depends on the environment (4.3): spoke-only `tag:mios-spoke`, or `tag:mios-spoke` plus one role tag in the monitor's or manager's environment | the cloud environment's settings, as an env var ("added in the environment's settings ... A new session picks it up", session documentation `environment.secrets`). The launcher passes it once as `--auth-key=file:<0600 tmp>` and drops it from the spoke's env. It never reaches a MiOS env file (Law 11). |
| Codespaces | same key type | a Codespaces secret (UNVERIFIED wording) |
| Cloud Shell | interactive `tailscale up` login URL | nothing stored |
| MiOS-DEV (hub) | interactive login once, or an auth key in `/etc/mios/secrets.env` (0600), **per instance** (4.3) | persistent nodes: `hub` (`tag:mios-hub`), `monitor` (`tag:mios-monitor`), `manager` (`tag:mios-manager`), state `/var/lib/mios/mesh/<instance>` |
| Blade | per T-986 (kernel mode) | host secrets |

The tailnet policy is an operator action (P-5): tags, `funnel` node attribute for `tag:mios-hub` only, HTTPS + MagicDNS, and tsidp app-capability grants.

### 4.2 Per-session tokens

- **Issuer: tsidp `v0.0.15`**, digest `sha256:cae91835375efcbf75ecb8f9520e3472cda946e3ca9af1df3bce9540902f289e` (MEASURED: ghcr tags list `v0.0.1`…`v0.0.15`). README (main): "A simple OIDC / OAuth Identity Provider (IdP) server for your tailnet", STS token exchange per RFC 8693 (`-enable-sts`), "experimental ... may experience breaking changes", `TAILSCALE_USE_WIP_CODE=1` "while version <1.0.0", `TS_AUTHKEY_FILE`, "tsidp requires persistent state storage". Its `-dir` is `/var/lib/mios/mesh-issuer`. It runs from the function-named Quadlet, hub role only, and gets its join key through Quadlet `Secret=`.
- **Grant (INFERRED).** A caller authenticates to tsidp as its tailnet node, with no client secret, and asks for a token with `resource=<URI>` (RFC 8707). There is one token per resource: `/a2a`, `/mcp` and `/forge/mcp` are distinct audiences. Refresh happens at 80% of `[relay].token_ttl_s`.
- **Role claim (new in rev 4, INFERRED).** The forge needs `role ∈ {monitor, manager, reader}`. tsidp adds claims through tailnet policy app-capability grants keyed on the caller's tag. Tag → role: `tag:mios-monitor` → `monitor`, `tag:mios-manager` → `manager`, `tag:mios-hub` (agent-pipe's node) → `reader`, **`tag:mios-spoke` → no role**. Which node carries which tag is section 4.3. **UNVERIFIED**: P0 row c measures a non-interactive, audience-bound token with a role claim for a tagged node.
- **Fallback if P0 row c fails:** a minimal Rust issuer on the hub (`tools/native/mios-mesh-issuer`). It identifies the caller through tailscaled LocalAPI `whois` on the connection's source and signs with a key from `/etc/mios/secrets.env`. It becomes a lane only if P0 fails.
- **A2A reconciliation:** the Agent Card `securitySchemes` is read from SSOT (`a2a.py:256-265`). M1 sets an OIDC scheme pointing at tsidp. The passports (`a2a.py:279-370`, `_a2a_verify_principal` `:697`) stay as message-level attestation.
- **No passthrough.** Upstream vendor credentials, including the GitHub installation token, come only from the bridge's own credentials. A spoke, hub or forge token is never forwarded upstream, and an upstream token is never returned to a client. The negatives in M3, M5, D1 and D11 enforce this.

### 4.3 Role identities: which node carries which role (rev 5)

Rule (INFERRED from 4.2): tsidp identifies a caller by the tailnet node the connection comes from, through LocalAPI `whois`. So:
- A forge role is a property of a node, and a loopback caller has no identity.
- Each node carries **at most one** role tag.
- `tag:mios-spoke` is membership only.
- The bridge accepts `/forge/mcp` only with a token whose `role` claim is exactly one of `monitor`, `manager` or `reader`. It refuses a missing, unknown or multi-valued claim (D1 controls c and e).

| Principal | Node | Tags (auth key kind, P-5) | Role claim | Reaches `/forge/mcp` through |
|---|---|---|---|---|
| agent-pipe on the hub (M13) | hub instance `hub`, persistent | `tag:mios-hub` | `reader` | the bridge's loopback, with a token minted by `mios-forge-token` through the `hub` instance |
| hub monitor container (D5) | hub instance `monitor`, persistent, its own node | `tag:mios-monitor` | `monitor` | the `monitor` instance's loopback forward, reached the way section 7 reaches `/v1/relay/sessions` |
| AGY manager launched on MiOS-DEV | hub instance `manager`, persistent, its own node | `tag:mios-manager` | `manager` | the `manager` instance's forward (D14 registers that port for the manager host) |
| monitor session in a cloud environment (for example, a Claude Code monitor) | the session's single ephemeral node | `tag:mios-spoke` + `tag:mios-monitor` (the **monitor key**, stored only in that environment's settings) | `monitor` | the session spoke's forward |
| AGY manager in a cloud environment | the session's single ephemeral node | `tag:mios-spoke` + `tag:mios-manager` (the **manager key**) | `manager` | the session spoke's forward |
| every other spoke (worker sessions, Codespaces, Cloud Shell, Blades; Blade guests through their Blade) | its node | `tag:mios-spoke` only | **none** | refused (`ROLE CLAIM MISSING`) |

- **Instances (M1, M6, M8):** templated `mios-mesh@.service` and `mios-spoke@.service`.
  - Each instance has its own `--statedir`, `--socket`, SOCKS5 port and ingress port, taken from `[relay.instances.<i>]`, which names the port keys (`[ports].*`, Law 7) and the tag.
  - The hub renders `hub`, `monitor` and `manager`. Other booted hosts render one instance, `node`. Container kinds run one instance under miosd.
  - Running several userspace tailscaled processes on one host with distinct state and sockets is INFERRED. P0 row h measures it.
- **Honest cost:** a cloud environment's key is shared by every session started in that environment, so role = environment. The monitor's and manager's environments must not also host worker sessions. Lanes inside those sessions share the uid (10.9).
- The monitor's `relay:read` caller key (section 7) is a hub-API credential, never a forge credential.
- The checked-in policy fragment `bridge/config/tailnet-policy.hujson` (D1) is what the operator applies in P-5. D1's test asserts that each role tag maps to exactly one role and that `tag:mios-spoke` maps to none. The grant syntax is UNVERIFIED until P0 row c.

---

## 5. Hub: reuse of `federation/a2a.py`, `mios-mcp`, and the T-040 session chain

### 5.1 `federation/a2a.py` (1379 lines), READ

| Existing | Citation | Gap | Closed by |
|---|---|---|---|
| Agent Card `/.well-known/agent-card.json`, `pushNotifications: True` | `a2a.py:189-270`, `:232` | none | reuse |
| `message/send` | `:901-929` | **G-A1:** text Parts only (`:907-910`; `_a2a_text_from_message` `:727-745`). Responses items and harness frames travel as data Parts. | M3 |
| Tasks in an in-memory LRU of 512 | `:712-713`, `:766-777` | **G-A2:** not durable | M3 (`agent_inbox`) |
| No duplicate detection | `:901-929` | **G-A3:** A2A 1.0 §3.3.1 "Agents may utilize the messageId to detect duplicate messages." | M3 (`idempotency_key` = `messageId`; `agent_inbox.idempotency_key text UNIQUE`, `schema-init.sql:1492`) |
| `SubscribeToTask` rejected | `:1068-1071`; SSE only for `message/stream` (`:1086-1110`) | **G-A4:** directives need a spoke-held stream; A2A 1.0 §3.5.2 "MUST deliver events in the order they were generated" | M3 (fed from `agent_outbox` in `seq` order) |
| Transport auth: `inbound_auth_mw` (`mios_pipe/auth.py:69-93`) gates `("/v1/", "/a2a")` (`server.py:699`) only when `api_require_auth` is true (default false, `server.py:691-694`); checker `_check_inbound_principal` (`access/authn.py:90-110`), wired at `server.py:4250-4257` | as cited | **G-A5:** no issuer JWKS or `aud` check; with auth on, a JWT is rejected before `a2a.py` | **M3** owns `auth.py` and new `relay_auth.py` (hub role: `/a2a` always gated; JWT `aud` per prefix; caller-key fallback). **M4** passes the composed checker in `server.py`. |
| Push notifications | `:780-824` | not used toward spokes (no inbound) | n/a |

`[a2a].discover_port = 8700` (`mios.toml:3494`) is a literal copy of `[ports].agent_pipe` (`mios.toml:6920`), a Law 7/9 debt. M1 derives it.

### 5.2 Durable queue, routing, events, and the capture store (READ)

- `agent_inbox`: `schema-init.sql:1489-1504` (`status` = `pending | processing | dispatched | duplicate | failed`, `origin_node`). It has **no recipient column** (`ADR0003-dispositions.md` §3.8).
- New tables (M1): **`agent_outbox`** (`dest_peer`, `spoke_session`, `seq`, `idempotency_key UNIQUE`, `next_attempt_at`, `acked_at`, `status`) and **`relay_session`** (`spoke_session`, `node`, `env_kind`, `role`, `manager_context_id`, `hw_seq`, `last_seen`, `state`). Both go into `[security.redact]` (`mios.toml:1730-1760`, gate `check_redact_coverage`). **No `relay_capture` table** (decision).
- **Routing, the §3.8 step 3 hop filed by the dispositions (M3):** a Message whose metadata carries `manager_context_id` is resolved through `relay_session` to that manager's spoke session, and M3 inserts an `agent_outbox` row with `dest_peer` and `spoke_session` set. A harness frame DataPart is routed to the bridge's loopback `/translate` (D3), and the returned items are ingested like any other item.
- **Capture store = T-040 `session` rows (decision).** READ:
  - `session` (`schema-init.sql:201-210`): `id text PRIMARY KEY`, `kind` (comment `:203`: "hermes | cron | cli | delegate | mcp"), `owui_chat_id`, `meta jsonb`, `origin_node`, logical clocks. Chain columns `chain_seq`, `prev_hash`, `chain_hash` are at `:652-655` ("T-040 (OBS-03): Session Hash Chain Migrations").
  - The chain covers `SESSION_CORE_FIELDS = ("id", "kind", "owui_chat_id", "meta")` (`observability/audit.py:42`). `stamp_session` is at `:197`, `verify_session_chain` at `:200`, and `usr/libexec/mios/mios-chain-verify` exists.
  - Every `session` write through `dbwrite._db_create` is stamped: `elif table == "session": fields = mios_audit.stamp_session(fields)` (`mios_pipe/dbwrite.py:77-78`).
  - `session` is already in `[security.redact].tables` (`mios.toml:1735-1740`), so DURA-02 redaction on persist applies with `fail_closed = true` (`:1733`).
  - M3 writes one row per relayed item: `id = "relay:<spoke_session>:<seq>"`, `kind` = `relay_msg` (messages) or `relay_tool_io` (function_call / function_call_output items), `meta` = `{spoke_session, seq, env_kind, generated_at, late, item: <scrubbed Responses item>}`. **Dedup happens before stamping**, through `agent_inbox`'s UNIQUE key and `hw_seq`, because `SessionChainer` advances in-process when it stamps. A duplicate that reached the insert would fail on the primary key after the chain had advanced, leaving a gap. M1 updates only the `kind` comment at `:203` (no DDL). (Rev 5: the critique's `:202`/`:200` is rejected. `grep -n` on the file at `02f0f5e` and at the branch tip `cfa98ab03` prints `201:CREATE TABLE IF NOT EXISTS session (` and `203:    kind ...`; `:200` is the banner comment.)
- Events hub: `AgentEventHub.broadcast` (`mios_events.py:65`) has zero callers. `authenticate()` accepts all connections when no key is set (`:25-29`). M3's `relay_ingest.py` takes an injected `on_item(event_type, data, session_id)` callable. M4 passes `broadcast` and replaces `authenticate()` with `_check_inbound_principal`, failing closed.
- Webhooks: `server.py:4505-4509` calls `ingest_webhook` without `db_pool` (`mios_webhook.py:60-68`, `:107`). M4 fixes it. GitHub App webhooks do **not** go here: they terminate at the bridge (section 10.6), because the event names are vendor names.
- Read API for the monitor: M3 adds `GET /v1/relay/sessions` (scope `relay:read`).

### 5.3 `mios-mcp` (READ)

`mios-mcp.service:19` runs `mcp-server-runner`, which falls back to `mios-mcp-server --http` (`mcp-server-runner:59`) on `127.0.0.1` (`:614`) with no `Authorization` handling (`[ports].mcp = 8770`, `mios.toml:6933`).
- **G-M1 (M11):** publish `/mcp`, `/a2a` and `/forge/mcp` through the hub's `tailscale serve` from `[relay.expose].paths`, and publish `/forge/webhook` alone through Funnel from `[relay.funnel].paths`. Loopback targets only; `/v1/` never.
- **G-M2 (M5):** RFC 9728 metadata, a 401 with `WWW-Authenticate: Bearer resource_metadata=…`, and an `aud` check.
- **G-M3 (M5):** rewrite the docstring (`:9-19`) in function terms.
- The registry path is correct in MiOS (`federation/mcp.py:64-68`: `/usr/share/mios/ai/v1/mcp.json`). mios-bootstrap `etc/mios/profile.toml:71` is stale (B1).

### 5.4 One front door (Law 5)

MiOS agents keep `MIOS_AI_ENDPOINT` as the only AI address. The bridge's `/v1` facade binds loopback and is reached by agent-pipe through `[nodes.*]` routed by function (M10). On a host without the bridge (any host whose profile set lacks `dev-host`: `core`, `full`, and every container kind), those nodes are reported unavailable. They are not silently dropped (M10 control c). The same rule holds for the MiOS workspace (M12): on such a host it lists the harnesses as `unavailable: no bridge on this host (profile <p>)` (M12 control b).

---

## 6. Spoke behaviour

Upstream patterns (READ): gRPC connection backoff v1.66.0 (`INITIAL_BACKOFF` 1 s, `MULTIPLIER` 1.6, `JITTER` 0.2, `MAX_BACKOFF` 120 s, `MIN_CONNECT_TIMEOUT` 20 s); Kubernetes v1.33 node status (Lease "every 10 seconds"; `NodeMonitorGracePeriod` "defaults to 50 seconds").

| Behaviour | Rule | SSOT key (M1) |
|---|---|---|
| Heartbeat | A2A `message/send` with a heartbeat data Part every 10 s (`spoke_session`, `seq_hw_local`, `spool_bytes`, `dropped_count`, `env_kind`, `state`) | `[relay].heartbeat_s = 10` |
| BLIND | `now - last_seen > 50 s`. BLIND means "not observed". A declared `suspend` (D6) sets the reason `declared-suspend`; the verdict stays BLIND. | `[relay].blind_after_s = 50` |
| LOST | `now - last_seen > 3600 s`, aligned with ephemeral-node removal | `[relay].lost_after_s = 3600` |
| Reconnect | gRPC backoff; no heartbeats while backing off | `[relay].backoff_*` |
| Spool bound | append-only segmented spool capped at `spool_max_mb`. When full: stop accepting non-heartbeat items, count `dropped_count`, send `spool_overflow {dropped, first_seq, last_seq}` on reconnect. Heartbeats are never spooled. | `[relay].spool_dir`, `spool_max_mb` |
| Secret in an item or frame | scanned **before** spooling with the shared secret set (section 8.1). On a hit the item is refused, and `capture_refused {seq, location, pattern_id}` is spooled without the content. | shared set |
| Harness frames | an opaque DataPart (`mediaType` from `[relay].frame_media_type`) that the spoke never parses beyond the secret scan | `[relay].frame_media_type` |
| Replay order | per-`spoke_session` monotonic `seq`, oldest first. The hub keeps `hw_seq`; `seq <= hw_seq` is acked as a duplicate; a gap is recorded as loss. | n/a |
| Late items | keep `generated_at`, flagged `late`; the interval stays BLIND | n/a |
| Hub outage | spool and back off; tokens are re-minted on reconnect; the monitor marks spokes BLIND with reason `hub_outage` | n/a |
| Environment ends | SIGTERM: 5 s flush plus `goodbye`. Whether Codespaces or Cloud Shell send SIGTERM is UNVERIFIED. | `[relay].goodbye_flush_s = 5` |
| Resume identity | `spoke_session` is kept in the spool header across a new ephemeral node | n/a |
| **Loopback forward (new)** | `http://127.0.0.1:<[ports].spoke_ingress>/<p>` forwards to the hub's `<p>` over the mesh, **only** for `p ∈ [relay.forward].paths` (vendor default `["/forge/mcp"]`). The spoke attaches a token it mints for that audience and never exposes it. This is how a monitor or manager reaches the forge without a token in any config file (section 10.9). The role comes from the node's role tag (4.3). A spoke-only node's forward reaches the bridge with no role claim and is refused. | `[relay.forward].paths` |
| Terminal output | none, ever | n/a |

---

## 7. One hub monitor, packaged outside MiOS paths

READ: `global_monitor.py:1-12` ("One monitor, not one of many ... it enumerates agents from EVERY harness"). It names vendor harnesses, so it may not live under a MiOS path.
- **Packaging:** the -dev-loop image `ghcr.io/mios-dev/agent-monitor` (D5). MiOS carries only `[monitor].image` and `mios-agent-monitor.container` (hub role only; Law 6 unprivileged; Law 3 bound).
- **Protocol identity (decision):** the monitor is an **MCP host** (clients: forge via the spoke forward or loopback, mios-mcp, dev-loop) and an **A2A client** of the hub. It is not an A2A server; the hub (agent-pipe) is.
- **Data access:** loopback HTTP only (`GET /v1/relay/sessions`, `/v1/events/ws`), with a host-local scoped caller key `{"principal": "hub-monitor", "scope": "relay:read"}` in the existing `caller-keys.json` store (`server.py:695-698`; `access/authn.py:72-110`). The key is minted by `usr/libexec/mios/mios-relay-monitor-key` (M4) and handed over as a podman secret through `Secret=`. It needs no Postgres credential. Honest cost: a static host-local key, revocable (`authn.py:101-104`). **Forge access (rev 5)** does not use this key. It goes through the hub's `monitor` instance, its own node `tag:mios-monitor` (4.3).
- **Verdicts:** observed / BLIND / LOST / ended, each with a reason. The pure verdict function is unit-tested with constructed timestamps. Enumerating real remote agents is **UNTESTED** until a relay capture exists.
- **Fleet slots (corrected in rev 4):** the hub mirrors **ADR 0003 item 1's AGY-manager counter** (`dl-h-manager-counter`, `live_managers.py`: at most 4 managers, at most 2 teamwork trees, AGENTS.md:105-110) as rows. It is never merged with item 14's heavy-lane knob (`ADR0003-dispositions.md` table row 1 and row 14). Revision 3's "item 14 behind the relay" is withdrawn.
- **Forge events:** the monitor receives `forge.event` messages (section 10.6) on its subscription and decides, inside a turn, whether to call forge tools.
- **Phase 2:** a `monitor` subcommand of the bridge binary; the monitor image is then retired.

---

## 8. Capture recorder: scrubbed, refuse-on-secret, PII redacted

The safety property of dropped ADR 0003 item 2 (READ, `0003-dev-loop-self-improvement.md:98-115`): "scrubs home paths and hostnames, writes a `MANIFEST.json` ... and **refuses** on any secret-pattern hit".

| Recorder | Records | Where | Rule |
|---|---|---|---|
| **Hub recorder** (MiOS, M3) | relayed messages and tool I/O as Responses items (T-040 OBS-03, `TASKS.md:1511`: "Record all LLM I/O ... and all tool I/O into the pgvector `session` table ... hash-chaining its entries") | **`session` rows**, kinds `relay_msg` / `relay_tool_io`, chained by `stamp_session` | **Refuse only on a secret hit.** `redact()`'s `is_redacted` also fires on `EMAIL_PATTERN` (`redact.py:12`, `:32-34`), so M3 adds `redact.secret_hit(text) -> (pattern_id, offset) \| None` built from `API_KEY_PATTERNS` (`:4-10`) and `MIOS_SECRET_PATTERN` (`:15`) only. On a hit the record is refused and a `capture_refused` event names the item, field and `pattern_id`, without the content. Email is redacted by DURA-02 on persist, not refused. `$HOME` and `/home/<u>` become `~`; hostnames become `<host>` (rule below). |
| **Bridge recorder** (-dev-loop, D4) | raw vendor frames | `tests/fixtures/transcripts/relay/<name>/` + `MANIFEST.json` | item-2 rules. The negative text names the **kind**, never the matched text (`secret_scan.py:9` no-leak rule): `SECRET IN CAPTURE: <file>:<n> api-secret-key; refusing to write the fixture`. |

Hostname rule (filed by the dispositions, §6 item 5; one rule in both -dev-loop sets): `*.local` (RFC 6762), `*.home.arpa` (RFC 8375), `*.lan`, `*.internal`, the configured hostname, and any `hostname` field whose value is not `<host>`.

### 8.1 One secret rule set, three implementations, parity gates

- **MiOS canonical set:** M3 adds `redact.export_secret_patterns()` (JSON: `id`, `regex`, `flags`).
- **Spoke parity (M6):** the crate embeds `tools/native/mios-spoke/patterns/secret-patterns.json`. `tests/test-secret-pattern-parity.py` asserts that file equals the export, then runs a shared plant corpus through `redact.secret_hit` and `mios-spoke scan` and requires identical `pattern_id` verdicts (this catches regex dialect drift, for example the class at `redact.py:9`).
- **Bridge parity (D4):** D4 pins `bridge/tests/vectors/secret-patterns.mios.json` (MiOS export at the M3 merge commit) and reads `skills/dev-loop-web/assets/secret-patterns.json` (produced by `dl-r-corpus-safety`, which has no deps, so it exists first). `bridge/tests/pattern_parity.rs` requires the bridge set to be a superset of both; a missing kind fails `SECRET PATTERNS DRIFT: capture.rs lacks kind <k>`.
- **Egress refusal (filed, §6 item 6):** D1's spoke client refuses items carrying vendor secret shapes (the same JSON) before they reach the spoke ingress, because MiOS `redact.py` cannot carry every vendor shape (Law 5).
- Honest gap: D4's pinned MiOS copy is refreshed by hand. No live cross-repo check exists.
- **Controls whose inputs exist today:** D4's positive runs on copies of the three real transcripts (`tests/fixtures/transcripts/{chat-question,native-ask,open-blocker}`), which are trimmed (`"input": {}`, `"(elided)"`), with `/home/plantuser/x` and a configured hostname planted into a text item. M3's recorder negative uses a `MIOS_API_TOKEN=` line (`MIOS_SECRET_PATTERN`), so no vendor string enters a MiOS test.
- **Still UNTESTED:** a real cross-host relay run; AGY NDJSON adaptation; a real Codespaces or Cloud Shell stop; a real GitHub webhook delivery; the hosted forge endpoint's real `tools/list`; ADR 0003 items 7, 8, 10, 12, 14, 17, 25, 30.

---

## 9. Baking and supervision per image kind (ADR-0025 phases, Law 12)

READ: ADR-0025 D2 (`adr/0025-core-image-profile.md:158-185`): every image kind is the root pipeline under `MIOS_PROFILE`; the devcontainer is "a rendered thin shim". `Containerfile:39` (`cp /build/tools/native/target/release/mios-* /out/`) and `:57` (`COPY --from=rust-builder /out/* /usr/libexec/mios/`) pick up every `tools/native` crate.

| Artifact | Into the image | Booted host (systemd) | Container kinds |
|---|---|---|---|
| `mios-spoke` | new crate; lands at `/usr/libexec/mios/mios-spoke` | `mios-spoke@<instance>.service` from `[units]` (Law 8; instances per 4.3) | `miosd daemon --profile dev` (M7) |
| mesh client | `[packages.mesh] pkgs = ["tailscale"]` in `[profiles.core]` (9.2: fail-closed at bake) | per archetype, section 9.1 | `mios-mesh` (userspace) under miosd |
| mesh issuer | `[relay.mesh].issuer_image` digest, bound (Law 3) | `mios-mesh-issuer.container`, hub role only | not present |
| **bridge** | **never baked.** `[bridge].image` is a digest pin used only by the Quadlet, in the firstboot tier: **not** bound (9.3; rev 4's "bound, Law 3" is withdrawn, because a bound image is baked) | `mios-agent-bridge.container`, **rendered only for `dev-host`** (9.3); vendor mounts from D8's drop-in | **not present** (decision): the `dev` render has no bridge Quadlet and no bound-images entry (M8 controls d, e). Harness frames go to the hub's bridge (section 1). |
| hub monitor | `[monitor].image` digest, bound | `mios-agent-monitor.container`, hub role only | not present |

- **Law 12:** a spoke with no hub configured degrades open (`state=unconfigured`). It never blocks boot. The bridge is not a MiOS payload.
- **Supervisor (M7):** `miosd daemon --profile <p>` spawns nothing when `/run/systemd/system` exists. Otherwise it spawns `[profiles.<p>].services` from `[supervisor.services.<name>].exec`, with section 6 backoff and shell exit receipts (`main.rs:202-210`, `daemon/mod.rs:41,123-146`).
- **Start points in container kinds:** `boot-mios-systems.sh` (postStart, MiOS `devcontainer.json:204`) launches `miosd daemon --profile dev` detached (M9). mios-bootstrap (`devcontainer.json:230`) and -dev-loop (`devcontainer.json:207`) run that same script, so they inherit the launch but not `containerEnv`. Each repo adds `MIOS_RELAY_SPOOL_DIR=${containerWorkspaceFolder}/.work/spool` itself (M9, D9, B3). MiOS's projector merges unowned keys (`tools/sync-dotfiles.py:286`, `dict(cenv, **env)`; owned keys `mios.toml:10366-10368`).
- **Claude Code cloud session:** the -dev-loop plugin's SessionStart hook runs `miosd daemon --profile dev` in the projection container (D6). The Stop hook posts `suspend` to the spoke. No bridge is installed on the cloud host (rev 4).
- **Budget:** the effect of mesh + spoke on ADR-0025's `budget_seconds = 300` is unmeasured. M8 re-runs ADR-0025 L6's cold-build control.

### 9.3 Which render carries the bridge, and why it is not bound (rev 5)

READ:
- ADR-0025 `[profiles.targets]` (`adr/0025-core-image-profile.md:141-146`): `oci = "full"`, `wsl2 = ["full", "dev"]`, `devcontainer = "dev"`, `cloud = "dev"`, `codespace = "dev"`. `[variants.entries.mios-dev]` gains `profile = ["full","dev"]` (`:152-153`). So `dev` means "developer userspace", in containers and on booted hosts alike. It does not mean "booted dev host".
- **A bound image is a baked image.** `99-postcheck.sh:608-652` (BOUND-IMAGES-RESOLVE) fails with "Image '<ref>' was not baked" for any bound image missing from the baked `bound-images.tsv`. So binding the bridge would bake it, which the decision forbids.
- The existing unbound tier: `[build.bake].firstboot_tokens = ["vllm", "sglang", "crawl4ai", "firecrawl"]` (`mios.toml:7623`). `miosd overlay-bind-images` skips a Quadlet whose `Image=` contains a token (`src/mios-rs/miosd/src/main.rs:1156`) and logs "firstboot tier -- web-pulled at first boot, not bound" (`:1159`). The Law 3 postcheck accepts it as "intentionally unbound" (`99-postcheck.sh:450-461`).

Design:
- **M1 adds `[profiles.dev-host]`** (`extends = ["dev"]`, units = the bridge Quadlet). It appends `"dev-host"` to `[profiles.targets].wsl2` and to `[variants.entries.mios-dev].profile`. No container kind lists it. This is filed as a shape change on top of ADR-0025 L1, and M1 runs after L1.
- **M1 appends `"agent-bridge"` to `firstboot_tokens`.** It matches the `[bridge].image` repository name, and no image in `[build.bake]` contains that substring (READ: `grep -n agent-bridge` on `mios.toml` at `02f0f5e` is empty). The Quadlet pulls by digest on first start.
  - Law 12: a failed pull degrades open. With no bridge running, the harnesses and non-OpenAI nodes report unavailable (5.4).
- **Runtime check (D8):** the drop-in installer refuses unless the resolved profile set contains `dev-host` **and** `/run/systemd/system` exists.
- **Controls (M8):**
  - Positive: the `dev-host` render contains `mios-agent-bridge.container`, and the postcheck prints `mios-agent-bridge.container intentionally unbound`.
  - Negative (d): the Quadlet planted into `[profiles.dev]` → `BRIDGE OUTSIDE DEV-HOST PROFILE: dev`.
  - Negative (e): `"agent-bridge"` removed from `firstboot_tokens` in a copy → `BRIDGE IMAGE BOUND: mios-agent-bridge.container`, with the bound-images set checked for every profile render.

### 9.1 Mesh mode per archetype (decided)

READ: the tailscale RPM ships `tailscaled.service`; MiOS's preset disables it (`90-mios.preset:258`). `mios-adguard-firstboot.service` (`mios.toml:830`) and `mios-ttyd-expose.service:8` order after it. MEASURED: no `[packages.*]` section installs tailscale on main today.

| Archetype | `[relay.mesh].mode` | Unit | Notes |
|---|---|---|---|
| Blade (bare metal) | `kernel` | vendor `tailscaled.service` (TUN, root), enabled by the Blade unit set (T-986) | the spoke dials directly. AdGuard and ttyd-expose keep their tailnet-IP features. |
| Blade guest (NIC-less) | `blade-route` | none; the baked client stays disabled | the spoke dials the hub through its Blade's membership (`TASKS.md:10738`: "the guest is not a peer on this mesh; it is routed over its Blade's membership") |
| everything else (cloud session, Codespace, Cloud Shell, MiOS-DEV, other booted hosts) | `userspace` (vendor default) | `mios-mesh@<instance>.service`: `tailscaled --tun=userspace-networking --statedir=/var/lib/mios/mesh/<instance> --socket=/run/mios/mesh/<instance>.sock` as an unprivileged sysuser, **`Conflicts=tailscaled.service`**; instances per 4.3 | SOCKS5 only. On non-Blade booted hosts, AdGuard and ttyd-expose have no tailnet interface IP. That is a stated limitation, not a silent fallback. |

Double registration is prevented structurally: `Conflicts=` plus the preset, with separate state directories. Moving a host between modes registers a new node, and that is documented.

### 9.2 Core requires the mesh client: repo-fetch failure fails the bake

READ: `06-enable-external-repos.sh:120-123` fetches the repo with `try_fetch ... || true`; `05-repos.sh:120` excludes `tailscale*` elsewhere. Rule: `06`'s `|| true` stays for other profiles. The new phase `automation/NN-mesh-verify.sh` (M8) fails every profile that lists `mesh` with `MESH CLIENT MISSING: tailscale (repo fetch at 06-enable-external-repos.sh:122 failed or package absent)`. Law 12 governs boot, not bake.

---

## 10. GitHub MCP behind the bridge (monitor, manager, reader, reviewer)

### 10.1 Role names aligned to upstream (decided)

| Our role | Upstream name (READ) | Protocol identity |
|---|---|---|
| **manager** (AGY L0: decomposes, dispatches, gates, merges lanes *locally*) | OpenAI Agents SDK "manager agent" ("A manager agent keeps control of the conversation and calls specialist agents through `Agent.as_tool()`", `openai.github.io/openai-agents-python/multi_agent/`); CrewAI hierarchical "manager agent", which "delegates tasks, and validates outcomes" | MCP host (dev-loop, forge); A2A server toward the hub; A2A client toward A2A lanes |
| **monitor** (watches runs, sessions, PRs; relays; commits; opens PRs; never merges) | none of the nine frameworks surveyed (GitHub draft §1.1) defines it, so it is defined by protocol identity | **MCP host** + **A2A client** (decision) |
| **reviewer** | GitHub "Copilot code review" | reads the PR head (section 10.8) |
| lanes | "specialist agents" / "workers" / A2A "remote agents" | never forge clients (section 10.9) |

"Supervisor" and "orchestrator" are never used for the monitor: upstream, both mean the dispatching role, which is our manager.

### 10.2 Upstream: GitHub's hosted MCP endpoint, called with the bridge's own token

READ:
- The hosted endpoint URL is in `github-mcp-server` `docs/remote-server.md:7` (-dev-loop config only; the host is Law 5 material in MiOS).
- Per-request configuration on the hosted server is by header (`remote-server.md:58-75`): `X-MCP-Toolsets`, `X-MCP-Tools` ("Invalid tools will throw an error"), `X-MCP-Readonly`, `X-MCP-Lockdown` ("a best-effort content filter, not a security boundary", `:71`), `X-MCP-Insiders`. `X-MCP-Exclude-Tools` is wired in the v1.12.2 code (`pkg/http/middleware/request_config.go:44`; `headers.go:62-64`) but not documented for the hosted server, so its hosted behaviour is UNVERIFIED and nothing relies on it.
- **Which tokens the hosted endpoint accepts** (the operator asked for primary docs):
  - GitHub's product page (`docs.github.com/en/copilot/how-tos/provide-context/use-mcp/set-up-the-github-mcp-server`, fetched 2026-09-26): "The remote GitHub MCP server uses one-click OAuth authentication by default, but you can also manually configure it to use a personal access token (PAT)". It names **no** GitHub App token type.
  - The server repo's own governance doc at the pin (`docs/policies-and-governance.md:25-27`), under "2. Remote GitHub MCP Server": "**GitHub App Installation Tokens:** Uses a signed JWT to request installation access tokens ... to operate as the application itself", alongside the OAuth authorization-code flow and PATs.
  - The shared HTTP code (the same codebase, `:15-16`: "two deployment modes, both built on the same underlying codebase") accepts both App token types by prefix: `pkg/utils/token.go:28` `"ghu_": TokenTypeUserToServerGitHubAppToken` and `:29` `"ghs_": TokenTypeServerToServerGitHubAppToken // Installation access token for a GitHub App`.
  - **Verdict:** installation tokens (`ghs_`) are accepted according to the upstream repo's documentation and code at `v1.12.2`. GitHub's product documentation does not state it, and the live endpoint has not been measured. **P0 row g** measures it: `initialize` then `tools/list` against the hosted endpoint with a fresh installation token from the MiOS App, expecting HTTP 200 and a non-empty tool list. This needs the App (operator action P-4).
  - **If the hosted endpoint refuses an installation token**, the smallest compliant alternative is: the same App, the same installation token, the same profiles, sent to the pinned `github-mcp-server v1.12.2` binary run by the bridge as a **stdio child** with GitHub App installation auth (`docs/github-app-auth.md`: that mode "is not available for the `http` command", so it must be stdio). The cost is vendoring one upstream Go binary into the bridge image, digest-pinned in `bridge/Containerfile` (created by D1, then owned by D10). That work is conditional lane **D11b-forge-stdio**, run only if P0 row g fails, after D10 and D11 (section 13). A **user-to-server token (`ghu_`) is not an acceptable fallback**: READ `ghappauth.md:15`, a user access token is for when "you want to attribute app activity to a user". The PRs would then be authored by the operator, and the operator cannot approve their own PR (the layer-4 problem in section 10.5).
- Installation tokens expire after one hour (READ, "The installation access token will expire after 1 hour", GitHub Docs "Generating an installation access token for a GitHub App", fetched 2026-09-26). The bridge mints them from the App private key (RS256 JWT), caches them for at most 50 minutes, and never logs or returns them.

### 10.3 PR author identity and GitHub App permissions (least privilege)

The author is a **MiOS GitHub App bot**, registered by the operator (P-4) and installed on `mios-dev/{MiOS,mios-bootstrap,-dev-loop}`. READ `ghappauth.md:11`: "Your app should authenticate as an app installation when you want to attribute app activity to the app."

READ, "Permissions required for GitHub Apps" (docs.github.com, fetched 2026-09-26; `scratchpad/ghperm-body.md`, cited by line; the Tokens column lists `UAT, IAT` for every row below):

| Permission | Level | Why (endpoint, line) |
|---|---|---|
| Pull requests | **write** | create PR `POST /repos/{o}/{r}/pulls` (`:1218`); review `POST .../pulls/{n}/reviews` (`:1228`) and `.../reviews/{id}/events` (`:1232`); reply `POST .../pulls/{n}/comments/{id}/replies` (`:1225`); PR conversation comment `POST .../issues/{n}/comments` (`:1200`, listed under Pull requests with additional permissions) |
| Contents | **read** | `GET .../contents/{path}` (`:979`) |
| Checks | read | `GET .../commits/{ref}/check-runs` (`:833`) |
| Actions | read | `GET .../actions/jobs/{job_id}/logs` (`:591`) |
| Commit statuses | read | `GET .../commits/{ref}/status` (`:913`) |
| Metadata | read | mandatory |

- **No Contents: write**, so the App cannot merge. READ: `PUT /repos/{o}/{r}/pulls/{n}/merge` needs **Contents: write** (`:950`), and so do `POST .../merges` (`:949`) and ref updates (`:936-940`). The draft's layer 3, which was UNVERIFIED, is now READ.
- **Caveat (READ):** `PUT .../pulls/{n}/update-branch` needs only **Pull requests: write** (`:1233`). The App credential could update a PR branch, so the bridge must refuse `update_pull_request_branch` (section 10.4).
- **Consequence (INFERRED):** without Contents: write the App cannot push a head branch. The **monitor pushes the branch** with its existing git credential (in a cloud session, the session's git proxy), then calls forge `create_pull_request`, so the PR is authored by the bot. A manager can open a PR only from a branch that is already pushed; AGY managers do not push (lane contract). That git credential is itself a merge path unless the default branch is protected (section 10.5).
- No Issues, code scanning, notifications or Administration permission is granted. The notifications toolset is dropped, because an installation has no user inbox (critique "wrong" #13). Events come from webhooks instead.

### 10.4 Profiles, tool allowlists and argument guards (bridge, default deny)

Each profile is a fixed set that the bridge sends upstream as `X-MCP-Tools: <exact allowlist>` plus `X-MCP-Lockdown: true` (content filter only; not counted as a control). Every client-supplied `X-MCP-*` header is **stripped**. With a hosted upstream, these headers are the upstream's configuration channel, so a forwarded client header could widen the tool set. The draft's claim that stripping was moot (it assumed a stdio child) no longer holds (critique "wrong" #10). The bridge also filters `tools/list` and refuses `tools/call` outside the profile. That is the load-bearing layer, because it does not depend on the upstream honouring headers.

| Profile | Who (role claim) | Tools |
|---|---|---|
| `monitor` | nodes tagged `tag:mios-monitor` (4.3): the hub monitor and monitor sessions | **read:** `get_me`, `get_file_contents`, `list_commits`, `get_commit`, `list_branches`, `list_pull_requests`, `search_pull_requests`, `search_code`, `pull_request_read` (all methods). **checks/CI:** `get_check_run`, `actions_list`, `actions_get`, `get_job_logs`. **review reply (COMMENT only):** `pull_request_review_write`, `add_comment_to_pending_review`, `add_reply_to_pull_request_comment`, `add_issue_comment` (PR targets only). **PR:** `create_pull_request`. |
| `manager` | nodes tagged `tag:mios-manager` (4.3): AGY L0 managers | the same set (decision). It is a separate profile for audit and revocation only. |
| `reader` | `tag:mios-hub`: agent-pipe (MiOS runtime) | the read and checks/CI groups only |
| (none) | `tag:mios-spoke` only | nothing: `/forge/mcp` refuses the token (D1 control e) |

Argument guards (READ `pkg/github/pullrequests.go:1812` methods `create, submit_pending, delete_pending, resolve_thread, unresolve_thread`; `:1833` event `APPROVE, REQUEST_CHANGES, COMMENT`; `:1860` "create with event" submits immediately):
- `pull_request_review_write`: `method=create` is allowed with `event` absent (a pending review) or `COMMENT`. `method=submit_pending` requires `event=COMMENT`. `delete_pending` is allowed (it only discards the caller's own pending review). `resolve_thread` and `unresolve_thread` are **refused**, because they change review state on threads the operator owns, which is more than a COMMENT right. `APPROVE` and `REQUEST_CHANGES` are refused on both `create` and `submit_pending` (critique "wrong" #12).
- `add_issue_comment`: allowed only when `pull_request_read method=get` on the same number succeeds (issue targets are refused).
- Never in any profile: `merge_pull_request`, `enable_pr_auto_merge`, `update_pull_request_branch`, `update_pull_request`, `create_branch`, `push_files`, `create_or_update_file`, `delete_file`, `create_repository`, `fork_repository`, `resolve_review_thread`, `unresolve_review_thread`, and every tool of the `copilot`, `copilot_issue_intents` and `copilot_spaces` toolsets (for example `request_copilot_review`, `assign_copilot_to_issue`, `create_pull_request_with_copilot`; toolset IDs in `remote-server.md:27-28,54` and `pkg/github/tools.go`, `copilot.go:887`). A control asserts that no advertised tool name contains `copilot` (critique "missing" #10).
- A tool that a newer upstream adds is invisible until the allowlist is reviewed (default deny).
- Annotations are passed through from upstream. The bridge never raises `readOnlyHint`.
- Audit: every `tools/call` is recorded by the bridge (tool, profile, `sub`, repo, PR, result class; never tokens) and relayed as a `relay_tool_io` item, so it lands in the T-040 chain.

### 10.5 "Nobody merges": the barriers, stated honestly

| # | Barrier | Covers | Status |
|---|---|---|---|
| 1 | Bridge profiles (section 10.4): merge-class tools absent, `update_pull_request_branch` refused | the forge path | lane D11 |
| 2 | App lacks Contents: write (`ghperm-body.md:950`) | the forge credential, even if barrier 1 fails | P-4 (operator registers the App) |
| 3 | -dev-loop plugin hook `no-merge.sh` denies `mcp__.+__(merge_pull_request\|enable_pr_auto_merge\|update_pull_request_branch)` in every session that loads the plugin; `guard.sh` denies `gh pr merge`; `.claude/settings.json` `permissions.deny` lists the three host GitHub MCP tools; `tests/test_guard_hooks.py` covers both sides; MiOS `ae9fa7ec6` and mios-bootstrap `6eed348` add a project `.claude/settings.json` deny for the same three tools (no `gh` rule) | the **host-side** GitHub MCP that monitor and manager sessions hold today (critique "wrong" #1 and "missing" #1) | `846164c`, `ae9fa7ec6` and `6eed348` are all **not on main**, only on `origin/claude/dev-loop-iv4399` (`git branch -r --contains`): P-2 |
| 4 | Default-branch ruleset on each repo: require a PR; require CODEOWNERS (the operator) approval; block direct and force pushes; no bypass actors except the operator | the monitor's git credential, `gh api` REST/GraphQL merges, and any path the hooks miss | **UNVERIFIED** (operator setting, P-4). Because PRs are authored by the bot, the operator can approve them. That removes the self-approval problem the critique raised for operator-authored PRs (critique "wrong" #2). |

Known holes in barrier 3 (INFERRED from `846164c`'s `guard.sh` diff, which adds only `gh pr merge`): `gh api -X PUT repos/<o>/<r>/pulls/<n>/merge`, `gh api graphql` with `mergePullRequest` or `enablePullRequestAutoMerge`, raw `curl` to the REST merge endpoint, and `git push <remote> <ref>:main`. They are filed as a row for the dispositions lane that owns `hooks/guard.sh` (`dl-c-guards`), with dictated texts: `dev-loop: gh api merge endpoint is a merge path; the operator merges (AGENTS.md)` and `dev-loop: pushing to the default branch is a merge path; the operator merges (AGENTS.md)`. Barrier 4 is the only complete one, and it is an operator setting nobody here has verified.

### 10.6 Events: App webhooks → bridge over the mesh → A2A `forge.event`

- **Ingress.** GitHub delivers App webhooks to a public HTTPS URL. The mesh's public ingress is **Funnel** on the hub node (`tag:mios-hub`, port 443), which M11 publishes for the single path `/forge/webhook` → `127.0.0.1:[ports].agent_bridge`. Funnel in userspace is UNVERIFIED (P0 row f). The fallback is `mode = kernel` on the hub host for Funnel only, and that would be a new decision.
- **Verification** (READ `ghwh.md:28`): "The hash signature will appear in each delivery as the value of the `X-Hub-Signature-256` header"; `:34` "GitHub uses an HMAC hex digest"; `:38` never use a plain `==`, use a "constant time" comparison. The bridge verifies HMAC-SHA256 over the raw body with the App webhook secret (drop-in mount), compares in constant time, and dedups on `X-GitHub-Delivery`. That value becomes the A2A `messageId`, which the hub's `INBOX DEDUP` covers again.
- **Subscribed events:** `pull_request`, `pull_request_review`, `pull_request_review_comment`, `issue_comment`, `check_suite`, `check_run`, `workflow_run`. Each is covered by a permission in section 10.3.
- **Normalisation (INFERRED):** A2A `Message{role: agent, contextId: "forge:<owner>/<repo>#<pr>", messageId: <delivery id>, parts:[DataPart{type:"forge.event", event:"<kind>.<action>", repo, pr, head_sha, conclusion, actor, url}]}`. No payload body is copied beyond these fields. The vendor event names exist only inside the bridge; MiOS sees the function type `forge.event`. The bridge posts through the local spoke ingress (hub host), so the spool, secret scan and T-040 recording apply.
- **Consumer:** the hub routes `forge.event` to the monitor's subscription. `subscribe_pr_activity` in the Claude Code host is not an upstream tool, and the design does not depend on it.
- **Controls:** GitHub publishes an HMAC test vector (READ `ghwh.md:42-50`: secret `It's a Secret to Everybody`, payload `Hello, World!`, `X-Hub-Signature-256: sha256=757107ea0eb2509fc211221cce984b8a37570b6d7586c22c46f4379c8b043e17`). It is an upstream vector, not a hand-written fake, so the signature positive and negative are runnable now. Normalisation of real payloads is **UNTESTED** until a real delivery is captured, because no App exists yet. A redacted body no longer matches its signature, so a re-signed fixture would be hand-built (critique "missing" #7).

### 10.7 MiOS consumer: agent-pipe is read-only

`mios_mcp.py:85-89,237-271` merges vendor, `/etc`, user and `mios.toml [mcp.servers]` entries and expands `${ENV}` in headers. The draft's `token_env = "MIOS_FORGE_MCP_TOKEN"` would have made a secret a `MIOS_*` variable, which the resolver must emit under Law 9 (referenced ⊆ emitted) and which Law 11 forbids in env files (critique "missing" #5). Rev 4 design, with the SSOT keys added by M1 (the `mios.toml` owner) and not by a separate lane (critique "wrong" #4):

```toml
[mcp.servers.forge]
enabled    = false                       # opt-in; degrades open (Law 12)
transport  = "http"
url        = ""                          # host overlay: the bridge's loopback /forge/mcp
role       = "reader"                    # least privilege for the runtime agent
token_file = "/run/mios/forge/token"     # 0600, owned by the agent-pipe user; tmpfiles (M1)
tier       = "rare"                      # off fan-out workers (worker_mcp_tools, mios.toml:3085)
taint      = "untrusted-content"         # forge text is prompt-injection surface
```

- The token is a file, never an env var, so Laws 9, 10 and 11 do not reach it. `mios_mcp.py` (M13) reads it per request and refuses a file with group or world bits set.
- `usr/libexec/mios/mios-forge-token` (M13, Python) mints a `reader` token for audience `/forge/mcp` from tsidp with the hub node's identity and writes it atomically, mode 0600.
- A vendor-TOML `role` other than `reader` fails M13's test. A host overlay may raise it only in `/etc` (an operator's choice).

### 10.8 Reviewer tailoring: `AGENTS.md` only

READ (`ghdocs/copilot_concepts_agents_code-review.md`, fetched 2026-09-26):
- `:229` code review draws on "`.github/copilot-instructions.md` ..., path-specific `*.instructions.md` ..., `AGENTS.md` for standing rules you want to share across AI tools and agents, and ... skills". `:234` stores `AGENTS.md` at the "Repository root".
- `:193` "Copilot reads repository custom instructions, agent instructions, and agent skills from the head branch ..., not the base branch."

Design:
- **Monitor action P-3:** add a marked block `<!-- review:begin -->` … `<!-- review:end -->` to the root `AGENTS.md` of each repo. The manager/monitor is the only writer of `AGENTS.md` (-dev-loop AGENTS.md:129), and no lane edits it.
  - **MiOS** (vendor-neutral; "the reviewer"): review against `mios.toml [laws]`, especially Law 5 (vendor names/URLs, `[docs].retired_ports`), Law 7 (no literal port/model/IP), Law 8 (derived file changed without its generator), Law 15 (mirrored surface updated in mios-bootstrap or divergence justified), Law 16 (templated types via `usr/share/mios/templates/`), and "a claimed test has a planted negative control that fails".
  - **mios-bootstrap** (vendor-neutral): Law 15 twin map, TOML-first, Law 5 in docs and commit messages, Law 14 (no new PowerShell-as-program).
  - **-dev-loop** (vendor names allowed): two-sided controls, no hand-written fakes, "untested" rather than "proven", lane contract, `validate.sh`.
- Since review reads the **head** branch, a PR can rewrite the rules it is reviewed under. The reviewer is advisory; the operator's approval (barrier 4) is the gate.
- No custom MCP server for code review. Review keeps GitHub's built-in server (draft §3.3), which avoids a public static-secret listener that the mesh-OIDC decision rules out.
- M14 and B4 own only the **controls** for the block (a test file each; M14 also deletes `.github/agents/dev-loop.agent.md`, QB). -dev-loop's block needs no lane; `validate.sh` already gates the file's form.
- The draft's `devloop_mcp.py` `readOnlyHint` lane is **dropped**. Its only consumer was a code-review custom MCP, which the decision removes (critique "wrong" #15 is moot).

### 10.9 Lanes never reach the forge

READ: no lane launcher passes an MCP config (`git grep strict-mcp-config` on `cd87715` is empty), so Claude lanes inherit the user and project MCP scopes. READ, `claude --help` (2.1.283): `--strict-mcp-config  Only use MCP servers from --mcp-config, ignoring all other MCP configurations`. Claude Code's scopes are local, project and user, plus per-invocation `--mcp-config`. There is no "session scope" (critique "missing" #8).

- The forge is registered once for the monitor and manager hosts (D14) as `http://127.0.0.1:<spoke_ingress>/forge/mcp`, a spoke forward with **no token in the config**.
- **D13:** every Claude lane is launched with `--strict-mcp-config --mcp-config skills/dev-loop/assets/lane-mcp.json` (the dev-loop server only). The control inspects the argv that `adapters.py` and `claude_lane.py` build. `--strict-mcp-config` joins `PROBE_FLAGS["claude-code"]` (`adapters.py:59`), so flag drift is caught by `adapters.py probe`.
- **Honest gap:** AGY native subagents have no known equivalent flag (UNTESTED). Any process with the same uid on a spoke can reach the loopback forward, so the spoke mints the node's role token for any local caller. Barriers 1 and 3 still deny merges, and the bridge audit (`sub`, `spoke_session`) makes an out-of-contract PR attributable. A lane-originated `create_pull_request` is detected, not prevented.

### 10.10 Resolution of the GitHub draft's critique (`w032p06ep.output`, "crit")

| # | Critique item | Resolution |
|---|---|---|
| W1 | Host GitHub MCP still grants merge; "four layers" overstated | Barrier 3 (`846164c`, P-2) covers the host MCP. The table in 10.5 scopes each barrier and names the holes. Only barrier 4 is complete, and it is unverified. |
| W2 | Layer 4 fails if PRs are operator-authored | PR author = App bot (decision, 10.3), so the operator can approve. Ruleset settings are listed; they are UNVERIFIED (P-4). |
| W3 | DL-BRIDGE-* collide with D1 | DL-BRIDGE-AUTH is merged into D1 (role claim + aud + passthrough). D1 creates the `forge/mod.rs` and `forge_events/mod.rs` stubs, the Cargo deps and the registration seam, then hands the directories to D11 and D12 down `depends_on` (11.4). |
| W4 | M-FORGE sub-file ownership (`#`) breaks mios.toml / 98-drift-checks serialisation | The `[mcp.servers.forge]` block moves into **M1** (serial owner). The drift check is folded into **M2**'s single pattern. M13 owns only `mios_mcp.py`, the token helper and its test. |
| W5 | Second vendor pattern duplicates `check_vendor_urls` and breaks M2's `grep -c == 1` control | No second pattern (2.1). |
| W6 | M-FORGE plant carries the vendor host literally | Removed. M13's negatives use no vendor string. M2's plant is concatenated (`tests/drift-gate-negatives.sh:4804-4827` style). |
| W7 | `.github/copilot-instructions.md` is a Law 5 leak and unnecessary | Decision: `AGENTS.md` only (10.8, READ `:229-234`). |
| W8 | `dev-loop.agent.md` Law 5 debt re-committed | M14 deletes it and lints `.github/**` (QB). |
| W9 | Wrong cite `AGENTS.md:109-110`; "monitor opens PRs" was INFERRED | The cite is now `AGENTS.md:117-118` at `cd87715`. PR creation by monitor and manager is now an operator decision, so it is no longer inferred. |
| W10 | `X-MCP-*` stripping moot | Not moot with a hosted upstream (10.4). Now a D11 control. |
| W11 | Lockdown is not a boundary | Stated (`remote-server.md:71`); not counted. |
| W12 | Review guard misses methods | Full method × event matrix (10.4). |
| W13 | Notifications advertised but unusable | Dropped from every profile and from the App permissions. |
| W14 | JSON and doc disagree on lanes | This document's §11 table is the single source. `lanes` in the StructuredOutput is derived from it. |
| W15 | `readOnlyHint` split unjustified | The lane is dropped (10.8). The bridge passes upstream annotations through and never raises them. |
| M1 | Deal with the host-side GitHub MCP, with a control | P-2 (`tests/test_guard_hooks.py::TestNoMergeHook`, which fails with the deny planted off, per `846164c`'s message). |
| M2 | Which identity authors PRs; exact permissions from docs | 10.3 (READ, line-cited). |
| M3 | Re-scope DL-BRIDGE-* onto D1 | 11.4 (D1 seam; D11, D12). |
| M4 | M-FORGE after M1/M2; cover mios.d and the Quadlet image ref; one Quadlet or two | M1 holds the block. M2 scans `mios.toml` and `mios.d`. M8's control greps the rendered `mios-agent-bridge.container` for vendor names. There is one Quadlet (2). |
| M5 | Law 11/9 for the token | A token file, not an env var (10.7). |
| M6 | `role="monitor"` gives agent-pipe PR-create | `role = "reader"` (decision), with an M13 control. |
| M7 | Webhook fixture test-double problem | Upstream HMAC vector (runnable). Real-payload normalisation is UNTESTED (10.6). |
| M8 | "Session scope" is not a Claude Code scope | `--strict-mcp-config` + `--mcp-config` (10.9, D13). |
| M9 | Law 5 lint scope for `.github/` | M14 sources `law5.sh` (URL pattern + M12's `check_vendor_names`) over the review block and `.github/**`. |
| M10 | Copilot tools; server-name override | Copilot toolsets are excluded, with a `copilot`-substring control (D11). The name is set by the bridge's own `initialize` (2). |

---

## 11. Lanes

Rules for every lane:
- One repo per lane, with exclusive `owned_paths` among lanes that can run concurrently. A shared file passes only down a strict `depends_on` chain.
- No `git add`, `commit` or `push`, and no edits to `AGENTS.md`, `CLAUDE.md` or `.devloop/`.
- Every control is runnable, and its inputs exist before the lane runs. Controls that need a capture this work produces are marked UNTESTED.
- Paths are repo-relative.

### 11.1 Generated projections: one manager step (MGR-regen), not lanes

`tools/sync-generated.sh` regenerates `automation/lib/globals.{sh,ps1}`, `usr/share/mios/reference/env-baseline.txt` (bump-gated, `98-drift-checks.sh:3358-3388`), `usr/share/mios/ai/v1/metadata.json`, `automation/manifest.json`, `tools/manifest.json`, `usr/share/mios/reference/manual-corpus.tsv` ("it censuses every tracked source file", `sync-generated.sh:185`), the `tool-index.md` MIOS-GEN blocks and `pipe-boundaries.manifest.json` (`check_pipe_boundaries`, `:3190`). No lane owns or commits these. A lane's `just drift-gate` positive runs in a scratch copy after `sync-generated.sh`. After each MiOS merge the manager runs `bash tools/sync-generated.sh` (with `MIOS_ENV_BASELINE_BUMP=1` only when `mios.toml` changed), then `just drift-gate`, and commits the projections itself. `tools/sync-generated.sh` is owned by ADR-0025 L4 and is never edited here.

### 11.2 Monitor and operator actions (preconditions, not lanes)

| id | Who | Action | Gates |
|---|---|---|---|
| **P-1** | monitor | Amend `.devloop/LEDGER.md:47` to "not pushed" (the claimed `live_managers.py` and quota stubs exist in no ref). ADR 0003 item 1 (decided). | `dl-h-manager-counter`, `dl-g-quota` (dispositions), D5 |
| **P-2** | monitor opens the PRs; operator merges | Put `846164c` (no-merge hook, `permissions.deny`, `gh pr merge` deny, tests) on -dev-loop main, and MiOS `ae9fa7ec6` / mios-bootstrap `6eed348` (project `.claude/settings.json` deny) on their mains | D6 (it edits `hooks/hooks.json`, which `846164c` also edits), D11-D14 |
| **P-3** | monitor (the only `AGENTS.md` writer) | Write the review block into each root `AGENTS.md` (10.8). MiOS and bootstrap text is vendor-neutral. | M14, B4 |
| **P-4** | operator | Register the MiOS GitHub App with exactly the section 10.3 permissions and the section 10.6 events; install it on the three repos; set the webhook URL to the hub's Funnel `/forge/webhook`; place the private key and webhook secret on the DEV host at the paths `bridge/config/forge.toml` names; configure default-branch rulesets (10.5 barrier 4) | P0 row g, D11/D12 live use |
| **P-5** | operator | Tailnet policy: tags `mios-hub`/`mios-spoke`/`mios-monitor`/`mios-manager`; `funnel` node attribute for `tag:mios-hub` only; HTTPS + MagicDNS; tsidp app-capability grants for role claims, applied from D1's `bridge/config/tailnet-policy.hujson`; issue the key kinds of 4.3 (spoke-only; spoke+monitor, stored only in the monitor's environment; spoke+manager; persistent per-instance keys `hub`/`monitor`/`manager` for MiOS-DEV) | P0 live rows |
| **MGR-regen** | manager | 11.1, after every MiOS merge | every later MiOS lane |

### 11.3 Lane table

| id | repo | owned_paths | objective | positive control | negative control → expected failure | deps |
|---|---|---|---|---|---|---|
| **P0-mesh-probe** | -dev-loop | `skills/dev-loop/scripts/env/mesh-probe.sh` | **Live, on demand, run by the monitor**, against the hosted tailnet: (a) inbound tailnet TCP in userspace; (b) `tailscale serve` HTTPS in userspace; (c) tsidp `v0.0.15` issuing a non-interactive, audience-bound token **with a role claim** to a tagged node; (d) tailscaled's own DERP client through the cloud proxy; (f) Funnel on the hub node in userspace; (g) the hosted forge endpoint answering `initialize` + `tools/list` with a `ghs_` installation token; (h) two userspace tailscaled instances on one host (distinct state, socket and tags) each obtaining a token whose `role` claim matches its own tag, and a `tag:mios-spoke`-only node obtaining a token with no `role` claim. Writes `mesh-probe.json` for the monitor to review. No test replays its output. | `bash -n mesh-probe.sh` | no join key → `NO JOIN KEY: refusing to report rows`, exit 2; row g with no App key path → `NO APP KEY: row g not measured`, exit 2 (both runnable before any key exists) | none (live rows need P-4, P-5) |
| **M1-ssot-schema** | MiOS | `usr/share/mios/mios.toml`, `usr/libexec/mios/seed-db-config.py`, `usr/share/mios/postgres/schema-init.sql`, `usr/lib/tmpfiles.d/mios-relay.conf`, `usr/lib/sysusers.d/mios-mesh.conf`, `tests/test-relay-outbox.py`, `tests/lib/throwaway_pg.py` | Add `[relay]` (role, heartbeat, blind, lost, backoff, spool, token TTL, goodbye, `frame_media_type`); `[relay.mesh]` (`mode` ∈ userspace/kernel/blade-route, vendor default userspace; login server and hub name empty; tags; `issuer_image` digest); `[relay.expose].paths` (`/a2a`, `/mcp`, `/forge/mcp` and their `/.well-known` metadata); `[relay.funnel].paths = ["/forge/webhook"]`; `[relay.forward].paths = ["/forge/mcp"]`; `[mcp.servers.forge]` (10.7); `[bridge].image`; `[monitor].image`; `[supervisor.services.*]`; `[packages.mesh]`; `[ports].{mesh_socks5,spoke_ingress,agent_bridge}`. Put `mesh`, `mios-mesh@`, `mios-spoke@` in `[profiles.core]`. **Add `[profiles.dev-host]`** (`extends = ["dev"]`, the bridge Quadlet only) and append `dev-host` to `[profiles.targets].wsl2` and `[variants.entries.mios-dev].profile` (9.3). **Append `"agent-bridge"` to `[build.bake].firstboot_tokens`** (`:7623`). Add `[relay.instances.{hub,monitor,manager,node}]` (tag, port keys, state dir; 4.3) and the per-instance `[ports]` keys. Add `[units]` for the templated spoke and mesh (`Conflicts=tailscaled.service`), issuer, bridge and monitor, with only the function-named credential `Volume=`. Add redact entries for `agent_outbox`/`relay_session`, the OIDC `[a2a]` scheme, a derived `[a2a].discover_port`, `[laws]` id 5 `enforced_by` naming both gates, and `port_ssot` (dispositions §3.31 row 7). DDL for `agent_outbox` and `relay_session` only (**no `relay_capture`**); the `session.kind` comment (`:203`) gains `relay_msg \| relay_tool_io`. Tmpfiles for spool, mesh state, issuer state, `agent-bridge/credentials`, and `/run/mios/forge` (0700). Mesh sysuser. No vendor key or path. | `python3 tools/drift-checks.py db-seed-coverage`; `python3 tests/test-relay-outbox.py` (throwaway cluster via `initdb`/`pg_ctl` in `mktemp -d`, socket-only; MEASURED: PG16 at `/usr/lib/postgresql/16/bin`; it **fails** `POSTGRES NOT AVAILABLE`, never skips); `just drift-gate` in a scratch copy | (a) drop `'relay'` from `_CANONICAL_SECTIONS` in a copy → `Section 'relay' is not handled by seed-db-config.py`; (b) a duplicate `idempotency_key` insert without `ON CONFLICT` → `OUTBOX DEDUP BROKEN: 2 rows for key <k>`; (c) `[mcp.servers.forge].role = "monitor"` in a copy → `FORGE ROLE ESCALATION: vendor role monitor` (the assertion lives in `test-relay-outbox.py`'s SSOT section); (d) `dev-host` appended to `[profiles.targets].devcontainer` in a copy → `DEV-HOST PROFILE ON CONTAINER KIND: devcontainer` (same SSOT section) | ADR-0025-L1 |
| **M2-law5-gate** | MiOS | `automation/lib/law5.sh`, `automation/99-postcheck.sh`, `automation/98-drift-checks.sh`, `tests/drift-gate-negatives.sh` | One vendor-URL pattern in `law5.sh`, sourced by both gates. A separate `LAW5_SCAN_FILES` loop covers `mios.toml` (never appended to `SCAN_DIRS`, whose `-d` guard at `:1259` skips files). A missing target is a violation. `mios.d` joins the dirs. Decide the `redact.py:4-10` anchored allowlist entry (2.1 note 3). **(rev 5)** `.devcontainer/Containerfile` joins `LAW5_SCAN_FILES`, with the hash-anchored `LAW5_DEBT` entries for `:69` and `:108` (2.3). | `bash automation/98-drift-checks.sh` green; `grep -c` of the pattern literal under `automation/` = 1; the output names `usr/share/mios/mios.toml` as scanned | (a) concatenated vendor URL appended to `mios.toml`, then restored → `check_vendor_urls` fails naming `usr/share/mios/mios.toml`; (b) `LAW5_SCAN_FILES` pointed at a renamed copy → `LAW5 SCAN TARGET MISSING: usr/share/mios/mios.toml`; (c) a second concatenated vendor URL appended to a copy of `.devcontainer/Containerfile` → `check_vendor_urls` fails naming `.devcontainer/Containerfile:<n>`; (d) the debt line deleted from the copy with its entry kept → `LAW5 DEBT STALE: <hash> .devcontainer/Containerfile` | M1, ADR-0025-L5 |
| **M3-hub-a2a** | MiOS | `usr/lib/mios/agent-pipe/mios_pipe/federation/a2a.py`, `.../federation/relay_ingest.py` (new), `.../federation/relay_auth.py` (new), `usr/lib/mios/agent-pipe/mios_pipe/auth.py`, `usr/lib/mios/agent-pipe/mios_pipe/redact.py`, `usr/lib/mios/agent-pipe/test_mios_relay_hub.py` | Close G-A1..G-A5 (5.1). Per-session `hw_seq`, gap-as-loss, `relay_session.last_seen`, `GET /v1/relay/sessions` (`relay:read`), injected `on_item`. **Routing:** `manager_context_id` → `relay_session` → `agent_outbox` (dispositions §3.8 step 3); harness frames → bridge `/translate`. **Recorder:** T-040 `session` rows through `dbwrite._db_create` (`id = relay:<spoke_session>:<seq>`, kinds `relay_msg`/`relay_tool_io`), dedup **before** stamping, refusal on `redact.secret_hit` only, email redacted. Add `redact.secret_hit` and `redact.export_secret_patterns`; `redact()` unchanged. | `cd usr/lib/mios/agent-pipe && python3 test_mios_relay_hub.py` (spec-shaped A2A frames against `tests/lib/throwaway_pg.py`; drives `inbound_auth_mw` in a Starlette test app; asserts three relayed items give three `session` rows and `audit.verify_session_chain` returns ok) | (a) foreign `aud`, check planted out → `TOKEN AUDIENCE ACCEPTED: aud=<plant>`; (b) same `messageId` twice → `INBOX DEDUP BROKEN`; (c) same `seq` twice with dedup-before-stamp planted out → `CHAIN GAP: session chain_seq <n> missing`; (d) `MIOS_API_TOKEN=` item, refusal planted out → `SECRET PERSISTED: session kind relay_tool_io`; (e) only a `Co-Authored-By: <name> <email>` line, refusal planted onto `is_redacted` → `EMAIL REFUSED AS SECRET`; (f) hub role, `api_require_auth=false`, no token, role gate planted out → `A2A OPEN IN HUB ROLE`; (g) a Message with `manager_context_id`, routing planted out → `UNROUTED CONTRACT UPDATE: no agent_outbox row for <ctx>` | M1 |
| **M4-pipe-events** | MiOS | `usr/lib/mios/agent-pipe/server.py`, `usr/lib/mios/agent-pipe/mios_events.py`, `usr/lib/mios/agent-pipe/mios_webhook.py`, `usr/libexec/mios/mios-relay-monitor-key` (new, Python), `usr/lib/mios/agent-pipe/test_mios_relay_events.py` | Wire `broadcast` as `on_item`. Pass the composed checker at `server.py:4250-4257`. `authenticate()` delegates to `_check_inbound_principal`, fail-closed. `db_pool` to `ingest_webhook`. Idempotent monitor-key minter. | `python3 test_mios_relay_events.py` (one `agent/event` per item; 401 without a key; `relay:read` subscribes; one `agent_inbox` row per webhook; the minter run twice → one `hub-monitor` entry) | (a) plant `if not self.api_key: return True` → `EVENTS AUTH OPEN: unauthenticated subscriber accepted`; (b) plant `db_pool=None` → `WEBHOOK NOT PERSISTED: agent_inbox rows 0 after 1 ingest`; (c) revocation planted out → `REVOKED KEY ACCEPTED` | M3 |
| **M5-mcp-auth** | MiOS | `usr/libexec/mios/mios-mcp-server`, `usr/libexec/mios/mcp-server-runner`, `tests/test-mcp-auth.py` | G-M2, G-M3; keep the loopback bind | `python3 tests/test-mcp-auth.py` (ephemeral port, test-generated JWKS; metadata lists `authorization_servers`; no token → 401 with the header; valid → 200 on `initialize`) | A2A-audience token, check planted out → `TOKEN AUDIENCE ACCEPTED: aud=<plant>` | M1 |
| **M6-spoke** | MiOS | `tools/native/mios-spoke/**` (incl. `patterns/secret-patterns.json`), `tools/native/Cargo.toml`, `tests/test-secret-pattern-parity.py` | The Rust spoke (section 6): ingress, secret refusal, bounded spool, SOCKS5 only, token refresh, SubscribeToTask directives, backoff, goodbye, file-only logging, `scan` subcommand, opaque harness frames, and the **loopback forward** restricted to `[relay.forward].paths` with per-audience tokens; `--instance <i>` reading `[relay.instances.<i>]` (4.3) | `cd tools/native && cargo test -p mios-spoke` (in-process A2A stub hub); `python3 tests/test-secret-pattern-parity.py` | (a) overflow report planted out → `SILENT DROP: <n> items`; (b) planted reorder → `REPLAY ORDER: seq <k+1> before <k>`; (c) `MIOS_API_TOKEN=x`, refusal out → `SECRET IN SPOOL`; (d) `println!` on the heartbeat path → `TERMINAL OUTPUT FROM SPOKE`; (e) delete one pattern → `SECRET PATTERN DRIFT: <id> missing in mios-spoke`; (f) forward request for `/v1/chat/completions` → `UNLISTED FORWARD PATH: /v1/chat/completions`, and it refuses; (g) forward with token attachment planted out → `FORWARD WITHOUT AUDIENCE TOKEN: /forge/mcp`; (h) two instances configured with one state dir → `INSTANCE STATE SHARED: <dir>` | M1, M3, ADR-0025-L4 |
| **M7-supervisor** | MiOS | `src/mios-rs/miosd/src/daemon/services.rs` (new), `src/mios-rs/miosd/src/daemon/mod.rs`, `src/mios-rs/miosd/tests/services.rs` | Supervise `[profiles.<p>].services` in container kinds; defer under systemd; receipts; backoff | `cd src/mios-rs && cargo test -p miosd services` | (a) unknown service → `SUPERVISOR UNKNOWN SERVICE: <plant>`; (b) systemd faked present, defer planted out → `DOUBLE SUPERVISION: <svc>` | M1, ADR-0025-L2 |
| **M8-bake** | MiOS | `Containerfile`, `usr/share/mios/templates/containerfile`, `.devcontainer/Containerfile`, `automation/NN-mesh-verify.sh` (new), `tests/test-mesh-verify.sh`, `usr/lib/systemd/system-preset/90-mios.preset`, `usr/share/mios/mios.toml` (**only** the `[bridge].image` and `[monitor].image` digest values after D1/D5 publish; serial after M1), and the regenerated `mios-spoke@.service`, `mios-mesh@.service`, `mios-mesh-issuer.container`, `mios-agent-bridge.container`, `mios-agent-monitor.container` | Re-render the shim with the `rust-builder` stage (no bridge stage). Mesh-verify phase (9.2). Presets. Regenerate units and Quadlets from SSOT, with the bridge Quadlet present only in the `dev-host` render and unbound (9.3). Re-run the ADR-0025 L6 budget. | `bash automation/97-ssot-lint.sh`; `bash automation/98-drift-checks.sh` (`check_quadlet_privilege` `:1111`; ADR-0025 `check_devcontainer_projection`); `grep -q 'AS rust-builder'` in the shim; `bash tests/test-mesh-verify.sh` (stub `rpm` → 0); `law5.sh` URL + name patterns over the rendered `mios-agent-bridge.container` → zero hits; the core-, full- and dev-profile renders list no `mios-agent-bridge`; the `dev-host` render lists it and the postcheck prints `mios-agent-bridge.container intentionally unbound` | (a) `User=root` in the rendered bridge Quadlet → `check_quadlet_privilege` fails naming it; (b) stub `rpm -q tailscale` → 1 → `MESH CLIENT MISSING: tailscale`; (c) the bridge Quadlet added to the core render → `BRIDGE OUTSIDE DEV-HOST PROFILE: core`; (d) the bridge Quadlet planted into `[profiles.dev]` (the devcontainer/cloud/Codespace render) → `BRIDGE OUTSIDE DEV-HOST PROFILE: dev`; (e) `"agent-bridge"` removed from `firstboot_tokens` in a copy → `BRIDGE IMAGE BOUND: mios-agent-bridge.container` (bound-images set checked for every profile render) | M1, M2, M6, M7, D1 (published), D5 (published), ADR-0025-L1, L3, L4 |
| **M9-devcontainer-start** | MiOS | `.devcontainer/boot-mios-systems.sh`, `.devcontainer/devcontainer.json`, `tests/test-devcontainer-relay.sh` | postStart launches `miosd daemon --profile dev` detached; `containerEnv.MIOS_RELAY_SPOOL_DIR = "${containerWorkspaceFolder}/.work/spool"` (MiOS `.gitignore` is a whitelist, `/*` at `:4`). **If QC = (a):** add the function-named `harness-clis` Feature id under `features` (2.3) | `bash -n`; boot script with a stub `miosd` → one detached `daemon --profile dev`; `python3 tools/sync-dotfiles.py --check` green | (a) foreground call → `BOOT BLOCKS ON SUPERVISOR`; (b) entry deleted → `SPOOL NOT ON WORKSPACE: .devcontainer/devcontainer.json` | M7, M8 |
| **M10-retire-translate** | MiOS | `usr/lib/mios/agent-pipe/mios_pipe/routing/provider_translate.py`, `usr/lib/mios/agent-pipe/mios_provider_translate.py`, `usr/lib/mios/agent-pipe/test_mios_provider_translate.py`, `usr/lib/mios/agent-pipe/mios_pipe/routing/remote_adapter.py`, `usr/lib/mios/agent-pipe/test_mios_interop.py` (remove `:65-195`), `usr/lib/mios/agent-pipe/test_mios_chat.py` (remove `:430-443`), `usr/lib/mios/agent-pipe/test_server_import.py` (drop `:66`), `usr/lib/mios/agent-pipe/server.py` (from M4), `usr/share/mios/mios.toml` (**only** `[drift].denylist` `:2943`; serial after M8), `usr/share/mios/templates/conformance-grandfathered.list` (`:95`), `usr/share/doc/mios/reference/orchestration.md` (`:27`, `:58`), `usr/share/doc/mios/manual/routing.md` (`:1805` block) | Delete the translator, its shim, `remote_adapter.py` (its only non-test caller; `call_remote` appears only at `:24` and `test_mios_interop.py:75`) and the import at `server.py:1326-1337`. Route non-OpenAI `[nodes.*]` to the bridge `/v1` by function; report them unavailable where no bridge runs. Generated references are rewritten by MGR-regen (11.1). `AGY-TASKS.md:1546-1548` stays. | `python3 test_server_import.py`; `python3 test_mios_interop.py`; `python3 test_mios_chat.py`; the `git grep -n -e provider_translate -e remote_adapter` with the generated-file exclusions is empty; `just drift-gate` in a scratch copy | (a) restore the import → `No module named 'mios_provider_translate'`; (b) restore the denylist entry → MGR-regen's scratch run names the stale `mios_provider_translate` (which check fires is UNVERIFIED; the lane records it); (c) non-OpenAI node with no bridge, availability report planted out → `NODE SILENTLY DROPPED: <name>` | D2, M4, M8 |
| **M11-hub-expose** | MiOS | `usr/libexec/mios/mios-mesh-serve` (new, Python), `tests/test-mesh-serve.py` | Render and apply, idempotently, the hub's `serve` config from `[relay.expose].paths` and its Funnel config from `[relay.funnel].paths` (`/forge/webhook` only, port 443), all to `127.0.0.1:[ports].*`. Hub role only. Uses what P0 rows b and f validated. | `python3 tests/test-mesh-serve.py` (fixture SSOT → exact command set; stub `tailscale` records calls; two runs are identical) | (a) non-loopback target → `NON-LOOPBACK SERVE TARGET: <host>`; (b) `/v1/` planted into the rendered set → `UNLISTED PATH EXPOSED: /v1/`; (c) `/a2a` planted into the Funnel set → `NON-WEBHOOK PATH ON PUBLIC INGRESS: /a2a` | M1, P0 (b, f reviewed) |
| **M12-a2o-migrate** | MiOS | `usr/share/mios/agents/**`, `usr/libexec/mios/install-ai-clis.sh`, `usr/libexec/mios/mios-agents-firstboot.sh`, `automation/lib/law5.sh` (serial after M2), `usr/share/mios/mios.toml` (**only** `[frontier]`, `[units."mios-agents.service"]`, `[packages.ai].npm_globals`; serial after M10), `tests/drift-gate-negatives.sh` (serial after M2), `tests/test-workspace-harness-availability.py` (new) | **Unconditional (decided).** Remove the vendor engine, model and effort keys and the vendor CLI installs. Keep the function-named workspace (`code-server` base, `tmux`) and point lane work at the bridge's MCP `lane_*` surface. The workspace launcher (`usr/share/mios/agents/mios-a2o`) probes the bridge's loopback `initialize`. Where no bridge answers (any host without `dev-host`, 5.4), it prints `unavailable: no bridge on this host (profile <p>)` for every harness and never drops them silently. Add `check_vendor_names` to `law5.sh` (scope and exclusions in 2.2; `.devcontainer/Containerfile` under 2.3's debt entries). | `bash automation/98-drift-checks.sh` with `check_vendor_names` at zero hits; `podman build --target` of the workspace image is **not** run (no image builds in lanes); a static check that `usr/share/mios/agents/Containerfile` has no `npm install -g` and no vendor binary install; `python3 tests/test-workspace-harness-availability.py` (a loopback stub bridge → `lane_*` listed available; no listener, `MIOS_PROFILE=full` → every harness listed `unavailable: no bridge on this host (profile full)`) | (a) concatenated plant `orch_engine = "cl""aude"` in a `mios.toml` copy → `check_vendor_names` fails naming `usr/share/mios/mios.toml`; (b) the unavailable report planted out → `HARNESS SILENTLY ABSENT: profile full` | M2, M10, **D10** (every removed value exists in -dev-loop first) |
| **M13-forge-consumer** | MiOS | `usr/lib/mios/agent-pipe/mios_mcp.py`, `usr/libexec/mios/mios-forge-token` (new, Python), `usr/lib/mios/agent-pipe/test_mios_forge_mcp.py` | `token_file` support in `mios_mcp.py` (read per request; refuse group/world bits; header `Bearer <file contents>`; never an env var). The token helper mints `reader` tokens for `/forge/mcp` from tsidp and writes them atomically at 0600. | `python3 test_mios_forge_mcp.py`: `mcp.forge` resolves disabled by default; with `url` and a 0600 temp token file the rendered request carries the file's bearer; the helper, with a stub issuer, writes mode 0600 and requests `role=reader`, `resource=<url>` | (a) token file 0644 → `FORGE TOKEN FILE READABLE: mode 0644`, request refused; (b) a `token_env` key planted → `FORGE TOKEN IN ENV: token_env`; (c) the helper asking for `role=monitor` (plant) → `FORGE ROLE ESCALATION: helper requested monitor` | M1 |
| **M14-review-hygiene** | MiOS | `.github/agents/dev-loop.agent.md` (delete, per QB), `tests/test-review-tailoring.py` | Controls for P-3's MiOS review block, plus removal of the dangling vendor-named agent file | `python3 tests/test-review-tailoring.py`: `AGENTS.md` has exactly one `review:begin/end` block; every "Law N" cited in it exists in `mios.toml [laws]`; `law5.sh` URL + name patterns give zero hits over the block and over `.github/**` | (a) a concatenated vendor reviewer product name planted into a copy of the block → Law 5 fails naming `AGENTS.md:<n>`; (b) "Law 17" cited → `UNKNOWN LAW CITED: 17`; (c) the deleted agent file restored → the `.github/**` scan fails naming `.github/agents/dev-loop.agent.md` | M2, M12, P-3 |
| **M15-devcontainer-vendor-out** (conditional: QC = (a)) | MiOS | `.devcontainer/Containerfile`, `usr/share/mios/templates/containerfile` (whichever of the two ADR-0025 L4 makes the shim's source; the lane confirms before claiming), `automation/lib/law5.sh` (**only** the two `LAW5_DEBT` entries), `tests/test-devcontainer-vendor-free.sh` (new) | Drop `.devcontainer/Containerfile:69` and `:103-110` (2.3) and remove their `LAW5_DEBT` entries in the same change, so the stale-debt check never goes red between two merges. Runs after M8 (last shim owner) and M12 (last `law5.sh` owner), which breaks the M8 → M10 → M12 cycle that folding this into M8 would create. | `bash automation/98-drift-checks.sh` with zero `LAW5_DEBT` entries; `bash tests/test-devcontainer-vendor-free.sh` (no `npm install -g` and no installer fetch in the shim; `python3 tools/sync-dotfiles.py --check` green) | (a) the `:69` line restored in a copy → `check_vendor_names` fails naming `.devcontainer/Containerfile:<n>`; (b) one `LAW5_DEBT` entry left behind → `LAW5 DEBT STALE: <hash> .devcontainer/Containerfile` | M8, M12, D15 (published), M9 |
| **D1-bridge-core** | -dev-loop | `bridge/Cargo.toml`, `bridge/src/{main,mcp,oai,auth,spoke_client,modules}.rs`, `bridge/src/forge/mod.rs` (stub; handed to D11), `bridge/src/forge_events/mod.rs` (stub; handed to D12), `bridge/config/defaults.toml`, `bridge/config/tailnet-policy.hujson` (new, 4.3), `bridge/tests/core.rs`, `bridge/tests/policy.rs` (new), `bridge/Containerfile` (handed to D10), `.github/workflows/agent-bridge-image.yml` | Rust static bridge: MCP `lane_open/send/close`; loopback OpenAI `/v1` facade; protected-resource metadata per resource (`/mcp`, `/forge/mcp`); JWT `iss`/`aud`/`exp` plus **`role` claim** (absorbs the draft's DL-BRIDGE-AUTH); the registration seam (`modules.rs`) and Cargo deps (`hmac`, `sha2`, `subtle`, `jsonwebtoken`, an HTTPS client) the forge modules need; credentials only from mounted paths; the spoke client refuses vendor secret shapes on egress (dispositions §6 item 6); publishes `ghcr.io/mios-dev/agent-bridge` | `cd bridge && cargo test --release`; `ldd` → "not a dynamic executable" | (a) foreign `aud` → `TOKEN AUDIENCE ACCEPTED: aud=<plant>`; (b) inbound bearer forwarded upstream (plant) → `TOKEN PASSTHROUGH: inbound bearer seen upstream`; (c) token without `role` accepted on `/forge/mcp` (plant) → `ROLE CLAIM MISSING ACCEPTED`; (d) a planted vendor key shape sent to the spoke ingress with the egress check out → `VENDOR SECRET SENT TO SPOKE: <kind>`; (e) a token with no `role` claim (the `tag:mios-spoke`-only shape of 4.3) sent to `/forge/mcp` `tools/list`, refusal planted out → `SPOKE-ONLY CALLER GRANTED: <profile>`; (f) a grant for `tag:mios-spoke` planted into `tailnet-policy.hujson` → `SPOKE TAG GRANTED ROLE: tag:mios-spoke -> <role>` (`policy.rs`; positive: each role tag maps to exactly one role) | none |
| **D2-translate** | -dev-loop | `bridge/src/adapters/{openai,anthropic,google}.rs`, `bridge/tests/translate_vectors.rs`, `bridge/tests/vectors/provider_translate/**` | Port `provider_translate.py` | vectors = MiOS `test_mios_provider_translate.py` and `test_mios_chat.py:430-443` at `02f0f5e` (they exist; M10 deletes them only after D2) | dropped `tool_result` → `TRANSLATION LOSS: tool_result <id> missing after round trip` | D1 |
| **D3-harness-adapters** | -dev-loop | `bridge/src/adapters/{claude_code,agy,codespaces,cloud_shell}.rs`, `bridge/src/translate_endpoint.rs`, `bridge/tests/replay_harness.rs` | Harness adapters to Responses items; lifecycle notices; the hub-side `/translate` endpoint for frames from spokes; the **final hop** (dispositions §3.8 step 5): append a relayed `contract-update/v1` to the manager's `<run>/contract-updates.md` | replay of the three real transcripts → an ordered item sequence (`tool_use (id,name)` → `function_call (call_id,name)` at the same position; `tool_result` → `function_call_output` with matching `call_id`; text keeps role and order); the same frames posted to `/translate` give the same sequence; a contract-update Message appends one line to a temp `contract-updates.md`. AGY, Codespaces, Cloud Shell are **UNTESTED**. | (a) dropped `tool_use` → `TRANSLATION LOSS: tool_use <id> missing`; (b) swapped calls → `ORDER LOSS: call <id> at <i>, expected <j>`; (c) append planted out → `CONTRACT UPDATE NOT APPENDED: <lane_id>` | D1 |
| **D4-capture** | -dev-loop | `bridge/src/capture.rs`, `bridge/tests/capture.rs`, `bridge/tests/pattern_parity.rs`, `bridge/tests/vectors/secret-patterns.mios.json` | Bridge recorder (section 8): scrub `$HOME`, `/home/<u>`, hostnames (the 8 rule); `MANIFEST.json`; refuse on a secret hit; pattern set ⊇ MiOS export ∪ `skills/dev-loop-web/assets/secret-patterns.json` (read-only input) | capture copies of the three real transcripts with `/home/plantuser/x` and `blade-devloop-planted.home.arpa` planted: every sha256 matches the manifest, the output has `~/x` and `<host>`, and neither plant remains; the parity test passes | (a) `sk-ant-DEVLOOP-PLANTED-CAPTURE` appended to a copy → `SECRET IN CAPTURE: <file>:<n> api-secret-key; refusing to write the fixture`; (b) home scrub out → `UNSCRUBBED HOME PATH: <file>:<n>`; (c) hostname scrub out → `UNSCRUBBED HOSTNAME: <file>:<n>`; (d) one kind deleted from the bridge set → `SECRET PATTERNS DRIFT: capture.rs lacks kind <k>` | D1, M3, dl-r-corpus-safety |
| **D5-hub-monitor** | -dev-loop | `skills/dev-loop/scripts/global_monitor.py`, `monitor/Containerfile`, `.github/workflows/agent-monitor-image.yml`, `tests/test_global_monitor_relay.py` | `--relay` source over loopback with the key from the podman secret file; forge calls through the hub's `monitor` instance forward (its own node `tag:mios-monitor`, 4.3), never with the `relay:read` key; verdicts with reasons; **fleet slot rows = item 1's counter** (reads `live_managers.py`'s output); `forge.event` rows; image publish | `python3 -m unittest tests.test_global_monitor_relay` (pure verdict function; loopback stub with spec-shaped rows; a stub `live_managers.py --json` with 3 live managers → 3 slot rows). Real remote enumeration is **UNTESTED**. | (a) stale peer returned clean → `BLIND REPORTED CLEAN: peer <id>`; (b) stub 401 with the BLIND-on-401 rule planted out → `UNAUTHORIZED READ REPORTED CLEAN`; (c) the heavy-lane knob counted as a manager slot (plant) → `FLEET SLOTS MIXED: item 14 counted as manager` | M3, M4, dl-h-manager-counter, P-1 |
| **D6-hooks** | -dev-loop | `hooks/spoke-notify.sh` (new), `hooks/hooks.json` (new SessionStart and Stop entries only), `tests/test_spoke_notify_hook.py` | SessionStart: `miosd daemon --profile dev` in the projection container (no bridge install; rev 4). Stop: post `suspend` to the spoke ingress; never block. | stdin = a Stop-hook JSON object `{"stop_hook_active": false, "transcript_path": "<a real fixture in tests/fixtures/transcripts/>"}`, built the way `tests/test_stop_gate.py:42-52` drives `stop-gate.sh`; a loopback listener → exit 0 and exactly one `suspend` carrying the transcript's session; `hooks/hooks.json` loads as JSON and still contains the `no-merge.sh` entry | (a) planted `exit 2` → `HOOK BLOCKS STOP`; (b) no listener → exit 0 within the timeout; a planted blocking connect → `HOOK HANGS ON DEAD SPOKE`; (c) the `no-merge.sh` entry dropped in the edit → `NO-MERGE HOOK LOST: hooks.json` | M6, M7, P-2, the session-start lanes of `SPIKE-dev-loop-self-improvement.md:566` (merged first) |
| **D7-mirror** | -dev-loop | `.devcontainer/Containerfile` | Byte-copy M8's shim (Law 15) | `python3 -m unittest tests.test_devcontainer_mirror` | one-byte edit in a temp copy → fails naming `.devcontainer/Containerfile` | M8, ADR-0025-L7; **M15 and D9 if QC = (a)** |
| **D8-bridge-install** | -dev-loop | `skills/dev-loop/scripts/env/bridge-install.sh`, `tests/test_bridge_install.py` | **Booted DEV hosts only** (rev 4): write `/etc/containers/systemd/mios-agent-bridge.container.d/50-credentials.conf` with read-only `Volume=` lines built from `bridge/config/defaults.toml` (harness keyrings) and `bridge/config/forge.toml` (App private key, webhook secret), under a `--root` prefix for tests. Refuses to run unless the resolved profile set contains `dev-host` **and** `/run/systemd/system` exists (9.3). Never writes under `/usr`. No container-kind install. | `python3 -m unittest tests.test_bridge_install` (the drop-in parses as a Quadlet `[Container]` section; every `Volume=` ends `:ro`; the App key and webhook secret paths are present) | (a) planted `:rw` → `CREDENTIALS MOUNTED WRITABLE: <path>`; (b) planted target under `<root>/usr/` → `DROP-IN OUTSIDE /etc`; (c) run with profile `dev` (a container kind), check planted out → `BRIDGE INSTALLED OUTSIDE DEV-HOST PROFILE: dev`; (d) `dev-host` with no `/run/systemd/system` under `--root`, check planted out → `BRIDGE INSTALLED WITHOUT SYSTEMD` | D1, D11 |
| **D9-devcontainer-spool** | -dev-loop | `.devcontainer/devcontainer.json`, `.gitignore` | `containerEnv.MIOS_RELAY_SPOOL_DIR = "${containerWorkspaceFolder}/.work/spool"`; `.work/` in `.gitignore` (not a whitelist today). **If QC = (a):** the `harness-clis` Feature id under `features` | `json.load`; `sh skills/dev-loop/scripts/validate.sh`; `git check-ignore .work/spool/x` succeeds | entry deleted → `SPOOL NOT ON WORKSPACE: .devcontainer/devcontainer.json` | M9 (same env name) |
| **D10-a2o-settings** | -dev-loop | `bridge/config/a2o.toml`, `bridge/Containerfile` (handed from D1), `bridge/tests/a2o_config.rs`, `bridge/tests/vectors/a2o.mios-02f0f5e.toml` | Receive the A2O vendor settings MiOS drops: the engine, model and effort keys (MiOS `mios.toml:5560-5590`, `:1100-1146` at `02f0f5e`) and the harness CLI installs (the agents `Containerfile:28,36`, `[packages.ai].npm_globals` `:6818-6826`), as a harness stage of the bridge image. Whether agy installs cleanly into the image is UNVERIFIED; if it does not, the stage records it and `setup-antigravity.sh` on the DEV host stays the path. | `cd bridge && cargo test a2o_config` (every key in the pinned vector exists in `a2o.toml` with the same default) | one key deleted from `a2o.toml` → `A2O SETTING LOST: <key>` | D1 |
| **D11-forge** | -dev-loop | `bridge/src/forge/**` (handed from D1), `bridge/tests/forge/**`, `bridge/config/forge.toml` | Forge module (10.2-10.4): upstream = hosted endpoint over HTTPS with an installation token minted from the App key (RS256 JWT, 50 min cache); per-profile `X-MCP-Tools`/`X-MCP-Lockdown` set by the bridge; client `X-MCP-*` stripped; `tools/list` filter; `tools/call` refusal and argument guards; `serverInfo.name = "forge"`; audit items. If P0 row g fails, the stdio-child alternative (10.2) is conditional lane **D11b**, not a new design. | `cargo test -p bridge forge::` against a pinned tool-name vector extracted from github-mcp-server `v1.12.2` `README.md` at `85598ba` (`bridge/tests/forge/vectors/tools-v1.12.2.txt`, which exists upstream before the lane): the `monitor` profile advertises `create_pull_request` and `pull_request_read` and no merge-class tool; `reader` has no write tool; an in-test HTTPS stub records the upstream headers (the stub is hand-built, so real-endpoint behaviour is **UNTESTED** until P0 row g) | (a) `merge_pull_request` planted into `forge.toml` → `MERGE TOOL EXPOSED: merge_pull_request in profile monitor`; (b) `submit_pending` with `event:"APPROVE"`, guard planted out → `NON-COMMENT REVIEW FORWARDED: APPROVE`; (c) `create` with `event:"REQUEST_CHANGES"`, guard out → `NON-COMMENT REVIEW FORWARDED: REQUEST_CHANGES`; (d) a client `X-MCP-Tools: merge_pull_request` header, stripping planted out → `CLIENT TOOLSET HEADER FORWARDED: X-MCP-Tools`; (e) any advertised name containing `copilot` → `VENDOR REVIEWER TOOL EXPOSED: <name>`; (f) `update_pull_request_branch` planted in → `MERGE TOOL EXPOSED: update_pull_request_branch in profile manager`; (g) installation token echoed in a tool result (plant) → `UPSTREAM TOKEN RETURNED TO CLIENT` | D1, P-2 |
| **D11b-forge-stdio** (conditional: only if P0 row g fails) | -dev-loop | `bridge/Containerfile` (handed from D10), `bridge/src/forge/upstream_stdio.rs` (new; created after D11 has merged, since D11 owns `bridge/src/forge/**`), `bridge/tests/forge_stdio.rs` | Vendor the github-mcp-server `v1.12.2` binary into the bridge image by digest, and run it as a stdio child with GitHub App installation auth (10.2). Same profiles, guards and audit as D11, with the upstream swapped behind one trait. | `cd bridge && cargo test forge_stdio` with the pinned binary run in `--help`/`initialize` mode (a real upstream binary, not a fake); `grep` for the pinned digest in `bridge/Containerfile` | (a) the digest replaced by a tag in `bridge/Containerfile` → `UNPINNED UPSTREAM BINARY: bridge/Containerfile:<n>`; (b) the child started with the token in argv (plant) → `UPSTREAM TOKEN IN ARGV`; (c) D11's negative (a) re-run against the stdio upstream → `MERGE TOOL EXPOSED` | D10, D11, P0 (row g reviewed as failed) |
| **D12-forge-events** | -dev-loop | `bridge/src/forge_events/**` (handed from D1), `bridge/tests/forge_events/**` | Webhook ingress on `/forge/webhook` (10.6): HMAC-SHA256 over the raw body, constant-time compare, dedup on `X-GitHub-Delivery`, normalise to `forge.event`, post through the local spoke ingress | the GitHub Docs vector (`ghwh.md:42-50`) verifies; a verified delivery yields exactly one A2A Message whose `messageId` is the delivery id. Normalisation of real payloads is **UNTESTED** (no App yet). | (a) one body byte flipped → rejected, zero Messages; with verification planted out → `UNSIGNED DELIVERY ACCEPTED`; (b) the comparison replaced by `==` (plant) → a source check fails `NON-CONSTANT-TIME SIGNATURE COMPARE: forge_events/verify.rs:<n>`; (c) the same delivery id twice → one Message; dedup planted out → `DUPLICATE DELIVERY RELAYED: <id>` | D1, P-2 |
| **D13-lane-mcp-isolation** | -dev-loop | `skills/dev-loop/scripts/adapters.py`, `skills/dev-loop/scripts/claude_lane.py`, `skills/dev-loop/assets/lane-mcp.json`, `tests/test_lane_mcp_isolation.py` | Every Claude lane gets `--strict-mcp-config --mcp-config <lane-mcp.json>` (dev-loop server only). `--strict-mcp-config` joins `PROBE_FLAGS["claude-code"]` (`adapters.py:59`). AGY subagents: UNTESTED (no known flag). | `python3 -m unittest tests.test_lane_mcp_isolation` (the argv built by both launchers carries both flags; `lane-mcp.json` loads and lists only `dev-loop`); `sh skills/dev-loop/scripts/validate.sh` | (a) flag removed from one launcher → `LANE INHERITS HOST MCP: claude_lane.py argv lacks --strict-mcp-config`; (b) `forge` added to `lane-mcp.json` → `FORGE IN LANE MCP CONFIG` | P-2, **dl-g-quota** (last dispositions lane owning `adapters.py`/`claude_lane.py`) |
| **D14-register-forge** | -dev-loop | `skills/dev-loop/scripts/register-mcp.sh`, `tests/test_register_mcp.py` | `--forge` adds a `forge` entry of type `http` with URL `http://127.0.0.1:<spoke_ingress>/forge/mcp` (the port read from the MiOS SSOT name, not a literal) for claude and agy, with **no** `Authorization` header or token | in a temp HOME: the entry is written, other servers are untouched, and the JSON loads | (a) planted literal bearer → `TOKEN IN MCP CONFIG: forge`; (b) planted literal port → `LITERAL PORT IN MCP CONFIG: forge` | D13, M6 (port name) |
| **D15-harness-feature** (conditional: QC = (a)) | -dev-loop | `features/harness-clis/devcontainer-feature.json`, `features/harness-clis/install.sh`, `tests/test_harness_feature.py`, `.github/workflows/devcontainer-features.yml` | A devcontainer Feature (containers.dev Features spec) installing the vendor CLIs that MiOS's shim drops (2.3): the npm packages from MiOS `.devcontainer/Containerfile:69` and agy through a fetch that refuses non-script payloads, as MiOS `fetch-installer.sh` does. Published under a function-named id. Publishing through the Features CLI is UNVERIFIED. | `json.load` of the feature JSON; `sh -n install.sh`; `python3 -m unittest tests.test_harness_feature` (stub `npm` and stub fetch on PATH record exactly the expected installs; the final `agy --version` runs) | (a) the stub fetch returns an HTML page → `NON-SCRIPT INSTALLER REFUSED`; (b) the stub `npm` exits 1 → the install exits non-zero with `HARNESS CLI INSTALL FAILED: <pkg>` (fails, never skips) | none |
| **B1-profile** | mios-bootstrap | `etc/mios/profile.toml`, `tests/test-relay-profile.py` | Fix the stale `mcp_registry` (`:71`); installer fields for `[relay].role` and the `[relay.mesh]` hub name and login server (no secrets) | `python3 tests/test-relay-profile.py` | old path planted → `STALE MCP REGISTRY PATH: profile.toml:71` | M1 |
| **B2-mirror** | mios-bootstrap | `.devcontainer/Containerfile` | Byte-copy M8's shim | `tools/sync-bootstrap.py --check`, run from MiOS | one-byte change → fails naming `.devcontainer/Containerfile` | M8, ADR-0025-L7; **M15 and B3 if QC = (a)** |
| **B3-devcontainer-spool** | mios-bootstrap | `.devcontainer/devcontainer.json`, `tests/test-devcontainer-spool.py` | The same `containerEnv` entry (`.gitignore` whitelist `/*` at `:6`). **If QC = (a):** the same `features` entry | `json.load`; MiOS `tools/sync-dotfiles.py --check` against this checkout | entry deleted → `SPOOL NOT ON WORKSPACE: .devcontainer/devcontainer.json` | M9 |
| **B4-review-hygiene** | mios-bootstrap | `tests/test-review-tailoring.py` | Controls for P-3's bootstrap review block (vendor-neutral; Law 15 twin map) | the test sources `automation/lib/law5.sh` from `$MIOS_ROOT` (default `/workspaces/MiOS`): one block, cited laws exist in MiOS `[laws]`, zero Law 5 hits | (a) concatenated vendor name planted into a copy → Law 5 fails naming `AGENTS.md:<n>`; (b) `$MIOS_ROOT` absent → `MIOS CHECKOUT MISSING: /workspaces/MiOS` (fails, never skips) | M2, M12, P-3 |

**Model policy (AGENTS.md):** M3, M6, M7, D1, D2, D3, D11 are heavy coding and run `opus --effort xhigh`, one at a time. M1, M2, M4, M5, M8-M15, D4-D10, D11b, D12-D15, B1-B4 run `sonnet --effort medium`. P0 is live, run by the monitor. MGR-regen and P-1..P-5 are not lanes.

### 11.4 How the GitHub draft's lanes were re-scoped (no owned_paths collisions)

| Draft lane | Rev 4 | Why |
|---|---|---|
| DL-BRIDGE-AUTH (`bridge/src/auth/**`) | merged into **D1** (`auth.rs` + role claim; control (c)) | the same module as D1's `auth.rs`; D1 already carried aud and passthrough (critique W3) |
| DL-BRIDGE-FORGE | **D11**, `bridge/src/forge/**` handed from D1's stub | D1 owns `main.rs`, `Cargo.toml`, `Containerfile` and the seam, so D11 needs no D1 path |
| DL-BRIDGE-EVENTS | **D12**, `bridge/src/forge_events/**` handed from D1's stub | same; D11 and D12 are disjoint and can run in parallel |
| DL-REVIEW-DOCS | dropped; the review block is P-3; the `devloop_mcp.py` annotation is dropped | AGENTS.md-only decision; `devloop_mcp.py` stays with `dl-e-merge` alone |
| DL-REGISTER | **D14** (`register-mcp.sh`) + **D13** (lane isolation) | the real Claude Code mechanism; D13 queues behind the dispositions chain on `adapters.py`/`claude_lane.py` |
| M-FORGE | SSOT block in **M1**; pattern in **M2**; consumer in **M13** | path-granular ownership; one mios.toml owner; one Law 5 pattern |
| M-REVIEW-DOCS | **P-3** + **M14** | AGENTS.md-only; lanes never edit AGENTS.md |
| B-REVIEW-DOCS | **P-3** + **B4** | same |

---

## 12. ADR 0003 disposition as it touches this work

- **Item 1: decided.** The monitor amends `.devloop/LEDGER.md:47` to "not pushed" (P-1). The counter is built fresh as `dl-h-manager-counter` (`live_managers.py`, `agy_host.sh`, `tests/test_live_managers.py`; dispositions §4). D5 mirrors it as fleet slot rows.
- **Item 3: kept.** Owned by dispositions lane `dl-a-hygiene`.
- **Item 4: kept, and its AGENTS.md half has landed.** -dev-loop `origin/main` `cd87715`, `AGENTS.md:190` reads "the monitor blocks on `scripts/job.py wait`" (the same line revision 3 cited as `:182` at `f05f60b`); `job.py:347` defines `wait`.
- **Item 2: dropped.** Its safety property lives in the recorders and parity gates (section 8).
- **Items 5-8: kept, with the MiOS ties from `ADR0003-dispositions.md` §3.5-3.8** (replacing revision 3's ties):
  - **5** (retire `contracts.py`): ORCH-02 (`ROADMAP.md:611`, `LISTEN`/`NOTIFY` "without HTTP polling loops") and T-517 (`TASKS.md:6032`, "insert into PostgreSQL `agent_inbox`").
  - **6** (one lane contract): ADR-0007:39 ("all SSOT-generated") and Law 8, with the five surfaces **generated** by `render_lane_contract.py`.
  - **7** (report fields): a tie to the **form** only: MiOS `CLAUDE.md` "OpenAI-format schemas, globally", T-223 (`TASKS.md:3094`), LANG-04 (`ROADMAP.md:370`). No MiOS row names `host_state_changes` or `base_sha`.
  - **8** (`contract_updates` as a relay message): T-517, T-518 (`TASKS.md:6040`), ORCH-02. Addressing is implemented here: M3's routing hop (section 5.2) and D3's final hop.
- **Items 9-31:** per `scratchpad/ADR0003-dispositions.md`. This SPIKE uses rows 9 (A2A TaskState mapping), 14 (the heavy-lane knob, **separate** from the fleet slots), 26 (typed verdict as MCP `outputSchema`) and 30: exit **69** `EX_UNAVAILABLE` in claude_lane (75 is taken: `claude_lane.py:194,684-686,1198`) and HTTP 429 + `Retry-After` at the relay. Revision 3's `EX_TEMPFAIL` is withdrawn. It also uses lane `dl-r-corpus-safety` (a D4 dependency).
- **Filed for the dispositions owner (from this SPIKE):** the `guard.sh` merge-path rows for `dl-c-guards` (section 10.5), and D13's position after `dl-g-quota` on `adapters.py`/`claude_lane.py`.

---

## 13. Collisions (explicit)

ADR-0025 D7 (`adr/0025-core-image-profile.md:249-262`): "`mios.toml` has exactly one owner". L1 = `mios.toml`, `seed-db-config.py`, `templates/containerfile`; L2 = `miosd/src/**`; L3 = `Containerfile`, `build.sh`, `packages.sh`; L4 = `.devcontainer/Containerfile`, `mios-containerfile-render/**`, `tools/sync-generated.sh`; L5 = `tools/drift-checks.py`, `98-drift-checks.sh`, `tests/drift-gate-negatives.sh`; L6 = `.devcontainer/post-start.sh`, `mios-profile-extend`; L7 = the mirrors and `cloud-fedora-setup.sh`.

| Shared path | Other owner | This work | Order |
|---|---|---|---|
| `usr/share/mios/mios.toml` | ADR-0025 L1 | M1 → M8 (digests) → M10 (denylist line) → M12 (A2O keys) | strict serial: L1 → M1 → M8 → M10 → M12; MGR-regen after each |
| `seed-db-config.py`, `schema-init.sql` | L1 (seed) | M1 | serial after L1 |
| `templates/containerfile`, `Containerfile`, `.devcontainer/Containerfile` (MiOS) | L1, L3, L4 | M8 → M15 (conditional) | serial after L1, L3, L4 |
| `src/mios-rs/miosd/src/**` | L2 | M7 | serial after L2 (dispositions §3.31 row 1 also queues there) |
| `tools/native/Cargo.toml` | L4 | M6 | serial after L4 |
| `98-drift-checks.sh`, `tests/drift-gate-negatives.sh`, `automation/lib/law5.sh` | L5 | M2 → M12 → M15 (`law5.sh` debt entries only, if QC = (a)); M14 and B4 read only | serial after L5 |
| `usr/lib/mios/agent-pipe/server.py` | none | M4 → M10 | serial |
| `mios_pipe/redact.py`, `mios_pipe/auth.py` | none | M3 | exclusive |
| `mios_mcp.py` | none found | M13 | exclusive |
| `.github/agents/dev-loop.agent.md` (MiOS) | none | M14 | exclusive |
| root `AGENTS.md` (all three) | the manager/monitor | P-3 only | no lane |
| generated projections | every file-changing lane | none | MGR-regen only |
| MiOS and bootstrap `.devcontainer/devcontainer.json` | edge-to-edge lanes (`SPIKE-edge-to-edge-global.md:289-294`) | M9, B3 (`containerEnv` entry only) | serial with those lanes, whichever is scheduled first |
| -dev-loop `bridge/Containerfile` | none | D1 → D10 → D11b (conditional) | serial |
| -dev-loop `bridge/src/forge/**` | none | D1 (stub) → D11 → D11b (conditional; one new file only) | serial hand-off |
| ADR-0025 `[profiles]` shape, `dev-userspace` phase | L1, L4 | M1 (`dev-host`, `firstboot_tokens`), 2.3 filed change | L1 → M1; L4 carries the vendor lines verbatim, never into `automation/` |
| `automation/lib/law5.sh` `LAW5_DEBT` entries | L5 | M2 (adds) → M12 → M15 (removes, if QC = (a)) | serial |
| MiOS, -dev-loop, bootstrap `devcontainer.json` `features` | edge-to-edge lanes | M9, D9, B3 (if QC = (a)) | after D15 is published |
| -dev-loop `bridge/src/forge/mod.rs`, `bridge/src/forge_events/mod.rs` | none | D1 (stub) → D11 / D12 | serial hand-off |
| -dev-loop `adapters.py`, `claude_lane.py` | dispositions chain b-report → c-guards → c-dispatch → d-invariants → e-merge → f-integrate → g-quota | D13 | after `dl-g-quota` |
| -dev-loop `hooks/hooks.json` | `846164c` (P-2); session-start lanes (`SPIKE-dev-loop-self-improvement.md:52-57`, `:566`) | D6 | after P-2 and those lanes; new entries only; the `no-merge.sh` entry is preserved (D6 control c) |
| -dev-loop `hooks/guard.sh` | `846164c`, then `dl-c-guards` | none (filed row) | n/a |
| -dev-loop `register-mcp.sh` | none found | D14 | exclusive |
| -dev-loop `.devcontainer/devcontainer.json`, `.gitignore` | none | D9 | exclusive |
| -dev-loop and bootstrap `.devcontainer/Containerfile` | L7 | D7, B2 | serial after L7 |
| -dev-loop `global_monitor.py`, `bridge/**`, `monitor/**` | excluded by the dispositions lanes (§4 ownership rule) | D1-D5, D10-D12 | exclusive |

---

## 14. `critic_relay` items: re-verified at the rev 4 baselines

| # | Critique item (`w1ypid9bh.output` `critic_relay`) | Status in rev 4 | Evidence |
|---|---|---|---|
| W1 | -dev-loop baseline stale; item 4 landed | **Resolved; re-baselined again** to `cd87715` | `git diff --stat f05f60b cd87715` = `AGENTS.md \| 8 +`; `AGENTS.md:190` (section 12) |
| W2 | M10 misses `remote_adapter.py:15` and forced surfaces; `mios.toml:2943` collision | **Resolved** (rev 3 scope kept) | M10 owned_paths; the `mios.toml` chain in section 13; generated files via MGR-regen (11.1) |
| W3 | Law 5 leak via vendor `Volume=` and a baked binary | **Resolved, tightened**: the bridge is never baked and not installed in container kinds (decision) | sections 2 and 9; D8 control (c); M8 control (c) |
| W4 | "No MiOS file carries a vendor key" false | **Resolved, now acted on**: M12 is unconditional, D10 receives the values | section 2.2 |
| W5 | Refusal keyed on `is_redacted` (fires on email) | **Resolved** | `redact.secret_hit`; M3 negative (e) |
| W6 | D6/D3/D4 controls could not fail | **Resolved** | D6 stdin object (`test_stop_gate.py:42-52`); D3 ordered ids + `ORDER LOSS`; D4 plants home path and hostname |
| W7 | P0 parser test circular | **Resolved** | P0 keeps only `bash -n` and the keyless negatives, now two: rows g and join |
| W8 | DERP overclaimed | **Resolved** | 3.2: curl measured, tailscaled's DERP UNVERIFIED (P0 d) |
| W9 | M3/M4 ownership; JWT rejected by the prefix gate | **Resolved** | M3 owns `auth.py` + `relay_auth.py` + `relay_ingest.py`; M4 wires `server.py:4250-4257`; M3 negative (f) |
| W10 | G-M1 had no lane; tsidp not run | **Resolved, extended**: M11 now also renders the Funnel path | M11; tsidp Quadlet (4.2). The critique's "no release tag" was rejected with evidence in rev 3 (ghcr tags `v0.0.1`…`v0.0.15`, MEASURED). |
| W11 | Other repos' devcontainers do not inherit the spool env | **Resolved** | M9, D9, B3; `sync-dotfiles.py:286` |
| W12 | M2 can pass vacuously via the `-d` guard | **Resolved** | `LAW5_SCAN_FILES` loop; M2 negative (b) |
| M1 | A2O overlap unaddressed | **Resolved by decision**: migrate | M12 + D10 (section 2.2) |
| M2 | Monitor auth and data access | **Resolved** | section 7 (loopback, scoped revocable key, no Postgres credential) |
| M3 | No secret parity gate | **Resolved; texts aligned with the dispositions** | section 8.1 (M6 parity; D4 `pattern_parity.rs` with `SECRET PATTERNS DRIFT`) |
| M4 | D6 vs the session-start lanes on `hooks.json` | **Resolved, extended**: D6 is also after P-2 (`846164c` edits `hooks.json`) | section 13; D6 control (c). The critique's citation `ADR0003-dispositions.md:566` was corrected in rev 3 to `SPIKE-dev-loop-self-improvement.md:566`. |
| M5 | Booted hosts: which daemon, double registration | **Resolved by decision** | 9.1 archetype table |
| M6 | Repo-fetch failure for `[packages.mesh]` | **Resolved** | 9.2 (fail-closed bake, `MESH CLIENT MISSING`) |

### 14.1 Revision 5 critique (rev 4 → rev 5)

| # | Item | Status | Where |
|---|---|---|---|
| W1 | Bridge in `[profiles.dev]` reaches devcontainer, cloud and Codespace renders; Law 3 bound image | **Resolved.** `dev-host` profile. Bound = baked (READ `99-postcheck.sh:608-652`), so the bridge is unbound through `firstboot_tokens`. M8 (d, e); D8 (c, d); M1 (d). | 9.3 |
| W2 | Monitor and manager lack forge roles; spoke-only callers | **Resolved.** One role tag per node; hub instances; monitor container = its own node; D1 (e, f); P0 h. | 4.3, 10.4 |
| W3 | `schema-init.sql:202/:200` | **Rejected** with `grep -n` at `02f0f5e` and `cfa98ab03` (`201:`, `203:`) | 5.2 |
| Missing 1 | Vendor CLIs in `.devcontainer/Containerfile:69,103-110`; ADR-0025 `:135`; M2 scope | **Resolved to a decision point.** Hash-anchored debt gate now (M2); ADR-0025 L1/L4 filed change; QC with lanes D15, M15, M9, D9, B3 and a stated order | 2.2, 2.3, 15 |
| Missing 2 | Who edits `bridge/Containerfile` for the stdio fallback | **Resolved.** D11b, after D10 and D11 | 10.2, 11.3, 13 |
| Missing 3 | Workspace on a `full` host | **Resolved.** M12 reports harnesses unavailable; control (b) | 5.4, M12 |

---

## 15. Operator questions

**Closed in revision 5 (operator, 2026-09-26):** QA -> (a) WAN-gateway Blade terminates public ACME HTTPS for `/forge/webhook` only, hub serves mesh TLS from `[relay.expose]`, issuer falls back to the whois-based Rust issuer; filed as a T-986 prerequisite row. QB -> (a) M14 deletes `.github/agents/dev-loop.agent.md`. QC -> (a) D15 publishes a function-named -dev-loop devcontainer Feature; M9/D9/B3 reference it; M15 drops the vendor CLI lines; ADR-0025 `dev-userspace` installs the venv and code-server only. The option text below is kept for the record.


- **QA. At T-986, headscale lacks Serve and Funnel.** READ, headscale `v0.29.4` `docs/about/features.md:43-44`: `- [ ] Funnel` and `- [ ] Serve`. The decision says spokes change only the login server. That holds for spokes, but the hub's `tailscale serve` HTTPS (`/a2a`, `/mcp`, `/forge/mcp`), the Funnel webhook ingress, and tsidp (a tsnet app documented for Tailscale tailnets) all need a replacement at the swap. Nothing is built for this now.
  - (a) **Recommended.** File it as a T-986 prerequisite row. At the swap, the singleton WAN-gateway Blade terminates public HTTPS (ACME) for `/forge/webhook` only. Hub resources are served with TLS on the mesh by the hub itself, from `[relay.expose]`. The issuer falls back to the whois-based Rust issuer (section 4.2), whose `whois` is client-side LocalAPI (INFERRED to work under headscale; unmeasured).
  - (b) Keep the hosted tailnet for the relay's public-facing pieces (webhook ingress, issuer) after T-986, and move only the Blade fabric to headscale.
  - (c) Wait for headscale to ship Serve/Funnel, and keep the hosted tailnet until it does.
- **QB. `.github/agents/dev-loop.agent.md` in MiOS.** It names vendor products (`:6`) and loads a skill path that does not exist. The AGENTS.md-only decision covers review tailoring, not custom agents, so deleting it is a small extension of that decision.
  - (a) **Recommended.** M14 deletes it. The dev-loop entry for GitHub-side agents lives in -dev-loop, where vendor names are allowed.
  - (b) M14 rewrites it vendor-neutrally and points it at a real path.
  - (c) Keep it as stated Law 5 debt.
- **QC. Vendor CLI installs in the one shared dev image** (MiOS `.devcontainer/Containerfile:69,103-110`, mirrored to all three repos; section 2.3). The A2O decision moved vendor CLI installs to -dev-loop for the war-room. Does it also cover the dev image?
  - (a) **Recommended.** Yes. D15 publishes a function-named -dev-loop devcontainer Feature. M9/D9/B3 reference it. M15 drops the lines, and ADR-0025's `dev-userspace` phase installs the venv and code-server only. Order as in 2.3 step 4.
  - (b) No. Keep them in the shim as operator-accepted Law 5 debt, gated by M2's hash-anchored entries. They never move into `automation/` or `mios.toml`.
  - (c) Remove them from every devcontainer, and let each session install harnesses through the -dev-loop plugin's SessionStart (`setup-antigravity.sh` already provisions agy on the host).

Closed in revision 4: coordinator (hosted now, headscale later), bridge profile (dev only), Blades/guests/userspace split, A2O (migrate), capture store (T-040 `session` rows), ADR 0003 item 1, every GitHub MCP choice (upstream, author identity, events, tailoring, role rights, role names). Not a question but a measured branch: whether the hosted endpoint accepts a `ghs_` token (P0 row g). If it does not, D11 takes the stdio-child alternative (10.2), which keeps every decided property.

---

## 16. Honest gaps

- Unmeasured: userspace inbound, `tailscale serve` in userspace, **Funnel in userspace**, tsidp tokens with role claims for tagged nodes, and tailscaled's DERP client through the cloud proxy (P0 a-d, f). M11 exposes nothing before those rows are reviewed.
- **The hosted forge endpoint's acceptance of an installation token is READ in upstream code and docs, but not in GitHub's product docs, and it is unmeasured** (P0 g).
- **"Nobody merges" is not enforced on -dev-loop main today.** `846164c` is unmerged (P-2). Its hook misses `gh api` merges, raw REST, GraphQL and pushes to the default branch (10.5). The complete barrier (rulesets) is an unverified operator setting.
- A lane on the same uid as a monitor can reach the spoke's forge forward. Claude lanes are isolated by D13; AGY subagents are UNTESTED. A lane PR would be detected by audit, not prevented.
- A PR can change the `AGENTS.md` rules it is reviewed under, because the reviewer reads the head branch (10.8). The reviewer is advisory.
- Userspace join in Codespaces, Cloud Shell and MiOS-DEV is unmeasured. Only the cloud session was probed, and only to login-URL issuance, plus a curl DERP upgrade.
- Whether Codespaces and Cloud Shell send SIGTERM is UNVERIFIED.
- The core-profile budget effect of mesh + spoke is unmeasured.
- D4's pinned MiOS pattern copy can drift between refreshes.
- The monitor uses a host-local static scoped key (section 7).
- On non-Blade booted hosts, AdGuard and ttyd-expose lose their tailnet-IP features (userspace mode).
- M10's denylist negative does not yet know which gate fires.
- Whether agy installs into the bridge image is UNVERIFIED (D10).
- Every agent-facing replay (cross-host relay, AGY NDJSON, real webhook payloads, the hosted `tools/list`) is UNTESTED until a real capture exists.
- The cloud-session lifetime evidence is one measurement (AGENTS.md:185-191).
- (rev 5) Several userspace tailscaled instances on one host (4.3) are unmeasured (P0 h), and so is the tsidp grant syntax for role claims (P0 c).
- (rev 5) A cloud environment's auth key is shared by all its sessions, so a forge role is per environment, not per session (4.3).
- (rev 5) The bridge is pulled on first start (firstboot tier), so a dev host with no egress at that moment has no bridge until a later start. It degrades open, and the harnesses report unavailable.
- (rev 5) Until QC is answered, the shared dev image keeps vendor CLI installs as gated debt (2.3).

## 17. Sources

- Upstream, fetched this session:
  - A2A 1.0.0: https://a2a-protocol.org/v1.0.0/specification/ (§3.1.6, §3.3.1, §3.5.2, §4.1.3, §4.6.2)
  - MCP 2025-11-25 authorization: https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization
  - Podman Quadlet drop-ins, v5.2.0: https://raw.githubusercontent.com/containers/podman/v5.2.0/docs/source/markdown/podman-systemd.unit.5.md (52-61)
  - gRPC backoff v1.66.0; Kubernetes node status v1.33 (URLs in section 6)
  - Tailscale KB (unversioned; client 1.102.4 measured): 1112, 1111, 1085, 1160, 1581, **1223 Funnel (validated Jan 20, 2026)**
  - tsidp README (main) and ghcr tags (MEASURED): `v0.0.15` = `sha256:cae91835375efcbf75ecb8f9520e3472cda946e3ca9af1df3bce9540902f289e`
  - **headscale `v0.29.4` (`8106636c7f8d`) `docs/about/features.md:10,25,26,43,44`** (https://raw.githubusercontent.com/juanfont/headscale/v0.29.4/docs/about/features.md)
  - **github-mcp-server `v1.12.2` (`85598ba6e125`):** `docs/remote-server.md:7,27-28,54,58-75`; `docs/policies-and-governance.md:15-16,25-27`; `docs/github-app-auth.md`; `pkg/utils/token.go:24-30`; `pkg/http/headers/headers.go:53-66`; `pkg/http/middleware/request_config.go:34,44`; `pkg/github/pullrequests.go:1812,1833,1860`; `pkg/github/server.go:111`
  - **GitHub Docs (fetched 2026-09-26; github/docs main `18945a31a4f2`):** "Setting up the GitHub MCP server" (OAuth/PAT statement); "Permissions required for GitHub Apps" (`scratchpad/ghperm-body.md:591,833,913,936-950,979,1200,1218,1225,1228,1232,1233`); "Validating webhook deliveries" (`scratchpad/ghwh.md:28,34,38,42-50`); "About authentication with a GitHub App" (`scratchpad/ghappauth.md:11,15`); "Generating an installation access token for a GitHub App" (1-hour expiry); "About GitHub Copilot code review" (`scratchpad/ghdocs/copilot_concepts_agents_code-review.md:193,229-234`)
  - Claude Code CLI 2.1.283 `--help` (`--strict-mcp-config`, `--mcp-config`), run locally
  - Codespaces timeout and lifecycle; Cloud Shell limits (section 3.2)
- Repos: MiOS `02f0f5e`, -dev-loop `cd87715` (plus unmerged `846164c`), mios-bootstrap `37584c0`; branch-only MiOS `ae9fa7ec6`/`cfa98ab03` and mios-bootstrap `6eed348` (rev 5, read with `git branch -r --contains` and `git diff --stat`); `scratchpad/ADR0003-dispositions.md` rev 4.
- Measurements: `scratchpad/ts/tsd.log:60-72`, `scratchpad/ts/derp.err`, the ghcr tag and digest queries, GitHub API PR list for mios-dev/-dev-loop (#30 closed at head `244ad99`). No tailnet was joined and no GitHub App exists.
