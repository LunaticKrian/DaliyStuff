<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useNotifyStore } from '../stores/notification'
import { getAiConfig, updateAiConfig, testAiConfig } from '../api/userConfig'
import type { AiConfig, AiConfigUpdate, AiConfigTestResult } from '../api/userConfig'

const router = useRouter()
const auth = useAuthStore()
const notify = useNotifyStore()

const cfg = ref<AiConfig | null>(null)
const loading = ref(true)
const loadError = ref('')

const form = reactive({
  provider: 'anthropic',
  model: '',
  base_url: '',
  api_key: '',
  max_turns: 8,
  max_budget_usd: 0.5,
  system_prompt_extra: '',
  enabled: true,
})

const showKey = ref(false)
const saving = ref(false)
const testing = ref(false)
const testResult = ref<AiConfigTestResult | null>(null)

const isAdmin = computed(() => !!auth.user?.is_admin)
const configured = computed(() => !!cfg.value?.configured)
const hasKey = computed(() => !!cfg.value?.has_key)
const signalBars = computed(() => {
  const on = configured.value ? 4 : 0
  return Array.from({ length: 5 }, (_, i) => i < on)
})
const hudModel = computed(() => cfg.value?.model || '未配置')
const hudKey = computed(() => cfg.value?.api_key_masked || '—')
const hudProvider = computed(() =>
  cfg.value?.provider === 'anthropic' ? 'Anthropic 兼容 · GLM' : (cfg.value?.provider || '—'),
)

function errMsg(e: unknown, fallback = '操作失败'): string {
  if (e && typeof e === 'object' && 'data' in e) {
    const d = (e as { data?: { detail?: unknown } }).data
    const det = d?.detail
    if (typeof det === 'string') return det
  }
  return fallback
}

function applyConfig(c: AiConfig) {
  cfg.value = c
  form.provider = c.provider || 'anthropic'
  form.model = c.model
  form.base_url = c.base_url
  form.api_key = ''
  form.max_turns = c.max_turns
  form.max_budget_usd = c.max_budget_usd
  form.system_prompt_extra = c.system_prompt_extra ?? ''
  form.enabled = c.enabled
}

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    applyConfig(await getAiConfig())
  } catch (e) {
    loadError.value = errMsg(e, '加载配置失败')
  } finally {
    loading.value = false
  }
}

function buildPayload(): AiConfigUpdate {
  return {
    provider: form.provider,
    model: form.model.trim(),
    base_url: form.base_url.trim(),
    api_key: form.api_key,
    max_turns: form.max_turns,
    max_budget_usd: form.max_budget_usd,
    system_prompt_extra: form.system_prompt_extra.trim() || null,
    enabled: form.enabled,
  }
}

async function handleTest() {
  testing.value = true
  testResult.value = null
  try {
    testResult.value = await testAiConfig(buildPayload())
  } catch (e) {
    testResult.value = { ok: false, message: errMsg(e, '测试失败'), model: null, latency_ms: null }
  } finally {
    testing.value = false
  }
}

