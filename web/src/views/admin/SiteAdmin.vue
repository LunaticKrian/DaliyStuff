<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useNotifyStore } from '../../stores/notification'
import {
  listAdminUsers, updateAdminUser, getAdminUserConfig, setAdminQuota,
  getAdminUsage, listAdminAudit,
} from '../../api/admin'
import type {
  AdminUser, AdminAiConfig, QuotaUpdate, UsageSummary, PaginatedAudit,
} from '../../api/admin'

const router = useRouter()
const notify = useNotifyStore()

const users = ref<AdminUser[]>([])
const usage = ref<UsageSummary | null>(null)
const audit = ref<PaginatedAudit | null>(null)
const loading = ref(true)
const loadError = ref('')

const stats = computed(() => ({
  total: users.value.length,
  configured: users.value.filter(u => u.has_config).length,
  tokens: usage.value?.total_tokens ?? 0,
  cost: usage.value?.total_cost ?? 0,
}))

const barColors = [
  'var(--d-grad)',
  'var(--pixel-info)',
  'var(--pixel-success)',
  'var(--pixel-warning)',
  'var(--pixel-accent)',
]

// 配额模态
const quotaTarget = ref<AdminUser | null>(null)
const quotaForm = reactive<{ token: string | number; cost: string | number }>({ token: '', cost: '' })
const quotaSaving = ref(false)

