use crate::services::audio_processor::AudioProcessor;
use crate::services::ollama::OllamaClient;
use serde::{Deserialize, Serialize};
use tauri::State;

#[derive(Debug, Deserialize)]
pub struct AudioTranscribeInput {
    pub audio_base64: String,
    #[allow(dead_code)]
    pub format: String, // "wav" or "mp3" - reserved for future use
}

#[derive(Debug, Serialize)]
pub struct AudioInfo {
    pub duration_secs: f32,
    pub size_kb: f32,
    pub exceeds_limit: bool,
    pub max_duration_secs: f32,
}

#[derive(Debug, Serialize)]
pub struct TranscribeResult {
    pub text: String,
    pub audio_info: AudioInfo,
    pub was_trimmed: bool,
}

#[tauri::command]
pub async fn get_audio_info(audio_base64: String) -> Result<AudioInfo, String> {
    let audio_data: Vec<u8> = AudioProcessor::decode_base64(&audio_base64)?;
    let info: crate::services::audio_processor::AudioInfo = AudioProcessor::get_audio_info(&audio_data);
    
    Ok(AudioInfo {
        duration_secs: info.duration_secs,
        size_kb: info.size_kb,
        exceeds_limit: info.exceeds_limit,
        max_duration_secs: info.max_duration_secs,
    })
}

#[tauri::command]
pub async fn transcribe_audio(
    input: AudioTranscribeInput,
    trim_if_needed: bool,
    ollama: State<'_, OllamaClient>,
) -> Result<TranscribeResult, String> {
    let mut audio_data = AudioProcessor::decode_base64(&input.audio_base64)?;
    let original_info = AudioProcessor::get_audio_info(&audio_data);
    
    let mut was_trimmed = false;
    
    // Check duration and trim if needed
    if original_info.exceeds_limit {
        if trim_if_needed {
            audio_data = AudioProcessor::trim_to_max_duration(&audio_data);
            was_trimmed = true;
        } else {
            return Err(format!(
                "Audio duration ({:.1}s) exceeds maximum allowed ({:.1}s). Enable trimming or record shorter audio.",
                original_info.duration_secs, original_info.max_duration_secs
            ));
        }
    }
    
    // Encode back to base64
    let audio_base64 = AudioProcessor::encode_base64(&audio_data);
    
    // Send to Gemma 3 for transcription
    let result = ollama
        .chat(
            "Transcribe this audio to text. Only return the transcribed text, nothing else.",
            vec![],
            Some(audio_base64),
        )
        .await
        .map_err(|e| e.to_string())?;
    
    let final_info = AudioProcessor::get_audio_info(&audio_data);
    
    Ok(TranscribeResult {
        text: result.text,
        audio_info: AudioInfo {
            duration_secs: final_info.duration_secs,
            size_kb: final_info.size_kb,
            exceeds_limit: final_info.exceeds_limit,
            max_duration_secs: final_info.max_duration_secs,
        },
        was_trimmed,
    })
}
