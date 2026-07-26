/* =====================================================================
   PixelPack · 冒险者履历 DOSSIER V1.0 设计稿 · 交互
   - 单一 state 驱动：编辑器表单 ↔ 预览双向同步
   - 履历/项目/技能/荣誉 重复项增删
   - 模式切换 PRO / 公會(Dossier) · 打印导出 PDF
   实际实现：Vue 3 + Pinia + REST；本稿为纯前端 Mock 演示
   ===================================================================== */

/* ── 初始示例数据（演示用，可「重置」恢复）── */
const SEED = {
  profile: {
    name: 'Krian',
    title: '全栈工程师 · 像素系统构筑师',
    location: '上海',
    years: '5 年',
    phone: '+86 138-0000-0000',
    email: 'krian@pixelpack.dev',
    site: 'pixelpack.dev',
    github: 'github.com/krian',
  },
  timeline: [
    { type: 'work', role: '高级前端工程师', org: 'PixelPack Studio', date: '2023.03 — 至今',
      desc: '主导 PixelPack 像素 RPG 管理系统前端架构，从 0 到 1 落地 Vue 3 + TS 全家桶。\n设计像素主题设计系统，统一 7 个子模块视觉语言。' },
    { type: 'work', role: '前端工程师', org: '某出海科技公司', date: '2021.07 — 2023.02',
      desc: '负责数据可视化平台，ECharts 复杂图表性能优化，首屏提速 40%。' },
    { type: 'edu', role: '计算机科学与技术 · 学士', org: '某大学', date: '2017.09 — 2021.06',
      desc: 'GPA 3.8/4.0 · 校 ACM 集训队队员。' },
  ],
  project: [
    { name: 'PixelPack', stack: 'Vue3 · TS · FastAPI · ECharts',
      desc: 'RPG 风个人物品/任务/冒险日志管理系统，含世界地图情报推送与角色系统。' },
    { name: 'airise-gateway', stack: 'Go · 反向代理 · 多租户',
      desc: '统一网关服务，承接多项目域名与文件代理，替代原有 Nginx 方案。' },
  ],
  skill: [
    { cat: '前端', tags: ['Vue', 'TypeScript', 'Vite', 'Pinia', 'CSS 像素动画'] },
    { cat: '后端', tags: ['Python', 'FastAPI', 'SQLAlchemy', 'Go'] },
    { cat: '工程', tags: ['Docker', 'CI/CD', '设计系统'] },
  ],
  award: [
    { name: '某黑客松 · 最佳体验奖', issuer: '主办方', year: '2024' },
    { name: 'PMP 项目管理认证', issuer: 'PMI', year: '2022' },
  ],
};

/* 深拷贝种子 */
let state = JSON.parse(JSON.stringify(SEED));
let mode = 'pro';

/* ── 小工具 ── */
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;' }[c]));
const nl2br = s => esc(s).replace(/\n/g, '<br>');
const bullets = s => (s || '').split('\n').map(l => l.trim()).filter(Boolean);

/* ─────────────────────────────────────────────
   编辑器：渲染表单（profile 直接绑定，列表项渲染）
   ───────────────────────────────────────────── */
function renderProfileForm() {
  $$('[data-bind^="profile."]').forEach(el => {
    const key = el.dataset.bind.split('.')[1];
    el.value = state.profile[key] ?? '';
  });
}

function renderTimelineEditor() {
  const wrap = $('#listTimeline');
  wrap.innerHTML = state.timeline.map((it, i) => `
    <div class="entry" data-i="${i}">
      <div class="entry__bar">
        <span class="entry__idx">#${String(i + 1).padStart(2, '0')}</span>
        <select class="input entry__type-select" style="flex:0 0 88px; padding:4px 6px;">
          <option value="work" ${it.type==='work'?'selected':''}>工作</option>
          <option value="edu"  ${it.type==='edu' ?'selected':''}>教育</option>
        </select>
        <input class="input entry__date" value="${esc(it.date)}" placeholder="2023.03 — 至今" style="flex:1; padding:5px 7px;">
        <button class="entry__del" data-del="timeline:${i}">✕</button>
      </div>
      <div class="field"><input class="input entry__role" value="${esc(it.role)}" placeholder="职位 / 学位"></div>
      <div class="field"><input class="input entry__org" value="${esc(it.org)}" placeholder="机构 / 公司" style="margin-top:6px;"></div>
      <textarea class="input entry__desc" placeholder="职责 / 经历，每行一条">${esc(it.desc)}</textarea>
    </div>`).join('');
  $('#cntTimeline').textContent = state.timeline.length;
}

function renderProjectEditor() {
  const wrap = $('#listProject');
  wrap.innerHTML = state.project.map((it, i) => `
    <div class="entry" data-i="${i}">
      <div class="entry__bar">
        <span class="entry__idx">PROJ ${String(i + 1).padStart(2, '0')}</span>
        <button class="entry__del" data-del="project:${i}" style="margin-left:auto">✕</button>
      </div>
      <div class="field"><input class="input p__name" value="${esc(it.name)}" placeholder="项目名"></div>
      <div class="field"><input class="input p__stack" value="${esc(it.stack)}" placeholder="技术栈" style="margin-top:6px;"></div>
      <textarea class="input p__desc" placeholder="项目描述 / 成果">${esc(it.desc)}</textarea>
    </div>`).join('');
  $('#cntProject').textContent = state.project.length;
}

