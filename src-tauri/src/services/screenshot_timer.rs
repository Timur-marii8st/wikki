use rand::Rng;
use serde::Serialize;
use std::time::Duration;
use tauri::{AppHandle, Emitter};
use tokio::time::sleep;

const MIN_INTERVAL_SECS: u64 = 300; // 5 minutes
const MAX_INTERVAL_SECS: u64 = 900; // 15 minutes

const COMMENTARY_PROMPTS: &[&str] = &[
    "I just peeked at your screen! What are you up to?",
    "Hmm, let me see what you're working on...",
    "Oh! What's this? Tell me about what you're doing!",
    "I noticed your screen changed! What's happening?",
    "*peeks curiously* What are we looking at?",
];

#[derive(Clone, Serialize)]
pub struct ScreenshotRequest {
    pub prompt: String,
}

pub async fn start(app: AppHandle) {
    loop {
        // Random interval
        let interval = rand::thread_rng().gen_range(MIN_INTERVAL_SECS..=MAX_INTERVAL_SECS);
        sleep(Duration::from_secs(interval)).await;

        // Pick random prompt
        let prompt_idx = rand::thread_rng().gen_range(0..COMMENTARY_PROMPTS.len());
        let prompt = COMMENTARY_PROMPTS[prompt_idx];

        // Emit event to frontend
        let _ = app.emit("screenshot-request", ScreenshotRequest {
            prompt: prompt.to_string(),
        });
    }
}
