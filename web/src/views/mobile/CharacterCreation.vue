<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { updateProfile } from '../../api/auth'
import { useNotifyStore } from '../../stores/notification'

const router = useRouter()
const auth = useAuthStore()
const notify = useNotifyStore()

const classes = [
  { key: '炼金术士', icon: '⚗' },
  { key: '剑士', icon: '⚔' },
  { key: '贤者', icon: '✦' },
  { key: '游侠', icon: '⌖' },
]
const selected = ref('剑士')
const name = ref('')
const birthday = ref('')
const loading = ref(false)

async function onSubmit() {
  if (!name.value.trim()) {
    notify.warning('请为角色命名')
    return
  }
  loading.value = true
  try {
    await updateProfile({
      character_name: name.value.trim(),
      character_class: selected.value,
      birthday: birthday.value || undefined,
    })
    await auth.initialize() // 刷新 user，profile_completed → true
    notify.success('踏入公会')
    router.push('/')
  } catch {
    notify.error('档案创建失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="m-screen">
    <div class="m-head">
      <span class="m-head__title">角色创建</span>
    </div>

    <div class="m-card m-center">
      <div class="m-avatar m-avatar--lg" style="margin: 0 auto; background: var(--pixel-primary); color: var(--pixel-bg);">◆</div>
      <div class="m-hint" style="margin-top: 8px;">选择初始职业</div>
    </div>

    <div class="m-grid-2" style="margin-top: 12px;">
      <div v-for="c in classes" :key="c.key" class="m-card m-center m-card--click"
           :style="{ borderColor: selected === c.key ? 'var(--pixel-primary)' : undefined }"
           @click="selected = c.key">
        <div style="font-size: 24px;">{{ c.icon }}</div>
        <div style="font-size: 12px; margin-top: 6px;" :style="{ color: selected === c.key ? 'var(--pixel-info)' : undefined }">{{ c.key }}</div>
      </div>
    </div>

    <div class="m-field" style="margin-top: 14px;">
      <span class="m-field__label">角色名</span>
      <input v-model="name" class="m-input" placeholder="为你的冒险者命名" />
    </div>
    <div class="m-field">
      <span class="m-field__label">诞生日（可选）</span>
      <input v-model="birthday" type="date" class="m-input" />
    </div>

    <button class="m-btn m-btn--primary m-btn--block" :disabled="loading" @click="onSubmit">
      {{ loading ? '创建中…' : '▸ 踏入公会' }}
    </button>
  </div>
</template>
