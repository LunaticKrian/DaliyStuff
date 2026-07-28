<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { getOverview, getRecentItems, type OverviewStats, type RecentItem } from '../../api/stats'
import { formatCurrency, formatDate } from '../../utils/format'

const router = useRouter()
const auth = useAuthStore()
const overview = ref<OverviewStats | null>(null)
const recent = ref<RecentItem[]>([])
const loading = ref(true)

const name = computed(() => auth.user?.character_name || auth.user?.username || '冒险者')
const initial = computed(() => (name.value || '?').slice(0, 1).toUpperCase())

const STATUS_LABEL: Record<string, string> = {
  ACTIVE: '使用中', IDLE: '闲置', RETIRED: '退役', SOLD: '已售', DISCARDED: '已弃',
}

async function load() {
  loading.value = true
  try {
    const [ov, rec] = await Promise.all([getOverview(), getRecentItems(4)])
    overview.value = ov
    recent.value = rec
  } catch { /* 静默 */ } finally {
    loading.value = false
  }
}
onMounted(load)
</script>

<template>
  <div class="m-screen">
    <div class="m-between m-mb">
      <span style="font-weight: 700; font-size: 15px;">主城 · GUILD HALL</span>
    </div>

    <!-- 冒险者卡 -->
    <div class="m-card">
      <div class="m-flex m-gap" style="align-items: center;">
        <div class="m-avatar m-avatar--lg" style="background: var(--pixel-primary); color: var(--pixel-bg);">{{ initial }}</div>
        <div style="flex: 1; min-width: 0;">
          <div style="font-weight: 700; font-size: 17px;" class="m-nowrap">{{ name }}</div>
          <div class="m-hint">{{ auth.user?.character_class || '冒险者' }} · 公会登记</div>
        </div>
      </div>
      <div class="m-grid-3" style="margin-top: 14px;" v-if="overview">
        <div class="m-stat"><div class="m-stat__num m-stat__num--gold">{{ formatCurrency(overview.total_assets_value) }}</div><div class="m-stat__lbl">总资产</div></div>
        <div class="m-stat"><div class="m-stat__num">{{ formatCurrency(overview.avg_daily_cost) }}</div><div class="m-stat__lbl">日均/天</div></div>
        <div class="m-stat"><div class="m-stat__num">{{ overview.total_items }}</div><div class="m-stat__lbl">物品</div></div>
      </div>
      <div v-else class="m-loading">▮ 加载中</div>
    </div>

    <!-- 快捷行动 -->
    <div class="m-section-title">快捷行动</div>
    <div class="m-grid-4">
      <div class="m-hub" @click="router.push('/items')"><div class="m-hub__ico" style="color: var(--pixel-primary);">◈</div><div class="m-hub__lbl">物品</div></div>
      <div class="m-hub" @click="router.push('/quests')"><div class="m-hub__ico" style="color: var(--pixel-success);">⚑</div><div class="m-hub__lbl">委托</div></div>
      <div class="m-hub" @click="router.push('/chat')"><div class="m-hub__ico" style="color: var(--pixel-info);">✦</div><div class="m-hub__lbl">智核</div></div>
      <div class="m-hub" @click="router.push('/blog')"><div class="m-hub__ico" style="color: var(--pixel-warning);">▤</div><div class="m-hub__lbl">日志</div></div>
    </div>

    <!-- 近期物品 -->
    <div class="m-section-title">近期物品</div>
    <template v-if="recent.length">
      <div v-for="r in recent" :key="r.id" class="m-row" @click="router.push(`/items/${r.id}`)">
        <div class="m-row__ico" style="background: var(--pixel-primary); color: var(--pixel-bg);">◈</div>
        <div class="m-row__main">
          <div class="m-row__title m-nowrap">{{ r.name }}</div>
          <div class="m-row__sub">{{ STATUS_LABEL[r.status] || r.status }} · {{ formatDate(r.created_at) }}</div>
        </div>
        <div class="m-row__meta">
          <div style="color: var(--pixel-info);">{{ formatCurrency(r.daily_cost) }}</div>
          <div class="m-hint">/ 天</div>
        </div>
      </div>
    </template>
    <div v-else-if="!loading" class="m-empty">
      <div class="m-empty__ico">◈</div>
      <div class="m-empty__txt">还没有物品，去添加一件 →</div>
      <button class="m-btn m-btn--primary m-btn--sm m-mt" @click="router.push('/items/new')">+ 添加物品</button>
    </div>
  </div>
</template>
