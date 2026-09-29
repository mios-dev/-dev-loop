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
    if !matches!(
        request.source.as_str(),
        "agy" | "claude" | "openai" | "openai_responses" | "codex"
    ) {
        return Err(format!("UNKNOWN SOURCE: {}", request.source));
    }
    let mut events = Vec::new();
    for frame in &request.frames {
        if let Some(key) = credential_key(frame) {
            return Err(format!("CREDENTIAL FIELD REFUSED: {key}"));
        }
        let mut next = match request.source.as_str() {
            "agy" => agy(frame)?,
            "claude" => claude(frame)?,
            "openai" | "openai_responses" | "codex" => openai(frame)?,
            other => return Err(format!("UNKNOWN SOURCE: {other}")),
        };
        events.append(&mut next);
    }
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
