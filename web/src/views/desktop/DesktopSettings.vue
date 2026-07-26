<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { isTauri, getOrigin, clearServerOrigin } from '../../utils/platform'
import { setupApiClient } from '../../api/client'
import {
  isAutostartEnabled,
  setAutostartEnabled,
  getStoredShortcut,
  setStoredShortcut,
  reregisterShortcut,
  desktopPlatform,
} from '../../utils/native'

const router = useRouter()

const serverOrigin = ref(getOrigin() || '未配置')
const autostart = ref(false)
const platform = ref('web')
const shortcut = ref('')
const capturing = ref(false)
const saveMsg = ref('')

let captureHandler: ((e: KeyboardEvent) => void) | null = null

onMounted(async () => {
  if (!isTauri()) return
  autostart.value = await isAutostartEnabled()
  shortcut.value = await getStoredShortcut()
  platform.value = await desktopPlatform()
})

onBeforeUnmount(() => stopCapture())

async function toggleAutostart() {
  autostart.value = !autostart.value
  await setAutostartEnabled(autostart.value)
  flash(autostart.value ? '已开启开机自启' : '已关闭开机自启')
}

function startCapture() {
  capturing.value = true
  captureHandler = (e: KeyboardEvent) => {
    e.preventDefault()
    if (e.key === 'Escape') { stopCapture(); return }
    const parts: string[] = []
    if (e.metaKey || e.ctrlKey) parts.push('CmdOrCtrl')
    if (e.altKey) parts.push('Alt')
    if (e.shiftKey) parts.push('Shift')
    const k = e.key.length === 1 ? e.key.toUpperCase() : e.key
    if (!['Meta', 'Control', 'Alt', 'Shift'].includes(e.key)) parts.push(k)
    if (parts.length <= 1) return // 至少要一个修饰键
    shortcut.value = parts.join('+')
    stopCapture()
    saveShortcut()
  }
  window.addEventListener('keydown', captureHandler)
}

function stopCapture() {
  capturing.value = false
  if (captureHandler) {
    window.removeEventListener('keydown', captureHandler)
    captureHandler = null
  }
}

async function saveShortcut() {
  await setStoredShortcut(shortcut.value)
  const ok = await reregisterShortcut(shortcut.value)
  flash(ok ? `快捷键已设为 ${shortcut.value}` : '快捷键注册失败（可能被占用）')
}

async function reconfigureServer() {
  await clearServerOrigin()
  setupApiClient()
  router.push('/setup')
}

function flash(msg: string) {
  saveMsg.value = msg
  setTimeout(() => (saveMsg.value = ''), 2000)
}
</script>

<template>
  <div class="ds-page">
    <div class="ds-card pixel-border">
      <h2 class="ds-h2">桌面设置 · SYSTEM TUNE</h2>
      <p class="ds-desc">仅桌面端可见。服务器地址、全局快捷键、开机自启。</p>

      <section class="ds-row">
        <div class="ds-row-main">
          <div class="ds-title">接驳服务器</div>
          <div class="ds-sub mono">{{ serverOrigin }}</div>
        </div>
        <button class="ds-btn" @click="reconfigureServer">重新配置</button>
      </section>

      <section class="ds-row">
        <div class="ds-row-main">
          <div class="ds-title">全局唤起快捷键</div>
          <div class="ds-sub">任意界面唤出/隐藏窗口</div>
        </div>
        <button class="ds-kbd" :class="{ capturing }" @click="startCapture">
          <template v-if="capturing">按下组合键…</template>
          <template v-else>{{ shortcut || '未设置' }}</template>
        </button>
      </section>

      <section class="ds-row">
        <div class="ds-row-main">
          <div class="ds-title">开机自启动</div>
          <div class="ds-sub">登录系统时启动并最小化到托盘</div>
        </div>
        <button class="ds-switch" :class="{ on: autostart }" @click="toggleAutostart">
          <span class="knob"></span>
        </button>
      </section>

      <section class="ds-row">
        <div class="ds-row-main">
          <div class="ds-title">关于</div>
          <div class="ds-sub mono">PixelPack Desktop · Tauri 2 · {{ platform }}</div>
        </div>
      </section>

      <div v-if="saveMsg" class="ds-toast">{{ saveMsg }}</div>
    </div>
  </div>
</template>

<style scoped>
.ds-page { padding: 24px; }
.ds-card { background: var(--pixel-card-bg); padding: 20px 22px; max-width: 720px; }
.ds-h2 { font-family: var(--font-pixel-en), monospace; font-size: 12px; letter-spacing: 1px; color: var(--pixel-text); margin: 0 0 4px; }
.ds-desc { color: var(--pixel-text-secondary); font-size: 12px; margin: 0 0 16px; }
.ds-row { display: flex; align-items: center; justify-content: space-between; gap: 16px; padding: 12px 14px; background: var(--pixel-bg-secondary); border: 2px solid var(--pixel-border); margin-bottom: 10px; }
.ds-row:last-of-type { margin-bottom: 0; }
.ds-title { font-weight: 600; }
.ds-sub { color: var(--pixel-text-secondary); font-size: 12px; margin-top: 2px; }
.mono { font-family: var(--font-pixel-num), monospace; }
.ds-btn { padding: 7px 12px; background: var(--pixel-bg); color: var(--pixel-text); border: 3px solid var(--pixel-border); font-family: var(--font-pixel); font-size: 12px; cursor: pointer; box-shadow: 2px 2px 0 var(--pixel-shadow); }
.ds-btn:hover { border-color: var(--pixel-primary); color: var(--pixel-info); }
.ds-btn:active { transform: translate(2px, 2px); box-shadow: none; }
.ds-kbd { min-width: 150px; padding: 8px 12px; background: var(--pixel-bg); border: 3px solid var(--pixel-border); font-family: var(--font-pixel-num), monospace; font-size: 13px; color: var(--pixel-info); cursor: pointer; }
.ds-kbd:hover { border-color: var(--pixel-primary); }
.ds-kbd.capturing { border-color: var(--pixel-warning); color: var(--pixel-warning); animation: blink 0.8s step-end infinite; }
@keyframes blink { 0%,100%{opacity:1;} 50%{opacity:0.4;} }
.ds-switch { position: relative; width: 48px; height: 22px; background: var(--pixel-bg); border: 3px solid var(--pixel-border); cursor: pointer; padding: 0; }
.ds-switch .knob { position: absolute; top: 1px; left: 1px; width: 12px; height: 12px; background: var(--pixel-border); transition: left 0.12s steps(2), background 0.12s steps(2); }
.ds-switch.on { background: var(--pixel-success); border-color: var(--pixel-success); }
.ds-switch.on .knob { left: 27px; background: var(--pixel-bg); }
.ds-toast { margin-top: 14px; padding: 8px 12px; background: var(--pixel-bg); border: 2px solid var(--pixel-success); color: var(--pixel-success); font-size: 12px; font-family: var(--font-pixel-num), monospace; }
</style>
