/* =====================================================================
   PixelPack · 冒险者履历 DOSSIER · AI 编辑交互演示 (chat.html)
   - SSE 拟流式：用户消息 → tool-line 读取简历 → 打字机回复 + 拟变更卡片
   - 拟变更卡片：接受 → 应用到预览 + 版本号 +1 / 拒绝 → 丢弃
   - 版本历史面板开关
   实际实现：SSE (fetch+ReadableStream) + GLM tool calling + REST accept/deny
   ===================================================================== */

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const thread = $('#thread');

/* ── 拟变更演示数据池（按指令产出不同 diff）── */
const PENDING = {
  quant: {
    tool: 'rewrite_section', target: '履历 #01', group: '1/1',
    del: '主导 PixelPack 前端架构，落地 Vue3 全家桶。设计像素主题设计系统，统一 7 个子模块。',
    add: '主导 PixelPack 前端架构，从 0 到 1 落地 Vue3 + TS，首屏提速 40%。设计像素主题设计系统，统一 7 个子模块视觉语言，复用率提升至 85%。',
    reply: '已读取履历 #01，补了三个量化指标（提速 40% / 复用率 85% / 从 0 到 1）。变更待你确认。',
    apply: () => applyWork1(
      ['主导 PixelPack 前端架构，从 0 到 1 落地 Vue3 + TS，首屏提速 40%。',
       '设计像素主题设计系统，统一 7 个子模块视觉语言，复用率提升至 85%。']),
  },
  en: {
    tool: 'translate', target: '整份简历', group: '1/3',
    del: '全栈工程师 · 像素系统构筑师',
    add: 'Full-Stack Engineer · Pixel Systems Architect',
    reply: '正在把整份简历译为英文，共 3 处变更。先给你看头衔这一条，其余在队列里。',
    apply: () => { $('.r-title').textContent = 'Full-Stack Engineer · Pixel Systems Architect'; },
  },
  page: {
    tool: 'compress', target: '整份简历', group: '1/2',
    del: '技能 · 前端 / 后端 两类共 5 条',
    add: '技能 · 合并为「工程：Vue、TypeScript、FastAPI」一条',
    reply: '为压到一页，我把技能从两类合并为一条、删除冗余项目描述。共 2 处变更，先看技能这条。',
    apply: () => {
      $('.r-skills').innerHTML = '<div class="r-skill-row"><span class="cat">工程</span><span class="tags">Vue、TypeScript、FastAPI</span></div>';
    },
  },
  eval: {
    tool: 'add_entry', target: '自我评价', group: '1/1',
    del: '(无)',
    add: '5 年全栈经验，擅长把游戏化体验融入工具型产品。从架构到像素细节都能独立交付。',
    reply: '我草拟了一段自我评价，放在简历开头。你确认后我会插入到姓名下方。',
    apply: () => {
      const head = $('.r-head');
      if (!head.querySelector('.r-eval')) {
        const e = document.createElement('div');
        e.className = 'r-title r-eval';
        e.style.cssText = 'font-size:12.5px;font-style:normal;margin-top:10px;color:var(--ink);max-width:420px;';
        e.textContent = '5 年全栈经验，擅长把游戏化体验融入工具型产品。从架构到像素细节都能独立交付。';
        head.appendChild(e);
      }
    },
  },
};

/* ── 发送 ── */
function send(text) {
  text = (text || '').trim();
  if (!text) return;
  appendMsg('me', '你', text);
  $('#composer').value = '';

  // 1. 内核运行状态
  const tool = toolLine('NEXA · 读取简历 get_section(timeline)');
  setTimeout(() => {
    tool.innerHTML = '<span class="ok">✓</span> 已读取 · 3 条履历 / 3 类技能';
    setTimeout(() => {
      tool.remove();
      // 2. 匹配指令 → 产出拟变更
      const key = matchIntent(text);
      const p = PENDING[key];
      typeReply(p.reply, () => emitPending(key, p));
    }, 500);
  }, 900);
}

function matchIntent(t) {
  if (/英文|english|翻译|translate/i.test(t)) return 'en';
  if (/一页|精简|压缩|缩短/i.test(t)) return 'page';
  if (/自我|评价|summary|个人简介/i.test(t)) return 'eval';
  return 'quant';
}

/* ── 消息 / 打字机 / 工具行 ── */
function appendMsg(who, name, html) {
  const node = document.createElement('div');
  node.className = 'msg msg--' + who;
  node.innerHTML = `<div class="msg__avatar">${who==='me'?'◈':''}</div>
    <div class="msg__col"><div class="msg__name">${name}</div>
    <div class="msg__bubble">${esc(html)}</div></div>`;
  thread.appendChild(node);
  thread.scrollTop = thread.scrollHeight;
}

function typeReply(full, done) {
  const node = document.createElement('div');
  node.className = 'msg msg--ai';
  node.innerHTML = `<div class="msg__avatar">◈</div>
    <div class="msg__col"><div class="msg__name">NEXA</div>
    <div class="msg__bubble"><span class="tw"></span><span class="cursor"></span></div></div>`;
  thread.appendChild(node);
  const span = node.querySelector('.tw');
  let i = 0;
  const tick = setInterval(() => {
    span.textContent = full.slice(0, ++i);
    thread.scrollTop = thread.scrollHeight;
    if (i >= full.length) { clearInterval(tick); node.querySelector('.cursor')?.remove(); done?.(); }
  }, 28);
}

