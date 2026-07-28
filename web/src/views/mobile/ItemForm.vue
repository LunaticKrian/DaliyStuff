<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getItem, createItem, updateItem } from '../../api/items'
import { listCategories } from '../../api/metadata'
import { useNotifyStore } from '../../stores/notification'
import type { Category } from '../../types/item'

const route = useRoute()
const router = useRouter()
const notify = useNotifyStore()

const editId = computed(() => (route.params.id ? Number(route.params.id) : null))
const isEdit = computed(() => editId.value !== null)
const categories = ref<Category[]>([])
const loading = ref(false)
const saving = ref(false)

const today = new Date().toISOString().slice(0, 10)
const form = ref({
  name: '',
  description: '',
  category_id: null as number | null,
  purchase_date: today,
  purchase_price: '',
  currency: 'CNY',
  purchase_channel: '',
  current_value: '',
  warranty_expiry: '',
  expected_lifespan: '',
  usage_count: '',
})

async function load() {
  loading.value = true
  try {
    categories.value = await listCategories()
    if (isEdit.value && editId.value) {
      const it = await getItem(editId.value)
      form.value = {
        name: it.name,
        description: it.description || '',
        category_id: it.category_id,
        purchase_date: it.purchase_date,
        purchase_price: String(it.purchase_price),
        currency: it.currency,
        purchase_channel: it.purchase_channel || '',
        current_value: it.current_value != null ? String(it.current_value) : '',
        warranty_expiry: it.warranty_expiry || '',
        expected_lifespan: it.expected_lifespan != null ? String(it.expected_lifespan) : '',
        usage_count: it.usage_count != null ? String(it.usage_count) : '',
      }
    }
  } finally {
    loading.value = false
  }
}
onMounted(load)

function num(v: string): number | undefined {
  if (v === '') return undefined
  const n = Number(v)
  return Number.isFinite(n) ? n : undefined
}

async function onSave() {
  if (!form.value.name.trim()) { notify.warning('请填写名称'); return }
  if (!num(form.value.purchase_price)) { notify.warning('请填写购入价'); return }
  saving.value = true
  const payload = {
    name: form.value.name.trim(),
    description: form.value.description || null,
    category_id: form.value.category_id,
    purchase_date: form.value.purchase_date,
    purchase_price: Number(form.value.purchase_price),
    currency: form.value.currency,
    purchase_channel: form.value.purchase_channel || null,
    current_value: num(form.value.current_value) ?? null,
    warranty_expiry: form.value.warranty_expiry || null,
    expected_lifespan: num(form.value.expected_lifespan) ?? null,
    usage_count: num(form.value.usage_count) ?? null,
  }
  try {
    if (isEdit.value && editId.value) {
      await updateItem(editId.value, payload)
      notify.success('已保存')
      router.replace(`/items/${editId.value}`)
    } else {
      const created = await createItem(payload)
      notify.success('已添加')
      router.replace(`/items/${created.id}`)
    }
  } catch {
    notify.error('保存失败')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="m-screen">
    <div class="m-head">
      <span class="m-head__back" @click="router.back()">◂</span>
      <span class="m-head__title">{{ isEdit ? '编辑物品' : '添加物品' }}</span>
    </div>

    <div v-if="loading" class="m-loading">▮ 加载中</div>
    <template v-else>
      <div class="m-section-title">基本信息</div>
      <div class="m-field"><span class="m-field__label">名称</span><input v-model="form.name" class="m-input" /></div>
      <div class="m-field"><span class="m-field__label">描述</span><textarea v-model="form.description" class="m-textarea"></textarea></div>
      <div class="m-field">
        <span class="m-field__label">分类</span>
        <select v-model="form.category_id" class="m-input">
          <option :value="null">未分类</option>
          <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>
      </div>

      <div class="m-section-title">购买信息</div>
      <div class="m-grid-2">
        <div class="m-field"><span class="m-field__label">购入价</span><input v-model="form.purchase_price" type="number" class="m-input" /></div>
        <div class="m-field">
          <span class="m-field__label">币种</span>
          <select v-model="form.currency" class="m-input">
            <option value="CNY">CNY ¥</option><option value="USD">USD $</option>
            <option value="EUR">EUR €</option><option value="JPY">JPY ¥</option>
          </select>
        </div>
      </div>
      <div class="m-grid-2">
        <div class="m-field"><span class="m-field__label">购入日期</span><input v-model="form.purchase_date" type="date" class="m-input" /></div>
        <div class="m-field"><span class="m-field__label">购买渠道</span><input v-model="form.purchase_channel" class="m-input" /></div>
      </div>

      <div class="m-section-title">使用与折旧</div>
      <div class="m-grid-2">
        <div class="m-field"><span class="m-field__label">当前残值</span><input v-model="form.current_value" type="number" class="m-input" /></div>
        <div class="m-field"><span class="m-field__label">预期寿命(天)</span><input v-model="form.expected_lifespan" type="number" class="m-input" /></div>
      </div>
      <div class="m-grid-2">
        <div class="m-field"><span class="m-field__label">保修到期</span><input v-model="form.warranty_expiry" type="date" class="m-input" /></div>
        <div class="m-field"><span class="m-field__label">使用次数</span><input v-model="form.usage_count" type="number" class="m-input" /></div>
      </div>

      <button class="m-btn m-btn--primary m-btn--block" :disabled="saving" @click="onSave">{{ saving ? '保存中…' : '▸ 保存' }}</button>
    </template>
  </div>
</template>
