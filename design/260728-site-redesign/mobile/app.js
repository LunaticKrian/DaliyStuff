/* PixelPack · 移动端原型交互 —— tab 切换 / 主题 / 像素块填充 */
(function () {
  'use strict';
  const html = document.documentElement;
  const tabbar = document.getElementById('tabbar');
  const views = document.querySelectorAll('.view');

  function buildBlocks(el) { const n = +el.dataset.blocks || 16; const f = document.createDocumentFragment(); for (let i = 0; i < n; i++) f.appendChild(document.createElement('i')); el.appendChild(f); }
  function fillBlocks(el) { const n = el.children.length; const pct = +el.dataset.pct || 0; const on = Math.round((pct / 100) * n); for (let i = 0; i < n; i++) el.children[i].classList.toggle('on', i < on); }
  document.querySelectorAll('.blocks').forEach((el) => { buildBlocks(el); fillBlocks(el); });

  function show(id) {
    views.forEach((v) => (v.hidden = v.id !== 'v-' + id));
    tabbar.querySelectorAll('a').forEach((a) => a.classList.toggle('is-active', a.dataset.view === id));
    const c = document.getElementById('content'); if (c) c.scrollTop = 0;
    history.replaceState(null, '', '#' + id);
  }
  tabbar.addEventListener('click', (e) => { const a = e.target.closest('a[data-view]'); if (a) { e.preventDefault(); show(a.dataset.view); } });

  const themeBtn = document.getElementById('themeBtn');
  const darkToggle = document.getElementById('darkToggle');
  function setTheme(t) { if (t === 'light') html.setAttribute('data-theme', 'light'); else html.removeAttribute('data-theme'); if (darkToggle) darkToggle.checked = t !== 'light'; }
  themeBtn && themeBtn.addEventListener('click', () => setTheme(html.getAttribute('data-theme') === 'light' ? 'dark' : 'light'));
  darkToggle && darkToggle.addEventListener('change', () => setTheme(darkToggle.checked ? 'dark' : 'light'));

  const initial = (location.hash || '').replace('#', '');
  show(initial && document.getElementById('v-' + initial) ? initial : 'dashboard');
})();
