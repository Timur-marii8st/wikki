use base64::{engine::general_purpose::STANDARD, Engine};

const MAX_AUDIO_DURATION_SECS: f32 = 15.0;
const SAMPLE_RATE: u32 = 16000; // 16kHz for speech
const BYTES_PER_SAMPLE: u32 = 2; // 16-bit audio

pub struct AudioProcessor;

impl AudioProcessor {
    #[allow(dead_code)]
    pub fn new() -> Self {
        Self
    }

    /// Calculate audio duration from raw PCM data
    pub fn calculate_duration(audio_data: &[u8], sample_rate: u32) -> f32 {
        let num_samples = audio_data.len() as f32 / BYTES_PER_SAMPLE as f32;
        num_samples / sample_rate as f32
    }

    /// Check if audio exceeds maximum duration
    #[allow(dead_code)]
    pub fn check_duration(audio_data: &[u8]) -> Result<f32, String> {
        let duration = Self::calculate_duration(audio_data, SAMPLE_RATE);
        
        if duration > MAX_AUDIO_DURATION_SECS {
            Err(format!(
                "Audio duration ({:.1}s) exceeds maximum allowed ({:.1}s)",
                duration, MAX_AUDIO_DURATION_SECS
            ))
        } else {
            Ok(duration)
        }
    }

    /// Trim audio to maximum duration
    pub fn trim_to_max_duration(audio_data: &[u8]) -> Vec<u8> {
        let max_bytes = (MAX_AUDIO_DURATION_SECS * SAMPLE_RATE as f32 * BYTES_PER_SAMPLE as f32) as usize;
        
        if audio_data.len() <= max_bytes {
            audio_data.to_vec()
        } else {
            audio_data[..max_bytes].to_vec()
        }
    }

    /// Encode audio to base64
    pub fn encode_base64(audio_data: &[u8]) -> String {
        STANDARD.encode(audio_data)
    }

    /// Decode audio from base64
    pub fn decode_base64(base64_data: &str) -> Result<Vec<u8>, String> {
        STANDARD.decode(base64_data).map_err(|e| e.to_string())
    }

    /// Get audio info
    pub fn get_audio_info(audio_data: &[u8]) -> AudioInfo {
        let duration = Self::calculate_duration(audio_data, SAMPLE_RATE);
        let size_kb = audio_data.len() as f32 / 1024.0;
        let exceeds_limit = duration > MAX_AUDIO_DURATION_SECS;

        AudioInfo {
            duration_secs: duration,
            size_kb,
            exceeds_limit,
            max_duration_secs: MAX_AUDIO_DURATION_SECS,
        }
    }
}

#[derive(Debug, Clone)]
pub struct AudioInfo {
    pub duration_secs: f32,
    pub size_kb: f32,
    pub exceeds_limit: bool,
    pub max_duration_secs: f32,
}
