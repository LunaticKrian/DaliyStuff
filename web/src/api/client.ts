import { ofetch, type FetchOptions, type $Fetch } from 'ofetch'
import { getOrigin, tokenStore, redirect } from '../utils/platform'

let refreshPromise: Promise<boolean> | null = null

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

async function tryRefresh(): Promise<boolean> {
  const rt = tokenStore.get('refresh_token')
  if (!rt) return false
  try {
    const res = await api<{ access_token: string; refresh_token: string }>('/auth/refresh', {
      method: 'POST',
      body: { refresh_token: rt },
    })
    tokenStore.set('access_token', res.access_token)
    tokenStore.set('refresh_token', res.refresh_token)
    return true
  } catch {
    tokenStore.del('access_token')
    tokenStore.del('refresh_token')
    return false
  }
}

function createClient(): $Fetch {
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
    async onResponseError({ response, options, request }) {
      if (response.status !== 401) return

      const url = typeof request === 'string' ? request : request.toString()
      if (
        url.includes('/auth/login') ||
        url.includes('/auth/register') ||
        url.includes('/auth/refresh')
      ) {
        tokenStore.del('access_token')
        tokenStore.del('refresh_token')
        redirect('/login')
        return
      }

      if (!refreshPromise) refreshPromise = tryRefresh()
      const refreshed = await refreshPromise
      refreshPromise = null

      if (!refreshed) {
        redirect('/login')
        return
      }

      const newToken = tokenStore.get('access_token')
      if (newToken) options.headers.set('Authorization', `Bearer ${newToken}`)
      // onResponseError 钩子要求 void 返回；重试交给 ofetch 再走一遍流程。
      await api(request as string, options as FetchOptions)
    },
  })
}

export let api = createClient()

/** origin 就绪后重建实例，使 baseURL 指向用户配置的服务器。在 main.ts 挂载前调用。 */
export function setupApiClient(): void {
  api = createClient()
}
