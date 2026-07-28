<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { updateMe, changePassword, listSessions, revokeSession } from '../api/auth'
import { useNotifyStore } from '../stores/notification'
import type { AuthSession } from '../types/user'

const router = useRouter()
const auth = useAuthStore()
const notify = useNotifyStore()

// Profile form
const profileForm = reactive({
  email: auth.user?.email || '',
  avatar_url: auth.user?.avatar_url || '',
})
const profileLoading = ref(false)
const profileError = ref('')

// Password form
const pwForm = reactive({
  old_password: '',
  new_password: '',
  confirm: '',
})
const pwLoading = ref(false)
const pwError = ref('')

// Sessions（设备会话）
const sessions = ref<AuthSession[]>([])
const sessionsLoading = ref(false)
const sessionsError = ref('')

async function loadSessions() {
  sessionsLoading.value = true
  sessionsError.value = ''
  try {
    sessions.value = await listSessions()
  } catch (e: any) {
    sessionsError.value = e?.data?.detail || '加载失败'
  } finally {
    sessionsLoading.value = false
  }
}

async function handleRevoke(id: number) {
  try {
    await revokeSession(id)
    await loadSessions()
    notify.success('已登出该设备')
  } catch (e: any) {
    notify.error(e?.data?.detail || '操作失败')
  }
}

function formatTime(t: string | null | undefined): string {
  if (!t) return '—'
  return t.slice(0, 16).replace('T', ' ')
}

onMounted(loadSessions)

async function handleSaveProfile() {
  profileLoading.value = true
  profileError.value = ''
  try {
    await updateMe({
      email: profileForm.email.trim() || undefined,
      avatar_url: profileForm.avatar_url.trim() || undefined,
    })
    await auth.initialize()
    notify.success('个人信息已更新')
  } catch (e: any) {
    profileError.value = e?.data?.detail || '更新失败'
    notify.error(profileError.value)
  } finally {
    profileLoading.value = false
  }
}

async function handleChangePassword() {
  pwError.value = ''
  if (!pwForm.old_password) { pwError.value = '请输入旧密码'; return }
  if (!pwForm.new_password || pwForm.new_password.length < 6) { pwError.value = '新密码至少6位'; return }
  if (pwForm.new_password !== pwForm.confirm) { pwError.value = '两次密码不一致'; return }

  pwLoading.value = true
  try {
    await changePassword({
      old_password: pwForm.old_password,
      new_password: pwForm.new_password,
    })
    pwForm.old_password = ''
    pwForm.new_password = ''
    pwForm.confirm = ''
    notify.success('密码已修改')
  } catch (e: any) {
    pwError.value = e?.data?.detail || '修改失败'
    notify.error(pwError.value)
  } finally {
    pwLoading.value = false
  }
}
</script>

