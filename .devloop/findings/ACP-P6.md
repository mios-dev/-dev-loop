## VERDICT
REFUTED

The proposal in ADR 0001 (open question 6) to evaluate `jiridanek/agy-acp` or adopt ACP (Agent Client Protocol) as an alternative lane transport to the NDJSON channel for phase P6 is REFUTED. Upstream investigation reveals that `agy` does not possess native ACP support, `jiridanek/agy-acp` is an incompatible wrapper over the Python SDK rather than the CLI, and ACP cannot carry the result envelope, subagent conversation tracking, or auto-denial surfaces currently provided by the NDJSON channel.

## WHAT IS ACTUALLY TRUE

1. **Current State of Native `agy --acp` and Upstream Issue #31**:
   - `google-antigravity/antigravity-cli` issue #31 ("Feature request: add ACP (Agent Client Protocol) stdio JSON-RPC mode", opened 2026-05-20T03:58:03Z by Joseph19820124; URL: https://github.com/google-antigravity/antigravity-cli/issues/31) remains **OPEN** as of 2026-09-27.
   - Issue metadata: `state: OPEN`, `stateReason: null`, `milestone: null`, assigned to `chandrashakherkamasani`.
   - Across 192 user comments/reactions, there are zero responses from Google maintainers or project members (every authorAssociation on the issue is `NONE`).
   - Direct verification against the installed binary (`agy` version 1.2.12) confirms that no native `--acp` flag or `acp` subcommand exists in the CLI; `agy` supports only `--input-format text|stream-json` and `--output-format text|json|stream-json`.

