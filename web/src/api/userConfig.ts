// ── 用户 AI 配置（per-user）· API 层 ──────────────────────────────────
// /api/me/ai-config：读取（key 掩码）/ 更新 / 测试连接。
import { api } from './client'

export interface AiConfig {
  provider: string
  model: string
  base_url: string
  api_key_masked: string   // sk-****1234；空表示未设置
  has_key: boolean
  max_turns: number
  max_budget_usd: number
  system_prompt_extra: string | null
  enabled: boolean
  configured: boolean
}

export interface AiConfigUpdate {
  provider?: string
  model?: string
  base_url?: string
  api_key?: string         // 留空 / 含 **** → 后端保留旧值
  max_turns?: number
  max_budget_usd?: number
  system_prompt_extra?: string | null
  enabled?: boolean
}

export interface AiConfigTestResult {
  ok: boolean
  message: string
  model: string | null
  latency_ms: number | null
}

export function getAiConfig(): Promise<AiConfig> {
  return api<AiConfig>('/me/ai-config')
}

export function updateAiConfig(data: AiConfigUpdate): Promise<AiConfig> {
  return api<AiConfig>('/me/ai-config', { method: 'PUT', body: data })
}

/** 测试连接：可不传（测已保存配置）或传未保存的表单值。 */
export function testAiConfig(data?: AiConfigUpdate): Promise<AiConfigTestResult> {
  return api<AiConfigTestResult>('/me/ai-config/test', { method: 'POST', body: data ?? {} })
}
