mod commands;
mod models;
mod services;

use tauri::{Manager, Emitter};
use tauri::menu::{Menu, MenuItem};
use tauri::tray::TrayIconBuilder;
use tauri_plugin_global_shortcut::{GlobalShortcutExt, Code, Modifiers, Shortcut};

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    env_logger::init();

    tauri::Builder::default()
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_global_shortcut::Builder::new().build())
        .setup(|app| {
            // Initialize services
            let ollama = services::ollama::OllamaClient::new().with_llama_cpp();
            app.manage(ollama);

            let tts = services::silero_tts::SileroTtsEngine::new();
            app.manage(tts);

            let llama_server = services::llama_server::LlamaServer::new();
            app.manage(llama_server);

            // Create tray menu
            let show_chat = MenuItem::with_id(app, "show_chat", "Show Chat", true, None::<&str>)?;
            let show_avatar = MenuItem::with_id(app, "show_avatar", "Show Avatar", true, None::<&str>)?;
            let quit = MenuItem::with_id(app, "quit", "Quit", true, None::<&str>)?;
            
            let menu = Menu::with_items(app, &[&show_chat, &show_avatar, &quit])?;

            let _tray = TrayIconBuilder::new()
                .icon(app.default_window_icon().unwrap().clone())
                .menu(&menu)
                .on_menu_event(|app, event| {
                    match event.id.as_ref() {
                        "show_chat" => {
                            if let Some(window) = app.get_webview_window("main") {
                                let _ = window.show();
                                let _ = window.set_focus();
                            }
                        }
                        "show_avatar" => {
                            if let Some(window) = app.get_webview_window("avatar") {
                                let _ = window.show();
                                let _ = window.set_focus();
                            }
                        }
                        "quit" => {
                            app.exit(0);
                        }
                        _ => {}
                    }
                })
                .build(app)?;

            // Start screenshot timer
            let app_handle = app.handle().clone();
            tauri::async_runtime::spawn(async move {
                services::screenshot_timer::start(app_handle).await;
            });

            // Register global hotkey for voice input (Ctrl+Shift+V)
            let shortcut = Shortcut::new(
                Some(Modifiers::CONTROL | Modifiers::SHIFT),
                Code::KeyV,
            );

            let app_handle = app.handle().clone();
            app.global_shortcut().on_shortcut(shortcut, move |_app, _shortcut, _event| {
                let _ = app_handle.emit("voice-input-toggle", ());
            }).ok();

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            commands::chat::send_message,
            commands::screenshot::capture_screen,
            commands::tts::synthesize_speech,
            commands::tts::stop_speech,
            commands::tts::set_tts_language,
            commands::tts::get_tts_language,
            commands::tts::preload_tts_model,
            commands::window::show_chat_window,
            commands::window::hide_chat_window,
            commands::window::toggle_avatar,
            commands::window::end_app,
            commands::llama::start_llama_server,
            commands::llama::stop_llama_server,
            commands::llama::get_llama_server_status,
            commands::llama::check_llama_server_health,
            commands::stt::get_audio_info,
            commands::stt::transcribe_audio,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
