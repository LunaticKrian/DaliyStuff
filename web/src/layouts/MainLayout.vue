<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useThemeStore } from '../stores/theme'

const router = useRouter()
const auth = useAuthStore()
const theme = useThemeStore()

// 夜间星空（仅深色模式）；动态随机分布，每隔数秒重新散布
const newPos = () => ({ left: Math.random() * 100 + '%', top: Math.random() * 100 + '%' })
const stars = ref(Array.from({ length: 64 }, () => ({
  ...newPos(),
  size: Math.random() < 0.82 ? 1 : 2,
  op: (0.2 + Math.random() * 0.5).toFixed(2),
  delay: (Math.random() * 4).toFixed(2) + 's',
  duration: (2.5 + Math.random() * 3.5).toFixed(2) + 's',
  mv: (2.5 + Math.random() * 2.5).toFixed(2) + 's',
})))
function reshuffleStars() {
  stars.value = stars.value.map((s) => ({ ...s, ...newPos() }))
}

// 24 小时时间进度
const now = ref(new Date())
let timeTimer: ReturnType<typeof setInterval> | null = null
const clockText = computed(() => {
  const d = now.value
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
})
const dayProgress = computed(() => {
  const d = now.value
  const secs = d.getHours() * 3600 + d.getMinutes() * 60 + d.getSeconds()
  return (secs / 86400) * 100
})
let starTimer: ReturnType<typeof setInterval> | null = null
onMounted(() => {
  timeTimer = setInterval(() => { now.value = new Date() }, 1000)
  starTimer = setInterval(reshuffleStars, 9000)
})
onUnmounted(() => {
  if (timeTimer) clearInterval(timeTimer)
  if (starTimer) clearInterval(starTimer)
})

const navItems = [
  { path: '/', label: '角色信息', icon: 'home' },
  { path: '/quests', label: '委托大厅', icon: 'clipboard' },
  { path: '/chat', label: 'AI 对话', icon: 'message' },
  { path: '/transfer', label: '传送法阵', icon: 'target' },
  { path: '/world-map', label: '世界地图', icon: 'globe' },
  { path: '/resume', label: '冒险履历', icon: 'notebook' },
]

async function handleLogout() {
  await auth.logout()
  router.push('/login')
}

// 主题切换：用 View Transitions API 做圆形展开过渡（不支持 / 减弱动效时直接切换）
function applyDomTheme(m: 'dark' | 'light') {
  if (m === 'light') document.documentElement.setAttribute('data-theme', 'light')
  else document.documentElement.removeAttribute('data-theme')
}
function onToggleTheme(e: MouseEvent) {
  const reduce = typeof window !== 'undefined' && !!window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches
  const doc = document as Document & { startViewTransition?: (cb: () => void) => unknown }
  const next: 'dark' | 'light' = theme.mode === 'light' ? 'dark' : 'light'
  if (reduce || typeof doc.startViewTransition !== 'function') { theme.set(next); return }
  doc.documentElement.style.setProperty('--vt-x', e.clientX + 'px')
  doc.documentElement.style.setProperty('--vt-y', e.clientY + 'px')
  doc.startViewTransition(() => {
    applyDomTheme(next) // 同步改 DOM，保证 VT 能捕获到新旧两帧
    theme.set(next)     // 更新响应式状态 + 持久化（watch 会幂等地再 apply 一次）
  })
}
</script>

