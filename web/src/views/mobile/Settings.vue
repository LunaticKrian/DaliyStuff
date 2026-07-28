<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { listSessions, revokeSession, changePassword } from '../../api/auth'
import { useNotifyStore } from '../../stores/notification'
import { useAppLock } from '../../composables/useAppLock'
import { isTauri } from '../../utils/platform'
import { formatDate } from '../../utils/format'
import type { AuthSession } from '../../types/user'

const router = useRouter()
const auth = useAuthStore()
const notify = useNotifyStore()
const lock = useAppLock()

const sessions = ref<AuthSession[]>([])
const oldPwd = ref('')
const newPwd = ref('')

async function loadSessions() {
  try { sessions.value = await listSessions() } catch { /* 静默 */ }
}
onMounted(loadSessions)

async function onChangePwd() {
  if (!oldPwd.value || !newPwd.value) { notify.warning('请填写新旧密钥'); return }
  try {
    await changePassword({ old_password: oldPwd.value, new_password: newPwd.value })
    notify.success('密钥已更改，其他设备将被踢出')
    oldPwd.value = ''; newPwd.value = ''
    await loadSessions()
  } catch { notify.error('更改失败') }
}

async function revoke(id: number) {
  try { await revokeSession(id); sessions.value = sessions.value.filter((s) => s.id !== id); notify.success('已踢出') } catch { notify.error('操作失败') }
}

async function enableLock() {
  const pin = window.prompt('设置 4~6 位应用锁密钥')
  if (!pin) return
  if (!/^\d{4,6}$/.test(pin)) { notify.warning('密钥须为 4~6 位数字'); return }
  const pin2 = window.prompt('再次输入确认')
  if (pin !== pin2) { notify.warning('两次输入不一致'); return }
  await lock.setPin(pin)
  notify.success('应用锁已启用')
}
function disableLock() {
  lock.clear()
  notify.success('应用锁已关闭')
}

async function logout() {
  await auth.logout()
  router.push('/login')
}
</script>

<template>
  <div class="m-screen">
    <div class="m-head">
      <span class="m-head__back" @click="router.push('/me')">◂</span>
      <span class="m-head__title">设置</span>
    </div>

    <!-- 账户 -->
    <div class="m-section-title">账户</div>
    <div class="m-card">
      <div class="m-between"><span class="m-hint">账号</span><span>{{ auth.user?.username }}</span></div>
      <hr class="m-divider" />
      <div class="m-field" style="margin: 0;"><span class="m-field__label">修改密钥（将踢出其他设备）</span></div>
      <div class="m-grid-2" style="margin-top: 6px;">
        <input v-model="oldPwd" type="password" class="m-input" placeholder="当前密钥" />
        <input v-model="newPwd" type="password" class="m-input" placeholder="新密钥" />
      </div>
      <button class="m-btn m-btn--sm m-mt" @click="onChangePwd">更改密钥</button>
    </div>

    <!-- 应用锁 -->
    <div class="m-section-title">应用锁 · GUILD LOCK</div>
    <div class="m-card">
      <div class="m-between">
        <div><div style="font-weight: 600;">应用锁</div><div class="m-hint">PIN{{ lock.biometric.value ? ' + 生物识别' : '' }} · {{ lock.enabled.value ? '已启用' : '未启用' }}</div></div>
        <button v-if="!lock.enabled.value" class="m-btn m-btn--sm m-btn--primary" @click="enableLock">启用</button>
        <button v-else class="m-btn m-btn--sm m-btn--danger" @click="disableLock">关闭</button>
      </div>
      <hr class="m-divider" v-if="lock.enabled.value" />
      <div v-if="lock.enabled.value" class="m-between">
        <span class="m-hint">生物识别（仅 App 内）</span>
        <span class="m-toggle" :class="{ 'm-toggle--on': lock.biometric.value }" @click="lock.setBiometric(!lock.biometric.value)">
          <span class="m-toggle__track"></span><span class="m-toggle__knob"></span>
        </span>
      </div>
      <div v-if="lock.enabled.value && !isTauri()" class="m-hint" style="margin-top: 8px;">提示：生物识别仅在安装版 App 内可用，当前环境仅支持 PIN。</div>
    </div>

    <!-- 设备会话 -->
    <div class="m-section-title">设备会话</div>
    <div v-for="s in sessions" :key="s.id" class="m-row" :class="{ 'm-row--bare': false }">
      <div class="m-row__ico" :style="{ background: s.is_current ? 'var(--pixel-success)' : 'var(--pixel-card-bg)', color: s.is_current ? 'var(--pixel-bg)' : undefined }">▣</div>
      <div class="m-row__main">
        <div class="m-row__title">{{ s.device_name || s.device_platform || '设备' }}{{ s.is_current ? ' · 本机' : '' }}</div>
        <div class="m-row__sub">{{ formatDate(s.last_seen_at) }}</div>
      </div>
      <button v-if="!s.is_current" class="m-tag m-tag--warn" @click="revoke(s.id)">踢出</button>
      <span v-else class="m-tag m-tag--ok">在线</span>
    </div>

    <button class="m-btn m-btn--danger m-btn--block m-mt" @click="logout">⏻ 退出登录</button>
    <div class="m-hint m-center" style="margin-top: 12px;">PixelPack Mobile · GUILD DECK</div>
  </div>
</template>
