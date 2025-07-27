use tauri::{AppHandle, Manager};

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
fn show_assistant_window(app: AppHandle) {
    if let Some(window) = app.get_webview_window("assistant") {
        window.show().ok();
        window.set_focus().ok();
    }
}

#[tauri::command]
fn hide_assistant_window(app: AppHandle) {
    if let Some(window) = app.get_webview_window("assistant") {
        window.hide().ok();
    }
}

#[tauri::command]
fn end_app(app: AppHandle) {
    app.exit(0);
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![
            show_main_window,
            hide_main_window,
            show_assistant_window,
            hide_assistant_window,
            end_app
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
