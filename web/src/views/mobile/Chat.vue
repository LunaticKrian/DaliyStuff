<script setup lang="ts">
import { onMounted, ref, nextTick, watch } from 'vue'
import { listSessions, createSession, listMessages } from '../../api/chat'
import { streamChatMessage } from '../../utils/sse'
import { useNotifyStore } from '../../stores/notification'
import type { ChatSession, ChatMessage } from '../../types/chat'

const notify = useNotifyStore()
const sessions = ref<ChatSession[]>([])
const activeId = ref<number | null>(null)
const messages = ref<ChatMessage[]>([])
const loading = ref(true)
const streaming = ref(false)
const input = ref('')
const bottom = ref<HTMLElement | null>(null)

async function loadSessions() {
  sessions.value = await listSessions()
  if (sessions.value.length && activeId.value === null) {
    await open(sessions.value[0].id)
  }
  loading.value = false
}

async function open(id: number) {
  activeId.value = id
  messages.value = await listMessages(id)
  await scrollBottom()
}

async function newSession() {
  const s = await createSession()
  sessions.value.unshift(s)
  await open(s.id)
}

async function send() {
  const content = input.value.trim()
  if (!content || streaming.value || activeId.value === null) return
  input.value = ''
  messages.value.push({ id: Date.now(), session_id: activeId.value, role: 'user', content, meta: null, created_at: new Date().toISOString() })
  await scrollBottom()

  streaming.value = true
  const assistantIdx = messages.value.push({ id: Date.now() + 1, session_id: activeId.value, role: 'assistant', content: '', meta: null, created_at: new Date().toISOString() }) - 1

  await streamChatMessage(activeId.value, content, {
    onEvent(e) {
      if (e.type === 'delta') {
        messages.value[assistantIdx].content += e.text
        scrollBottom()
      } else if (e.type === 'task_created') {
        notify.success(`NEXA 创建了委托：${e.task.title}`)
      } else if (e.type === 'error') {
        notify.error(e.message)
      }
    },
    onError() { notify.error('连接中断'); },
  })
  streaming.value = false
}

async function scrollBottom() {
  await nextTick()
  bottom.value?.scrollIntoView({ behavior: 'smooth' })
}

onMounted(loadSessions)
watch(() => messages.value.length, scrollBottom)
</script>

<template>
  <div class="m-screen chat-wrap">
    <div class="m-between m-mb">
      <div class="m-flex m-gap" style="align-items: center;">
        <div class="m-avatar" style="background: var(--pixel-info); color: var(--pixel-bg);">✦</div>
        <div>
          <div style="font-weight: 700; font-size: 14px;">NEXA 智核</div>
          <div class="m-hint">{{ activeId ? '会话 #' + activeId : '公会智核' }}</div>
        </div>
      </div>
      <button class="m-btn m-btn--sm" @click="newSession">+ 新对话</button>
    </div>

    <div v-if="loading" class="m-loading">▮ 加载中</div>
    <template v-else>
      <div v-if="!activeId" class="m-empty">
        <div class="m-empty__ico">✦</div>
        <div class="m-empty__txt">开始与 NEXA 对话，生成委托或获取建议</div>
        <button class="m-btn m-btn--primary m-btn--sm m-mt" @click="newSession">▸ 新对话</button>
      </div>

      <div v-for="m in messages" :key="m.id" class="msg" :class="m.role">
        <div class="bubble">{{ m.content }}<span v-if="streaming && m.role === 'assistant' && m === messages[messages.length - 1]" class="cursor">▍</span></div>
      </div>
      <div ref="bottom"></div>
    </template>

    <!-- 输入栏（避开底部 Dock） -->
    <div class="input-bar">
      <input v-model="input" class="m-input" placeholder="向 NEXA 下令…" :disabled="streaming || !activeId" @keyup.enter="send" />
      <button class="m-btn m-btn--primary" :disabled="streaming || !input.trim() || !activeId" @click="send">▸</button>
    </div>
  </div>
</template>

<style scoped>
/* 令牌兜底：脱离 .m-deck 时也保留新视觉语言 */
.chat-wrap {
  --pixel-bg: #0b0d14;
  --pixel-bg-secondary: #14171f;
  --pixel-card-bg: rgba(255, 255, 255, 0.045);
  --pixel-border: rgba(255, 255, 255, 0.09);
  --pixel-primary: #22d3ee;
  --pixel-info: #38bdf8;
  --pixel-text: #f4f6fb;
  --pixel-text-secondary: #9aa3b2;
  --d-grad: linear-gradient(135deg, #818cf8 0%, #7c5cff 40%, #22d3ee 100%);
  --d-radius: 14px;
  --d-radius-sm: 10px;
  --d-shadow-sm: 0 4px 14px -8px rgba(0, 0, 0, .6);
  padding-bottom: 130px;
}

.msg { display: flex; margin-bottom: 10px; }
.msg.user { justify-content: flex-end; }

.bubble {
  max-width: 82%;
  padding: 10px 14px;
  line-height: 1.5;
  font-size: 14px;
  border: 1px solid var(--pixel-border);
  border-radius: 14px;
  white-space: pre-wrap;
  word-break: break-word;
  box-shadow: var(--d-shadow-sm);
}
.msg.user .bubble {
  background: var(--d-grad);
  border-color: transparent;
  color: #0a0b10;
  font-weight: 500;
  border-bottom-right-radius: 4px;
}
[data-theme="light"] .msg.user .bubble { color: #fff; }
.msg.assistant .bubble {
  background: var(--pixel-card-bg);
  backdrop-filter: blur(10px);
  border-bottom-left-radius: 4px;
}

.cursor { animation: m-blink 0.8s steps(2) infinite; color: var(--pixel-info); }

.input-bar {
  position: fixed; left: 12px; right: 12px;
  bottom: calc(76px + env(safe-area-inset-bottom, 0px));
  display: flex; gap: 8px; z-index: 90;
}
</style>
