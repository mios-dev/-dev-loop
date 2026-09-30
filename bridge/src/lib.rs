use serde::{Deserialize, Serialize};
use serde_json::{json, Value};

pub mod server;

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum Event {
    Text {
        role: String,
        text: String,
    },
    ToolCall {
        call_id: String,
        name: String,
        arguments: Value,
    },
    ToolOutput {
        call_id: String,
        output: Value,
    },
    Terminal {
        status: String,
        text: String,
        error: Option<String>,
    },
}

#[derive(Debug, Deserialize)]
pub struct TranslateRequest {
    pub source: String,
    pub frames: Vec<Value>,
    #[serde(default)]
    pub evidence: Option<GateEvidence>,
}

#[derive(Debug, Deserialize)]
pub struct GateEvidence {
    pub diff_bytes: u64,
    pub positive: bool,
    pub negative: bool,
    pub tree_restored: bool,
    pub exit_code: i32,
    #[serde(default)]
    pub timed_out: bool,
}

#[derive(Debug, Serialize)]
pub struct TranslateResponse {
    pub schema: &'static str,
    pub events: Vec<Event>,
    pub responses_items: Vec<Value>,
}

pub fn translate(request: TranslateRequest) -> Result<TranslateResponse, String> {
    // "auto" sniffs the wire dialect from the first informative frame; every
    // explicit source name stays honoured so callers can pin the dialect.
    let source = match request.source.as_str() {
        "auto" => request
            .frames
            .iter()
            .find_map(detect_source)
            .ok_or_else(|| "AUTO DETECTION FAILED: no known frame shape".to_owned())?,
        known @ ("agy"
        | "claude"
        | "openai"
        | "openai_responses"
        | "codex"
        | "openai_chat"
        | "chat_completions"
        | "openai_compatible"
        | "generic") => known,
        other => return Err(format!("UNKNOWN SOURCE: {other}")),
    };
    for frame in &request.frames {
        if let Some(key) = credential_key(frame) {
            return Err(format!("CREDENTIAL FIELD REFUSED: {key}"));
        }
    }
    // Chat Completions is translated in one stateful pass: streaming chunks
    // split tool-call arguments across frames and must be accumulated.
    let mut events = match source {
        "openai_chat" | "chat_completions" | "openai_compatible" | "generic" => {
            openai_chat(&request.frames)?
        }
        _ => {
            let mut events = Vec::new();
            for frame in &request.frames {
                let mut next = match source {
                    "agy" => agy(frame)?,
                    "claude" => claude(frame)?,
                    "openai" | "openai_responses" | "codex" => openai(frame)?,
                    other => return Err(format!("UNKNOWN SOURCE: {other}")),
                };
                events.append(&mut next);
            }
            events
        }
    };
    if !events
        .iter()
        .any(|event| matches!(event, Event::Text { .. }))
    {
        if let Some(text) = events.iter().rev().find_map(|event| match event {
            Event::Terminal { text, .. } if !text.is_empty() => Some(text.clone()),
            _ => None,
        }) {
            let terminal_index = events
                .iter()
                .position(|event| matches!(event, Event::Terminal { .. }))
                .unwrap_or(events.len());
            events.insert(
                terminal_index,
                Event::Text {
                    role: "assistant".into(),
                    text,
                },
            );
        }
    }
    if !events
        .iter()
        .any(|event| matches!(event, Event::Terminal { .. }))
    {
        events.push(Event::Terminal {
            status: "errored".into(),
            text: String::new(),
            error: Some("MISSING TERMINAL ENVELOPE".into()),
        });
    }
    let denied = request.frames.iter().any(|frame| {
        let envelope = frame.get("result").unwrap_or(frame);
        envelope
            .get("denied_actions")
            .and_then(Value::as_array)
            .is_some_and(|v| !v.is_empty())
            || envelope
                .get("permission_denials")
                .and_then(Value::as_array)
                .is_some_and(|v| !v.is_empty())
    });
    for event in &mut events {
        if let Event::Terminal { status, .. } = event {
            if status == "delivered" {
                *status = if denied {
                    "refused"
                } else if let Some(evidence) = &request.evidence {
                    if evidence.timed_out {
                        "timed_out"
                    } else if evidence.exit_code != 0 {
                        "errored"
                    } else if !evidence.tree_restored {
                        "control_invalid"
                    } else if !evidence.positive || !evidence.negative {
                        "gate_failed"
                    } else if evidence.diff_bytes == 0 {
                        "vacuous"
                    } else {
                        "delivered"
                    }
                } else {
                    "unverified"
                }
                .into();
            }
        }
    }
    let responses_items = responses_items(&events);
    Ok(TranslateResponse {
        schema: "loop.v1",
        events,
        responses_items,
    })
}

