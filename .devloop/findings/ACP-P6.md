## VERDICT
REFUTED

## WHAT IS ACTUALLY TRUE
1. **Native ACP Support in `agy`**: `agy` has not gained a native `--acp` mode. The `google-antigravity/antigravity-cli` issue #31 remains a feature request for an ACP stdio JSON-RPC mode as of 2026-09. Developers currently rely on third-party adapters like `jiridanek/agy-acp` (which wraps the SDK) rather than first-party CLI support (see https://github.com/google-antigravity/antigravity-cli/issues/31, 2026-09-19).

2. **ACP Transport Costs**: Switching to an ACP transport would require rewriting the communication layer in several scripts:
   - `skills/dev-loop/scripts/agy_session.py`: The script currently holds the session open by speaking the NDJSON wire protocol, handling proprietary events like `init`, `step_update`, and `result` (skills/dev-loop/scripts/agy_session.py:27). This would need to be completely rewritten to speak JSON-RPC 2.0.
   - `skills/dev-loop/scripts/adapters.py`: The CLI flag `--output-format json` (skills/dev-loop/scripts/adapters.py:214) would be replaced. Moreover, `find_envelope` and report normalization would have to parse ACP messages instead of agy's proprietary envelope to capture auto-denied tool calls (skills/dev-loop/scripts/adapters.py:344).
   - `skills/dev-loop/scripts/agy_host.sh`: The flag surface for the headless mode (skills/dev-loop/scripts/agy_host.sh:146) and session mode would change from `--output-format json` and `--input-format stream-json` to the new ACP mode.

3. **Loss of Fidelity**: The ACP standard is generally designed for editor-to-agent interactions, not necessarily exposing internal Google Antigravity features. The current NDJSON channel natively emits exact Google-specific events, including `step_update` with child `conversation_id`s, and detailed `permission_denials`. ACP might not carry this exact denial surface or subagent lifecycle events without custom extensions, meaning we could lose the fidelity needed to correctly track subagent reporting and denied actions. 

**Recommendation**: Wait. It is not worth adopting a third-party wrapper (`jiridanek/agy-acp`) that might obscure the exact internal events (like subagent dispatches and denials) that the dev-loop currently relies upon.

## NUMBERS
- `agy_session.py` requires 1 JSON message per turn (NDJSON)
- 3 core files require modification for transport migration

## PROPOSED FIX
Do not migrate to ACP at this time. Maintain the current `stream-json` and `json` NDJSON channel which natively supports the per-turn result envelope, subagent steps, and denial surface without a third-party translation layer.

## FILES TO CHANGE
If ACP were to be adopted, changes would occur in:
- `skills/dev-loop/scripts/agy_session.py`
- `skills/dev-loop/scripts/adapters.py`
- `skills/dev-loop/scripts/agy_host.sh`

## NEGATIVE CONTROL
PLANTED-ACP-NOPE

## UNVERIFIED
- The exact mapping of agy's `step_update` event to an ACP JSON-RPC notification.
- Whether a future official `--acp` flag will expose internal `permission_denials`.
