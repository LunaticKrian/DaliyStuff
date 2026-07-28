/* PixelPack · 桌面端原型交互
   - 视图切换（模拟路由） · 面包屑 · 历史哈希
   - 主题切换（深 / 浅） · 与设置开关联动
   - 分段像素块按 data-pct 填充
*/
(function () {
  'use strict';
  const html = document.documentElement;
  const nav = document.getElementById('nav');
  const views = document.querySelectorAll('.view');
  const crumb = document.getElementById('crumb');

  /* —— 分段像素块 —— */
  function buildBlocks(el) {
    const n = +el.dataset.blocks || 16;
    const f = document.createDocumentFragment();
    for (let i = 0; i < n; i++) f.appendChild(document.createElement('i'));
    el.appendChild(f);
  }
  function fillBlocks(el) {
    const n = el.children.length;
    const pct = +el.dataset.pct || 0;
    const on = Math.round((pct / 100) * n);
    for (let i = 0; i < n; i++) el.children[i].classList.toggle('on', i < on);
  }
  document.querySelectorAll('.blocks').forEach((el) => { buildBlocks(el); fillBlocks(el); });

  /* —— 视图切换 —— */
  function show(id) {
    views.forEach((v) => (v.hidden = v.id !== 'v-' + id));
    nav.querySelectorAll('a').forEach((a) => a.classList.toggle('is-active', a.dataset.view === id));
    if (crumb) crumb.textContent = '/' + id;
    const top = document.getElementById('content');
    if (top) top.scrollTop = 0;
    history.replaceState(null, '', '#' + id);
  }
  nav.addEventListener('click', (e) => {
    const a = e.target.closest('a[data-view]');
    if (a) { e.preventDefault(); show(a.dataset.view); }
  });
  document.querySelectorAll('[data-go]').forEach((el) =>
    el.addEventListener('click', () => show(el.dataset.go))
  );

  /* —— 主题切换 —— */
  const themeBtn = document.getElementById('themeBtn');
  const darkToggle = document.getElementById('darkToggle');
  function setTheme(t) {
    if (t === 'light') html.setAttribute('data-theme', 'light');
    else html.removeAttribute('data-theme');
    if (darkToggle) darkToggle.checked = t !== 'light';
  }
  themeBtn && themeBtn.addEventListener('click', () =>
    setTheme(html.getAttribute('data-theme') === 'light' ? 'dark' : 'light')
  );
  darkToggle && darkToggle.addEventListener('change', () => setTheme(darkToggle.checked ? 'dark' : 'light'));

  /* —— 初始化 —— */
  const initial = (location.hash || '').replace('#', '');
  show(initial && document.getElementById('v-' + initial) ? initial : 'dashboard');
})();