async function handleSave() {
  saving.value = true
  try {
    applyConfig(await updateAiConfig(buildPayload()))
    notify.success('AI 配置已保存')
  } catch (e) {
    notify.error(errMsg(e, '保存失败'))
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="ai-config-page animate-fade-in">
    <div class="ai-header">
      <button class="back-btn" @click="router.push('/settings')">
        <span>◀</span><span>返回设置</span>
      </button>
      <h1 class="page-title">
        <span class="title-icon">◈</span>
        <span>AI 模型配置</span>
      </h1>
      <router-link v-if="isAdmin" to="/hero" class="admin-link">管理后台 →</router-link>
    </div>

    <div v-if="loading" class="settings-card pixel-border"><div class="card-body"><div class="field-readonly">加载中…</div></div></div>
    <div v-else-if="loadError" class="settings-card pixel-border"><div class="card-body"><div class="field-error">{{ loadError }}</div></div></div>

    <template v-else>
      <!-- 签名：模型链路 HUD -->
      <div class="hud-card" :class="{ off: !configured }">
        <span class="tick tl"></span><span class="tick tr"></span>
        <span class="tick bl"></span><span class="tick br"></span>
        <div class="link-hud">
          <div class="signal">
            <div class="tower" :class="{ live: configured }">
              <i v-for="(on, idx) in signalBars" :key="idx" :class="{ on }"></i>
            </div>
            <div class="slbl">SIGNAL</div>
          </div>
          <div class="core">
            <span class="prov">{{ hudProvider }}</span>
            <div class="model grad">{{ hudModel }}</div>
            <div class="url">{{ cfg?.base_url || '—' }}</div>
            <span class="keychip">
              <span class="lock">▣</span>
              <span class="k">{{ hudKey }}</span>
              <span class="enc" v-if="hasKey">· 已加密存储</span>
            </span>
          </div>
          <div class="status">
            <span class="badge" :class="configured ? 'success' : 'idle'">
              <span class="dot"></span>{{ configured ? '已启用' : '未配置' }}
            </span>
            <span v-if="testResult" class="lat">{{ testResult.ok ? '↑' : '✕' }} {{ testResult.latency_ms ?? '—' }}ms</span>
          </div>
        </div>
      </div>

      <div class="g-main">
        <!-- 左：连接参数 -->
        <div class="settings-card pixel-border">
          <div class="card-header">
            <span class="card-icon">▣</span>
            <span>连接参数</span>
            <span class="head-tag">per-user</span>
          </div>
          <div class="card-body">
            <div class="ai-form-grid">
              <div class="field-group">
                <label class="field-label">服务商</label>
                <select v-model="form.provider" class="pixel-input">
                  <option value="anthropic">Anthropic 兼容（GLM / Claude）</option>
                  <option value="openai" disabled>OpenAI 兼容（敬请期待）</option>
                </select>
              </div>

              <div class="field-group">
                <label class="field-label">模型 Model</label>
                <input v-model="form.model" type="text" class="pixel-input" placeholder="如 glm-5.2" />
              </div>

              <div class="field-group span2">
                <label class="field-label">接口地址 Base URL</label>
                <input v-model="form.base_url" type="text" class="pixel-input" placeholder="https://…" />
              </div>

              <div class="field-group span2">
                <label class="field-label">
                  API 密钥
                  <span v-if="hasKey" class="opt saved">已保存</span>
                  <span v-else class="opt">加密入库 · 不回显</span>
                </label>
                <div class="key-wrap">
                  <input
                    v-model="form.api_key"
                    :type="showKey ? 'text' : 'password'"
                    class="pixel-input key-input"
                    placeholder="留空则保持原有密钥不变"
                  />
                  <button type="button" class="key-eye" @click="showKey = !showKey">{{ showKey ? '◉' : '⬤' }}</button>
                </div>
              </div>

              <div class="field-group">
                <label class="field-label">最大轮数 Max Turns</label>
                <input v-model.number="form.max_turns" type="number" min="1" max="50" class="pixel-input" />
              </div>

              <div class="field-group">
                <label class="field-label">单次预算上限 (USD)</label>
                <input v-model.number="form.max_budget_usd" type="number" step="0.1" min="0" class="pixel-input" />
              </div>

              <div class="field-group span2">
                <label class="field-label">附加系统提示</label>
                <textarea v-model="form.system_prompt_extra" class="pixel-textarea" placeholder="可选：自定义人设 / 口吻 / 输出约束。例：始终用简体中文回答，语气简洁专业。"></textarea>
              </div>

              <div class="span2 toggle-row">
                <div class="toggle-text">
                  <div class="t-main">启用此配置</div>
                  <div class="t-desc">关闭后，你的 AI 功能将不可用</div>
                </div>
                <button
                  type="button"
                  class="switch"
                  :class="{ on: form.enabled }"
                  @click="form.enabled = !form.enabled"
                >
                  <span class="track"></span><span class="thumb"></span>
                </button>
              </div>
            </div>

            <div class="action-row">
              <button class="pixel-btn" :disabled="testing" @click="handleTest">
                {{ testing ? '测试中…' : '⚡ 测试连接' }}
              </button>
              <button class="pixel-btn primary" :disabled="saving" @click="handleSave">
                {{ saving ? '保存中…' : '✓ 保存配置' }}
              </button>
            </div>

            <div v-if="testResult" class="test-result" :class="testResult.ok ? 'ok' : 'fail'">
              <div class="tr-head">{{ testResult.ok ? '✓ 连接成功' : '✕ 连接失败' }}</div>
              <div class="tr-meta">
                模型 <b>{{ testResult.model || form.model || '—' }}</b>
                <span v-if="testResult.latency_ms !== null"> · 往返 {{ testResult.latency_ms }}ms</span>
                · {{ testResult.message }}
              </div>
            </div>
          </div>
        </div>

        <!-- 右：生效范围 + 安全 -->
        <div class="col-right">
          <div class="settings-card pixel-border">
            <div class="card-header">
              <span class="card-icon">✦</span>
              <span>生效范围</span>
            </div>
            <div class="card-body">
              <div class="scope-list">
                <div class="scope-li" :class="{ off: !configured }">
                  <span class="ck">✓</span>
                  <span class="who">AI 对话（生成任务）<span class="mdl">· {{ form.model || '—' }}</span></span>
                </div>
                <div class="scope-li" :class="{ off: !configured }">
                  <span class="ck">✓</span>
                  <span class="who">简历 AI 编辑<span class="mdl">· {{ form.model || '—' }}</span></span>
                </div>
                <div class="scope-li" :class="{ off: !configured }">
                  <span class="ck">✓</span>
                  <span class="who">每日资讯 intel<span class="mdl">· {{ form.model || '—' }} · 定时</span></span>
                </div>
              </div>
              <div class="hint-block">未配置时，以上功能将全部不可用。</div>
            </div>
          </div>

          <div class="settings-card pixel-border">
            <div class="card-header">
              <span class="card-icon">◈</span>
              <span>安全</span>
            </div>
            <div class="card-body">
              <p class="safe-text">
                你的 API 密钥使用 <code>AES / Fernet</code> 加密后存入数据库，任何接口都
                <strong>不会回显明文</strong>，仅返回掩码。仅本人可修改此配置。
              </p>
              <div class="badge-row">
                <span class="mini-badge ok"><span class="dot"></span>加密存储</span>
                <span class="mini-badge">掩码回显</span>
                <span class="mini-badge">仅本人可改</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&display=swap');

/* ═══════ 本页令牌：--pixel-* 重映射为高级深色（浅色自适应）═══════ */
.ai-config-page {
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

  max-width: 960px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
  font-family: var(--d-f-body);
  color: var(--pixel-text);
}
[data-theme="light"] .ai-config-page {
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

.ai-header { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.admin-link { margin-left: auto; font-family: var(--d-f-mono); font-size: 12px; color: var(--pixel-warning); text-decoration: none; padding: 7px 12px; border: 1px solid rgba(251, 191, 36, .35); border-radius: var(--d-radius-sm); background: rgba(251, 191, 36, .06); transition: background .2s ease; }
.admin-link:hover { background: rgba(251, 191, 36, .12); }
.back-btn { display: inline-flex; align-items: center; gap: 6px; background: var(--pixel-card-bg); backdrop-filter: blur(10px); border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); color: var(--pixel-text-secondary); font-family: var(--d-f-body); font-size: 13px; padding: 7px 12px; cursor: pointer; transition: color .2s ease, border-color .2s ease; }
.back-btn:hover { color: var(--pixel-primary); border-color: var(--pixel-primary); }
.page-title { font-family: var(--d-f-display); font-size: 18px; font-weight: 700; display: flex; align-items: center; gap: 10px; margin: 0; letter-spacing: -.01em; }
.title-icon { color: var(--pixel-primary); font-size: 16px; }

/* ===== Card（沿用 Settings 写法） ===== */
.settings-card { background: var(--pixel-card-bg); backdrop-filter: blur(10px); border: 1px solid var(--pixel-border); border-radius: var(--d-radius); box-shadow: var(--d-shadow-sm); overflow: hidden; }
.card-header { display: flex; align-items: center; gap: 8px; padding: 12px 16px; border-bottom: 1px solid var(--pixel-border); font-family: var(--d-f-mono); font-size: 12px; color: var(--pixel-text); letter-spacing: .02em; user-select: none; }
.card-icon { font-size: 14px; color: var(--pixel-primary); width: 18px; text-align: center; }
.head-tag { margin-left: auto; font-size: 10px; color: var(--pixel-text-secondary); padding: 2px 8px; border: 1px solid var(--pixel-border); border-radius: 999px; }
.card-body { padding: 16px; display: flex; flex-direction: column; gap: 14px; }
.field-group { display: flex; flex-direction: column; gap: 6px; }
.field-label { font-family: var(--d-f-mono); font-size: 11px; color: var(--pixel-text-secondary); letter-spacing: .04em; display: flex; align-items: center; gap: 8px; }
.field-label .opt { font-size: 10px; color: var(--pixel-faint); }
.field-label .opt.saved { color: var(--pixel-success); }
.field-readonly { font-family: var(--d-f-body); font-size: 13px; color: var(--pixel-text); padding: 9px 11px; background: var(--pixel-bg-secondary); border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); opacity: .85; }
.pixel-input { background: var(--pixel-bg-secondary); border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); color: var(--pixel-text); font-family: var(--d-f-body); font-size: 13px; padding: 9px 11px; outline: none; width: 100%; box-sizing: border-box; transition: border-color .2s ease, box-shadow .2s ease; }
.pixel-input:focus { border-color: var(--pixel-primary); box-shadow: 0 0 0 3px rgba(34, 211, 238, .16); }
.pixel-input::placeholder { color: var(--pixel-text-secondary); opacity: .55; }
.pixel-textarea { background: var(--pixel-bg-secondary); border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); color: var(--pixel-text); font-family: var(--d-f-body); font-size: 13px; padding: 10px 11px; outline: none; width: 100%; min-height: 80px; resize: vertical; box-sizing: border-box; transition: border-color .2s ease, box-shadow .2s ease; line-height: 1.5; }
.pixel-textarea:focus { border-color: var(--pixel-primary); box-shadow: 0 0 0 3px rgba(34, 211, 238, .16); }
.pixel-textarea::placeholder { color: var(--pixel-text-secondary); opacity: .55; }
.field-error { font-family: var(--d-f-body); font-size: 12px; color: var(--pixel-accent); padding: 8px 10px; border: 1px solid var(--pixel-accent); border-radius: var(--d-radius-sm); background: rgba(251, 113, 133, .08); }
.pixel-btn { font-family: var(--d-f-body); font-weight: 600; font-size: 13px; padding: 9px 16px; border-radius: var(--d-radius-sm); border: 1px solid var(--pixel-border); background: var(--pixel-bg-secondary); color: var(--pixel-text); cursor: pointer; transition: color .2s ease, border-color .2s ease; }
.pixel-btn:hover:not(:disabled) { color: var(--pixel-primary); border-color: var(--pixel-primary); }
.pixel-btn:disabled { opacity: .5; cursor: not-allowed; }
.pixel-btn.primary { border: 0; color: #0a0b10; background: var(--d-grad); font-weight: 700; box-shadow: 0 8px 22px -10px rgba(99, 102, 241, .8); }
.pixel-btn.primary:hover:not(:disabled) { box-shadow: 0 12px 28px -8px rgba(99, 102, 241, .95); }
[data-theme="light"] .pixel-btn.primary { color: #fff; }

/* ===== 布局 ===== */
.g-main { display: grid; grid-template-columns: 1.4fr 1fr; gap: 16px; align-items: start; }
.col-right { display: flex; flex-direction: column; gap: 16px; }
@media (max-width: 860px) { .g-main { grid-template-columns: 1fr; } }

/* ===== 表单网格 ===== */
.ai-form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px 16px; }
.ai-form-grid .span2 { grid-column: 1 / -1; }
@media (max-width: 560px) { .ai-form-grid { grid-template-columns: 1fr; } .ai-form-grid .span2 { grid-column: auto; } }
.key-wrap { position: relative; }
.key-wrap .key-input { padding-right: 40px; font-family: var(--d-f-mono); letter-spacing: .08em; }
.key-eye { position: absolute; right: 6px; top: 50%; transform: translateY(-50%); width: 30px; height: 30px; border: 0; background: transparent; color: var(--pixel-faint); cursor: pointer; border-radius: 6px; font-size: 14px; }
.key-eye:hover { color: var(--pixel-text); background: var(--pixel-bg-secondary); }

.toggle-row { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 10px 0 4px; border-top: 1px dashed var(--pixel-border); }
.toggle-text { display: flex; flex-direction: column; gap: 2px; }
.t-main { font-size: 13px; font-weight: 600; }
.t-desc { font-family: var(--d-f-mono); font-size: 11px; color: var(--pixel-text-secondary); }
.switch { position: relative; width: 44px; height: 24px; flex: none; background: transparent; border: 0; cursor: pointer; padding: 0; }
.switch .track { position: absolute; inset: 0; background: var(--pixel-bg-secondary); border: 1px solid var(--pixel-border); border-radius: 999px; transition: background .2s ease; }
.switch .thumb { position: absolute; top: 3px; left: 3px; width: 16px; height: 16px; background: var(--pixel-text-secondary); border-radius: 50%; transition: left .2s ease, background .2s ease; }
.switch.on .track { background: var(--d-grad); border-color: transparent; }
.switch.on .thumb { left: 23px; background: #fff; }

.action-row { display: flex; gap: 10px; }
.action-row .pixel-btn { flex: 1; text-align: center; }

/* ===== 测试结果 ===== */
.test-result { padding: 12px 14px; border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); background: var(--pixel-bg-secondary); }
.test-result.ok { border-color: rgba(52, 211, 153, .4); background: rgba(52, 211, 153, .07); }
.test-result.fail { border-color: rgba(251, 113, 133, .4); background: rgba(251, 113, 133, .07); }
.test-result .tr-head { font-size: 13px; font-weight: 600; }
.test-result.ok .tr-head { color: var(--pixel-success); }
.test-result.fail .tr-head { color: var(--pixel-accent); }
.test-result .tr-meta { font-family: var(--d-f-mono); font-size: 12px; color: var(--pixel-text-secondary); margin-top: 4px; }
.test-result .tr-meta b { color: var(--pixel-text); font-weight: 600; }

/* ═══════ 签名：模型链路 HUD ═══════ */
.hud-card { position: relative; border: 1px solid var(--pixel-border-2); border-radius: 6px; overflow: hidden; background:
  repeating-linear-gradient(135deg, rgba(255,255,255,.018) 0 2px, transparent 2px 5px),
  var(--pixel-card-bg); backdrop-filter: blur(10px); box-shadow: var(--d-shadow-sm); }
[data-theme="light"] .hud-card { background:
  repeating-linear-gradient(135deg, rgba(17,20,40,.022) 0 2px, transparent 2px 5px),
  var(--pixel-card-bg); }
.hud-card::before { content: ""; position: absolute; inset: 0; border-radius: 6px; padding: 1px; background: var(--d-grad); -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0); -webkit-mask-composite: xor; mask-composite: exclude; opacity: .35; pointer-events: none; }
.tick { position: absolute; width: 10px; height: 10px; border: 2px solid var(--pixel-primary); }
.tick.tl { top: 6px; left: 6px; border-right: 0; border-bottom: 0; }
.tick.tr { top: 6px; right: 6px; border-left: 0; border-bottom: 0; }
.tick.bl { bottom: 6px; left: 6px; border-right: 0; border-top: 0; }
.tick.br { bottom: 6px; right: 6px; border-left: 0; border-top: 0; }

