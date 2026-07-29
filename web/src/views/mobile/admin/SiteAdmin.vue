<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useNotifyStore } from '../../../stores/notification'
import {
  listAdminUsers, updateAdminUser, getAdminUserConfig, setAdminQuota,
  getAdminUsage, listAdminAudit,
} from '../../../api/admin'
import type {
  AdminUser, AdminAiConfig, QuotaUpdate, UsageSummary, PaginatedAudit,
} from '../../../api/admin'

const router = useRouter()
const notify = useNotifyStore()

const users = ref<AdminUser[]>([])
const usage = ref<UsageSummary | null>(null)
const audit = ref<PaginatedAudit | null>(null)
const loading = ref(true)
const loadError = ref('')

// 展开的用户卡（操作菜单）
const openId = ref<number | null>(null)

const stats = computed(() => ({
  total: users.value.length,
  configured: users.value.filter(u => u.has_config).length,
  tokens: usage.value?.total_tokens ?? 0,
  cost: usage.value?.total_cost ?? 0,
}))

const barColors = ['var(--d-grad)', 'var(--pixel-info)', 'var(--pixel-success)', 'var(--pixel-warning)', 'var(--pixel-accent)']

const quotaTarget = ref<AdminUser | null>(null)
const quotaForm = reactive<{ token: string | number; cost: string | number }>({ token: '', cost: '' })
const quotaSaving = ref(false)

const configUser = ref<AdminUser | null>(null)
const configData = ref<AdminAiConfig | null>(null)
const configLoading = ref(false)

function errMsg(e: unknown, fallback = '操作失败'): string {
  if (e && typeof e === 'object' && 'data' in e) {
    const d = (e as { data?: { detail?: unknown } }).data
    const det = d?.detail
    if (typeof det === 'string') return det
  }
  return fallback
}
function numOrNull(v: string | number): number | null {
  if (v === '' || v === null) return null
  const n = Number(v)
  return Number.isFinite(n) ? n : null
}
function fmtTokens(n: number): string {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(n >= 10_000_000 ? 0 : 1) + 'M'
  if (n >= 1_000) return (n / 1_000).toFixed(n >= 100_000 ? 0 : 1) + 'k'
  return String(n)
}
function fmtCost(n: number): string { return '$' + n.toFixed(2) }
function fmtTime(t: string): string { return t.slice(0, 16).replace('T', ' ') }

async function loadAll() {
  loading.value = true
  loadError.value = ''
  try {
    const [u, us, au] = await Promise.all([listAdminUsers(), getAdminUsage(), listAdminAudit()])
    users.value = u
    usage.value = us
    audit.value = au
  } catch (e) {
    loadError.value = errMsg(e, '加载失败')
  } finally {
    loading.value = false
  }
}

async function toggleAdmin(u: AdminUser) {
  try {
    const upd = await updateAdminUser(u.id, { is_admin: !u.is_admin })
    Object.assign(u, upd)
    notify.success(upd.is_admin ? '已提升为管理员' : '已撤销管理员')
  } catch (e) {
    notify.error(errMsg(e, '操作失败'))
  }
}
async function toggleDisabled(u: AdminUser) {
  try {
    const upd = await updateAdminUser(u.id, { disabled: !u.disabled })
    Object.assign(u, upd)
    notify.success(upd.disabled ? '已禁用用户' : '已启用用户')
  } catch (e) {
    notify.error(errMsg(e, '操作失败'))
  }
}

function openQuota(u: AdminUser) {
  quotaTarget.value = u
  quotaForm.token = ''
  quotaForm.cost = ''
  openId.value = null
}
async function saveQuota() {
  if (!quotaTarget.value) return
  const id = quotaTarget.value.id
  const data: QuotaUpdate = {
    monthly_token_cap: numOrNull(quotaForm.token),
    monthly_cost_cap_usd: numOrNull(quotaForm.cost),
  }
  quotaSaving.value = true
  try {
    await setAdminQuota(id, data)
    notify.success('配额已更新')
    quotaTarget.value = null
  } catch (e) {
    notify.error(errMsg(e, '保存配额失败'))
  } finally {
    quotaSaving.value = false
  }
}

