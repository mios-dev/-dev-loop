use axum::{
    extract::Json,
    http::{HeaderMap, StatusCode, Uri},
    routing::{get, post},
    Router,
};
use serde_json::{json, Value};
use std::io::{self, BufRead, Write};

use crate::{translate, TranslateRequest};

/// MCP Streamable HTTP transport, per the current MCP specification line
/// (2025-06-18 and later revisions through 2026-07-28, matching the upstream
/// `mcp` SDK 2.x line this bridge is deployed alongside).
///
/// - POST /mcp carries one JSON-RPC 2.0 message per request body (batching was
///   removed from the spec; an array is rejected with -32600).
/// - Responses are single JSON objects (`application/json`), which the spec
///   permits when the server has no server-initiated stream.
/// - GET /mcp and DELETE /mcp return 405: this server offers no SSE stream
///   and no sessions (stateless servers MAY omit Mcp-Session-Id).
/// - After initialization, clients send MCP-Protocol-Version; an unsupported
///   version is rejected with 400 as the spec prescribes.
pub const LATEST_PROTOCOL_VERSION: &str = "2026-07-28";
pub const SUPPORTED_PROTOCOL_VERSIONS: [&str; 3] =
    ["2026-07-28", "2025-11-25", "2025-06-18"];

pub fn router() -> Router {
    Router::new()
        .route("/health", get(|| async { Json(json!({"status":"ok"})) }))
        .route("/translate", post(translate_http))
        .route("/mcp", post(mcp_http).get(mcp_unsupported).delete(mcp_unsupported))
}

fn local_request(headers: &HeaderMap) -> bool {
    let host = headers
        .get("host")
        .and_then(|v| v.to_str().ok())
        .unwrap_or("");
    let loopback = |name: &str| matches!(name, "127.0.0.1" | "localhost" | "[::1]");
    let host_ok = host
        .parse::<axum::http::uri::Authority>()
        .is_ok_and(|authority| loopback(authority.host()));
    let origin_ok = headers
        .get("origin")
        .and_then(|v| v.to_str().ok())
        .map(|origin| {
            origin.parse::<Uri>().is_ok_and(|uri| {
                uri.scheme_str() == Some("http")
                    && uri
                        .authority()
                        .is_some_and(|authority| loopback(authority.host()))
            })
        })
        .unwrap_or(true);
    host_ok && origin_ok
}

async fn translate_http(
    headers: HeaderMap,
    Json(body): Json<TranslateRequest>,
) -> Result<Json<Value>, (StatusCode, Json<Value>)> {
    if !local_request(&headers) {
        return Err((
            StatusCode::FORBIDDEN,
            Json(json!({"error":"LOCAL HOST REQUIRED"})),
        ));
    }
    translate(body)
        .map(|value| Json(serde_json::to_value(value).expect("serializable translation")))
        .map_err(|error| (StatusCode::BAD_REQUEST, Json(json!({"error":error}))))
}

async fn mcp_unsupported() -> (StatusCode, Json<Value>) {
    (
        StatusCode::METHOD_NOT_ALLOWED,
        Json(json!({"jsonrpc":"2.0","error":{
            "code":-32601,
            "message":"MCP METHOD NOT ALLOWED: this server answers POST /mcp only (no server-initiated streams, no sessions)"}})),
    )
}

