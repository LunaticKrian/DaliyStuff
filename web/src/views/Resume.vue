<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useNotifyStore } from '../stores/notification'
import { useTypewriter } from '../composables/useTypewriter'
import {
  listResumes, getResume, createResume, saveResume, updateResumeMeta,
  createThread, listMessages, chat, inlinePolish,
  listPending, acceptPending, acceptGroup, denyPending,
  listVersions, revertResume, emptyResumeData,
} from '../api/resume'
import { useResumeI18n } from '../composables/useResumeI18n'
import { exportElementToPdf } from '../utils/exportPdf'
import { TEMPLATE_DEFS, templateComponent } from '../components/resume-templates'
import type {
  Resume, ResumeData, Profile,
  PendingChange, PendingGroup, ResumeMessage, ResumeStreamEvent, ChangeDiff, VersionItem,
} from '../types/resume'

const notify = useNotifyStore()

const resume = ref<Resume | null>(null)
const data = ref<ResumeData>(emptyResumeData())
const threadId = ref<number | null>(null)

// 模板 + 当前语言（持久化在 Resume 上；data 始终是当前语言侧的内容）
const lang = ref<'zh' | 'en'>('zh')
const template = ref<string>('pixel')
const labels = useResumeI18n(lang)
const templateOptions = computed(() =>
  TEMPLATE_DEFS.map((t) => ({ key: t.key, label: labels.value.templates[t.key] ?? t.key })),
)
const templateComp = computed(() => templateComponent(template.value))

interface ThreadMsg { role: 'user' | 'assistant'; content: string; streaming?: boolean }
const messages = ref<ThreadMsg[]>([])
const pendingGroups = ref<PendingGroup[]>([])
const versions = ref<VersionItem[]>([])
const showVersions = ref(false)

const composer = ref('')
const streaming = ref(false)
const thinking = ref(false) // tool_read 读取简历中
const threadEl = ref<HTMLElement | null>(null)
const printRoot = ref<HTMLElement | null>(null)

let saveTimer: ReturnType<typeof setTimeout> | null = null

// ── 加载 ──────────────────────────────────────────────────────────────
async function load() {
  try {
    let list = await listResumes()
    let r: Resume
    if (list.length === 0) {
      r = await createResume('我的简历', 'zh')
    } else {
      r = await getResume(list[0].id)
    }
    resume.value = r
    data.value = r.data
    lang.value = (r.lang === 'en' ? 'en' : 'zh')
    template.value = r.template || 'pixel'
    // 线程
    const t = await createThread(r.id)
    threadId.value = t.id
    const msgs = await listMessages(r.id, t.id)
    messages.value = msgs.map((m: ResumeMessage) => ({ role: m.role, content: m.content }))
    if (messages.value.length === 0) {
      messages.value.push({
        role: 'assistant',
        content: '我是你的简历军师 NEXA。说「把工作经历量化」「翻译成英文」或「精简技能」，我会产出变更供你确认——你点头才落库。',
      })
    }
    await reloadPending()
    await reloadVersions()
  } catch (e) {
    notify.error('加载简历失败：' + (e as Error).message)
  }
}

async function reloadPending() {
  if (!resume.value) return
  try {
    pendingGroups.value = await listPending(resume.value.id)
  } catch { /* ignore */ }
}

async function reloadVersions() {
  if (!resume.value) return
  try {
    versions.value = await listVersions(resume.value.id)
  } catch { /* ignore */ }
}

// ── 编辑器：本地修改 + 防抖保存 ────────────────────────────────────────
function scheduleSave() {
  if (saveTimer) clearTimeout(saveTimer)
  saveTimer = setTimeout(async () => {
    if (!resume.value) return
    try {
      const r = await saveResume(resume.value.id, data.value, '手动编辑')
      resume.value = r
      await reloadVersions()
    } catch (e) {
      notify.error('保存失败：' + (e as Error).message)
    }
  }, 900)
}

function setProfile(field: keyof Profile, value: string) {
  data.value.profile[field] = value
  scheduleSave()
}

/** 立即落盘当前编辑（取消防抖，同步等待完成）。仅当有未保存改动时才写，避免空保存污染版本历史。 */
async function flushSave() {
  if (!saveTimer || !resume.value) return
  clearTimeout(saveTimer)
  saveTimer = null
  try {
    const r = await saveResume(resume.value.id, data.value, '手动编辑')
    resume.value = r
    await reloadVersions()
  } catch (e) {
    notify.error('保存失败：' + (e as Error).message)
  }
}

/** 切模板：轻量持久化，不重载 data、不前进版本。 */
async function changeTemplate(key: string) {
  if (!resume.value || key === template.value) return
  template.value = key
  try {
    const r = await updateResumeMeta(resume.value.id, { template: key })
    resume.value = r
  } catch (e) {
    notify.error('切换模板失败：' + (e as Error).message)
  }
}

/** 切语言：先把当前语言侧落盘，再持久化 lang，最后重载为另一侧内容。 */
async function changeLang(next: 'zh' | 'en') {
  if (!resume.value || next === lang.value || streaming.value) return
  await flushSave()
  try {
    const r = await updateResumeMeta(resume.value.id, { lang: next })
    resume.value = r
    lang.value = next
    data.value = r.data // 后端返回新当前语言侧
    await reloadPending()
  } catch (e) {
    notify.error('切换语言失败：' + (e as Error).message)
  }
}