function renderSkillEditor() {
  const wrap = $('#listSkill');
  wrap.innerHTML = state.skill.map((g, i) => `
    <div class="skill-cat" data-i="${i}">
      <div class="skill-cat__head">
        <input class="input sk__cat" value="${esc(g.cat)}" placeholder="分类" style="flex:0 0 90px;">
        <input class="input sk__add" placeholder="+ 输入技能回车添加" style="flex:1;">
        <button class="entry__del" data-del="skill:${i}">✕</button>
      </div>
      <div class="skill-tags">
        ${g.tags.map((t, j) => `<span class="skill-chip">${esc(t)}<span class="x" data-skillx="${i}:${j}">✕</span></span>`).join('') || '<span style="color:var(--c-text-dim);font-size:10px;">无技能</span>'}
      </div>
    </div>`).join('') + `
    <button class="addbtn" data-add="skill">+ 新增技能分类</button>`;
  $('#cntSkill').textContent = state.skill.length;
}

function renderAwardEditor() {
  const wrap = $('#listAward');
  wrap.innerHTML = state.award.map((it, i) => `
    <div class="entry" data-i="${i}" style="padding:7px 9px;">
      <div class="entry__bar" style="margin-bottom:0;">
        <input class="input a__name" value="${esc(it.name)}" placeholder="荣誉 / 证书名" style="flex:1;">
        <input class="input a__issuer" value="${esc(it.issuer)}" placeholder="颁发方" style="flex:0 0 110px;">
        <input class="input a__year" value="${esc(it.year)}" placeholder="年份" style="flex:0 0 64px;">
        <button class="entry__del" data-del="award:${i}">✕</button>
      </div>
    </div>`).join('');
  $('#cntAward').textContent = state.award.length;
}

function renderEditor() {
  renderProfileForm();
  renderTimelineEditor();
  renderProjectEditor();
  renderSkillEditor();
  renderAwardEditor();
}

/* ─────────────────────────────────────────────
   预览：从 state 渲染简历纸
   ───────────────────────────────────────────── */
function renderPreview() {
  const p = state.profile;

  // 头部姓名 / 头衔
  $('[data-view="profile.name"]').textContent = p.name || '姓名';
  $('[data-view="profile.title"]').textContent = p.title || '';

  // 联系方式
  const lines = [
    p.location && `⚲ ${p.location}${p.years ? ' · ' + p.years : ''}`,
    p.phone && `☏ ${p.phone}`,
    p.email && `✉ ${p.email}`,
    p.site && `<a href="#">↗ ${p.site}</a>`,
    p.github && `<a href="#">⌥ ${p.github}</a>`,
  ].filter(Boolean);
  $('#rContact').innerHTML = lines.map(l => `<span>${l}</span>`).join('');

  // 履历
  $('#rTimeline').innerHTML = state.timeline.length
    ? state.timeline.map(it => `
        <div class="r-item">
          <div class="r-item__top">
            <div class="r-item__role">${esc(it.role)}${it.org ? ` <span class="at">· ${esc(it.org)}</span>` : ''}</div>
            <div class="r-item__date">${esc(it.date)}</div>
          </div>
          ${bullets(it.desc).length ? `<ul>${bullets(it.desc).map(b => `<li>${esc(b)}</li>`).join('')}</ul>` : ''}
        </div>`).join('')
    : '<div class="r-empty">尚无履历，在左侧添加教育或工作经历。</div>';

  // 项目
  $('#rProject').innerHTML = state.project.length
    ? state.project.map(it => `
        <div class="r-proj">
          <div class="r-proj__top">
            <div class="r-proj__name">${esc(it.name)}</div>
            <div class="r-proj__stack">${esc(it.stack)}</div>
          </div>
          ${bullets(it.desc).length ? `<ul>${bullets(it.desc).map(b => `<li>${esc(b)}</li>`).join('')}</ul>` : ''}
        </div>`).join('')
    : '<div class="r-empty">尚无项目，在左侧添加你的战绩。</div>';

  // 技能
  $('#rSkills').innerHTML = state.skill.length
    ? state.skill.map(g => `
        <div class="r-skill-row">
          <span class="cat">${esc(g.cat)}</span>
          <span class="tags">${g.tags.length ? g.tags.map(t => esc(t)).join('、') : '—'}</span>
        </div>`).join('')
    : '<div class="r-empty" style="grid-column:1/-1">尚无技能分类。</div>';

  // 荣誉
  $('#rAwards').innerHTML = state.award.length
    ? state.award.map(a => `
        <div class="r-award">
          <span>${esc(a.name)}${a.issuer ? ` · <span style="color:var(--ink-soft)">${esc(a.issuer)}</span>` : ''}</span>
          <span class="yr">${esc(a.year)}</span>
        </div>`).join('')
    : '<div class="r-empty">尚无荣誉或证书。</div>';
}

