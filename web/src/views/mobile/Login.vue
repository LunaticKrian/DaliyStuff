<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { useNotifyStore } from '../../stores/notification'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const notify = useNotifyStore()

const username = ref('')
const password = ref('')
const loading = ref(false)

async function onSubmit() {
  if (!username.value || !password.value) {
    notify.warning('请输入账号与密钥')
    return
  }
  loading.value = true
  try {
    await auth.login({ username: username.value, password: password.value })
    notify.success('登入公会')
    const redirect = (route.query.redirect as string) || '/'
    router.push(redirect)
  } catch {
    notify.error('账号或密钥错误')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="m-screen" style="padding-top: 56px;">
    <div class="m-center" style="margin-bottom: 28px;">
      <div class="m-sb__mark" style="width: 22px; height: 22px; margin: 0 auto 14px;" />
      <div style="font-weight: 700; letter-spacing: 2px;">登入公会</div>
      <div class="m-hint">冒险者凭证核验</div>
    </div>

    <div class="m-card">
      <div class="m-field">
        <span class="m-field__label">ADVENTURER ID</span>
        <input v-model="username" class="m-input" placeholder="账号 / 邮箱" @keyup.enter="onSubmit" />
      </div>
      <div class="m-field">
        <span class="m-field__label">SECRET KEY</span>
        <input v-model="password" type="password" class="m-input" placeholder="密钥" @keyup.enter="onSubmit" />
      </div>
      <button class="m-btn m-btn--primary m-btn--block" :disabled="loading" @click="onSubmit">
        {{ loading ? '核验中…' : '▸ 进入主城' }}
      </button>
      <div class="m-between" style="margin-top: 14px;">
        <span class="m-hint">忘记密钥？</span>
        <span class="m-hint" style="color: var(--pixel-info); text-decoration: underline;" @click="router.push('/register')">注册新冒险者 ▸</span>
      </div>
    </div>
  </div>
</template>
