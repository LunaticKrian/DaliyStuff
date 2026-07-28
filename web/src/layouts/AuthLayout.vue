<script setup lang="ts">
import { useThemeStore } from '../stores/theme'

const theme = useThemeStore()

// 夜间星空（仅深色模式）
const stars = Array.from({ length: 56 }, () => ({
  left: Math.random() * 100 + '%',
  top: Math.random() * 100 + '%',
  size: Math.random() < 0.8 ? 1 : 2,
  op: (0.2 + Math.random() * 0.5).toFixed(2),
  delay: (Math.random() * 4).toFixed(2) + 's',
  duration: (2.5 + Math.random() * 3).toFixed(2) + 's',
}))
</script>

<template>
  <div class="auth-screen">
    <!-- 背景：极光 + 网格 + 星点 -->
    <div class="bg" aria-hidden="true">
      <span class="orb a"></span><span class="orb b"></span><span class="grid"></span>
      <div class="stars">
        <span
          v-for="(s, i) in stars"
          :key="i"
          class="star"
          :style="{ left: s.left, top: s.top, width: s.size + 'px', height: s.size + 'px', '--op': s.op, animationDelay: s.delay, animationDuration: s.duration }"
        ></span>
      </div>
    </div>

    <!-- 主题切换 -->
    <button
      class="theme-toggle"
      @click="theme.toggle()"
      :aria-label="theme.mode === 'light' ? '切换到深色模式' : '切换到浅色模式'"
    >
      <svg v-show="theme.mode === 'dark'" class="tt-ico" viewBox="0 0 24 24" fill="currentColor"><path d="M18 22H8v-2h10v2ZM8 20H6v-2h2v2Zm12 0h-2v-2h2v2ZM6 18H4v-2h2v2Zm16 0h-2v-4h-2v-2h2v-2h2v8ZM4 16H2V6h2v10Zm14 0h-6v-2h6v2Zm-6-2h-2v-2h2v2Zm-2-2H8V6h2v6ZM6 6H4V4h2v2Zm8-2h-2v2h-2V4H6V2h8v2Z"/></svg>
      <svg v-show="theme.mode === 'light'" class="tt-ico" viewBox="0 0 24 24" fill="currentColor"><rect x="9" y="9" width="6" height="6"/><rect x="11" y="3" width="2" height="3"/><rect x="11" y="18" width="2" height="3"/><rect x="3" y="11" width="3" height="2"/><rect x="18" y="11" width="3" height="2"/><rect x="5" y="5" width="3" height="3"/><rect x="16" y="5" width="3" height="3"/><rect x="5" y="16" width="3" height="3"/><rect x="16" y="16" width="3" height="3"/></svg>
    </button>

    <div class="stage">
      <!-- ══ 左：品牌面板 ══ -->
      <aside class="brand">
        <div class="brand-inner">
          <div class="brand-top">
            <span class="brandmark"><span class="brand-dot"></span>PixelPack</span>
            <span class="brand-tag">自托管 · MIT</span>
          </div>

          <div class="brand-mid">
            <div class="brand-headline">
              <span class="eyebrow">RPG · 物品与日常</span>
              <h2>把生活过成<br /><span class="grad">一场 RPG</span></h2>
              <p>用游戏化的方式管理物品、消费与日常任务 —— 每件物品都是装备，每笔消费都在升级你的角色。</p>
            </div>
            <ul class="features">
              <li>
                <span class="f-ico"><svg viewBox="0 0 24 24"><path d="M3 7l9-4 9 4-9 4-9-4z"/><path d="M3 7v10l9 4 9-4V7"/><path d="M12 11v10"/></svg></span>
                <div><b>物品管理</b><span>价格、保修、日均成本一目了然</span></div>
              </li>
              <li>
                <span class="f-ico"><svg viewBox="0 0 24 24"><path d="M9 5h6v2H9z"/><rect x="5" y="6" width="14" height="15" rx="2"/><path d="M9 11h6M9 15h4"/></svg></span>
                <div><b>每日任务</b><span>完成即获 EXP，解锁成就</span></div>
              </li>
              <li>
                <span class="f-ico"><svg viewBox="0 0 24 24"><path d="M4 20V11M10 20V5M16 20v-7M22 20H2"/></svg></span>
                <div><b>数据统计</b><span>把冒险变成可视化图表</span></div>
              </li>
            </ul>
          </div>

          <footer class="brand-foot">© 2026 Krian · PixelPack · MIT</footer>
        </div>
      </aside>

      <!-- ══ 右：表单 ══ -->
      <main class="form-panel">
        <slot />
      </main>
    </div>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&display=swap');

