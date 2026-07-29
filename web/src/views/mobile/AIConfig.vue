<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { useNotifyStore } from '../../stores/notification'
import { getAiConfig, updateAiConfig, testAiConfig } from '../../api/userConfig'
import type { AiConfig, AiConfigUpdate, AiConfigTestResult } from '../../api/userConfig'

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
  cfg.value?.provider === 'anthropic' ? 'Anthropic · GLM' : (cfg.value?.provider || '—'),
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
  <div class="m-screen">
    <div class="m-head">
      <span class="m-head__back" @click="router.push('/settings')">◂</span>
      <span class="m-head__title">AI 模型配置</span>
      <router-link v-if="isAdmin" to="/hero" class="m-head__sub" style="color: var(--pixel-warning); text-decoration: none;">管理 →</router-link>
    </div>

    <div v-if="loading" class="m-loading">加载中…</div>
    <div v-else-if="loadError" class="m-card"><div style="color: var(--pixel-accent); font-size: 13px;">{{ loadError }}</div></div>

    <template v-else>
      <!-- 签名：模型链路 HUD 紧凑版 -->
      <div class="hud-card" :class="{ off: !configured }">
        <span class="tick tl"></span><span class="tick tr"></span>
        <span class="tick bl"></span><span class="tick br"></span>
        <div class="link-hud">
          <div class="signal">
            <div class="tower" :class="{ live: configured }">
              <i v-for="(on, idx) in signalBars" :key="idx" :class="{ on }"></i>
            </div>
          </div>
          <div class="core">
            <span class="prov">{{ hudProvider }}</span>
            <div class="model grad">{{ hudModel }}</div>
            <span class="keychip"><span class="lock">▣</span> {{ hudKey }}<span v-if="hasKey" class="enc"> · 已加密</span></span>
          </div>
          <div class="status">
            <span class="m-tag" :class="configured ? 'm-tag--ok' : ''">{{ configured ? '已启用' : '未配置' }}</span>
          </div>
        </div>
      </div>

      <!-- 连接参数 -->
      <div class="m-section-title">连接参数</div>
      <div class="m-card">
        <div class="m-field">
          <span class="m-field__label">服务商</span>
          <select v-model="form.provider" class="m-input">
            <option value="anthropic">Anthropic 兼容（GLM / Claude）</option>
            <option value="openai" disabled>OpenAI 兼容（敬请期待）</option>
          </select>
        </div>
        <div class="m-field">
          <span class="m-field__label">模型 Model</span>
          <input v-model="form.model" class="m-input" placeholder="如 glm-5.2" />
        </div>
        <div class="m-field">
          <span class="m-field__label">接口地址</span>
          <input v-model="form.base_url" class="m-input" placeholder="https://…" />
        </div>
        <div class="m-field" style="margin-bottom: 0;">
          <span class="m-field__label">
            API 密钥
            <span v-if="hasKey" style="color: var(--pixel-success);">· 已保存</span>
          </span>
          <div class="key-wrap">
            <input
              v-model="form.api_key"
              :type="showKey ? 'text' : 'password'"
              class="m-input key-input"
              placeholder="留空则保持原有密钥不变"
            />
            <button type="button" class="key-eye" @click="showKey = !showKey">{{ showKey ? '◉' : '⬤' }}</button>
          </div>
        </div>
      </div>

      <div class="m-grid-2" style="margin-top: 12px;">
        <div class="m-card" style="margin: 0;">
          <div class="m-field" style="margin: 0;">
            <span class="m-field__label">最大轮数</span>
            <input v-model.number="form.max_turns" type="number" min="1" max="50" class="m-input" />
          </div>
        </div>
        <div class="m-card" style="margin: 0;">
          <div class="m-field" style="margin: 0;">
            <span class="m-field__label">单次预算 $</span>
            <input v-model.number="form.max_budget_usd" type="number" step="0.1" min="0" class="m-input" />
          </div>
        </div>
      </div>

      <div class="m-card" style="margin-top: 12px;">
        <div class="m-field" style="margin: 0;">
          <span class="m-field__label">附加系统提示</span>
          <textarea v-model="form.system_prompt_extra" class="m-textarea" placeholder="可选：自定义人设 / 口吻 / 输出约束"></textarea>
        </div>
      </div>

      <div class="m-card m-between" style="margin-top: 12px;">
        <div>
          <div style="font-weight: 600; font-size: 14px;">启用此配置</div>
          <div class="m-hint">关闭后 AI 功能不可用</div>
        </div>
        <span class="m-toggle" :class="{ 'm-toggle--on': form.enabled }" @click="form.enabled = !form.enabled">
          <span class="m-toggle__track"></span><span class="m-toggle__knob"></span>
        </span>
      </div>

      <button class="m-btn m-btn--block" style="margin-top: 12px;" :disabled="testing" @click="handleTest">
        {{ testing ? '测试中…' : '⚡ 测试连接' }}
      </button>

      <div v-if="testResult" class="test-result" :class="testResult.ok ? 'ok' : 'fail'" style="margin-top: 10px;">
        <div class="tr-head">{{ testResult.ok ? '✓ 连接成功' : '✕ 连接失败' }}</div>
        <div class="tr-meta">
          {{ testResult.model || form.model || '—' }}
          <span v-if="testResult.latency_ms !== null"> · {{ testResult.latency_ms }}ms</span>
          · {{ testResult.message }}
        </div>
      </div>

      <!-- 生效范围 -->
      <div class="m-section-title">生效范围</div>
      <div class="m-card">
        <div class="scope-li" :class="{ off: !configured }">
          <span class="ck">✓</span>
          <span class="who">AI 对话<span class="mdl">· {{ form.model || '—' }}</span></span>
        </div>
        <div class="scope-li" :class="{ off: !configured }">
          <span class="ck">✓</span>
          <span class="who">简历 AI 编辑<span class="mdl">· {{ form.model || '—' }}</span></span>
        </div>
        <div class="scope-li" :class="{ off: !configured }" style="border: 0; padding-bottom: 0;">
          <span class="ck">✓</span>
          <span class="who">每日资讯 intel<span class="mdl">· {{ form.model || '—' }}</span></span>
        </div>
      </div>

      <!-- 安全 -->
      <div class="m-section-title">安全</div>
      <div class="m-card">
        <p class="safe-text">密钥使用 <code>AES / Fernet</code> 加密入库，任何接口都不回显明文，仅返回掩码；仅本人可改。</p>
        <div class="m-flex m-wrap m-gap" style="margin-top: 10px;">
          <span class="m-tag m-tag--ok">加密存储</span>
          <span class="m-tag">掩码回显</span>
          <span class="m-tag">仅本人可改</span>
        </div>
      </div>

      <button class="m-btn m-btn--primary m-btn--block" style="margin-top: 14px;" :disabled="saving" @click="handleSave">
        {{ saving ? '保存中…' : '✓ 保存配置' }}
      </button>
    </template>
  </div>
