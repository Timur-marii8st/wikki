use serde::{Deserialize, Serialize};
use std::io::{BufRead, BufReader, Write};
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use base64::{engine::general_purpose::STANDARD, Engine};

#[derive(Debug, Serialize)]
struct TtsRequest {
    command: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    text: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    language: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    emotion: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    use_ssml: Option<bool>,
}

#[derive(Debug, Deserialize)]
struct TtsResponse {
    success: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    audio_base64: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    sample_rate: Option<u32>,
    #[allow(dead_code)]
    #[serde(skip_serializing_if = "Option::is_none")]
    duration: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<String>,
    #[allow(dead_code)]
    #[serde(skip_serializing_if = "Option::is_none")]
    message: Option<String>,
}

pub struct SileroTtsEngine {
    process: Mutex<Option<Child>>,
    language: Mutex<String>,
}

impl SileroTtsEngine {
    pub fn new() -> Self {
        Self {
            process: Mutex::new(None),
            language: Mutex::new("en".to_string()),
        }
    }

    pub fn set_language(&self, lang: &str) -> Result<(), String> {
        let mut language = self.language.lock().map_err(|e| e.to_string())?;
        *language = lang.to_string();
        Ok(())
    }

    pub fn get_language(&self) -> Result<String, String> {
        let language = self.language.lock().map_err(|e| e.to_string())?;
        Ok(language.clone())
    }

    fn start_process(&self) -> Result<Child, String> {
        // Get path to Python script
        let script_path = std::env::current_exe()
            .map_err(|e| e.to_string())?
            .parent()
            .ok_or("Failed to get parent directory")?
            .join("silero_tts_service.py");

        // Start Python process
        let child = Command::new("python")
            .arg(script_path)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .map_err(|e| format!("Failed to start Python TTS service: {}", e))?;

        Ok(child)
    }

    fn ensure_process_running(&self) -> Result<(), String> {
        let mut process_guard = self.process.lock().map_err(|e| e.to_string())?;

        // Check if process is running
        if let Some(ref mut child) = *process_guard {
            if let Ok(Some(_)) = child.try_wait() {
                // Process exited, restart it
                *process_guard = None;
            } else {
                // Process is running
                return Ok(());
            }
        }

        // Start new process
        let child = self.start_process()?;
        *process_guard = Some(child);

        Ok(())
    }

    fn send_request(&self, request: &TtsRequest) -> Result<TtsResponse, String> {
        self.ensure_process_running()?;

        let mut process_guard = self.process.lock().map_err(|e| e.to_string())?;
        let child = process_guard.as_mut().ok_or("Process not running")?;

        // Serialize request to JSON
        let request_json = serde_json::to_string(request).map_err(|e| e.to_string())?;

        // Send request to stdin
        let stdin = child.stdin.as_mut().ok_or("Failed to get stdin")?;
        writeln!(stdin, "{}", request_json).map_err(|e| e.to_string())?;
        stdin.flush().map_err(|e| e.to_string())?;

        // Read response from stdout
        let stdout = child.stdout.as_mut().ok_or("Failed to get stdout")?;
        let mut reader = BufReader::new(stdout);
        let mut response_line = String::new();
        reader.read_line(&mut response_line).map_err(|e| e.to_string())?;

        // Parse response
        let response: TtsResponse = serde_json::from_str(&response_line)
            .map_err(|e| format!("Failed to parse response: {}", e))?;

        Ok(response)
    }

    pub fn speak(&self, text: &str, emotion: &str) -> Result<(), String> {
        let language = self.get_language()?;

        let request = TtsRequest {
            command: "synthesize".to_string(),
            text: Some(text.to_string()),
            language: Some(language),
            emotion: Some(emotion.to_string()),
            use_ssml: Some(true),
        };

        let response = self.send_request(&request)?;

        if !response.success {
            return Err(response.error.unwrap_or_else(|| "Unknown error".to_string()));
        }

        // Get audio data
        let audio_base64 = response.audio_base64.ok_or("No audio data in response")?;
        let audio_bytes = STANDARD.decode(&audio_base64).map_err(|e| e.to_string())?;

        // Play audio using rodio
        self.play_audio(&audio_bytes, response.sample_rate.unwrap_or(48000))?;

        Ok(())
    }

    fn play_audio(&self, audio_bytes: &[u8], _sample_rate: u32) -> Result<(), String> {
        use rodio::{Decoder, OutputStream, Sink};
        use std::io::Cursor;

        let (_stream, stream_handle) = OutputStream::try_default()
            .map_err(|e| format!("Failed to get audio output: {}", e))?;

        let sink = Sink::try_new(&stream_handle)
            .map_err(|e| format!("Failed to create audio sink: {}", e))?;

        let cursor = Cursor::new(audio_bytes.to_vec());
        let source = Decoder::new(cursor)
            .map_err(|e| format!("Failed to decode audio: {}", e))?;

        sink.append(source);
        sink.sleep_until_end();

        Ok(())
    }

    pub fn stop(&self) -> Result<(), String> {
        let mut process_guard = self.process.lock().map_err(|e| e.to_string())?;

        if let Some(ref mut child) = *process_guard {
            // Send shutdown command
            let request = TtsRequest {
                command: "shutdown".to_string(),
                text: None,
                language: None,
                emotion: None,
                use_ssml: None,
            };

            if let Ok(request_json) = serde_json::to_string(&request) {
                if let Some(stdin) = child.stdin.as_mut() {
                    let _ = writeln!(stdin, "{}", request_json);
                    let _ = stdin.flush();
                }
            }

            // Wait a bit for graceful shutdown
            std::thread::sleep(std::time::Duration::from_millis(500));

            // Force kill if still running
            let _ = child.kill();
            *process_guard = None;
        }

        Ok(())
    }

    pub fn preload_model(&self, language: &str) -> Result<(), String> {
        let request = TtsRequest {
            command: "load_model".to_string(),
            text: None,
            language: Some(language.to_string()),
            emotion: None,
            use_ssml: None,
        };

        let response = self.send_request(&request)?;

        if !response.success {
            return Err(response.error.unwrap_or_else(|| "Failed to load model".to_string()));
        }

        Ok(())
    }
}

impl Drop for SileroTtsEngine {
    fn drop(&mut self) {
        let _ = self.stop();
    }
}
