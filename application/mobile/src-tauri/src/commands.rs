//! 令牌与敏感数据存储 + 生物识别命令。
//!
//! 前端 web/src/utils/platform.ts 的 tokenStore 经 invoke 调用 set/get/del_secret，
//! 与桌面端命令同名同参 → 前端无需为移动端分叉。
//!
//! ⚠️ 存储后端：当前用 tauri-plugin-store（应用沙箱内，非明文盘但非硬件隔离）。
//! 生产强化建议换平台安全存储：iOS Keychain / Android Keystore
//! （如 tauri-plugin-keychain 或自写 UnifiedCredential 命令）。

use tauri::{AppHandle, Wry};
use tauri_plugin_store::StoreExt;

const STORE_FILE: &str = "secrets.json";

#[tauri::command]
pub fn set_secret(app: AppHandle<Wry>, key: String, value: String) -> Result<(), String> {
    let store = app.store(STORE_FILE).map_err(|e| e.to_string())?;
    store.set(key, serde_json::json!(value));
    store.save().map_err(|e| e.to_string())
}

#[tauri::command]
pub fn get_secret(app: AppHandle<Wry>, key: String) -> Result<Option<String>, String> {
    let store = app.store(STORE_FILE).map_err(|e| e.to_string())?;
    Ok(store.get(&key).and_then(|v| v.as_str().map(String::from)))
}

#[tauri::command]
pub fn del_secret(app: AppHandle<Wry>, key: String) -> Result<(), String> {
    let store = app.store(STORE_FILE).map_err(|e| e.to_string())?;
    store.delete(&key);
    store.save().map_err(|e| e.to_string())
}

/// 生物识别解锁（GUILD LOCK）。
///
/// TODO（待工具链验证）：接入 tauri-plugin-biometric。
///   1) Cargo.toml 取消注释 `tauri-plugin-biometric = "2"`
///   2) lib.rs `.plugin(tauri_plugin_biometric::init())`
///   3) 这里改为：`use tauri_plugin_biometric::BiometricExt;`
///      `app.biometric().authenticate(...).await.map_err(|e| e.to_string())`
///   4) capabilities/default.json 增加 `biometric:allow-authenticate` 等权限
/// 前端 LockScreen 在 Tauri 环境下会调用本命令；当前占位返回错误，PIN 解锁照常可用。
#[tauri::command]
pub async fn authenticate_biometric() -> Result<(), String> {
    Err("生物识别未接入：请按 commands.rs 中 TODO 接入 tauri-plugin-biometric".into())
}
