<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { isServerConfigured, isTauri } from '../utils/platform'
import { useAppLock } from '../composables/useAppLock'
import LockScreen from '../components/mobile/LockScreen.vue'

const route = useRoute()
const router = useRouter()

// 应用锁（GUILD LOCK）：启动与回前台时落锁
const { enabled: lockEnabled, locked: isLocked, lock: doLock } = useAppLock()
function onVisibility() {
  if (document.visibilityState === 'visible') doLock()
}

// CRT 开机幕：仅首次挂载播一次
const booting = ref(true)
let bootTimer: ReturnType<typeof setTimeout> | undefined
onMounted(() => {
  bootTimer = setTimeout(() => (booting.value = false), 820)
  doLock() // 启动时若已启用则落锁
  document.addEventListener('visibilitychange', onVisibility)
})
onUnmounted(() => {
  bootTimer && clearTimeout(bootTimer)
  document.removeEventListener('visibilitychange', onVisibility)
})

// 链路 LED：在线/离线（navigator.onLine）；桌面未配置服务器时显离线
const online = ref(typeof navigator !== 'undefined' ? navigator.onLine : true)
const linkClass = computed(() => {
  if (isTauri() && !isServerConfigured()) return 'm-link--offline'
  return online.value ? 'm-link--linked' : 'm-link--offline'
})
const linkTxt = computed(() => {
  if (isTauri() && !isServerConfigured()) return 'NO LINK'
  return online.value ? 'LINKED' : 'OFFLINE'
})
function onOnline() { online.value = true }
function onOffline() { online.value = false }
onMounted(() => {
  window.addEventListener('online', onOnline)
  window.addEventListener('offline', onOffline)
})
onUnmounted(() => {
  window.removeEventListener('online', onOnline)
  window.removeEventListener('offline', onOffline)
})

// 时钟
const clock = ref('')
let clockTimer: ReturnType<typeof setInterval> | undefined
function tick() {
  const d = new Date()
  clock.value = `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
onMounted(() => { tick(); clockTimer = setInterval(tick, 10000) })
onUnmounted(() => clockTimer && clearInterval(clockTimer))

// Tab Dock：仅在 primary 路由（route.meta.tab 存在）显示
const showDock = computed(() => !!route.meta.tab)
const tabs = [
  { key: 'dashboard', to: '/', icon: '⌂', label: '主城' },
  { key: 'items', to: '/items', icon: '◈', label: '物品' },
  { key: 'chat', to: '/chat', icon: '✦', label: '智核', crest: true },
  { key: 'quests', to: '/quests', icon: '⚑', label: '委托' },
  { key: 'profile', to: '/me', icon: '◉', label: '我的' },
]
function isActive(key: string) {
  return route.meta.tab === key
}
function go(to: string) {
  router.push(to)
}
</script>

<template>
  <div class="m-deck">
    <div v-if="booting" class="m-boot"></div>
    <LockScreen v-if="lockEnabled && isLocked" />

    <!-- 设备状态条 -->
    <div class="m-statusbar">
      <div class="m-sb__mark"></div>
      <div class="m-sb__brand">PIXELPACK</div>
      <div class="m-sb__spacer"></div>
      <div class="m-link" :class="linkClass"><span class="m-link__dot"></span><span class="m-link__txt">{{ linkTxt }}</span></div>
      <div class="m-sb__clock">{{ clock }}</div>
    </div>

    <!-- 屏幕区 -->
    <main class="m-viewport">
      <slot />
    </main>

    <!-- Tab Dock（仅 primary 路由） -->
    <nav v-if="showDock" class="m-tabbar">
      <a v-for="t in tabs" :key="t.key" class="m-tab"
         :class="{ active: isActive(t.key), 'm-tab--crest': t.crest }"
         @click="go(t.to)">
        <span v-if="t.crest" class="m-crest">{{ t.icon }}</span>
        <span v-else class="m-tab__ico">{{ t.icon }}</span>
        <span class="m-tab__lbl">{{ t.label }}</span>
      </a>
    </nav>
  </div>
</template>
