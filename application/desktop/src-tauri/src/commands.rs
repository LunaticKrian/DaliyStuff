//! OS Keychain 钥匙串命令 —— JWT 令牌不落明文盘。
//! 前端 web/src/utils/platform.ts 的 tokenStore 通过 invoke 调用这些命令。
//!
//! 服务名固定 "PixelPack"，key 为 access_token / refresh_token。
//! 平台映射：macOS Keychain / Windows Credential Manager / Linux Secret Service。

use keyring::Entry;

const SERVICE: &str = "PixelPack";

#[tauri::command]
pub fn set_secret(key: String, value: String) -> Result<(), String> {
    Entry::new(SERVICE, &key)
        .map_err(|e| e.to_string())?
        .set_password(&value)
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub fn get_secret(key: String) -> Result<Option<String>, String> {
    match Entry::new(SERVICE, &key)
        .map_err(|e| e.to_string())?
        .get_password()
    {
        Ok(v) => Ok(Some(v)),
        Err(keyring::Error::NoEntry) => Ok(None),
        Err(e) => Err(e.to_string()),
    }
}

#[tauri::command]
pub fn del_secret(key: String) -> Result<(), String> {
    match Entry::new(SERVICE, &key)
        .map_err(|e| e.to_string())?
        .delete_credential()
    {
        Ok(_) => Ok(()),
        // 已不存在视为成功
        Err(keyring::Error::NoEntry) => Ok(()),
        Err(e) => Err(e.to_string()),
    }
}
