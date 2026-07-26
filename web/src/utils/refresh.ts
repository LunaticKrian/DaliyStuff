import { ofetch } from 'ofetch'
import { getOrigin, tokenStore, redirect } from './platform'

/**
 * 统一刷新入口（鉴权会话化配套）。
 *
 * 全前端唯一一条 /auth/refresh 调用路径：
 * - 模块级单例去重并发（同一 tab 内多个 401 只发一次刷新）；
 * - 成功写 tokenStore（Web 端写 localStorage → 其他 tab 经 storage 事件同步）；
 * - 失败（会话被吊销 / 复用检测 / 过期）清 token 并跳登录。
 *
 * 此前 client.ts / sse.ts / auth store 各有一份 refresh，HTTP+SSE 同 tab 并发会双刷，
 * 触发服务端复用检测误伤——本模块消除该竞态。
 */
let refreshPromise: Promise<boolean> | null = null

export function refreshTokens(): Promise<boolean> {
  if (refreshPromise) return refreshPromise

  refreshPromise = (async () => {
    const rt = tokenStore.get('refresh_token')
    if (!rt) {
      redirect('/login')
      return false
    }
    try {
      const res = await ofetch<{ access_token: string; refresh_token: string }>(
        getOrigin() + '/api/auth/refresh',
        { method: 'POST', body: { refresh_token: rt } },
      )
      tokenStore.set('access_token', res.access_token)
      tokenStore.set('refresh_token', res.refresh_token)
      return true
    } catch {
      tokenStore.del('access_token')
      tokenStore.del('refresh_token')
      redirect('/login')
      return false
    } finally {
      refreshPromise = null
    }
  })()

  return refreshPromise
}
