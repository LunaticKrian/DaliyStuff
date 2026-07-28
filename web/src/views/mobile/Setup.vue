<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { isTauri, getOrigin, setServerOrigin } from '../../utils/platform'
import { setupApiClient } from '../../api/client'

const router = useRouter()
const origin = ref('https://pixelpack.airise.site')
const testing = ref(false)
const result = ref<'idle' | 'ok' | 'fail'>('idle')
const log = ref<{ text: string; cls?: string }[]>([
  { text: '> GUILD DECK v1.0', cls: 'dim' },
  { text: '> 等待公会服务器地址…', cls: 'dim' },
])
const barsOn = ref([false, false, false, false])

onMounted(() => {
  if (!isTauri()) {
    // Web 端误入：直接回首页（Web 走同源，无需接驳）
    router.replace('/')
    return
  }
  const last = getOrigin()
  if (last) origin.value = last
})

function pushLine(text: string, cls?: string) {
  log.value.push({ text, cls })
}
const wait = (ms: number) => new Promise((r) => setTimeout(r, ms))

async function testConnectivity(o: string): Promise<boolean> {
  try {
    const res = await fetch(`${o}/api/auth/me`, { method: 'GET' })
    return res.status === 401 || res.ok
  } catch {
    return false
  }
}

async function onTest() {
  if (testing.value) return
  const o = origin.value.trim().replace(/\/+$/, '')
  if (!/^https?:\/\//.test(o)) {
    pushLine('> ✗ 地址须以 http:// 或 https:// 开头', 'warn')
    return
  }
  testing.value = true
  result.value = 'idle'
  barsOn.value = [false, false, false, false]
  log.value = log.value.slice(0, 2)
  pushLine(`> 解析 ${o.replace(/^https?:\/\//, '')} …`, 'dim')
  await wait(250); barsOn.value[0] = true
  pushLine('> TLS 握手 …', 'dim')
  await wait(400); barsOn.value[1] = true
  pushLine('> 探测 /api …', 'dim')
  const ok = await testConnectivity(o)
  await wait(200); barsOn.value[2] = true; barsOn.value[3] = true
  if (ok) {
    pushLine('> ✓ 接驳成功 · LINKED', 'ok')
    await setServerOrigin(o)
    setupApiClient()
    result.value = 'ok'
    testing.value = false
    await wait(400)
    router.push('/login')
  } else {
    pushLine('> ✗ 接驳失败：无法连接或 CORS 被拒', 'warn')
    result.value = 'fail'
    testing.value = false
  }
}
</script>

<template>
  <div class="m-screen" style="padding-top: 40px;">
    <div class="m-center" style="margin-bottom: 24px;">
      <div class="m-sb__mark" style="width: 26px; height: 26px; margin: 0 auto 14px; box-shadow: 9px 0 0 var(--pixel-warning), 0 9px 0 var(--pixel-success);" />
      <div style="font-weight: 700; letter-spacing: 2px; color: var(--pixel-info);">GUILD DECK</div>
      <div class="m-hint">接驳公会服务器以激活掌机</div>
    </div>

    <div class="m-card m-center" style="padding: 18px;">
      <div class="signal">
        <span v-for="(on, i) in barsOn" :key="i" class="bar" :class="{ on, fail: result === 'fail' }" />
      </div>
      <div class="boot-log">
        <div v-for="(l, i) in log" :key="i" :class="l.cls">{{ l.text }}</div>
        <div v-if="testing" class="caret">▮</div>
      </div>
    </div>

    <div class="m-card" style="margin-top: 14px;">
      <div class="m-field">
        <span class="m-field__label">SERVER ENDPOINT</span>
        <input v-model="origin" class="m-input" placeholder="https://your-host" :disabled="testing" @keyup.enter="onTest" />
      </div>
      <button class="m-btn m-btn--primary m-btn--block" :disabled="testing" @click="onTest">
        {{ testing ? '接驳中…' : '▸ 建立链路' }}
      </button>
      <div v-if="result === 'fail'" class="m-hint m-center" style="color: var(--pixel-warning); margin-top: 10px;">✗ 请检查地址与网络</div>
    </div>
  </div>
</template>

<style scoped>
/* 令牌兜底：脱离 .m-deck 时也保留新视觉语言 */
.m-screen {
  --pixel-bg: #0b0d14;
  --pixel-bg-secondary: #14171f;
  --pixel-card-bg: rgba(255, 255, 255, 0.045);
  --pixel-border: rgba(255, 255, 255, 0.09);
  --pixel-accent: #fb7185;
  --pixel-warning: #fbbf24;
  --pixel-success: #34d399;
  --pixel-info: #38bdf8;
  --pixel-text: #f4f6fb;
  --pixel-text-secondary: #9aa3b2;
  --d-grad: linear-gradient(135deg, #818cf8 0%, #7c5cff 40%, #22d3ee 100%);
  --d-radius: 14px;
  --d-radius-sm: 10px;
  --d-shadow-sm: 0 4px 14px -8px rgba(0, 0, 0, .6);
}

.signal { display: flex; align-items: flex-end; justify-content: center; gap: 6px; height: 52px; margin-bottom: 14px; }
.signal .bar {
  width: 12px;
  background: var(--pixel-border);
  border-radius: 3px;
  transition: background .2s ease, box-shadow .2s ease;
}
.signal .bar:nth-child(1) { height: 13px; }
.signal .bar:nth-child(2) { height: 25px; }
.signal .bar:nth-child(3) { height: 37px; }
.signal .bar:nth-child(4) { height: 49px; }
.signal .bar.on {
  background: var(--pixel-success);
  box-shadow: 0 0 10px rgba(52, 211, 153, .45);
}
.signal .bar.fail {
  background: var(--pixel-accent);
  box-shadow: 0 0 10px rgba(251, 113, 133, .4);
}

.boot-log {
  width: 100%;
  padding: 12px 14px;
  background: var(--pixel-bg);
  border: 1px solid var(--pixel-border);
  border-radius: 10px;
  font-family: var(--font-pixel-num);
  font-size: 11px;
  line-height: 1.7;
  color: var(--pixel-success);
  min-height: 96px;
  text-align: left;
  box-shadow: var(--d-shadow-sm);
}
.boot-log .dim { color: var(--pixel-text-secondary); }
.boot-log .warn { color: var(--pixel-warning); }

.caret { color: var(--pixel-success); animation: m-blink 0.8s steps(2) infinite; }
</style>
