import { ofetch, type FetchOptions } from 'ofetch'
import { getOrigin, tokenStore, redirect } from '../utils/platform'
import { refreshTokens } from '../utils/refresh'

const AUTH_PATHS = ['/auth/login', '/auth/register', '/auth/refresh']

/** 把响应里相对的 /uploads/* 资源补全为绝对地址（桌面 origin ≠ SPA origin）。 */
function absolutizeUploads(node: unknown, origin: string): unknown {
  if (typeof node === 'string') {
    return node.startsWith('/uploads/') ? origin + node : node
  }
  if (Array.isArray(node)) {
    for (let i = 0; i < node.length; i++) node[i] = absolutizeUploads(node[i], origin)
    return node
  }
  if (node && typeof node === 'object') {
    const obj = node as Record<string, unknown>
    for (const k of Object.keys(obj)) obj[k] = absolutizeUploads(obj[k], origin)
    return node
  }
  return node
}

function createClient() {
  return ofetch.create({
    baseURL: getOrigin() + '/api',
    onRequest({ options }) {
      const token = tokenStore.get('access_token')
      if (token) options.headers.set('Authorization', `Bearer ${token}`)
    },
    onResponse({ response }) {
      const origin = getOrigin()
      if (origin && response._data) absolutizeUploads(response._data, origin)
    },
    // 401 刷新+重试交给下方 api 包装层统一处理（onResponseError 的重试返回值无法回传调用方）。
  })
}

let _client = createClient()

/** origin 就绪后重建底层实例（baseURL 指向用户配置的服务器）。在 main.ts 挂载前、以及改服务器地址后调用。 */
export function setupApiClient(): void {
  _client = createClient()
}

function isAuthPath(url: string): boolean {
  return AUTH_PATHS.some((p) => url.includes(p))
}

/**
 * 带统一 401 刷新+重试的请求封装。
 * 在此层 catch 401 → refreshTokens → 重试并把结果回传调用方（修复原先重试结果被丢弃的问题）。
 */
export async function api<T = unknown>(url: string, options: FetchOptions<"json"> = {}): Promise<T> {
  try {
    return await _client<T>(url, options)
  } catch (err) {
    if (err && typeof err === 'object' && (err as { response?: { status?: number } }).response?.status !== 401) {
      throw err
    }
    if (isAuthPath(url)) {
      tokenStore.del('access_token')
      tokenStore.del('refresh_token')
      redirect('/login')
      throw err
    }
    if (!(await refreshTokens())) throw err // worker 已 redirect
    return await _client<T>(url, options) // onRequest 自动带新 token
  }
}
