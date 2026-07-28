/* =====================================================================
   PixelPack · 移动端原型交互  —— 纯演示用，非产品代码
   - CRT 开机幕 → 默认进主城
   - go(id) 切屏 + 同步底部 Dock 高亮
   - 智核徽记(crest) 直进 AI 对话页
   ===================================================================== */

// 屏幕ID → 所属底部Tab（决定 Dock 高亮；auth 流程为 null 不高亮）
const TAB_OF = {
  dashboard: 'dashboard', items: 'items', chat: 'chat', quests: 'quests', profile: 'profile',
  'item-detail': 'items', 'item-form': 'items',
  'blog-detail': 'profile', worldmap: 'profile', stats: 'profile', 'blog-list': 'profile',
  resume: 'profile', transfer: 'profile', settings: 'profile',
  handshake: null, login: null, register: null, 'character-create': null,
};

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];

function setTab(key) {
  $$('.tab').forEach((t) => t.classList.toggle('active', t.dataset.tab === key));
}

function go(id) {
  const vp = $('#deck .viewport');
  $$('.screen').forEach((s) => s.classList.remove('active'));
  const target = $('#scr-' + id);
  if (!target) return;
  target.classList.add('active');
  if (vp) vp.scrollTop = 0;
  setTab(TAB_OF[id] ?? null);
  hideSheet();
}

// ── 底部抽屉（保留扩展位，当前直进对话页）──
function showSheet() { $('#scrim').classList.add('show'); $('#sheet').classList.add('show'); }
function hideSheet() { $('#scrim').classList.remove('show'); $('#sheet').classList.remove('show'); }

// ── 链路 LED 状态循环（演示三态：在线/同步/在线）──
function ledDemo() {
  const link = $('#link');
  if (!link) return;
  const cycle = ['link--linked', 'link--syncing', 'link--linked'];
  const txt = { 'link--linked': 'LINKED', 'link--syncing': 'SYNC', 'link--offline': 'OFFLINE' };
  let i = 0;
  setInterval(() => {
    i = (i + 1) % cycle.length;
    link.className = 'link ' + cycle[i];
    $('.link__txt', link).textContent = txt[cycle[i]];
  }, 2600);
}

document.addEventListener('DOMContentLoaded', () => {
  // CRT 开机幕 → 默认进主城
  const boot = $('#boot');
  setTimeout(() => {
    boot && boot.classList.add('done');
    go('dashboard');
  }, 820);

  // LOGO 可重看开机接驳流程
  const brand = $('.sb__brand');
  brand && (brand.style.cursor = 'pointer') &&
    brand.addEventListener('click', () => go('handshake'));

  // 抽屉遮罩关闭
  $('#scrim') && $('#scrim').addEventListener('click', hideSheet);

  ledDemo();
});