async function viewConfig(u: AdminUser) {
  configUser.value = u
  configData.value = null
  configLoading.value = true
  openId.value = null
  try {
    configData.value = await getAdminUserConfig(u.id)
  } catch (e) {
    notify.error(errMsg(e, '加载配置失败'))
  } finally {
    configLoading.value = false
  }
}

onMounted(loadAll)
</script>

<template>
  <div class="m-screen">
    <div class="m-head">
      <span class="m-head__back" @click="router.push('/settings')">◂</span>
      <span class="m-head__title">站点管理</span>
      <span class="m-head__sub" style="cursor: pointer;" @click="loadAll">↻</span>
    </div>

    <div v-if="loading" class="m-loading">加载中…</div>
    <div v-else-if="loadError" class="m-card" style="color: var(--pixel-accent);">{{ loadError }}</div>

    <template v-else>
      <!-- 统计 -->
      <div class="m-grid-2">
        <div class="m-stat">
          <div class="m-stat__num">{{ stats.total }}</div>
          <div class="m-stat__lbl">总用户</div>
        </div>
        <div class="m-stat">
          <div class="m-stat__num">{{ stats.configured }}</div>
          <div class="m-stat__lbl">已配置 AI</div>
        </div>
        <div class="m-stat">
          <div class="m-stat__num">{{ fmtTokens(stats.tokens) }}</div>
          <div class="m-stat__lbl">本月 tokens</div>
        </div>
        <div class="m-stat">
          <div class="m-stat__num m-stat__num--gold">{{ fmtCost(stats.cost) }}</div>
          <div class="m-stat__lbl">本月成本</div>
        </div>
      </div>

      <!-- 用户列表 -->
      <div class="m-section-title">用户管理 · {{ users.length }}</div>
      <div v-for="u in users" :key="u.id" class="usr-card" :class="{ off: u.disabled }">
        <div class="usr-top" @click="openId = openId === u.id ? null : u.id">
          <span class="usr-av">{{ u.is_admin ? '◈' : '☺' }}</span>
          <div class="usr-main">
            <div class="usr-name">
              {{ u.username }}
              <span class="m-tag" :class="u.is_admin ? 'm-tag--warn' : ''" style="margin-left: 4px;">{{ u.is_admin ? 'ADMIN' : 'USER' }}</span>
              <span v-if="u.disabled" class="m-tag m-tag--danger" style="margin-left: 2px;">禁用</span>
            </div>
            <div class="usr-sub">{{ u.email || '—' }}</div>
          </div>
          <span class="usr-chev">{{ openId === u.id ? '▴' : '▾' }}</span>
        </div>

        <div class="usr-meta">
          <div class="usr-meta-row">
            <span class="m-hint">AI 配置</span>
            <span v-if="u.has_config" class="cfg-on">✦ {{ u.model || '—' }}</span>
            <span v-else class="cfg-off">未配置</span>
          </div>
          <div class="usr-meta-row">
            <span class="m-hint">本月用量</span>
            <span class="m-mono">{{ fmtTokens(u.tokens_month) }} tok · {{ fmtCost(u.cost_month) }}</span>
          </div>
        </div>

        <div v-if="openId === u.id" class="usr-actions">
          <button v-if="u.has_config" class="m-btn m-btn--sm m-btn--ghost" @click="viewConfig(u)">◉ 查看配置</button>
          <button class="m-btn m-btn--sm m-btn--ghost" @click="openQuota(u)">◎ 配额</button>
          <button class="m-btn m-btn--sm m-btn--ghost" @click="toggleAdmin(u)">{{ u.is_admin ? '▽ 撤管' : '△ 提权' }}</button>
          <button class="m-btn m-btn--sm" :class="u.disabled ? 'm-btn--primary' : 'm-btn--danger'" @click="toggleDisabled(u)">{{ u.disabled ? '◐ 启用' : '⊘ 禁用' }}</button>
        </div>
      </div>
      <div v-if="!users.length" class="m-empty"><div class="m-empty__ico">∅</div><div class="m-empty__txt">无用户数据</div></div>

      <!-- 模型分布 -->
      <div class="m-section-title">模型分布 · 本月</div>
      <div class="m-card">
        <div v-if="usage && usage.by_model.length" class="model-bars">
          <div v-for="(m, idx) in usage.by_model" :key="m.name" class="mb">
            <span class="nm">{{ m.name }}</span>
            <span class="tr"><i :style="{ width: Math.max(m.pct, 3) + '%', background: barColors[idx % barColors.length] }"></i></span>
            <span class="pc">{{ m.pct.toFixed(0) }}%</span>
          </div>
        </div>
        <div v-else class="m-hint">暂无数据</div>
      </div>

      <!-- 审计日志 -->
      <div class="m-section-title">审计日志 · {{ audit?.total ?? 0 }}</div>
      <div class="m-card">
        <div v-if="audit && audit.items.length" class="timeline">
          <div v-for="item in audit.items" :key="item.id" class="tl-item">
            <div class="tl-time">{{ fmtTime(item.created_at) }}</div>
            <div class="tl-text">
              <b>{{ item.action }}</b>
              <span v-if="item.target_type" class="tl-target">{{ item.target_type }}<span v-if="item.target_id !== null">#{{ item.target_id }}</span></span>
            </div>
          </div>
        </div>
        <div v-else class="m-hint">暂无记录</div>
      </div>
    </template>

    <!-- 配额模态 -->
    <Transition name="sheet">
      <div v-if="quotaTarget" class="m-overlay" @click.self="quotaTarget = null">
        <div class="m-sheet">
          <div class="sheet-head">
            <span>编辑配额 · {{ quotaTarget.username }}</span>
            <button class="sheet-close" @click="quotaTarget = null">✕</button>
          </div>
          <div class="sheet-body">
            <div class="m-field">
              <span class="m-field__label">月 Token 上限 <span style="color: var(--pixel-text-secondary);">· 留空 = 不限</span></span>
              <input v-model="quotaForm.token" type="number" min="0" class="m-input" placeholder="如 500000" />
            </div>
            <div class="m-field" style="margin-bottom: 0;">
              <span class="m-field__label">月成本上限 USD <span style="color: var(--pixel-text-secondary);">· 留空 = 不限</span></span>
              <input v-model="quotaForm.cost" type="number" min="0" step="0.5" class="m-input" placeholder="如 10" />
            </div>
            <div class="usage-mini">
              <div class="usage-mini-row"><span>本月 tokens</span><b>{{ fmtTokens(quotaTarget.tokens_month) }}</b></div>
              <div class="usage-mini-row"><span>本月成本</span><b>{{ fmtCost(quotaTarget.cost_month) }}</b></div>
            </div>
          </div>
          <div class="sheet-foot">
            <button class="m-btn m-btn--ghost" style="flex: 1;" @click="quotaTarget = null">取消</button>
            <button class="m-btn m-btn--primary" style="flex: 1;" :disabled="quotaSaving" @click="saveQuota">{{ quotaSaving ? '保存中…' : '✓ 保存' }}</button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- 配置查看模态 -->
    <Transition name="sheet">
      <div v-if="configUser" class="m-overlay" @click.self="configUser = null">
        <div class="m-sheet">
          <div class="sheet-head">
            <span>AI 配置 · {{ configUser.username }} <span class="readonly-tag">只读</span></span>
            <button class="sheet-close" @click="configUser = null">✕</button>
          </div>
          <div class="sheet-body">
            <div v-if="configLoading" class="m-hint">加载中…</div>
            <div v-else-if="configData" class="cfg-detail">
              <div class="cfg-row"><span class="cfg-k">服务商</span><span class="cfg-v">{{ configData.provider || '—' }}</span></div>
              <div class="cfg-row"><span class="cfg-k">模型</span><span class="cfg-v mono">{{ configData.model || '—' }}</span></div>
              <div class="cfg-row"><span class="cfg-k">Base URL</span><span class="cfg-v mono">{{ configData.base_url || '—' }}</span></div>
              <div class="cfg-row"><span class="cfg-k">API 密钥</span><span class="cfg-v mono">{{ configData.api_key_masked || '—' }}</span></div>
              <div class="cfg-row"><span class="cfg-k">最大轮数</span><span class="cfg-v">{{ configData.max_turns }}</span></div>
              <div class="cfg-row"><span class="cfg-k">单次预算</span><span class="cfg-v">{{ fmtCost(configData.max_budget_usd) }}</span></div>
              <div class="cfg-row"><span class="cfg-k">状态</span>
                <span class="m-tag" :class="configData.enabled ? 'm-tag--ok' : ''">{{ configData.enabled ? '已启用' : '已停用' }}</span>
              </div>
              <div v-if="configData.system_prompt_extra" class="cfg-row col">
                <span class="cfg-k">附加系统提示</span>
                <span class="cfg-v prompt-extra">{{ configData.system_prompt_extra }}</span>
              </div>
            </div>
            <div v-else class="m-hint">无配置数据</div>
          </div>
          <div class="sheet-foot">
            <button class="m-btn m-btn--primary" style="flex: 1;" @click="configUser = null">关闭</button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