fn credential_key(value: &Value) -> Option<&str> {
    match value {
        Value::Object(map) => {
            for (key, value) in map {
                let normalized = key.to_ascii_lowercase().replace('-', "_");
                if matches!(
                    normalized.as_str(),
                    "api_key"
                        | "access_token"
                        | "refresh_token"
                        | "authorization"
                        | "client_secret"
                        | "password"
                        | "private_key"
                ) {
                    return Some(key);
                }
                if let Some(found) = credential_key(value) {
                    return Some(found);
                }
            }
            None
        }
        Value::Array(values) => values.iter().find_map(credential_key),
        _ => None,
    }
}

fn required_str<'a>(value: &'a Value, key: &str, context: &str) -> Result<&'a str, String> {
    value
        .get(key)
        .and_then(Value::as_str)
        .filter(|value| !value.is_empty())
        .ok_or_else(|| format!("{context}: missing {key}"))
}

fn parse_arguments(value: &Value) -> Result<Value, String> {
    match value {
        Value::String(text) => {
            serde_json::from_str(text).map_err(|_| "MALFORMED TOOL ARGUMENTS".into())
        }
        other => Ok(other.clone()),
    }
}

fn agy(frame: &Value) -> Result<Vec<Event>, String> {
    if frame.get("event").is_none() && frame.get("status").is_some() {
        return agy(&json!({"event":"result","result":frame}));
    }
    match frame.get("event").and_then(Value::as_str) {
        Some("init") => Ok(vec![]),
        Some("step_update") => {
            let step = frame.get("step_update").ok_or("AGY STEP MISSING")?;
            match step.get("step_type").and_then(Value::as_str) {
                Some("agent_response") => Ok(step
                    .get("text_delta")
                    .and_then(Value::as_str)
                    .filter(|text| !text.is_empty())
                    .map(|text| {
                        vec![Event::Text {
                            role: "assistant".into(),
                            text: text.into(),
                        }]
                    })
                    .unwrap_or_default()),
                Some("tool") if step.get("state").and_then(Value::as_str) == Some("DONE") => {
                    let info = step.get("tool_info").ok_or("AGY TOOL INFO MISSING")?;
                    let call_id = match step.get("call_id").and_then(Value::as_str) {
                        Some(id) if !id.is_empty() => id.to_owned(),
                        _ => {
                            let index = step
                                .get("step_index")
                                .and_then(Value::as_u64)
                                .ok_or("AGY TOOL STEP INDEX MISSING")?;
                            let conversation = frame
                                .get("conversation_id")
                                .and_then(Value::as_str)
                                .unwrap_or("session");
                            format!("agy:{conversation}:{index}")
                        }
                    };
                    let name = required_str(step, "tool_name", "AGY TOOL NAME MISSING")?.to_owned();
                    let mut result = vec![Event::ToolCall {
                        call_id: call_id.clone(),
                        name,
                        arguments: info.get("parameters").cloned().unwrap_or_else(|| json!({})),
                    }];
                    if let Some(output) = info.get("output") {
                        result.push(Event::ToolOutput {
                            call_id,
                            output: output.clone(),
                        });
                    }
                    Ok(result)
                }
                Some("tool" | "subagent" | "user_input" | "system_message") => Ok(vec![]),
                other => Err(format!(
                    "AGY UNKNOWN STEP TYPE: {}",
                    other.unwrap_or("missing")
                )),
            }
        }
        Some("result") => {
            let result = frame.get("result").ok_or("AGY RESULT MISSING")?;
            let status = match result.get("status").and_then(Value::as_str) {
                Some("SUCCESS") => "delivered",
                Some("ERROR" | "FAILURE") => "errored",
                _ => "errored",
            };
            let error = result
                .get("error")
                .and_then(Value::as_str)
                .map(str::to_owned);
            let text = result
                .get("response")
                .and_then(Value::as_str)
                .unwrap_or("")
                .to_owned();
            Ok(vec![Event::Terminal {
                status: status.into(),
                text,
                error,
            }])
        }
        other => Err(format!("AGY UNKNOWN EVENT: {}", other.unwrap_or("missing"))),
    }
}

