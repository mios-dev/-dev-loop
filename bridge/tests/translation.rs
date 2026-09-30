use devloop_bridge::{server::mcp_dispatch, translate, Event, GateEvidence, TranslateRequest};
use serde_json::{json, Value};

fn request(source: &str, frames: Vec<Value>, evidence: Option<GateEvidence>) -> TranslateRequest {
    TranslateRequest {
        source: source.into(),
        frames,
        evidence,
    }
}

fn good(diff_bytes: u64) -> GateEvidence {
    GateEvidence {
        diff_bytes,
        positive: true,
        negative: true,
        tree_restored: true,
        exit_code: 0,
        timed_out: false,
    }
}

#[test]
fn agy_result_needs_two_sided_evidence() {
    let frame = json!({"event":"result","result":{"status":"SUCCESS","response":"PROBE_OK\n"}});
    let unverified = translate(request("agy", vec![frame.clone()], None)).unwrap();
    assert_eq!(
        unverified.events[0],
        Event::Text {
            role: "assistant".into(),
            text: "PROBE_OK\n".into()
        }
    );
    assert!(
        matches!(&unverified.events[1], Event::Terminal { status, .. } if status == "unverified")
    );
    let vacuous = translate(request("agy", vec![frame.clone()], Some(good(0)))).unwrap();
    assert!(matches!(&vacuous.events[1], Event::Terminal { status, .. } if status == "vacuous"));
    let delivered = translate(request("agy", vec![frame], Some(good(512)))).unwrap();
    assert!(
        matches!(&delivered.events[1], Event::Terminal { status, .. } if status == "delivered")
    );
}

#[test]
fn agy_tool_step_has_stable_call_pair() {
    let frame = json!({"event":"step_update","conversation_id":"conversation-1",
        "step_update":{"step_index":7,"state":"DONE","step_type":"tool",
            "tool_name":"read_file","tool_info":{"parameters":{"path":"a"},"output":"ok"}}});
    let result = translate(request(
        "agy",
        vec![
            frame,
            json!({"event":"result","result":
        {"status":"SUCCESS","response":""}}),
        ],
        None,
    ))
    .unwrap();
    assert!(
        matches!(&result.events[0], Event::ToolCall { call_id, name, .. }
        if call_id == "agy:conversation-1:7" && name == "read_file")
    );
    assert!(
        matches!(&result.events[1], Event::ToolOutput { call_id, .. }
        if call_id == "agy:conversation-1:7")
    );
    assert_eq!(
        result.responses_items[0]["call_id"],
        result.responses_items[1]["call_id"]
    );
}

#[test]
fn claude_tool_use_and_result_keep_order_and_id() {
    let frames = vec![
        json!({"type":"assistant","message":{"role":"assistant","content":[
            {"type":"text","text":"checking"},
            {"type":"tool_use","id":"call-1","name":"read_file","input":{"path":"a"}}]}}),
        json!({"type":"user","message":{"role":"user","content":[
            {"type":"tool_result","tool_use_id":"call-1","content":"ok"}]}}),
        json!({"type":"result","result":"done","is_error":false}),
    ];
    let result = translate(request("claude", frames, None)).unwrap();
    assert!(matches!(&result.events[0], Event::Text { text, .. } if text == "checking"));
    assert!(matches!(&result.events[1], Event::ToolCall { call_id, .. } if call_id == "call-1"));
    assert!(matches!(&result.events[2], Event::ToolOutput { call_id, .. } if call_id == "call-1"));
    assert_eq!(result.responses_items[1]["type"], "function_call");
    assert_eq!(result.responses_items[2]["type"], "function_call_output");
}

#[test]
fn codex_responses_items_project_without_model_gateway() {
    let frames = vec![
        json!({"type":"response.output_item.done","item":{"type":"function_call",
            "call_id":"c1","name":"read_file","arguments":"{\"path\":\"a\"}"}}),
        json!({"type":"function_call_output","call_id":"c1","output":"ok"}),
        json!({"type":"response.output_item.done","item":{"type":"message","role":"assistant",
            "content":[{"type":"output_text","text":"done"}]}}),
        json!({"type":"response.completed","response":{"status":"completed"}}),
    ];
    let result = translate(request("codex", frames, None)).unwrap();
    assert_eq!(result.responses_items.len(), 3);
    assert_eq!(result.responses_items[0]["call_id"], "c1");
    assert_eq!(result.responses_items[1]["call_id"], "c1");
    assert!(matches!(&result.events[3], Event::Terminal { status, .. } if status == "unverified"));
}

#[test]
fn full_response_and_bare_print_results_are_supported() {
    let full = json!({"object":"response","status":"completed","output":[
        {"type":"message","role":"assistant","content":[{"type":"output_text","text":"ready"}]}
    ]});
    let result = translate(request("openai", vec![full], None)).unwrap();
    assert!(matches!(&result.events[0], Event::Text { text, .. } if text == "ready"));
    assert!(matches!(&result.events[1], Event::Terminal { status, .. } if status == "unverified"));
    let agy = translate(request(
        "agy",
        vec![json!({"status":"SUCCESS","response":"ready"})],
        None,
    ))
    .unwrap();
    let claude = translate(request(
        "claude",
        vec![json!({"result":"ready","is_error":false})],
        None,
    ))
    .unwrap();
    assert_eq!(agy.responses_items, claude.responses_items);
}

#[test]
fn incomplete_or_malformed_frames_fail_closed() {
    let absent = translate(request(
        "agy",
        vec![json!({"event":"init","init":{}})],
        None,
    ))
    .unwrap();
    assert!(
        matches!(&absent.events[0], Event::Terminal { status, error, .. }
        if status == "errored" && error.as_deref() == Some("MISSING TERMINAL ENVELOPE"))
    );
    let bad = translate(request(
        "codex",
        vec![json!({"type":"function_call",
        "name":"read_file","arguments":"{}"})],
        None,
    ))
    .unwrap_err();
    assert!(bad.contains("RESPONSES CALL ID MISSING"));
    let unknown = translate(request("other", vec![json!({"type":"message"})], None)).unwrap_err();
    assert!(unknown.contains("UNKNOWN SOURCE"));
    let secret = translate(request(
        "codex",
        vec![json!({"type":"function_call_output",
        "call_id":"c1","output":{"authorization":"Bearer planted"}})],
        None,
    ))
    .unwrap_err();
    assert_eq!(secret, "CREDENTIAL FIELD REFUSED: authorization");
    assert!(!secret.contains("planted"));
}

#[test]
fn mcp_exposes_one_translation_tool() {
    let listed = mcp_dispatch(&json!({"jsonrpc":"2.0","id":1,"method":"tools/list"})).unwrap();
    assert_eq!(listed["result"]["tools"][0]["name"], "translate_frames");
    let called = mcp_dispatch(&json!({"jsonrpc":"2.0","id":2,"method":"tools/call",
        "params":{"name":"translate_frames","arguments":{"source":"agy","frames":[
            {"event":"result","result":{"status":"SUCCESS","response":"hello"}}]}}}))
    .unwrap();
    assert_eq!(called["result"]["structuredContent"]["schema"], "loop.v1");
    assert_eq!(
        called["result"]["structuredContent"]["responses_items"][0]["content"][0]["text"],
        "hello"
    );
}