// 通用板块增删（timeline/project/award/skill）
type ListSection = 'timeline' | 'project' | 'skill' | 'award'
function addEntry(section: ListSection) {
  if (section === 'timeline') data.value.timeline.push({ type: 'work', role: '', org: '', date: '', desc: '' })
  else if (section === 'project') data.value.project.push({ name: '', stack: '', desc: '' })
  else if (section === 'skill') data.value.skill.push({ cat: '新分类', tags: [] })
  else if (section === 'award') data.value.award.push({ name: '', issuer: '', year: '' })
  scheduleSave()
}
function removeEntry(section: ListSection, index: number) {
  (data.value[section] as unknown[]).splice(index, 1)
  scheduleSave()
}
function addSkillTag(groupIdx: number, tag: string) {
  const t = tag.trim()
  if (!t) return
  if (!data.value.skill[groupIdx].tags.includes(t)) data.value.skill[groupIdx].tags.push(t)
}
function removeSkillTag(groupIdx: number, tagIdx: number) {
  data.value.skill[groupIdx].tags.splice(tagIdx, 1)
  scheduleSave()
}

// ── AI 对话 ───────────────────────────────────────────────────────────
async function send(text?: string) {
  const content = (text ?? composer.value).trim()
  if (!content || streaming.value || !resume.value || !threadId.value) return
  composer.value = ''
  messages.value.push({ role: 'user', content })
  const assistant = reactive<ThreadMsg>({ role: 'assistant', content: '', streaming: true })
  messages.value.push(assistant)
  streaming.value = true
  await scrollThread()

  // 打字机：吸收后端快速 delta，前端按 ~30ms/字逐字显示。
  // assistant.streaming 维持到队列排空（而非后端结束），让光标在打字期间一直闪。
  let finalized = false
  const typewriter = useTypewriter({
    speedMs: 30,
    onUpdate: (full) => { assistant.content = full; scrollThread() },
    onDone: () => {
      if (finalized) return
      finalized = true
      assistant.streaming = false
      streaming.value = false
      thinking.value = false
      reloadPending()
    },
  })

  await chat(resume.value.id, threadId.value, content, {
    onEvent(e: ResumeStreamEvent) {
      if (e.type === 'delta') {
        typewriter.push(e.text)
      } else if (e.type === 'tool_read') {
        thinking.value = true
      } else if (e.type === 'tool_call') {
        thinking.value = false
        pushPending({
          id: e.pending_id, groupId: e.group_id, tool: e.tool, args: e.args,
          diff: e.diff, baseRevision: e.base_revision, lang: e.lang, status: 'pending', createdAt: '',
        })
      } else if (e.type === 'error') {
        typewriter.push(`\n[错误] ${e.message}`)
      }
      // done/end 不在此收尾，交给打字机排空后 onDone 统一处理
    },
    onError(err) {
      typewriter.push(`\n[错误] ${err.message}`)
    },
  })

  // 后端流结束 → 通知打字机：队列打完后触发 onDone 收尾
  typewriter.finish()
}

function pushPending(c: PendingChange) {
  let g = pendingGroups.value.find((x) => x.groupId === c.groupId)
  if (!g) {
    g = { groupId: c.groupId, baseRevision: c.baseRevision, changes: [] }
    pendingGroups.value.push(g)
  }
  if (!g.changes.find((x) => x.id === c.id)) g.changes.push(c)
}

// 内联润色
async function polish(section: 'profile' | ListSection, index: number, field?: string) {
  if (!resume.value) return
  const instruction = field
    ? `润色 ${section} 的 ${field} 字段，更专业、简洁`
    : `量化并润色这条 ${section} 经历，动词前置、突出成果`
  try {
    notify.info('NEXA 正在润色…')
    const { pending } = await inlinePolish(resume.value.id, { section, index, field: field ?? null, instruction })
    pushPending(pending)
    await reloadPending()
    notify.success('已生成拟变更，请确认')
  } catch (e) {
    notify.error('润色失败：' + (e as Error).message)
  }
}

// 接受 / 拒绝
async function acceptChange(c: PendingChange) {
  if (!resume.value) return
  try {
    const r = await acceptPending(resume.value.id, c.id)
    resume.value = r
    data.value = r.data
    await reloadPending()
    await reloadVersions()
    notify.success('已接受 · 生成 r' + r.revision)
  } catch (e) {
    notify.error('接受失败：' + (e as Error).message)
    await reloadPending()
  }
}
async function acceptWholeGroup(g: PendingGroup) {
  if (!resume.value) return
  try {
    const r = await acceptGroup(resume.value.id, g.groupId)
    resume.value = r
    data.value = r.data
    await reloadPending()
    await reloadVersions()
    notify.success(`已整组接受 ${g.changes.length} 条 · r${r.revision}`)
  } catch (e) {
    notify.error('接受失败：' + (e as Error).message)
    await reloadPending()
  }
}
async function denyChange(c: PendingChange) {
  if (!resume.value) return
  try {
    await denyPending(resume.value.id, c.id)
    await reloadPending()
    notify.info('已拒绝')
  } catch (e) {
    notify.error('操作失败：' + (e as Error).message)
  }
}

