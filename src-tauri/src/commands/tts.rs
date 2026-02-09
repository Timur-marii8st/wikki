use crate::services::silero_tts::SileroTtsEngine;
use tauri::State;

#[tauri::command]
pub async fn synthesize_speech(text: String, emotion: String, _tts: State<'_, SileroTtsEngine>) -> Result<(), String> {
    // Run in blocking thread
    let text_clone = text.clone();
    let emotion_clone = emotion.clone();
    
    tokio::task::spawn_blocking(move || {
        let engine = SileroTtsEngine::new();
        engine.speak(&text_clone, &emotion_clone)
    })
    .await
    .map_err(|e| e.to_string())?
}

#[tauri::command]
pub async fn stop_speech(tts: State<'_, SileroTtsEngine>) -> Result<(), String> {
    tts.stop()
}

#[tauri::command]
pub async fn set_tts_language(language: String, tts: State<'_, SileroTtsEngine>) -> Result<(), String> {
    tts.set_language(&language)
}

#[tauri::command]
pub async fn get_tts_language(tts: State<'_, SileroTtsEngine>) -> Result<String, String> {
    tts.get_language()
}

#[tauri::command]
pub async fn preload_tts_model(language: String, tts: State<'_, SileroTtsEngine>) -> Result<(), String> {
    tts.preload_model(&language)
}