</template>

<style scoped>
/* ═══════ 签名：模型链路 HUD（紧凑移动版）═══════ */
.hud-card { position: relative; border: 1px solid var(--pixel-border-2, rgba(255,255,255,.16)); border-radius: 6px; overflow: hidden; background:
  repeating-linear-gradient(135deg, rgba(255,255,255,.018) 0 2px, transparent 2px 5px),
  var(--pixel-card-bg); backdrop-filter: blur(10px); box-shadow: var(--d-shadow-sm); }
.hud-card::before { content: ""; position: absolute; inset: 0; border-radius: 6px; padding: 1px; background: var(--d-grad); -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0); -webkit-mask-composite: xor; mask-composite: exclude; opacity: .35; pointer-events: none; }
[data-theme="light"] .hud-card { background:
  repeating-linear-gradient(135deg, rgba(17,20,40,.022) 0 2px, transparent 2px 5px),
  var(--pixel-card-bg); }
.tick { position: absolute; width: 8px; height: 8px; border: 2px solid var(--pixel-primary); }
.tick.tl { top: 5px; left: 5px; border-right: 0; border-bottom: 0; }
.tick.tr { top: 5px; right: 5px; border-left: 0; border-bottom: 0; }
.tick.bl { bottom: 5px; left: 5px; border-right: 0; border-top: 0; }
.tick.br { bottom: 5px; right: 5px; border-left: 0; border-top: 0; }

