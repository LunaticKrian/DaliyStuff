/**
 * 原生能力抽象层 —— 桌面端（Tauri）走插件，Web 端一律 no-op / 默认值。
 * 所有 @tauri-apps/* 模块动态 import，仅桌面加载；保证 web 构建与纯浏览器运行不受影响。
 */
import { isTauri } from './platform'

// ── 系统通知 ────────────────────────────────────────────────
export async function notify(title: string, body?: string): Promise<void> {
  if (!isTauri()) return
  const { sendNotification } = await import('@tauri-apps/plugin-notification')
  try {
    await sendNotification({ title, body })
  } catch {
    /* 通知权限未授予等，静默 */
  }
}

// ── 开机自启 ────────────────────────────────────────────────
export async function isAutostartEnabled(): Promise<boolean> {
  if (!isTauri()) return false
  const { isEnabled } = await import('@tauri-apps/plugin-autostart')
  try {
    return await isEnabled()
  } catch {
    return false
  }
}

export async function setAutostartEnabled(enabled: boolean): Promise<void> {
  if (!isTauri()) return
  const autostart = await import('@tauri-apps/plugin-autostart')
  try {
    if (enabled) await autostart.enable()
    else await autostart.disable()
  } catch {
    /* 平台不支持时静默 */
  }
}

// ── 全局快捷键（唤起窗口）──────────────────────────────────
const SHORTCUT_STORE_KEY = 'shortcut.show'

export async function getStoredShortcut(): Promise<string> {
  if (!isTauri()) return ''
  const { load } = await import('@tauri-apps/plugin-store')
  const store = await load('app.json')
  return (await store.get<string>(SHORTCUT_STORE_KEY)) ?? 'CmdOrCtrl+Shift+P'
}

export async function setStoredShortcut(accelerator: string): Promise<void> {
  if (!isTauri()) return
  const { load } = await import('@tauri-apps/plugin-store')
  const store = await load('app.json')
  await store.set(SHORTCUT_STORE_KEY, accelerator)
  await store.save()
}

/**
 * 注册全局快捷键。Rust 侧在快捷键触发时切换窗口显隐，前端只需把用户偏好同步到 store，
 * 真正注册由 lib.rs 启动时读取 store 完成；这里暴露重注册接口供设置页改键后调用。
 */
export async function reregisterShortcut(accelerator: string): Promise<boolean> {
  if (!isTauri()) return false
  try {
    const { invoke } = await import('@tauri-apps/api/core')
    await invoke('reregister_show_shortcut', { accelerator })
    return true
  } catch {
    return false
  }
}

// ── 托盘事件（Rust 发出，前端订阅）────────────────────────
export type TrayAction = 'show' | 'sync' | 'settings'

export async function onTrayAction(cb: (action: TrayAction) => void): Promise<() => void> {
  if (!isTauri()) return () => {}
  const { listen } = await import('@tauri-apps/api/event')
  const unlisten = await listen<{ action: TrayAction }>('pxp-tray', (e) => {
    if (e.payload?.action) cb(e.payload.action)
  })
  return unlisten
}

// ── 平台信息 ────────────────────────────────────────────────
export async function desktopPlatform(): Promise<string> {
  if (!isTauri()) return 'web'
  const { platform } = await import('@tauri-apps/plugin-os')
  try {
    return platform()
  } catch {
    return 'unknown'
  }
}