// 配置查看模态
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
  <div class="admin-page animate-fade-in">
    <div class="admin-header">
      <button class="back-btn" @click="router.push('/settings')">
        <span>◀</span><span>返回设置</span>
      </button>
      <h1 class="page-title">
        <span class="title-icon">◈</span>
        <span>站点管理后台</span>
      </h1>
      <button class="refresh-btn" @click="loadAll">{{ loading ? '刷新中…' : '↻ 刷新' }}</button>
    </div>

    <p class="page-sub">用户与权限 · AI 配置可见性 · 配额 · 调用统计 · 审计日志。所有操作均记录在案。</p>

    <div v-if="loading" class="settings-card pixel-border"><div class="card-body"><div class="field-readonly">加载中…</div></div></div>
    <div v-else-if="loadError" class="settings-card pixel-border"><div class="card-body"><div class="field-error">{{ loadError }}</div></div></div>

    <template v-else>
      <!-- 顶部统计 -->
      <div class="stat-grid">
        <div class="stat-card">
          <div class="stat-ico">⬡</div>
          <div class="stat-num grad">{{ stats.total }}</div>
          <div class="stat-lbl">总用户</div>
        </div>
        <div class="stat-card">
          <div class="stat-ico">✦</div>
          <div class="stat-num">{{ stats.configured }}</div>
          <div class="stat-lbl">已配置 AI</div>
        </div>
        <div class="stat-card">
          <div class="stat-ico">⚡</div>
          <div class="stat-num grad">{{ fmtTokens(stats.tokens) }}</div>
          <div class="stat-lbl">本月 tokens</div>
        </div>
        <div class="stat-card">
          <div class="stat-ico">◈</div>
          <div class="stat-num">{{ fmtCost(stats.cost) }}</div>
          <div class="stat-lbl">本月成本</div>
        </div>
      </div>

      <div class="g-main">
        <!-- 左：用户管理 -->
        <div class="settings-card pixel-border">
          <div class="card-header">
            <span class="card-icon">⬡</span>
            <span>用户管理</span>
            <span class="head-tag">{{ users.length }}</span>
          </div>
          <div class="table-wrap">
            <table class="usr-table">
              <thead>
                <tr>
                  <th>用户</th><th>角色</th><th>AI 配置</th>
                  <th>本月用量</th><th>状态</th><th class="ta-right">操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="u in users" :key="u.id" :class="{ disabled: u.disabled }">
                  <td>
                    <div class="usr-cell">
                      <span class="av">{{ u.is_admin ? '◈' : '☺' }}</span>
                      <div class="umin">
                        <div class="un">{{ u.username }}</div>
                        <div class="ue">{{ u.email || '—' }}</div>
                      </div>
                    </div>
                  </td>
                  <td>
                    <span class="role-badge" :class="u.is_admin ? 'admin' : ''">{{ u.is_admin ? 'ADMIN' : 'USER' }}</span>
                  </td>
                  <td>
                    <span v-if="u.has_config" class="cfg-cell">✦ {{ u.model || '—' }}</span>
                    <span v-else class="cfg-none">未配置</span>
                  </td>
                  <td>
                    <div class="usage-cell">
                      <div class="ut">{{ fmtTokens(u.tokens_month) }} tok</div>
                      <div class="uc">{{ fmtCost(u.cost_month) }}</div>
                    </div>
                  </td>
                  <td>
                    <span class="badge" :class="u.disabled ? 'danger' : 'success'">
                      <span class="dot"></span>{{ u.disabled ? '已禁用' : '正常' }}
                    </span>
                  </td>
                  <td>
                    <div class="row-actions">
                      <button v-if="u.has_config" class="mini-btn" title="查看配置" @click="viewConfig(u)">◉</button>
                      <button class="mini-btn" title="配额" @click="openQuota(u)">◎</button>
                      <button
                        class="mini-btn"
                        :title="u.is_admin ? '撤销管理员' : '提升为管理员'"
                        @click="toggleAdmin(u)"
                      >{{ u.is_admin ? '▽' : '△' }}</button>
                      <button
                        class="mini-btn"
                        :class="{ danger: !u.disabled }"
                        :title="u.disabled ? '启用' : '禁用'"
                        @click="toggleDisabled(u)"
                      >{{ u.disabled ? '◐' : '⊘' }}</button>
                    </div>
                  </td>
                </tr>
                <tr v-if="!users.length">
                  <td colspan="6" class="empty-row">无用户数据</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- 右：模型分布 + 审计 -->
        <div class="col-right">
          <div class="settings-card pixel-border">
            <div class="card-header">
              <span class="card-icon">✦</span>
              <span>模型分布</span>
              <span class="head-tag">本月</span>
            </div>
            <div class="card-body">
              <div v-if="usage && usage.by_model.length" class="model-bars">
                <div v-for="(m, idx) in usage.by_model" :key="m.name" class="mb">
                  <span class="nm" :title="m.name">{{ m.name }}</span>
                  <span class="tr"><i :style="{ width: Math.max(m.pct, 2) + '%', background: barColors[idx % barColors.length] }"></i></span>
                  <span class="pc">{{ m.pct.toFixed(0) }}%</span>
                </div>
              </div>
              <div v-else class="empty-row">暂无数据</div>
            </div>
          </div>

          <div class="settings-card pixel-border">
            <div class="card-header">
              <span class="card-icon">◷</span>
              <span>审计日志</span>
              <span class="head-tag">{{ audit?.total ?? 0 }}</span>
            </div>
            <div class="card-body">
              <div v-if="audit && audit.items.length" class="timeline">
                <div v-for="item in audit.items" :key="item.id" class="tl-item">
                  <div class="tl-time">{{ fmtTime(item.created_at) }}</div>
                  <div class="tl-text">
                    <b>{{ item.action }}</b>
                    <span v-if="item.target_type" class="tl-target">{{ item.target_type }}<span v-if="item.target_id !== null">#{{ item.target_id }}</span></span>
                  </div>
                </div>
              </div>
              <div v-else class="empty-row">暂无记录</div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- 配额模态 -->
    <Transition name="modal">
      <div v-if="quotaTarget" class="modal-overlay" @click.self="quotaTarget = null">
        <div class="modal-card pixel-border animate-scale-in">
          <div class="modal-head">
            <span>◎ 编辑配额 · {{ quotaTarget.username }}</span>
            <button class="modal-close" @click="quotaTarget = null">✕</button>
          </div>
          <div class="modal-body">
            <div class="quota-field">
              <div class="qlbl"><span>月 Token 上限</span><span class="hint">留空 = 不限</span></div>
              <input v-model="quotaForm.token" type="number" min="0" class="pixel-input" placeholder="如 500000" />
            </div>
            <div class="quota-field">
              <div class="qlbl"><span>月成本上限 (USD)</span><span class="hint">留空 = 不限</span></div>
              <input v-model="quotaForm.cost" type="number" min="0" step="0.5" class="pixel-input" placeholder="如 10" />
            </div>
            <div class="usage-mini">
              <div class="usage-mini-row"><span>本月 tokens</span><b>{{ fmtTokens(quotaTarget.tokens_month) }}</b></div>
              <div class="usage-mini-row"><span>本月成本</span><b>{{ fmtCost(quotaTarget.cost_month) }}</b></div>
            </div>
          </div>
          <div class="modal-foot">
            <button class="pixel-btn" @click="quotaTarget = null">取消</button>
            <button class="pixel-btn primary" :disabled="quotaSaving" @click="saveQuota">{{ quotaSaving ? '保存中…' : '✓ 保存' }}</button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- 配置查看模态 -->
    <Transition name="modal">
      <div v-if="configUser" class="modal-overlay" @click.self="configUser = null">
        <div class="modal-card pixel-border animate-scale-in">
          <div class="modal-head">
            <span>◉ AI 配置 · {{ configUser.username }} <span class="readonly-tag">只读</span></span>
            <button class="modal-close" @click="configUser = null">✕</button>
          </div>
          <div class="modal-body">
            <div v-if="configLoading" class="empty-row">加载中…</div>
            <div v-else-if="configData" class="cfg-detail">
              <div class="cfg-row"><span class="cfg-k">服务商</span><span class="cfg-v">{{ configData.provider || '—' }}</span></div>
              <div class="cfg-row"><span class="cfg-k">模型</span><span class="cfg-v mono">{{ configData.model || '—' }}</span></div>
              <div class="cfg-row"><span class="cfg-k">Base URL</span><span class="cfg-v mono">{{ configData.base_url || '—' }}</span></div>
              <div class="cfg-row"><span class="cfg-k">API 密钥</span><span class="cfg-v mono">{{ configData.api_key_masked || '—' }}</span></div>
              <div class="cfg-row"><span class="cfg-k">最大轮数</span><span class="cfg-v">{{ configData.max_turns }}</span></div>
              <div class="cfg-row"><span class="cfg-k">单次预算</span><span class="cfg-v">{{ fmtCost(configData.max_budget_usd) }}</span></div>
              <div class="cfg-row"><span class="cfg-k">状态</span><span class="cfg-v">
                <span class="badge" :class="configData.enabled ? 'success' : 'idle'">
                  <span class="dot"></span>{{ configData.enabled ? '已启用' : '已停用' }}
                </span>
              </span></div>
              <div v-if="configData.system_prompt_extra" class="cfg-row col">
                <span class="cfg-k">附加系统提示</span>
                <span class="cfg-v prompt-extra">{{ configData.system_prompt_extra }}</span>
              </div>
            </div>
            <div v-else class="empty-row">无配置数据</div>
          </div>
          <div class="modal-foot">
            <button class="pixel-btn primary" @click="configUser = null">关闭</button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&display=swap');