// 版本回滚
async function doRevert(revision: number) {
  if (!resume.value) return
  try {
    const r = await revertResume(resume.value.id, revision)
    resume.value = r
    data.value = r.data
    await reloadPending()
    await reloadVersions()
    showVersions.value = false
    notify.success(`已回滚到 r${revision}`)
  } catch (e) {
    notify.error('回滚失败：' + (e as Error).message)
  }
}

// ── 渲染辅助 ──────────────────────────────────────────────────────────
function summarize(val: unknown): string {
  if (val == null) return '(空)'
  if (typeof val === 'string') return val
  if (Array.isArray(val)) return val.join('、')
  const o = val as Record<string, unknown>
  return (o.desc as string) || (o.role as string) || (o.name as string) || (o.cat as string) || JSON.stringify(o)
}
function diffPair(d: ChangeDiff): { before: string; after: string } {
  return { before: summarize(d.before), after: summarize(d.after) }
}
function toolLabel(tool: string): string {
  return ({
    update_profile: '修改字段', add_entry: '新增条目', update_entry: '更新条目', delete_entry: '删除条目',
  } as Record<string, string>)[tool] || tool
}
function sectionLabel(section: string): string {
  return ({ profile: '基本信息', timeline: '履历', project: '项目', skill: '技能', award: '荣誉' } as Record<string, string>)[section] || section
}

const pendingCount = computed(() =>
  pendingGroups.value.reduce((n, g) => n + g.changes.length, 0))

async function scrollThread() {
  await nextTick()
  if (threadEl.value) threadEl.value.scrollTop = threadEl.value.scrollHeight
}

// 导出 PDF：把当前模板的打印渲染（.resume-print）转成满版 A4 PDF（html2canvas + jsPDF），
// 不再走浏览器打印（打印路径无法保证满版无白边）。
const exporting = ref(false)
async function exportPdf() {
  if (exporting.value || !printRoot.value) return
  exporting.value = true
  notify.info('正在生成 PDF…')
  try {
    const name = data.value.profile.name?.trim() || 'resume'
    await exportElementToPdf(printRoot.value, `${name}.pdf`)
    notify.success('PDF 已生成')
  } catch (e) {
    notify.error('导出 PDF 失败：' + (e as Error).message)
  } finally {
    exporting.value = false
  }
}

onMounted(load)
onUnmounted(() => { if (saveTimer) clearTimeout(saveTimer) })
</script>

