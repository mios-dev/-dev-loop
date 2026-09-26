# ADR 0003: dispositions for items 1-31, with the relay decisions applied (rev 5)

Source ADR: `/home/user/-dev-loop/docs/decisions/0003-dev-loop-self-improvement.md` (status `proposed`).
**Pins (re-pinned in rev 4):** every `-dev-loop` file:line cite is `origin/main` **cd87715** (merge of PR #30,
head `244ad99`; `git show origin/main:<path>`). `git diff --stat f05f60b cd87715` = `AGENTS.md | 8 ++++++++`
(the legibility-drain bullet inserted at :109-116), so every AGENTS.md line cite after :108 moves by +8 (the rev 3
`AGENTS.md:182` is now **:190**) and every other -dev-loop cite, including `.devloop/LEDGER.md:47` (file still 188
lines), is unchanged. Every MiOS cite is MiOS `origin/main` **02f0f5e** (still the tip on re-fetch); mios-bootstrap
`origin/main` **37584c0** (still the tip). Read 2026-09-26. **Rev 5 re-fetch:** all three `origin/main` tips unchanged (`cd87715`, `02f0f5e`, `37584c0`);
the local MiOS checkout sits on `claude/dev-loop-iv4399` (`cfa98ab`), and `git diff --quiet 02f0f5e cfa98ab --
audit.py schema-init.sql dbwrite.py` is clean, so the §0 capture cites read the same on both.

**Correction to the rev 4 task framing (READ, git + GitHub API):** the no-merge enforcement (`hooks/no-merge.sh`,
`permissions.deny` in `.claude/settings.json`, `gh pr merge` in `hooks/guard.sh`, `tests/test_guard_hooks.py`) is
commit **846164c** on `origin/claude/dev-loop-iv4399`, *after* PR #30 was merged. PR #30 merged head `244ad99`
("docs(agents): the automated legibility drain"), and `git log origin/main..origin/claude/dev-loop-iv4399` lists
exactly `846164c`. No PR carries it yet. So "nobody merges" is **not** enforced on -dev-loop main today; it is a
rule plus an unmerged commit. This document treats it as precondition P-2 (§4), not as a fact on main.

Upstream pins (each fetched this session, quotes verbatim):
- A2A **1.0.0**: `https://a2a-protocol.org/v1.0.0/specification/` (not `/latest`).
- MCP **2026-07-28**, **2025-11-25** and **2025-06-18**: `modelcontextprotocol/modelcontextprotocol@ab3a39c13bd2`
  `docs/specification/<ver>/...`.
- openai/codex `@e72da2b53805`; openai/openai-agents-python `@588826c5be27`;
  anthropics/claude-agent-sdk-python `@36f95486ee9f`; tree-sitter/tree-sitter-bash `v0.25.0` (`56b54c61fb48`);
  astral-sh/ruff `@869cb447ff57`; reviewdog/reviewdog `@418ae09bc492`; github/docs `@18945a31a4f2`;
  freebsd/freebsd-src `@f492ef8318f5` `include/sysexits.h`; git docs **2.43.0** (`https://git-scm.com/docs/<page>/2.43.0`);
  PostgreSQL **17** (`https://www.postgresql.org/docs/17/explicit-locking.html`); RFC 9110; RFC 6585; RFC 6762
  (`.local`); RFC 8375 (`home.arpa`).

Labels: **READ** = seen in a file or pinned upstream page, quoted. **INFERRED** = my judgement. **UNTESTED** =
no real capture exists yet for that control.

## 0. Binding inputs applied in this revision

### 0.0 Rev 4 inputs (operator, 2026-09-26, question UI; binding on top of everything below)

- **Item 1 (decided):** amend `.devloop/LEDGER.md:47` to "not pushed" and build the manager counter fresh as lane
  `dl-h-manager-counter`. The amendment is a **monitor action** (AGENTS.md: "The manager is the only writer to
  shared state (`AGENTS.md`, `.devloop/`, merges)"), recorded as P-1 (§4). Former Q1 is closed.
- **Captures (decided):** EXTEND MiOS T-040 hash-chained `session` rows with kinds `relay_msg` / `relay_tool_io`;
  **no `relay_capture` table**. Former Q2 is closed. Evidence that this needs no DDL is in §0 below.
- **Relay facts this document must stay consistent with:** hosted tailnet coordinator now (headscale on a Blade
  when T-986 lands); bridge = pinned container on booted hosts in the DEV profile only, never baked; Blades run
  kernel-mode tailscaled, other images the userspace mesh service with `Conflicts=tailscaled`; the A2O war-room
  **migrates** (SPIKE Q4 answered: lane M12 runs; vendor keys and CLI installs move to -dev-loop, into a SPIKE
  lane this document does not own).
- **GitHub MCP (SPIKE-owned section):** the bridge calls GitHub's hosted MCP endpoint with its own token; PR
  author = a MiOS GitHub App bot without Contents:write; events = HMAC-verified App webhooks normalised to A2A
  `forge.event`; Copilot review tailoring = `AGENTS.md` **only**; monitor and manager get read + COMMENT-only
  review reply + checks read + create PR; agent-pipe read-only; **nobody merges**. None of this adds an ADR 0003
  item. Its only contact with the lanes below is path ordering (§4 P-2, and `devloop_mcp.py`, §0.1).

Operator, 2026-09-26 (question UI): envelope = A2A 1.0 carrying OpenAI Responses-shaped items, MCP for tools;
hub core = MiOS's existing A2A federation (`usr/lib/mios/agent-pipe/mios_pipe/federation/a2a.py`, `agent_inbox`
at `usr/share/mios/postgres/schema-init.sql:1490`, a new `agent_outbox`) + `mios-mcp`, **not** a new relayd hub;
-dev-loop ships only the vendor **bridge** (Rust static binary + OCI image); mesh VPN in userspace mode;
per-session tokens from the mesh OIDC issuer (MCP authorization profile, audience checks, no passthrough); miosd
supervises `[profiles.<p>].services`; one hub monitor, thin spokes, silent spoke = **BLIND**; the relay records
relayed messages and tool I/O as the capture source **with item-2 safety** (scrub home paths and hostnames,
refuse on any secret-pattern hit), and agent-facing controls stay UNTESTED until a matching capture exists.

Earlier and still binding: items 1, 3, 4 keep; 2 dropped (its safety property now lives in the relay
recorder); 5-8 kept only with a cited MiOS roadmap/ADR/TASKS tie; 9-31 decided by copying upstream patterns.

Consequences of the capture decision:
- Item 2's safety property is **not lost**: it moves to the recorders, and the -dev-loop fixture corpus gets a
  standing gate (lane `dl-r-corpus-safety`) so that no producer (bridge recorder or a hand copy) lands a fixture
  with a secret, an unscrubbed home path, or an unscrubbed hostname.