fn claude(frame: &Value) -> Result<Vec<Event>, String> {
    if frame.get("type").is_none() && frame.get("result").is_some() {
        let mut wrapped = frame.clone();
        wrapped["type"] = json!("result");
        return claude(&wrapped);
    }
    match frame.get("type").and_then(Value::as_str) {
        Some("system") => Ok(vec![]),
        Some("assistant" | "user") => {
            let message = frame.get("message").ok_or("CLAUDE MESSAGE MISSING")?;
            let role = required_str(message, "role", "CLAUDE ROLE MISSING")?;
            let blocks = message
                .get("content")
                .and_then(Value::as_array)
                .ok_or("CLAUDE CONTENT MISSING")?;
            let mut events = Vec::new();
            for block in blocks {
                match block.get("type").and_then(Value::as_str) {
                    Some("text") => events.push(Event::Text {
                        role: role.into(),
                        text: required_str(block, "text", "CLAUDE TEXT MISSING")?.into(),
                    }),
                    Some("tool_use") => events.push(Event::ToolCall {
                        call_id: required_str(block, "id", "CLAUDE TOOL ID MISSING")?.into(),
                        name: required_str(block, "name", "CLAUDE TOOL NAME MISSING")?.into(),
                        arguments: block.get("input").cloned().unwrap_or_else(|| json!({})),
                    }),
                    Some("tool_result") => events.push(Event::ToolOutput {
                        call_id: required_str(
                            block,
                            "tool_use_id",
                            "CLAUDE TOOL RESULT ID MISSING",
                        )?
                        .into(),
                        output: block.get("content").cloned().unwrap_or(Value::Null),
                    }),
                    other => {
                        return Err(format!(
                            "CLAUDE UNKNOWN CONTENT: {}",
                            other.unwrap_or("missing")
                        ))
                    }
                }
            }
            Ok(events)
        }
        Some("result") => {
            let error = if frame.get("is_error").and_then(Value::as_bool) == Some(true) {
                Some(
                    frame
                        .get("result")
                        .and_then(Value::as_str)
                        .unwrap_or("CLAUDE ERROR")
                        .to_owned(),
                )
            } else {
                None
            };
            let text = frame
                .get("result")
                .and_then(Value::as_str)
                .unwrap_or("")
                .to_owned();
            let status = if error.is_some() {
                "errored"
            } else {
                "delivered"
            };
            Ok(vec![Event::Terminal {
                status: status.into(),
                text,
                error,
            }])
        }
        other => Err(format!(
            "CLAUDE UNKNOWN EVENT: {}",
            other.unwrap_or("missing")
        )),
    }
}

fn openai_item(item: &Value) -> Result<Vec<Event>, String> {
    match item.get("type").and_then(Value::as_str) {
        Some("message") => {
            let role = item
                .get("role")
                .and_then(Value::as_str)
                .unwrap_or("assistant");
            let blocks = item
                .get("content")
                .and_then(Value::as_array)
                .ok_or("RESPONSES MESSAGE CONTENT MISSING")?;
            let mut events = Vec::new();
            for block in blocks {
                match block.get("type").and_then(Value::as_str) {
                    Some("output_text" | "input_text") => events.push(Event::Text {
                        role: role.into(),
                        text: required_str(block, "text", "RESPONSES TEXT MISSING")?.into(),
                    }),
                    other => {
                        return Err(format!(
                            "RESPONSES UNKNOWN CONTENT: {}",
                            other.unwrap_or("missing")
                        ))
                    }
                }
            }
            Ok(events)
        }
        Some("function_call") => Ok(vec![Event::ToolCall {
            call_id: required_str(item, "call_id", "RESPONSES CALL ID MISSING")?.into(),
            name: required_str(item, "name", "RESPONSES FUNCTION NAME MISSING")?.into(),
            arguments: parse_arguments(
                item.get("arguments").ok_or("RESPONSES ARGUMENTS MISSING")?,
            )?,
        }]),
        Some("function_call_output") => Ok(vec![Event::ToolOutput {
            call_id: required_str(item, "call_id", "RESPONSES OUTPUT CALL ID MISSING")?.into(),
            output: item
                .get("output")
                .cloned()
                .ok_or("RESPONSES OUTPUT MISSING")?,
        }]),
        other => Err(format!(
            "RESPONSES UNKNOWN ITEM: {}",
            other.unwrap_or("missing")
        )),
    }
}