/* ═══════ 本页令牌 ══════ */
.admin-page {
  --pixel-bg: #0b0d14;
  --pixel-bg-secondary: #14171f;
  --pixel-card-bg: rgba(255, 255, 255, 0.045);
  --pixel-border: rgba(255, 255, 255, 0.09);
  --pixel-border-2: rgba(255, 255, 255, 0.16);
  --pixel-primary: #22d3ee;
  --pixel-accent: #fb7185;
  --pixel-warning: #fbbf24;
  --pixel-success: #34d399;
  --pixel-info: #38bdf8;
  --pixel-text: #f4f6fb;
  --pixel-text-secondary: #9aa3b2;
  --pixel-faint: #6b7382;
  --pixel-shadow: rgba(0, 0, 0, 0.5);
  --d-grad: linear-gradient(135deg, #818cf8 0%, #7c5cff 40%, #22d3ee 100%);
  --d-radius: 14px;
  --d-radius-sm: 10px;
  --d-shadow-sm: 0 4px 14px -8px rgba(0, 0, 0, .6);
  --d-shadow: 0 18px 44px -22px rgba(0, 0, 0, .7);
  --d-f-display: 'Space Grotesk', 'PingFang SC', system-ui, sans-serif;
  --d-f-body: 'Inter', 'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif;
  --d-f-mono: 'JetBrains Mono', ui-monospace, monospace;

  max-width: 1100px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
  font-family: var(--d-f-body);
  color: var(--pixel-text);
}
[data-theme="light"] .admin-page {
  --pixel-bg: #f4f5fa;
  --pixel-bg-secondary: #eef0f7;
  --pixel-card-bg: rgba(17, 20, 40, 0.04);
  --pixel-border: rgba(17, 20, 40, 0.12);
  --pixel-border-2: rgba(17, 20, 40, 0.16);
  --pixel-primary: #0891b2;
  --pixel-accent: #e11d48;
  --pixel-warning: #d97706;
  --pixel-success: #059669;
  --pixel-info: #0284c7;
  --pixel-text: #0f1326;
  --pixel-text-secondary: #4b5568;
  --pixel-faint: #94a3b8;
  --pixel-shadow: rgba(17, 20, 40, .15);
  --d-shadow-sm: 0 4px 14px -8px rgba(17, 20, 40, .2);
  --d-shadow: 0 18px 44px -22px rgba(17, 20, 40, .24);
}

.admin-header { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.refresh-btn { margin-left: auto; font-family: var(--d-f-body); font-size: 13px; padding: 7px 14px; border-radius: var(--d-radius-sm); border: 1px solid var(--pixel-border); background: var(--pixel-card-bg); color: var(--pixel-text); cursor: pointer; transition: color .2s, border-color .2s; }
.refresh-btn:hover { color: var(--pixel-primary); border-color: var(--pixel-primary); }
.back-btn { display: inline-flex; align-items: center; gap: 6px; background: var(--pixel-card-bg); backdrop-filter: blur(10px); border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); color: var(--pixel-text-secondary); font-family: var(--d-f-body); font-size: 13px; padding: 7px 12px; cursor: pointer; transition: color .2s, border-color .2s; }
.back-btn:hover { color: var(--pixel-primary); border-color: var(--pixel-primary); }
.page-title { font-family: var(--d-f-display); font-size: 18px; font-weight: 700; display: flex; align-items: center; gap: 10px; margin: 0; letter-spacing: -.01em; }
.title-icon { color: var(--pixel-warning); font-size: 16px; }
.page-sub { font-family: var(--d-f-mono); font-size: 12px; color: var(--pixel-text-secondary); margin: -8px 0 0; line-height: 1.5; }

/* ===== Card ===== */
.settings-card { background: var(--pixel-card-bg); backdrop-filter: blur(10px); border: 1px solid var(--pixel-border); border-radius: var(--d-radius); box-shadow: var(--d-shadow-sm); overflow: hidden; }
.card-header { display: flex; align-items: center; gap: 8px; padding: 12px 16px; border-bottom: 1px solid var(--pixel-border); font-family: var(--d-f-mono); font-size: 12px; color: var(--pixel-text); letter-spacing: .02em; user-select: none; }
.card-icon { font-size: 14px; color: var(--pixel-primary); width: 18px; text-align: center; }
.head-tag { margin-left: auto; font-size: 10px; color: var(--pixel-text-secondary); padding: 2px 8px; border: 1px solid var(--pixel-border); border-radius: 999px; }
.card-body { padding: 16px; display: flex; flex-direction: column; gap: 14px; }
.field-readonly { font-family: var(--d-f-body); font-size: 13px; color: var(--pixel-text); padding: 9px 11px; background: var(--pixel-bg-secondary); border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); opacity: .85; }
.field-error { font-family: var(--d-f-body); font-size: 12px; color: var(--pixel-accent); padding: 8px 10px; border: 1px solid var(--pixel-accent); border-radius: var(--d-radius-sm); background: rgba(251, 113, 133, .08); }
.pixel-input { background: var(--pixel-bg-secondary); border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); color: var(--pixel-text); font-family: var(--d-f-body); font-size: 13px; padding: 9px 11px; outline: none; width: 100%; box-sizing: border-box; transition: border-color .2s, box-shadow .2s; }
.pixel-input:focus { border-color: var(--pixel-primary); box-shadow: 0 0 0 3px rgba(34, 211, 238, .16); }
.pixel-input::placeholder { color: var(--pixel-text-secondary); opacity: .55; }
.pixel-btn { font-family: var(--d-f-body); font-weight: 600; font-size: 13px; padding: 9px 16px; border-radius: var(--d-radius-sm); border: 1px solid var(--pixel-border); background: var(--pixel-bg-secondary); color: var(--pixel-text); cursor: pointer; transition: color .2s, border-color .2s; }
.pixel-btn:hover:not(:disabled) { color: var(--pixel-primary); border-color: var(--pixel-primary); }
.pixel-btn:disabled { opacity: .5; cursor: not-allowed; }
.pixel-btn.primary { border: 0; color: #0a0b10; background: var(--d-grad); font-weight: 700; box-shadow: 0 8px 22px -10px rgba(99, 102, 241, .8); }
[data-theme="light"] .pixel-btn.primary { color: #fff; }

/* ===== 布局 ===== */
.g-main { display: grid; grid-template-columns: 1.6fr 1fr; gap: 16px; align-items: start; }
.col-right { display: flex; flex-direction: column; gap: 16px; }
@media (max-width: 900px) { .g-main { grid-template-columns: 1fr; } }

/* ===== 统计卡 ===== */
.stat-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
@media (max-width: 700px) { .stat-grid { grid-template-columns: repeat(2, 1fr); } }
.stat-card { background: var(--pixel-card-bg); backdrop-filter: blur(10px); border: 1px solid var(--pixel-border); border-radius: var(--d-radius); padding: 14px 16px; position: relative; overflow: hidden; }
.stat-ico { position: absolute; top: 10px; right: 12px; font-size: 22px; color: var(--pixel-faint); opacity: .5; }
.stat-num { font-family: var(--d-f-display); font-weight: 700; font-size: 26px; line-height: 1.1; }
.stat-num.grad { background: var(--d-grad); -webkit-background-clip: text; background-clip: text; color: transparent; }
.stat-lbl { font-family: var(--d-f-mono); font-size: 11px; color: var(--pixel-text-secondary); margin-top: 6px; letter-spacing: .04em; }

/* ===== 用户表 ===== */
.table-wrap { overflow-x: auto; }
.usr-table { width: 100%; border-collapse: collapse; font-size: 13px; min-width: 640px; }
.usr-table thead th { font-family: var(--d-f-mono); font-size: 11px; letter-spacing: .04em; color: var(--pixel-text-secondary); text-align: left; padding: 10px 14px; border-bottom: 1px solid var(--pixel-border); font-weight: 500; white-space: nowrap; }
.usr-table thead th.ta-right { text-align: right; }
.usr-table tbody td { padding: 11px 14px; border-bottom: 1px solid var(--pixel-border); vertical-align: middle; }
.usr-table tbody tr:last-child td { border-bottom: 0; }
.usr-table tbody tr:hover { background: var(--pixel-bg-secondary); }
tr.disabled td { opacity: .5; }
tr.disabled .un { text-decoration: line-through; }

.usr-cell { display: flex; align-items: center; gap: 10px; }
.usr-cell .av { width: 32px; height: 32px; border-radius: 50%; flex: none; display: grid; place-items: center; background: var(--pixel-bg-secondary); border: 1px solid var(--pixel-border); color: var(--pixel-primary); font-size: 14px; }
.umin .un { font-weight: 600; font-size: 13px; }
.umin .ue { font-family: var(--d-f-mono); font-size: 10px; color: var(--pixel-text-secondary); margin-top: 1px; }

.role-badge { font-family: var(--d-f-mono); font-size: 10px; letter-spacing: .06em; padding: 3px 7px; border: 1px solid var(--pixel-border); border-radius: 3px; background: var(--pixel-bg-secondary); color: var(--pixel-text-secondary); }
.role-badge.admin { color: var(--pixel-warning); border-color: rgba(251, 191, 36, .4); background: rgba(251, 191, 36, .1); }

.cfg-cell { display: inline-flex; align-items: center; gap: 4px; font-family: var(--d-f-mono); font-size: 12px; color: var(--pixel-info); }
.cfg-none { font-family: var(--d-f-mono); font-size: 11px; color: var(--pixel-faint); padding: 2px 7px; border: 1px solid var(--pixel-border); border-radius: 3px; }

.usage-cell { font-family: var(--d-f-mono); }
.usage-cell .ut { font-size: 12px; color: var(--pixel-text); }
.usage-cell .uc { font-size: 10px; color: var(--pixel-text-secondary); margin-top: 2px; }

.badge { display: inline-flex; align-items: center; gap: 5px; font-family: var(--d-f-mono); font-size: 10px; padding: 3px 8px; border-radius: 999px; border: 1px solid var(--pixel-border); white-space: nowrap; }
.badge .dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
.badge.success { color: var(--pixel-success); border-color: rgba(52, 211, 153, .4); background: rgba(52, 211, 153, .1); }
.badge.danger { color: var(--pixel-accent); border-color: rgba(251, 113, 133, .4); background: rgba(251, 113, 133, .1); }
.badge.idle { color: var(--pixel-faint); }

.row-actions { display: flex; gap: 5px; justify-content: flex-end; }
.mini-btn { width: 28px; height: 28px; display: grid; place-items: center; font-size: 13px; border: 1px solid var(--pixel-border); background: var(--pixel-bg-secondary); color: var(--pixel-text-secondary); border-radius: var(--d-radius-sm); cursor: pointer; transition: color .2s, border-color .2s; padding: 0; font-family: var(--d-f-body); }
.mini-btn:hover { color: var(--pixel-primary); border-color: var(--pixel-primary); }
.mini-btn.danger:hover { color: var(--pixel-accent); border-color: var(--pixel-accent); }

.empty-row { text-align: center; padding: 28px 12px; font-family: var(--d-f-mono); font-size: 12px; color: var(--pixel-text-secondary); }

/* ===== 模型分布 ===== */
.model-bars { display: flex; flex-direction: column; gap: 10px; }
.mb { display: grid; grid-template-columns: 6.5rem 1fr 3rem; align-items: center; gap: 10px; }
.mb .nm { font-family: var(--d-f-mono); font-size: 12px; color: var(--pixel-text-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.mb .tr { height: 10px; border-radius: 999px; background: var(--pixel-bg-secondary); overflow: hidden; }
.mb .tr > i { display: block; height: 100%; border-radius: inherit; }
.mb .pc { font-family: var(--d-f-mono); font-size: 12px; color: var(--pixel-text); text-align: right; }

/* ===== 审计时间线 ===== */
.timeline { display: flex; flex-direction: column; gap: 12px; }
.tl-item { position: relative; padding-left: 14px; }
.tl-item::before { content: ""; position: absolute; left: 0; top: 6px; width: 6px; height: 6px; border-radius: 50%; background: var(--pixel-primary); box-shadow: 0 0 8px var(--pixel-primary); }
.tl-item::after { content: ""; position: absolute; left: 2px; top: 14px; bottom: -12px; width: 2px; background: var(--pixel-border); }
.tl-item:last-child::after { display: none; }
.tl-time { font-family: var(--d-f-mono); font-size: 10px; color: var(--pixel-text-secondary); }
.tl-text { font-size: 12px; color: var(--pixel-text); margin-top: 2px; }
.tl-text b { font-weight: 600; }
.tl-target { font-family: var(--d-f-mono); font-size: 11px; color: var(--pixel-info); margin-left: 6px; }

/* ===== 模态 ===== */
.modal-overlay { position: fixed; inset: 0; z-index: 200; background: rgba(0, 0, 0, .6); backdrop-filter: blur(6px); display: grid; place-items: center; padding: 20px; }
.modal-card { background: var(--pixel-bg-secondary); border-radius: var(--d-radius); width: 100%; max-width: 460px; box-shadow: var(--d-shadow); overflow: hidden; }
[data-theme="light"] .modal-card { background: #fff; }
.modal-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; padding: 14px 18px; border-bottom: 1px solid var(--pixel-border); font-family: var(--d-f-mono); font-size: 13px; color: var(--pixel-text); }
.readonly-tag { font-size: 10px; color: var(--pixel-faint); padding: 1px 6px; border: 1px solid var(--pixel-border); border-radius: 3px; margin-left: 4px; }
.modal-close { background: transparent; border: 0; color: var(--pixel-text-secondary); cursor: pointer; font-size: 16px; padding: 4px; }
.modal-close:hover { color: var(--pixel-accent); }
.modal-body { padding: 18px; display: flex; flex-direction: column; gap: 14px; }
.modal-foot { display: flex; gap: 10px; justify-content: flex-end; padding: 14px 18px; border-top: 1px solid var(--pixel-border); }

.quota-field { display: flex; flex-direction: column; gap: 6px; }
.qlbl { display: flex; align-items: center; justify-content: space-between; font-family: var(--d-f-mono); font-size: 11px; letter-spacing: .04em; color: var(--pixel-text-secondary); text-transform: uppercase; }
.qlbl .hint { text-transform: none; letter-spacing: 0; color: var(--pixel-faint); font-size: 10px; }
.usage-mini { background: var(--pixel-card-bg); border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); padding: 10px 12px; display: flex; flex-direction: column; gap: 6px; }
.usage-mini-row { display: flex; justify-content: space-between; font-family: var(--d-f-mono); font-size: 11px; color: var(--pixel-text-secondary); }
.usage-mini-row b { color: var(--pixel-text); font-weight: 600; }

.cfg-detail { display: flex; flex-direction: column; gap: 10px; }
.cfg-row { display: flex; align-items: center; gap: 12px; padding: 8px 0; border-bottom: 1px solid var(--pixel-border); }
.cfg-row:last-child { border-bottom: 0; }
.cfg-row.col { flex-direction: column; align-items: flex-start; gap: 6px; }
.cfg-k { font-family: var(--d-f-mono); font-size: 11px; color: var(--pixel-text-secondary); min-width: 6rem; letter-spacing: .04em; }
.cfg-v { font-size: 13px; color: var(--pixel-text); word-break: break-all; }
.cfg-v.mono { font-family: var(--d-f-mono); font-size: 12px; }
.prompt-extra { font-size: 12px; line-height: 1.5; color: var(--pixel-text-secondary); background: var(--pixel-card-bg); padding: 8px 10px; border-radius: var(--d-radius-sm); border: 1px solid var(--pixel-border); white-space: pre-wrap; }

.modal-enter-active, .modal-leave-active { transition: opacity .2s ease; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
</style>
