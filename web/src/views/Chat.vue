<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useNotifyStore } from '../stores/notification'
import { listSessions, createSession, listMessages, deleteSession } from '../api/chat'
import { streamChatMessage } from '../utils/sse'
import { useTypewriter } from '../composables/useTypewriter'
import type { ChatSession, ChatMessage, CreatedTask } from '../types/chat'
import { CATEGORY_ICONS, CATEGORY_LABELS, CATEGORY_COLORS, type TaskCategory } from '../types/task'

const notify = useNotifyStore()
const router = useRouter()

const sessions = ref<ChatSession[]>([])
const activeId = ref<number | null>(null)
const messages = ref<ChatMessage[]>([])
const loading = ref(false)

const input = ref('')
const sending = ref(false)
const streamText = ref('')
const toolActive = ref(false)
const turnTasks = ref<CreatedTask[]>([])

const threadEl = ref<HTMLElement | null>(null)

async function scrollDown() {
  await nextTick()
  if (threadEl.value) threadEl.value.scrollTop = threadEl.value.scrollHeight
}

async function loadSessions() {
  sessions.value = await listSessions()
}

async function selectSession(id: number) {
  if (sending.value) return
  activeId.value = id
  loading.value = true
  try {
    messages.value = await listMessages(id)
    await scrollDown()
  } catch {
    notify.error('加载对话失败')
  } finally {
    loading.value = false
  }
}

async function startNewChat() {
  if (sending.value) return
  const s = await createSession()
  sessions.value.unshift(s)
  await selectSession(s.id)
}

async function ensureSession() {
  if (sessions.value.length === 0) {
    await startNewChat()
  } else {
    await selectSession(sessions.value[0].id)
  }
}

async function onRemoveSession(id: number) {
  if (sending.value) return
  if (!window.confirm('删除该对话？')) return
  await deleteSession(id)
  sessions.value = sessions.value.filter((s) => s.id !== id)
  if (activeId.value === id) {
    if (sessions.value.length) await selectSession(sessions.value[0].id)
    else { activeId.value = null; messages.value = [] }
  }
  notify.success('已删除')
}

async function send() {
  const content = input.value.trim()
  if (!content || sending.value || !activeId.value) return

  // 本地立即渲染用户消息
  messages.value.push({
    id: Date.now(), session_id: activeId.value, role: 'user',
    content, meta: null, created_at: new Date().toISOString(),
  })
  input.value = ''
  sending.value = true
  streamText.value = ''
  toolActive.value = false
  turnTasks.value = []
  await scrollDown()

  // fullRaw 累积后端全部 delta（用于落库的正式消息）；
  // 打字机驱动 streamText 做逐字显示，两者解耦。
  let fullRaw = ''
  let errored = false
  let finalized = false

  const typewriter = useTypewriter({
    speedMs: 30,
    onUpdate: (full) => { streamText.value = full; scrollDown() },
    onDone: finalize,
  })

  function finalize() {
    if (finalized) return
    finalized = true
    // 把本轮助手回复落为正式消息（用完整原文，而非打字机里可能未排空的部分）
    const finalText = fullRaw.trim() || (errored ? '(生成失败)' : '(无回复)')
    messages.value.push({
      id: Date.now() + 1, session_id: activeId.value!, role: 'assistant',
      content: finalText, meta: { tasks_created: turnTasks.value.length },
      created_at: new Date().toISOString(),
    })

    sending.value = false
    streamText.value = ''
    toolActive.value = false
    turnTasks.value = []
    scrollDown()
    // 刷新会话列表（标题/预览/计数）
    loadSessions().catch(() => {})
  }

  await streamChatMessage(activeId.value, content, {
    onEvent(e) {
      if (e.type === 'delta') {
        fullRaw += e.text
        typewriter.push(e.text)
      } else if (e.type === 'tool') {
        toolActive.value = true
      } else if (e.type === 'task_created') {
        turnTasks.value.push(e.task)
        notify.info(`✦ 新任务：${e.task.title}`)
        scrollDown()
      } else if (e.type === 'error') {
        errored = true
        notify.error(e.message || '生成失败')
      } else if (e.type === 'end') {
        // 收尾
      }
    },
    onError(err) {
      errored = true
      notify.error(err.message || '网络错误')
    },
  })

  // 后端流结束 → 通知打字机：队列排空后触发 onDone 完成收尾
  typewriter.finish()
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    send()
  }
}

