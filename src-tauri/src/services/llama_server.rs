use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use std::path::PathBuf;

pub struct LlamaServer {
    process: Mutex<Option<Child>>,
    executable_path: Mutex<Option<PathBuf>>,
    model_path: Mutex<Option<PathBuf>>,
}

impl LlamaServer {
    pub fn new() -> Self {
        Self {
            process: Mutex::new(None),
            executable_path: Mutex::new(None),
            model_path: Mutex::new(None),
        }
    }

    pub fn set_paths(&self, exe_path: PathBuf, model_path: PathBuf) -> Result<(), String> {
        let mut exe = self.executable_path.lock().map_err(|e| e.to_string())?;
        let mut model = self.model_path.lock().map_err(|e| e.to_string())?;
        
        *exe = Some(exe_path);
        *model = Some(model_path);
        
        Ok(())
    }

    pub fn start(&self) -> Result<(), String> {
        let mut process_guard = self.process.lock().map_err(|e| e.to_string())?;
        
        // Check if already running
        if let Some(ref mut child) = *process_guard {
            if let Ok(None) = child.try_wait() {
                return Err("Server is already running".to_string());
            }
        }

        let exe_guard = self.executable_path.lock().map_err(|e| e.to_string())?;
        let model_guard = self.model_path.lock().map_err(|e| e.to_string())?;

        let exe_path = exe_guard.as_ref().ok_or("Executable path not set")?;
        let model_path = model_guard.as_ref().ok_or("Model path not set")?;

        // Start llama-server process
        let child = Command::new(exe_path)
            .args(&[
                "-m", model_path.to_str().unwrap(),
                "-ngl", "99",
                "-sm", "none",
                "-mg", "0",
                "--mmap",
                "--host", "127.0.0.1",
                "--port", "8080",
            ])
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .map_err(|e| format!("Failed to start llama-server: {}", e))?;

        *process_guard = Some(child);
        
        Ok(())
    }

    pub fn stop(&self) -> Result<(), String> {
        let mut process_guard = self.process.lock().map_err(|e| e.to_string())?;
        
        if let Some(ref mut child) = *process_guard {
            child.kill().map_err(|e| format!("Failed to kill process: {}", e))?;
            *process_guard = None;
            Ok(())
        } else {
            Err("Server is not running".to_string())
        }
    }

    pub fn is_running(&self) -> bool {
        let mut process_guard = self.process.lock().ok();
        
        if let Some(ref mut guard) = process_guard {
            if let Some(ref mut child) = **guard {
                if let Ok(None) = child.try_wait() {
                    return true;
                }
            }
        }
        
        false
    }

    pub fn get_status(&self) -> String {
        if self.is_running() {
            "running".to_string()
        } else {
            "stopped".to_string()
        }
    }
}

impl Drop for LlamaServer {
    fn drop(&mut self) {
        let _ = self.stop();
    }
}
