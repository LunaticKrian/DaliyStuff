<script setup lang="ts">
import { ref } from 'vue'
import { useAppLock } from '../../composables/useAppLock'
import { useNotifyStore } from '../../stores/notification'
import { isTauri } from '../../utils/platform'

const lock = useAppLock()
const notify = useNotifyStore()

const pin = ref('')
const error = ref(false)

function tap(d: string) {
  if (pin.value.length >= 6) return
  pin.value += d
  error.value = false
  if (pin.value.length >= 4) submit()
}
function del() {
  pin.value = pin.value.slice(0, -1)
  error.value = false
}
async function submit() {
  const ok = await lock.unlock(pin.value)
  if (!ok) {
    error.value = true
    notify.error('密钥错误')
    setTimeout(() => { pin.value = '' }, 300)
  } else {
    pin.value = ''
  }
}

async function biometricAuth() {
  if (!isTauri()) {
    notify.warning('生物识别需在 App 内可用')
    return
  }
  try {
    const { invoke } = await import('@tauri-apps/api/core')
    await invoke('authenticate_biometric')
    lock.unlockDirect()
  } catch {
    notify.error('生物识别失败或已取消')
  }
}
</script>

<template>
  <div class="lock-overlay">
    <div class="m-sb__mark" style="width: 24px; height: 24px; box-shadow: 9px 0 0 var(--pixel-warning), 0 9px 0 var(--pixel-success);" />
    <div style="font-weight: 700; letter-spacing: 2px; margin-top: 16px;">GUILD LOCK</div>
    <div class="m-hint">输入密钥解锁掌机</div>

    <div class="dots" :class="{ err: error }">
      <span v-for="i in 4" :key="i" :class="{ filled: pin.length >= i }" />
    </div>

    <div class="pad">
      <button v-for="n in [1,2,3,4,5,6,7,8,9]" :key="n" class="key" @click="tap(String(n))">{{ n }}</button>
      <button v-if="lock.biometric.value && isTauri()" class="key fn" @click="biometricAuth">✦</button>
      <button v-else class="key fn" disabled></button>
      <button class="key" @click="tap('0')">0</button>
      <button class="key fn" @click="del">⌫</button>
    </div>
  </div>
</template>

<style scoped>
/* 令牌兜底：脱离 .m-deck 时也保留新视觉语言 */
.lock-overlay {
  --pixel-bg: #0b0d14;
  --pixel-bg-secondary: #14171f;
  --pixel-card-bg: rgba(255, 255, 255, 0.045);
  --pixel-border: rgba(255, 255, 255, 0.09);
  --pixel-accent: #fb7185;
  --pixel-info: #38bdf8;
  --pixel-text: #f4f6fb;
  --pixel-text-secondary: #9aa3b2;
  --d-grad: linear-gradient(135deg, #818cf8 0%, #7c5cff 40%, #22d3ee 100%);
  --d-radius: 14px;
  --d-radius-sm: 10px;
  --d-shadow-sm: 0 4px 14px -8px rgba(0, 0, 0, .6);

  position: absolute; inset: 0; z-index: 500;
  background: radial-gradient(120% 80% at 50% 0%, rgba(99, 102, 241, .10), transparent 60%), var(--pixel-bg);
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 0 40px calc(env(safe-area-inset-bottom, 0px) + 40px);
}

.dots { display: flex; gap: 16px; margin: 28px 0 8px; }
.dots span {
  width: 16px; height: 16px;
  border: 1px solid var(--pixel-border);
  border-radius: 50%;
  background: transparent;
  transition: background .18s ease, border-color .18s ease;
}
.dots span.filled { background: var(--d-grad); border-color: transparent; }
.dots.err span.filled { background: var(--pixel-accent); border-color: transparent; }

.pad {
  display: grid; grid-template-columns: repeat(3, 64px); gap: 14px; margin-top: 24px;
}
.key {
  height: 64px;
  background: var(--pixel-card-bg);
  backdrop-filter: blur(10px);
  color: var(--pixel-text);
  border: 1px solid var(--pixel-border);
  border-radius: 14px;
  font-family: var(--font-pixel-num);
  font-size: 22px;
  cursor: pointer;
  box-shadow: var(--d-shadow-sm);
  transition: transform .12s ease, background .15s ease;
}
.key:active { transform: scale(.96); background: var(--pixel-bg-secondary); }
.key.fn { font-size: 18px; color: var(--pixel-info); }
.key[disabled] { opacity: 0.3; box-shadow: none; }
</style>
