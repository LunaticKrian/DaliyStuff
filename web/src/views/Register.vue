<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()

const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const email = ref('')
const error = ref('')
const loading = ref(false)
const showPw = ref(false)

const TIERS = ['新手', '见习', '冒险者', '老练', '传奇']
const COLORS = ['#fb7185', '#fbbf24', '#facc15', '#34d399', '#22d3ee']

// 密码强度 → EXP / 等级（签名：越强密码，初始等级越高）
const pwStrength = computed(() => {
  const p = password.value
  let s = 0
  if (p.length >= 6) s += 18
  if (p.length >= 10) s += 16
  if (p.length >= 14) s += 14
  if (/[a-z]/.test(p)) s += 10
  if (/[A-Z]/.test(p)) s += 14
  if (/[0-9]/.test(p)) s += 14
  if (/[^A-Za-z0-9]/.test(p)) s += 14
  return Math.max(0, Math.min(100, s))
})
const pwTierIdx = computed(() => Math.min(4, Math.floor(pwStrength.value / 20)))
const pwLevel = computed(() => pwTierIdx.value + 1)
const pwTier = computed(() => TIERS[pwTierIdx.value])
const pwColor = computed(() => COLORS[pwTierIdx.value])

async function handleRegister() {
  error.value = ''
  if (!username.value || !password.value) {
    error.value = '用户名和密码不能为空'
    return
  }
  if (password.value.length < 6) {
    error.value = '密码至少6位'
    return
  }
  if (password.value !== confirmPassword.value) {
    error.value = '两次输入的密码不一致'
    return
  }
  loading.value = true
  try {
    await auth.register({
      username: username.value,
      password: password.value,
      email: email.value || undefined,
    })
    router.push('/character/create')
  } catch (e: any) {
    error.value = e?.data?.detail || '注册失败，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-form">
    <div class="form-card">
      <header class="form-head">
        <span class="eyebrow">SIGN UP</span>
        <h1>创建账号</h1>
        <p>起个名字、设置密码 —— 越强的密码，初始等级越高。</p>
      </header>

      <form class="fields" @submit.prevent="handleRegister">
        <div class="field">
          <label>用户名</label>
          <div class="input-wrap">
            <span class="ico"><svg viewBox="0 0 24 24"><circle cx="12" cy="8" r="4" /><path d="M4 21c0-4 4-7 8-7s8 3 8 7" /></svg></span>
            <input v-model="username" type="text" class="input" placeholder="起个名字" autocomplete="username" />
          </div>
        </div>

        <div class="field">
          <label>邮箱 <span class="opt">选填</span></label>
          <div class="input-wrap">
            <span class="ico"><svg viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="14" rx="2" /><path d="m3 7 9 6 9-6" /></svg></span>
            <input v-model="email" type="email" class="input" placeholder="name@example.com" autocomplete="email" />
          </div>
        </div>

        <div class="field">
          <label>密码</label>
          <div class="input-wrap">
            <span class="ico"><svg viewBox="0 0 24 24"><rect x="4" y="10" width="16" height="11" rx="2" /><path d="M8 10V7a4 4 0 0 1 8 0v3" /></svg></span>
            <input v-model="password" :type="showPw ? 'text' : 'password'" class="input" placeholder="设置密码（6 位以上）" autocomplete="new-password" />
            <button type="button" class="toggle-pw" :aria-label="showPw ? '隐藏密码' : '显示密码'" @click="showPw = !showPw">
              <svg viewBox="0 0 24 24"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z" /><circle cx="12" cy="12" r="3" /></svg>
            </button>
          </div>
          <!-- 密码强度 → EXP 等级（签名） -->
          <div class="pw-strength">
            <span class="pw-bar" :style="{ width: pwStrength + '%', background: pwColor }"></span>
            <span class="pw-note">初始等级 <b :style="{ color: pwColor }">Lv.{{ pwLevel }} · {{ pwTier }}</b></span>
          </div>
        </div>

        <div class="field">
          <label>确认密码</label>
          <div class="input-wrap">
            <span class="ico"><svg viewBox="0 0 24 24"><path d="M9 12l2 2 4-4" /><path d="M5 12V8a3 3 0 0 1 3-3h8a3 3 0 0 1 3 3v4" /><rect x="4" y="12" width="16" height="8" rx="2" /></svg></span>
            <input v-model="confirmPassword" :type="showPw ? 'text' : 'password'" class="input" placeholder="再次输入密码" autocomplete="new-password" />
          </div>
        </div>

        <div v-if="error" class="error" role="alert">
          <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" /><path d="M12 8v5M12 16h.01" /></svg>
          <span>{{ error }}</span>
        </div>

        <button type="submit" class="btn-primary" :disabled="loading">
          <span v-if="loading" class="spinner"></span>
          <template v-else>创建账号 · 开启冒险 →</template>
        </button>
      </form>

      <p class="switch-link">已有账号？<router-link to="/login">直接登录</router-link></p>
    </div>
  </div>
</template>

<style scoped>
.auth-form { width: 100%; max-width: 380px; }
.form-card { animation: rise .6s cubic-bezier(.2, .7, .2, 1) both; }
@keyframes rise { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: none; } }

.form-head { margin-bottom: 1.4rem; }
.form-head .eyebrow { display: inline-block; font-family: var(--f-mono); font-size: .68rem; letter-spacing: .16em; color: var(--cyan); text-transform: uppercase; margin-bottom: .7rem; }
.form-head h1 { font-family: var(--f-display); font-size: 1.7rem; font-weight: 700; letter-spacing: -.02em; }
.form-head p { color: var(--muted); font-size: .9rem; margin-top: .5rem; }

.fields { display: flex; flex-direction: column; gap: .95rem; }
.field { display: flex; flex-direction: column; gap: .45rem; }
.field > label { font-family: var(--f-mono); font-size: .64rem; letter-spacing: .14em; text-transform: uppercase; color: var(--muted); display: flex; align-items: center; gap: .5rem; }
.opt { font-size: .56rem; color: var(--faint); border: 1px solid var(--border); padding: .1em .4em; letter-spacing: .08em; }

.input-wrap { position: relative; display: flex; align-items: center; }
.input-wrap .ico { position: absolute; left: .85rem; color: var(--faint); pointer-events: none; display: inline-flex; transition: color .2s ease; }
.input-wrap .ico svg { width: 17px; height: 17px; fill: none; stroke: currentColor; stroke-width: 1.7; stroke-linecap: round; stroke-linejoin: round; }
.input { width: 100%; font-family: var(--f-body); font-size: .96rem; color: var(--text); background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: .82rem 1rem .82rem 2.55rem; outline: none; box-sizing: border-box; transition: border-color .2s ease, background .2s ease, box-shadow .2s ease; }
.input::placeholder { color: var(--faint); }
.input:hover { border-color: var(--border-2); }
.input:focus { border-color: var(--cyan); background: var(--surface-2); box-shadow: 0 0 0 3px rgba(34, 211, 238, .16); }
.input-wrap:has(.input:focus) .ico { color: var(--cyan); }
.toggle-pw { position: absolute; right: .5rem; display: inline-flex; align-items: center; justify-content: center; width: 30px; height: 30px; border: 0; border-radius: 8px; background: transparent; color: var(--faint); cursor: pointer; }
.toggle-pw:hover { color: var(--muted); background: var(--surface-2); }
.toggle-pw svg { width: 17px; height: 17px; fill: none; stroke: currentColor; stroke-width: 1.7; stroke-linecap: round; stroke-linejoin: round; }

/* 密码强度 EXP */
.pw-strength { display: flex; align-items: center; gap: .7rem; margin-top: .15rem; min-height: 1rem; }
.pw-bar { flex: none; width: 0; height: 5px; border-radius: 999px; background: var(--surface-3); transition: width .4s cubic-bezier(.2, .7, .2, 1), background .3s ease; }
.pw-strength .pw-bar { flex: 1; width: auto; }
.pw-note { font-family: var(--f-mono); font-size: .64rem; letter-spacing: .04em; color: var(--faint); white-space: nowrap; }
.pw-note b { font-weight: 600; }

.error { display: flex; align-items: center; gap: .55rem; font-size: .82rem; color: var(--danger); background: rgba(251, 113, 133, .08); border: 1px solid rgba(251, 113, 133, .3); padding: .6rem .8rem; border-radius: var(--radius-sm); }
.error svg { flex: none; width: 15px; height: 15px; fill: none; stroke: currentColor; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }

.btn-primary { display: inline-flex; align-items: center; justify-content: center; gap: .5rem; width: 100%; margin-top: .3rem; font-family: var(--f-body); font-weight: 700; font-size: .95rem; padding: .85rem 1rem; border: 0; border-radius: var(--radius-sm); cursor: pointer; color: #0a0b10; background: var(--grad); box-shadow: 0 10px 28px -12px rgba(99, 102, 241, .8); transition: transform .15s ease, box-shadow .25s ease; }
.btn-primary:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 14px 34px -10px rgba(99, 102, 241, .95); }
.btn-primary:disabled { opacity: .6; cursor: not-allowed; }
[data-theme="light"] .btn-primary { color: #fff; }
.spinner { width: 16px; height: 16px; border-radius: 50%; border: 2px solid rgba(10, 11, 16, .35); border-top-color: #0a0b10; animation: spin .7s linear infinite; }
[data-theme="light"] .spinner { border-color: rgba(255, 255, 255, .4); border-top-color: #fff; }
@keyframes spin { to { transform: rotate(360deg); } }

.switch-link { text-align: center; margin-top: 1.4rem; font-size: .86rem; color: var(--muted); }
.switch-link a { color: var(--text); font-weight: 600; transition: color .2s ease; }
.switch-link a:hover { color: var(--cyan); }
</style>