function toolLine(text) {
  const node = document.createElement('div');
  node.className = 'tool-line';
  node.innerHTML = `<span class="tool-line__dot"></span> ${text}`;
  thread.appendChild(node);
  thread.scrollTop = thread.scrollHeight;
  return node;
}

/* ── 拟变更卡片 ── */
let pendingCnt = 1;
function emitPending(key, p) {
  const node = document.createElement('div');
  node.className = 'pending';
  node.dataset.key = key;
  node.innerHTML = `
    <div class="pending__head">
      <span>⎔ ${p.tool}</span>
      <span class="grp-tag">组 ${p.group}</span>
      <span class="target">${p.target}</span>
    </div>
    <div class="pending__body">
      <div class="diff">
        <div class="diff__row diff__row--del"><div class="diff__sign">−</div>
          <div class="diff__txt"><span class="k">value</span>${esc(p.del)}</div></div>
        <div class="diff__row diff__row--add"><div class="diff__sign">+</div>
          <div class="diff__txt"><span class="k">value</span>${esc(p.add)}</div></div>
      </div>
      <div class="pending__acts">
        <button class="pbtn pbtn--ok" data-act="ok">✓ 接受</button>
        <button class="pbtn pbtn--no" data-act="no">✕ 拒绝</button>
        <span class="pending__meta">基于 r7 · 待确认</span>
      </div>
    </div>`;
  thread.appendChild(node);
  thread.scrollTop = thread.scrollHeight;
}

/* ── 接受 / 拒绝（事件委托）── */
thread.addEventListener('click', e => {
  const card = e.target.closest('.pending'); if (!card) return;
  const key = card.dataset.key;
  const p = PENDING[key]; if (!p) return;

  if (e.target.dataset.act === 'ok') {
    p.apply();            // 应用到预览
    card.classList.add('pending--applied');
    card.querySelector('.pending__head').innerHTML =
      `<span>✓ 已接受 · ${p.tool}</span><span class="target">${p.target}</span>`;
    card.querySelector('.pending__acts').innerHTML =
      `<span class="pending__meta">已应用 · 生成 r${++rev}</span>`;
    bumpRev();
    toast('已接受 · 生成新版本');
  } else if (e.target.dataset.act === 'no') {
    card.style.transition = 'opacity .25s';
    card.style.opacity = '0';
    setTimeout(() => card.remove(), 250);
    toast('已拒绝 · 简历未改动');
  }
});

/* 应用到预览：工作经历 #01 */
function applyWork1(items) {
  const ul = $('#prevWork1')?.querySelector('ul');
  if (ul) ul.innerHTML = items.map(i => `<li>${esc(i)}</li>`).join('');
  const ta = $('#work1desc'); if (ta) ta.value = items.join('\n');
}

/* ── 版本号 ── */
let rev = 7;
function bumpRev() {
  $('#revTag').textContent = 'r' + rev;
  $('#pendingCnt').textContent = '已存档';
  $('#pendingCnt').style.color = 'var(--c-success)';
}

function toast(msg) {
  const t = document.createElement('div');
  t.textContent = msg;
  t.style.cssText = 'position:fixed;left:50%;bottom:30px;transform:translateX(-50%);' +
    'font-family:var(--f-en);font-size:10px;color:var(--c-gold);background:var(--c-card);' +
    'border:2px solid var(--c-gold);padding:8px 14px;z-index:300;box-shadow:3px 3px 0 var(--c-shadow);';
  document.body.appendChild(t);
  setTimeout(() => { t.style.opacity = '0'; t.style.transition = 'opacity .3s'; }, 1400);
  setTimeout(() => t.remove(), 1800);
}

/* ── 版本面板 ── */
$('#btnVersions').addEventListener('click', () => $('#veil').classList.add('is-open'));
$('#btnCloseVeil').addEventListener('click', () => $('#veil').classList.remove('is-open'));
$('#veil').addEventListener('click', e => { if (e.target === $('#veil')) $('#veil').classList.remove('is-open'); });
$$('.revert').forEach(b => b.addEventListener('click', () => toast('回滚请求已提交 · 将生成 r' + (++rev + 1))));

/* ── 内联润色按钮 → 直接产出一条拟变更 ── */
$$('[data-polish]').forEach(b => b.addEventListener('click', () => {
  const p = PENDING.quant;
  typeReply('读取该字段，按量化重写。变更待你确认：', () => emitPending('quant', p));
  thread.scrollTop = thread.scrollHeight;
}));

/* ── 快捷指令 / 发送 ── */
$('.quickchips').addEventListener('click', e => {
  const c = e.target.closest('.qchip'); if (!c) return;
  $('#composer').value = c.textContent; send(c.textContent);
});
$('#btnSend').addEventListener('click', () => send($('#composer').value));
$('#composer').addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send($('#composer').value); }
});

function esc(s) {
  return String(s).replace(/[&<>"]/g, c => ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;' }[c]));
}
