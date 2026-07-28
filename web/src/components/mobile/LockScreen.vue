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
.lock-overlay {
  position: absolute; inset: 0; z-index: 500;
  background: var(--pixel-bg);
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 0 40px calc(env(safe-area-inset-bottom, 0px) + 40px);
}
.dots { display: flex; gap: 16px; margin: 28px 0 8px; }
.dots span {
  width: 16px; height: 16px; border: 2px solid var(--pixel-border); background: transparent;
  transition: background 120ms steps(2);
}
.dots span.filled { background: var(--pixel-info); }
.dots.err span.filled { background: var(--pixel-accent); }
.pad {
  display: grid; grid-template-columns: repeat(3, 64px); gap: 14px; margin-top: 24px;
}
.key {
  height: 64px; background: var(--pixel-card-bg); color: var(--pixel-text);
  border: 3px solid var(--pixel-border);
  font-family: var(--font-pixel-num); font-size: 22px; cursor: pointer;
  transition: transform 60ms steps(2);
}
.key:active { transform: translate(2px, 2px); background: var(--pixel-bg-secondary); }
.key.fn { font-size: 18px; color: var(--pixel-info); }
.key[disabled] { opacity: 0.3; }
</style>
