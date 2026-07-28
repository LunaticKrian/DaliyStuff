/**
 * 应用锁（GUILD LOCK）—— 单例状态。
 * PIN 用 SHA-256(salt+pin) 存储（不存明文）；生物识别为 Tauri 原生命令（best-effort）。
 * 桌面/移动 Tauri 理论上应改用 OS 安全存储存 pinHash；当前 Web/移动 WebView 用 localStorage。
 */
import { ref } from 'vue'

const STORAGE_KEY = 'pp_applock'

interface AppLockData {
  enabled: boolean
  pinHash: string | null
  biometric: boolean
}

function load(): AppLockData {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) return { enabled: false, pinHash: null, biometric: false, ...JSON.parse(raw) }
  } catch { /* ignore */ }
  return { enabled: false, pinHash: null, biometric: false }
}

const _data = load()
const enabled = ref(_data.enabled)
const locked = ref(false)
const biometric = ref(_data.biometric)

function persist() {
  localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify({ enabled: enabled.value, pinHash: _data.pinHash, biometric: biometric.value }),
  )
}

async function hash(pin: string): Promise<string> {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode('pixelpack::' + pin))
  return Array.from(new Uint8Array(buf)).map((b) => b.toString(16).padStart(2, '0')).join('')
}

export function useAppLock() {
  /** 启用并设置 PIN（或改 PIN）。 */
  async function setPin(pin: string) {
    _data.pinHash = await hash(pin)
    enabled.value = true
    locked.value = false
    persist()
  }
  /** 关闭应用锁。 */
  function clear() {
    _data.pinHash = null
    enabled.value = false
    biometric.value = false
    locked.value = false
    persist()
  }
  /** 尝试用 PIN 解锁。 */
  async function unlock(pin: string): Promise<boolean> {
    if (!_data.pinHash) {
      locked.value = false
      return true
    }
    if ((await hash(pin)) === _data.pinHash) {
      locked.value = false
      return true
    }
    return false
  }
  /** 落锁（启动 / 回前台时调用；仅当已启用）。 */
  function lock() {
    if (enabled.value && _data.pinHash) locked.value = true
  }
  /** 直接解锁（生物识别通过后）。 */
  function unlockDirect() {
    locked.value = false
  }
  function setBiometric(v: boolean) {
    biometric.value = v
    persist()
  }
  return { enabled, locked, biometric, setPin, clear, unlock, lock, unlockDirect, setBiometric }
}