.link-hud { display: grid; grid-template-columns: auto 1fr auto; gap: 22px; align-items: center; padding: 22px 26px; }
.signal { display: flex; flex-direction: column; align-items: center; gap: 8px; }
.tower { display: flex; align-items: flex-end; gap: 3px; height: 56px; }
.tower > i { width: 7px; border-radius: 1px; background: var(--pixel-bg-secondary); border: 1px solid var(--pixel-border); transition: background .3s, box-shadow .3s; }
.tower > i:nth-child(1) { height: 30%; }
.tower > i:nth-child(2) { height: 48%; }
.tower > i:nth-child(3) { height: 68%; }
.tower > i:nth-child(4) { height: 88%; }
.tower > i:nth-child(5) { height: 100%; }
.tower > i.on { background: var(--pixel-primary); border-color: transparent; box-shadow: 0 0 9px rgba(34, 211, 238, .5); }
.tower.live > i.on { animation: hud-pulse-bar 1.6s ease-in-out infinite; }
.tower.live > i.on:nth-child(2) { animation-delay: .15s; }
.tower.live > i.on:nth-child(3) { animation-delay: .3s; }
.tower.live > i.on:nth-child(4) { animation-delay: .45s; }
@keyframes hud-pulse-bar { 0%, 100% { opacity: .55; } 50% { opacity: 1; } }
.slbl { font-family: var(--d-f-mono); font-size: 10px; letter-spacing: .1em; color: var(--pixel-faint); text-transform: uppercase; }

