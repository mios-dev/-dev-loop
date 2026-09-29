use axum::{
    extract::Json,
    http::{HeaderMap, StatusCode, Uri},
    routing::{get, post},
    Router,
};
use serde_json::{json, Value};
use std::io::{self, BufRead, Write};

use crate::{translate, TranslateRequest};

pub fn router() -> Router {
    Router::new()
        .route("/health", get(|| async { Json(json!({"status":"ok"})) }))
        .route("/translate", post(translate_http))
        .route("/mcp", post(mcp_http))
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

async fn mcp_http(
    headers: HeaderMap,
    Json(body): Json<Value>,
) -> Result<(StatusCode, Json<Value>), (StatusCode, Json<Value>)> {
    if !local_request(&headers) {
        return Err((
            StatusCode::FORBIDDEN,
            Json(json!({"error":"LOCAL HOST REQUIRED"})),
        ));
    }
    Ok(match mcp_dispatch(&body) {
        Some(response) => (StatusCode::OK, Json(response)),
        None => (StatusCode::ACCEPTED, Json(json!({}))),
    })
}

pub fn mcp_dispatch(request: &Value) -> Option<Value> {
    let id = request.get("id")?.clone();
    let method = request.get("method").and_then(Value::as_str).unwrap_or("");
    let result: Result<Value, String> = match method {
        "initialize" => Ok(json!({
            "protocolVersion":"2025-11-25",
            "capabilities":{"tools":{}},
            "serverInfo":{"name":"devloop-bridge","version":env!("CARGO_PKG_VERSION")}
        })),
        "ping" => Ok(json!({})),
        "tools/list" => Ok(json!({"tools":[{
            "name":"translate_frames",
            "description":"Normalize AGY, Claude, or OpenAI Responses/Codex frames to ordered loop.v1 events and Responses items. No model call or permission grant occurs.",
            "inputSchema":{"type":"object","additionalProperties":false,
                "required":["source","frames"],"properties":{
                    "source":{"type":"string","enum":["agy","claude","openai","openai_responses","codex"]},
                    "frames":{"type":"array","items":{"type":"object"}},
                    "evidence":{"type":"object","required":["diff_bytes","positive","negative","tree_restored","exit_code"],
                        "properties":{"diff_bytes":{"type":"integer"},"positive":{"type":"boolean"},
                        "negative":{"type":"boolean"},"tree_restored":{"type":"boolean"},
                        "exit_code":{"type":"integer"},"timed_out":{"type":"boolean"}}}
                }}
        }]})),
        "tools/call" => {
            let params = request.get("params").ok_or("MCP PARAMS MISSING".to_owned());
            params.and_then(|params| {
                let name = params
                    .get("name")
                    .and_then(Value::as_str)
                    .ok_or("MCP TOOL NAME MISSING".to_owned())?;
                if name != "translate_frames" {
                    return Err("MCP UNKNOWN TOOL".into());
                }
                let args = params
                    .get("arguments")
                    .cloned()
                    .ok_or("MCP ARGUMENTS MISSING".to_owned())?;
                let parsed: TranslateRequest =
                    serde_json::from_value(args).map_err(|_| "MCP INVALID ARGUMENTS".to_owned())?;
                let translated = translate(parsed)?;
                Ok(
                    json!({"content":[{"type":"text","text":serde_json::to_string(&translated)
                    .expect("serializable translation")}],"structuredContent":translated}),
                )
            })
        }
        _ => Err("MCP METHOD NOT FOUND".into()),
    };
    Some(match result {
        Ok(value) => json!({"jsonrpc":"2.0","id":id,"result":value}),
        Err(message) => json!({"jsonrpc":"2.0","id":id,"error":{
            "code": if method == "tools/call" { -32602 } else { -32601 },"message":message}}),
    })
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
}
