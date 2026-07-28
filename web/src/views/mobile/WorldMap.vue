<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { listTodayIntel, getIntelStats, listArchive, generateIntel } from '../../api/intel'
import { REGIONS, type Article, type IntelStats, type ArchivePage, type RegionSlug } from '../../types/intel'
import { useNotifyStore } from '../../stores/notification'

const router = useRouter()
const notify = useNotifyStore()
const stats = ref<IntelStats | null>(null)
const today = ref<Article[]>([])
const region = ref<RegionSlug | null>(null)
const archive = ref<ArchivePage | null>(null)
const loading = ref(true)
const detecting = ref(false)

const regionColor = (slug: RegionSlug) => REGIONS.find((r) => r.slug === slug)?.color || 'var(--pixel-info)'
const regionName = (slug: RegionSlug) => REGIONS.find((r) => r.slug === slug)?.name || slug

async function loadToday() {
  loading.value = true
  try {
    const [s, t] = await Promise.all([getIntelStats(), listTodayIntel()])
    stats.value = s
    today.value = t
  } finally { loading.value = false }
}
async function loadArchive() {
  try { archive.value = await listArchive(region.value, 1) } catch { /* 静默 */ }
}
async function detect() {
  detecting.value = true
  try {
    await generateIntel(true)
    notify.success('侦测完成')
    await loadToday()
  } catch { notify.error('侦测失败，请稍后重试') } finally { detecting.value = false }
}
onMounted(() => { loadToday(); loadArchive() })
</script>

<template>
  <div class="m-screen">
    <div class="m-head">
      <span class="m-head__back" @click="router.push('/me')">◂</span>
      <span class="m-head__title">世界地图</span>
    </div>

    <!-- 信号台 -->
    <div class="m-card">
      <div class="m-between">
        <span class="m-tag m-tag--info m-blink" v-if="stats && stats.todayCount">◉ ON AIR</span>
        <span class="m-tag" v-else>○ 待机</span>
        <button class="m-btn m-btn--sm" :disabled="detecting" @click="detect">{{ detecting ? '侦测中…' : '◎ 发起侦测' }}</button>
      </div>
      <div class="m-grid-3 m-mt" v-if="stats">
        <div class="m-stat"><div class="m-stat__num">{{ stats.todayCount }}</div><div class="m-stat__lbl">今日</div></div>
        <div class="m-stat"><div class="m-stat__num">{{ stats.weekCount }}</div><div class="m-stat__lbl">本周</div></div>
        <div class="m-stat"><div class="m-stat__num">{{ stats.archivedCount }}</div><div class="m-stat__lbl">归档</div></div>
      </div>
    </div>

    <div class="m-section-title">今日情报</div>
    <div v-if="loading" class="m-loading">▮ 加载中</div>
    <template v-else>
      <div v-for="a in today" :key="a.id" class="m-card">
        <div class="m-flex m-gap m-wrap" style="margin-bottom: 6px;">
          <span class="m-tag" :style="{ color: regionColor(a.region), borderColor: regionColor(a.region) }">{{ regionName(a.region) }}</span>
          <span class="m-hint">{{ a.source }} · {{ a.readTime }}</span>
        </div>
        <div style="font-weight: 700;" class="m-nowrap">{{ a.title }}</div>
        <div class="m-hint" style="margin-top: 4px;">{{ a.summary }}</div>
        <a v-if="a.url" :href="a.url" target="_blank" class="m-hint" style="color: var(--pixel-info); margin-top: 6px; display: inline-block;">阅读原文 ▸</a>
      </div>
      <div v-if="!today.length" class="m-empty"><div class="m-empty__ico">❖</div><div class="m-empty__txt">今日暂无情报，可手动侦测</div></div>
    </template>

    <div class="m-section-title">航海日志</div>
    <div class="m-flex m-gap m-wrap m-mb">
      <span class="m-tag m-card--click" :class="{ 'm-tag--info': !region }" @click="region = null; loadArchive()">全部</span>
      <span v-for="r in REGIONS" :key="r.slug" class="m-tag m-card--click"
            :class="{ 'm-tag--info': region === r.slug }" @click="region = r.slug; loadArchive()">{{ r.name }}</span>
    </div>
    <div v-if="archive && archive.items.length">
      <div class="m-hint m-mb">{{ archive.date }} · 第 {{ archive.page }}/{{ archive.totalPages }} 天</div>
      <div v-for="a in archive.items" :key="a.id" class="m-row m-row--bare" style="padding: 6px 0;">
        <div class="m-row__ico" :style="{ background: regionColor(a.region), color: 'var(--pixel-bg)' }">❖</div>
        <div class="m-row__main"><div class="m-row__title m-nowrap">{{ a.title }}</div><div class="m-row__sub">{{ regionName(a.region) }} · {{ a.publishedAt }}</div></div>
      </div>
    </div>
  </div>
</template>