async fn mcp_http(
    headers: HeaderMap,
    body: axum::body::Bytes,
) -> Result<(StatusCode, Json<Value>), (StatusCode, Json<Value>)> {
    if !local_request(&headers) {
        return Err((
            StatusCode::FORBIDDEN,
            Json(json!({"error":"LOCAL HOST REQUIRED"})),
        ));
    }
    // Spec: once initialized, every request carries MCP-Protocol-Version; a
    // version the server does not support is a 400 before any dispatch.
    if let Some(version) = headers
        .get("mcp-protocol-version")
        .and_then(|value| value.to_str().ok())
    {
        if !supported_protocol_version(version) {
            return Err((
                StatusCode::BAD_REQUEST,
                Json(json!({"jsonrpc":"2.0","id":null,"error":{
                    "code":-32600,
                    "message":format!("UNSUPPORTED MCP-PROTOCOL-VERSION: {version} (supported: {SUPPORTED_PROTOCOL_VERSIONS:?}, latest {LATEST_PROTOCOL_VERSION})")}})),
            ));
        }
    }
    let message: Value = match serde_json::from_slice(&body) {
        Ok(value) => value,
        Err(_) => {
            return Ok((
                StatusCode::OK,
                Json(json!({"jsonrpc":"2.0","id":null,"error":{
                    "code":-32700,"message":"MCP PARSE ERROR"}})),
            ))
        }
    };
    if message.as_array().is_some() {
        // JSON-RPC batching was removed from the MCP streamable transport.
        return Ok((
            StatusCode::OK,
            Json(json!({"jsonrpc":"2.0","id":null,"error":{
                "code":-32600,"message":"MCP BATCHING NOT SUPPORTED: one message per POST"}})),
        ));
    }
    Ok(match mcp_dispatch(&message) {
        Some(response) => (StatusCode::OK, Json(response)),
        // Notifications (no id) must yield 202 Accepted with no body.
        None => (StatusCode::ACCEPTED, Json(json!({}))),
    })
}

fn supported_protocol_version(version: &str) -> bool {
    SUPPORTED_PROTOCOL_VERSIONS.contains(&version)
}

fn negotiated_version(requested: Option<&str>) -> String {
    match requested {
        Some(version) if supported_protocol_version(version) => version.to_owned(),
        // Spec: respond with the latest version the server supports when the
        // client asked for one the server does not know.
        _ => LATEST_PROTOCOL_VERSION.to_owned(),
    }
}

pub fn mcp_dispatch(request: &Value) -> Option<Value> {
    let id = request.get("id")?.clone();
    let method = request.get("method").and_then(Value::as_str).unwrap_or("");
    let params = request.get("params").cloned().unwrap_or(Value::Null);
    let result: Result<Value, (i32, String)> = match method {
        "initialize" => {
            let requested = params
                .get("protocolVersion")
                .and_then(Value::as_str)
                .map(str::to_owned);
            Ok(json!({
                "protocolVersion": negotiated_version(requested.as_deref()),
                "capabilities":{"tools":{}},
                "serverInfo":{"name":"devloop-bridge","version":env!("CARGO_PKG_VERSION")},
                "instructions":"Loop translation for AGY, Claude, OpenAI Responses/Codex, and any OpenAI-compatible Chat Completions harness. Read-only: no model call, no permission grant, no credentials."
            }))
        }
        "ping" => Ok(json!({})),
        "notifications/initialized" | "notifications/cancelled" => return None,
        "tools/list" => Ok(json!({"tools":[{
            "name":"translate_frames",
            "description":"Normalize frames from AGY, Claude, OpenAI Responses/Codex, or any OpenAI-compatible harness (Chat Completions: vLLM, llama.cpp, LM Studio, Ollama, OpenRouter, custom agents) to ordered loop.v1 events and Responses items. Source 'auto' sniffs the dialect. No model call or permission grant occurs.",
            "inputSchema":{"type":"object","additionalProperties":false,
                "required":["source","frames"],"properties":{
                    "source":{"type":"string","enum":["auto","agy","claude","openai","openai_responses","codex","openai_chat","chat_completions","openai_compatible","generic"]},
                    "frames":{"type":"array","items":{"type":"object"}},
                    "evidence":{"type":"object","required":["diff_bytes","positive","negative","tree_restored","exit_code"],
                        "properties":{"diff_bytes":{"type":"integer"},"positive":{"type":"boolean"},
                        "negative":{"type":"boolean"},"tree_restored":{"type":"boolean"},
                        "exit_code":{"type":"integer"},"timed_out":{"type":"boolean"}}}
                }}
        }]})),
        "tools/call" => tools_call(&params),
        _ => Err((-32601, "MCP METHOD NOT FOUND".to_owned())),
    };
    Some(match result {
        Ok(value) => json!({"jsonrpc":"2.0","id":id,"result":value}),
        Err((code, message)) => json!({"jsonrpc":"2.0","id":id,"error":{"code":code,"message":message}}),
    })
}

