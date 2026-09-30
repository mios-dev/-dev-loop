# Dev-loop translation bridge

This crate implements a local loop translation service. It converts harness frames into
ordered `loop.v1` events and OpenAI Responses items. It does not impersonate a model
endpoint or translate permissions. Select an adapter explicitly or detect it from the
first informative frame. Adding a harness requires an adapter, not a new transport.

## Definition of done for this slice

- Objective: AGY, Claude, OpenAI Responses/Codex, and OpenAI-compatible Chat
  Completions frames retain text, tool calls, tool outputs, and terminal outcomes
  in one ordered representation.
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
serves MCP Streamable HTTP: one JSON-RPC message per POST, empty `202` responses
for notifications, and `405` for GET/DELETE. Every MCP HTTP method rejects foreign
origins and hosts. Invalid messages and batches fail with named protocol errors.
`devloop-bridge stdio` serves the same translation tool.

Modern MCP `2026-07-28` requests use per-request metadata and `server/discover`;
there is no initialization handshake. HTTP requests must mirror the protocol
version and method in headers; tool calls also mirror the tool name, including
Base64 sentinel decoding. Missing capabilities and mismatched headers fail before
translation. Unsupported versions return `-32022` with the supported versions;
unknown modern HTTP methods return `404` with `-32601`.

Legacy clients negotiate `2025-11-25` or `2025-06-18` through `initialize`.
A legacy request for a modern or unknown revision receives the latest supported
legacy revision, rather than a modern version with legacy behavior.
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