<template>
  <div class="settings-page animate-fade-in">
    <div class="settings-header">
      <button class="back-btn" @click="router.push('/')">
        <span>◀</span>
        <span>角色信息</span>
      </button>
      <h1 class="page-title">
        <span class="title-icon">◈</span>
        <span>个人设置</span>
      </h1>
    </div>

    <!-- Profile Section -->
    <div class="settings-card pixel-border">
      <div class="card-header">
        <span class="card-icon">☺</span>
        <span>基本信息</span>
      </div>
      <div class="card-body">
        <div class="field-group">
          <label class="field-label">用户名</label>
          <div class="field-readonly">{{ auth.user?.username }}</div>
        </div>
        <div class="field-group">
          <label class="field-label">邮箱</label>
          <input v-model="profileForm.email" type="email" class="pixel-input" placeholder="输入邮箱..." />
        </div>
        <div class="field-group">
          <label class="field-label">头像 URL</label>
          <input v-model="profileForm.avatar_url" type="text" class="pixel-input" placeholder="输入头像图片链接..." />
        </div>
        <div v-if="profileError" class="field-error">{{ profileError }}</div>
        <button class="pixel-btn primary" :disabled="profileLoading" @click="handleSaveProfile">
          {{ profileLoading ? '保存中...' : '✓ 保存' }}
        </button>
      </div>
    </div>

    <!-- Password Section -->
    <div class="settings-card pixel-border">
      <div class="card-header">
        <span class="card-icon">▣</span>
        <span>修改密码</span>
      </div>
      <div class="card-body">
        <div class="field-group">
          <label class="field-label">旧密码</label>
          <input v-model="pwForm.old_password" type="password" class="pixel-input" placeholder="输入旧密码" />
        </div>
        <div class="field-group">
          <label class="field-label">新密码</label>
          <input v-model="pwForm.new_password" type="password" class="pixel-input" placeholder="至少6位" />
        </div>
        <div class="field-group">
          <label class="field-label">确认密码</label>
          <input v-model="pwForm.confirm" type="password" class="pixel-input" placeholder="再次输入新密码" @keydown.enter="handleChangePassword" />
        </div>
        <div v-if="pwError" class="field-error">{{ pwError }}</div>
        <button class="pixel-btn primary" :disabled="pwLoading" @click="handleChangePassword">
          {{ pwLoading ? '修改中...' : '✓ 修改密码' }}
        </button>
      </div>
    </div>

    <!-- Account Info -->
    <div class="settings-card pixel-border">
      <div class="card-header">
        <span class="card-icon">▤</span>
        <span>账户信息</span>
      </div>
      <div class="card-body">
        <div class="field-group">
          <label class="field-label">注册时间</label>
          <div class="field-readonly">{{ auth.user?.created_at?.slice(0, 10) || '—' }}</div>
        </div>
        <div class="field-group">
          <label class="field-label">用户 ID</label>
          <div class="field-readonly">{{ auth.user?.id }}</div>
        </div>
      </div>
    </div>

    <!-- Sessions -->
    <div class="settings-card pixel-border">
      <div class="card-header">
        <span class="card-icon">⬡</span>
        <span>设备会话</span>
      </div>
      <div class="card-body">
        <div v-if="sessionsLoading" class="field-readonly">加载中...</div>
        <div v-else-if="sessionsError" class="field-error">{{ sessionsError }}</div>
        <div v-else-if="!sessions.length" class="field-readonly">无活跃会话</div>
        <div v-for="s in sessions" :key="s.id" class="session-row">
          <div class="session-info">
            <div class="session-name">
              {{ s.device_name || '未知设备' }}
              <span v-if="s.is_current" class="session-badge">本机</span>
            </div>
            <div class="session-meta">
              {{ s.device_platform || '—' }} · {{ formatTime(s.last_seen_at) }}
            </div>
          </div>
          <button
            class="pixel-btn"
            :disabled="s.is_current"
            :title="s.is_current ? '当前会话，请用页面退出登录' : '登出该设备'"
            @click="handleRevoke(s.id)"
          >登出</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&display=swap');

/* ═══════ 本页令牌：--pixel-* 重映射为高级深色（浅色自适应）═══════ */
.settings-page {
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

  max-width: 600px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
  font-family: var(--d-f-body);
  color: var(--pixel-text);
}
[data-theme="light"] .settings-page {
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

.settings-header { display: flex; align-items: center; gap: 12px; }

.back-btn { display: inline-flex; align-items: center; gap: 6px; background: var(--pixel-card-bg); backdrop-filter: blur(10px); border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); color: var(--pixel-text-secondary); font-family: var(--d-f-body); font-size: 13px; padding: 7px 12px; cursor: pointer; transition: color .2s ease, border-color .2s ease; }
.back-btn:hover { color: var(--pixel-primary); border-color: var(--pixel-primary); }

