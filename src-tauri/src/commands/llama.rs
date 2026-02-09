use crate::services::llama_server::LlamaServer;
use tauri::State;
use std::path::PathBuf;

#[tauri::command]
pub async fn start_llama_server(
    exe_path: String,
    model_path: String,
    server: State<'_, LlamaServer>,
) -> Result<(), String> {
    server.set_paths(PathBuf::from(exe_path), PathBuf::from(model_path))?;
    server.start()
}

#[tauri::command]
pub async fn stop_llama_server(server: State<'_, LlamaServer>) -> Result<(), String> {
    server.stop()
}

#[tauri::command]
pub async fn get_llama_server_status(server: State<'_, LlamaServer>) -> Result<String, String> {
    Ok(server.get_status())
}

#[tauri::command]
pub async fn check_llama_server_health() -> Result<bool, String> {
    let client = reqwest::Client::new();
    let result = client
        .get("http://127.0.0.1:8080/health")
        .timeout(std::time::Duration::from_secs(2))
        .send()
        .await;
    
    Ok(result.is_ok())
}
