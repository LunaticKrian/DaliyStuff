<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getItem, listCosts, deleteItem, changeItemStatus } from '../../api/items'
import { formatCurrency, formatDays, formatDate } from '../../utils/format'
import { useNotifyStore } from '../../stores/notification'
import type { Item, AdditionalCost } from '../../types/item'

const route = useRoute()
const router = useRouter()
const notify = useNotifyStore()

const id = Number(route.params.id)
const item = ref<Item | null>(null)
const costs = ref<AdditionalCost[]>([])
const loading = ref(true)

const STATUS = [
  { key: 'ACTIVE', label: '使用中' }, { key: 'IDLE', label: '闲置' },
  { key: 'RETIRED', label: '退役' }, { key: 'SOLD', label: '已售' }, { key: 'DISCARDED', label: '已弃' },
]

async function load() {
  loading.value = true
  try {
    const [it, cs] = await Promise.all([getItem(id), listCosts(id)])
    item.value = it
    costs.value = cs
  } catch {
    notify.error('加载失败')
  } finally {
    loading.value = false
  }
}
onMounted(load)

async function onStatus(status: string) {
  if (!item.value) return
  try {
    item.value = await changeItemStatus(id, status)
    notify.success('状态已更新')
  } catch { notify.error('更新失败') }
}
async function onDelete() {
  if (!confirm('移除此物品？')) return
  try {
    await deleteItem(id)
    notify.success('已移除')
    router.replace('/items')
  } catch { notify.error('删除失败') }
}
</script>

<template>
  <div class="m-screen">
    <div class="m-head">
      <span class="m-head__back" @click="router.push('/items')">◂</span>
      <span class="m-head__title">物品详情</span>
    </div>

    <div v-if="loading" class="m-loading">▮ 加载中</div>
    <template v-else-if="item">
      <!-- 日均成本（核心） -->
      <div class="m-card m-center">
        <div style="font-weight: 700; font-size: 17px;">{{ item.name }}</div>
        <div class="m-hint">每天使用价格</div>
        <div class="m-mono" style="font-size: 30px; color: var(--pixel-info);">{{ formatCurrency(item.daily_cost, item.currency) }}<span class="m-hint"> / 天</span></div>
        <div class="m-hint">购入 {{ formatCurrency(item.purchase_price, item.currency) }} · 已用 {{ formatDays(item.usage_days) }}</div>
      </div>

      <!-- 成本拆解 -->
      <div class="m-card">
        <div class="m-card__title">成本拆解</div>
        <div class="m-grid-2">
          <div class="m-stat"><div class="m-stat__num">{{ formatCurrency(item.purchase_price, item.currency) }}</div><div class="m-stat__lbl">购入价</div></div>
          <div class="m-stat"><div class="m-stat__num m-stat__num--gold">{{ formatCurrency(item.total_cost, item.currency) }}</div><div class="m-stat__lbl">总消耗</div></div>
          <div class="m-stat"><div class="m-stat__num">{{ formatDays(item.usage_days) }}</div><div class="m-stat__lbl">使用天数</div></div>
          <div class="m-stat" v-if="item.current_value != null"><div class="m-stat__num">{{ formatCurrency(item.current_value, item.currency) }}</div><div class="m-stat__lbl">当前残值</div></div>
        </div>
        <hr class="m-divider" />
        <div class="m-between"><span class="m-hint">预期寿命</span><span class="m-mono">{{ item.expected_lifespan ? item.expected_lifespan + ' 天' : '—' }}</span></div>
        <div class="m-between"><span class="m-hint">保修到期</span><span class="m-mono">{{ item.warranty_expiry ? formatDate(item.warranty_expiry) : '—' }}</span></div>
        <div class="m-between" v-if="item.per_use_cost != null"><span class="m-hint">每次使用</span><span class="m-mono">{{ formatCurrency(item.per_use_cost, item.currency) }}</span></div>
      </div>

      <!-- 附加成本 -->
      <div class="m-card" v-if="costs.length">
        <div class="m-card__title">附加成本 <span class="m-tag m-tag--warn">+{{ formatCurrency(costs.reduce((s, c) => s + Number(c.amount), 0), item.currency) }}</span></div>
        <div v-for="c in costs" :key="c.id" class="m-row m-row--bare">
          <div class="m-row__ico" style="background: var(--pixel-card-bg); color: var(--pixel-text-secondary);">+</div>
          <div class="m-row__main"><div class="m-row__title">{{ c.name }}</div><div class="m-row__sub">{{ formatDate(c.date) }}{{ c.description ? ' · ' + c.description : '' }}</div></div>
          <div class="m-row__meta">{{ formatCurrency(Number(c.amount), item.currency) }}</div>
        </div>
      </div>

      <!-- 状态 -->
      <div class="m-card">
        <div class="m-card__title">状态</div>
        <div class="m-seg">
          <div v-for="s in STATUS" :key="s.key" class="m-seg__btn" :class="{ active: item.status === s.key }" @click="onStatus(s.key)">{{ s.label }}</div>
        </div>
      </div>

      <div class="m-grid-2">
        <button class="m-btn" @click="router.push(`/items/${id}/edit`)">✎ 编辑</button>
        <button class="m-btn m-btn--danger" @click="onDelete">✕ 移除</button>
      </div>
    </template>
  </div>
</template>
