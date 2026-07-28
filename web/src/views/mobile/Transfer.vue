<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'
import { useRouter } from 'vue-router'
import { getOrigin, tokenStore } from '../../utils/platform'

const router = useRouter()

let ws: WebSocket | null = null
let pc: RTCPeerConnection | null = null
let dc: RTCDataChannel | null = null

const me = ref<{ id: number; username: string } | null>(null)
const myCode = ref('')
const inputCode = ref('')
const connState = ref<'idle' | 'connecting' | 'connected' | 'failed'>('idle')
const statusMsg = ref('正在连接信令服务器…')
const errorMsg = ref('')
const selectedFile = ref<File | null>(null)
const sending = ref(false)
const progress = ref(0)
const progressLabel = ref('')

const CHUNK = 16 * 1024
const BUFFER_HIGH = 1 * 1024 * 1024
const connected = computed(() => connState.value === 'connected')
const canSend = computed(() => connected.value && !!selectedFile.value && !sending.value)

function wsUrl(): string {
  const origin = getOrigin()
  const base = origin || `${location.protocol}//${location.host}`
  const proto = base.startsWith('https') ? 'wss' : 'ws'
  return `${proto}://${base.replace(/^https?:\/\//, '')}/api/rtc/signal`
}

function sendSignal(obj: Record<string, unknown>) { ws?.send(JSON.stringify(obj)) }

function connectSignal() {
  const token = tokenStore.get('access_token')
  if (!token) { statusMsg.value = '未登录'; return }
  ws = new WebSocket(wsUrl())
  ws.onopen = () => ws!.send(JSON.stringify({ token }))
  ws.onmessage = (ev) => onSignal(JSON.parse(ev.data))
  ws.onclose = () => { statusMsg.value = '信令断开，请返回重试' }
}

async function onSignal(m: any) {
  switch (m.type) {
    case 'auth_ok': me.value = m.me; statusMsg.value = '已就绪，创建或加入频道'; break
    case 'auth_failed': statusMsg.value = '鉴权失败'; break
    case 'invite_created': myCode.value = m.code; statusMsg.value = '把频道码告诉对方'; break
    case 'offer': await onIncomingOffer(m); break
    case 'answer': await pc!.setRemoteDescription(new RTCSessionDescription(m.answer)); break
    case 'invite_not_found': errorMsg.value = '频道码无效或已过期'; connState.value = 'failed'; break
    case 'peer_unavailable': errorMsg.value = '对方已离线'; connState.value = 'failed'; break
  }
}

function newPeer(): RTCPeerConnection {
  const peer = new RTCPeerConnection({ iceServers: [] })
  peer.onconnectionstatechange = () => {
    const s = peer.connectionState
    if (s === 'connected') { connState.value = 'connected'; statusMsg.value = '通道就绪' }
    else if (['failed', 'disconnected', 'closed'].includes(s)) { if (connState.value !== 'connected') connState.value = 'failed'; statusMsg.value = `状态：${s}` }
  }
  return peer
}
function waitIceComplete(peer: RTCPeerConnection, timeoutMs = 4000): Promise<void> {
  return new Promise((resolve) => {
    if (peer.iceGatheringState === 'complete') return resolve()
    let done = false
    const finish = () => { if (!done) { done = true; resolve() } }
    peer.addEventListener('icegatheringstatechange', () => { if (peer.iceGatheringState === 'complete') finish() })
    setTimeout(finish, timeoutMs)
  })
}

async function createInvite() {
  errorMsg.value = ''; connState.value = 'connecting'
  pc = newPeer(); dc = pc.createDataChannel('file', { ordered: true }); setupDataChannel(dc)
  const offer = await pc.createOffer(); await pc.setLocalDescription(offer); await waitIceComplete(pc)
  sendSignal({ type: 'invite_create', offer: pc.localDescription })
}
function joinInvite() {
  errorMsg.value = ''
  if (!inputCode.value.trim()) return
  connState.value = 'connecting'
  sendSignal({ type: 'invite_join', code: inputCode.value.trim().toUpperCase() })
}
async function onIncomingOffer(m: any) {
  pc = newPeer()
  pc.ondatachannel = (ev) => { dc = ev.channel; setupDataChannel(dc) }
  await pc.setRemoteDescription(new RTCSessionDescription(m.offer))
  const answer = await pc.createAnswer(); await pc.setLocalDescription(answer); await waitIceComplete(pc)
  sendSignal({ type: 'answer', to: m.from, answer: pc.localDescription })
}