/* 用户卡 */
.usr-card { background: var(--pixel-card-bg); backdrop-filter: blur(10px); border: 1px solid var(--pixel-border); border-radius: var(--d-radius); box-shadow: var(--d-shadow-sm); padding: 12px 14px; margin-top: 10px; transition: opacity .2s; }
.usr-card.off { opacity: .55; }
.usr-card.off .usr-name { text-decoration: line-through; }
.usr-top { display: flex; align-items: center; gap: 10px; cursor: pointer; }
.usr-av { width: 36px; height: 36px; flex: none; display: grid; place-items: center; background: var(--pixel-bg-secondary); border: 1px solid var(--pixel-border); border-radius: 10px; color: var(--pixel-primary); font-size: 16px; }
.usr-main { flex: 1; min-width: 0; }
.usr-name { font-weight: 600; font-size: 14px; display: flex; align-items: center; flex-wrap: wrap; }
.usr-sub { font-family: var(--font-pixel-num); font-size: 11px; color: var(--pixel-text-secondary); margin-top: 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.usr-chev { color: var(--pixel-text-secondary); font-size: 12px; padding: 4px; }

.usr-meta { margin-top: 10px; padding-top: 10px; border-top: 1px dashed var(--pixel-border); display: flex; flex-direction: column; gap: 6px; }
.usr-meta-row { display: flex; align-items: center; justify-content: space-between; gap: 8px; font-size: 12px; }
.cfg-on { font-family: var(--font-pixel-num); color: var(--pixel-info); font-size: 12px; }
.cfg-off { font-family: var(--font-pixel-num); color: var(--pixel-text-secondary); font-size: 11px; }

.usr-actions { margin-top: 10px; padding-top: 10px; border-top: 1px solid var(--pixel-border); display: flex; flex-wrap: wrap; gap: 6px; }

/* 模型分布 */
.model-bars { display: flex; flex-direction: column; gap: 10px; }
.mb { display: grid; grid-template-columns: 5rem 1fr 2.6rem; align-items: center; gap: 8px; }
.mb .nm { font-family: var(--font-pixel-num); font-size: 11px; color: var(--pixel-text-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.mb .tr { height: 9px; border-radius: 999px; background: var(--pixel-bg-secondary); overflow: hidden; }
.mb .tr > i { display: block; height: 100%; border-radius: inherit; }
.mb .pc { font-family: var(--font-pixel-num); font-size: 11px; color: var(--pixel-text); text-align: right; }

/* 审计时间线 */
.timeline { display: flex; flex-direction: column; gap: 12px; }
.tl-item { position: relative; padding-left: 14px; }
.tl-item::before { content: ""; position: absolute; left: 0; top: 5px; width: 6px; height: 6px; border-radius: 50%; background: var(--pixel-primary); box-shadow: 0 0 8px var(--pixel-primary); }
.tl-item::after { content: ""; position: absolute; left: 2px; top: 13px; bottom: -12px; width: 2px; background: var(--pixel-border); }
.tl-item:last-child::after { display: none; }
.tl-time { font-family: var(--font-pixel-num); font-size: 10px; color: var(--pixel-text-secondary); }
.tl-text { font-size: 12px; color: var(--pixel-text); margin-top: 2px; }
.tl-text b { font-weight: 600; }
.tl-target { font-family: var(--font-pixel-num); font-size: 11px; color: var(--pixel-info); margin-left: 6px; }

/* 底部抽屉式模态 */
.m-overlay { position: fixed; inset: 0; z-index: 300; background: rgba(0, 0, 0, .6); backdrop-filter: blur(6px); display: flex; align-items: flex-end; }
.m-sheet { width: 100%; background: var(--pixel-bg-secondary); border-top-left-radius: 18px; border-top-right-radius: 18px; border-top: 1px solid var(--pixel-border-2, rgba(255,255,255,.16)); box-shadow: var(--d-shadow); max-height: 86vh; display: flex; flex-direction: column; padding-bottom: env(safe-area-inset-bottom, 0px); }
[data-theme="light"] .m-sheet { background: #fff; }
.sheet-head { display: flex; align-items: center; justify-content: space-between; padding: 14px 16px; border-bottom: 1px solid var(--pixel-border); font-family: var(--font-pixel-num); font-size: 13px; color: var(--pixel-text); flex: none; }
.readonly-tag { font-size: 10px; color: var(--pixel-text-secondary); padding: 1px 6px; border: 1px solid var(--pixel-border); border-radius: 3px; margin-left: 4px; }
.sheet-close { background: transparent; border: 0; color: var(--pixel-text-secondary); cursor: pointer; font-size: 16px; padding: 4px; }
.sheet-body { padding: 16px; overflow-y: auto; display: flex; flex-direction: column; gap: 14px; }
.sheet-foot { display: flex; gap: 8px; padding: 12px 16px; border-top: 1px solid var(--pixel-border); flex: none; }

.usage-mini { background: var(--pixel-card-bg); border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); padding: 10px 12px; display: flex; flex-direction: column; gap: 6px; }
.usage-mini-row { display: flex; justify-content: space-between; font-family: var(--font-pixel-num); font-size: 11px; color: var(--pixel-text-secondary); }
.usage-mini-row b { color: var(--pixel-text); font-weight: 600; }

.cfg-detail { display: flex; flex-direction: column; gap: 4px; }
.cfg-row { display: flex; align-items: center; gap: 12px; padding: 8px 0; border-bottom: 1px solid var(--pixel-border); }
.cfg-row:last-child { border-bottom: 0; }
.cfg-row.col { flex-direction: column; align-items: flex-start; gap: 6px; }
.cfg-k { font-family: var(--font-pixel-num); font-size: 10px; color: var(--pixel-text-secondary); min-width: 5rem; letter-spacing: .04em; text-transform: uppercase; }
.cfg-v { font-size: 13px; color: var(--pixel-text); word-break: break-all; text-align: right; flex: 1; }
.cfg-v.mono { font-family: var(--font-pixel-num); font-size: 12px; }
.prompt-extra { font-size: 12px; line-height: 1.5; color: var(--pixel-text-secondary); background: var(--pixel-card-bg); padding: 8px 10px; border-radius: var(--d-radius-sm); border: 1px solid var(--pixel-border); white-space: pre-wrap; text-align: left; flex: none; width: 100%; box-sizing: border-box; }

.sheet-enter-active, .sheet-leave-active { transition: opacity .2s ease; }
.sheet-enter-from, .sheet-leave-to { opacity: 0; }
.sheet-enter-active .m-sheet, .sheet-leave-active .m-sheet { transition: transform .25s cubic-bezier(.2, .7, .2, 1); }
.sheet-enter-from .m-sheet, .sheet-leave-to .m-sheet { transform: translateY(100%); }
</style>
