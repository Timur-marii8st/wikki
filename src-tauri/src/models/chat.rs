use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Message {
    pub role: String,
    pub content: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub images: Option<Vec<String>>,
}

#[derive(Debug, Deserialize)]
pub struct ChatInput {
    pub message: String,
    pub history: Vec<Message>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub image: Option<String>,
}

#[derive(Debug, Serialize)]
pub struct ChatOutput {
    pub response: String,
    pub emotion: String,
    pub updated_history: Vec<Message>,
}
