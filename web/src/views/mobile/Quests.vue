<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { listTasks, completeTask, uncompleteTask, progressTask } from '../../api/tasks'
import { CATEGORY_ICONS, CATEGORY_LABELS, CATEGORY_COLORS, type TaskCategory } from '../../types/task'
import type { Task } from '../../types/task'
import { useNotifyStore } from '../../stores/notification'

const router = useRouter()
const notify = useNotifyStore()
const tasks = ref<Task[]>([])
const loading = ref(true)

const today = computed(() => new Date().toISOString().slice(0, 10))
const doneCount = computed(() => tasks.value.filter((t) => t.completed).length)
const totalExp = computed(() => tasks.value.filter((t) => !t.completed).reduce((s, t) => s + (t.exp_reward || 0), 0))

async function load() {
  loading.value = true
  try {
    tasks.value = await listTasks(today.value)
  } finally {
    loading.value = false
  }
}
onMounted(load)

async function toggle(t: Task) {
  try {
    if (t.completed) {
      tasks.value = tasks.value.map((x) => (x.id === t.id ? { ...x, completed: false } : x))
      await uncompleteTask(t.id)
    } else {
      const res = await completeTask(t.id)
      tasks.value = tasks.value.map((x) => (x.id === t.id ? res.task : x))
      notify.success(`完成 · +${res.exp_gained} EXP${res.leveled_up ? ' · 升级！' : ''}`)
    }
  } catch {
    notify.error('操作失败')
    await load()
  }
}

async function step(t: Task) {
  try {
    const updated = await progressTask(t.id, 1)
    tasks.value = tasks.value.map((x) => (x.id === t.id ? updated : x))
    if (updated.completed) notify.success('委托完成')
  } catch { notify.error('操作失败') }
}
</script>

<template>
  <div class="m-screen">
    <div class="m-between m-mb">
      <span style="font-weight: 700; font-size: 15px;">委托大厅</span>
      <span class="m-hint">{{ doneCount }}/{{ tasks.length }} · 待领 {{ totalExp }} EXP</span>
    </div>

    <button class="m-btn m-btn--block m-mb" @click="router.push('/chat')">
      <span style="color: var(--pixel-info);">✦</span> 召唤 NEXA 生成委托
    </button>

    <div v-if="loading" class="m-loading">▮ 加载中</div>
    <template v-else>
      <div v-for="t in tasks" :key="t.id" class="m-card">
        <div class="m-between">
          <div class="m-flex m-gap" style="align-items: center;">
            <div class="m-row__ico" :style="{ background: CATEGORY_COLORS[t.category as TaskCategory], color: 'var(--pixel-bg)' }">{{ CATEGORY_ICONS[t.category as TaskCategory] }}</div>
            <div>
              <div style="font-weight: 700;" :class="{ 'm-muted': t.completed }">{{ t.title }}</div>
              <div class="m-hint">{{ CATEGORY_LABELS[t.category as TaskCategory] }}<span v-if="t.source === 'ai'"> · AI</span> · +{{ t.exp_reward }} EXP</div>
            </div>
          </div>
          <button class="m-avatar" style="width: 34px; height: 34px; cursor: pointer;"
                  :style="{ background: t.completed ? 'var(--pixel-success)' : 'var(--pixel-card-bg)', color: t.completed ? 'var(--pixel-bg)' : 'var(--pixel-text-secondary)', border: '2px solid var(--pixel-border)' }"
                  @click="toggle(t)">{{ t.completed ? '✓' : '○' }}</button>
        </div>
        <div v-if="t.target && t.target > 1" class="m-flex m-gap" style="align-items: center; margin-top: 10px;">
          <div class="m-meter" style="flex: 1;"><div class="m-meter__fill m-meter__fill--ok" :style="{ width: Math.min(100, (t.progress / t.target) * 100) + '%' }"></div></div>
          <span class="m-mono m-hint">{{ t.progress }}/{{ t.target }}</span>
          <button v-if="!t.completed" class="m-btn m-btn--sm" @click="step(t)">+1</button>
        </div>
      </div>
      <div v-if="!tasks.length" class="m-empty">
        <div class="m-empty__ico">⚑</div>
        <div class="m-empty__txt">今日暂无委托</div>
      </div>
    </template>
  </div>
</template>
