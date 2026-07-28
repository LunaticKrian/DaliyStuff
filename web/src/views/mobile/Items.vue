<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { listItems } from '../../api/items'
import { getOverview, type OverviewStats } from '../../api/stats'
import { listCategories } from '../../api/metadata'
import { formatCurrency, formatDays } from '../../utils/format'
import type { Item, Category } from '../../types/item'

const router = useRouter()
const overview = ref<OverviewStats | null>(null)
const items = ref<Item[]>([])
const categories = ref<Category[]>([])
const loading = ref(true)
const keyword = ref('')
const statusFilter = ref('')

const STATUS = [
  { key: '', label: '全部' },
  { key: 'ACTIVE', label: '使用中' },
  { key: 'IDLE', label: '闲置' },
  { key: 'RETIRED', label: '退役' },
]
const STATUS_LABEL: Record<string, string> = { ACTIVE: '使用中', IDLE: '闲置', RETIRED: '退役', SOLD: '已售', DISCARDED: '已弃' }
const STATUS_TAG: Record<string, string> = { ACTIVE: 'm-tag--ok', IDLE: 'm-tag--warn', RETIRED: '', SOLD: 'm-tag--info', DISCARDED: 'm-tag--danger' }

const catName = computed(() => {
  const m = new Map(categories.value.map((c) => [c.id, c.name]))
  return (id: number | null) => (id != null ? m.get(id) || '' : '')
})

async function load() {
  loading.value = true
  try {
    const [ov, cats, res] = await Promise.all([
      getOverview(),
      listCategories(),
      listItems({ keyword: keyword.value || undefined, status: statusFilter.value || undefined, page_size: 50 }),
    ])
    overview.value = ov
    categories.value = cats
    items.value = res.items
  } catch { /* 静默 */ } finally {
    loading.value = false
  }
}
onMounted(load)
</script>

<template>
  <div class="m-screen">
    <div class="m-between m-mb">
      <span style="font-weight: 700; font-size: 15px;">物品管理</span>
      <span class="m-hint">{{ overview?.total_items ?? items.length }} 件</span>
    </div>

    <!-- 汇总 -->
    <div class="m-card" v-if="overview">
      <div class="m-grid-3">
        <div class="m-stat"><div class="m-stat__num m-stat__num--gold">{{ formatCurrency(overview.total_assets_value) }}</div><div class="m-stat__lbl">总资产</div></div>
        <div class="m-stat"><div class="m-stat__num">{{ formatCurrency(overview.avg_daily_cost) }}</div><div class="m-stat__lbl">日均/天</div></div>
        <div class="m-stat"><div class="m-stat__num">{{ overview.active_items }}</div><div class="m-stat__lbl">使用中</div></div>
      </div>
    </div>

    <div class="m-seg m-mt">
      <div v-for="s in STATUS" :key="s.key" class="m-seg__btn" :class="{ active: statusFilter === s.key }" @click="statusFilter = s.key; load()">{{ s.label }}</div>
    </div>
    <input v-model="keyword" class="m-input m-mt" placeholder="检索物品…" @keyup.enter="load" />

    <div v-if="loading" class="m-loading">▮ 加载中</div>
    <template v-else>
      <div v-for="it in items" :key="it.id" class="m-card m-card--click" @click="router.push(`/items/${it.id}`)">
        <div class="m-between">
          <div class="m-flex m-gap" style="align-items: center;">
            <div class="m-row__ico" style="background: var(--pixel-primary); color: var(--pixel-bg);">◈</div>
            <div>
              <div style="font-weight: 700;" class="m-nowrap">{{ it.name }}</div>
              <div class="m-hint">{{ catName(it.category_id) || '未分类' }} · 购入 {{ formatCurrency(it.purchase_price, it.currency) }} · 已用 {{ formatDays(it.usage_days) }}</div>
            </div>
          </div>
          <span class="m-tag" :class="STATUS_TAG[it.status]">{{ STATUS_LABEL[it.status] }}</span>
        </div>
        <div class="m-grid-2" style="margin-top: 10px;">
          <div class="m-stat"><div class="m-stat__num">{{ formatCurrency(it.daily_cost, it.currency) }}</div><div class="m-stat__lbl">每天使用价格</div></div>
          <div class="m-stat"><div class="m-stat__num m-stat__num--gold">{{ formatCurrency(it.total_cost, it.currency) }}</div><div class="m-stat__lbl">总消耗</div></div>
        </div>
      </div>
      <div v-if="!items.length" class="m-empty">
        <div class="m-empty__ico">◈</div>
        <div class="m-empty__txt">暂无物品</div>
      </div>
    </template>

    <button class="m-fab" @click="router.push('/items/new')">+</button>
  </div>
</template>
