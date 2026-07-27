/* ════════════════════════════════════════════════
   PixelPack 介绍页 v2 · 交互
   ════════════════════════════════════════════════ */

// ════════════ 链接配置 ════════════
const GITHUB_URL = 'https://github.com/LunaticKrian/PixelPack';
const DEMO_URL = ''; // ← TODO: 填入在线 Demo 地址(例如 https://pixelpack.airise.site)。留空时降级为「即将上线」。
// ══════════════════════════════════

const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

/** 注入 CTA */
function wireCTAs() {
  document.querySelectorAll('[data-cta="github"]').forEach((a) => (a.href = GITHUB_URL));
  document.querySelectorAll('[data-cta="demo"]').forEach((a) => {
    if (DEMO_URL) {
      a.href = DEMO_URL;
    } else {
      a.removeAttribute('href');
      a.removeAttribute('target');
      a.setAttribute('data-pending', '');
      a.setAttribute('aria-disabled', 'true');
      a.textContent = a.textContent.includes('试用') ? 'Demo 即将上线' : '即将上线';
    }
  });
}

/** 滚动渐显 */
function wireReveal() {
  const els = document.querySelectorAll('[data-reveal]');
  if (reduceMotion || !('IntersectionObserver' in window)) {
    els.forEach((el) => el.setAttribute('data-in', 'true'));
    return;
  }
  const io = new IntersectionObserver(
    (entries) => {
      entries.forEach((e, i) => {
        if (e.isIntersecting) {
          e.target.style.setProperty('--d', `${Math.min(i, 4) * 70}ms`);
          e.target.setAttribute('data-in', 'true');
          io.unobserve(e.target);
        }
      });
    },
    { threshold: 0.12, rootMargin: '0px 0px -8% 0px' }
  );
  els.forEach((el) => io.observe(el));
}

/** 数字滚动 */
function animateCount(el) {
  const target = Number(el.dataset.count || '0');
  const suffix = el.dataset.suffix || '';
  if (reduceMotion) {
    el.textContent = target + suffix;
    return;
  }
  const dur = 1200;
  const start = performance.now();
  const tick = (now) => {
    const t = Math.min((now - start) / dur, 1);
    const eased = 1 - Math.pow(1 - t, 3);
    el.textContent = Math.round(target * eased) + suffix;
    if (t < 1) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}
function wireCounters() {
  const nums = document.querySelectorAll('.stat-num[data-count]');
  if (reduceMotion || !('IntersectionObserver' in window)) {
    nums.forEach(animateCount);
    return;
  }
  const io = new IntersectionObserver(
    (entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) {
          animateCount(e.target);
          io.unobserve(e.target);
        }
      });
    },
    { threshold: 0.6 }
  );
  nums.forEach((n) => io.observe(n));
}

/** Hero 截图视差倾斜 */
function wireTilt() {
  if (reduceMotion) return;
  const tilt = document.querySelector('[data-tilt]');
  if (!tilt) return;
  const card = tilt.querySelector('.shot-card');
  const glare = tilt.querySelector('.shot-glare');
  let raf = 0;
  tilt.addEventListener('mousemove', (ev) => {
    const r = tilt.getBoundingClientRect();
    const px = (ev.clientX - r.left) / r.width - 0.5;
    const py = (ev.clientY - r.top) / r.height - 0.5;
    if (raf) cancelAnimationFrame(raf);
    raf = requestAnimationFrame(() => {
      card.style.setProperty('--rx', `${(-py * 7).toFixed(2)}deg`);
      card.style.setProperty('--ry', `${(px * 9).toFixed(2)}deg`);
      if (glare) {
        glare.style.setProperty('--mx', `${(px + 0.5) * 100}%`);
        glare.style.setProperty('--my', `${(py + 0.5) * 100}%`);
      }
    });
  });
  tilt.addEventListener('mouseleave', () => {
    card.style.setProperty('--rx', '2deg');
    card.style.setProperty('--ry', '-3deg');
  });
}

/** 技术标签切换 */
function wireTabs() {
  const tabs = document.querySelectorAll('.tech-tab');
  const panels = document.querySelectorAll('.tech-chips');
  tabs.forEach((tab) => {
    tab.addEventListener('click', () => {
      const idx = tab.dataset.tab;
      tabs.forEach((t) => t.classList.toggle('is-active', t === tab));
      panels.forEach((p) => {
        const show = p.dataset.tech === idx;
        p.hidden = !show;
        if (show) {
          // 重启入场动画
          p.style.animation = 'none';
          p.offsetHeight; // reflow
          p.style.animation = '';
        }
      });
    });
  });
}

document.addEventListener('DOMContentLoaded', () => {
  wireCTAs();
  wireReveal();
  wireCounters();
  wireTilt();
  wireTabs();
});
