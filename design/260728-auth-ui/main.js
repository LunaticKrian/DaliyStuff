/* PixelPack · 登录/注册 交互
   - 视图切换（登录 / 注册）
   - 密码显隐
   - 注册密码强度 → 角色卡 EXP / 等级（签名交互）
   - 模拟提交（loading + 错误演示）—— 仅设计稿用
*/
(function () {
  'use strict';

  const stage = document.querySelector('.stage');
  const switches = document.querySelectorAll('.switch button');
  const loginForm = document.getElementById('form-login');
  const registerForm = document.getElementById('form-register');

  const TIERS = ['新手', '见习', '冒险者', '老练', '传奇'];

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

    // 左面板文案 / 存档卡随视图切换
    document.querySelectorAll('[data-when]').forEach((el) => {
      el.hidden = el.dataset.when !== view;
    });

    if (location.hash !== '#' + view) {
      history.replaceState(null, '', '#' + view);
    }
  }

  switches.forEach((b) => b.addEventListener('click', () => showView(b.dataset.view)));
  document.querySelectorAll('[data-goto]').forEach((a) =>
    a.addEventListener('click', (e) => {
      e.preventDefault();
      showView(a.dataset.goto);
    })
  );

  // 深链：#register / #login
  const initial = /register/i.test(location.hash) ? 'register' : 'login';
  showView(initial);

  /* ── 密码显隐 ── */
  document.querySelectorAll('.toggle-pw').forEach((btn) => {
    btn.addEventListener('click', () => {
      const input = btn.parentElement.querySelector('.input');
      const show = input.type === 'password';
      input.type = show ? 'text' : 'password';
      btn.setAttribute('aria-label', show ? '隐藏密码' : '显示密码');
    });
  });

  /* ── 密码强度 → 角色卡 EXP / 等级（签名） ── */
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
  const COLORS = ['#fb7185', '#fbbf24', '#facc15', '#34d399', '#22d3ee'];

  const regPass = document.getElementById('rg-pass');
  const regAvatar = document.getElementById('regAvatar');
  const regLv = document.getElementById('regLv');
  const regTier = document.getElementById('regTier');
  const regExpText = document.getElementById('regExpText');
  const regExpBar = document.getElementById('regExpBar');
  const pwTrack = document.querySelector('.pw-strength .track > i');
  const pwNote = document.getElementById('pwNote');

  function renderStrength(pw) {
    const s = strength(pw);
    const idx = Math.min(4, Math.floor(s / 20)); // 0..4
    const lv = idx + 1;
    const color = COLORS[idx];

    regAvatar.style.setProperty('--exp', s);
    regLv.textContent = lv;
    regTier.textContent = TIERS[idx] + ' · ' + (pw ? '存档已生成' : '未定职业');
    regExpText.textContent = s + ' / 100';
    regExpBar.style.width = s + '%';

    if (pwTrack) {
      pwTrack.style.width = s + '%';
      pwTrack.style.background = color;
    }
    if (pwNote) pwNote.textContent = 'Lv.' + lv + ' ' + TIERS[idx];
  }
  if (regPass) regPass.addEventListener('input', (e) => renderStrength(e.target.value));
  renderStrength('');

  /* ── 模拟提交（设计稿演示） ── */
  function wireSubmit(form, errMsg) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const err = form.querySelector('.error');
      const btn = form.querySelector('.btn');
      const original = btn.querySelector('.label').textContent;

      err.classList.remove('show');
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
        // 演示：保留表单即可触发错误样式（这里仅展示成功路径的回滚）
      }, 1200);
    });
  }
  wireSubmit(loginForm);
  wireSubmit(registerForm);
})();
