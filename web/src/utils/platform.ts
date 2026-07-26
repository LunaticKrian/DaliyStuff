/**
 * 平台抽象层 —— 统一 Web 与桌面（Tauri）的差异。
 *
 * 设计要点：
 * - `tokenStore` 提供**同步** get/set/del：内存缓存为权威源，持久化（桌面=keychain、Web=localStorage）异步写回。
 *   这样 client.ts / sse.ts / auth store 只需把 localStorage 调用换成 tokenStore，无需改异步。
 * - `origin` 同步缓存：桌面端从 tauri-plugin-store 读出服务器地址缓存到内存；Web 端为 ''（相对路径，走同源 / 网关）。
 * - 所有 Tauri 专属模块（@tauri-apps/*）一律**动态 import**，仅在 isTauri() 为真时加载；
 *   Web 构建因此不会在运行时触碰它们，纯浏览器访问行为不变。
 *
 * 初始化顺序（main.ts）：await initPlatform() → setupApiClient() → setRedirector(router.push) → mount。
 */

const TOKEN_KEYS = ['access_token', 'refresh_token'] as const
type TokenKey = (typeof TOKEN_KEYS)[number]

let _tauri = false
let _origin = '' // '' = Web（相对）或桌面未配置
let _configured = false
const _tok: Partial<Record<TokenKey, string>> = {}

// ── 运行环境 ────────────────────────────────────────────────
export function isTauri(): boolean {
  return _tauri
}

/** 同步取服务器 origin（Web 返回 ''，桌面返回已配置地址）。 */
export function getOrigin(): string {
  return _origin
}

export function isServerConfigured(): boolean {
  return _configured
}

// ── 动态调用 Tauri 命令 ─────────────────────────────────────
async function invoke<T>(cmd: string, args?: Record<string, unknown>): Promise<T> {
  const { invoke } = await import('@tauri-apps/api/core')
  return invoke<T>(cmd, args)
}

// ── 初始化 ──────────────────────────────────────────────────
/** Web 跨标签同步：他 tab 写/删 token（刷新、登出、被踢）经 storage 事件同步到本 tab 内存缓存。
 *  桌面端令牌在钥匙串、不触发 storage 事件，此监听在桌面端空转。 */
function setupCrossTabSync(): void {
  if (typeof window === 'undefined') return
  window.addEventListener('storage', (e: StorageEvent) => {
    if (e.key !== 'access_token' && e.key !== 'refresh_token') return
    const k = e.key as TokenKey
    if (e.newValue) {
      _tok[k] = e.newValue
    } else {
      delete _tok[k]
      // 他 tab 已清空 token（登出/会话被吊销）→ 本 tab 一并跳登录
      if (!_tok.access_token && !_tok.refresh_token) redirect('/login')
    }
  })
}

export async function initPlatform(): Promise<void> {
  _tauri =
    typeof window !== 'undefined' &&
    ('__TAURI_INTERNALS__' in window || '__TAURI__' in window)

  setupCrossTabSync()

  if (!_tauri) {
    // Web：从 localStorage 载入缓存，保持向后兼容
    for (const k of TOKEN_KEYS) {
      const v = localStorage.getItem(k)
      if (v) _tok[k] = v
    }
    return
  }

  // 桌面：读服务器地址
  try {
    const { load } = await import('@tauri-apps/plugin-store')
    const store = await load('app.json', { autoSave: false })
    const o = await store.get<string>('server.origin')
    if (o) {
      _origin = o.replace(/\/+$/, '')
      _configured = true
    }
  } catch {
    /* store 读取失败不阻塞，走首屏配置 */
  }

  // 桌面：从 OS Keychain 读令牌
  for (const k of TOKEN_KEYS) {
    try {
      const v = await invoke<string | null>('get_secret', { key: k })
      if (v) _tok[k] = v
    } catch {
      /* keychain 不可用时回退空，首屏重新登录 */
    }
  }
}

// ── 服务器地址 ──────────────────────────────────────────────
export async function setServerOrigin(origin: string): Promise<void> {
  const o = origin.trim().replace(/\/+$/, '')
  _origin = o
  _configured = !!o
  if (!_tauri) return
  const { load } = await import('@tauri-apps/plugin-store')
  const store = await load('app.json')
  await store.set('server.origin', o)
  await store.save()
}

export async function clearServerOrigin(): Promise<void> {
  _origin = ''
  _configured = false
  if (!_tauri) return
  const { load } = await import('@tauri-apps/plugin-store')
  const store = await load('app.json')
  await store.delete('server.origin')
  await store.save()
}

// ── 令牌存储（同步 API，异步持久化）────────────────────────
export const tokenStore = {
  get(key: TokenKey): string | null {
    return _tok[key] ?? null
  },
  set(key: TokenKey, value: string): void {
    _tok[key] = value
    if (!_tauri) {
      localStorage.setItem(key, value)
      return
    }
    // 桌面：fire-and-forget 写 keychain；内存缓存已是本会话权威源
    invoke('set_secret', { key, value }).catch(() => {
      /* 写入失败不阻塞业务；下次启动会重新登录 */
    })
  },
  del(key: TokenKey): void {
    delete _tok[key]
    if (!_tauri) {
      localStorage.removeItem(key)
      return
    }
    invoke('del_secret', { key }).catch(() => {})
  },
}

// ── 路由跳转（替代 window.location.href 硬跳转）────────────
let _redirector: (path: string) => void = (p) => {
  window.location.href = p
}

export function setRedirector(fn: (path: string) => void): void {
  _redirector = fn
}

export function redirect(path: string): void {
  _redirector(path)
}

// ── 资源地址 ────────────────────────────────────────────────
/** 把相对的服务端资源（/uploads/...）补全为绝对地址；Web 端 origin='' 等价不改。 */
export function assetUrl(path: string): string {
  if (!path) return path
  if (/^(https?:|blob:|data:|tauri:)/i.test(path)) return path
  if (_origin && path.startsWith('/')) return _origin + path
  return path
}
