# Dev-loop translation bridge

This crate implements a local loop translation service. It converts harness frames into
ordered `loop.v1` events and OpenAI Responses items. It does not impersonate a model
endpoint or translate permissions. The source adapters are selected explicitly; adding
a harness requires an adapter, not a new transport.

## Definition of done for this slice

- Objective: AGY, Claude, and OpenAI Responses/Codex frames retain text, tool calls,
  tool outputs, and terminal outcomes in one ordered representation.
- Positive controls: `cargo test` verifies each adapter, HTTP and stdio MCP dispatch,
  and Responses item projection. `cargo build --release` builds the binary.
- Negative controls: unknown sources and malformed tool calls fail with named errors;
  a terminal success without work is `vacuous`, and a missing terminal is `errored`.
- Non-goals: model API proxying, remote exposure, CLI invocation, credential forwarding,
  permission translation, forge integration, A2A transport, and network authentication.
- Stop condition: the adapter and local transport checks pass. Remote deployment awaits
  the authenticated bridge core defined by the relay design.

## Run

`devloop-bridge serve` binds `127.0.0.1:8765`. `POST /translate` accepts
`{"source":"auto|agy|claude|openai|openai_responses|codex|openai_chat|chat_completions|openai_compatible|generic","frames":[...],"evidence":{...}}` and returns
`{"schema":"loop.v1","events":[...],"responses_items":[...]}`. `POST /mcp`
serves the MCP Streamable HTTP transport (one JSON-RPC message per POST;
notifications answer `202`; batches are rejected with `-32600`; `GET`/`DELETE`
answer `405` because this server is stateless and offers no server-initiated
streams) for `initialize`, `tools/list`, and `tools/call` of `translate_frames`.
`devloop-bridge stdio` serves the same MCP tool over stdio.
Protocol negotiation follows the current spec: `initialize` echoes a supported
client version (`2026-07-28`, `2025-11-25`, `2025-06-18`) and otherwise answers
with the server's latest (`2026-07-28`); requests carrying an unsupported
`MCP-Protocol-Version` header are rejected with `400` before dispatch.
No client bearer token or harness credential is read or forwarded.
Known credential fields in frames are refused before any translation result is returned;
the rejection reports only the field name.

`openai` and `codex` consume Responses output items and completed stream events.
`openai_chat` (aliases `chat_completions`, `openai_compatible`, `generic`)
consumes the OpenAI-compatible Chat Completions dialect spoken by vLLM,
llama.cpp, LM Studio, Ollama, OpenRouter, OpenWebUI and custom agents:
non-streaming response objects, streaming chunks (tool-call argument
fragments are accumulated per index until the terminal chunk), and bare
transcript messages including `role:"tool"` results. `auto` sniffs the wire
dialect from the first informative frame.
`claude` consumes print-mode stream JSON frames. `agy` consumes its stream JSON
`step_update` and `result` frames. Tool output is associated with its call ID;
AGY tools without a native call ID receive a stable ID from conversation and step index.
The status is `unverified` until two-sided gate evidence is supplied; a success word in a
harness result alone is never promoted to `delivered`.

## Protocol references

- [OpenAI Responses API](https://platform.openai.com/docs/api-reference/responses)
- [OpenAI Chat Completions API](https://platform.openai.com/docs/api-reference/chat)
- [MCP Streamable HTTP transport (2026-07-28 line)](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports)
- [MCP versioning and negotiation](https://modelcontextprotocol.io/specification/2026-07-28/basic/versioning)
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code/cli-usage)
- `docs/decisions/0001-loop-translation-layer-serve-both-harnesses-translate-the-lo.md`
- `docs/research/monitor-relay-spike-2026-09.md`, rows D1-D3