fn openai(frame: &Value) -> Result<Vec<Event>, String> {
    if frame.get("object").and_then(Value::as_str) == Some("response") {
        let items = frame
            .get("output")
            .and_then(Value::as_array)
            .ok_or("RESPONSES OUTPUT ARRAY MISSING")?;
        let mut events = Vec::new();
        for item in items {
            events.extend(openai_item(item)?);
        }
        let status = if frame.get("status").and_then(Value::as_str) == Some("completed")
            && frame.get("error").is_none_or(Value::is_null)
        {
            "delivered"
        } else {
            "errored"
        };
        let error = frame
            .get("error")
            .and_then(|value| value.get("message"))
            .and_then(Value::as_str)
            .map(str::to_owned);
        events.push(Event::Terminal {
            status: status.into(),
            text: String::new(),
            error,
        });
        return Ok(events);
    }
    match frame.get("type").and_then(Value::as_str) {
        Some("response.output_item.done") => {
            openai_item(frame.get("item").ok_or("RESPONSES STREAM ITEM MISSING")?)
        }
        Some("response.completed" | "response.failed") => {
            let response = frame.get("response").ok_or("RESPONSES TERMINAL MISSING")?;
            let status = if frame.get("type").and_then(Value::as_str) == Some("response.failed")
                || response.get("error").is_some_and(|v| !v.is_null())
            {
                "errored"
            } else {
                "delivered"
            };
            let error = response
                .get("error")
                .and_then(|v| v.get("message"))
                .and_then(Value::as_str)
                .map(str::to_owned);
            Ok(vec![Event::Terminal {
                status: status.into(),
                text: String::new(),
                error,
            }])
        }
        Some("response.output_item.added" | "response.output_text.delta") => Ok(vec![]),
        Some("message" | "function_call" | "function_call_output") => openai_item(frame),
        other => Err(format!(
            "RESPONSES UNKNOWN EVENT: {}",
            other.unwrap_or("missing")
        )),
    }
}

/// Sniff the wire dialect of one frame. Priority: AGY envelopes, Responses
/// objects/stream events, Chat Completions objects/messages, Claude envelopes.
pub fn detect_source(frame: &Value) -> Option<&'static str> {
    if frame.get("event").is_some() {
        return Some("agy");
    }
    if frame.get("object").and_then(Value::as_str) == Some("response")
        || frame
            .get("type")
            .and_then(Value::as_str)
            .is_some_and(|t| t.starts_with("response."))
    {
        return Some("openai");
    }
    let object = frame.get("object").and_then(Value::as_str);
    if matches!(
        object,
        Some("chat.completion") | Some("chat.completion.chunk")
    ) || frame.get("tool_call_id").is_some()
        || frame.get("tool_calls").is_some()
    {
        return Some("openai_chat");
    }
    if let Some(kind) = frame.get("type").and_then(Value::as_str) {
        if matches!(kind, "system" | "assistant" | "user") && frame.get("message").is_some() {
            return Some("claude");
        }
        // A Claude terminal envelope carries type:"result" WITHOUT a message
        // envelope -- its payload sits in frame.result / frame.is_error.
        if kind == "result"
            && (frame.get("result").is_some() || frame.get("is_error").is_some())
        {
            return Some("claude");
        }
        // Responses items are typed frames ("message"/"function_call"/...); a
        // "message" whose content blocks are output_text/input_text is the
        // Responses shape, plain text blocks belong to Chat Completions.
        if matches!(
            kind,
            "message" | "function_call" | "function_call_output"
        ) {
            let responses_blocks = frame
                .get("content")
                .and_then(Value::as_array)
                .is_some_and(|blocks| {
                    blocks.iter().all(|block| {
                        matches!(
                            block.get("type").and_then(Value::as_str),
                            Some("output_text") | Some("input_text")
                        )
                    })
                });
            return if responses_blocks || kind != "message" {
                Some("openai")
            } else {
                Some("openai_chat")
            };
        }
    }
    if frame.get("role").and_then(Value::as_str).is_some() {
        return Some("openai_chat");
    }
    None
}