.link-hud { display: grid; grid-template-columns: auto 1fr auto; gap: 14px; align-items: center; padding: 14px 16px; }
.signal { display: flex; align-items: center; }
.tower { display: flex; align-items: flex-end; gap: 3px; height: 44px; }
.tower > i { width: 6px; border-radius: 1px; background: var(--pixel-bg-secondary); border: 1px solid var(--pixel-border); transition: background .3s, box-shadow .3s; }
.tower > i:nth-child(1) { height: 30%; }
.tower > i:nth-child(2) { height: 48%; }
.tower > i:nth-child(3) { height: 68%; }
.tower > i:nth-child(4) { height: 88%; }
.tower > i:nth-child(5) { height: 100%; }
.tower > i.on { background: var(--pixel-primary); border-color: transparent; box-shadow: 0 0 9px rgba(34, 211, 238, .5); }
.tower.live > i.on { animation: mob-hud-pulse 1.6s ease-in-out infinite; }
.tower.live > i.on:nth-child(2) { animation-delay: .15s; }
.tower.live > i.on:nth-child(3) { animation-delay: .3s; }
.tower.live > i.on:nth-child(4) { animation-delay: .45s; }
@keyframes mob-hud-pulse { 0%, 100% { opacity: .55; } 50% { opacity: 1; } }

.core { min-width: 0; }
.prov { display: inline-flex; align-items: center; gap: 5px; font-family: var(--font-pixel-num); font-size: 10px; letter-spacing: .06em; color: var(--pixel-primary); text-transform: uppercase; }
.prov::before { content: ""; width: 5px; height: 5px; background: var(--pixel-primary); box-shadow: 0 0 8px var(--pixel-primary); }
.model { font-family: var(--font-pixel-en); font-weight: 700; font-size: 22px; line-height: 1.1; margin: 4px 0; word-break: break-all; }
.model.grad { background: var(--d-grad); -webkit-background-clip: text; background-clip: text; color: transparent; }
.keychip { display: inline-flex; align-items: center; gap: 5px; font-family: var(--font-pixel-num); font-size: 10px; color: var(--pixel-text-secondary); padding: 3px 7px; border: 1px solid var(--pixel-border-2, rgba(255,255,255,.16)); border-radius: 3px; background: var(--pixel-bg-secondary); }
.keychip .lock { color: var(--pixel-primary); }
.keychip .enc { color: var(--pixel-text-secondary); }
.status { display: flex; align-items: center; }
.hud-card.off .tower > i.on { background: transparent; box-shadow: none; }
.hud-card.off .model { background: none; color: var(--pixel-text-secondary); -webkit-text-fill-color: var(--pixel-text-secondary); }
.hud-card.off .prov::before { background: var(--pixel-text-secondary); box-shadow: none; }

.key-wrap { position: relative; }
.key-wrap .key-input { padding-right: 38px; font-family: var(--font-pixel-num); letter-spacing: .08em; }
.key-eye { position: absolute; right: 6px; top: 50%; transform: translateY(-50%); width: 30px; height: 30px; border: 0; background: transparent; color: var(--pixel-text-secondary); cursor: pointer; border-radius: 6px; font-size: 14px; }

.test-result { padding: 10px 12px; border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); background: var(--pixel-bg-secondary); }
.test-result.ok { border-color: rgba(52, 211, 153, .4); background: rgba(52, 211, 153, .07); }
.test-result.fail { border-color: rgba(251, 113, 133, .4); background: rgba(251, 113, 133, .07); }
.test-result .tr-head { font-size: 13px; font-weight: 600; }
.test-result.ok .tr-head { color: var(--pixel-success); }
.test-result.fail .tr-head { color: var(--pixel-accent); }
.test-result .tr-meta { font-family: var(--font-pixel-num); font-size: 11px; color: var(--pixel-text-secondary); margin-top: 3px; }

.scope-li { display: flex; align-items: center; gap: 10px; padding: 8px 0; font-size: 13px; border-bottom: 1px solid var(--pixel-border); }
.scope-li .ck { width: 20px; height: 20px; border-radius: 5px; background: rgba(52, 211, 153, .14); color: var(--pixel-success); display: grid; place-items: center; flex: none; font-size: 11px; }
.scope-li.off .ck { background: var(--pixel-bg-secondary); color: var(--pixel-text-secondary); }
.scope-li .who { flex: 1; }
.scope-li .mdl { font-family: var(--font-pixel-num); font-size: 11px; color: var(--pixel-text-secondary); }

.safe-text { font-size: 13px; line-height: 1.6; color: var(--pixel-text); margin: 0; }
.safe-text code { font-family: var(--font-pixel-num); font-size: 12px; color: var(--pixel-primary); padding: 1px 5px; background: var(--pixel-bg-secondary); border-radius: 3px; }
</style>
