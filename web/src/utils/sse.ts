import type { ChatStreamEvent } from '../types/chat'
import type { ResumeStreamEvent } from '../types/resume'
import { getOrigin, tokenStore, redirect } from './platform'

/** 带 JWT 的 SSE 客户端（EventSource 不能带 Authorization 头，故用 fetch + ReadableStream）。
 *  解析 `text/event-stream`：以空行分隔事件，取 `data:` 行拼成 JSON。 */

function apiBase(): string {
  return getOrigin() + '/api'
}

async function refreshToken(): Promise<boolean> {
  const rt = tokenStore.get('refresh_token')
  if (!rt) return false
  try {
    const res = await fetch(`${apiBase()}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: rt }),
    })
    if (!res.ok) return false
    const data = await res.json()
    tokenStore.set('access_token', data.access_token)
    tokenStore.set('refresh_token', data.refresh_token)
    return true
  } catch {
    return false
  }
}

function authHeader(): string | null {
  const t = tokenStore.get('access_token')
  return t ? `Bearer ${t}` : null
}

export interface StreamOptions {
  signal?: AbortSignal
  onEvent: (e: ChatStreamEvent) => void
  onError?: (err: Error) => void
}

/** 向对话发送一条消息并流式消费 SSE 事件。返回是否成功开始流式。 */
export async function streamChatMessage(
  sessionId: number,
  content: string,
  { signal, onEvent, onError }: StreamOptions,
): Promise<void> {
  const doFetch = (token: string) =>
    fetch(`${apiBase()}/chat/sessions/${sessionId}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: token },
      body: JSON.stringify({ content }),
      signal,
    })

  let token = authHeader()
  if (!token) {
    throw new Error('未登录')
  }

  let res = await doFetch(token)

  // 401 → 刷新一次重试
  if (res.status === 401) {
    const ok = await refreshToken()
    if (!ok) {
      redirect('/login')
      return
    }
    token = authHeader()!
    res = await doFetch(token)
  }

  if (!res.ok || !res.body) {
    const msg = `请求失败 (${res.status})`
    onError?.(new Error(msg))
    return
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buf = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buf += decoder.decode(value, { stream: true })
      let sep: number
      while ((sep = buf.indexOf('\n\n')) >= 0) {
        const raw = buf.slice(0, sep)
        buf = buf.slice(sep + 2)
        const dataLine = raw
          .split('\n')
          .filter((l) => l.startsWith('data:'))
          .map((l) => l.slice(5).trim())
          .join('')
        if (!dataLine) continue
        try {
          onEvent(JSON.parse(dataLine) as ChatStreamEvent)
        } catch {
          /* 忽略无法解析的事件 */
        }
      }
    }
  } catch (e) {
    if ((e as Error).name !== 'AbortError') onError?.(e as Error)
  }
}

export interface ResumeStreamOptions {
  signal?: AbortSignal
  onEvent: (e: ResumeStreamEvent) => void
  onError?: (err: Error) => void
}

/** 简历 AI 对话：发送一条消息并流式消费 SSE 事件（复用鉴权 + 解析逻辑）。 */
export async function streamResumeChat(
  resumeId: number,
  threadId: number,
  content: string,
  { signal, onEvent, onError }: ResumeStreamOptions,
): Promise<void> {
  const doFetch = (token: string) =>
    fetch(`${apiBase()}/resume/${resumeId}/threads/${threadId}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: token },
      body: JSON.stringify({ content }),
      signal,
    })

  let token = authHeader()
  if (!token) throw new Error('未登录')

  let res = await doFetch(token)
  if (res.status === 401) {
    const ok = await refreshToken()
    if (!ok) {
      redirect('/login')
      return
    }
    token = authHeader()!
    res = await doFetch(token)
  }

  if (!res.ok || !res.body) {
    onError?.(new Error(`请求失败 (${res.status})`))
    return
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buf = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buf += decoder.decode(value, { stream: true })
      let sep: number
      while ((sep = buf.indexOf('\n\n')) >= 0) {
        const raw = buf.slice(0, sep)
        buf = buf.slice(sep + 2)
        const dataLine = raw
          .split('\n')
          .filter((l) => l.startsWith('data:'))
          .map((l) => l.slice(5).trim())
          .join('')
        if (!dataLine) continue
        try {
          onEvent(JSON.parse(dataLine) as ResumeStreamEvent)
        } catch {
          /* 忽略无法解析的事件 */
        }
      }
    }
  } catch (e) {
    if ((e as Error).name !== 'AbortError') onError?.(e as Error)
  }
}
