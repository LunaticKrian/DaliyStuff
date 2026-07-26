/** 冒险者履历 DOSSIER · 类型定义（与后端 schemas/resume.py camelCase 严格一致） */

export type TimelineType = 'work' | 'edu'
export type SectionName = 'timeline' | 'project' | 'skill' | 'award'
export type ProfileField =
  | 'name' | 'title' | 'location' | 'years' | 'phone' | 'email' | 'site' | 'github'

export interface Profile {
  name: string
  title: string
  location: string
  years: string
  phone: string
  email: string
  site: string
  github: string
}

export interface TimelineEntry {
  type: TimelineType
  role: string
  org: string
  date: string
  desc: string
}

export interface ProjectEntry {
  name: string
  stack: string
  desc: string
}

export interface SkillGroup {
  cat: string
  tags: string[]
}

export interface AwardEntry {
  name: string
  issuer: string
  year: string
}

export interface ResumeData {
  profile: Profile
  timeline: TimelineEntry[]
  project: ProjectEntry[]
  skill: SkillGroup[]
  award: AwardEntry[]
}

export interface Resume {
  id: number
  title: string
  lang: string
  template: string
  revision: number
  data: ResumeData
  updatedAt: string
}

export interface ResumeListItem {
  id: number
  title: string
  lang: string
  template: string
  revision: number
  updatedAt: string
}

/** PendingChange.diff 的结构 */
export interface ChangeDiff {
  section: string
  field?: string | null
  index?: number | null
  before: unknown
  after: unknown
  deleted?: boolean
}

export interface PendingChange {
  id: number
  groupId: string
  tool: string
  args: Record<string, unknown>
  diff: ChangeDiff
  baseRevision: number
  lang: string
  status: 'pending' | 'applied' | 'denied'
  createdAt: string
}

export interface PendingGroup {
  groupId: string
  baseRevision: number
  changes: PendingChange[]
}

export interface VersionItem {
  revision: number
  summary: string
  source: 'manual' | 'nexa' | string
  createdAt: string
}

export interface VersionDiffSection {
  section: string
  changed: boolean
  aCount: number
  bCount: number
  fields?: string[]
}

export interface VersionDiff {
  a: number
  b: number
  sections: VersionDiffSection[]
}

export interface ResumeMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  createdAt: string
}

/** SSE 事件（与后端 routers/resume.py _sse 一致） */
export type ResumeStreamEvent =
  | { type: 'start'; groupId: string }
  | { type: 'delta'; text: string }
  | { type: 'tool_read'; name: string }
  | {
      type: 'tool_call'
      pending_id: number
      group_id: string
      tool: string
      args: Record<string, unknown>
      diff: ChangeDiff
      base_revision: number
      lang: string
    }
  | { type: 'done'; text: string; subtype: string; count: number }
  | { type: 'error'; message: string }
  | { type: 'end'; groupId: string }