- **Secret rule sets (rev 2's "one pattern list" claim is withdrawn).** There are three today, not one:
  (a) -dev-loop `skills/dev-loop-web/scripts/secret_scan.py:30-43` `PATTERNS` (12 kinds);
  (b) the bridge recorder dictated by the relay SPIKE, lane D4 (`bridge/src/capture.rs`, `SPIKE-monitor-relay.md:410`, rev 3);
  (c) MiOS `usr/lib/mios/agent-pipe/mios_pipe/redact.py:4-15` (`API_KEY_PATTERNS`, `EMAIL_PATTERN`,
  `MIOS_SECRET_PATTERN`) for the hub recorder (`SPIKE-monitor-relay.md:296`, rev 3). SPIKE rev 3 §8.1 (:299-317) adds a fourth, the
  Rust spoke (M6), held to MiOS's set by `tests/test-secret-pattern-parity.py`; it is MiOS-side and outside this
  document's lanes.
  Resolution: (a) and (b) become **one** set inside -dev-loop. `dl-r-corpus-safety` generates
  `skills/dev-loop-web/assets/secret-patterns.json` from `PATTERNS` and guards it with a regenerate-and-diff check.
  D4 embeds that file and carries a parity test (a SPIKE change, §6). (c) stays separate **by design**: Law 5
  keeps vendor key shapes out of MiOS files, so the hub recognises MiOS-shaped secrets (`MIOS_SECRET_PATTERN`)
  and the bridge refuses vendor shapes on the egress leg before a frame reaches a spoke (SPIKE change, §6).
  READ `secret_scan.py:9`: "A finding prints its location and kind, never the matched text, so the scan cannot
  leak what it found." That property is kept in both -dev-loop sets.
- **Where the hub recorder writes (DECIDED rev 4: extend T-040).** MiOS T-040 (OBS-03, status done,
  `TASKS.md:1509-1516`) already records "all LLM I/O (prompt + completion) and all tool I/O into the pgvector
  `session` table" and makes the log "tamper-evident by hash-chaining its entries through T-034". The recording
  gate is `mios_pipe/routing/chat.py:21` `_record_active`; rows are `kind` `llm_io`/`tool_io` (`chat.py:58`);
  they are hash-chained by `SessionChainer`, implemented at `mios_pipe/observability/audit.py:153` with the
  process-wide instance `_SESSION_CHAINER` at `:195` and the entry point `stamp_session` at `:197-198`, called
  from the one session write path `mios_pipe/dbwrite.py:77-78` (`mios_audit.py` is only the shim the tests import;
  tests `test_mios_audit.py:449-470`, "Unit tests for T-040 (OBS-03 record-and-replay determinism + session hash
  chaining)"). Relayed items become `session` rows of kind
  `relay_msg` (A2A Message / Responses message items) and `relay_tool_io` (function_call + function_call_output
  pairs), written through the same chainer. READ facts that make this a no-DDL change:
  - `schema-init.sql:203` declares `kind text` with no CHECK constraint or enum (comment lists
    "hermes | cron | cli | delegate | mcp"), so new kinds need only the comment updated.
  - The chain columns already exist on `session`: `schema-init.sql:653-655` (`chain_seq`, `prev_hash`,
    `chain_hash`; `chain_hash` is the column `verify_session_chain`, `audit.py:200-219`, checks against).
  - T-040's chat replay selects `kind = 'llm_io' OR kind = 'tool_io'` only (`chat.py:758-760`), so relay rows can
    never be served into a chat replay by accident. Relay replay needs its own query (SPIKE M3).
  The `relay_capture` table (SPIKE rev 3 :221, :296, M1 DDL :395, M3 negative :397) is
  not created (§6 item 8).

  **Requirements on SPIKE M3 (not read facts; nothing in the code does these today):**
  - *R-1, refuse before stamping.* `SessionChainer.stamp` (`audit.py:173-193`) has no secret check, and no
    existing refusal runs before it. M3 must run the secret refusal **before** `stamp_session`, so a refused item
    never takes a `chain_seq` and the chain has no hole to explain. Negative: `SECRET PERSISTED: session kind
    relay_tool_io` (§6 change 8).
  - *R-2, single writer of the chain head.* The chain head lives in memory in one process: `audit.py:154`
    ("In-memory chain head for the session table"), the singleton at `:195`, seeded once from the DB head at
    `:244-265` (`seed_session_from_db`, called at startup from `server.py:789`). No DB constraint backs it:
    `schema-init.sql:653-655` adds the columns with no UNIQUE index or sequence on `session.chain_seq` (READ,
    `grep -n "UNIQUE\|chain" schema-init.sql`: no session chain index). A relay writer in any other process
    (hub monitor, a separate ingest worker, the bridge) would seed from the same head and write duplicate
    `chain_seq` values, forking the chain. So `relay_ingest` runs **inside the agent-pipe process** and writes
    through `dbwrite.py`, which reaches `_SESSION_CHAINER` via `stamp_session`. The only alternative is a DB-side
    sequence or advisory lock for the head, which is DDL, and that reopens the "no DDL" decision; it needs the
    operator. INFERRED: the in-process route is the compliant one.
  - *R-2 negative (runnable, M3):* two `SessionChainer` instances seeded from the same head, each stamping one
    row, then a fork check over the rows → `SESSION CHAIN FORK: duplicate chain_seq <n>`. READ: today's
    `verify_session_chain` (`audit.py:200-219`) has no duplicate-seq check; a fork shows only as a broken link
    at the second row (`first_broken_seq`), so M3 adds the named check. Positive: one instance stamping both rows
    → verify `ok: True`, no fork reported.

### 0.1 Open conflicts with `SPIKE-monitor-relay.md` (rev 2's "no longer disagree" is withdrawn)

Neither document goes to the operator until the SPIKE owner applies §6 (this lane cannot write the SPIKE). The
conflicts:

Line numbers are **SPIKE revision 3** (514 lines, read this revision); rev 3 of this document cited revision 2
lines, which moved.

| SPIKE rev 3 line | SPIKE says | This document says | Why |
|---|---|---|---|
| §11 :430 | item 4's AGENTS.md half landed at `f05f60b`, `AGENTS.md:182` | still landed; at `cd87715` the line is `AGENTS.md:190` | PR #30 inserted 8 lines at :109-116 |
| §11 :433-436 | ties 5 = T-040, 6 = -dev-loop AGENTS.md, 7 = "OpenAI-format schemas, globally", 8 = `broadcast` wired by M3/M4 | 5 = ORCH-02 (`ROADMAP.md:610-612`) + T-517 (`TASKS.md:6030-6034`); 6 = ADR-0007:39 + Law 8, surfaces **generated** (§3.6); 7 = the same directive (MiOS `CLAUDE.md:154`) + T-223 + LANG-04, **form only** (§3.7, Q3); 8 = T-517 + T-518 + ORCH-02, with the addressing of §3.8 (both hold; SPIKE should add the addressing) | T-040 is record-and-replay, not a message bus; the rule requires a MiOS tie for 6 |
| :285 and §11 :437 | fleet slots (AGENTS.md 4 managers / 2 teamwork) are "ADR 0003 item 14 behind the relay" | that cap is **item 1's** AGY-manager counter (`dl-h-manager-counter`, decided rev 4); item 14 is the separate heavy-lane knob | AGENTS.md caps them separately (`AGENTS.md:105-108`) |
| §11 :437 | item 30 = "`EX_TEMPFAIL`, HTTP 429 `Retry-After`" | exit **69** `EX_UNAVAILABLE` in claude_lane; HTTP 429 + `Retry-After` at the relay | 75 is taken (`claude_lane.py:194,684-686,1198`) |
| :292, :410 (D4) | negative `SECRET IN CAPTURE: <file>:<n> matches sk-ant-; refusing to write the fixture` | `SECRET IN CAPTURE: <file>:<n> api-secret-key; refusing to write the fixture` | `secret_scan.py:9` no-leak rule. SPIKE rev 3 already pins `secret-patterns.devloop.json` from `dl-r-corpus-safety` and plants a hostname, so only the text differs |
| :221, :296, M1 :395, M3 :397 | `relay_capture` table (M1 DDL); M3 negative `SECRET PERSISTED: relay_capture` | **decided rev 4:** T-040 `session` rows, kinds `relay_msg`/`relay_tool_io`; M3 negative `SECRET PERSISTED: session kind relay_tool_io` | operator 2026-09-26; no DDL needed (§0) |
| :412 (D6) | D6 adds entries to `hooks/hooks.json` | `hooks/hooks.json` is also edited by `846164c` (no-merge PreToolUse entry, +10 lines) | D6 must be based on a main that contains the no-merge PR (P-2) |
| GitHub MCP draft §5, DL-REVIEW-DOCS | owns `skills/dev-loop/scripts/devloop_mcp.py` (readOnlyHint annotations) | `dl-e-merge` owns the same file (§3.26 per-request `outputSchema` on the same `TOOLS` list) | order: `dl-e-merge` merges first; DL-REVIEW-DOCS rebases on it. Under "Copilot tailoring = AGENTS.md only" its `.github/**` paths are dropped, leaving only the annotation edit |

## 1. Disposition table

| # | Item (short) | Disposition | Precedent (pinned) | Change (relay effect in **bold**) |
|---|---|---|---|---|
| 1 | Reconcile ledger's unpushed claims | keep (operator) | none needed | `.devloop/LEDGER.md:47` claims "4-manager cap (live_managers.py, launcher refuses a 5th; both sides); quota probe/wait". Neither file exists in any ref, and `agy_host.sh` has no cap. **Decided (rev 4):** the monitor amends that line to "not pushed" (P-1); the counter is built fresh as lane `dl-h-manager-counter` (wave 1). P-1 gates **30** (ADR item 30 "Deps 1, 2"), because the same ledger line claims "quota probe/wait". **The counter is later mirrored by hub-held rows (SPIKE D5 "fleet slot rows"); it is never merged with item 14's heavy-lane counter.** |
| 2 | Fixture corpus + `capture.py` | drop (operator) | MiOS T-040 (`TASKS.md:1509-1516`) record-and-replay | **The safety rule moves into the recorders (§0)**; the hub recorder writes T-040 `session` rows of kind `relay_msg`/`relay_tool_io` (decided); corpus gate lane `dl-r-corpus-safety`. |
| 3 | Stale `devloop.sh:NN` citations | keep (operator) | none needed | Unchanged. |
| 4 | Dangling script names in AGENTS.md | keep (operator) | none needed | AGENTS.md half **done on main** (since f05f60b; `AGENTS.md:190` at cd87715). `tests/test_contract_refs.py` still to do; the planted `not_a_script.py` negative is the red-before test. |
| 5 | Retire `scripts/contracts.py` | **keep** | MiOS ORCH-02 (`ROADMAP.md:610-612`); T-517 (`TASKS.md:6030-6034`) | A polling file bus contradicts the roadmap's direction ("wake background daemons reactively without HTTP polling loops") and would be a second inbound channel beside `agent_inbox`. Controls as ADR item 5. |
| 6 | One canonical lane contract, 5 surfaces | **modify: generated, not copied** | MiOS ADR-0007:39 + Law 8 (`mios.toml:2231`); openai/codex `WritableRoot` | `assets/lane-contract.txt` is the source. The two Python surfaces **read it at runtime**, and the three Markdown surfaces carry a block **rendered** by `render_lane_contract.py`, guarded by `--check` (regenerate-and-diff). §3.6. **The bridge serves the same file to remote lanes.** |
| 7 | Report fields `host_state_changes`, `shared_interfaces` | **modify** | MiOS `CLAUDE.md:154`, T-223 (`TASKS.md:3094`), LANG-04 (`ROADMAP.md:370`), tying the schema **form** only; openai-agents-python `strict_schema.py:238-239,253` | Keep `host_state_changes`; fold `shared_interfaces` into 27's `provides`/`consumes`; add 25's `base_sha`. Strict schema. **No MiOS row ties the two specific fields** (§3.7). **The report is the payload of the bridge's A2A `Task` artifact.** |
| 8 | Consumer for `contract_updates` | **modify: becomes a relay message type** | MiOS T-517, T-518 (`TASKS.md:6040`), ORCH-02; A2A 1.0 §4.6.2 | Local sink `<run>/contract-updates.md` stays. **Relay: an A2A `Message` with extension `contract-update/v1`, addressed by `contextId` = run id and `taskId` = lane task. The hub queues it in `agent_outbox.dest_peer` = the manager's spoke, which appends it to the manager's local sink (§3.8). The final hop is an open SPIKE row.** |
| 9 | One definition of `blocked` | **modify: map to A2A, carry exact status in an extension** | A2A 1.0 §4.1.3, §4.6.2-4.6.3; MCP 2025-11-25 tasks | Mapping table §3.9; lossless claim withdrawn (rev 2). Exact status in `lane-status/v1`. |
| 10 | `guard.sh` scans only text that executes | **keep the ADR design; Codex cited for fail-closed only** | openai/codex `bash.rs:30-32` | §3.10. Positive UNTESTED until a real `<<'EOF'` commit `tool_use` is recorded. |
| 11 | Git-verb fence for lanes | **modify** | openai/codex `permissions.rs:2347-2366` | Scratch carve-out = `$TMPDIR`, `/tmp`. **agy lanes UNTESTED.** |
| 12 | Exclusive `owned_paths` across live nested lanes | **keep** (local) | PostgreSQL 17 §13.3.5 | Local check as ADR. **Cross-container leases: SPIKE M1 DDL (§3.31 row 5).** |
| 13 | `--requires <id>` at dispatch | **keep** | GitHub Actions `jobs.<id>.needs` | Unchanged. |
| 14 | Heavy-model admission, one knob | **modify: two counters, not one** | FreeBSD sysexits `EX_TEMPFAIL 75`; MCP 2025-11-25 tasks | Heavy-Claude-lane knob as ADR (rc 75). The AGY-manager counter is item 1 (`dl-h-manager-counter`). |
| 15 | `--mutation`/`--full-gate` on nested dispatch | **keep** | in-repo `adapters.py cmd_gate` | Parity fix. |
| 16 | Close the `\|\| true` gap | **modify** | in-repo `gate_audit.py:147` `RE_SWALLOW` | One detector. |
| 17 | `lane_invariants.py` scoper + SOURCE_TEXT_ASSERT | **modify** | reviewdog `-filter-mode added` | Literal-Python negative ships; android-edge-node negative UNTESTED. |
| 18 | Literal family | **keep as ADR wrote it** | in-repo evidence; MiOS `tools/drift-checks.py:1711`, `src/mios-rs/miosd/src/drift/ports.rs:19-29` | BARE_PORT **on by default**. `port_ssot` only names the SSOT in the remedy text. **No repo declares `port_ssot` today** (`git grep -nw port_ssot origin/main` in MiOS: no hit; in -dev-loop only the ADR's proposal, `0003-dev-loop-self-improvement.md:401`). A MiOS declaration naming `usr/share/mios/mios.toml [ports]` is **to be added** by the `mios.toml` owner (§3.31 row 7). |
| 19 | Invariants before the controls | **keep** | openai-agents-python `docs/guardrails.md:38` | Unchanged. |
| 20 | Waivers at the base commit | **modify** | ruff RUF100 `unused_noqa.rs:30-35` | Unchanged. |
| 21 | Coverage map + `--diff` decision | **keep** | none needed | `--diff` do-later. |
| 22 | Freshness at dispatch (`--fresh`) | **keep, default off** | github/docs `about-protected-branches.md:107-108`; merge queue | Fresh-base retest is item 27. |
| 23 | Merge preview + git probe | **keep** | git-merge-tree 2.43.0 EXIT STATUS | 0 clean, 1 conflict, else `broken`. |
| 24 | Launcher base hygiene | **keep** | none needed | `DevLoop.ps1` UNTESTED where `pwsh` is absent. |
| 25 | Base for `isolation: worktree` lanes | **modify** | `agents/lane-worker.md:5` | `base_sha` ships in 7's lane. **The bridge stamps `base_sha`.** Positive UNTESTED. |
| 26 | Typed gate verdict | **replace-with-upstream** | MCP 2025-11-25 `server/tools.mdx`; MCP 2026-07-28 `basic/index.mdx:353,375`, `basic/versioning.mdx:174-180`; MCP 2025-06-18 `basic/transports.mdx:251-253` | `outputSchema`/`structuredContent` decided **per request** from the request's own version (§3.26). TextContent always. **Relay carries it as `gate-verdict/v1`.** |
| 27 | `provides`/`consumes` + integration | **replace-with-upstream** | GitHub merge queue | §3.27. |
| 28 | Proposer shape + Workflow-tool host | **modify** | none needed | Unchanged. |
| 29 | Segment-aware `is_owned` for globs | **replace-with-upstream** | gitglossary 2.43.0 `:(glob)` | Unchanged. |
| 30 | Detect a Claude usage limit | **modify: structured detector, exit 69** | claude-agent-sdk-python `types.py:1391-1433`, `message_parser.py:356-372`; sysexits; RFC 9110 §10.2.3; RFC 6585 §4 | §3.30. The stream parse and `rate_limit_event` detection are **UNTESTED**: no print-mode stream-json capture exists (§3.30). `quota/v1` is owned by `dl-g-quota`. |
| 31 | Backlog rows + 429 forensic record | **modify** | none needed | Monitor-owned. MiOS rows in §3.31 point at the owning SPIKE or ADR-0025 lane. |

## 2. Critique resolution

### 2.00 Rev 5 round (critique of rev 4: 3 wrong, 1 missing)

| Item | Status | Evidence re-run this revision (MiOS `02f0f5e`; identical at `cfa98ab`) |
|---|---|---|
| wrong 1: "refuse-on-secret before the chainer" listed as a read fact | **Accepted.** Moved out of the read facts into §0 "Requirements on SPIKE M3" as R-1, and labelled as a requirement (nothing does it today); §6 change 8 now says so | `audit.py:173-193` (`stamp`) has no secret check; `dbwrite.py:77-78` calls `stamp_session` with no refusal before it |
| wrong 2: chain columns cited `:653-654` | **Accepted.** Now `schema-init.sql:653-655` in §0 and §2.0 | `sed -n 653,655p`: `chain_seq`, `prev_hash`, `chain_hash` |
| wrong 3: chainer named `mios_audit.SessionChainer` | **Accepted.** Now `mios_pipe/observability/audit.py:153` (class), `:195` (`_SESSION_CHAINER`), `:197-198` (`stamp_session`), reached from `dbwrite.py:77-78`; `mios_audit.py` named as the test shim | `grep -n` in `audit.py` and `dbwrite.py` |
| missing 1: single-process chain head | **Accepted.** Added as §0 R-2 (`relay_ingest` runs inside agent-pipe and writes through `_SESSION_CHAINER`; otherwise a DB sequence/lock = DDL) with the runnable M3 negative `SESSION CHAIN FORK: duplicate chain_seq <n>` and its positive; filed in §6 change 8 | `audit.py:154,195,244-265`; `server.py:789` seeds once at startup; no UNIQUE index or sequence on `session.chain_seq` in `schema-init.sql`; `verify_session_chain` (`:200-219`) has no duplicate-seq check, so the named check is new |

No item is rejected.

### 2.0 Rev 4 re-check of every `critic_dispo` item at the new pins

Each item of `critic_dispo` (task `w1ypid9bh`, 10 wrong + 5 missing) was re-checked against -dev-loop
`cd87715`, MiOS `02f0f5e`, mios-bootstrap `37584c0`. Since rev 3 the only repo change is `AGENTS.md` +8 lines
(`git diff --stat f05f60b cd87715`), so the rev 3 resolutions in §2.1 stand, with these re-checks:

| critic_dispo item | Rev 4 status | Evidence re-run this revision |
|---|---|---|
| wrong 1: pin stale, item 4 row | **Resolved again**: re-pinned to `cd87715`; item 4 line is now `AGENTS.md:190` | `git show origin/main:AGENTS.md \| grep -n "job.py wait"` → `190:`; PR #30 merged `244ad99` (GitHub API: `merged_at 2026-09-26T15:32:27Z`) |
| wrong 2: `port_ssot` not declared | **Resolved** (row 7 of §3.31: to be added) | `git grep -nw port_ssot origin/main`: MiOS no hit; -dev-loop only `docs/decisions/0003-dev-loop-self-improvement.md:401` |
| wrong 3: item 26 presumes session state | **Resolved** (§3.26 per-request rule) | `devloop_mcp.py:9-10` unchanged: "Stateless by design (MCP 2026-07-28 model)" |
| wrong 4: no per-manager inbox | **Resolved** (§3.8 addressing via A2A ids + `agent_outbox.dest_peer`) | MiOS pin unchanged, `schema-init.sql:1490-1501` |
| wrong 5: item 7 tie | **Resolved** as a form-only tie; the one residual reading is Q3 (§5) | MiOS `CLAUDE.md:154`; `TASKS.md:3094`; `ROADMAP.md:370` |
| wrong 6: item 6 Law 8 vs hand copies | **Resolved** (§3.6 generated + `--check`) | ADR-0007:39; `mios.toml:2231` |
| wrong 7: conflicts with SPIKE hidden | **Resolved and extended**: §0.1 now also lists SPIKE rev 3 lines that are *still* stale (:434-437, D4 text) and the two new collisions (D6 `hooks.json`, DL-REVIEW-DOCS `devloop_mcp.py`) | SPIKE rev 3 §11 :434-437 read this revision |
| wrong 8: "one pattern list" false | **Resolved**; SPIKE rev 3 §8.1 now pins `secret-patterns.devloop.json` from `dl-r-corpus-safety` and adds a parity test, so the consumer exists; only D4's failure text remains (§6 item 5) | SPIKE :309-310, :410 |
| wrong 9: dl-x validates quota/v1 first | **Resolved** (`quota/v1` owned by `dl-g-quota`) | §4 table |
| wrong 10: dl-g-quota positive vacuous | **Resolved** (parse + detector UNTESTED) | all three fixtures still have types `{header, user, assistant}` only (re-run: `json.loads` per line on `origin/main`) |
| missing 1: ADR-0025 coordination | **Resolved** (§3.31 owners) | ADR-0025:249-262 |
| missing 2: MiOS rows duplicate SPIKE lanes | **Resolved** (rows 4-6 point at SPIKE lanes; the capture row is now M3's `session` write, not M1 DDL) | §3.31 |
| missing 3: lane/question consistency | **Resolved**: Q1 is decided, so P-1 is a fixed monitor action; `dl-h-manager-counter` exists with texts; sibling-window texts dictated (§3.30) | §4 |
| missing 4: hostnames never planted | **Resolved** (`blade-devloop-planted.home.arpa` plant, `UNSCRUBBED HOSTNAME`) | fixtures hold no private-suffix FQDN (0 hits) |
| missing 5: T-040 vs `relay_capture` | **Resolved by operator decision**: extend T-040, no DDL needed | `schema-init.sql:203` (`kind text`, no CHECK), `:653-655` (chain columns, rev 5 cite fix), `chat.py:758-760` (chat replay filters its own kinds) |

No item is rejected: every one was correct on the facts it cited.

### 2.1 Rev 3 round (critique of rev 2; SPIKE line cites in this subsection are SPIKE revision 2 lines, kept as the historical record)

| # | Critique | Resolution | Evidence |
|---|---|---|---|
| W1 | Pin stale; item 4 row wrong | **Accepted.** Re-pinned to f05f60b; item 4 row and §0.1 updated. | `git log origin/main` = `f05f60b Merge pull request #29`; `git show f05f60b:AGENTS.md` :182 "the monitor blocks on `scripts/job.py wait`"; diff stat touches only AGENTS.md (+1/-1) and LEDGER.md (+7 at the end), so every code cite and `LEDGER.md:47` hold. |
| W2 | Item 18: MiOS does not declare `port_ssot` | **Accepted.** Reworded as a declaration to be added (§3.31 row 7). | `git grep -nw port_ssot origin/main`: MiOS no hit; -dev-loop only `docs/decisions/0003-dev-loop-self-improvement.md:401`. |
| W3 | Item 26 rule presumes session state the stateless server lacks | **Accepted.** Per-request rule plus pre-initialize behaviour dictated (§3.26). | READ `devloop_mcp.py:9-10` "Stateless by design (MCP 2026-07-28 model)"; `:142-150` `handle()` keeps no version and `tools/list` returns constant `TOOLS`. READ MCP 2026-07-28 `basic/index.mdx:375` "`io.modelcontextprotocol/protocolVersion` ... Yes ... Protocol version for this request"; `versioning.mdx:178-180` "An `initialize` request selects legacy semantics, scoped to the stdio process (stdio) or the session (HTTP)". |
| W4 | Item 8: `agent_inbox` has no recipient column | **Accepted.** Addressing = A2A `contextId`/`taskId` in the payload plus `agent_outbox.dest_peer`/`spoke_session`. Delivery leg named; final hop is an open SPIKE row (§3.8). | READ `schema-init.sql:1490-1501`: columns id, idempotency_key, source, event_type, payload, status, retry_count, created_at, processed_at, origin_node. SPIKE :185 `agent_outbox`: "`dest_peer`, `spoke_session`, `seq`, ...". |
| W5 | Item 7 tie (T-040/T-218) does not support typed fields | **Accepted.** Replaced with a tie to the schema form. States plainly that no MiOS row ties the fields themselves (§3.7). | READ `TASKS.md:3094` T-223 "mark the tool surface strict (`strict:true`, `additionalProperties:false`)"; `ROADMAP.md:370` LANG-04 "`--format json` emitting an OpenAI-format structured-output schema"; MiOS `CLAUDE.md:154` "Every schema is an OpenAI format". |
| W6 | Item 6: Law 8 cite contradicts hand-carried copies | **Accepted.** Surfaces are generated or read at runtime; regenerate-and-diff check (§3.6). | READ ADR-0007:39 "all SSOT-generated"; `mios.toml:2231` Law 8 `enforced_by = "98-drift-checks.sh:check_projection_registry"`. |
| W7 | Conflicts with the SPIKE hidden | **Accepted.** §0.1 lists each SPIKE line (re-anchored to SPIKE rev 3 in rev 4); §6 is the change list for the SPIKE owner. Neither document goes to the operator first. | SPIKE :246, :342-356, :187, :253, :312-314, :325. |
| W8 | "One pattern list" false; D4 text differs; `--export-patterns` has no consumer | **Accepted.** Three sets named. -dev-loop's two unified via generated `secret-patterns.json`; D4 consumes it (SPIKE change); D4 text aligned; MiOS set separate by Law 5 (§0). | `secret_scan.py:30-43`; SPIKE :325; `redact.py:4-15`. |
| W9 | dl-x validates `quota/v1` before its producer exists | **Accepted.** `quota/v1` moved into `dl-g-quota`; dl-x ships three extensions whose producers precede it (§4). | dl-b-report (report, sink), dl-b-contract (status table), dl-e-merge (`gate-<id>.json`) all precede dl-x on the chain. |
| W10 | dl-g-quota positive is vacuous | **Accepted.** Parse and detector positives are UNTESTED. Runnable controls are only those whose input is claude_lane's own receipts (§3.30). | Each `tests/fixtures/transcripts/*.jsonl` has types {header, `user`, `assistant`} only (chat-question 1/3/5, native-ask 1/2/2, open-blocker 1/2/3), with no `result`, `system` or `rate_limit_event`. |
| M1 | No coordination with ADR-0025 beyond mios.toml | **Accepted.** Each MiOS row names its ADR-0025 serial owner (§3.31). | ADR-0025:249-262 (D7): L2 owns `src/mios-rs/miosd/src/**`; L5 owns `tools/drift-checks.py`, `automation/98-drift-checks.sh`, `tests/drift-gate-negatives.sh`. |
| M2 | MiOS rows duplicate SPIKE lanes | **Accepted.** Rows 4-6 point at SPIKE M1/M2/M3/M4/D5 and are not filed in parallel. | SPIKE :312 (M1 DDL), :313 (M2 vendor-URL gate), :314 (M3), :315 (M4 broadcast), :326 (D5 fleet slot rows). |
| M3 | Lane/question inconsistency | **Accepted.** Item 1 is a precondition written the same way in the table and in the JSON objective, not a `depends_on`. Q1's option is lane `dl-h-manager-counter`. The sibling-window refusal has dictated texts. | §4. |
| M4 | Hostnames claimed, never planted | **Accepted.** Hostname rule and planted negative added. | Real fixtures hold no home path and no private-suffix FQDN (grep of all three: 0 hits), so the positive stays green. |
| M5 | T-040 vs `relay_capture` not addressed | **Accepted.** Recommendation: extend T-040 `session` rows (§0). Filed as a SPIKE change and as Q2. | `TASKS.md:1511`; `chat.py:21,58,758-764`; `test_mios_audit.py:449-470`; SPIKE :187. |

### 2.2 Rev 2 round (kept; two rows amended)

W1 (exit 69 not 75), W2 (stream-json), W3 (Codex rejects heredocs), W4 (two counters), W5 (A2A mapping not
lossless), W6 (freshness = item 27), W7 (BARE_PORT on by default), W8 (agy UNTESTED), W10 (item 1 dependents):
accepted as recorded in rev 2, evidence unchanged. **Amended:** rev 2's M1 ("extends secret_scan.py instead of
adding a second pattern list") is superseded by §0's three-set statement. Rev 2's M3 ties for 5-8 are superseded
for items 6 and 7 (§3.6, §3.7). Rev 2's W9/OQ-1 note about SPIKE Q1 was stale: SPIKE :31 already closes its own
revision 1 Q1.

## 3. Rationale per item (5-31)

### 3.5 Retire `contracts.py` (keep)
READ `ROADMAP.md:611` ORCH-02: "Implement PostgreSQL `LISTEN`/`NOTIFY` on `tasks` and `pending_action` tables to
wake background daemons reactively without HTTP polling loops." READ `TASKS.md:6032` T-517: "insert into
PostgreSQL `agent_inbox`, and trigger asynchronous agent worker dispatch." Controls unchanged from ADR item 5
(`RETIRED NAME: contracts.py cited at shims/cursor/verify.mdc:<n>`).

### 3.6 Canonical lane contract (modify: generated)
MiOS tie, READ ADR-0007:39: "Net stack: **Spec (rules) ← ADRs (decisions) ← drift-checks (evals)** — all
SSOT-generated and cross-referenced." Law 8 (`mios.toml:2231`, SSOT-PROJECTION) asks for a derived surface to be
"emitted by a generator and guarded by a regenerate-and-diff drift-check". Applied to the five surfaces ADR item
6 names (`0003-...md:172-177`):
- `adapters.lane_prompt` and `devloop_worker.build_system` (Python) **read `assets/lane-contract.txt` at run
  time**. There is no copy, so nothing can drift.
- `agents/lane-worker.md`, `assets/templates/prompts/nested-claude-lanes.md` and `SKILL.md` §11 carry the text
  between `<!-- lane-contract:begin -->` / `<!-- lane-contract:end -->` markers, written by new
  `skills/dev-loop/scripts/render_lane_contract.py --write`. `--check` re-renders into memory and diffs.
- Positive: `python3 skills/dev-loop/scripts/render_lane_contract.py --check` exits 0 after `--write`, and
  `python3 -m unittest tests.test_lane_contract_parity` (which also asserts both Python surfaces open the asset)
  passes. Red today: no markers exist.
- Negative 1 (ADR text kept): delete the canonical line inside the block of a temp copy of `agents/lane-worker.md`
  → `LANE CONTRACT DRIFT: agents/lane-worker.md lacks canonical line 'NEVER WRITE OUTSIDE YOUR WORKTREE AND SCRATCH'`.
- Negative 2 (hand edit): change one word inside the block → `LANE CONTRACT DRIFT: agents/lane-worker.md block
  differs from render of lane-contract.txt (run render_lane_contract.py --write)`.
- Negative 3: a Python surface with a string literal of the line instead of reading the asset →
  `LANE CONTRACT COPY: adapters.py embeds the contract text instead of reading lane-contract.txt`.

Upstream vocabulary unchanged from rev 2 (codex `permissions.rs:2353-2355`). The scratch sentence names `$TMPDIR`
and `/tmp`.

### 3.7 Report fields (modify)
MiOS tie, **to the form, not the fields**: READ MiOS `CLAUDE.md:154-156` "**OpenAI-format schemas, globally.**
Every schema is an OpenAI format -- not only the `/v1` wire surface but schemas everywhere."; `TASKS.md:3094`
T-223 "mark the tool surface strict (`strict:true`, `additionalProperties:false`)"; `ROADMAP.md:370` LANG-04
"`--format json` emitting an OpenAI-format structured-output schema". So the report schema in
`openai-tools.json` follows OpenAI strict structured output. **No MiOS roadmap, ADR or TASKS row names
`host_state_changes` or `base_sha`.** Their justification is -dev-loop evidence (ADR item 7 and item 25), and the
operator rule "5-8 kept only with a cited tie" is met by the form tie alone. If the operator reads the rule as
requiring a field-level tie, item 7 has none and falls to "drop": say so in the operator brief (§6 last line).
Upstream: `strict_schema.py:238-239` `json_schema["additionalProperties"] = False`, `:253`
`json_schema["required"] = list(properties.keys())`. Optional values as `["array","null"]`/`["string","null"]`.
Negative as ADR (`REPORT SCHEMA DRIFT: host_state_changes is in SKILL.md §13 but not required by openai-tools.json report`).
Rev 2's T-040/T-218 tie is withdrawn: T-040 records I/O, and T-218 is item 9 material.

### 3.8 `contract_updates` as a relay message type (modify)
MiOS ties: T-517 (`agent_inbox`), T-518 (`TASKS.md:6040` "/v1/events/ws"), ORCH-02.
Addressing and delivery (INFERRED design over READ schemas; `agent_inbox` has **no** recipient column,
`schema-init.sql:1490-1501`):
1. **Emit (lane side, bridge):** `Message{messageId, contextId: <dev-loop run id>, taskId: <lane task id>,
   role: ROLE_AGENT, parts:[{text:<update>}], extensions:[".../contract-update/v1"],
   metadata:{".../contract-update/v1": {lane_id, report_path, run_id, manager_context_id}}}`. A2A 1.0 §4.6.2:
   "Messages can be extended to allow clients to provide additional strongly typed context".
2. **Ingest (hub, SPIKE M3):** `relay_ingest` inserts into `agent_inbox` with `idempotency_key` = messageId
   (SPIKE M3's `INBOX DEDUP BROKEN` negative), `source='relay'`, `event_type='a2a.message'`, and the Message as
   `payload`. The routing keys are payload fields, not columns.
3. **Route (hub):** the hub resolves `manager_context_id` to the manager's spoke session through `relay_session`
   (SPIKE M1 DDL) and inserts an `agent_outbox` row with `dest_peer` = that spoke's peer id and `spoke_session` =
   its session (SPIKE rev 3 :219 columns).
4. **Deliver (spoke):** the manager's spoke receives it in `seq` order on its SubscribeToTask stream (SPIKE G-A4,
   lane M3).
5. **Final hop (open SPIKE row, §6):** the bridge beside the AGY manager appends the update to the manager's
   `<run>/contract-updates.md`. That is the same sink local lanes write, so the manager reads one place and stays
   the only writer of AGENTS.md. Until that row lands, relayed updates reach the hub and stop there. That state
   is reported, not hidden.

Local sink and the ADR negative (`CONTRACT UPDATES LOST: 1 in reports, 0 in contract-updates.md`) ship now. The
positive over a real report is UNTESTED.
Extension URI namespace: `https://github.com/mios-dev/-dev-loop/ext/<name>/v1`. -dev-loop may carry vendor URLs
(AGENTS.md). MiOS reads these URIs from SSOT (SPIKE M1), and `check_vendor_urls`
(`98-drift-checks.sh:1255`) does not match `github.com`.

### 3.9 `blocked` mapping (modify)
READ A2A 1.0 §4.1.3: `TASK_STATE_INPUT_REQUIRED` "Indicates that the agent requires additional user input to
proceed. This is an interrupted state."; `TASK_STATE_AUTH_REQUIRED` "Indicates that authentication is required
to proceed. This is an interrupted state."; `TASK_STATE_FAILED` "finished with an error. This is a terminal
state."; `TASK_STATE_CANCELED` "canceled before completion". MCP 2025-11-25 tasks `:405-406`: from `working`
"may move to `input_required`, `completed`, `failed`, or `cancelled`".

| dev-loop status (cause) | A2A 1.0 TaskState | MCP task status | `lane-status/v1` metadata |
|---|---|---|---|
| `done` | `TASK_STATE_COMPLETED` | `completed` | `{status:"done"}` |
| `blocked` (operator decision) | `TASK_STATE_INPUT_REQUIRED` | `input_required` | `{status:"blocked", cause:"operator", next}` |
| `blocked` (credential) | `TASK_STATE_AUTH_REQUIRED` | `input_required` | `{status:"blocked", cause:"credential", next}` |
| `blocked` (external event) | `TASK_STATE_INPUT_REQUIRED` | `input_required` | `{status:"blocked", cause:"external", next}` |
| `partial` / `converged_stuck` / `budget` | `TASK_STATE_FAILED` | `failed` | `{status:<exact>, reason?}` |
| `halted` | `TASK_STATE_CANCELED` | `cancelled` | `{status:"halted"}` |

External event -> INPUT_REQUIRED (INFERRED): the lane has ended and resumes only when the requestor (the
manager) sends a message saying the event occurred; that is "requires additional input", interrupted, not
terminal. A stock client cannot tell the three `blocked` causes or the three failure kinds apart; that loss
is stated, and the extension is what removes it. MiOS's own status vocabulary uses the same table (item 31).

### 3.10 `guard.sh` exec_text (keep ADR design)
READ tree-sitter-bash v0.25.0 `src/node-types.json` defines `heredoc_body`, `heredoc_start`, `raw_string`, so a
grammar could locate the text. Not adopted: it adds a native parser dependency to a POSIX hook that must run in
every harness (INFERRED), and no upstream project uses it to *drop* non-executing text. The ADR's rules stand:
drop quoted-terminator heredoc bodies and single-quoted strings; keep unquoted heredocs and `$(...)`; return raw
text on any doubt. Negatives as ADR, verbatim deny text. Positive UNTESTED until recorded.

### 3.11 Git-verb fence (modify)
As ADR. Deny text as ADR. Carve-out `${TMPDIR:-/tmp}` and `/tmp`. UNTESTED for agy lanes.

### 3.12 / 3.14 Ownership and admission
Local checks ship now. Cross-container leases and the counters' hub mirror are SPIKE M1 DDL plus SPIKE D5
fleet-slot rows (§3.31 row 5). Item 14 keeps rc 75 (`sysexits.h:108`, `claude_lane.py:129`). Item 1's counter is
`dl-h-manager-counter`.

### 3.13 `--requires`
READ github/docs: "Use `jobs.<job_id>.needs` to identify any jobs that must complete successfully before this job will run."

### 3.15 / 3.16
15: in-repo parity. 16: READ `gate_audit.py:147` `RE_SWALLOW` matches `|| true`, `|| :`, `; true`, `set +e`,
`--exit-zero`, `|| exit 0`. ADR negative text unchanged.

### 3.17 / 3.18 / 3.19 / 3.20 / 3.21
17: reviewdog README "### `added` (default) Filter results by added/modified lines." 18: see rev 2 W7; OQ-2 closed
because the evidenced defect (literals in a repo with no SSOT) is exactly the case a `port_ssot` gate misses,
and MiOS's full gate is proven partial; running MiOS `just drift-gate` through `--full-gate` (item 15) is
additive, not a replacement. 19: READ `guardrails.md:38` "The guardrail runs and completes *before* the agent
starts. If the guardrail tripwire is triggered, the agent never executes". 20: READ ruff `unused_noqa.rs`
"A `noqa` directive that no longer matches any diagnostic violations is likely included by mistake, and should
be removed". 21: no upstream.

### 3.22 / 3.23
22: READ `about-protected-branches.md:107-108` (Loose) "The branch **does not** have to be up to date with the
base branch before merging." The merge queue groups a PR "with the latest version of the `base_branch` as well
as changes from pull requests ahead of it" -> item 27. 23: READ git-merge-tree 2.43.0 "For a successful,
non-conflicted merge, the exit status is 0. When the merge has conflicts, the exit status is 1. If the merge is
not able to complete (or start) due to some kind of error, the exit status is something other than 0 or 1".

### 3.26 Typed verdict (per-request version)
READ MCP 2025-11-25 `server/tools.mdx`: "For backwards compatibility, a tool that returns structured content
SHOULD also return the serialized JSON in a TextContent block." READ MCP 2026-07-28 `basic/index.mdx:369-375`:
"Servers use these to identify the protocol version and capabilities in use without relying on any prior
connection state", `io.modelcontextprotocol/protocolVersion` required on every request. READ
`basic/versioning.mdx:176-180`: "A request carrying modern per-request `_meta` is served statelessly according to
this revision. An `initialize` request selects legacy semantics, scoped to the stdio process (stdio) or the
session (HTTP)". READ 2025-06-18 `basic/transports.mdx:251-253`: without a version header "and has no other way to
identify the version ... the server **SHOULD** assume protocol version `2025-03-26`."

Rule. The **effective version** of each `tools/list` / `tools/call`, first match wins:
1. `params._meta["io.modelcontextprotocol/protocolVersion"]` (modern, 2026-07-28 and later).
2. On an HTTP transport (the bridge, not today's stdio server), the `MCP-Protocol-Version` header.
3. The version negotiated by `initialize` on this stdio process. This is the one piece of state the server
   gains, legacy only, per `versioning.mdx:178-180`.
4. None of the above: `2025-03-26`, copied from the 2025-06-18 transport rule (INFERRED to apply to stdio too).

`outputSchema` is listed and `structuredContent` returned only when the effective version is in
{2025-06-18, 2025-11-25, 2026-07-28}. TextContent (the JSON) is always returned. `tools/list` sent before any
`initialize` and without `_meta` therefore returns the tools **without** `outputSchema`.
Controls (plain JSON-RPC lines into `devloop_mcp.py` stdin; protocol data, not harness transcripts):
- Positive: `initialize` 2025-11-25 → `tools/list` has `outputSchema` on `gate`; `tools/list` with `_meta`
  2026-07-28 and no initialize → has it.
- Negative 1: `initialize` 2025-03-26 → `tools/list`; with the gate planted out →
  `STRUCTURED CONTENT ON OLD PROTOCOL: outputSchema advertised to a 2025-03-26 request`.
- Negative 2: `initialize` 2025-03-26, then `tools/list` with `_meta` 2026-07-28; with process state planted to win
  → `PER-REQUEST VERSION IGNORED: _meta protocolVersion 2026-07-28 overridden by initialize 2025-03-26`.
- Negative 3: `tools/list` with neither → `outputSchema` present fails
  `STRUCTURED CONTENT ON OLD PROTOCOL: outputSchema advertised to a 2025-03-26 request (no version supplied)`.
- ADR negative (`TYPED VERDICT IGNORED: ...`) stays.

### 3.27 Integration (merge-queue semantics)
READ github/docs `managing-a-merge-queue.md:49`: "These are the temporary branches that are created on your
behalf by a merge queue"; docs page: "if there are failed required status checks or conflicts with the base
branch, the pull request will be removed from the queue." Semantics copied:
1. Order the wave (lanes.json order). Build cumulative prefixes `base+L1`, `base+L1+L2`, ... in throwaway
   worktrees; run `interfaces.check_cmd` on each.
2. The first failing prefix names the failing lane `Lk`. Remove `Lk` and every lane whose `consumes` intersects
   `Lk`'s `provides` (transitively). Rebuild prefixes from the rest and retest; merge what passes.
3. Release rule: a held consumer is released only when its provider is re-dispatched and passes integration in
   a later wave, or the manager edits the consumer's `consumes` to drop the dependency. Never automatically.
Positive (plain inputs: temp git repos): `a` provides `f`, `b` consumes `f`, independent `c`; all merge.
Negative 1: `a` renames `f` -> exit 1 with
`INTEGRATION FAILED: interfaces.check_cmd exit 1 at prefix a; removed a and its consumers (b); merged 1 of 3 (c)`,
and neither `a` nor `b` merged. Negative 2 (plant: skip the retest) must fail with
`INTEGRATION RETEST SKIPPED: c not retested after removing a`.

### 3.28 / 3.29
28: no upstream. 29: READ gitglossary 2.43.0: "wildcards in the pattern will not match a / in the pathname. For
example, "Documentation/*.html" matches "Documentation/git.html" but not "Documentation/ppc/ppc.html"".

### 3.30 Usage limit
READ `types.py:1391` `RateLimitStatus = Literal["allowed", "allowed_warning", "rejected"]`; `:1405` "resets_at:
Unix timestamp when the rate limit window resets."; `:1428-1430` "gracefully back off when ``status ==
"rejected"``"; `message_parser.py:361` wire key `resetsAt` (camelCase) inside `rate_limit_info`. Plan:
1. `adapters.py:253` claude argv -> `--output-format stream-json` (plus `--verbose` if `adapters.py probe`
   shows print-mode stream-json requires it; UNVERIFIED); the report is the last `type:"result"` object of the
   NDJSON stream. `PROBE_FLAGS["claude-code"]` (`adapters.py:59`) keeps `--output-format`.
2. Detector: a `rate_limit_event` whose `rate_limit_info.status == "rejected"`, or an assistant message with
   `error == "rate_limit"` (`types.py:1038-1041`). Never prose.
3. Where the typed reason lives: `report._meta.quota = {reason:"quota", reset_at:<resetsAt>, rate_limit_type}`;
   the job receipt gets `quota_reset_at`; `claude_lane.py wait/list/status` JSON gets
   `{"state":"failed","why":"quota","quota_reset_at":<ts>}` and exit **69**. `wait` never maps quota to
   `running`/75. Status stays `budget` (enum unchanged).
4. Failure texts: `QUOTA MISSED: <fixture> carries a rate_limit_event status=rejected but _meta.quota is absent`
   (ADR negative, reworded to the structured signal); busy-vs-quota plant (map quota to 75) must fail with
   `QUOTA REPORTED AS BUSY: rc 75 for a lane whose report carries _meta.quota`.
5. Relay: the bridge maps `_meta.quota` to HTTP 429 (READ RFC 6585 §4 "The 429 status code indicates that the
   user has sent too many requests in a given amount of time") with `Retry-After` (READ RFC 9110 §10.2.3
   "Servers send the "Retry-After" header field to indicate how long the user agent ought to wait before making
   a follow-up request."); A2A side: READ A2A 1.0 §3.3.2 Error Handling "Servers MAY include retry guidance (e.g.,
   Retry-After header in HTTP)".
Corrections in rev 3:
- **UNTESTED:** the stream parse ("report = last `type:"result"` object") and the detector. No print-mode
  `claude -p --output-format stream-json` capture exists. The three fixtures are Stop-hook transcripts (types
  header/`user`/`assistant` only). Rev 2's "stream-json parse over the existing real transcripts" is withdrawn. If
  the monitor records one real print-mode stream-json run before the lane runs (scrubbed, passing
  `dl-r-corpus-safety`), the `result` parse positive becomes runnable. The `rejected` detector stays UNTESTED
  until a real rejected event is recorded. `QUOTA MISSED` is the dictated text for that future control.
- **Runnable now** (input = claude_lane's own receipts and reports, built by the test; not harness output):
  - Exit map: a receipt with `quota_reset_at` → `wait` exits 69 with `{"state":"failed","why":"quota",...}`.
    Plant 75 → `QUOTA REPORTED AS BUSY: rc 75 for a lane whose report carries _meta.quota`.
  - Sibling window: a pure `quota_window_open(run_dir, now)` plus `dispatch --check-only` (added by
    dl-c-dispatch). With a sibling receipt whose `quota_reset_at` = now+3600, dispatch is refused (rc 69) with
    `QUOTA WINDOW OPEN: sibling <id> reported quota, resets at <iso>; refusing dispatch`. With the check planted
    out, the test fails `QUOTA WINDOW IGNORED: dispatched while sibling <id> reset_at <iso> is in the future`. A
    `reset_at` in the past is allowed (positive).
  - `quota/v1` JSON Schema (owned here, not by dl-x) validates the `_meta.quota` object this lane writes into a
    test-built report. Negative: drop `reset_at` from `required` → `EXTENSION DRIFT: quota/v1 lacks reset_at`.
- Precondition (not a lane): P-1, the monitor's amendment of `.devloop/LEDGER.md:47` to "not pushed" (decided
  rev 4), because the same ledger line claims "quota probe/wait" work.

### 3.31 MiOS cross-repo rows (monitor files them; Law 5: no vendor names/URLs/key schemas)
Each row names its owner. None is filed in parallel with a SPIKE lane.

| # | Row | Path(s) | Owner / serialisation |
|---|---|---|---|
| 1 | `BarePortLiteralsCheck` Skip stub | `src/mios-rs/miosd/src/drift/ports.rs:19-29` | queued **behind ADR-0025 L2** (owns `miosd/src/**`, ADR-0025:249-262), and serial with SPIKE M7 (same tree) |
| 2 | Python port check covers 6 ports in 3 dirs | `tools/drift-checks.py:1711` | queued **behind ADR-0025 L5** (owns `tools/drift-checks.py`) |
| 3 | Status vocabulary = §3.9 table (A2A names only) | `usr/share/mios/ai/system.md` (in MiOS only; absent from mios-bootstrap main 37584c0) | no ADR-0025 or SPIKE lane owns it; standalone row |
| 4 | `agent_outbox` DDL; `broadcast()` emitter; recognise the -dev-loop extension URIs from SSOT | `schema-init.sql`; `mios_events.py:65`; `a2a.py` | **SPIKE M1** (DDL), **SPIKE M4** (broadcast), **SPIKE M3** (URIs, routing §3.8 step 3). Not a separate row. |
| 5 | Leases for ownership (12) and hub mirror of both counters (1, 14) | `schema-init.sql`; monitor | **SPIKE M1** (DDL) + **SPIKE D5** (fleet slot rows; SPIKE text must say item 1, §0.1) |
| 6 | Vendor-URL gate over new bridge config surfaces; extend to `.py` and key-name patterns | `automation/98-drift-checks.sh:1255` | **SPIKE M2**, serial after **ADR-0025 L5**. Note for M2: adding `.py` plus key-shape patterns flags MiOS's own `mios_pipe/redact.py:6` (`sk-ant-...`). M2 must decide between a narrow anchored allowlist entry and moving that pattern behind the bridge. |
| 7 | Declare `port_ssot` naming `usr/share/mios/mios.toml [ports]` | `usr/share/mios/mios.toml` | the **mios.toml owner** (ADR-0025 L1, then SPIKE M1, serial) |
| 8 | Relay capture as T-040 `session` rows, kinds `relay_msg`/`relay_tool_io` (decided); refuse-on-secret before the chainer insert; update the `kind` comment at `schema-init.sql:203` | `mios_pipe/federation/relay_ingest.py`, `mios_pipe/redact.py`, `schema-init.sql:203` (comment only) | **SPIKE M3** (writer + refusal). The comment line is in M1's file, so M1 carries it; M1 drops the `relay_capture` DDL. Not a separate row. |

No -dev-loop lane writes `mios.toml`, and no MiOS row here writes it outside that serial owner.

## 4. Lanes (-dev-loop only)

Ownership rule: owned_paths are exclusive among lanes that can run at the same time. A shared file is passed only
down a strict `depends_on` chain (the ADR's "same files, serialise" rule). No lane touches `AGENTS.md`,
`.devloop/`, `bridge/**`, `monitor/**`, `global_monitor.py`, `devloop_serverd.py`, `hooks/spoke-notify.sh`,
`hooks/hooks.json`, `hooks/no-merge.sh`, `.claude/settings.json`, `.devcontainer/**`, `.github/**`,
`skills/dev-loop/scripts/env/**` (P0, D8, and the SPIKE lane that receives the migrated A2O vendor keys and CLI
installs), `skills/dev-loop/scripts/register-mcp.sh` (GitHub MCP DL-REGISTER),
`tests/fixtures/transcripts/relay/**` (SPIKE lanes), MiOS, or `mios.toml`. **Shared path with a SPIKE lane:**
`skills/dev-loop/scripts/devloop_mcp.py` is owned by `dl-e-merge` first; the GitHub MCP lane DL-REVIEW-DOCS
(readOnlyHint annotations) is dispatched only after `dl-e-merge` has merged, on a base that contains it. Controls whose input is a real capture are UNTESTED. No lane replays a capture it produces.
**Preconditions** (monitor actions, not lanes, written identically in the table and the JSON objectives):
- **P-1** (decided rev 4): the monitor amends `.devloop/LEDGER.md:47` to state that `live_managers.py`, the
  launcher cap and the quota stub tests were **not pushed** (exist in no ref). Gates `dl-h-manager-counter` and
  `dl-g-quota`.
- **P-2**: commit `846164c` (no-merge hook: `hooks/no-merge.sh`, `hooks/hooks.json`, `hooks/guard.sh`,
  `.claude/settings.json`, `tests/test_guard_hooks.py`) reaches `origin/main` through its own PR (the operator
  merges). Gates `dl-c-guards`, which owns `hooks/guard.sh` and `tests/test_guard_hooks.py`: its base must contain
  the `gh pr merge` deny, and its positive includes `test_merge_tools_are_denied` staying green.
- **P-3**: branch `origin/claude/mios-dev-loop-startup-4elr0n` (`300e358`..`bbdfd2b`: `agy_host.sh`,
  `agy_session.py`, `tests/test_agy_remote_control.py`, `tests/test_devloop_exclude.py`) is merged or abandoned
  before `dl-h-manager-counter` is dispatched, because both edit `skills/dev-loop/scripts/agy_host.sh`.

| id | items | owned_paths | positive (runnable now) | negative (exact text) | deps |
|---|---|---|---|---|---|
| dl-r-corpus-safety | recorder safety (2's rule) | `skills/dev-loop-web/scripts/secret_scan.py`, `skills/dev-loop-web/assets/secret-patterns.json`, `tests/test_fixture_corpus_safety.py` | 3 real transcripts pass; `secret_scan.py --export-patterns --check` regenerates `secret-patterns.json` and diffs clean | `sk-ant-DEVLOOP-PLANTED-CAPTURE` in a copy → `SECRET IN FIXTURE: chat-question.jsonl:<n> api-secret-key (planted: DEVLOOP-PLANTED-CAPTURE); refusing`; `/home/<user>/x` → `UNSCRUBBED HOME PATH: chat-question.jsonl:<n>`; `blade-devloop-planted.home.arpa` → `UNSCRUBBED HOSTNAME: chat-question.jsonl:<n>`; hand edit of the JSON → `SECRET PATTERNS DRIFT: secret-patterns.json differs from secret_scan.PATTERNS` | none |
| dl-a-hygiene | 3, 4, 5 | `skills/dev-loop/references/run-directory.md`, `skills/dev-loop/scripts/contracts.py`, `shims/**/verify.*`, `README.md`, `skills/verify/SKILL.md`, `skills/dev-loop/references/upstream-patterns.md`, `skills/dev-loop/SKILL.md`, `tests/test_contract_refs.py`, `tests/test_retired_names.py`, `tests/test_stale_refs.py` | ADR items 3-5 positives | ADR texts (`RETIRED NAME: ...`, planted `not_a_script.py`) | none |
| dl-b-contract | 6, 9 | `skills/dev-loop/assets/lane-contract.txt`, `skills/dev-loop/scripts/render_lane_contract.py`, `skills/dev-loop/SKILL.md`, `agents/lane-worker.md`, `hooks/stop-gate.sh`, `skills/dev-loop/assets/templates/prompts/system.md`, `skills/dev-loop/assets/templates/prompts/nested-claude-lanes.md`, `skills/dev-loop/scripts/adapters.py`, `skills/dev-loop/scripts/devloop_worker.py`, `tests/test_lane_contract_parity.py`, `tests/test_status_vocabulary.py` | `render_lane_contract.py --check`; parity + vocabulary tests | §3.6 texts; `STATUS VOCABULARY DRIFT: ...` | dl-a-hygiene |
| dl-b-report | 7, 25, 8 (local sink) | `skills/dev-loop/assets/openai-tools.json`, `skills/dev-loop/scripts/adapters.py`, `skills/dev-loop/scripts/devloop_worker.py`, `skills/dev-loop/scripts/claude_lane.py`, `skills/dev-loop/scripts/devloop.sh`, `skills/dev-loop/SKILL.md`, `agents/lane-worker.md`, `agents/orchestrator.md`, `tests/test_report_schema_parity.py`, `tests/test_lane_prompt.py`, `tests/test_contract_updates.py` | schema parity; `contract-updates` subcommand over a plain lanes run dir built by the test | `REPORT SCHEMA DRIFT: ...`; `BASE MISMATCH: ...`; `CONTRACT UPDATES LOST: ...` (real-report positives UNTESTED) | dl-b-contract |
| dl-c-guards | 10, 11 | `hooks/_lib.sh`, `hooks/guard.sh`, `tests/test_guard_hooks.py`, `skills/dev-loop/scripts/adapters.py`, `skills/dev-loop/scripts/claude_lane.py` | fence allows `git -C "$(mktemp -d)" init` | ADR deny texts verbatim (unquoted heredoc, unbalanced quote, `git commit`) | dl-b-report |
| dl-c-dispatch | 12, 13, 14, 15, 16 | `skills/dev-loop/scripts/claude_lane.py`, `skills/dev-loop/scripts/adapters.py`, `skills/dev-loop/scripts/devloop.sh`, `skills/dev-loop/assets/lane-schema.json`, `skills/dev-loop/assets/templates/prompts/nested-claude-lanes.md`, `tests/test_claude_lane_ownership.py`, `tests/test_admission.py`, `tests/test_claude_lane.py` | `--check-only` disjoint / merged `--requires` in temp repos; `dispatch --check-only` (consumed by dl-g-quota) | `OWNERSHIP OVERLAP: ...`; `REQUIRES UNMET: ...`; `ADMISSION REFUSED: ...` (rc 75); `full gate: FAIL (exit 3)`; `... ends in '\|\| true', so it can never fail` | dl-c-guards |
| dl-h-manager-counter | 1 (counter) | `skills/dev-loop/scripts/live_managers.py`, `skills/dev-loop/scripts/agy_host.sh`, `tests/test_live_managers.py` | temp run dirs with `manager.json` {pid, mode} for 3 live child pids + 1 dead pid → count 3, launch allowed | 4 live → `MANAGER CAP: 4 live AGY managers (cap 4); refusing a 5th`; 2 live teamwork + teamwork launch → `TEAMWORK CAP: 2 live teamwork trees (cap 2); refusing`; dead pid counted (plant) → `STALE MANAGER COUNTED: pid <n> is not alive`; `agy_host.sh` launched with the check planted out while 4 are live → `CAP NOT ENFORCED: agy_host.sh launched a 5th manager` | none (lanes); P-1, P-3 |
| dl-d-invariants | 17, 18, 19, 20, 21 | `skills/dev-loop/scripts/lane_invariants.py`, `skills/dev-loop/scripts/adapters.py`, `skills/dev-loop/scripts/claude_lane.py`, `skills/dev-loop/scripts/gate_audit.py`, `skills/dev-loop/references/gate-audit.md`, `tests/test_lane_invariants.py`, `tests/test_gate_audit.py` | 196894c / 219049e diffs clean | `SOURCE_TEXT_ASSERT ...`; `BARE_PORT ... 8443` + `HARDCODED_IP ... 10.0.0.7`; `invariants: 1 finding(s) ...`; `STALE WAIVER: ...`; `COVERAGE MAP DRIFT: ...` | dl-c-dispatch |
| dl-e-merge | 22, 23, 24, 26 | `skills/dev-loop/scripts/claude_lane.py`, `skills/dev-loop/scripts/adapters.py`, `skills/dev-loop/scripts/devloop.sh`, `skills/dev-loop/scripts/DevLoop.ps1`, `skills/dev-loop/scripts/devloop_mcp.py`, `tests/test_freshness.py`, `tests/test_launcher_base.py`, `tests/test_lane_isolation_leakage.py`, `tests/test_mcp_structured.py` | freshness/merge-preview in temp repos; §3.26 positive (initialize 2025-11-25, and `_meta` 2026-07-28 without initialize) | ADR texts + §3.26 `STRUCTURED CONTENT ON OLD PROTOCOL: ...` and `PER-REQUEST VERSION IGNORED: ...`; exit 2 from merge-tree -> `broken` | dl-d-invariants |
| dl-f-integrate | 27 (lane 1), 29 | `skills/dev-loop/assets/lane-schema.json`, `skills/dev-loop/scripts/adapters.py`, `skills/dev-loop/scripts/claude_lane.py`, `skills/dev-loop/scripts/devloop.sh`, `tests/test_integrate.py`, `tests/test_lane_isolation_leakage.py` | a/b/c temp branches merge | §3.27 texts; `OWNERSHIP VIOLATION: src/a/b/evil.txt` | dl-e-merge |
| dl-f-review | 27 (lane 2), 28 | `skills/dev-loop/scripts/review.py`, `skills/dev-loop/references/harness-adapters.md`, `skills/dev-loop/assets/lanes.proposer.example.json`, `tests/test_review.py`, `tests/test_prompt_templates.py` | `adapters.py validate lanes.proposer.example.json` exits 0 | `lane apply: depends_on unknown lane ghost`; review reasons label substring fallback `heuristic` | dl-f-integrate |
| dl-x-a2a-extensions | 8, 9, 26 (ext) | `skills/dev-loop/assets/a2a-extensions/contract-update-v1.json`, `.../lane-status-v1.json`, `.../gate-verdict-v1.json`, `tests/test_a2a_extensions.py` | gate-verdict/v1 validates a `gate-<id>.json` produced by running dl-e-merge's gate on a temp repo; lane-status/v1 validates every row of dl-b-contract's status table; contract-update/v1 validates the object derived from dl-b-report's sink entry. The Message wrapper is a **hand-written schema instance, labelled so** (no emitter until the bridge) | `EXTENSION DRIFT: lane-status/v1 lacks blocked cause external` | dl-f-integrate |
| dl-g-quota | 30 steps 1-4 | `skills/dev-loop/scripts/adapters.py`, `skills/dev-loop/scripts/claude_lane.py`, `skills/dev-loop/references/postmortem.md`, `skills/dev-loop/assets/templates/prompts/nested-claude-lanes.md`, `skills/dev-loop/assets/a2a-extensions/quota-v1.json`, `tests/test_quota.py` | §3.30 runnable list (exit map, sibling window, quota/v1). Parse/detector UNTESTED | `QUOTA REPORTED AS BUSY: ...`; `QUOTA WINDOW OPEN: ...` / `QUOTA WINDOW IGNORED: ...`; `EXTENSION DRIFT: quota/v1 lacks reset_at`; `QUOTA MISSED: ...` (future, UNTESTED) | dl-f-review, dl-x-a2a-extensions; P-1 |

Sequence: wave 1 `dl-r-corpus-safety`, `dl-a-hygiene`, `dl-h-manager-counter` (after P-1, P-3; it shares no path
with any other ADR lane, and AGENTS.md already claims "Launchers refuse a fifth", which is false until it lands);
then b-contract → b-report → c-guards (after P-2) → c-dispatch → d-invariants → e-merge → f-integrate →
{f-review, x-a2a-extensions} → g-quota (after P-1). Rev 3 ordered `dl-h-manager-counter` after `dl-c-dispatch`
as INFERRED ordering only; with no shared path and the counter decided, that edge is removed. Models per AGENTS.md: opus xhigh one at a time for
b-report, c-*, d, e, f-integrate, g; sonnet medium for r, a, b-contract, h, f-review, x.

## 5. Operator questions

**Closed in rev 4 (operator, 2026-09-26):** Q1 (item 1) → amend the ledger to "not pushed" (P-1) and build
`dl-h-manager-counter` fresh. Q2 (capture store) → extend T-040 `session` rows with kinds
`relay_msg`/`relay_tool_io`; no `relay_capture`.

**Q3 closed (operator, 2026-09-26: "research upstream patterns").** Upstream decides item 7 like items 9-31. No source carries a self-reported report-level host field (Codex exec `file_change{changes[{path,kind}]}` at openai/codex `b334d5b`; Responses `apply_patch` `operation{type,path}`; MCP 2025-11-25 `ToolAnnotations` hints only; A2A 1.0 `metadata`; OTel GenAI v1.41.0 none; SLSA v1.1 `runDetails.byproducts` is the nearest analogue). Decision: **keep item 7 as `modify`, renamed** to `out_of_tree_changes: [{kind: file|package|service|env|config|process|network, target, action: add|update|delete|start|stop|install|remove}]`, required under `strict: true`, default `[]`, warn-only in the gate (self-reported; a host-diff detector is future work). `base_sha` (item 25) unchanged. The original question follows for the record.

**Q3 (original text).** The rule "items 5-8 kept only with a cited MiOS roadmap/ADR/TASKS tie": does a
tie to the schema **form** satisfy it for item 7? MiOS ties the report's form (`CLAUDE.md:154` "Every schema is an
OpenAI format"; T-223 `TASKS.md:3094` strict schemas; LANG-04 `ROADMAP.md:370`), but no MiOS row names
`host_state_changes` or `base_sha` (`git grep` in MiOS `02f0f5e`: no hit for either).
1. *(recommended)* The form tie is enough: keep item 7 as `modify` (§3.7); `dl-b-report` ships as written.
2. A field-level tie is required: item 7 drops; `dl-b-report` loses `host_state_changes`, the strict report
   schema stays and still carries item 25's `base_sha` (items 9-31 are decided by upstream patterns and need no MiOS
   tie), and `dl-x`'s contract-update input is
   unchanged because it comes from item 8's sink.

## 6. Changes filed for the SPIKE owner (`SPIKE-monitor-relay.md`, outside this document's write scope)

1. §11 :430: item 4's line is `AGENTS.md:190` at `cd87715` (PR #30 inserted 8 lines above it).
2. §11 :433-436 ties 5-8: use §3.5-3.8 ties (item 7: form-only tie, pending Q3).
3. :285 and §11 :437: fleet slots = item 1's AGY-manager counter (`dl-h-manager-counter`, decided), not item 14.
4. §11 :437: exit 69 in claude_lane, HTTP 429 + `Retry-After` at the relay; drop `EX_TEMPFAIL`.
5. D4 (:410) and §8 (:292): negative text `SECRET IN CAPTURE: <file>:<n> api-secret-key; refusing to write the
   fixture` (kind name from the pinned pattern JSON, never the matched prefix). The rest of rev 3's item 5
   (pinned `secret-patterns.devloop.json`, parity test, hostname plant) is already in SPIKE rev 3 §8.1 and D4.
6. D1: the bridge refuses vendor secret shapes (the same JSON) on the egress leg to the spoke ingress, because
   MiOS `redact.py` cannot carry them (Law 5).
7. D1/D3: add the §3.8 step 5 final hop (append relayed `contract-update/v1` to the manager's
   `<run>/contract-updates.md`). M3: add §3.8 step 3 routing via `relay_session`.
8. :221, :296, M1 :395, M3 :397 (decided): drop `relay_capture`. M3 writes relay items as T-040 `session` rows,
   kinds `relay_msg`/`relay_tool_io`, through `dbwrite.py` → `stamp_session` → `_SESSION_CHAINER`
   (`mios_pipe/observability/audit.py:153,195,197`), with `relay_ingest` running **inside the agent-pipe process**
   (§0 R-2; a writer in another process forks the chain, and the alternative is DDL), refusing on a secret hit
   **before** `stamp_session` (§0 R-1; nothing does this today); M1 only updates the `kind` comment at `schema-init.sql:203`. M3's negative becomes
   `SECRET PERSISTED: session kind relay_tool_io`; add a second M3 negative: a `relay_tool_io` row served by
   T-040's chat replay → `RELAY ROW IN CHAT REPLAY: <id>` (guards `chat.py:758-760`'s kind filter); add a third: two writers seeded from the same head →
   `SESSION CHAIN FORK: duplicate chain_seq <n>` (§0 R-2).
9. M2 (:313): the `redact.py:6` note in §3.31 row 6.
10. D6 (:412): add P-2 (the no-merge PR, `846164c`, also edits `hooks/hooks.json`) to D6's deps.
11. GitHub MCP section, DL-REVIEW-DOCS: under "Copilot tailoring = AGENTS.md only" drop its `.github/**` paths;
    its `devloop_mcp.py` annotation edit depends on `dl-e-merge`. The task text's "enforced now by ... PR #30" is
    wrong: PR #30 carried only the legibility-drain bullet; the no-merge commit `846164c` has no PR yet (P-2).
12. §13 Q4 is answered (A2O migrates): M12 runs; name the -dev-loop lane and paths that receive the vendor keys
    and CLI installs (this document excludes `skills/dev-loop/scripts/env/**` and `bridge/**` for it).
Last line for the operator brief: item 7's MiOS tie is to the schema form only (§3.7).