/// One Chat Completions assistant/tool message, as carried inside a
/// non-streaming choice or a transcript frame.
fn chat_message(message: &Value) -> Result<Vec<Event>, String> {
    let role = message
        .get("role")
        .and_then(Value::as_str)
        .unwrap_or("assistant")
        .to_owned();
    // A tool result frame is an output, not a turn of conversation.
    if role == "tool" {
        let call_id = required_str(message, "tool_call_id", "CHAT TOOL RESULT ID MISSING")?;
        return Ok(vec![Event::ToolOutput {
            call_id: call_id.to_owned(),
            output: message.get("content").cloned().unwrap_or(Value::Null),
        }]);
    }
    let mut events = Vec::new();
    match message.get("content") {
        Some(Value::String(text)) if !text.is_empty() => events.push(Event::Text {
            role: role.clone(),
            text: text.clone(),
        }),
        Some(Value::Array(blocks)) => {
            for block in blocks {
                if block.get("type").and_then(Value::as_str) == Some("text") {
                    if let Some(text) = block.get("text").and_then(Value::as_str) {
                        if !text.is_empty() {
                            events.push(Event::Text {
                                role: role.clone(),
                                text: text.to_owned(),
                            });
                        }
                    }
                } else if let Some(text) = block.as_str() {
                    if !text.is_empty() {
                        events.push(Event::Text {
                            role: role.clone(),
                            text: text.to_owned(),
                        });
                    }
                }
            }
        }
        _ => {}
    }
    if let Some(calls) = message.get("tool_calls").and_then(Value::as_array) {
        for call in calls {
            let function = call
                .get("function")
                .ok_or("CHAT TOOL FUNCTION MISSING")?;
            let call_id = call
                .get("id")
                .and_then(Value::as_str)
                .filter(|id| !id.is_empty())
                .ok_or("CHAT TOOL ID MISSING")?;
            events.push(Event::ToolCall {
                call_id: call_id.to_owned(),
                name: required_str(function, "name", "CHAT TOOL NAME MISSING")?.to_owned(),
                arguments: parse_arguments(
                    function.get("arguments").ok_or("CHAT ARGUMENTS MISSING")?,
                )?,
            });
        }
    }
    Ok(events)
}

fn chat_finish(reason: Option<&str>) -> Option<Event> {
    match reason {
        Some("stop") | Some("tool_calls") => Some(Event::Terminal {
            status: "delivered".into(),
            text: String::new(),
            error: None,
        }),
        Some(other) => Some(Event::Terminal {
            status: "errored".into(),
            text: String::new(),
            error: Some(format!("CHAT FINISH REASON: {other}")),
        }),
        None => None,
    }
}