<template>
  <div class="app-shell">
    <!-- 背景：极光 + 网格（去 CRT 扫描线 / 星点） -->
    <div class="bg" aria-hidden="true">
      <span class="orb a"></span><span class="orb b"></span><span class="grid"></span>
      <div class="stars">
        <span
          v-for="(s, i) in stars"
          :key="i"
          class="star"
          :style="{ left: s.left, top: s.top, width: s.size + 'px', height: s.size + 'px', '--op': s.op, '--mv': s.mv, animationDelay: s.delay, animationDuration: s.duration }"
        ></span>
      </div>
    </div>

    <!-- 像素图标 sprite（Pixelarticons, MIT） -->
    <svg width="0" height="0" style="position:absolute" aria-hidden="true">
      <symbol id="ml-home" viewBox="0 0 24 24" fill="currentColor"><path d="M4 20h16v2H4zm16-10h2v10h-2zM2 10h2v10H2zm2-2h2v2H4zm2-2h2v2H6zm2-2h2v2H8zm2-2h4v2h-4zm4 2h2v2h-2zm2 2h2v2h-2zm2 2h2v2h-2zM8 14h2v6H8zm2-2h4v2h-4zm4 2h2v6h-2z"/></symbol>
      <symbol id="ml-clipboard" viewBox="0 0 24 24" fill="currentColor"><path d="M4 6h2v14H4zm2 14h12v2H6zM18 6h2v14h-2zM6 4h2v2H6zm10 0h2v2h-2zm-6-2h4v2h-4zm0 4h4v2h-4zM8 2h2v6H8zm6 0h2v6h-2z"/></symbol>
      <symbol id="ml-message" viewBox="0 0 24 24" fill="currentColor"><path d="M20 2H4v2h16zm0 14H6v2h14zm2-12h-2v12h2zM4 4H2v18h2zm2 14H4v2h2z"/></symbol>
      <symbol id="ml-target" viewBox="0 0 24 24" fill="currentColor"><path d="M5 1h14v2H5zM3 3h2v2H3zm0 16h2v2H3zm16 0h2v2h-2zm0-16h2v2h-2zm2 2h2v14h-2zM5 21h14v2H5zM1 5h2v14H1zm8 0h6v2H9zM5 9h2v6H5zm4 8h6v2H9zm8-8h2v6h-2zm-6 0h2v2h-2zM7 7h2v2H7zm0 8h2v2H7zm8 0h2v2h-2zm0-8h2v2h-2zm-6 4h2v2H9zm2 2h2v2h-2zm2-2h2v2h-2z"/></symbol>
      <symbol id="ml-globe" viewBox="0 0 24 24" fill="currentColor"><path d="M6 2h12v2H6zm0 18h12v2H6zM4 4h2v2H4zm5 0h2v2H9zm0 14h2v2H9zm4 0h2v2h-2zM7 6h2v12H7zm8 0h2v12h-2zm-2-2h2v2h-2zm7 0h-2v2h2zM2 6h2v12H2zm20 0h-2v12h2zM4 18h2v2H4zm16 0h-2v2h2z"/><path d="M3 11h18v2H3z"/></symbol>
      <symbol id="ml-notebook" viewBox="0 0 24 24" fill="currentColor"><path d="M6 2h14v2H6zm0 18h14v2H6zM20 4h2v16h-2zM4 4h2v16H4z"/><path d="M2 7h6v2H2zm0 4h6v2H2zm0 4h6v2H2zM16 4h2v16h-2z"/></symbol>
      <symbol id="ml-user" viewBox="0 0 24 24" fill="currentColor"><path d="M9 2h6v2H9zm0 8h6v2H9zm6-6h2v6h-2zM7 4h2v6H7zM4 18h2v4H4zm14 0h2v4h-2zM8 14h8v2H8zm-2 2h2v2H6zm10 0h2v2h-2z"/></symbol>
      <symbol id="ml-logout" viewBox="0 0 24 24" fill="currentColor"><path d="M8 11h12v2H8zm8-2h2v2h-2z"/><path d="M14 7h2v10h-2zm2 6h2v2h-2zM6 2h12v2H6zm0 18h12v2H6zM4 4h2v16H4zm14 0h2v3h-2zm0 13h2v3h-2z"/></symbol>
      <symbol id="ml-clock" viewBox="0 0 24 24" fill="currentColor"><path d="M6 2h12v2H6zM2 6h2v12H2zm18 0h2v12h-2zm-2-2h2v2h-2zM4 4h2v2H4zm2 18h12v-2H6zm12-2h2v-2h-2zM4 20h2v-2H4zm7-14h2v7h-2zm2 7h2v2h-2zm2 2h2v2h-2z"/></symbol>
      <symbol id="ml-moon" viewBox="0 0 24 24" fill="currentColor"><path d="M18 22H8v-2h10v2ZM8 20H6v-2h2v2Zm12 0h-2v-2h2v2ZM6 18H4v-2h2v2Zm16 0h-2v-4h-2v-2h2v-2h2v8ZM4 16H2V6h2v10Zm14 0h-6v-2h6v2Zm-6-2h-2v-2h2v2Zm-2-2H8V6h2v6ZM6 6H4V4h2v2Zm8-2h-2v2h-2V4H6V2h8v2Z"/></symbol>
      <symbol id="ml-sun" viewBox="0 0 24 24" fill="currentColor"><rect x="9" y="9" width="6" height="6"/><rect x="11" y="3" width="2" height="3"/><rect x="11" y="18" width="2" height="3"/><rect x="3" y="11" width="3" height="2"/><rect x="18" y="11" width="3" height="2"/><rect x="5" y="5" width="3" height="3"/><rect x="16" y="5" width="3" height="3"/><rect x="5" y="16" width="3" height="3"/><rect x="16" y="16" width="3" height="3"/></symbol>
    </svg>

    <!-- ════════ 顶栏 ════════ -->
    <header class="topbar">
      <div class="brand"><span class="brand-dot"></span>PixelPack</div>
      <nav class="nav">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-tab"
          :class="{ active: $route.path === item.path || (item.path !== '/' && $route.path.startsWith(item.path)) }"
        >
          <svg class="nav-ico"><use :href="'#ml-' + item.icon" /></svg>
          <span class="nav-label">{{ item.label }}</span>
        </router-link>
      </nav>
      <div class="topbar-right">
        <button
          class="theme-btn"
          @click="onToggleTheme($event)"
          :aria-label="theme.mode === 'light' ? '切换到深色模式' : '切换到浅色模式'"
          :title="theme.mode === 'light' ? '切换到深色' : '切换到浅色'"
        >
          <svg class="status-ico" v-show="theme.mode === 'dark'"><use href="#ml-moon" /></svg>
          <svg class="status-ico" v-show="theme.mode === 'light'"><use href="#ml-sun" /></svg>
        </button>
        <span class="time-pill" :title="'今日进度 ' + dayProgress.toFixed(1) + '%'">
          <svg class="status-ico"><use href="#ml-clock" /></svg>
          <span class="time-bar"><i :style="{ width: dayProgress + '%' }"></i></span>
          <span class="time-num">{{ clockText }}</span>
        </span>
      </div>
    </header>

    <!-- ════════ 内容 ════════ -->
    <main class="content-area">
      <slot />
    </main>

    <!-- ════════ 底部状态栏 ════════ -->
    <footer class="statusbar">
      <router-link to="/settings" class="status-user">
        <svg class="status-ico"><use href="#ml-user" /></svg>
        <span>{{ auth.user?.username }}</span>
      </router-link>
      <div class="status-right">
        <span class="crumb"><span class="crumb-prefix">/</span>{{ $route.name }}</span>
        <button class="logout-btn" @click="handleLogout">
          <svg class="status-ico"><use href="#ml-logout" /></svg>
          <span>退出</span>
        </button>
      </div>
    </footer>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&display=swap');