function catMeta(cat: string) {
  const c = (cat as TaskCategory) || 'other'
  return { icon: CATEGORY_ICONS[c] ?? '◆', label: CATEGORY_LABELS[c] ?? cat, color: CATEGORY_COLORS[c] ?? '#b48cff' }
}

onMounted(async () => {
  try {
    await loadSessions()
    await ensureSession()
  } catch {
    notify.error('初始化对话失败')
  }
})
</script>

<template>
  <div class="chat-page animate-fade-in">
    <div class="c-layout">

      <!-- ====== 会话侧栏 ====== -->
      <aside class="c-sidebar">
        <button class="new-btn" :disabled="sending" @click="startNewChat">+ 新对话</button>
        <div class="session-list">
          <div
            v-for="s in sessions"
            :key="s.id"
            class="session-item pixel-border"
            :class="{ active: s.id === activeId, disabled: sending }"
            @click="selectSession(s.id)"
          >
            <div class="si-title">{{ s.title }}</div>
            <div class="si-meta">
              <span>{{ s.message_count }} 条</span>
              <button class="si-del" title="删除" @click.stop="onRemoveSession(s.id)">✕</button>
            </div>
          </div>
          <div v-if="sessions.length === 0" class="empty-mini">暂无对话</div>
        </div>
      </aside>

      <!-- ====== 对话主区 ====== -->
      <section class="c-main pixel-border">
        <header class="c-header">
          <div class="c-title">
            <span class="core-glyph">◉</span>
            <span class="c-name">NEXA</span>
            <span class="c-sub">// 任务生成内核</span>
          </div>
          <div class="c-status">
            <button class="goto-quests" @click="router.push('/quests')">委托大厅 ▶</button>
            <span class="dot" :class="{ busy: sending }"></span>
            <span>{{ sending ? '运行中' : '在线' }}</span>
          </div>
        </header>

        <div ref="threadEl" class="c-thread">
          <!-- 欢迎语 -->
          <div v-if="messages.length === 0 && !sending" class="welcome">
            <div class="welcome-glyph">◉</div>
            <div class="welcome-text">链路已建立。描述你今天的学习或工作计划，我会拆成任务写入清单。</div>
            <div class="welcome-hint">例如：今天考研冲刺，上午复习高数第三章，下午做英语阅读 2 篇并背 50 个单词。</div>
          </div>

          <div
            v-for="m in messages"
            :key="m.id"
            class="msg"
            :class="m.role"
          >
            <div class="msg-av">{{ m.role === 'user' ? '◈' : '◉' }}</div>
            <div class="msg-col">
              <div class="msg-name">{{ m.role === 'user' ? '你' : 'NEXA' }}</div>
              <div class="msg-bubble">{{ m.content }}</div>
            </div>
          </div>

          <!-- 流式进行中的助手消息 -->
          <div v-if="sending" class="msg assistant">
            <div class="msg-av">◉</div>
            <div class="msg-col">
              <div class="msg-name">NEXA</div>
              <div v-if="!toolActive && !streamText" class="think-line">
                <span class="td"></span><span class="td"></span><span class="td"></span> 思考中 …
              </div>
              <div v-if="toolActive && !streamText" class="tool-line"><span class="tdot"></span> 内核运行中 · 生成任务 …</div>
              <div v-if="turnTasks.length" class="summon-list">
                <div v-for="(t, i) in turnTasks" :key="i" class="summon">
                  <span class="s-plus">▸ TASK</span>
                  <span class="s-gem" :style="{ background: catMeta(t.category).color }">{{ catMeta(t.category).icon }}</span>
                  <span class="s-title">{{ t.title }}</span>
                  <span class="s-exp">+{{ t.exp_reward }}</span>
                </div>
              </div>
              <div v-if="streamText" class="msg-bubble streaming">{{ streamText }}<span class="cursor"></span></div>
            </div>
          </div>
        </div>

        <footer class="c-compose">
          <textarea
            v-model="input"
            class="c-input"
            rows="2"
            placeholder="描述你今天的学习或工作计划…  (Enter 发送 / Shift+Enter 换行)"
            :disabled="sending"
            @keydown="onKeydown"
          ></textarea>
          <button class="c-send" :disabled="sending || !input.trim()" @click="send">
            {{ sending ? '生成中…' : '发送 ▶' }}
          </button>
        </footer>
        <div class="c-foot-hint">// NEXA 会把计划拆成任务并直接写入「委托大厅」清单</div>
      </section>
    </div>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&display=swap');

