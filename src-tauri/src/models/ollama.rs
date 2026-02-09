use serde::{Deserialize, Serialize};
use super::chat::Message;

#[derive(Debug, Serialize)]
pub struct ChatRequest {
    pub model: String,
    pub messages: Vec<Message>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub stream: Option<bool>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub options: Option<ModelOptions>,
}

#[derive(Debug, Serialize)]
pub struct ModelOptions {
    pub temperature: f32,
}

#[derive(Debug, Deserialize)]
pub struct ChatResponse {
    #[allow(dead_code)]
    pub model: String,
    pub message: Message,
    #[allow(dead_code)]
    pub done: bool,
}
