use crate::models::chat::{ChatInput, ChatOutput, Message};
use crate::services::ollama::OllamaClient;
use tauri::State;

#[tauri::command]
pub async fn send_message(
    input: ChatInput,
    ollama: State<'_, OllamaClient>,
) -> Result<ChatOutput, String> {
    let result = ollama
        .chat(&input.message, input.history.clone(), input.image)
        .await
        .map_err(|e| e.to_string())?;

    // Build updated history
    let mut updated_history = input.history;
    updated_history.push(Message {
        role: "user".to_string(),
        content: input.message,
        images: None,
    });
    updated_history.push(result.raw_message);

    Ok(ChatOutput {
        response: result.text,
        emotion: result.emotion,
        updated_history,
    })
}