.core { min-width: 0; }
.prov { display: inline-flex; align-items: center; gap: 6px; font-family: var(--d-f-mono); font-size: 11px; letter-spacing: .08em; color: var(--pixel-primary); text-transform: uppercase; }
.prov::before { content: ""; width: 6px; height: 6px; background: var(--pixel-primary); box-shadow: 0 0 8px var(--pixel-primary); }
.model { font-family: var(--d-f-display); font-weight: 700; font-size: 28px; line-height: 1.05; margin: 6px 0 4px; word-break: break-all; }
.model.grad { background: var(--d-grad); -webkit-background-clip: text; background-clip: text; color: transparent; }
.url { font-family: var(--d-f-mono); font-size: 12px; color: var(--pixel-text-secondary); word-break: break-all; }
.keychip { display: inline-flex; align-items: center; gap: 6px; margin-top: 10px; font-family: var(--d-f-mono); font-size: 11px; color: var(--pixel-text-secondary); padding: 4px 9px; border: 1px solid var(--pixel-border-2); border-radius: 3px; background: var(--pixel-bg-secondary); }
.keychip .lock { color: var(--pixel-primary); }
.keychip .k { color: var(--pixel-text); }
.keychip .enc { color: var(--pixel-faint); }

.status { display: flex; flex-direction: column; align-items: flex-end; gap: 8px; }
.badge { display: inline-flex; align-items: center; gap: 6px; font-family: var(--d-f-mono); font-size: 11px; padding: 4px 10px; border-radius: 999px; border: 1px solid var(--pixel-border); }
.badge .dot { width: 7px; height: 7px; border-radius: 50%; background: currentColor; box-shadow: 0 0 8px currentColor; }
.badge.success { color: var(--pixel-success); border-color: rgba(52, 211, 153, .4); background: rgba(52, 211, 153, .1); }
.badge.idle { color: var(--pixel-faint); border-color: var(--pixel-border); background: var(--pixel-bg-secondary); }
.lat { font-family: var(--d-f-mono); font-size: 11px; color: var(--pixel-faint); }