/// Chat Completions: the wire dialect every OpenAI-compatible harness speaks
/// (vLLM, llama.cpp, LM Studio, Ollama, OpenRouter, OpenWebUI, custom agents).
/// Accepts non-streaming response objects, streaming chunks (tool-call
/// argument fragments are accumulated per index until the terminal chunk),
/// and bare transcript messages including `role:"tool"` results.
fn openai_chat(frames: &[Value]) -> Result<Vec<Event>, String> {
    #[derive(Default)]
    struct Pending {
        id: String,
        name: String,
        arguments: String,
    }
    let mut events = Vec::new();
    let mut pending: Vec<Option<Pending>> = Vec::new();
    let flush = |pending: &mut Vec<Option<Pending>>, events: &mut Vec<Event>| -> Result<(), String> {
        for slot in pending.iter_mut().flatten() {
            let arguments = serde_json::from_str(&slot.arguments)
                .map_err(|_| "MALFORMED TOOL ARGUMENTS".to_owned())?;
            events.push(Event::ToolCall {
                call_id: slot.id.clone(),
                name: slot.name.clone(),
                arguments,
            });
        }
        pending.clear();
        Ok(())
    };
    for frame in frames {
        let object = frame.get("object").and_then(Value::as_str);
        match object {
            Some("chat.completion") => {
                let choice = frame
                    .get("choices")
                    .and_then(Value::as_array)
                    .and_then(|choices| choices.first())
                    .ok_or("CHAT CHOICES MISSING")?;
                let message = choice
                    .get("message")
                    .ok_or("CHAT MESSAGE MISSING")?;
                events.extend(chat_message(message)?);
                if let Some(terminal) =
                    chat_finish(choice.get("finish_reason").and_then(Value::as_str))
                {
                    events.push(terminal);
                }
            }
            Some("chat.completion.chunk") => {
                let choice = frame
                    .get("choices")
                    .and_then(Value::as_array)
                    .and_then(|choices| choices.first())
                    .ok_or("CHAT CHUNK CHOICES MISSING")?;
                let delta = choice.get("delta").ok_or("CHAT DELTA MISSING")?;
                if let Some(text) = delta.get("content").and_then(Value::as_str) {
                    if !text.is_empty() {
                        events.push(Event::Text {
                            role: delta
                                .get("role")
                                .and_then(Value::as_str)
                                .unwrap_or("assistant")
                                .to_owned(),
                            text: text.to_owned(),
                        });
                    }
                }
                if let Some(calls) = delta.get("tool_calls").and_then(Value::as_array) {
                    for call in calls {
                        let index = call.get("index").and_then(Value::as_u64).unwrap_or(0)
                            as usize;
                        let function = call.get("function").cloned().unwrap_or(Value::Null);
                        let id = call.get("id").and_then(Value::as_str).unwrap_or("");
                        if pending.len() <= index {
                            pending.resize_with(index + 1, || None);
                        }
                        let slot = pending[index].get_or_insert_with(Pending::default);
                        if !id.is_empty() {
                            slot.id = id.to_owned();
                        }
                        if let Some(name) = function.get("name").and_then(Value::as_str) {
                            if !name.is_empty() {
                                slot.name = name.to_owned();
                            }
                        }
                        if let Some(fragment) =
                            function.get("arguments").and_then(Value::as_str)
                        {
                            slot.arguments.push_str(fragment);
                        }
                    }
                }
                if let Some(terminal) =
                    chat_finish(choice.get("finish_reason").and_then(Value::as_str))
                {
                    flush(&mut pending, &mut events)?;
                    events.push(terminal);
                }
            }
            _ => {
                // Bare transcript message (assistant with tool_calls, tool
                // result, user/system turn). A new message boundary closes any
                // streamed tool call still being accumulated.
                flush(&mut pending, &mut events)?;
                events.extend(chat_message(frame)?);
            }
        }
    }
    flush(&mut pending, &mut events)?;
    Ok(events)
}

