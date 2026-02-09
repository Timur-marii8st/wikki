use base64::{engine::general_purpose::STANDARD, Engine};
use screenshots::Screen;

#[tauri::command]
pub async fn capture_screen() -> Result<String, String> {
    // Run in blocking task to not block async runtime
    tokio::task::spawn_blocking(|| {
        let screens = Screen::all().map_err(|e| e.to_string())?;

        let screen = screens.first().ok_or("No screen found")?;

        let image = screen.capture().map_err(|e| e.to_string())?;
        
        // Convert ImageBuffer to PNG bytes manually
        let width = image.width();
        let height = image.height();
        let raw_data = image.as_raw();
        
        // Create PNG encoder
        let mut png_data = Vec::new();
        {
            let mut encoder = png::Encoder::new(&mut png_data, width, height);
            encoder.set_color(png::ColorType::Rgba);
            encoder.set_depth(png::BitDepth::Eight);
            let mut writer = encoder.write_header().map_err(|e| e.to_string())?;
            writer.write_image_data(raw_data).map_err(|e| e.to_string())?;
        }

        Ok(STANDARD.encode(&png_data))
    })
    .await
    .map_err(|e| e.to_string())?
}
