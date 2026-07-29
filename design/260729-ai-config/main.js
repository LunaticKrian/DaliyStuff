/* ════════════════════════════════════════════════════════════
   PixelPack · 260729 AI 配置 / 管理后台 设计稿 · 交互预览
   所有 handler 都做存在性守卫，三个 HTML 共用本脚本。
   ════════════════════════════════════════════════════════════ */
(function () {
  const root = document.documentElement;
  const $ = (id) => document.getElementById(id);

  /* —— 主题切换（深/浅，持久化）—— */
  const stored = localStorage.getItem('pixelpack-theme');
  if (stored) root.setAttribute('data-theme', stored);
  const themeBtn = $('themeBtn');
  if (themeBtn) themeBtn.addEventListener('click', () => {
    const next = root.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
    root.setAttribute('data-theme', next);
    localStorage.setItem('pixelpack-theme', next);
  });

  /* —— 密钥显示/隐藏 —— */
  const toggleKey = $('toggleKey');
  const fKey = $('fKey');
  if (toggleKey && fKey) toggleKey.addEventListener('click', () => {
    fKey.type = fKey.type === 'password' ? 'text' : 'password';
  });

  /* —— Toast —— */
  function toast(msg, kind) {
    kind = kind || 'success';
    let host = document.querySelector('.toast-host');
    if (!host) {
      host = document.createElement('div');
      host.className = 'toast-host';
      host.style.cssText = 'position:fixed;top:18px;right:18px;z-index:300;display:flex;flex-direction:column;gap:.5rem;pointer-events:none';
      document.body.appendChild(host);
    }
    const t = document.createElement('div');
    t.className = 'toast';
    t.style.transition = 'opacity .25s ease, transform .25s ease';
    t.innerHTML = '<svg class="pi sm" style="color:var(--' + (kind === 'error' ? 'danger' : 'success') + ')"><use href="#pi-check"/></svg> ' + msg;
    host.appendChild(t);
    setTimeout(() => {
      t.style.opacity = '0';
      t.style.transform = 'translateY(-6px)';
      setTimeout(() => t.remove(), 260);
    }, 2200);
  }

  /* —— 测试连接：信号塔闪烁 → 出结果 —— */
  const testBtn = $('testBtn');
  const tower = $('signalTower');
  const result = $('testResult');
  const hudLat = $('hudLat');
  if (testBtn) testBtn.addEventListener('click', () => {
    testBtn.disabled = true;
    const old = testBtn.innerHTML;
    testBtn.innerHTML = '<svg class="pi"><use href="#pi-zap"/></svg> 测试中…';
    if (tower) tower.querySelectorAll('i').forEach((b) => b.classList.add('on'));
    if (tower) tower.classList.remove('live'); tower.classList.add('live');
    if (result) result.classList.remove('show');
    setTimeout(() => {
      const ms = 70 + Math.floor(Math.random() * 60);
      if (result) { result.classList.add('show', 'ok'); result.classList.remove('fail'); }
      if (hudLat) hudLat.textContent = '↑ ' + ms + 'ms · 5 段信号 4/5';
      testBtn.disabled = false;
      testBtn.innerHTML = old;
      toast('连接成功 · ' + ms + 'ms');
    }, 1200);
  });

  /* —— 保存 —— */
  const saveBtn = $('saveBtn');
  if (saveBtn) saveBtn.addEventListener('click', () => toast('配置已保存（加密入库）'));

  /* —— 配额编辑模态 —— */
  const quotaModal = $('quotaModal');
  const openModal = () => { if (quotaModal) quotaModal.hidden = false; };
  const closeModal = () => { if (quotaModal) quotaModal.hidden = true; };
  const quotaBtn = $('quotaBtn');
  if (quotaBtn) quotaBtn.addEventListener('click', openModal);
  ['closeQuota', 'cancelQuota'].forEach((id) => { const el = $(id); if (el) el.addEventListener('click', closeModal); });
  if (quotaModal) quotaModal.addEventListener('click', (e) => { if (e.target === quotaModal) closeModal(); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeModal(); });
})();