/* —— 令牌（表单组件经 slot 继承）—— */
.auth-screen {
  --bg: #0a0b10;
  --bg-1: #0e0f16;
  --surface: rgba(255, 255, 255, 0.04);
  --surface-2: rgba(255, 255, 255, 0.065);
  --surface-3: rgba(255, 255, 255, 0.10);
  --border: rgba(255, 255, 255, 0.08);
  --border-2: rgba(255, 255, 255, 0.16);
  --text: #f4f6fb;
  --muted: #9aa3b2;
  --faint: #626b7e;
  --indigo: #6366f1;
  --violet: #a855f7;
  --cyan: #22d3ee;
  --success: #34d399;
  --danger: #fb7185;
  --grad: linear-gradient(135deg, #818cf8 0%, #7c5cff 40%, #22d3ee 100%);
  --grad-text: linear-gradient(110deg, #c7d2fe 0%, #d8b4fe 40%, #7dd3fc 80%, #67e8f9 100%);
  --radius: 16px;
  --radius-sm: 12px;
  --shadow: 0 24px 60px -24px rgba(0, 0, 0, 0.75);
  --glow: 0 0 80px -22px rgba(99, 102, 241, 0.55);
  --f-display: 'Space Grotesk', 'PingFang SC', system-ui, sans-serif;
  --f-body: 'Inter', 'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif;
  --f-mono: 'JetBrains Mono', ui-monospace, monospace;
  --aurora-1: rgba(99, 102, 241, 0.22);
  --aurora-2: rgba(34, 211, 238, 0.12);
  --grid-line: rgba(255, 255, 255, 0.022);

  position: relative;
  min-height: 100vh;
  display: flex;
  background: var(--bg);
  color: var(--text);
  font-family: var(--f-body);
  overflow: hidden;
}
[data-theme="light"] .auth-screen {
  --bg: #f4f5fa;
  --bg-1: #ffffff;
  --surface: rgba(17, 20, 40, 0.04);
  --surface-2: rgba(17, 20, 40, 0.065);
  --surface-3: rgba(17, 20, 40, 0.10);
  --border: rgba(17, 20, 40, 0.10);
  --border-2: rgba(17, 20, 40, 0.16);
  --text: #0f1326;
  --muted: #4b5568;
  --faint: #8b94a7;
  --cyan: #0891b2;
  --grad: linear-gradient(135deg, #6366f1 0%, #7c3aed 40%, #0891b2 100%);
  --grad-text: linear-gradient(110deg, #4f46e5 0%, #7c3aed 40%, #0891b2 80%, #059669 100%);
  --shadow: 0 18px 44px -22px rgba(17, 20, 40, 0.24);
  --glow: 0 0 60px -22px rgba(79, 70, 229, 0.35);
  --aurora-1: rgba(99, 102, 241, 0.14);
  --aurora-2: rgba(8, 145, 178, 0.10);
  --grid-line: rgba(17, 20, 40, 0.04);
}

/* —— 背景 —— */
.bg { position: absolute; inset: 0; z-index: 0; pointer-events: none; overflow: hidden; }
.bg .orb { position: absolute; border-radius: 50%; filter: blur(80px); }
.bg .orb.a { width: 440px; height: 440px; left: -8%; top: -12%; background: radial-gradient(circle, var(--aurora-1), transparent 65%); }
.bg .orb.b { width: 380px; height: 380px; right: -8%; bottom: -14%; background: radial-gradient(circle, var(--aurora-2), transparent 65%); }
.bg .grid { position: absolute; inset: 0; background-image: linear-gradient(var(--grid-line) 1px, transparent 1px), linear-gradient(90deg, var(--grid-line) 1px, transparent 1px); background-size: 46px 46px; -webkit-mask-image: radial-gradient(80% 70% at 50% 30%, #000, transparent 85%); mask-image: radial-gradient(80% 70% at 50% 30%, #000, transparent 85%); }
.stars { position: absolute; inset: 0; z-index: 0; pointer-events: none; }
.star { position: absolute; background: #f4f6fb; border-radius: 50%; animation-name: twinkle; animation-timing-function: ease-in-out; animation-iteration-count: infinite; }
@keyframes twinkle { 0%, 100% { opacity: var(--op, .3); } 50% { opacity: 1; } }
[data-theme="light"] .stars { display: none; }
@media (prefers-reduced-motion: reduce) { .star { animation: none; opacity: var(--op, .3); } }

/* —— 主题切换 —— */
.theme-toggle { position: absolute; top: 1.1rem; right: 1.1rem; z-index: 20; width: 38px; height: 38px; display: grid; place-items: center; border-radius: 12px; border: 1px solid var(--border); background: var(--surface); backdrop-filter: blur(10px); color: var(--muted); cursor: pointer; transition: color .2s ease, background .2s ease, border-color .2s ease; }
.theme-toggle:hover { color: var(--text); background: var(--surface-2); border-color: var(--border-2); }
.tt-ico { width: 18px; height: 18px; }

/* —— 舞台分屏 —— */
.stage { position: relative; z-index: 2; display: grid; grid-template-columns: 1.08fr 0.92fr; width: 100%; min-height: 100vh; }

/* —— 品牌面板 —— */
.brand { position: relative; display: flex; padding: clamp(1.5rem, 4vw, 3rem); overflow: hidden; }
.brand-inner { position: relative; z-index: 1; display: flex; flex-direction: column; justify-content: space-between; gap: 2rem; max-width: 480px; }
.brand-top { display: flex; align-items: center; gap: 1rem; }
.brandmark { display: inline-flex; align-items: center; gap: .55rem; font-family: var(--f-display); font-weight: 700; font-size: 1.15rem; letter-spacing: -.01em; }
.brand-dot { width: 12px; height: 12px; background: var(--grad); box-shadow: var(--glow); }
.brand-tag { margin-left: auto; font-family: var(--f-mono); font-size: .68rem; letter-spacing: .12em; color: var(--faint); text-transform: uppercase; padding: .35em .7em; border: 1px solid var(--border); border-radius: 999px; }

.brand-mid { display: flex; flex-direction: column; gap: 2rem; }
.brand-headline .eyebrow { display: inline-block; font-family: var(--f-mono); font-size: .72rem; letter-spacing: .16em; color: var(--cyan); text-transform: uppercase; margin-bottom: 1rem; }
.brand-headline h2 { font-family: var(--f-display); font-size: clamp(1.9rem, 3.4vw, 2.8rem); font-weight: 700; line-height: 1.1; letter-spacing: -.02em; }
.grad { background: var(--grad-text); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent; color: transparent; }
.brand-headline p { color: var(--muted); margin-top: 1rem; max-width: 40ch; line-height: 1.7; }

.features { display: flex; flex-direction: column; gap: 1rem; margin: 0; padding: 0; list-style: none; }
.features li { display: flex; align-items: center; gap: .9rem; }
.f-ico { flex: none; display: inline-grid; place-items: center; width: 42px; height: 42px; border-radius: 11px; border: 1px solid var(--border); background: var(--surface); color: var(--cyan); }
.f-ico svg { width: 20px; height: 20px; fill: none; stroke: currentColor; stroke-width: 1.7; stroke-linecap: round; stroke-linejoin: round; }
.features b { display: block; font-family: var(--f-display); font-weight: 600; font-size: .96rem; color: var(--text); }
.features span { font-size: .82rem; color: var(--muted); }

.brand-foot { font-family: var(--f-mono); font-size: .74rem; color: var(--faint); }

/* —— 表单面板 —— */
.form-panel { position: relative; display: flex; align-items: center; justify-content: center; padding: clamp(1.5rem, 4vw, 3rem); }

/* —— 响应式 —— */
@media (max-width: 920px) {
  .stage { grid-template-columns: 1fr; }
  .brand { display: none; }
}
@media (max-width: 420px) {
  .brand-tag { display: none; }
}
</style>