function setupDataChannel(channel: RTCDataChannel) {
  channel.binaryType = 'arraybuffer'
  let meta: { name: string; size: number; mime: string } | null = null
  const chunks: ArrayBuffer[] = []
  let received = 0
  channel.onopen = () => { connState.value = 'connected'; statusMsg.value = '通道就绪' }
  channel.onmessage = (ev) => {
    if (typeof ev.data === 'string') {
      const msg = JSON.parse(ev.data)
      if (msg.kind === 'meta') { meta = msg; chunks.length = 0; received = 0; progress.value = 0; progressLabel.value = `接收：${msg.name}` }
      else if (msg.kind === 'done') {
        const blob = new Blob(chunks, { type: meta?.mime || 'application/octet-stream' })
        const url = URL.createObjectURL(blob); const a = document.createElement('a')
        a.href = url; a.download = meta?.name || 'received'; a.click(); URL.revokeObjectURL(url)
        progress.value = 100; progressLabel.value = `已接收：${meta?.name}`
      }
    } else { chunks.push(ev.data); received += ev.data.byteLength; if (meta) progress.value = Math.min(99, Math.round((received / meta.size) * 100)) }
  }
}
function onFileChange(e: Event) {
  const f = (e.target as HTMLInputElement).files?.[0]; selectedFile.value = f ?? null; progress.value = 0
}
async function waitDrain(channel: RTCDataChannel) {
  if (channel.bufferedAmount < BUFFER_HIGH) return
  await new Promise<void>((resolve) => {
    const t = setInterval(() => { if (channel.bufferedAmount < BUFFER_HIGH / 2) { clearInterval(t); resolve() } }, 20)
  })
}
async function sendFile() {
  if (!dc || dc.readyState !== 'open' || !selectedFile.value) return
  sending.value = true; errorMsg.value = ''
  try {
    const file = selectedFile.value
    dc.send(JSON.stringify({ kind: 'meta', name: file.name, size: file.size, mime: file.type }))
    for (let offset = 0; offset < file.size; offset += CHUNK) {
      const buf = await file.slice(offset, offset + CHUNK).arrayBuffer(); await waitDrain(dc); dc.send(buf)
      progress.value = Math.round((offset / file.size) * 100)
    }
    dc.send(JSON.stringify({ kind: 'done' })); progress.value = 100; progressLabel.value = `已发送：${file.name}`
  } catch (e) { errorMsg.value = `发送失败：${(e as Error).message}` } finally { sending.value = false }
}
function hangUp() {
  dc?.close(); pc?.close(); dc = null; pc = null
  myCode.value = ''; inputCode.value = ''; connState.value = 'idle'; statusMsg.value = '已断开'; progress.value = 0; progressLabel.value = ''
}
async function copyCode() {
  try { await navigator.clipboard?.writeText(myCode.value) } catch { /* ignore */ }
}

onMounted(connectSignal)
onBeforeUnmount(() => { ws?.close(); hangUp() })
</script>

<template>
  <div class="m-screen">
    <div class="m-head">
      <span class="m-head__back" @click="router.push('/me')">◂</span>
      <span class="m-head__title">点对点传输</span>
    </div>

    <div class="m-card m-center">
      <div style="font-size: 36px; color: var(--pixel-info);" :class="{ 'm-blink': connState === 'connecting' }">⇄</div>
      <div class="m-hint">{{ statusMsg }}</div>
      <span class="m-tag" :class="{ 'm-tag--ok': connected, 'm-tag--warn': connState === 'connecting' }">{{ connState.toUpperCase() }}</span>
    </div>

    <div class="m-card">
      <div class="m-card__title">建立频道</div>
      <button class="m-btn m-btn--block" :disabled="connState !== 'idle' && !myCode" @click="createInvite">▶ 创建频道码</button>
      <div v-if="myCode" class="m-between m-mt">
        <span class="m-mono" style="font-size: 18px; color: var(--pixel-warning); letter-spacing: 3px;">{{ myCode }}</span>
        <button class="m-btn m-btn--sm" @click="copyCode">复制</button>
      </div>
      <hr class="m-divider" />
      <div class="m-field" style="margin: 0;"><span class="m-field__label">或加入频道</span></div>
      <div class="m-flex m-gap m-mt" style="margin-top: 6px;">
        <input v-model="inputCode" class="m-input" placeholder="频道码" style="flex: 1;" />
        <button class="m-btn m-btn--primary" @click="joinInvite">加入</button>
      </div>
    </div>

    <div class="m-card" v-if="connected">
      <div class="m-card__title">传输货物</div>
      <input type="file" class="m-input" @change="onFileChange" style="padding: 8px;" />
      <div class="m-meter m-mt" v-if="progress || progressLabel"><div class="m-meter__fill" :style="{ width: progress + '%' }"></div></div>
      <div class="m-hint" v-if="progressLabel">{{ progressLabel }} · {{ progress }}%</div>
      <button class="m-btn m-btn--primary m-btn--block m-mt" :disabled="!canSend" @click="sendFile">{{ sending ? '传输中…' : '▸ 发送' }}</button>
    </div>

    <div v-if="errorMsg" class="m-hint m-center" style="color: var(--pixel-warning);">{{ errorMsg }}</div>
    <button v-if="connState !== 'idle'" class="m-btn m-btn--ghost m-btn--block m-mt" @click="hangUp">断开</button>
  </div>
</template>