fn tools_call(params: &Value) -> Result<Value, (i32, String)> {
    let name = params
        .get("name")
        .and_then(Value::as_str)
        .ok_or((-32602i32, "MCP INVALID PARAMS: tool name missing".to_owned()))?;
    if name != "translate_frames" {
        return Err((-32602, format!("MCP UNKNOWN TOOL: {name}")));
    }
    let args = params
        .get("arguments")
        .cloned()
        .ok_or((-32602, "MCP INVALID PARAMS: arguments missing".to_owned()))?;
    let parsed: TranslateRequest = serde_json::from_value(args)
        .map_err(|_| (-32602, "MCP INVALID PARAMS: malformed arguments".to_owned()))?;
    let translated = translate(parsed).map_err(|message| (-32602, format!("MCP TOOL ERROR: {message}")))?;
    Ok(json!({"content":[{"type":"text","text":serde_json::to_string(&translated)
        .expect("serializable translation")}],"structuredContent":translated}))
}

pub fn run_stdio() -> io::Result<()> {
    let stdin = io::stdin();
    let mut stdout = io::stdout().lock();
    for line in stdin.lock().lines() {
        let line = line?;
        let response = match serde_json::from_str::<Value>(&line) {
            Ok(request) => mcp_dispatch(&request),
            Err(_) => Some(json!({"jsonrpc":"2.0","id":null,"error":{
                "code":-32700,"message":"MCP PARSE ERROR"}})),
        };
        if let Some(response) = response {
            serde_json::to_writer(&mut stdout, &response)?;
            stdout.write_all(b"\n")?;
            stdout.flush()?;
        }
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use axum::{
        body::{to_bytes, Body},
        http::Request,
    };
    use tower::ServiceExt;

    #[test]
    fn loopback_hosts_and_origins_only() {
        let mut headers = HeaderMap::new();
        headers.insert("host", "127.0.0.1:8765".parse().unwrap());
        assert!(local_request(&headers));
        headers.insert("origin", "http://localhost:3000".parse().unwrap());
        assert!(local_request(&headers));
        headers.insert("origin", "http://localhost.evil.example".parse().unwrap());
        assert!(!local_request(&headers));
        headers.remove("origin");
        headers.insert("host", "localhost.evil.example:8765".parse().unwrap());
        assert!(!local_request(&headers));
    }

    #[test]
    fn initialize_negotiates_protocol_version() {
        let echo = mcp_dispatch(&json!({"jsonrpc":"2.0","id":1,"method":"initialize",
            "params":{"protocolVersion":"2025-06-18"}}))
            .expect("response");
        assert_eq!(echo["result"]["protocolVersion"], "2025-06-18");
        let upgrade = mcp_dispatch(&json!({"jsonrpc":"2.0","id":2,"method":"initialize",
            "params":{"protocolVersion":"1999-01-01"}}))
            .expect("response");
        assert_eq!(upgrade["result"]["protocolVersion"], LATEST_PROTOCOL_VERSION);
        let none = mcp_dispatch(&json!({"jsonrpc":"2.0","id":3,"method":"initialize","params":{}}))
            .expect("response");
        assert_eq!(none["result"]["protocolVersion"], LATEST_PROTOCOL_VERSION);
        assert!(none["result"]["serverInfo"]["name"].is_string());
    }

    #[test]
    fn unknown_method_and_tool_use_spec_error_codes() {
        let missing = mcp_dispatch(&json!({"jsonrpc":"2.0","id":1,"method":"no/such"})).unwrap();
        assert_eq!(missing["error"]["code"], -32601);
        let unknown_tool = mcp_dispatch(&json!({"jsonrpc":"2.0","id":2,"method":"tools/call",
            "params":{"name":"fetch_url","arguments":{}}}))
            .unwrap();
        assert_eq!(unknown_tool["error"]["code"], -32602);
        assert!(unknown_tool["error"]["message"]
            .as_str()
            .unwrap()
            .contains("UNKNOWN TOOL"));
    }

    #[test]
    fn notifications_yield_no_response() {
        assert!(mcp_dispatch(&json!({"jsonrpc":"2.0","method":"notifications/initialized"})).is_none());
    }

    async fn post_mcp(body: String, version_header: Option<&str>) -> axum::http::Response<Body> {
        let mut builder = Request::builder()
            .method("POST")
            .uri("/mcp")
            .header("host", "127.0.0.1:8765")
            .header("content-type", "application/json");
        if let Some(version) = version_header {
            builder = builder.header("mcp-protocol-version", version);
        }
        router()
            .oneshot(builder.body(Body::from(body)).unwrap())
            .await
            .unwrap()
    }

    #[tokio::test]
    async fn http_translation_and_host_rejection() {
        let payload = json!({"source":"agy","frames":[{"event":"result",
            "result":{"status":"SUCCESS","response":"ready"}}]})
        .to_string();
        let allowed = Request::builder()
            .method("POST")
            .uri("/translate")
            .header("host", "127.0.0.1:8765")
            .header("content-type", "application/json")
            .body(Body::from(payload.clone()))
            .unwrap();
        let response = router().oneshot(allowed).await.unwrap();
        assert_eq!(response.status(), StatusCode::OK);
        let body = to_bytes(response.into_body(), 1024 * 1024).await.unwrap();
        let parsed: Value = serde_json::from_slice(&body).unwrap();
        assert!(parsed["schema"].is_string());

        let denied = Request::builder()
            .method("POST")
            .uri("/translate")
            .header("host", "attacker.example")
            .header("content-type", "application/json")
            .body(Body::from(payload))
            .unwrap();
        let response = router().oneshot(denied).await.unwrap();
        assert_eq!(response.status(), StatusCode::FORBIDDEN);
    }

    #[tokio::test]
    async fn mcp_http_streamable_contract() {
        // Batches are rejected with -32600.
        let response = post_mcp(json!([{"jsonrpc":"2.0","id":1,"method":"ping"}]).to_string(), None).await;
        assert_eq!(response.status(), StatusCode::OK);
        let body = to_bytes(response.into_body(), 1024 * 1024).await.unwrap();
        let parsed: Value = serde_json::from_slice(&body).unwrap();
        assert_eq!(parsed["error"]["code"], -32600);

        // Notifications answer 202 with an empty body.
        let response = post_mcp(
            json!({"jsonrpc":"2.0","method":"notifications/initialized"}).to_string(),
            None,
        )
        .await;
        assert_eq!(response.status(), StatusCode::ACCEPTED);

        // Unsupported MCP-Protocol-Version headers are a 400 before dispatch.
        let response = post_mcp(json!({"jsonrpc":"2.0","id":1,"method":"ping"}).to_string(), Some("2000-01-01")).await;
        assert_eq!(response.status(), StatusCode::BAD_REQUEST);

        // A supported version header dispatches normally.
        let response = post_mcp(
            json!({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2026-07-28"}}).to_string(),
            Some("2026-07-28"),
        )
        .await;
        assert_eq!(response.status(), StatusCode::OK);
        let body = to_bytes(response.into_body(), 1024 * 1024).await.unwrap();
        let parsed: Value = serde_json::from_slice(&body).unwrap();
        assert_eq!(parsed["result"]["protocolVersion"], "2026-07-28");

        // GET and DELETE are 405 (no server-initiated streams, no sessions).
        for method in ["GET", "DELETE"] {
            let request = Request::builder()
                .method(method)
                .uri("/mcp")
                .header("host", "127.0.0.1:8765")
                .body(Body::empty())
                .unwrap();
            let response = router().oneshot(request).await.unwrap();
            assert_eq!(response.status(), StatusCode::METHOD_NOT_ALLOWED);
        }
    }
}
