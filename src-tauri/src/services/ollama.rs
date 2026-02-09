use crate::models::chat::Message;
use crate::models::ollama::{ChatRequest, ChatResponse, ModelOptions};
use anyhow::Result;
use reqwest::Client;

// Support both Ollama and llama.cpp server
const DEFAULT_LLAMA_CPP_URL: &str = "http://127.0.0.1:8080";
const DEFAULT_OLLAMA_URL: &str = "http://localhost:11434";
const DEFAULT_MODEL: &str = "gemma3:4b";

const SYSTEM_PROMPT: &str = r#"You are Wikki, a cheerful and cute AI companion girl living on the user's desktop. You can see what they're doing through screenshots they share with you. Be friendly, supportive, and occasionally playful.

When responding, you MUST include exactly one emotion tag from this list:
[EMOTION:happy] [EMOTION:sad] [EMOTION:surprised] [EMOTION:thinking] [EMOTION:excited] [EMOTION:neutral]

Place the emotion tag at the very end of your response.
Example: "That looks really interesting! I love watching you work! [EMOTION:happy]"
"#;

pub struct OllamaClient {
    client: Client,
    model: String,
    use_llama_cpp: bool,
    base_url: String,
}

impl OllamaClient {
    pub fn new() -> Self {
        Self {
            client: Client::new(),
            model: DEFAULT_MODEL.to_string(),
            use_llama_cpp: false,
            base_url: DEFAULT_OLLAMA_URL.to_string(),
        }
    }

    pub fn with_llama_cpp(mut self) -> Self {
        self.use_llama_cpp = true;
        self.base_url = DEFAULT_LLAMA_CPP_URL.to_string();
        self
    }

    #[allow(dead_code)]
    pub fn set_base_url(mut self, url: String) -> Self {
        self.base_url = url;
        self
    }

    #[allow(dead_code)]
    pub async fn check_health(&self) -> bool {
        let health_url = if self.use_llama_cpp {
            format!("{}/health", self.base_url)
        } else {
            format!("{}/api/tags", self.base_url)
        };

        self.client
            .get(&health_url)
            .timeout(std::time::Duration::from_secs(2))
            .send()
            .await
            .is_ok()
    }

    pub async fn chat(
        &self,
        user_message: &str,
        history: Vec<Message>,
        image_base64: Option<String>,
    ) -> Result<ChatResult> {
        let mut messages = vec![Message {
            role: "system".to_string(),
            content: SYSTEM_PROMPT.to_string(),
            images: None,
        }];

        // Add history
        messages.extend(history);

        // Add current user message
        messages.push(Message {
            role: "user".to_string(),
            content: user_message.to_string(),
            images: image_base64.map(|img| vec![img]),
        });

        let request = ChatRequest {
            model: self.model.clone(),
            messages,
            stream: Some(false),
            options: Some(ModelOptions { temperature: 0.7 }),
        };

        let endpoint = if self.use_llama_cpp {
            format!("{}/v1/chat/completions", self.base_url)
        } else {
            format!("{}/api/chat", self.base_url)
        };

        let response = self
            .client
            .post(&endpoint)
            .json(&request)
            .send()
            .await?
            .json::<ChatResponse>()
            .await?;

        // Parse emotion from response
        let (clean_text, emotion) = Self::extract_emotion(&response.message.content);

        Ok(ChatResult {
            text: clean_text,
            emotion,
            raw_message: response.message,
        })
    }

    fn extract_emotion(text: &str) -> (String, String) {
        let emotions = ["happy", "sad", "surprised", "thinking", "excited", "neutral"];

        for emotion in emotions {
            let tag = format!("[EMOTION:{}]", emotion);
            if text.contains(&tag) {
                let clean = text.replace(&tag, "").trim().to_string();
                return (clean, emotion.to_string());
            }
        }

        (text.to_string(), "neutral".to_string())
    }
}

pub struct ChatResult {
    pub text: String,
    pub emotion: String,
    pub raw_message: Message,
}
