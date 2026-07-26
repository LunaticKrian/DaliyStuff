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
  { text: '> PixelPack Terminal v1.0', cls: 'dim' },
  { text: '> 等待公会大厅地址…', cls: 'dim' },
])
const barsOn = ref([false, false, false, false])

onMounted(() => {
  // Web 端误入：直接回首页
  if (!isTauri()) {
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
    // 探测 API 活性：401 也算「可达」（服务在线、路由存在）
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
    pushLine('> ✗ 地址必须以 http:// 或 https:// 开头', 'warn')
    return
  }
  testing.value = true
  result.value = 'idle'
  barsOn.value = [false, false, false, false]
  log.value = log.value.slice(0, 2)
  pushLine(`> 解析地址 ${o.replace(/^https?:\/\//, '')} …`, 'dim')
  await wait(250)
  barsOn.value[0] = true
  pushLine('> TLS 握手 …', 'dim')
  await wait(450)
  barsOn.value[1] = true
  pushLine('> 探测 /api …', 'dim')

  const ok = await testConnectivity(o)
  await wait(200)
  barsOn.value[2] = true
  barsOn.value[3] = true

  if (ok) {
    pushLine('> ✓ 接驳成功 · LINKED', 'ok')
    await setServerOrigin(o)
    setupApiClient() // 重建 API 客户端，baseURL 指向新服务器
    result.value = 'ok'
    testing.value = false
    await wait(400)
    // 已登录则进首页，否则进登录
    router.push('/login')
  } else {
    pushLine('> ✗ 接驳失败：无法连接或 CORS 被拒', 'warn')
    result.value = 'fail'
    testing.value = false
  }
}
</script>

<template>
  <div class="setup-shell">
    <div class="setup-card pixel-border">
      <!-- 左：信号塔 + 日志 -->
      <div class="setup-left">
        <div class="title">TERMINAL LINK</div>
        <div class="sub">接驳公会大厅</div>

        <div class="signal">
          <span v-for="(on, i) in barsOn" :key="i" class="bar" :class="{ on, fail: result === 'fail' }"></span>
        </div>

        <div class="boot-log">
          <div v-for="(l, i) in log" :key="i" :class="l.cls">{{ l.text }}</div>
          <div v-if="testing" class="caret">▮</div>
        </div>
      </div>

      <!-- 右：表单 -->
      <div class="setup-right">
        <div class="stage"><span class="cur">01 · 指定服务器</span><i>▸</i><span class="todo">02 · 登录冒险者</span></div>

        <label class="lbl">◈ 公会大厅地址 (SERVER ORIGIN)</label>
        <input v-model="origin" class="inp" placeholder="https://your-host" :disabled="testing" @keyup.enter="onTest" />
        <div class="hint">仅接受 https:// 生产地址，或 http://localhost 本地调试</div>

        <button class="btn-primary" :disabled="testing" @click="onTest">
          {{ testing ? '接驳中…' : '▶ 测试接驳' }}
        </button>

        <div v-if="result === 'ok'" class="result ok">✓ 已接驳，即将进入登录…</div>
        <div v-else-if="result === 'fail'" class="result warn">✗ 接驳失败，请检查地址与网络</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.setup-shell {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  background:
    radial-gradient(ellipse at 30% 0%, rgba(65, 166, 246, 0.1), transparent 55%),
    var(--pixel-bg);
  font-family: var(--font-pixel);
}
.setup-card {
  display: grid;
  grid-template-columns: 300px 1fr;
  width: 720px;
  max-width: 100%;
  background: var(--pixel-bg-secondary);
  box-shadow: 3px 3px 0 var(--pixel-shadow);
}
.setup-left {
  padding: 26px 22px;
  border-right: 3px solid var(--pixel-border);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  background: linear-gradient(180deg, rgba(65, 166, 246, 0.06), transparent 60%), var(--pixel-bg);
}
.title { font-family: var(--font-pixel-en), monospace; font-size: 12px; letter-spacing: 1px; color: var(--pixel-info); }
.sub { font-size: 12px; color: var(--pixel-text-secondary); margin-top: -10px; }
.signal { display: flex; align-items: flex-end; gap: 5px; height: 52px; }
.signal .bar { width: 12px; background: var(--pixel-border); transition: background 0.12s steps(2); }
.signal .bar:nth-child(1) { height: 13px; }
.signal .bar:nth-child(2) { height: 25px; }
.signal .bar:nth-child(3) { height: 37px; }
.signal .bar:nth-child(4) { height: 49px; }
.signal .bar.on { background: var(--pixel-success); box-shadow: 0 0 6px rgba(56, 183, 100, 0.5); }
.signal .bar.fail { background: var(--pixel-accent); box-shadow: 0 0 6px rgba(177, 62, 83, 0.5); }

.boot-log {
  width: 100%;
  flex: 1;
  padding: 10px 12px;
  background: var(--pixel-bg);
  border: 2px solid var(--pixel-border);
  font-family: var(--font-pixel-num), monospace;
  font-size: 11px;
  line-height: 1.7;
  color: var(--pixel-success);
  min-height: 110px;
}
.boot-log .dim { color: var(--pixel-text-secondary); }
.boot-log .warn { color: var(--pixel-warning); }
.boot-log .ok { color: var(--pixel-success); font-weight: bold; }
.caret { color: var(--pixel-success); animation: blink 0.8s step-end infinite; }
@keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }

.setup-right { padding: 28px 26px; display: flex; flex-direction: column; gap: 10px; }
.stage { display: flex; gap: 8px; align-items: center; font-family: var(--font-pixel-en), monospace; font-size: 8px; letter-spacing: 1px; color: var(--pixel-text-secondary); margin-bottom: 8px; }
.stage .cur { color: var(--pixel-info); border: 2px solid var(--pixel-primary); padding: 4px 8px; box-shadow: 0 0 6px rgba(65, 166, 246, 0.4); }
.stage .todo { border: 2px solid var(--pixel-border); padding: 4px 8px; }
.stage i { color: var(--pixel-border); }
.lbl { font-family: var(--font-pixel-en), monospace; font-size: 8px; letter-spacing: 1px; color: var(--pixel-info); margin-top: 4px; }
.inp {
  padding: 10px 12px;
  background: var(--pixel-bg);
  color: var(--pixel-text);
  border: 3px solid var(--pixel-border);
  font-family: var(--font-pixel-num), monospace;
  font-size: 14px;
  outline: none;
}
.inp:focus { border-color: var(--pixel-primary); box-shadow: 0 0 0 1px var(--pixel-primary), 0 0 10px rgba(65, 166, 246, 0.3); }
.hint { font-size: 11px; color: var(--pixel-text-secondary); font-family: var(--font-pixel-num), monospace; margin-bottom: 8px; }
.btn-primary {
  padding: 10px 16px;
  background: var(--pixel-primary);
  color: var(--pixel-bg);
  border: 3px solid var(--pixel-primary);
  box-shadow: 0 0 8px rgba(65, 166, 246, 0.35), 3px 3px 0 var(--pixel-shadow);
  font-family: var(--font-pixel);
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
}
.btn-primary:hover { filter: brightness(1.1); }
.btn-primary:active { transform: translate(2px, 2px); box-shadow: 1px 1px 0 var(--pixel-shadow); }
.btn-primary[disabled] { opacity: 0.5; cursor: not-allowed; }
.result { font-size: 12px; font-family: var(--font-pixel-num), monospace; margin-top: 4px; }
.result.ok { color: var(--pixel-success); }
.result.warn { color: var(--pixel-warning); }
</style>