function render() { renderEditor(); renderPreview(); }

/* ─────────────────────────────────────────────
   事件绑定：表单 → state（实时）
   ───────────────────────────────────────────── */
function bindEditorEvents() {
  const root = $('.editor');

  // profile 文本输入
  root.addEventListener('input', e => {
    const t = e.target;
    if (t.dataset.bind?.startsWith('profile.')) {
      state.profile[t.dataset.bind.split('.')[1]] = t.value;
      renderPreview();
    }
  });

  // 履历条目
  $('#listTimeline').addEventListener('input', e => {
    const entry = e.target.closest('.entry'); if (!entry) return;
    const i = +entry.dataset.i, it = state.timeline[i]; if (!it) return;
    if (e.target.classList.contains('entry__type-select')) it.type = e.target.value;
    else if (e.target.classList.contains('entry__date')) it.date = e.target.value;
    else if (e.target.classList.contains('entry__role')) it.role = e.target.value;
    else if (e.target.classList.contains('entry__org')) it.org = e.target.value;
    else if (e.target.classList.contains('entry__desc')) it.desc = e.target.value;
    renderPreview();
  });

  // 项目条目
  $('#listProject').addEventListener('input', e => {
    const entry = e.target.closest('.entry'); if (!entry) return;
    const i = +entry.dataset.i, it = state.project[i]; if (!it) return;
    if (e.target.classList.contains('p__name')) it.name = e.target.value;
    else if (e.target.classList.contains('p__stack')) it.stack = e.target.value;
    else if (e.target.classList.contains('p__desc')) it.desc = e.target.value;
    renderPreview();
  });

  // 荣誉条目
  $('#listAward').addEventListener('input', e => {
    const entry = e.target.closest('.entry'); if (!entry) return;
    const i = +entry.dataset.i, it = state.award[i]; if (!it) return;
    if (e.target.classList.contains('a__name')) it.name = e.target.value;
    else if (e.target.classList.contains('a__issuer')) it.issuer = e.target.value;
    else if (e.target.classList.contains('a__year')) it.year = e.target.value;
    renderPreview();
  });

  // 技能分类名 / 标签删除 / 回车添加
  $('#listSkill').addEventListener('input', e => {
    const cat = e.target.closest('.skill-cat'); if (!cat) return;
    const i = +cat.dataset.i, g = state.skill[i]; if (!g) return;
    if (e.target.classList.contains('sk__cat')) { g.cat = e.target.value; renderPreview(); }
  });
  $('#listSkill').addEventListener('keydown', e => {
    if (e.key !== 'Enter') return;
    const inp = e.target.closest('.sk__add'); if (!inp) return;
    e.preventDefault();
    const cat = inp.closest('.skill-cat');
    const g = state.skill[+cat.dataset.i]; if (!g) return;
    const v = inp.value.trim(); if (!v) return;
    g.tags.push(v); inp.value = '';
    renderSkillEditor(); renderPreview();
    cat.querySelector('.sk__add')?.focus();
  });
  $('#listSkill').addEventListener('click', e => {
    const x = e.target.closest('[data-skillx]'); if (!x) return;
    const [i, j] = x.dataset.skillx.split(':').map(Number);
    state.skill[i].tags.splice(j, 1);
    renderSkillEditor(); renderPreview();
  });

  // 删除条目
  root.addEventListener('click', e => {
    const del = e.target.closest('[data-del]'); if (!del) return;
    const [key, i] = del.dataset.del.split(':');
    const map = { timeline: state.timeline, project: state.project, skill: state.skill, award: state.award };
    if (map[key]) { map[key].splice(+i, 1); render(); }
  });

  // 新增按钮（含动态生成的 skill addbtn）
  root.addEventListener('click', e => {
    const add = e.target.closest('[data-add]'); if (!add) return;
    const key = add.dataset.add;
    if (key === 'timeline') state.timeline.unshift({ type: 'work', role: '', org: '', date: '', desc: '' });
    else if (key === 'project') state.project.unshift({ name: '', stack: '', desc: '' });
    else if (key === 'skill') state.skill.push({ cat: '新分类', tags: [] });
    else if (key === 'award') state.award.unshift({ name: '', issuer: '', year: '' });
    render();
  });
}

/* ── 顶栏：模式 / 重置 / 打印 ── */
function bindToolbar() {
  $('#modeSeg').addEventListener('click', e => {
    const b = e.target.closest('button[data-mode]'); if (!b) return;
    mode = b.dataset.mode;
    $$('#modeSeg button').forEach(x => x.classList.toggle('is-on', x === b));
    $('#paper').classList.toggle('paper--pro', mode === 'pro');
    $('#hintMode').textContent = mode === 'pro' ? 'PRO · A4' : '公會 · A4';
  });

  $('#btnReset').addEventListener('click', () => {
    state = JSON.parse(JSON.stringify(SEED));
    render();
  });

  $('#btnPrint').addEventListener('click', () => window.print());
}

/* ── 启动 ── */
document.addEventListener('DOMContentLoaded', () => {
  bindEditorEvents();
  bindToolbar();
  render();
});
