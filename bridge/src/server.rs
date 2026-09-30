use axum::{
    extract::Json,
    http::{HeaderMap, StatusCode, Uri},
    response::{IntoResponse, Response},
    routing::{get, post},
    Router,
};
use base64::{engine::general_purpose::STANDARD, Engine};
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
/// - Modern requests carry per-request metadata and mirrored HTTP headers.
///   Legacy clients initialize only with the supported legacy revisions.
pub const LATEST_PROTOCOL_VERSION: &str = "2026-07-28";
pub const SUPPORTED_PROTOCOL_VERSIONS: [&str; 3] = ["2026-07-28", "2025-11-25", "2025-06-18"];

pub fn router() -> Router {
    Router::new()
        .route("/health", get(|| async { Json(json!({"status":"ok"})) }))
        .route("/translate", post(translate_http))
        .route(
            "/mcp",
            post(mcp_http).get(mcp_unsupported).delete(mcp_unsupported),
        )
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
        .map(|value| {
            let Ok(origin) = value.to_str() else {
                return false;
            };
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

fn rpc_error(request: &Value, code: i32, message: &str) -> Value {
    json!({"jsonrpc":"2.0","id":request.get("id").cloned().unwrap_or(Value::Null),
        "error":{"code":code,"message":message}})
}

fn unsupported_version(request: &Value, version: &str) -> Value {
    let mut error = rpc_error(request, -32022, "Unsupported protocol version");
    error["error"]["data"] = json!({"supported":SUPPORTED_PROTOCOL_VERSIONS,"requested":version});
    error
}

fn request_version(request: &Value) -> Option<&str> {
    request
        .pointer("/params/_meta/io.modelcontextprotocol~1protocolVersion")
        .and_then(Value::as_str)
}

fn modern(request: &Value) -> bool {
    request
        .pointer("/params/_meta/io.modelcontextprotocol~1protocolVersion")
        .is_some()
}

async fn mcp_unsupported(headers: HeaderMap) -> Response {
    if !local_request(&headers) {
        return (
            StatusCode::FORBIDDEN,
            Json(json!({"error":"LOCAL HOST REQUIRED"})),
        )
            .into_response();
    }
    StatusCode::METHOD_NOT_ALLOWED.into_response()
}

fn decoded_name(headers: &HeaderMap) -> Option<String> {
    let raw = headers.get("mcp-name")?.to_str().ok()?;
    if let Some(encoded) = raw
        .strip_prefix("=?base64?")
        .and_then(|s| s.strip_suffix("?="))
    {
        return String::from_utf8(STANDARD.decode(encoded).ok()?).ok();
    }
    if raw.trim() != raw || !raw.bytes().all(|b| (0x20..=0x7e).contains(&b)) {
        return None;
    }
    Some(raw.to_owned())
}

async fn mcp_http(headers: HeaderMap, body: axum::body::Bytes) -> Response {
    if !local_request(&headers) {
        return (
            StatusCode::FORBIDDEN,
            Json(json!({"error":"LOCAL HOST REQUIRED"})),
        )
            .into_response();
    }
    let request: Value = match serde_json::from_slice(&body) {
        Ok(value) => value,
        Err(_) => {
            return (
                StatusCode::BAD_REQUEST,
                Json(rpc_error(&Value::Null, -32700, "MCP PARSE ERROR")),
            )
                .into_response()
        }
    };
    let header = headers
        .get("mcp-protocol-version")
        .and_then(|v| v.to_str().ok());
    if modern(&request) || header == Some(LATEST_PROTOCOL_VERSION) {
        let version = request_version(&request);
        let method = request.get("method").and_then(Value::as_str);
        if version.is_none()
            || header != version
            || headers.get("mcp-method").and_then(|v| v.to_str().ok()) != method
            || (method == Some("tools/call")
                && decoded_name(&headers).as_deref()
                    != request.pointer("/params/name").and_then(Value::as_str))
        {
            return (
                StatusCode::BAD_REQUEST,
                Json(rpc_error(&request, -32020, "Header mismatch")),
            )
                .into_response();
        }
        let accepts = headers
            .get("accept")
            .and_then(|v| v.to_str().ok())
            .unwrap_or("");
        if !accepts
            .split(',')
            .any(|s| s.trim().starts_with("application/json"))
            || !accepts
                .split(',')
                .any(|s| s.trim().starts_with("text/event-stream"))
        {
            return StatusCode::NOT_ACCEPTABLE.into_response();
        }
    } else if let Some(value) = headers.get("mcp-protocol-version") {
        if !value.to_str().is_ok_and(supported_protocol_version) {
            return (
                StatusCode::BAD_REQUEST,
                Json(unsupported_version(
                    &request,
                    header.unwrap_or("invalid header"),
                )),
            )
                .into_response();
        }
    }
    match mcp_dispatch(&request) {
        None => StatusCode::ACCEPTED.into_response(),
        Some(response) => {
            let code = response.pointer("/error/code").and_then(Value::as_i64);
            let status = if modern(&request) {
                match code {
                    Some(-32601) => StatusCode::NOT_FOUND,
                    Some(_) => StatusCode::BAD_REQUEST,
                    None => StatusCode::OK,
                }
            } else if matches!(code, Some(-32700 | -32600)) {
                StatusCode::BAD_REQUEST
            } else {
                StatusCode::OK
            };
            (status, Json(response)).into_response()
        }
    }
}

fn supported_protocol_version(version: &str) -> bool {
    SUPPORTED_PROTOCOL_VERSIONS.contains(&version)
}

fn negotiated_version(requested: Option<&str>) -> String {
    match requested {
        Some(version) if SUPPORTED_PROTOCOL_VERSIONS[1..].contains(&version) => version.to_owned(),
        // Spec: respond with the latest version the server supports when the
        // client asked for one the server does not know.
        _ => "2025-11-25".to_owned(),
    }
}

pub fn mcp_dispatch(request: &Value) -> Option<Value> {
    let method = request.get("method").and_then(Value::as_str);
    if request.get("jsonrpc").and_then(Value::as_str) != Some("2.0")
        || method.is_none()
        || request
            .get("id")
            .is_some_and(|id| !id.is_string() && !id.is_number())
        || request
            .get("params")
            .is_some_and(|params| !params.is_object())
    {
        return Some(rpc_error(request, -32600, "MCP INVALID REQUEST"));
    }
    let method = method?;
    let id = request.get("id")?.clone();
    let params = request.get("params").cloned().unwrap_or(Value::Null);
    let is_modern = modern(request);
    if is_modern {
        let Some(version) = request_version(request) else {
            return Some(rpc_error(
                request,
                -32602,
                "Protocol version must be a string",
            ));
        };
        if version != LATEST_PROTOCOL_VERSION {
            return Some(unsupported_version(request, version));
        }
        if !request
            .pointer("/params/_meta/io.modelcontextprotocol~1clientCapabilities")
            .is_some_and(Value::is_object)
        {
            return Some(rpc_error(request, -32602, "Client capabilities required"));
        }
    }
    let result: Result<Value, (i32, String)> = match method {
        "server/discover" if is_modern => {
            Ok(json!({"supportedVersions":SUPPORTED_PROTOCOL_VERSIONS,"capabilities":{"tools":{}}}))
        }
        "initialize" if !is_modern => {
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
        "ping" if !is_modern => Ok(json!({})),
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
        Ok(mut value) => {
            if is_modern {
                value["resultType"] = json!("complete");
                value["_meta"] = json!({"io.modelcontextprotocol/serverInfo":{"name":"devloop-bridge","version":env!("CARGO_PKG_VERSION")}});
            }
            json!({"jsonrpc":"2.0","id":id,"result":value})
        }
        Err((code, message)) => {
            json!({"jsonrpc":"2.0","id":id,"error":{"code":code,"message":message}})
        }
    })
}

fn tools_call(params: &Value) -> Result<Value, (i32, String)> {
    let name = params.get("name").and_then(Value::as_str).ok_or((
        -32602i32,
        "MCP INVALID PARAMS: tool name missing".to_owned(),
    ))?;
    if name != "translate_frames" {
        return Err((-32602, format!("MCP UNKNOWN TOOL: {name}")));
    }
    let args = params
        .get("arguments")
        .cloned()
        .ok_or((-32602, "MCP INVALID PARAMS: arguments missing".to_owned()))?;
    let parsed: TranslateRequest = serde_json::from_value(args)
        .map_err(|_| (-32602, "MCP INVALID PARAMS: malformed arguments".to_owned()))?;
    let translated =
        translate(parsed).map_err(|message| (-32602, format!("MCP TOOL ERROR: {message}")))?;
    Ok(
        json!({"content":[{"type":"text","text":serde_json::to_string(&translated)
        .expect("serializable translation")}],"structuredContent":translated}),
    )
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
        assert_eq!(upgrade["result"]["protocolVersion"], "2025-11-25");
        let none = mcp_dispatch(&json!({"jsonrpc":"2.0","id":3,"method":"initialize","params":{}}))
            .expect("response");
        assert_eq!(none["result"]["protocolVersion"], "2025-11-25");
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
        assert!(
            mcp_dispatch(&json!({"jsonrpc":"2.0","method":"notifications/initialized"})).is_none()
        );
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
        assert_eq!(parsed["responses_items"][0]["content"][0]["text"], "ready");

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
        let response = post_mcp(
            json!([{"jsonrpc":"2.0","id":1,"method":"ping"}]).to_string(),
            None,
        )
        .await;
        assert_eq!(response.status(), StatusCode::BAD_REQUEST);
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
        assert!(to_bytes(response.into_body(), 1024)
            .await
            .unwrap()
            .is_empty());

        // Unsupported MCP-Protocol-Version headers are a 400 before dispatch.
        let response = post_mcp(
            json!({"jsonrpc":"2.0","id":1,"method":"ping"}).to_string(),
            Some("2000-01-01"),
        )
        .await;
        assert_eq!(response.status(), StatusCode::BAD_REQUEST);

        // A supported version header dispatches normally.
        let response = post_mcp(
            json!({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25"}}).to_string(),
            Some("2025-11-25"),
        )
        .await;
        assert_eq!(response.status(), StatusCode::OK);
        let body = to_bytes(response.into_body(), 1024 * 1024).await.unwrap();
        let parsed: Value = serde_json::from_slice(&body).unwrap();
        assert_eq!(parsed["result"]["protocolVersion"], "2025-11-25");

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
    fn modern_request(method: &str) -> Value {
        json!({"jsonrpc":"2.0","id":7,"method":method,"params":{"_meta":{
            "io.modelcontextprotocol/protocolVersion":LATEST_PROTOCOL_VERSION,
            "io.modelcontextprotocol/clientCapabilities":{}}}})
    }

    async fn post_modern(request: Value, header_method: &str, name: Option<&str>) -> Response {
        let mut builder = Request::builder()
            .method("POST")
            .uri("/mcp")
            .header("host", "127.0.0.1:8765")
            .header("accept", "application/json, text/event-stream")
            .header("content-type", "application/json")
            .header("mcp-protocol-version", LATEST_PROTOCOL_VERSION)
            .header("mcp-method", header_method);
        if let Some(name) = name {
            builder = builder.header("mcp-name", name);
        }
        router()
            .oneshot(builder.body(Body::from(request.to_string())).unwrap())
            .await
            .unwrap()
    }

    #[tokio::test]
    async fn modern_discovery_without_initialize() {
        let response =
            post_modern(modern_request("server/discover"), "server/discover", None).await;
        assert_eq!(response.status(), StatusCode::OK);
        let result: Value =
            serde_json::from_slice(&to_bytes(response.into_body(), 1024 * 1024).await.unwrap())
                .unwrap();
        assert_eq!(result["result"]["resultType"], "complete");
        assert_eq!(
            result["result"]["supportedVersions"][0],
            LATEST_PROTOCOL_VERSION
        );
        assert_eq!(
            result["result"]["_meta"]["io.modelcontextprotocol/serverInfo"]["name"],
            "devloop-bridge"
        );
        let response = post_modern(modern_request("initialize"), "initialize", None).await;
        assert_eq!(response.status(), StatusCode::NOT_FOUND);
    }

    #[tokio::test]
    async fn modern_headers_match_body_and_capabilities_are_required() {
        let response = post_modern(modern_request("tools/list"), "tools/call", None).await;
        assert_eq!(response.status(), StatusCode::BAD_REQUEST);
        let body: Value =
            serde_json::from_slice(&to_bytes(response.into_body(), 1024 * 1024).await.unwrap())
                .unwrap();
        assert_eq!(body["error"]["code"], -32020);
        let mut request = modern_request("tools/list");
        request["params"]["_meta"]
            .as_object_mut()
            .unwrap()
            .remove("io.modelcontextprotocol/clientCapabilities");
        let response = post_modern(request, "tools/list", None).await;
        assert_eq!(response.status(), StatusCode::BAD_REQUEST);
        let body: Value =
            serde_json::from_slice(&to_bytes(response.into_body(), 1024 * 1024).await.unwrap())
                .unwrap();
        assert_eq!(body["error"]["code"], -32602);
        let response = post_modern(modern_request("tools/list"), "tools/list", None).await;
        assert_eq!(response.status(), StatusCode::OK);
    }

    #[test]
    fn modern_unknown_versions_and_invalid_envelopes_are_rejected() {
        let mut request = modern_request("server/discover");
        request["params"]["_meta"]["io.modelcontextprotocol/protocolVersion"] = json!("1900-01-01");
        let result = mcp_dispatch(&request).unwrap();
        assert_eq!(result["id"], 7);
        assert_eq!(result["error"]["code"], -32022);
        assert_eq!(result["error"]["data"]["requested"], "1900-01-01");
        assert!(result["error"]["data"]["supported"]
            .as_array()
            .unwrap()
            .contains(&json!(LATEST_PROTOCOL_VERSION)));
        for bad in [
            json!(null),
            json!([]),
            json!({"id":1,"method":"tools/list"}),
            json!({"jsonrpc":"2.0","id":{},"method":"tools/list"}),
        ] {
            assert_eq!(mcp_dispatch(&bad).unwrap()["error"]["code"], -32600);
        }
    }

    #[tokio::test]
    async fn modern_tool_name_header_decodes_and_translation_keeps_content() {
        let mut request = modern_request("tools/call");
        request["params"]["name"] = json!("translate_frames");
        request["params"]["arguments"] = json!({"source":"agy","frames":[{"event":"result","result":{"status":"SUCCESS","response":"ready"}}]});
        let response = post_modern(request.clone(), "tools/call", Some("other_tool")).await;
        assert_eq!(response.status(), StatusCode::BAD_REQUEST);
        let encoded = format!("=?base64?{}?=", STANDARD.encode("translate_frames"));
        let response = post_modern(request, "tools/call", Some(&encoded)).await;
        assert_eq!(response.status(), StatusCode::OK);
        let body: Value =
            serde_json::from_slice(&to_bytes(response.into_body(), 1024 * 1024).await.unwrap())
                .unwrap();
        assert_eq!(
            body["result"]["structuredContent"]["responses_items"][0]["content"][0]["text"],
            "ready"
        );
        assert_eq!(body["result"]["resultType"], "complete");
    }

    #[tokio::test]
    async fn all_mcp_http_methods_reject_foreign_origins() {
        for method in ["POST", "GET", "DELETE"] {
            let request = Request::builder()
                .method(method)
                .uri("/mcp")
                .header("host", "127.0.0.1:8765")
                .header("origin", "http://attacker.example")
                .body(Body::from("{}"))
                .unwrap();
            assert_eq!(
                router().oneshot(request).await.unwrap().status(),
                StatusCode::FORBIDDEN
            );
        }
        let mut headers = HeaderMap::new();
        headers.insert("host", "127.0.0.1:8765".parse().unwrap());
        headers.insert(
            "origin",
            axum::http::HeaderValue::from_bytes(b"\xff").unwrap(),
        );
        assert!(!local_request(&headers));
    }
}
