/* PixelPack · 登录/注册 交互（Hi-fi Pixel）
   - 视图切换（登录 / 注册）
   - 密码显隐
   - 分段像素经验条：登录态按 data-pct 静态填充；注册态由密码强度实时驱动
   - 模拟提交（loading）—— 仅设计稿用
*/
(function () {
  'use strict';

  const switches = document.querySelectorAll('.switch button');
  const loginForm = document.getElementById('form-login');
  const registerForm = document.getElementById('form-register');

  const TIERS = ['新手', '见习', '冒险者', '老练', '传奇'];
  const COLORS = ['#fb7185', '#fbbf24', '#facc15', '#34d399', '#22d3ee'];

  /* ── 视图切换 ── */
  function showView(view) {
    const isReg = view === 'register';
    switches.forEach((b) => {
      const on = b.dataset.view === view;
      b.classList.toggle('is-active', on);
      b.setAttribute('aria-selected', on ? 'true' : 'false');
    });
    loginForm.hidden = isReg;
    registerForm.hidden = !isReg;
    document.querySelectorAll('[data-when]').forEach((el) => {
      el.hidden = el.dataset.when !== view;
    });
    if (location.hash !== '#' + view) history.replaceState(null, '', '#' + view);
  }
  switches.forEach((b) => b.addEventListener('click', () => showView(b.dataset.view)));
  document.querySelectorAll('[data-goto]').forEach((a) =>
    a.addEventListener('click', (e) => { e.preventDefault(); showView(a.dataset.goto); })
  );

  /* ── 分段像素块：构建 + 填充 ── */
  function buildBlocks(el) {
    const n = +el.dataset.blocks || 16;
    const frag = document.createDocumentFragment();
    for (let i = 0; i < n; i++) {
      const b = document.createElement('i');
      frag.appendChild(b);
    }
    el.appendChild(frag);
  }
  function fillBlocks(el, pct, color) {
    if (!el) return;
    const n = el.children.length;
    const on = Math.round((pct / 100) * n);
    if (color) el.style.setProperty('--bar-color', color);
    for (let i = 0; i < n; i++) el.children[i].classList.toggle('on', i < on);
  }

  // 登录态：静态经验条（按 data-pct 一次性填充）
  const loginExp = document.querySelector('.save-login .blocks');
  if (loginExp) { buildBlocks(loginExp); fillBlocks(loginExp, +loginExp.dataset.pct || 0); }

  /* ── 密码显隐 ── */
  document.querySelectorAll('.toggle-pw').forEach((btn) =>
    btn.addEventListener('click', () => {
      const input = btn.parentElement.querySelector('.input');
      const show = input.type === 'password';
      input.type = show ? 'text' : 'password';
      btn.setAttribute('aria-label', show ? '隐藏密码' : '显示密码');
    })
  );

  /* ── 密码强度 → 角色卡 EXP/等级 + 像素块（签名） ── */
  function strength(pw) {
    let s = 0;
    if (pw.length >= 6) s += 18;
    if (pw.length >= 10) s += 16;
    if (pw.length >= 14) s += 14;
    if (/[a-z]/.test(pw)) s += 10;
    if (/[A-Z]/.test(pw)) s += 14;
    if (/[0-9]/.test(pw)) s += 14;
    if (/[^A-Za-z0-9]/.test(pw)) s += 14;
    return Math.max(0, Math.min(100, s));
  }

  const regPass = document.getElementById('rg-pass');
  const regAvatar = document.getElementById('regAvatar');
  const regLv = document.getElementById('regLv');
  const regTier = document.getElementById('regTier');
  const regExpText = document.getElementById('regExpText');
  const regExpBar = document.getElementById('regExpBar');
  const pwBlocks = document.getElementById('pwBlocks');
  const pwNote = document.getElementById('pwNote');

  if (regExpBar) buildBlocks(regExpBar);
  if (pwBlocks) buildBlocks(pwBlocks);

  function renderStrength(pw) {
    const s = strength(pw);
    const idx = Math.min(4, Math.floor(s / 20));
    const lv = idx + 1;
    const color = COLORS[idx];

    if (regAvatar) regAvatar.style.setProperty('--exp', s);
    if (regLv) regLv.textContent = lv;
    if (regTier) regTier.textContent = TIERS[idx] + ' · ' + (pw ? '存档已生成' : '未定职业');
    if (regExpText) regExpText.textContent = s + ' / 100';
    fillBlocks(regExpBar, s);
    fillBlocks(pwBlocks, s, color);
    if (pwNote) pwNote.textContent = 'Lv.' + lv + ' ' + TIERS[idx];
  }
  if (regPass) regPass.addEventListener('input', (e) => renderStrength(e.target.value));
  // demo 钩子：?pw= 预填密码，便于截取"像素块填满"的签名态
  const demoPw = new URLSearchParams(location.search).get('pw');
  if (regPass && demoPw) { regPass.value = demoPw; renderStrength(demoPw); }
  else renderStrength('');

  /* ── 视图初始化（深链） ── */
  showView(/register/i.test(location.hash) ? 'register' : 'login');

  /* ── 模拟提交（设计稿演示） ── */
  function wireSubmit(form) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const btn = form.querySelector('.btn');
      const original = btn.querySelector('.label').textContent;
      btn.disabled = true;
      btn.querySelector('.label').textContent = '处理中…';
      const spin = document.createElement('span');
      spin.className = 'spinner';
      btn.querySelector('.arrow').replaceWith(spin);
      setTimeout(() => {
        btn.disabled = false;
        btn.querySelector('.label').textContent = original;
        const arrow = document.createElement('span');
        arrow.className = 'arrow';
        arrow.textContent = '→';
        spin.replaceWith(arrow);
      }, 1200);
    });
  }
  wireSubmit(loginForm);
  wireSubmit(registerForm);
})();