.hud-card.off .tower > i.on { background: transparent; box-shadow: none; }
.hud-card.off .model { background: none; color: var(--pixel-faint); -webkit-text-fill-color: var(--pixel-faint); }
.hud-card.off .prov::before { background: var(--pixel-faint); box-shadow: none; }

@media (max-width: 640px) {
  .link-hud { grid-template-columns: 1fr; gap: 14px; padding: 18px; }
  .signal { flex-direction: row; }
  .status { align-items: flex-start; flex-direction: row; }
}

/* ===== 生效范围 / 安全 ===== */
.scope-list { display: flex; flex-direction: column; gap: 10px; }
.scope-li { display: flex; align-items: center; gap: 10px; font-size: 13px; }
.scope-li .ck { width: 20px; height: 20px; border-radius: 5px; background: rgba(52, 211, 153, .14); color: var(--pixel-success); display: grid; place-items: center; flex: none; font-size: 11px; }
.scope-li.off .ck { background: var(--pixel-bg-secondary); color: var(--pixel-faint); }
.scope-li .who { flex: 1; }
.scope-li .mdl { font-family: var(--d-f-mono); font-size: 11px; color: var(--pixel-faint); }
.hint-block { font-family: var(--d-f-mono); font-size: 11px; color: var(--pixel-text-secondary); padding-top: 4px; }
.safe-text { font-size: 13px; line-height: 1.6; color: var(--pixel-text); }
.safe-text code { font-family: var(--d-f-mono); font-size: 12px; color: var(--pixel-primary); padding: 1px 5px; background: var(--pixel-bg-secondary); border-radius: 3px; }
.badge-row { display: flex; gap: 8px; flex-wrap: wrap; }
.mini-badge { display: inline-flex; align-items: center; gap: 6px; font-family: var(--d-f-mono); font-size: 11px; padding: 3px 9px; border: 1px solid var(--pixel-border); border-radius: 999px; color: var(--pixel-text-secondary); }
.mini-badge.ok { color: var(--pixel-success); border-color: rgba(52, 211, 153, .4); background: rgba(52, 211, 153, .08); }
.mini-badge .dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
</style>