.page-title { font-family: var(--d-f-display); font-size: 18px; font-weight: 700; color: var(--pixel-text); display: flex; align-items: center; gap: 10px; margin: 0; letter-spacing: -.01em; }
.title-icon { color: var(--pixel-primary); font-size: 16px; }

/* ===== Card ===== */
.settings-card { background: var(--pixel-card-bg); backdrop-filter: blur(10px); border: 1px solid var(--pixel-border); border-radius: var(--d-radius); box-shadow: var(--d-shadow-sm); overflow: hidden; }

.card-header { display: flex; align-items: center; gap: 8px; padding: 12px 16px; border-bottom: 1px solid var(--pixel-border); font-family: var(--d-f-mono); font-size: 12px; color: var(--pixel-text); letter-spacing: .02em; user-select: none; }
.card-icon { font-size: 14px; color: var(--pixel-primary); width: 18px; text-align: center; }
.card-body { padding: 16px; display: flex; flex-direction: column; gap: 14px; }

/* ===== Fields ===== */
.field-group { display: flex; flex-direction: column; gap: 6px; }
.field-label { font-family: var(--d-f-mono); font-size: 11px; color: var(--pixel-text-secondary); letter-spacing: .04em; }
.field-readonly { font-family: var(--d-f-body); font-size: 13px; color: var(--pixel-text); padding: 9px 11px; background: var(--pixel-bg-secondary); border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); opacity: .85; }

.pixel-input { background: var(--pixel-bg-secondary); border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); color: var(--pixel-text); font-family: var(--d-f-body); font-size: 13px; padding: 9px 11px; outline: none; width: 100%; box-sizing: border-box; transition: border-color .2s ease, box-shadow .2s ease; }
.pixel-input:focus { border-color: var(--pixel-primary); box-shadow: 0 0 0 3px rgba(34, 211, 238, .16); }
.pixel-input::placeholder { color: var(--pixel-text-secondary); opacity: .55; }

.field-error { font-family: var(--d-f-body); font-size: 12px; color: var(--pixel-accent); padding: 8px 10px; border: 1px solid var(--pixel-accent); border-radius: var(--d-radius-sm); background: rgba(251, 113, 133, .08); }

/* ===== Button ===== */
.pixel-btn { font-family: var(--d-f-body); font-weight: 600; font-size: 13px; padding: 9px 16px; border-radius: var(--d-radius-sm); border: 1px solid var(--pixel-border); background: var(--pixel-bg-secondary); color: var(--pixel-text); cursor: pointer; align-self: flex-start; transition: color .2s ease, border-color .2s ease; }
.pixel-btn:hover:not(:disabled) { color: var(--pixel-primary); border-color: var(--pixel-primary); }
.pixel-btn:disabled { opacity: .5; cursor: not-allowed; }
.pixel-btn.primary { border: 0; color: #0a0b10; background: var(--d-grad); font-weight: 700; box-shadow: 0 8px 22px -10px rgba(99, 102, 241, .8); }
.pixel-btn.primary:hover:not(:disabled) { box-shadow: 0 12px 28px -8px rgba(99, 102, 241, .95); }
[data-theme="light"] .pixel-btn.primary { color: #fff; }

/* ===== Sessions ===== */
.session-row { display: flex; align-items: center; justify-content: space-between; gap: 10px; padding: 10px 12px; background: var(--pixel-bg-secondary); border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); }
.session-info { display: flex; flex-direction: column; gap: 3px; min-width: 0; }
.session-name { font-family: var(--d-f-body); font-size: 13px; color: var(--pixel-text); display: flex; align-items: center; gap: 6px; }
.session-badge { font-family: var(--d-f-mono); font-size: 10px; font-weight: 600; color: #0a0b10; background: var(--pixel-primary); padding: 2px 7px; border-radius: 999px; letter-spacing: .04em; }
[data-theme="light"] .session-badge { color: #fff; }
.session-meta { font-family: var(--d-f-mono); font-size: 11px; color: var(--pixel-text-secondary); }
</style>
