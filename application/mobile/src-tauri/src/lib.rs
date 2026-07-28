//! PixelPack 移动端 Rust 外壳（iOS / Android）。
//!
//! 职责（瘦客户端，服务端零改动）：
//! - 装配 Tauri 2 插件：store（服务器地址 + 令牌存储）/ os（平台判定）/ notification
//! - 注册命令（commands.rs）：set/get/del_secret（令牌）+ authenticate_biometric（生物识别，TODO）
//!
//! 与桌面端共用前端 web/（含 platform.ts）：移动端 = UA 命中的 iOS/Android WebView，
//! 走 MobileLayout + views/mobile/*；平台判定在前端完成，Rust 侧无需注入标记。

mod commands;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_store::Builder::default().build())
        .plugin(tauri_plugin_os::init())
        .plugin(tauri_plugin_notification::init())
        .invoke_handler(tauri::generate_handler![
            commands::set_secret,
            commands::get_secret,
            commands::del_secret,
            commands::authenticate_biometric,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