/* —— 本外壳令牌（高级深色；浅色自适应）—— */
.app-shell {
  --ml-bg: #0b0d14;
  --ml-bar: rgba(11, 13, 20, 0.6);
  --ml-surface: rgba(255, 255, 255, 0.04);
  --ml-surface-2: rgba(255, 255, 255, 0.065);
  --ml-border: rgba(255, 255, 255, 0.08);
  --ml-border-2: rgba(255, 255, 255, 0.16);
  --ml-text: #f4f6fb;
  --ml-muted: #9aa3b2;
  --ml-faint: #626b7e;
  --ml-cyan: #22d3ee;
  --ml-rpg-hp: #fb7185;
  --ml-grad: linear-gradient(135deg, #818cf8 0%, #7c5cff 40%, #22d3ee 100%);
  --ml-aurora-1: rgba(99, 102, 241, 0.20);
  --ml-aurora-2: rgba(34, 211, 238, 0.11);
  --ml-grid: rgba(255, 255, 255, 0.022);
  --ml-f-display: 'Space Grotesk', 'PingFang SC', system-ui, sans-serif;
  --ml-f-body: 'Inter', 'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif;
  --ml-f-mono: 'JetBrains Mono', ui-monospace, monospace;

  position: relative;
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
  background: var(--ml-bg);
  font-family: var(--ml-f-body);
  color: var(--ml-text);
}
[data-theme="light"] .app-shell {
  --ml-bg: #f4f5fa;
  --ml-bar: rgba(255, 255, 255, 0.7);
  --ml-surface: rgba(17, 20, 40, 0.04);
  --ml-surface-2: rgba(17, 20, 40, 0.065);
  --ml-border: rgba(17, 20, 40, 0.10);
  --ml-border-2: rgba(17, 20, 40, 0.16);
  --ml-text: #0f1326;
  --ml-muted: #4b5568;
  --ml-faint: #8b94a7;
  --ml-cyan: #0891b2;
  --ml-rpg-hp: #e11d48;
  --ml-grad: linear-gradient(135deg, #6366f1 0%, #7c3aed 40%, #0891b2 100%);
  --ml-aurora-1: rgba(99, 102, 241, 0.12);
  --ml-aurora-2: rgba(8, 145, 178, 0.08);
  --ml-grid: rgba(17, 20, 40, 0.04);
}

/* —— 背景氛围 —— */
.bg { position: absolute; inset: 0; z-index: 0; pointer-events: none; overflow: hidden; }
.bg .orb { position: absolute; border-radius: 50%; filter: blur(80px); }
.bg .orb.a { width: 420px; height: 420px; left: -8%; top: -12%; background: radial-gradient(circle, var(--ml-aurora-1), transparent 65%); }
.bg .orb.b { width: 360px; height: 360px; right: -8%; bottom: -14%; background: radial-gradient(circle, var(--ml-aurora-2), transparent 65%); }
.bg .grid { position: absolute; inset: 0; background-image: linear-gradient(var(--ml-grid) 1px, transparent 1px), linear-gradient(90deg, var(--ml-grid) 1px, transparent 1px); background-size: 46px 46px; -webkit-mask-image: radial-gradient(80% 70% at 50% 0%, #000, transparent 85%); mask-image: radial-gradient(80% 70% at 50% 0%, #000, transparent 85%); }

/* 夜间星空（仅深色模式） */
.stars { position: absolute; inset: 0; z-index: 0; pointer-events: none; }
.star { position: absolute; background: #f4f6fb; border-radius: 50%; animation-name: twinkle; animation-timing-function: ease-in-out; animation-iteration-count: infinite; transition: left var(--mv, 3s) ease, top var(--mv, 3s) ease; }
@keyframes twinkle { 0%, 100% { opacity: var(--op, .3); } 50% { opacity: 1; } }
[data-theme="light"] .stars { display: none; }
@media (prefers-reduced-motion: reduce) { .star { animation: none; opacity: var(--op, .3); } }

/* —— 像素图标 —— */
.nav-ico, .status-ico { width: 17px; height: 17px; fill: currentColor; shape-rendering: crispEdges; flex: none; }

/* —— 顶栏 —— */
.topbar {
  position: relative; z-index: 5; height: 60px; flex: none;
  display: flex; align-items: center; gap: 1rem;
  padding: 0 clamp(0.8rem, 2vw, 1.4rem);
  border-bottom: 1px solid var(--ml-border);
  background: var(--ml-bar);
  backdrop-filter: blur(14px);
}
.brand { display: inline-flex; align-items: center; gap: .55rem; font-family: var(--ml-f-display); font-weight: 700; font-size: 1.05rem; letter-spacing: -.01em; color: var(--ml-text); }
.brand-dot { width: 12px; height: 12px; background: var(--ml-grad); box-shadow: 0 0 16px -2px rgba(99, 102, 241, .6); }

.nav { display: flex; align-items: center; gap: 2px; margin-left: .6rem; }
.nav-tab {
  position: relative;
  display: inline-flex; align-items: center; gap: .5rem;
  padding: .5rem .8rem; border-radius: 10px;
  font-size: .88rem; font-weight: 500; color: var(--ml-muted);
  transition: color .2s ease, background .2s ease;
}
.nav-tab:hover { color: var(--ml-text); background: var(--ml-surface); }
.nav-tab.active { color: var(--ml-text); background: var(--ml-surface-2); }
.nav-tab.active::after { content: ''; position: absolute; left: 50%; bottom: -1px; width: 22px; height: 2px; transform: translateX(-50%); background: var(--ml-grad); border-radius: 2px; }

.topbar-right { margin-left: auto; display: flex; align-items: center; gap: .6rem; }
.time-pill { display: inline-flex; align-items: center; gap: .5rem; padding: .35rem .65rem; border: 1px solid var(--ml-border-2); border-radius: 999px; background: var(--ml-surface); color: var(--ml-muted); }
.time-pill .status-ico { width: 14px; height: 14px; color: var(--ml-cyan); }
.time-bar { width: 64px; height: 6px; border-radius: 3px; background: var(--ml-surface-2); overflow: hidden; }
.time-bar > i { display: block; height: 100%; background: var(--ml-grad); transition: width 1s linear; }
.time-num { font-family: var(--ml-f-mono); font-size: .72rem; color: var(--ml-text); font-variant-numeric: tabular-nums; }
.theme-btn { display: inline-grid; place-items: center; width: 34px; height: 34px; border-radius: 10px; border: 1px solid var(--ml-border); background: var(--ml-surface); color: var(--ml-muted); cursor: pointer; transition: color .2s ease, background .2s ease, border-color .2s ease; }
.theme-btn:hover { color: var(--ml-text); background: var(--ml-surface-2); border-color: var(--ml-border-2); }

/* —— 内容区 —— */
.content-area { position: relative; z-index: 1; flex: 1; overflow-y: auto; padding: clamp(1rem, 2.4vw, 1.8rem) clamp(1rem, 3vw, 2.2rem); }

/* —— 底部状态栏 —— */
.statusbar {
  position: relative; z-index: 5; height: 42px; flex: none;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 clamp(0.8rem, 2vw, 1.4rem);
  border-top: 1px solid var(--ml-border);
  background: var(--ml-bar);
  backdrop-filter: blur(14px);
  font-size: .8rem;
}
.status-user { display: inline-flex; align-items: center; gap: .45rem; color: var(--ml-muted); transition: color .2s ease; }
.status-user:hover { color: var(--ml-text); }
.status-right { display: flex; align-items: center; gap: 1rem; }
.crumb { font-family: var(--ml-f-mono); color: var(--ml-faint); }
.crumb-prefix { color: var(--ml-cyan); margin-right: 1px; }
.logout-btn { display: inline-flex; align-items: center; gap: .4rem; padding: .35rem .7rem; border: 1px solid var(--ml-border-2); border-radius: 8px; background: var(--ml-surface); color: var(--ml-muted); cursor: pointer; transition: color .2s ease, border-color .2s ease, background .2s ease; }
.logout-btn:hover { color: var(--ml-rpg-hp); border-color: var(--ml-rpg-hp); background: rgba(251, 113, 133, .08); }

/* —— 响应式 —— */
@media (max-width: 860px) {
  .nav-tab .nav-label { display: none; }
  .nav-tab { padding: .5rem .6rem; }
  .nav { margin-left: .3rem; }
  .time-pill .time-num { display: none; }
  .time-bar { width: 44px; }
}
@media (max-width: 560px) {
  .crumb { display: none; }
  .brand { font-size: .95rem; }
}
</style>

<style>
/* 主题切换：从点击点圆形展开（View Transitions API；不支持时回退即时切换） */
::view-transition-old(root),
::view-transition-new(root) { animation: none; mix-blend-mode: normal; }
::view-transition-new(root) { animation: vt-reveal .5s ease; }
@keyframes vt-reveal {
  from { clip-path: circle(0px at var(--vt-x, 50%) var(--vt-y, 50%)); }
  to { clip-path: circle(150% at var(--vt-x, 50%) var(--vt-y, 50%)); }
}
@media (prefers-reduced-motion: reduce) {
  ::view-transition-old(root), ::view-transition-new(root) { animation: none !important; }
}
</style>
