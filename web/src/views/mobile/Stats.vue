<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getOverview, getByCategory, getDailyCostRank, type OverviewStats, type CategoryStat, type DailyCostRankItem } from '../../api/stats'
import { formatCurrency } from '../../utils/format'

const router = useRouter()
const overview = ref<OverviewStats | null>(null)
const cats = ref<CategoryStat[]>([])
const rank = ref<DailyCostRankItem[]>([])
const loading = ref(true)

async function load() {
  loading.value = true
  try {
    const [ov, c, r] = await Promise.all([getOverview(), getByCategory(), getDailyCostRank(8)])
    overview.value = ov
    cats.value = c
    rank.value = r
  } finally { loading.value = false }
}
onMounted(load)
</script>

<template>
  <div class="m-screen">
    <div class="m-head">
      <span class="m-head__back" @click="router.push('/me')">◂</span>
      <span class="m-head__title">统计</span>
    </div>

    <div v-if="loading" class="m-loading">▮ 加载中</div>
    <template v-else>
      <div class="m-grid-2" v-if="overview">
        <div class="m-stat"><div class="m-stat__num m-stat__num--gold">{{ formatCurrency(overview.total_assets_value) }}</div><div class="m-stat__lbl">总资产</div></div>
        <div class="m-stat"><div class="m-stat__num">{{ formatCurrency(overview.avg_daily_cost) }}</div><div class="m-stat__lbl">日均/天</div></div>
        <div class="m-stat"><div class="m-stat__num">{{ overview.total_items }}</div><div class="m-stat__lbl">物品总数</div></div>
        <div class="m-stat"><div class="m-stat__num">{{ overview.active_items }}</div><div class="m-stat__lbl">使用中</div></div>
      </div>

      <div class="m-section-title">日均成本榜</div>
      <div v-for="r in rank" :key="r.id" class="m-row" @click="router.push(`/items/${r.id}`)">
        <div class="m-row__ico" style="background: var(--pixel-primary); color: var(--pixel-bg);">◈</div>
        <div class="m-row__main"><div class="m-row__title m-nowrap">{{ r.name }}</div><div class="m-row__sub">{{ formatCurrency(r.purchase_price) }} · 已用 {{ r.usage_days }} 天</div></div>
        <div class="m-row__meta" style="color: var(--pixel-info);">{{ formatCurrency(r.daily_cost) }}<div class="m-hint">/ 天</div></div>
      </div>

      <div class="m-section-title">分类分布</div>
      <div class="m-card">
        <div v-for="c in cats" :key="c.category_id ?? 'none'" class="m-between" style="margin-bottom: 8px;">
          <span class="m-nowrap" style="font-size: 13px;">{{ c.category_name }} <span class="m-hint">{{ c.item_count }} 件</span></span>
          <span class="m-mono" style="color: var(--pixel-info);">{{ formatCurrency(c.avg_daily_cost) }}/天</span>
        </div>
        <div v-if="!cats.length" class="m-hint">暂无数据</div>
      </div>
    </template>
  </div>
</template>
