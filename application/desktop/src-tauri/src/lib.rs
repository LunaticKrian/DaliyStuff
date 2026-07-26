//! PixelPack 桌面端 Rust 外壳。
//!
//! 职责（服务端零改动，桌面端为瘦客户端）：
//! - 装配 Tauri 2 插件（store / notification / global-shortcut / autostart / os）
//! - 系统托盘 + 菜单（显示窗口 / 立即同步 / 桌面设置 / 退出）
//! - 全局快捷键唤起/隐藏窗口（启动时读 store，可经命令重注册）
//! - 注册 keychain 命令（commands.rs）

mod commands;

use tauri::{
    menu::{Menu, MenuItem},
    tray::{TrayIconBuilder, TrayIconEvent},
    AppHandle, Emitter, Manager, Runtime,
};
use tauri_plugin_autostart::MacosLauncher;
use tauri_plugin_global_shortcut::{Builder as ShortcutBuilder, Code, GlobalShortcutExt, Modifiers, Shortcut, ShortcutState};
use tauri_plugin_store::StoreExt;

const SHOW_SHORTCUT_DEFAULT: &str = "CmdOrCtrl+Shift+P";

/// 显示并聚焦主窗口。
fn show_main_window<R: Runtime>(app: &AppHandle<R>) {
    if let Some(w) = app.get_webview_window("main") {
        let _ = w.show();
        let _ = w.set_focus();
    }
}

/// 切换主窗口显隐（全局快捷键触发）。
fn toggle_main_window<R: Runtime>(app: &AppHandle<R>) {
    if let Some(w) = app.get_webview_window("main") {
        if w.is_visible().unwrap_or(false) {
            let _ = w.hide();
        } else {
            let _ = w.show();
            let _ = w.set_focus();
        }
    }
}

/// 解析快捷键字符串（如 "CmdOrCtrl+Shift+P"）为 Tauri Shortcut。
fn parse_shortcut(s: &str) -> Option<Shortcut> {
    let mut mods = Modifiers::empty();
    let mut code: Option<Code> = None;
    for part in s.split('+') {
        let p = part.trim();
        if p.is_empty() {
            continue;
        }
        match p.to_ascii_lowercase().as_str() {
            "cmdorctrl" | "commandorcontrol" | "control" | "ctrl" => mods |= Modifiers::CONTROL,
            "shift" => mods |= Modifiers::SHIFT,
            "alt" | "option" | "opt" => mods |= Modifiers::ALT,
            "super" | "cmd" | "command" | "meta" | "win" => mods |= Modifiers::SUPER,
            _ => code = parse_code(p),
        }
    }
    Some(Shortcut::new(Some(mods), code?))
}

/// 字母 / 数字 / F 键 → Code 枚举。
fn parse_code(s: &str) -> Option<Code> {
    let up = s.to_ascii_uppercase();
    if up.len() == 1 {
        return match up.chars().next().unwrap() {
            'A' => Some(Code::KeyA), 'B' => Some(Code::KeyB), 'C' => Some(Code::KeyC),
            'D' => Some(Code::KeyD), 'E' => Some(Code::KeyE), 'F' => Some(Code::KeyF),
            'G' => Some(Code::KeyG), 'H' => Some(Code::KeyH), 'I' => Some(Code::KeyI),
            'J' => Some(Code::KeyJ), 'K' => Some(Code::KeyK), 'L' => Some(Code::KeyL),
            'M' => Some(Code::KeyM), 'N' => Some(Code::KeyN), 'O' => Some(Code::KeyO),
            'P' => Some(Code::KeyP), 'Q' => Some(Code::KeyQ), 'R' => Some(Code::KeyR),
            'S' => Some(Code::KeyS), 'T' => Some(Code::KeyT), 'U' => Some(Code::KeyU),
            'V' => Some(Code::KeyV), 'W' => Some(Code::KeyW), 'X' => Some(Code::KeyX),
            'Y' => Some(Code::KeyY), 'Z' => Some(Code::KeyZ),
            '0' => Some(Code::Digit0), '1' => Some(Code::Digit1), '2' => Some(Code::Digit2),
            '3' => Some(Code::Digit3), '4' => Some(Code::Digit4), '5' => Some(Code::Digit5),
            '6' => Some(Code::Digit6), '7' => Some(Code::Digit7), '8' => Some(Code::Digit8),
            '9' => Some(Code::Digit9),
            _ => None,
        };
    }
    if let Some(rest) = up.strip_prefix('F') {
        if let Ok(n) = rest.parse::<u32>() {
            return match n {
                1 => Some(Code::F1), 2 => Some(Code::F2), 3 => Some(Code::F3), 4 => Some(Code::F4),
                5 => Some(Code::F5), 6 => Some(Code::F6), 7 => Some(Code::F7), 8 => Some(Code::F8),
                9 => Some(Code::F9), 10 => Some(Code::F10), 11 => Some(Code::F11), 12 => Some(Code::F12),
                _ => None,
            };
        }
    }
    None
}

