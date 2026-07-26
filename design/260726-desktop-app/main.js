/* =====================================================================
   PixelPack · 桌面端设计稿 交互 (data-attribute 驱动，各页按需启用)
   ===================================================================== */
(function () {
  'use strict';

  // —— 像素开关 ——
  document.querySelectorAll('[data-toggle]').forEach(function (t) {
    t.addEventListener('click', function () { t.classList.toggle('toggle--on'); });
  });

  // —— 设置页左导航切换面板 ——
  var navItems = document.querySelectorAll('.nav-item[data-panel]');
  if (navItems.length) {
    navItems.forEach(function (item) {
      item.addEventListener('click', function () {
        var key = item.getAttribute('data-panel');
        document.querySelectorAll('.nav-item').forEach(function (n) { n.classList.remove('active'); });
        item.classList.add('active');
        document.querySelectorAll('.panel').forEach(function (p) {
          p.classList.toggle('active', p.getAttribute('data-panel') === key);
        });
      });
    });
  }

  // —— 全局快捷键捕获格 ——
  var hot = document.querySelector('[data-hotkey]');
  if (hot) {
    hot.addEventListener('click', function () {
      hot.classList.add('hotkey-cell--capture');
      hot.innerHTML = '按下组合键 <span class="caret">▮</span>';
      function onKey(e) {
        e.preventDefault();
        if (e.key === 'Escape') { reset(); return; }
        var parts = [];
        if (e.metaKey)  parts.push(mod('⌘', e));
        if (e.ctrlKey)  parts.push('<span class="keycap">Ctrl</span>');
        if (e.altKey)   parts.push('<span class="keycap">⌥</span>');
        if (e.shiftKey) parts.push('<span class="keycap">⇧</span>');
        var k = (e.key.length === 1 ? e.key.toUpperCase() : e.key);
        parts.push('<span class="keycap">' + k + '</span>');
        hot.classList.remove('hotkey-cell--capture');
        hot.innerHTML = parts.join('');
        window.removeEventListener('keydown', onKey);
      }
      function mod() { return '<span class="keycap">⌘</span>'; }
      function reset() {
        hot.classList.remove('hotkey-cell--capture');
        hot.innerHTML = '<span class="keycap">⌘</span><span class="keycap">⇧</span><span class="keycap">P</span>';
        window.removeEventListener('keydown', onKey);
      }
      window.addEventListener('keydown', onKey);
    });
  }

  // —— 清空缓存（模拟）——
  var clearBtn = document.getElementById('clearCache');
  if (clearBtn) {
    clearBtn.addEventListener('click', function () {
      var fill = document.getElementById('cacheFill');
      var size = document.getElementById('cacheSize');
      if (fill) fill.style.width = '0%';
      if (size) size.textContent = '0.0';
      clearBtn.textContent = '已清空';
      clearBtn.disabled = true;
    });
  }
})();
