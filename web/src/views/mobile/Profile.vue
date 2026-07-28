<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const name = computed(() => auth.user?.character_name || auth.user?.username || '冒险者')
const initial = computed(() => (name.value || '?').slice(0, 1).toUpperCase())

const hubs = [
  { to: '/world-map', icon: '❖', color: 'var(--pixel-info)', label: '世界地图' },
  { to: '/stats', icon: '▥', color: 'var(--pixel-info)', label: '统计' },
  { to: '/blog', icon: '▤', color: 'var(--pixel-warning)', label: '冒险日志' },
  { to: '/resume', icon: '❒', color: 'var(--pixel-success)', label: '履历' },
  { to: '/transfer', icon: '⇄', color: 'var(--pixel-warning)', label: '传输' },
  { to: '/items', icon: '◈', color: 'var(--pixel-primary)', label: '物品' },
]
</script>

<template>
  <div class="m-screen">
    <div style="font-weight: 700; font-size: 15px;" class="m-mb">我的 · ADVENTURER</div>

    <div class="m-card m-center">
      <div class="m-avatar m-avatar--lg" style="background: var(--pixel-primary); color: var(--pixel-bg); margin: 0 auto;">{{ initial }}</div>
      <div style="font-weight: 700; font-size: 18px; margin-top: 10px;">{{ name }}</div>
      <div class="m-hint">{{ auth.user?.character_class || '冒险者' }}</div>
    </div>

    <div class="m-section-title">公会模块</div>
    <div class="m-grid-3">
      <div v-for="h in hubs" :key="h.to" class="m-hub" @click="router.push(h.to)">
        <div class="m-hub__ico" :style="{ color: h.color }">{{ h.icon }}</div>
        <div class="m-hub__lbl">{{ h.label }}</div>
      </div>
    </div>

    <div class="m-section-title">设置</div>
    <div class="m-row" @click="router.push('/settings')"><div class="m-row__ico">⚙</div><div class="m-row__main"><div class="m-row__title">设置</div><div class="m-row__sub">应用锁 · 设备会话 · 账户</div></div><div class="m-row__meta" style="color: var(--pixel-info);">▸</div></div>
  </div>
</template>