/// 注册全局快捷键（先清空再注册）。handler 统一在插件 Builder 中设置。
fn register_show_shortcut<R: Runtime>(app: &AppHandle<R>, accelerator: &str) -> Result<(), String> {
    let shortcut = parse_shortcut(accelerator).ok_or_else(|| format!("无效快捷键: {accelerator}"))?;
    let gs = app.global_shortcut();
    let _ = gs.unregister_all();
    gs.register(shortcut).map_err(|e| e.to_string())
}

/// 托盘菜单 + 事件。
fn build_tray<R: Runtime>(app: &AppHandle<R>) -> tauri::Result<()> {
    let show = MenuItem::with_id(app, "show", "显示窗口", true, None::<&str>)?;
    let sync = MenuItem::with_id(app, "sync", "立即同步", true, None::<&str>)?;
    let settings = MenuItem::with_id(app, "settings", "桌面设置…", true, None::<&str>)?;
    let quit = MenuItem::with_id(app, "quit", "退出 PixelPack", true, None::<&str>)?;
    let menu = Menu::with_items(app, &[&show, &sync, &settings, &quit])?;

    TrayIconBuilder::with_id("main")
        .tooltip("PixelPack")
        .icon_as_template(true)
        .menu(&menu)
        .show_menu_on_left_click(false)
        .on_menu_event(|app, event| match event.id.as_ref() {
            "show" => show_main_window(app),
            "sync" => {
                let _ = app.emit("pxp-tray", serde_json::json!({ "action": "sync" }));
            }
            "settings" => {
                let _ = app.emit("pxp-tray", serde_json::json!({ "action": "settings" }));
                show_main_window(app);
            }
            "quit" => app.exit(0),
            _ => {}
        })
        .on_tray_icon_event(|tray, event| {
            if let TrayIconEvent::DoubleClick { .. } = event {
                show_main_window(tray.app_handle());
            }
        })
        .build(app)?;
    Ok(())
}

#[tauri::command]
fn reregister_show_shortcut<R: Runtime>(app: AppHandle<R>, accelerator: String) -> Result<(), String> {
    register_show_shortcut(&app, &accelerator)
}

#[cfg_attr(mobile, allow(dead_code))]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_store::Builder::default().build())
        .plugin(tauri_plugin_notification::init())
        .plugin(
            ShortcutBuilder::new()
                .with_handler(|app, _shortcut, event| {
                    // 仅在按下时切换，避免 Pressed/Released 双触发互相抵消
                    if matches!(event.state, ShortcutState::Pressed) {
                        toggle_main_window(app);
                    }
                })
                .build(),
        )
        .plugin(tauri_plugin_autostart::init(MacosLauncher::LaunchAgent, None))
        .plugin(tauri_plugin_os::init())
        .setup(|app| {
            build_tray(app.handle())?;

            // 启动时按 store 中保存的快捷键注册；缺失则用默认值。
            let accel = app
                .store("app.json")
                .ok()
                .and_then(|s| s.get("shortcut.show"))
                .and_then(|v| v.as_str().map(|s| s.to_string()))
                .unwrap_or_else(|| SHOW_SHORTCUT_DEFAULT.to_string());
            if let Err(e) = register_show_shortcut(app.handle(), &accel) {
                eprintln!("[pixelpack] 启动注册快捷键 {accel} 失败: {e}");
            }
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            commands::set_secret,
            commands::get_secret,
            commands::del_secret,
            reregister_show_shortcut,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