/* ═══════ 本页令牌：--pixel-* 重映射为高级深色（浅色自适应）═══════ */
.chat-page {
  --pixel-bg: #0b0d14;
  --pixel-bg-secondary: #14171f;
  --pixel-card-bg: rgba(255, 255, 255, 0.045);
  --pixel-border: rgba(255, 255, 255, 0.09);
  --pixel-primary: #22d3ee;
  --pixel-accent: #fb7185;
  --pixel-warning: #fbbf24;
  --pixel-success: #34d399;
  --pixel-info: #38bdf8;
  --pixel-text: #f4f6fb;
  --pixel-text-secondary: #9aa3b2;
  --pixel-shadow: rgba(0, 0, 0, 0.5);
  --d-grad: linear-gradient(135deg, #818cf8 0%, #7c5cff 40%, #22d3ee 100%);
  --d-radius: 14px;
  --d-radius-sm: 10px;
  --d-shadow-sm: 0 4px 14px -8px rgba(0, 0, 0, .6);
  --d-shadow: 0 18px 44px -22px rgba(0, 0, 0, .7);
  --d-f-display: 'Space Grotesk', 'PingFang SC', system-ui, sans-serif;
  --d-f-body: 'Inter', 'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif;
  --d-f-mono: 'JetBrains Mono', ui-monospace, monospace;

  min-height: 100%;
  font-family: var(--d-f-body);
  color: var(--pixel-text);
}
[data-theme="light"] .chat-page {
  --pixel-bg: #f4f5fa;
  --pixel-bg-secondary: #eef0f7;
  --pixel-card-bg: rgba(17, 20, 40, 0.04);
  --pixel-border: rgba(17, 20, 40, 0.12);
  --pixel-primary: #0891b2;
  --pixel-accent: #e11d48;
  --pixel-warning: #d97706;
  --pixel-success: #059669;
  --pixel-info: #0284c7;
  --pixel-text: #0f1326;
  --pixel-text-secondary: #4b5568;
  --pixel-shadow: rgba(17, 20, 40, .15);
  --d-shadow-sm: 0 4px 14px -8px rgba(17, 20, 40, .2);
  --d-shadow: 0 18px 44px -22px rgba(17, 20, 40, .24);
}

.chat-page { min-height: 100%; }
.c-layout { display: grid; grid-template-columns: 220px 1fr; gap: 16px; height: calc(100vh - 140px); min-height: 520px; }

/* ===== Sidebar ===== */
.c-sidebar { display: flex; flex-direction: column; gap: 10px; min-height: 0; }
.new-btn { font-family: var(--d-f-body); font-weight: 700; font-size: 13px; padding: 10px; border: 0; border-radius: var(--d-radius-sm); cursor: pointer; color: #0a0b10; background: var(--d-grad); box-shadow: 0 8px 22px -12px rgba(99, 102, 241, .8); transition: transform .15s ease, box-shadow .2s ease; }
.new-btn:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 12px 26px -10px rgba(99, 102, 241, .95); }
.new-btn:disabled { opacity: .5; cursor: default; }
[data-theme="light"] .new-btn { color: #fff; }

.session-list { display: flex; flex-direction: column; gap: 7px; overflow-y: auto; min-height: 0; }
.session-item { background: var(--pixel-card-bg); backdrop-filter: blur(10px); border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); padding: 9px 11px; cursor: pointer; transition: border-color .15s ease, background .15s ease; }
.session-item:hover { border-color: var(--pixel-info); background: var(--pixel-bg-secondary); }
.session-item.active { border-color: var(--pixel-info); background: rgba(56, 189, 248, .08); }
.session-item.disabled { opacity: .6; cursor: default; }
.si-title { font-family: var(--d-f-body); font-size: 13px; font-weight: 500; color: var(--pixel-text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.si-meta { display: flex; justify-content: space-between; align-items: center; margin-top: 4px; font-family: var(--d-f-mono); font-size: 10px; color: var(--pixel-text-secondary); }
.si-del { background: transparent; border: 1px solid var(--pixel-border); border-radius: 6px; color: var(--pixel-text-secondary); cursor: pointer; font-size: 10px; width: 20px; height: 20px; display: inline-flex; align-items: center; justify-content: center; line-height: 1; transition: border-color .15s ease, color .15s ease; }
.si-del:hover { border-color: var(--pixel-accent); color: var(--pixel-accent); }
.empty-mini { font-size: 12px; color: var(--pixel-text-secondary); padding: 14px; text-align: center; opacity: .7; }

/* ===== Main ===== */
.c-main { background: var(--pixel-card-bg); backdrop-filter: blur(10px); border: 1px solid var(--pixel-border); border-radius: var(--d-radius); box-shadow: var(--d-shadow-sm); display: flex; flex-direction: column; min-height: 0; position: relative; overflow: hidden; }

.c-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 11px 15px; border-bottom: 1px solid var(--pixel-border); }
.c-title { display: flex; align-items: center; gap: 9px; min-width: 0; }
.core-glyph { color: var(--pixel-info); font-size: 15px; text-shadow: 0 0 10px rgba(56, 189, 248, .5); animation: corepulse 2.4s ease-in-out infinite; }
@keyframes corepulse { 50% { opacity: .55; } }
.c-name { font-family: var(--d-f-display); font-size: 14px; font-weight: 700; color: var(--pixel-text); letter-spacing: .04em; }
.c-sub { font-family: var(--d-f-mono); font-size: 11px; color: var(--pixel-text-secondary); }
.c-status { display: flex; align-items: center; gap: 7px; font-family: var(--d-f-mono); font-size: 11px; color: var(--pixel-text-secondary); white-space: nowrap; }
.goto-quests { font-family: var(--d-f-body); font-weight: 600; font-size: 12px; background: var(--pixel-card-bg); border: 1px solid var(--pixel-border); border-radius: 999px; color: var(--pixel-text-secondary); cursor: pointer; padding: 5px 11px; transition: color .2s ease, border-color .2s ease; }
.goto-quests:hover { color: var(--pixel-info); border-color: var(--pixel-info); }
.dot { width: 8px; height: 8px; border-radius: 50%; background: var(--pixel-success); box-shadow: 0 0 8px var(--pixel-success); }
.dot.busy { background: var(--pixel-info); box-shadow: 0 0 8px var(--pixel-info); animation: corepulse .9s ease-in-out infinite; }

/* Thread */
.c-thread { flex: 1; overflow-y: auto; padding: 18px; display: flex; flex-direction: column; gap: 16px; }

.welcome { text-align: center; padding: 40px 20px; color: var(--pixel-text-secondary); margin: auto 0; }
.welcome-glyph { font-size: 34px; color: var(--pixel-info); text-shadow: 0 0 16px rgba(56, 189, 248, .45); margin-bottom: 14px; }
.welcome-text { font-family: var(--d-f-body); font-size: 14px; color: var(--pixel-text); margin-bottom: 8px; }
.welcome-hint { font-size: 12px; line-height: 1.6; max-width: 440px; margin: 0 auto; }

.msg { display: flex; gap: 10px; max-width: 82%; }
.msg.user { align-self: flex-end; flex-direction: row-reverse; }
.msg.assistant { align-self: flex-start; }
.msg-av { width: 34px; height: 34px; flex: 0 0 34px; display: flex; align-items: center; justify-content: center; font-size: 16px; border-radius: 10px; background: var(--pixel-bg-secondary); border: 1px solid var(--pixel-border); color: var(--pixel-text-secondary); }
.msg.assistant .msg-av { border-color: rgba(56, 189, 248, .45); color: var(--pixel-info); background: rgba(56, 189, 248, .1); }
.msg-col { display: flex; flex-direction: column; gap: 5px; min-width: 0; }
.msg-name { font-family: var(--d-f-mono); font-size: 10px; color: var(--pixel-text-secondary); }
.msg.user .msg-name { text-align: right; color: var(--pixel-primary); }
.msg-bubble { padding: 10px 13px; background: var(--pixel-bg-secondary); border: 1px solid var(--pixel-border); border-radius: 12px; font-family: var(--d-f-body); font-size: 13.5px; line-height: 1.6; word-break: break-word; white-space: pre-wrap; color: var(--pixel-text); }
.msg.assistant .msg-bubble { border-top-left-radius: 4px; }
.msg.user .msg-bubble { background: var(--d-grad); color: #0a0b10; border-color: transparent; border-top-right-radius: 4px; font-weight: 500; }
[data-theme="light"] .msg.user .msg-bubble { color: #fff; }

.tool-line { display: inline-flex; align-items: center; gap: 7px; align-self: flex-start; font-family: var(--d-f-mono); font-size: 11px; color: var(--pixel-info); padding: 6px 11px; border-radius: 8px; border: 1px solid rgba(56, 189, 248, .3); background: rgba(56, 189, 248, .08); }
.tdot { width: 6px; height: 6px; border-radius: 50%; background: var(--pixel-info); animation: corepulse .8s ease-in-out infinite; }

.summon-list { display: flex; flex-direction: column; gap: 6px; }
.summon { display: flex; align-items: center; gap: 9px; padding: 7px 11px; background: var(--pixel-card-bg); border: 1px solid rgba(56, 189, 248, .35); border-radius: var(--d-radius-sm); box-shadow: 0 0 18px -8px rgba(56, 189, 248, .3); animation: slidein .25s ease both; }
@keyframes slidein { from { transform: translateX(-10px); opacity: 0; } to { transform: none; opacity: 1; } }
.s-plus { font-family: var(--d-f-mono); font-size: 10px; color: var(--pixel-info); letter-spacing: .05em; }
.s-gem { width: 22px; height: 22px; flex: 0 0 22px; display: flex; align-items: center; justify-content: center; font-size: 13px; color: #0a0b10; border-radius: 6px; font-family: var(--d-f-display); }
.s-title { font-size: 12.5px; color: var(--pixel-text); flex: 1; min-width: 0; }
.s-exp { font-family: var(--d-f-mono); font-size: 11px; color: var(--pixel-warning); font-weight: 600; }

.cursor { display: inline-block; width: 7px; height: 15px; background: var(--pixel-info); vertical-align: -2px; margin-left: 2px; border-radius: 1px; animation: corepulse .7s ease-in-out infinite; }

/* 首 token 前「思考中」三点 */
.think-line { display: inline-flex; align-items: center; gap: 5px; align-self: flex-start; font-family: var(--d-f-mono); font-size: 11px; color: var(--pixel-info); padding: 8px 12px; border-radius: 8px; border: 1px solid rgba(56, 189, 248, .3); background: rgba(56, 189, 248, .08); }
.think-line .td { width: 6px; height: 6px; border-radius: 50%; background: var(--pixel-info); display: inline-block; animation: thinkblink 1.2s ease-in-out infinite; }
.think-line .td:nth-child(2) { animation-delay: .2s; }
.think-line .td:nth-child(3) { animation-delay: .4s; }
@keyframes thinkblink { 0%, 100% { opacity: .25; transform: translateY(0); } 50% { opacity: 1; transform: translateY(-2px); } }

/* Compose */
.c-compose { display: flex; gap: 10px; padding: 12px; border-top: 1px solid var(--pixel-border); }
.c-input { flex: 1; font-family: var(--d-f-body); font-size: 13.5px; background: var(--pixel-bg-secondary); border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); color: var(--pixel-text); padding: 11px 13px; resize: none; outline: none; line-height: 1.55; transition: border-color .2s ease, box-shadow .2s ease; }
.c-input::placeholder { color: var(--pixel-text-secondary); opacity: .6; }
.c-input:focus { border-color: var(--pixel-info); box-shadow: 0 0 0 3px rgba(56, 189, 248, .16); }
.c-input:disabled { opacity: .6; }
.c-send { font-family: var(--d-f-body); font-weight: 700; font-size: 13px; padding: 0 20px; border: 0; border-radius: var(--d-radius-sm); cursor: pointer; color: #0a0b10; background: var(--d-grad); align-self: stretch; box-shadow: 0 8px 22px -12px rgba(99, 102, 241, .8); transition: transform .15s ease, box-shadow .2s ease; }
.c-send:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 12px 26px -10px rgba(99, 102, 241, .95); }
.c-send:disabled { opacity: .5; cursor: default; }
[data-theme="light"] .c-send { color: #fff; }
.c-foot-hint { padding: 7px 15px 11px; font-family: var(--d-f-mono); font-size: 10px; color: var(--pixel-text-secondary); border-top: 1px solid var(--pixel-border); opacity: .75; }

/* ===== Responsive ===== */
@media (max-width: 800px) {
  .c-layout { grid-template-columns: 1fr; height: auto; }
  .c-sidebar { order: 2; max-height: 180px; }
  .c-main { height: calc(100vh - 220px); min-height: 420px; }
}
</style>