2. **Evaluation of `jiridanek/agy-acp`**:
   - Upstream source (https://github.com/jiridanek/agy-acp, checked 2026-09-27) reveals that `jiridanek/agy-acp` does **not** wrap or drive the `agy` CLI binary. Instead, it is a Python wrapper around the `google-antigravity` Python SDK (`pip install google-antigravity`).
   - It requires a standalone `GEMINI_API_KEY` (AI Studio or Vertex AI), explicitly stating that third-party software cannot use an Antigravity account without violating Google's Terms of Service. This conflicts with this repo's shared Ultra subscription quota pool (documented in skills/dev-loop/references/translation-layer.md:24).
   - Its documentation explicitly states: *"Windows is not supported — symlinks used for skill discovery"*, making it unusable on Windows development environments.
   - The underlying `google-antigravity` SDK runtime is a closed compiled binary wheel with `max_subagent_depth` defaulting to 1 (cited in docs/decisions/0001-loop-translation-layer-serve-both-harnesses-translate-the-lo.md:143 and skills/dev-loop/references/translation-layer.md:377), lacking the CLI's native multi-agent execution machinery.

3. **Cost of an ACP Transport in This Repository**:
   Replacing or supplementing the NDJSON transport with ACP would impact three core scripts in this repo:
   - `skills/dev-loop/scripts/agy_session.py`: Currently implements the held NDJSON session protocol using `agy --input-format stream-json --output-format stream-json -p=''` (skills/dev-loop/scripts/agy_session.py:21 and skills/dev-loop/scripts/agy_session.py:550). It parses stream events (`init`, `step_update`, `result`; skills/dev-loop/scripts/agy_session.py:682) and drives the multi-turn polling loop. An ACP transport would require replacing this with a JSON-RPC 2.0 client (`initialize`, `session/new`, `session/prompt`), managing external bridge subprocesses, and sacrificing session hold/remote-control integration.
   - `skills/dev-loop/scripts/adapters.py`: Currently handles envelope parsing and tool denial detection via `find_envelope` and `DENIAL_KEYS = ("permission_denials", "denied_actions")` (skills/dev-loop/scripts/adapters.py:403 and skills/dev-loop/scripts/adapters.py:406). Line skills/dev-loop/scripts/adapters.py:279 dispatches `agy` with `--output-format json`. An ACP transport produces no such terminal envelope, forcing `adapters.py` to reconstruct synthetic envelopes from notification streams, obscuring harness denials (skills/dev-loop/scripts/adapters.py:466).
   - `skills/dev-loop/scripts/agy_host.sh`: Currently configures `--headless` (skills/dev-loop/scripts/agy_host.sh:234) and `--session` (skills/dev-loop/scripts/agy_host.sh:254) modes, sourcing keyring credentials (`~/.config/agy-cloud/keyring.env`), passing `--remote-control`, and selecting prompt templates. ACP would require a separate mode branching, external API key configuration, and prompt dispatch restructuring.

4. **Protocol Fidelity: NDJSON vs. ACP**:
   ACP cannot carry what the first-party NDJSON stream already delivers:
   - **Per-Turn Result Envelope**: `agy`'s NDJSON emits a deterministic `result` event per turn containing `conversation_id`, `status`, `duration_seconds`, `num_turns`, detailed `usage` (including `thinking_tokens` and `cache_read_tokens`), and `denied_actions`. In ACP v2, `session/prompt` merely acknowledges the prompt; completion is signaled by `state_update` stop reasons, and token usage is an optional coarse update (`used`, `size`, `cost`).
   - **Subagent Steps & Child Conversation IDs**: `agy` NDJSON streams `step_update` events with `step_type: "subagent"` containing `subagent_info.subagents[]{type_name, role, initial_prompt, conversation_id}` (skills/dev-loop/scripts/agy_session.py:693). ACP models a flat 1:1 editor-to-agent session and has no data structure or protocol event for child subagents or subagent conversation IDs.
   - **Denial Surface**: Headless unapproved tools in `agy` are surfaced post-hoc in `denied_actions` within the `result` event (skills/dev-loop/scripts/adapters.py:403). ACP relies on interactive client-side permission approvals; an automated ACP client must either approve all tools or reject them, leaving no native audit trail of auto-denials.

**Recommendation**: WAIT. Retain the first-party NDJSON channel (`agy_session.py`) as the primary transport. Do not adopt `jiridanek/agy-acp` or invest in an ACP transport for P6 until Google provides an official, native `--acp` implementation in `agy` that preserves multi-agent and denial telemetry.

## NUMBERS
- `0`: Native ACP flags or subcommands in `agy` 1.2.12
- `0`: Responses from Google maintainers on `google-antigravity/antigravity-cli` issue #31 (all author associations: NONE)
- `192`: Community interaction comments on issue #31 as of September 2026
- `1`: Default `max_subagent_depth` in the `google-antigravity` Python SDK wrapped by `agy-acp`
- `3`: Core repository files required to change for an ACP transport migration (`agy_session.py`, `adapters.py`, `agy_host.sh`)

## PROPOSED FIX
Do not adopt `jiridanek/agy-acp` or implement P6 ACP transport at this time. Close open question 6 in ADR 0001 / `translation-layer.md` with the decision to keep the first-party NDJSON stdio channel (`--input-format stream-json --output-format stream-json`), which natively supports stateful multi-turn sessions, subagent tracking, token usage breakdown, and silent-denial detection.

## FILES TO CHANGE
If ACP were to be adopted in the future upon a native Google release, the affected files would be:
- `skills/dev-loop/scripts/agy_session.py` (rewrite transport from NDJSON to JSON-RPC 2.0 client)
- `skills/dev-loop/scripts/adapters.py` (rewrite envelope extraction and denial checking)
- `skills/dev-loop/scripts/agy_host.sh` (add ACP launch mode and credential handling)
- `docs/decisions/0001-loop-translation-layer-serve-both-harnesses-translate-the-lo.md` (record P6 evaluation outcome)
- `skills/dev-loop/references/translation-layer.md` (update open question 6 and P6 phasing)

## NEGATIVE CONTROL
The negative control command appends an unresolved citation token (the lane's planted sentinel (named in `.devloop/lanes.research.json`)) to this findings file. When `check_finding.py` evaluates the mutated file, citation resolution fails on the unresolvable reference with a non-zero exit code, matching the sentinel regex the lane's planted sentinel (named in `.devloop/lanes.research.json`).

## UNVERIFIED
- Internal Google timelines or roadmap milestones for implementing native ACP in `agy` (issue #31 has no assigned milestone).
- Whether a future official Google ACP implementation would expose proprietary events (such as `subagent_info` or `denied_actions`) via custom ACP metadata fields.
