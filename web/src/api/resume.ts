import { api } from './client'
import { streamResumeChat } from '../utils/sse'
import type { ResumeStreamEvent } from '../types/resume'
import type {
  PendingChange,
  PendingGroup,
  Resume,
  ResumeData,
  ResumeListItem,
  ResumeMessage,
  VersionDiff,
  VersionItem,
} from '../types/resume'

const EMPTY: ResumeData = {
  profile: { name: '', title: '', location: '', years: '', phone: '', email: '', site: '', github: '' },
  timeline: [],
  project: [],
  skill: [],
  award: [],
}

export function emptyResumeData(): ResumeData {
  return JSON.parse(JSON.stringify(EMPTY))
}

// ── 简历 CRUD ──────────────────────────────────────────────────────────
export function listResumes(): Promise<ResumeListItem[]> {
  return api<ResumeListItem[]>('/resume')
}

export function getResume(id: number): Promise<Resume> {
  return api<Resume>(`/resume/${id}`)
}

export function createResume(title?: string, lang: 'zh' | 'en' = 'zh'): Promise<Resume> {
  return api<Resume>('/resume', { method: 'POST', body: { title: title ?? null, lang } })
}

export function saveResume(id: number, data: ResumeData, summary = '手动编辑'): Promise<Resume> {
  return api<Resume>(`/resume/${id}`, { method: 'PUT', body: { data, summary } })
}

export function deleteResume(id: number): Promise<void> {
  return api<void>(`/resume/${id}`, { method: 'DELETE' })
}

// ── 对话 ───────────────────────────────────────────────────────────────
export function createThread(resumeId: number): Promise<{ id: number; resumeId: number }> {
  return api(`/resume/${resumeId}/threads`, { method: 'POST', body: {} })
}

export function listMessages(resumeId: number, threadId: number): Promise<ResumeMessage[]> {
  return api(`/resume/${resumeId}/threads/${threadId}/messages`)
}

export function chat(
  resumeId: number,
  threadId: number,
  content: string,
  opts: { signal?: AbortSignal; onEvent: (e: ResumeStreamEvent) => void; onError?: (e: Error) => void },
): Promise<void> {
  return streamResumeChat(resumeId, threadId, content, opts)
}

export interface InlinePolishArgs {
  section: 'profile' | 'timeline' | 'project' | 'skill' | 'award'
  index: number
  field?: string | null
  instruction: string
}

export function inlinePolish(resumeId: number, args: InlinePolishArgs): Promise<{ pending: PendingChange }> {
  return api(`/resume/${resumeId}/inline-polish`, {
    method: 'POST',
    body: args,
    timeout: 120000,
  })
}

// ── 待确认变更 ─────────────────────────────────────────────────────────
export function listPending(resumeId: number): Promise<PendingGroup[]> {
  return api(`/resume/${resumeId}/pending`)
}

export function acceptPending(resumeId: number, pendingId: number): Promise<Resume> {
  return api(`/resume/${resumeId}/pending/${pendingId}/accept`, { method: 'POST' })
}

export function acceptGroup(resumeId: number, groupId: string): Promise<Resume> {
  return api(`/resume/${resumeId}/pending/group/${groupId}/accept`, { method: 'POST' })
}

export function denyPending(resumeId: number, pendingId: number): Promise<void> {
  return api(`/resume/${resumeId}/pending/${pendingId}`, { method: 'DELETE' })
}

export function denyGroup(resumeId: number, groupId: string): Promise<{ denied: number }> {
  return api(`/resume/${resumeId}/pending/group/${groupId}`, { method: 'DELETE' })
}

// ── 版本 ───────────────────────────────────────────────────────────────
export function listVersions(resumeId: number): Promise<VersionItem[]> {
  return api(`/resume/${resumeId}/versions`)
}

export function revertResume(resumeId: number, revision: number): Promise<Resume> {
  return api(`/resume/${resumeId}/revert/${revision}`, { method: 'POST' })
}

export function diffVersions(resumeId: number, a: number, b: number): Promise<VersionDiff> {
  return api(`/resume/${resumeId}/versions/${a}/diff/${b}`)
}