<template>
  <div class="page resume-page">
    <!-- 顶栏 -->
    <header class="topbar pixel-border">
      <div class="topbar__title">冒险者履历 <small>DOSSIER</small></div>
      <span class="rev" v-if="resume">已存档 · r{{ resume.revision }}</span>
      <span class="spacer"></span>
      <button class="tbtn" @click="showVersions = true">▤ 版本历史</button>
      <button class="tbtn tbtn--gold" @click="exportPdf">⤓ 导出 PDF</button>
    </header>

    <div class="dossier" v-if="resume">
      <!-- 左：编辑器 -->
      <div class="editor">
        <!-- 基本信息 -->
        <section class="panel pixel-border">
          <div class="panel__head"><span class="gem" style="background:var(--pixel-primary)"></span> 冒险者档案</div>
          <div class="panel__body">
            <div class="grid2">
              <label class="fld">姓名
                <div class="row"><input class="inp" :value="data.profile.name" @input="setProfile('name', ($event.target as HTMLInputElement).value)" /><button class="polish" @click="polish('profile', 0, 'name')">✨</button></div>
              </label>
              <label class="fld">头衔
                <div class="row"><input class="inp" :value="data.profile.title" @input="setProfile('title', ($event.target as HTMLInputElement).value)" /><button class="polish" @click="polish('profile', 0, 'title')">✨</button></div>
              </label>
              <label class="fld">所在地<input class="inp" :value="data.profile.location" @input="setProfile('location', ($event.target as HTMLInputElement).value)" /></label>
              <label class="fld">从业年限<input class="inp" :value="data.profile.years" @input="setProfile('years', ($event.target as HTMLInputElement).value)" /></label>
              <label class="fld">电话<input class="inp" :value="data.profile.phone" @input="setProfile('phone', ($event.target as HTMLInputElement).value)" /></label>
              <label class="fld">邮箱<input class="inp" :value="data.profile.email" @input="setProfile('email', ($event.target as HTMLInputElement).value)" /></label>
              <label class="fld">站点<input class="inp" :value="data.profile.site" @input="setProfile('site', ($event.target as HTMLInputElement).value)" /></label>
              <label class="fld">GitHub<input class="inp" :value="data.profile.github" @input="setProfile('github', ($event.target as HTMLInputElement).value)" /></label>
            </div>
          </div>
        </section>

        <!-- 履历 -->
        <section class="panel pixel-border">
          <div class="panel__head"><span class="gem" style="background:var(--pixel-info)"></span> 履历时间线
            <span class="count">{{ data.timeline.length }}</span>
          </div>
          <div class="panel__body">
            <div class="entry" v-for="(it, i) in data.timeline" :key="'tl'+i">
              <div class="entry__bar">
                <select class="inp inp--sm" v-model="it.type" @change="scheduleSave()">
                  <option value="work">工作</option><option value="edu">教育</option>
                </select>
                <input class="inp inp--sm" v-model="it.date" placeholder="2023.03 — 至今" @input="scheduleSave()" />
                <button class="del" @click="removeEntry('timeline', i)">✕</button>
              </div>
              <input class="inp" v-model="it.role" placeholder="职位 / 学位" @input="scheduleSave()" />
              <input class="inp" v-model="it.org" placeholder="机构 / 公司" @input="scheduleSave()" />
              <textarea class="inp" v-model="it.desc" placeholder="职责 / 经历，每行一条" @input="scheduleSave()"></textarea>
              <button class="polish polish--full" @click="polish('timeline', i)">✨ 量化这条经历</button>
            </div>
            <button class="addbtn" @click="addEntry('timeline')">+ 新增履历</button>
          </div>
        </section>

        <!-- 项目 -->
        <section class="panel pixel-border">
          <div class="panel__head"><span class="gem" style="background:var(--pixel-success)"></span> 项目战绩
            <span class="count">{{ data.project.length }}</span>
          </div>
          <div class="panel__body">
            <div class="entry" v-for="(it, i) in data.project" :key="'pj'+i">
              <div class="entry__bar"><span class="idx">PROJ</span><button class="del" style="margin-left:auto" @click="removeEntry('project', i)">✕</button></div>
              <input class="inp" v-model="it.name" placeholder="项目名" @input="scheduleSave()" />
              <input class="inp" v-model="it.stack" placeholder="技术栈" @input="scheduleSave()" />
              <textarea class="inp" v-model="it.desc" placeholder="项目描述 / 成果" @input="scheduleSave()"></textarea>
              <button class="polish polish--full" @click="polish('project', i)">✨ 润色描述</button>
            </div>
            <button class="addbtn" @click="addEntry('project')">+ 新增项目</button>
          </div>
        </section>

        <!-- 技能 -->
        <section class="panel pixel-border">
          <div class="panel__head"><span class="gem" style="background:#b48cff"></span> 技能盘
            <span class="count">{{ data.skill.length }}</span>
          </div>
          <div class="panel__body">
            <div class="entry" v-for="(g, gi) in data.skill" :key="'sk'+gi">
              <div class="entry__bar">
                <input class="inp inp--sm" v-model="g.cat" placeholder="分类" @input="scheduleSave()" />
                <button class="del" style="margin-left:auto" @click="removeEntry('skill', gi)">✕</button>
              </div>
              <div class="chips">
                <span class="chip" v-for="(t, ti) in g.tags" :key="ti">{{ t }}<span class="chipx" @click="removeSkillTag(gi, ti)">✕</span></span>
              </div>
              <input
                class="inp"
                placeholder="+ 输入技能回车添加"
                @keydown.enter.prevent="(e) => { addSkillTag(gi, (e.target as HTMLInputElement).value); (e.target as HTMLInputElement).value=''; scheduleSave() }"
              />
            </div>
            <button class="addbtn" @click="addEntry('skill')">+ 新增技能分类</button>
          </div>
        </section>

        <!-- 荣誉 -->
        <section class="panel pixel-border">
          <div class="panel__head"><span class="gem" style="background:var(--pixel-warning)"></span> 荣誉与证
            <span class="count">{{ data.award.length }}</span>
          </div>
          <div class="panel__body">
            <div class="entry entry--tight" v-for="(it, i) in data.award" :key="'aw'+i">
              <div class="entry__bar">
                <input class="inp inp--sm" v-model="it.name" placeholder="荣誉 / 证书" @input="scheduleSave()" />
                <input class="inp inp--sm" v-model="it.issuer" placeholder="颁发方" @input="scheduleSave()" />
                <input class="inp inp--sm" style="flex:0 0 64px" v-model="it.year" placeholder="年份" @input="scheduleSave()" />
                <button class="del" @click="removeEntry('award', i)">✕</button>
              </div>
            </div>
            <button class="addbtn" @click="addEntry('award')">+ 新增荣誉 / 证书</button>
          </div>
        </section>
      </div>

      <!-- 中：预览 -->
      <div class="stage pixel-border">
        <div class="stage__hint">
          <span><i class="dot"></i> 实时预览</span>
          <span v-if="pendingCount">修订 <b>{{ pendingCount }} 待确认</b></span>
          <span v-else class="ok">已同步</span>
          <div class="stage__tools">
            <div class="tpl-switch">
              <button
                v-for="opt in templateOptions"
                :key="opt.key"
                class="tpl-chip"
                :class="{ active: opt.key === template }"
                @click="changeTemplate(opt.key)"
              >◆ {{ opt.label }}</button>
            </div>
            <div class="lang-switch">
              <button :class="{ active: lang === 'zh' }" @click="changeLang('zh')">中</button>
              <button :class="{ active: lang === 'en' }" @click="changeLang('en')">EN</button>
            </div>
          </div>
        </div>
        <div class="paper">
          <component :is="templateComp" :data="data" :labels="labels" :lang="lang" />
        </div>
      </div>

      <!-- 打印专用渲染：复用当前选中模板，进入 print 模式（关掉不适合纸张的修饰），仅导出 PDF 时显示 -->
      <div ref="printRoot" class="resume-print print-root">
        <component :is="templateComp" :data="data" :labels="labels" :lang="lang" :print="true" />
      </div>

      <!-- 右：AI 对话 -->
      <aside class="chat-drawer">
        <section class="panel pixel-border chat-panel">
          <div class="chat-head">
            <div class="core"></div>
            <div class="core-name">NEXA · 简历军师<small>GLM · 工具调用</small></div>
          </div>

          <div class="thread" ref="threadEl">
            <div v-for="(m, i) in messages" :key="i" class="msg" :class="'msg--' + m.role">
              <div class="msg__avatar">{{ m.role === 'user' ? '◈' : '◉' }}</div>
              <div class="msg__col">
                <div class="msg__name">{{ m.role === 'user' ? '你' : 'NEXA' }}</div>
                <div v-if="m.streaming && !m.content" class="msg__bubble msg__bubble--think">
                  <span class="d"></span><span class="d"></span><span class="d"></span> 思考中 …
                </div>
                <div v-else class="msg__bubble">{{ m.content }}<span class="cursor" v-if="m.streaming"></span></div>
              </div>
            </div>
            <div class="tool-line" v-if="thinking"><span class="d"></span> NEXA · 读取简历中…</div>

            <!-- 拟变更卡片 -->
            <template v-for="g in pendingGroups" :key="g.groupId">
              <div class="pending" v-for="c in g.changes" :key="c.id">
                <div class="pending__head">
                  <span>⎔ {{ toolLabel(c.tool) }}</span>
                  <span class="badge" v-if="g.changes.length > 1">组 {{ g.changes.indexOf(c) + 1 }}/{{ g.changes.length }}</span>
                  <span class="target">{{ sectionLabel(c.diff.section) }}</span>
                </div>
                <div class="pending__body">
                  <div class="diff">
                    <div class="diff__row del" v-if="diffPair(c.diff).before && !c.diff.deleted">
                      <span class="sign">−</span><span class="txt">{{ diffPair(c.diff).before }}</span>
                    </div>
                    <div class="diff__row add" v-if="!c.diff.deleted">
                      <span class="sign">+</span><span class="txt">{{ diffPair(c.diff).after }}</span>
                    </div>
                    <div class="diff__row del" v-if="c.diff.deleted">
                      <span class="sign">−</span><span class="txt">删除：{{ diffPair(c.diff).before }}</span>
                    </div>
                  </div>
                  <div class="pending__acts">
                    <button class="pbtn pbtn--ok" @click="acceptChange(c)">✓ 接受</button>
                    <button class="pbtn pbtn--no" @click="denyChange(c)">✕ 拒绝</button>
                    <button v-if="g.changes.length > 1" class="pbtn pbtn--grp" @click="acceptWholeGroup(g)">整组接受</button>
                    <span class="meta">基于 r{{ c.baseRevision }}</span>
                  </div>
                </div>
              </div>
            </template>
          </div>

          <div class="quickchips">
            <span class="qchip" @click="send('把工作经历量化，突出成果')">把工作经历量化</span>
            <span class="qchip" @click="send('把简历翻译成英文')">翻译成英文</span>
            <span class="qchip" @click="send('精简到一页')">精简到一页</span>
            <span class="qchip" @click="send('帮我补一段自我评价')">补自我评价</span>
          </div>

          <div class="composer">
            <textarea v-model="composer" placeholder="对 NEXA 说点什么…（Enter 发送）"
              @keydown.enter.exact.prevent="send()"></textarea>
            <button class="send" @click="send()" :disabled="streaming">发送 ▶</button>
          </div>
        </section>
      </aside>
    </div>

    <div class="loading" v-else>读取档案中…</div>

    <!-- 版本历史 -->
    <div class="veil" :class="{ 'is-open': showVersions }" @click.self="showVersions = false">
      <div class="versions pixel-border">
        <div class="versions__head">▤ 版本历史 <button class="x" @click="showVersions = false">✕</button></div>
        <div class="ver-item" v-for="v in versions" :key="v.revision"
             :class="{ cur: resume && v.revision === resume.revision }">
          <div class="ver__rev">r{{ v.revision }}<small v-if="resume && v.revision === resume.revision">当前</small></div>
          <div class="ver__info">
            <div class="ver__title">{{ v.summary || '—' }}</div>
            <div class="ver__time">{{ new Date(v.createdAt).toLocaleString() }} · {{ v.source === 'nexa' ? 'NEXA' : '手动' }}</div>
          </div>
          <button class="revert" v-if="!(resume && v.revision === resume.revision)" @click="doRevert(v.revision)">回滚</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.resume-page { padding: 16px; max-width: 1500px; margin: 0 auto; }