pub fn responses_items(events: &[Event]) -> Vec<Value> {
    events.iter().filter_map(|event| match event {
        Event::Text { role, text } => Some(json!({"type":"message","role":role,
            "content":[{"type": if role == "assistant" { "output_text" } else { "input_text" },"text":text}]})),
        Event::ToolCall { call_id, name, arguments } => Some(json!({
            "type":"function_call","call_id":call_id,"name":name,"arguments":arguments.to_string()})),
        Event::ToolOutput { call_id, output } => Some(json!({
            "type":"function_call_output","call_id":call_id,"output":output})),
        Event::Terminal { .. } => None,
    }).collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    fn translate_json(source: &str, frames: Value) -> TranslateResponse {
        translate(TranslateRequest {
            source: source.to_owned(),
            frames: serde_json::from_value(frames).expect("frames"),
            evidence: None,
        })
        .expect("translation")
    }

    #[test]
    fn chat_completion_message_with_tool_call() {
        let out = translate_json(
            "openai_chat",
            json!([{"object":"chat.completion","choices":[{
                "index":0,"finish_reason":"tool_calls",
                "message":{"role":"assistant","content":"checking",
                    "tool_calls":[{"id":"call_1","type":"function",
                        "function":{"name":"run_tests","arguments":"{\"suite\":\"unit\"}"}}]}}]}]),
        );
        assert_eq!(
            out.events,
            vec![
                Event::Text { role: "assistant".into(), text: "checking".into() },
                Event::ToolCall {
                    call_id: "call_1".into(),
                    name: "run_tests".into(),
                    arguments: json!({"suite":"unit"}),
                },
                Event::Terminal { status: "unverified".into(), text: String::new(), error: None },
            ]
        );
        assert_eq!(out.responses_items.len(), 2);
        assert_eq!(out.responses_items[1]["type"], "function_call");
    }

    #[test]
    fn chat_stream_accumulates_split_tool_arguments() {
        let chunk1 = json!({"object":"chat.completion.chunk","choices":[{"index":0,"delta":{"role":"assistant","tool_calls":[{"index":0,"id":"call_9","function":{"name":"edit_file","arguments":"{\"pa"}}]}}]});
        let chunk2 = json!({"object":"chat.completion.chunk","choices":[{"index":0,"delta":{"tool_calls":[{"index":0,"function":{"arguments":"th\":\"a.txt\"}"}}]}}]});
        let chunk3 = json!({"object":"chat.completion.chunk","choices":[{"index":0,"delta":{},"finish_reason":"tool_calls"}]});
        let out = translate_json("generic", json!([chunk1, chunk2, chunk3]));
        assert_eq!(
            out.events,
            vec![
                Event::ToolCall {
                    call_id: "call_9".into(),
                    name: "edit_file".into(),
                    arguments: json!({"path":"a.txt"}),
                },
                Event::Terminal { status: "unverified".into(), text: String::new(), error: None },
            ]
        );
    }

    #[test]
    fn chat_tool_result_message_maps_to_output() {
        let out = translate_json(
            "openai_compatible",
            json!([{"role":"tool","tool_call_id":"call_1","content":"12 passed"}]),
        );
        assert_eq!(
            out.events[0],
            Event::ToolOutput { call_id: "call_1".into(), output: Value::String("12 passed".into()) }
        );
        // No terminal envelope in a bare transcript frame: the honest fallback.
        assert!(matches!(out.events.last(), Some(Event::Terminal { status, .. }) if status == "errored"));
    }

    #[test]
    fn auto_detects_each_dialect() {
        let frames = json!([{"event":"result","result":{"status":"SUCCESS","response":"ok"}}]);
        assert!(matches!(translate_json("auto", frames.clone()).events.last(),
            Some(Event::Terminal { status, .. }) if status == "unverified"));
        let chat = translate_json(
            "auto",
            json!([{"object":"chat.completion.chunk","choices":[{"index":0,"delta":{"content":"hi"},"finish_reason":"stop"}]}]),
        );
        assert_eq!(chat.events[0], Event::Text { role: "assistant".into(), text: "hi".into() });
        let claude = translate_json(
            "auto",
            json!([{"type":"result","is_error":false,"result":"done"}]),
        );
        assert!(matches!(claude.events.last(), Some(Event::Terminal { status, .. }) if status == "unverified"));
        let responses = translate_json(
            "auto",
            json!([{"object":"response","status":"completed","output":[
                {"type":"message","role":"assistant","content":[{"type":"output_text","text":"ok"}]}]}]),
        );
        assert_eq!(responses.events[0], Event::Text { role: "assistant".into(), text: "ok".into() });
    }

    #[test]
    fn unknown_source_and_malformed_arguments_fail_with_named_errors() {
        let err = translate(TranslateRequest {
            source: "vax".into(),
            frames: vec![json!({})],
            evidence: None,
        })
        .unwrap_err();
        assert_eq!(err, "UNKNOWN SOURCE: vax");
        let err = translate(TranslateRequest {
            source: "openai_chat".into(),
            frames: vec![json!({"role":"assistant","tool_calls":[{"id":"c","function":{"name":"f","arguments":"{broken"}}]})],
            evidence: None,
        })
        .map(|_| ())
        .unwrap_err();
        assert_eq!(err, "MALFORMED TOOL ARGUMENTS");
    }

    #[test]
    fn credential_fields_are_refused_by_name() {
        let err = translate(TranslateRequest {
            source: "openai_chat".into(),
            frames: vec![json!({"object":"chat.completion","choices":[{"message":{"role":"assistant","api_key":"sk-..."}}]})],
            evidence: None,
        })
        .map(|_| ())
        .unwrap_err();
        assert_eq!(err, "CREDENTIAL FIELD REFUSED: api_key");
    }

    #[test]
    fn chat_delivered_is_demoted_without_evidence() {
        let request = TranslateRequest {
            source: "openai_chat".into(),
            frames: vec![json!({"object":"chat.completion","choices":[
                {"message":{"role":"assistant","content":"done"},"finish_reason":"stop"}]})],
            evidence: Some(GateEvidence {
                diff_bytes: 0,
                positive: true,
                negative: true,
                tree_restored: true,
                exit_code: 0,
                timed_out: false,
            }),
        };
        let out = translate(request).expect("translation");
        assert!(matches!(out.events.last(), Some(Event::Terminal { status, .. }) if status == "vacuous"));
    }
}
