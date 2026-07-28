import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export type ThemeMode = 'dark' | 'light'

export const THEME_STORAGE_KEY = 'pixelpack-theme'

function systemPrefersLight(): boolean {
  return (
    typeof window !== 'undefined' &&
    !!window.matchMedia &&
    window.matchMedia('(prefers-color-scheme: light)').matches
  )
}

/** 读取应使用的主题：本地保存优先，否则跟随系统偏好 */
export function readThemeMode(): ThemeMode {
  try {
    const saved = localStorage.getItem(THEME_STORAGE_KEY)
    if (saved === 'dark' || saved === 'light') return saved
  } catch {}
  return systemPrefersLight() ? 'light' : 'dark'
}

/** 把主题写到 <html data-theme>（light 时设属性，dark 时移除→走 :root 默认） */
export function applyTheme(mode: ThemeMode) {
  if (typeof document === 'undefined') return
  const root = document.documentElement
  if (mode === 'light') root.setAttribute('data-theme', 'light')
  else root.removeAttribute('data-theme')
}

/** 入口前置调用：在挂载前应用主题，避免首屏闪烁。返回当前主题。 */
export function initTheme(): ThemeMode {
  const mode = readThemeMode()
  applyTheme(mode)
  return mode
}

export const useThemeStore = defineStore('theme', () => {
  const mode = ref<ThemeMode>(readThemeMode())
  applyTheme(mode.value)

  watch(mode, (m) => {
    applyTheme(m)
    try {
      localStorage.setItem(THEME_STORAGE_KEY, m)
    } catch {}
  })

  function toggle() {
    mode.value = mode.value === 'light' ? 'dark' : 'light'
  }
  function set(m: ThemeMode) {
    mode.value = m
  }

  return { mode, toggle, set }
})