/* 顶栏 */
.topbar { display: flex; align-items: center; gap: 12px; padding: 10px 14px; margin-bottom: 16px;
  background: var(--pixel-card-bg); }
.topbar__title { font-size: 15px; letter-spacing: 1.5px; color: var(--pixel-warning, #f5d976); font-weight: 700; }
.topbar__title small { font-size: 9px; color: var(--pixel-info); margin-left: 6px; font-weight: 400; }
.rev { font-size: 11px; color: var(--pixel-success); }
.spacer { flex: 1; }
.tbtn { font-family: inherit; font-size: 11px; color: var(--pixel-text); background: var(--pixel-bg-secondary);
  border: 2px solid var(--pixel-border); box-shadow: 2px 2px 0 var(--pixel-shadow); padding: 6px 11px; cursor: pointer; }
.tbtn:hover { color: var(--pixel-warning, #f5d976); }
.tbtn--gold { color: #20180a; background: #f5d976; border-color: #c9a93f; }
.tbtn--gold:hover { background: #ffe89a; }

/* 三栏 */
.dossier { display: grid; grid-template-columns: 360px 1fr 360px; gap: 14px; align-items: start; }
@media (max-width: 1280px) { .dossier { grid-template-columns: 320px 1fr; } .chat-drawer { grid-column: 1 / -1; } }
@media (max-width: 860px) { .dossier { grid-template-columns: 1fr; } }

.panel { background: var(--pixel-card-bg); }
.panel__head { display: flex; align-items: center; gap: 8px; padding: 8px 12px;
  background: var(--pixel-bg-secondary); font-size: 11px; letter-spacing: 1px; color: var(--pixel-info);
  border-bottom: 2px solid var(--pixel-border); }
.panel__head .gem { width: 10px; height: 10px; transform: rotate(45deg); display: inline-block; }
.panel__head .count { margin-left: auto; color: var(--pixel-text-secondary); font-size: 10px; }
.panel__body { padding: 12px; }

/* 表单 */
.grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.fld { display: flex; flex-direction: column; gap: 3px; font-size: 9px; color: var(--pixel-text-secondary); letter-spacing: 0.5px; text-transform: uppercase; }
.inp { width: 100%; font-family: inherit; font-size: 12px; color: var(--pixel-text);
  background: #141a36; border: 2px solid var(--pixel-border); padding: 6px 8px; outline: none;
  box-shadow: inset 2px 2px 0 rgba(0,0,0,0.4); }
.inp:focus { border-color: var(--pixel-info); }
.inp--sm { padding: 4px 6px; font-size: 11px; }
textarea.inp { resize: vertical; min-height: 48px; }
.row { display: flex; gap: 4px; }
.polish { font-size: 11px; color: var(--pixel-text-secondary); background: var(--pixel-bg-secondary);
  border: 1px solid var(--pixel-border); padding: 0 6px; cursor: pointer; line-height: 1.6; }
.polish:hover { color: var(--pixel-warning, #f5d976); border-color: var(--pixel-warning, #f5d976); }
.polish--full { width: 100%; margin-top: 6px; padding: 5px; font-size: 10px; }

.entry { background: #141a36; border: 2px solid var(--pixel-border); padding: 9px; margin-bottom: 8px; display: flex; flex-direction: column; gap: 5px; }
.entry--tight { padding: 7px; }
.entry__bar { display: flex; gap: 6px; align-items: center; }
.entry__bar .idx { font-size: 9px; color: var(--pixel-warning, #f5d976); }
.del { margin-left: auto; font-size: 11px; color: var(--pixel-text-secondary); background: transparent; border: 1px solid var(--pixel-border); cursor: pointer; padding: 2px 6px; }
.del:hover { color: var(--pixel-accent); border-color: var(--pixel-accent); }
.addbtn { width: 100%; font-family: inherit; font-size: 10px; color: var(--pixel-success);
  background: #141a36; border: 2px dashed var(--pixel-border); padding: 7px; cursor: pointer; }
.addbtn:hover { color: var(--pixel-info); border-color: var(--pixel-info); }

.chips { display: flex; flex-wrap: wrap; gap: 4px; min-height: 22px; }
.chip { font-size: 11px; background: var(--pixel-bg-secondary); border: 1px solid var(--pixel-border); padding: 2px 4px 2px 7px; }
.chipx { color: var(--pixel-text-secondary); cursor: pointer; padding: 0 3px; margin-left: 3px; border-left: 1px solid var(--pixel-border); }
.chipx:hover { color: var(--pixel-accent); }

/* 预览舞台 */
.stage { background: #141a36; padding: 22px; min-height: 600px;
  background-image: linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px);
  background-size: 10px 10px; }
.stage__hint { display: flex; gap: 14px; align-items: center; font-size: 10px; color: var(--pixel-text-secondary); margin-bottom: 14px; }
.stage__hint b { color: var(--pixel-warning, #f5d976); }
.stage__hint .ok { color: var(--pixel-success); }
.stage__hint .muted { margin-left: auto; }
.stage__hint .dot { width: 7px; height: 7px; background: var(--pixel-success); display: inline-block; animation: blk 1.6s steps(2) infinite; }
@keyframes blk { 50% { opacity: 0.25; } }

/* 预览工具条：模板选择 + 语言切换 */
.stage__tools { margin-left: auto; display: flex; align-items: center; gap: 10px; }
.tpl-switch { display: flex; gap: 4px; flex-wrap: wrap; }
.tpl-chip {
  font-family: var(--font-pixel), var(--font-pixel), monospace; font-size: 10px;
  padding: 4px 8px; background: transparent; color: var(--pixel-text-secondary);
  border: 2px solid var(--pixel-border); cursor: pointer; transition: color 0.12s, border-color 0.12s, background 0.12s;
}
.tpl-chip:hover { color: var(--pixel-text); border-color: var(--pixel-info); }
.tpl-chip.active { color: var(--pixel-info); border-color: var(--pixel-info); background: rgba(115, 239, 247, 0.1); box-shadow: 0 2px 0 var(--pixel-info); }
.lang-switch { display: flex; border: 2px solid var(--pixel-border); }
.lang-switch button {
  font-family: var(--font-pixel-en), monospace; font-size: 8px; padding: 4px 7px;
  background: transparent; color: var(--pixel-text-secondary); border: 0; cursor: pointer;
}
.lang-switch button.active { background: var(--pixel-info); color: #062a30; }

/* 简历纸：中立容器，背景/字体交由各模板组件自绘 */
.paper { margin: 0 auto; max-width: 760px; }

/* 打印专用渲染：屏幕上完全不占位，仅导出 PDF 时由 print.css 显示 */
.resume-print { display: none; }
.r-head { display: flex; justify-content: space-between; align-items: flex-end; border-bottom: 2px solid #1d2236; padding-bottom: 12px; }
.r-name { font-size: 28px; font-weight: 700; margin: 0; letter-spacing: -0.5px; }
.r-title { font-style: italic; font-size: 14px; color: #4a5470; margin-top: 3px; }
.r-contact { font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: 9.5px; line-height: 1.7; color: #4a5470; text-align: right; }
.r-contact span { display: block; }
.r-sec { margin-top: 20px; }
.r-sec__title { font-size: 12px; letter-spacing: 2px; text-transform: uppercase; margin: 0 0 10px;
  display: flex; align-items: center; gap: 8px; }
.r-sec__title::after { content: ''; flex: 1; height: 1px; background: #c9b98a; }
.r-sec__title .mark { color: #8a2f3f; font-family: 'JetBrains Mono', ui-monospace, monospace; }
.r-item, .r-proj { margin-bottom: 11px; }
.r-item__top, .r-proj__top { display: flex; justify-content: space-between; gap: 12px; align-items: baseline; }
.r-item__role, .r-proj__name { font-weight: 600; font-size: 14px; }
.r-item__role .at, .r-proj__stack { color: #4a5470; font-weight: 400; }
.r-item__date { font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: 9.5px; color: #4a5470; white-space: nowrap; }
.r-proj__stack { font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: 9px; }
.r-item ul, .r-proj ul { margin: 4px 0 0; padding-left: 16px; }
.r-item li, .r-proj li { font-size: 12.5px; line-height: 1.5; color: #2a3050; }
.r-skills { display: grid; grid-template-columns: 1fr 1fr; gap: 5px 24px; }
.r-skill-row { font-size: 12.5px; display: flex; gap: 8px; }
.r-skill-row .cat { font-weight: 600; min-width: 70px; }
.r-awards { font-size: 12.5px; }
.r-award { display: flex; justify-content: space-between; gap: 12px; padding: 3px 0; border-bottom: 1px dotted #c9b98a; }
.r-award:last-child { border-bottom: none; }
.r-award .yr, .r-award .muted { font-family: 'JetBrains Mono', ui-monospace, monospace; font-size: 10px; color: #4a5470; }

/* 对话抽屉 */
.chat-drawer { min-width: 0; }
.chat-panel { display: flex; flex-direction: column; max-height: calc(100vh - 130px); }
.chat-head { display: flex; align-items: center; gap: 8px; padding: 9px 12px; background: var(--pixel-bg-secondary); border-bottom: 2px solid var(--pixel-border); }
.core { width: 18px; height: 18px; border-radius: 50%; border: 2px solid var(--pixel-info);
  background: radial-gradient(circle at 35% 30%, var(--pixel-info), var(--pixel-primary) 60%, #141a36);
  box-shadow: 0 0 8px rgba(115,239,247,0.5); }
.core-name { font-size: 11px; letter-spacing: 1px; color: var(--pixel-info); }
.core-name small { display: block; font-size: 8px; color: var(--pixel-text-secondary); }
.thread { flex: 1; overflow-y: auto; padding: 12px; display: flex; flex-direction: column; gap: 11px; background: #141a36; }
.msg { display: flex; gap: 8px; }
.msg__avatar { width: 24px; height: 24px; flex: 0 0 24px; display: grid; place-items: center; font-size: 12px;
  background: var(--pixel-bg-secondary); border: 2px solid var(--pixel-border); }
.msg--assistant .msg__avatar { color: var(--pixel-info); border-color: var(--pixel-info); }
.msg__col { min-width: 0; }
.msg__name { font-size: 8px; color: var(--pixel-text-secondary); margin-bottom: 3px; }
.msg__bubble { font-size: 12.5px; line-height: 1.5; color: #ffffff; background: var(--pixel-card-bg); border: 2px solid var(--pixel-border); padding: 8px 10px; white-space: pre-wrap; word-break: break-word; }
.msg--user .msg__bubble { background: var(--pixel-bg-secondary); }
.cursor { display: inline-block; width: 7px; height: 13px; background: var(--pixel-info); vertical-align: -2px; margin-left: 1px; animation: blk 0.8s steps(2) infinite; }
.tool-line { display: flex; align-items: center; gap: 8px; padding: 6px 10px; font-size: 9px; color: var(--pixel-info);
  background: rgba(65,166,246,0.1); border-left: 3px solid var(--pixel-info); }
.tool-line .d { width: 7px; height: 7px; background: var(--pixel-info); display: inline-block; animation: blk 1.2s steps(2) infinite; }

/* 首 token 前的「思考中」三点动画（复用 .d，叠加交错延迟） */
.msg__bubble--think { display: inline-flex; align-items: center; gap: 5px; color: var(--pixel-info); }
.msg__bubble--think .d { animation: thinkblink 1.2s steps(1) infinite; }
.msg__bubble--think .d:nth-child(2) { animation-delay: 0.2s; }
.msg__bubble--think .d:nth-child(3) { animation-delay: 0.4s; }
@keyframes thinkblink { 0%, 100% { opacity: 0.2; } 50% { opacity: 1; } }

/* 拟变更卡片 */
.pending { background: var(--pixel-card-bg); border: 2px solid var(--pixel-border); box-shadow: 3px 3px 0 var(--pixel-shadow); position: relative; padding-left: 10px; }
.pending::before { content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 5px;
  background: repeating-linear-gradient(45deg, var(--pixel-warning) 0 6px, #f5d976 6px 12px); }
.pending__head { display: flex; align-items: center; gap: 8px; padding: 7px 10px; background: var(--pixel-bg-secondary);
  border-bottom: 2px solid var(--pixel-border); font-size: 9px; color: var(--pixel-warning); letter-spacing: 0.5px; }
.pending__head .badge { font-size: 7px; background: var(--pixel-accent); color: var(--pixel-text); padding: 2px 5px; }
.pending__head .target { margin-left: auto; color: var(--pixel-text-secondary); font-size: 9px; }
.pending__body { padding: 9px 10px; }
.diff { display: flex; flex-direction: column; gap: 5px; }
.diff__row { display: flex; gap: 6px; padding: 3px 6px; font-size: 12px; line-height: 1.45; }
.diff__row.del { background: rgba(177,62,83,0.18); color: var(--pixel-text-secondary); }
.diff__row.del .sign { color: var(--pixel-accent); }
.diff__row.add { background: rgba(56,183,100,0.18); }
.diff__row.add .sign { color: var(--pixel-success); }
.diff__row .sign { flex: 0 0 12px; font-weight: 700; }
.pending__acts { display: flex; gap: 6px; align-items: center; margin-top: 9px; padding-top: 8px; border-top: 1px dashed var(--pixel-border); }
.pbtn { font-family: inherit; font-size: 10px; padding: 5px 9px; cursor: pointer; border: 2px solid var(--pixel-border); background: var(--pixel-bg-secondary); color: var(--pixel-text); box-shadow: 2px 2px 0 var(--pixel-shadow); }
.pbtn:active { transform: translate(2px,2px); box-shadow: none; }
.pbtn--ok { color: var(--pixel-success); border-color: var(--pixel-success); }
.pbtn--ok:hover { background: var(--pixel-success); color: #141a36; }
.pbtn--no:hover { color: var(--pixel-accent); border-color: var(--pixel-accent); }
.pbtn--grp { color: var(--pixel-warning, #f5d976); border-color: var(--pixel-warning, #f5d976); }
.pending__acts .meta { margin-left: auto; font-size: 8px; color: var(--pixel-text-secondary); }

.quickchips { display: flex; flex-wrap: wrap; gap: 5px; padding: 8px 12px 0; }
.qchip { font-size: 9px; color: var(--pixel-info); background: #141a36; border: 1px solid var(--pixel-border); padding: 4px 7px; cursor: pointer; }
.qchip:hover { color: var(--pixel-warning, #f5d976); border-color: var(--pixel-warning, #f5d976); }
.composer { display: flex; gap: 8px; padding: 10px 12px; border-top: 2px solid var(--pixel-border); }
.composer textarea { flex: 1; font-family: inherit; font-size: 12px; color: var(--pixel-text); background: #141a36;
  border: 2px solid var(--pixel-border); padding: 7px 9px; resize: none; height: 40px; outline: none; }
.composer textarea:focus { border-color: var(--pixel-info); }
.send { font-family: inherit; font-size: 10px; color: #20180a; background: #f5d976; border: 2px solid #c9a93f; padding: 0 12px; cursor: pointer; box-shadow: 2px 2px 0 var(--pixel-shadow); }
.send:disabled { opacity: 0.5; cursor: not-allowed; }

.loading { padding: 60px; text-align: center; color: var(--pixel-text-secondary); }

/* 版本面板 */
.veil { position: fixed; inset: 0; z-index: 200; background: rgba(10,14,32,0.75); display: none; align-items: center; justify-content: center; }
.veil.is-open { display: flex; }
.versions { width: min(520px, 92vw); max-height: 80vh; overflow-y: auto; background: var(--pixel-card-bg); }
.versions__head { display: flex; align-items: center; padding: 10px 14px; background: var(--pixel-bg-secondary);
  border-bottom: 2px solid var(--pixel-border); font-size: 11px; letter-spacing: 1px; color: var(--pixel-info); }
.versions__head .x { margin-left: auto; cursor: pointer; color: var(--pixel-text-secondary); background: none; border: none; font-size: 16px; }
.ver-item { display: flex; align-items: center; gap: 12px; padding: 11px 14px; border-bottom: 1px solid var(--pixel-border); }
.ver__rev { font-size: 12px; color: var(--pixel-warning, #f5d976); min-width: 40px; }
.ver__rev small { display: block; font-size: 7px; color: var(--pixel-success); }
.ver-item.cur .ver__rev { color: var(--pixel-success); }
.ver__info { flex: 1; min-width: 0; }
.ver__title { font-size: 12px; }
.ver__time { font-size: 8px; color: var(--pixel-text-secondary); }
.revert { font-size: 9px; color: var(--pixel-warning, #f5d976); background: transparent; border: 1px solid var(--pixel-border); padding: 5px 9px; cursor: pointer; }
.revert:hover { border-color: var(--pixel-warning, #f5d976); }
</style>
