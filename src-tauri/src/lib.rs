use tauri::{AppHandle, Manager};
use tauri::Emitter;

#[tauri::command]
fn show_main_window(app: AppHandle) {
    if let Some(window) = app.get_webview_window("main") {
        window.show().ok();
        window.set_focus().ok();
    }
}

#[tauri::command]
fn hide_main_window(app: AppHandle) {
    if let Some(window) = app.get_webview_window("main") {
        window.hide().ok();
    }
}

#[tauri::command]
fn show_context_menu(app: AppHandle) {
    if let Some(window) = app.get_webview_window("assistant") {
        window.emit("show-context-menu", {}).ok();
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![
            show_main_window,
            hide_main_window,
            show_context_menu
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
