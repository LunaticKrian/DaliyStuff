// ── 站点管理后台 · API 层 ─────────────────────────────────────────────
// /api/admin/*：用户管理 / 配置可见性 / 配额 / 用量 / 审计。仅 is_admin 可调。
import { api } from './client'

export interface AdminUser {
  id: number
  username: string
  email: string | null
  is_admin: boolean
  disabled: boolean
  has_config: boolean
  model: string
  tokens_month: number
  cost_month: number
  created_at: string
}

export interface AdminUserUpdate {
  is_admin?: boolean
  disabled?: boolean
}

export interface AdminAiConfig {
  provider: string
  model: string
  base_url: string
  api_key_masked: string
  has_key: boolean
  max_turns: number
  max_budget_usd: number
  system_prompt_extra: string | null
  enabled: boolean
}

export interface QuotaResponse {
  user_id: number
  monthly_token_cap: number | null
  monthly_cost_cap_usd: number | null
}

export interface QuotaUpdate {
  monthly_token_cap?: number | null
  monthly_cost_cap_usd?: number | null
}

export interface UsageItem {
  name: string
  tokens: number
  cost: number
  pct: number
}

export interface UsageSummary {
  total_tokens: number
  total_cost: number
  by_model: UsageItem[]
  by_agent: UsageItem[]
}

export interface AuditLogRow {
  id: number
  actor_id: number
  action: string
  target_type: string | null
  target_id: number | null
  detail: Record<string, unknown>
  ip: string | null
  created_at: string
}

export interface PaginatedAudit {
  items: AuditLogRow[]
  total: number
  page: number
  size: number
}

export function listAdminUsers(): Promise<AdminUser[]> {
  return api<AdminUser[]>('/admin/users')
}

export function updateAdminUser(id: number, data: AdminUserUpdate): Promise<AdminUser> {
  return api<AdminUser>(`/admin/users/${id}`, { method: 'PATCH', body: data })
}

export function getAdminUserConfig(id: number): Promise<AdminAiConfig> {
  return api<AdminAiConfig>(`/admin/users/${id}/ai-config`)
}

export function setAdminQuota(userId: number, data: QuotaUpdate): Promise<QuotaResponse> {
  return api<QuotaResponse>(`/admin/quota/${userId}`, { method: 'PUT', body: data })
}

export function getAdminUsage(params: { user_id?: number; agent_type?: string } = {}): Promise<UsageSummary> {
  return api<UsageSummary>('/admin/usage', { params })
}

export function listAdminAudit(params: { page?: number; size?: number; action?: string } = {}): Promise<PaginatedAudit> {
  return api<PaginatedAudit>('/admin/audit', { params })
}
