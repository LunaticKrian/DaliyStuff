<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { useNotifyStore } from '../../stores/notification'

const router = useRouter()
const auth = useAuthStore()
const notify = useNotifyStore()

const username = ref('')
const email = ref('')
const password = ref('')
const loading = ref(false)

async function onSubmit() {
  if (!username.value || !password.value) {
    notify.warning('账号与密钥必填')
    return
  }
  loading.value = true
  try {
    await auth.register({
      username: username.value,
      password: password.value,
      email: email.value || undefined,
    })
    notify.success('缔约成功')
    router.push('/')
  } catch {
    notify.error('注册失败，账号可能已存在')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="m-screen" style="padding-top: 56px;">
    <div class="m-head">
      <span class="m-head__back" @click="router.push('/login')">◂</span>
      <span class="m-head__title">注册新冒险者</span>
    </div>

    <div class="m-card">
      <div class="m-field"><span class="m-field__label">ADVENTURER ID</span><input v-model="username" class="m-input" placeholder="账号" /></div>
      <div class="m-field"><span class="m-field__label">EMAIL（可选）</span><input v-model="email" class="m-input" placeholder="邮箱" /></div>
      <div class="m-field"><span class="m-field__label">SECRET KEY</span><input v-model="password" type="password" class="m-input" placeholder="密钥" /></div>
      <button class="m-btn m-btn--primary m-btn--block" :disabled="loading" @click="onSubmit">
        {{ loading ? '缔约中…' : '▸ 缔结契约' }}
      </button>
      <div class="m-hint m-center" style="margin-top: 12px;">注册后将创建你的角色档案</div>
    </div>
  </div>
</template>
