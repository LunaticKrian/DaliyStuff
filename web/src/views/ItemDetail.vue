<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { getItem, deleteItem, changeItemStatus, addCost, deleteCost, uploadImage, deleteImage } from '../api/items'
import { formatCurrency, formatDays, formatDate } from '../utils/format'
import type { Item, AdditionalCost, ItemImage } from '../types/item'

const router = useRouter()
const route = useRoute()
const itemId = Number(route.params.id)

// State
const item = ref<Item | null>(null)
const images = ref<ItemImage[]>([])
const additionalCosts = ref<AdditionalCost[]>([])
const loading = ref(true)
const notFound = ref(false)
const errorMsg = ref('')

// Image gallery
const activeImageIndex = ref(0)

// Status change modal
const showStatusModal = ref(false)
const selectedStatus = ref('')
const statusReason = ref('')

// Add cost form
const showAddCost = ref(false)
const newCost = ref({ name: '', amount: '', date: '' })
const costSubmitting = ref(false)

// Delete confirmation
const showDeleteConfirm = ref(false)
const deleting = ref(false)

// Status change submitting
const statusSubmitting = ref(false)

// Computed
const activeImage = computed(() => {
  if (images.value.length === 0) return null
  return images.value[activeImageIndex.value]?.url ?? null
})

const totalAdditionalCosts = computed(() => {
  return additionalCosts.value.reduce((sum, c) => sum + c.amount, 0)
})

const dailyDepreciation = computed(() => {
  if (!item.value) return null
  if (item.value.current_value == null) return null
  if (item.value.usage_days <= 0) return null
  return (item.value.purchase_price - item.value.current_value) / item.value.usage_days
})

const statusOptions: { value: string; label: string; color: string }[] = [
  { value: 'ACTIVE', label: '使用中', color: '#6BCB77' },
  { value: 'IDLE', label: '闲置', color: '#FFD93D' },
  { value: 'RETIRED', label: '退役', color: '#A0A0B0' },
  { value: 'SOLD', label: '已售出', color: '#3CBBB1' },
  { value: 'DISCARDED', label: '已丢弃', color: '#FF6B6B' },
]

function getStatusColor(status: string): string {
  const map: Record<string, string> = {
    ACTIVE: '#6BCB77',
    IDLE: '#FFD93D',
    RETIRED: '#A0A0B0',
    SOLD: '#3CBBB1',
    DISCARDED: '#FF6B6B',
  }
  return map[status] || '#A0A0B0'
}

function getStatusLabel(status: string): string {
  const map: Record<string, string> = {
    ACTIVE: '使用中',
    IDLE: '闲置',
    RETIRED: '退役',
    SOLD: '已售出',
    DISCARDED: '已丢弃',
  }
  return map[status] || status
}

// Fetch item data
async function fetchItem() {
  loading.value = true
  notFound.value = false
  errorMsg.value = ''
  try {
    const res = await getItem(itemId)
    item.value = res
    // Populate relations from response (backend may embed them)
    if ((res as any).images) images.value = (res as any).images
    if ((res as any).additional_costs) additionalCosts.value = (res as any).additional_costs
  } catch (e: any) {
    if (e?.response?.status === 404 || e?.statusCode === 404) {
      notFound.value = true
    } else {
      errorMsg.value = e?.data?.detail || '加载失败'
    }
  } finally {
    loading.value = false
  }
}

// Actions
function goEdit() {
  router.push(`/items/${itemId}/edit`)
}

function openStatusModal() {
  if (!item.value) return
  selectedStatus.value = item.value.status
  statusReason.value = ''
  showStatusModal.value = true
}

async function confirmStatusChange() {
  if (!selectedStatus.value) return
  statusSubmitting.value = true
  try {
    const res = await changeItemStatus(itemId, selectedStatus.value, statusReason.value || undefined)
    item.value = res
    showStatusModal.value = false
  } catch (e: any) {
    errorMsg.value = e?.data?.detail || '状态更改失败'
  } finally {
    statusSubmitting.value = false
  }
}

function openDeleteConfirm() {
  showDeleteConfirm.value = true
}

async function confirmDelete() {
  deleting.value = true
  try {
    await deleteItem(itemId)
    router.push('/items')
  } catch (e: any) {
    errorMsg.value = e?.data?.detail || '删除失败'
    showDeleteConfirm.value = false
  } finally {
    deleting.value = false
  }
}

// Additional costs
function openAddCost() {
  newCost.value = { name: '', amount: '', date: new Date().toISOString().slice(0, 10) }
  showAddCost.value = true
}

async function submitCost() {
  if (!newCost.value.name || !newCost.value.amount || !newCost.value.date) return
  costSubmitting.value = true
  try {
    const created = await addCost(itemId, {
      name: newCost.value.name,
      amount: Number(newCost.value.amount),
      date: newCost.value.date,
    })
    additionalCosts.value.push(created)
    showAddCost.value = false
  } catch (e: any) {
    errorMsg.value = e?.data?.detail || '添加费用失败'
  } finally {
    costSubmitting.value = false
  }
}

async function removeCost(costId: number) {
  try {
    await deleteCost(costId)
    additionalCosts.value = additionalCosts.value.filter(c => c.id !== costId)
  } catch (e: any) {
    errorMsg.value = e?.data?.detail || '删除费用失败'
  }
}

// Image upload
async function handleImageUpload(event: Event) {
  const input = event.target as HTMLInputElement
  if (!input.files?.length) return
  try {
    const created = await uploadImage(itemId, input.files[0])
    images.value.push(created)
    activeImageIndex.value = images.value.length - 1
  } catch (e: any) {
    errorMsg.value = e?.data?.detail || '上传图片失败'
  }
  input.value = ''
}

async function removeImage(imageId: number) {
  try {
    await deleteImage(imageId)
    images.value = images.value.filter(img => img.id !== imageId)
    if (activeImageIndex.value >= images.value.length) {
      activeImageIndex.value = Math.max(0, images.value.length - 1)
    }
  } catch (e: any) {
    errorMsg.value = e?.data?.detail || '删除图片失败'
  }
}

onMounted(fetchItem)
</script>

<template>
  <div class="item-detail-page">
    <!-- Error banner -->
    <div v-if="errorMsg" class="error-banner">
      <span class="error-icon">!</span>
      {{ errorMsg }}
      <button class="error-close" @click="errorMsg = ''">&times;</button>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="loading-state">
      <div class="pixel-loading"></div>
      <span class="loading-text">加载中...</span>
    </div>

    <!-- 404 state -->
    <div v-else-if="notFound" class="not-found-state">
      <div class="not-found-icon">?</div>
      <h2 class="not-found-title">物品不存在</h2>
      <p class="not-found-desc">该物品可能已被删除或ID无效</p>
      <button class="pixel-btn pixel-btn-glow primary" @click="router.push('/items')">
        &lt; 返回列表
      </button>
    </div>

    <!-- Main content -->
    <template v-else-if="item">
      <!-- Two-column layout -->
      <div class="two-columns">
        <!-- Left column: main info -->
        <div class="column-left">
          <!-- Image gallery -->
          <div class="card image-gallery-card">
            <div class="gallery-main">
              <img
                v-if="activeImage"
                :src="activeImage"
                :alt="item.name"
                class="main-image"
              />
              <div v-else class="image-placeholder">
                <span class="placeholder-icon">&#9670;</span>
              </div>
              <!-- Image controls overlay -->
              <div class="image-controls" v-if="images.length > 0">
                <button
                  class="img-ctrl-btn"
                  @click="activeImageIndex = Math.max(0, activeImageIndex - 1)"
                  :disabled="activeImageIndex === 0"
                >&lt;</button>
                <span class="img-counter">{{ activeImageIndex + 1 }}/{{ images.length }}</span>
                <button
                  class="img-ctrl-btn"
                  @click="activeImageIndex = Math.min(images.length - 1, activeImageIndex + 1)"
                  :disabled="activeImageIndex === images.length - 1"
                >&gt;</button>
              </div>
            </div>
            <!-- Thumbnail strip -->
            <div class="thumbnail-strip" v-if="images.length > 1">
              <div
                v-for="(img, idx) in images"
                :key="img.id"
                class="thumbnail"
                :class="{ active: idx === activeImageIndex }"
                @click="activeImageIndex = idx"
              >
                <img :src="img.url" :alt="`Image ${idx + 1}`" />
              </div>
              <!-- Upload button -->
              <label class="thumbnail upload-thumb">
                <span>+</span>
                <input type="file" accept="image/*" class="hidden-input" @change="handleImageUpload" />
              </label>
            </div>
            <div v-else class="upload-row">
              <label class="upload-btn">
                <span>+ 上传图片</span>
                <input type="file" accept="image/*" class="hidden-input" @change="handleImageUpload" />
              </label>
              <button
                v-if="images.length === 1"
                class="remove-img-btn"
                @click="removeImage(images[0].id)"
              >&times; 删除</button>
            </div>
          </div>

          <!-- Item name & status -->
          <div class="card item-header-card pixel-card-hover">
            <div class="item-name-row">
              <h1 class="item-name">{{ item.name }}</h1>
              <span
                class="status-badge"
                :style="{
                  color: getStatusColor(item.status),
                  borderColor: getStatusColor(item.status),
                  background: getStatusColor(item.status) + '18'
                }"
              >
                {{ getStatusLabel(item.status) }}
              </span>
            </div>
            <div v-if="item.description" class="item-description">
              {{ item.description }}
            </div>
          </div>

          <!-- Item details card -->
          <div class="card details-card pixel-card-hover">
            <div class="card-title">
              <span class="title-bracket">[</span>物品信息<span class="title-bracket">]</span>
            </div>
            <div class="detail-grid">
              <div class="detail-item">
                <span class="detail-label">购买日期</span>
                <span class="detail-value">{{ formatDate(item.purchase_date) }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">购买价格</span>
                <span class="detail-value highlight">{{ formatCurrency(item.purchase_price, item.currency) }}</span>
              </div>
              <div class="detail-item" v-if="item.purchase_channel">
                <span class="detail-label">购买渠道</span>
                <span class="detail-value">{{ item.purchase_channel }}</span>
              </div>
              <div class="detail-item" v-if="item.current_value != null">
                <span class="detail-label">当前价值</span>
                <span class="detail-value">{{ formatCurrency(item.current_value, item.currency) }}</span>
              </div>
              <div class="detail-item" v-if="item.warranty_expiry">
                <span class="detail-label">保修到期</span>
                <span class="detail-value">{{ formatDate(item.warranty_expiry) }}</span>
              </div>
              <div class="detail-item" v-if="item.expected_lifespan">
                <span class="detail-label">预期寿命</span>
                <span class="detail-value">{{ item.expected_lifespan }} 天</span>
              </div>
              <div class="detail-item" v-if="item.usage_count != null">
                <span class="detail-label">使用次数</span>
                <span class="detail-value">{{ item.usage_count }} 次</span>
              </div>
              <div class="detail-item" v-if="item.retired_at">
                <span class="detail-label">退役日期</span>
                <span class="detail-value">{{ formatDate(item.retired_at) }}</span>
              </div>
              <div class="detail-item" v-if="item.retired_reason">
                <span class="detail-label">退役原因</span>
                <span class="detail-value">{{ item.retired_reason }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Right column: stats & actions -->
        <div class="column-right">
          <!-- Cost stats card (CORE FEATURE) -->
          <div class="card stats-card pixel-card-hover">
            <div class="card-title">
              <span class="title-bracket">[</span>成本分析<span class="title-bracket">]</span>
            </div>

            <!-- Daily cost - big display -->
            <div class="stat-hero">
              <div class="stat-hero-label">日均成本</div>
              <div class="stat-hero-value">
                {{ formatCurrency(item.daily_cost, item.currency) }}
              </div>
              <div class="stat-hero-unit">/ 天</div>
            </div>

            <div class="stat-divider"></div>

            <div class="stat-rows">
              <div class="stat-row">
                <span class="stat-row-label">总投入</span>
                <span class="stat-row-value">{{ formatCurrency(item.total_cost, item.currency) }}</span>
              </div>
              <div class="stat-row">
                <span class="stat-row-label">使用天数</span>
                <span class="stat-row-value">{{ formatDays(item.usage_days) }}</span>
              </div>
              <div class="stat-row">
                <span class="stat-row-label">单次成本</span>
                <span class="stat-row-value">
                  {{ item.per_use_cost != null ? formatCurrency(item.per_use_cost, item.currency) : '—' }}
                </span>
              </div>
              <div class="stat-row" v-if="dailyDepreciation != null">
                <span class="stat-row-label">日均损耗</span>
                <span class="stat-row-value accent">{{ formatCurrency(dailyDepreciation, item.currency) }}</span>
              </div>
            </div>

            <div class="stat-divider" v-if="additionalCosts.length > 0"></div>

            <div class="stat-extra" v-if="additionalCosts.length > 0">
              <div class="stat-row">
                <span class="stat-row-label">附加费用合计</span>
                <span class="stat-row-value warning">{{ formatCurrency(totalAdditionalCosts, item.currency) }}</span>
              </div>
            </div>
          </div>

          <!-- Action buttons -->
          <div class="card actions-card">
            <button class="pixel-btn pixel-btn-glow primary" @click="goEdit">
              <span class="btn-icon">&#9998;</span> 编辑
            </button>
            <button class="pixel-btn pixel-btn-glow warning" @click="openStatusModal">
              <span class="btn-icon">&#9651;</span> 状态
            </button>
            <button class="pixel-btn pixel-btn-glow danger" @click="openDeleteConfirm">
              <span class="btn-icon">&#10005;</span> 删除
            </button>
          </div>
        </div>
      </div>

      <!-- Additional costs section (below columns) -->
      <div class="card costs-section">
        <div class="costs-header">
          <div class="card-title">
            <span class="title-bracket">[</span>附加费用<span class="title-bracket">]</span>
          </div>
          <button class="pixel-btn pixel-btn-glow small primary" @click="openAddCost">+ 添加</button>
        </div>

        <!-- Add cost form -->
        <div v-if="showAddCost" class="add-cost-form">
          <div class="form-row">
            <div class="form-field">
              <label class="field-label">名称</label>
              <input v-model="newCost.name" class="pixel-input" placeholder="费用名称" />
            </div>
            <div class="form-field">
              <label class="field-label">金额</label>
              <input v-model="newCost.amount" type="number" step="0.01" class="pixel-input" placeholder="0.00" />
            </div>
            <div class="form-field">
              <label class="field-label">日期</label>
              <input v-model="newCost.date" type="date" class="pixel-input" />
            </div>
          </div>
          <div class="form-actions">
            <button class="pixel-btn pixel-btn-glow small primary" @click="submitCost" :disabled="costSubmitting">
              <span v-if="costSubmitting" class="pixel-loading inline"></span>
              <span v-else>确认</span>
            </button>
            <button class="pixel-btn pixel-btn-glow small" @click="showAddCost = false">取消</button>
          </div>
        </div>

        <!-- Costs list -->
        <div v-if="additionalCosts.length > 0" class="costs-list">
          <div class="cost-item" v-for="cost in additionalCosts" :key="cost.id">
            <div class="cost-info">
              <span class="cost-name">{{ cost.name }}</span>
              <span class="cost-date">{{ formatDate(cost.date) }}</span>
            </div>
            <div class="cost-right">
              <span class="cost-amount">{{ formatCurrency(cost.amount, item.currency) }}</span>
              <button class="cost-delete-btn" @click="removeCost(cost.id)" title="删除">&times;</button>
            </div>
          </div>
          <div class="costs-total">
            <span>合计</span>
            <span class="costs-total-value">{{ formatCurrency(totalAdditionalCosts, item.currency) }}</span>
          </div>
        </div>
        <div v-else class="costs-empty">
          <span class="empty-icon">-</span>
          <span>暂无附加费用</span>
        </div>
      </div>
    </template>

    <!-- Status change modal -->
    <Teleport to="body">
      <div v-if="showStatusModal" class="modal-overlay" @click.self="showStatusModal = false">
        <div class="modal-card">
          <div class="modal-title">
            <span class="title-bracket">[</span>更改状态<span class="title-bracket">]</span>
          </div>
          <div class="modal-body">
            <div class="status-options">
              <label
                v-for="opt in statusOptions"
                :key="opt.value"
                class="status-option"
                :class="{ selected: selectedStatus === opt.value }"
              >
                <input
                  type="radio"
                  :value="opt.value"
                  v-model="selectedStatus"
                  class="hidden-radio"
                />
                <span class="status-dot" :style="{ background: opt.color }"></span>
                <span class="status-label">{{ opt.label }}</span>
              </label>
            </div>
            <div class="modal-field">
              <label class="field-label">原因（可选）</label>
              <textarea
                v-model="statusReason"
                class="pixel-textarea"
                rows="3"
                placeholder="输入状态变更原因..."
              ></textarea>
            </div>
          </div>
          <div class="modal-actions">
            <button class="pixel-btn pixel-btn-glow primary" @click="confirmStatusChange" :disabled="statusSubmitting">
              <span v-if="statusSubmitting" class="pixel-loading inline"></span>
              <span v-else>确认</span>
            </button>
            <button class="pixel-btn pixel-btn-glow" @click="showStatusModal = false">取消</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Delete confirmation modal -->
    <Teleport to="body">
      <div v-if="showDeleteConfirm" class="modal-overlay" @click.self="showDeleteConfirm = false">
        <div class="modal-card modal-confirm">
          <div class="modal-title danger-text">
            <span class="title-bracket">[</span>确认删除<span class="title-bracket">]</span>
          </div>
          <div class="modal-body">
            <p class="confirm-text">
              确定要删除 <strong>{{ item?.name }}</strong> 吗？此操作不可撤销。
            </p>
          </div>
          <div class="modal-actions">
            <button class="pixel-btn pixel-btn-glow danger" @click="confirmDelete" :disabled="deleting">
              <span v-if="deleting" class="pixel-loading inline"></span>
              <span v-else>确认删除</span>
            </button>
            <button class="pixel-btn pixel-btn-glow" @click="showDeleteConfirm = false">取消</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&display=swap');

/* ═══════ 本页令牌：--pixel-* 重映射为高级深色（浅色自适应）═══════ */
.item-detail-page {
  --pixel-bg: #0b0d14;
  --pixel-bg-secondary: #14171f;
  --pixel-card-bg: rgba(255, 255, 255, 0.045);
  --pixel-border: rgba(255, 255, 255, 0.09);
  --pixel-primary: #22d3ee;
  --pixel-accent: #fb7185;
  --pixel-warning: #fbbf24;
  --pixel-success: #34d399;
  --pixel-info: #38bdf8;
  --pixel-text: #f4f6fb;
  --pixel-text-secondary: #9aa3b2;
  --pixel-shadow: rgba(0, 0, 0, 0.5);
  --d-grad: linear-gradient(135deg, #818cf8 0%, #7c5cff 40%, #22d3ee 100%);
  --d-radius: 14px;
  --d-radius-sm: 10px;
  --d-shadow-sm: 0 4px 14px -8px rgba(0, 0, 0, .6);
  --d-shadow: 0 18px 44px -22px rgba(0, 0, 0, .7);
  --d-f-display: 'Space Grotesk', 'PingFang SC', system-ui, sans-serif;
  --d-f-body: 'Inter', 'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif;
  --d-f-mono: 'JetBrains Mono', ui-monospace, monospace;

  display: flex;
  flex-direction: column;
  gap: 20px;
  font-family: var(--d-f-body);
  color: var(--pixel-text);
  animation: pixel-fade-in 0.3s ease-out;
}
[data-theme="light"] .item-detail-page {
  --pixel-bg: #f4f5fa;
  --pixel-bg-secondary: #eef0f7;
  --pixel-card-bg: rgba(17, 20, 40, 0.04);
  --pixel-border: rgba(17, 20, 40, 0.12);
  --pixel-primary: #0891b2;
  --pixel-accent: #e11d48;
  --pixel-warning: #d97706;
  --pixel-success: #059669;
  --pixel-info: #0284c7;
  --pixel-text: #0f1326;
  --pixel-text-secondary: #4b5568;
  --pixel-shadow: rgba(17, 20, 40, .15);
  --d-shadow-sm: 0 4px 14px -8px rgba(17, 20, 40, .2);
  --d-shadow: 0 18px 44px -22px rgba(17, 20, 40, .24);
}

/* Cards */
.card {
  background: var(--pixel-card-bg); backdrop-filter: blur(10px);
  border: 1px solid var(--pixel-border); border-radius: var(--d-radius); box-shadow: var(--d-shadow-sm);
  padding: 18px;
  transition: border-color .2s ease, transform .12s ease;
}
.card.pixel-card-hover:hover { border-color: var(--pixel-primary); }
.card-title { font-family: var(--d-f-mono); font-size: 12px; color: var(--pixel-primary); margin-bottom: 12px; letter-spacing: .02em; }
.title-bracket { color: var(--pixel-border); }

/* Error banner */
.error-banner { background: rgba(251, 113, 133, .1); border: 1px solid var(--pixel-accent); border-radius: var(--d-radius-sm); color: var(--pixel-accent); padding: 10px 14px; display: flex; align-items: center; gap: 10px; font-size: 13px; }
.error-icon { font-family: var(--d-f-mono); font-size: 11px; width: 20px; height: 20px; display: flex; align-items: center; justify-content: center; background: var(--pixel-accent); color: var(--pixel-bg); border-radius: 50%; flex-shrink: 0; font-weight: 700; }
.error-close { margin-left: auto; background: none; border: 0; color: var(--pixel-accent); cursor: pointer; font-size: 20px; padding: 0 4px; line-height: 1; }

/* Loading */
.loading-state { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 300px; gap: 16px; }
.loading-text { font-family: var(--d-f-mono); font-size: 12px; color: var(--pixel-text-secondary); letter-spacing: .1em; }

/* 404 */
.not-found-state { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 300px; gap: 12px; }
.not-found-icon { font-family: var(--d-f-display); font-size: 36px; font-weight: 700; color: var(--pixel-text-secondary); width: 80px; height: 80px; display: flex; align-items: center; justify-content: center; border: 1px solid var(--pixel-border); background: var(--pixel-card-bg); border-radius: var(--d-radius); }
.not-found-title { font-family: var(--d-f-display); font-size: 18px; font-weight: 700; color: var(--pixel-text); margin: 0; }
.not-found-desc { color: var(--pixel-text-secondary); font-size: 13px; margin: 0; }

/* Two columns layout */
.two-columns { display: grid; grid-template-columns: 1fr; gap: 20px; }
@media (min-width: 900px) {
  .two-columns { grid-template-columns: 65fr 35fr; }
}
.column-left, .column-right { display: flex; flex-direction: column; gap: 16px; }

/* Image gallery */
.image-gallery-card { padding: 0; overflow: hidden; }
.gallery-main { position: relative; width: 100%; aspect-ratio: 4 / 3; background: var(--pixel-bg-secondary); display: flex; align-items: center; justify-content: center; overflow: hidden; }
.main-image { width: 100%; height: 100%; object-fit: contain; }
.image-placeholder { display: flex; align-items: center; justify-content: center; width: 100%; height: 100%; }
.placeholder-icon { font-size: 80px; color: var(--pixel-border); opacity: .5; }
.image-controls { position: absolute; bottom: 12px; left: 50%; transform: translateX(-50%); display: flex; align-items: center; gap: 8px; background: rgba(11, 13, 20, .85); backdrop-filter: blur(8px); border: 1px solid var(--pixel-border); border-radius: 999px; padding: 5px 10px; }
.img-ctrl-btn { background: none; border: 1px solid var(--pixel-border); border-radius: 999px; color: var(--pixel-text); cursor: pointer; font-family: var(--d-f-mono); font-size: 12px; padding: 2px 8px; transition: border-color .15s ease, color .15s ease; }
.img-ctrl-btn:disabled { opacity: .3; cursor: default; }
.img-ctrl-btn:not(:disabled):hover { border-color: var(--pixel-primary); color: var(--pixel-primary); }
.img-counter { font-family: var(--d-f-mono); font-size: 11px; color: var(--pixel-text-secondary); min-width: 36px; text-align: center; }

.thumbnail-strip { display: flex; gap: 8px; padding: 12px 14px; border-top: 1px solid var(--pixel-border); overflow-x: auto; }
.thumbnail { width: 56px; height: 56px; border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); cursor: pointer; flex-shrink: 0; overflow: hidden; background: var(--pixel-bg-secondary); display: flex; align-items: center; justify-content: center; transition: border-color .15s ease, box-shadow .15s ease; }
.thumbnail.active { border-color: var(--pixel-primary); box-shadow: 0 0 0 2px rgba(34, 211, 238, .4); }
.thumbnail:hover { border-color: var(--pixel-primary); }
.thumbnail img { width: 100%; height: 100%; object-fit: cover; }
.upload-thumb { color: var(--pixel-text-secondary); font-size: 24px; cursor: pointer; }
.upload-thumb:hover { color: var(--pixel-primary); border-color: var(--pixel-primary); }
.hidden-input { display: none; }
.upload-row { display: flex; align-items: center; gap: 12px; padding: 12px 14px; border-top: 1px solid var(--pixel-border); }
.upload-btn { display: inline-flex; align-items: center; gap: 6px; padding: 7px 12px; border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); color: var(--pixel-text-secondary); cursor: pointer; font-size: 12px; font-family: var(--d-f-body); background: var(--pixel-card-bg); transition: border-color .2s ease, color .2s ease; }
.upload-btn:hover { border-color: var(--pixel-primary); color: var(--pixel-primary); }
.remove-img-btn { background: none; border: 1px solid var(--pixel-accent); border-radius: var(--d-radius-sm); color: var(--pixel-accent); cursor: pointer; font-family: var(--d-f-body); font-size: 12px; padding: 6px 10px; transition: background .2s ease; }
.remove-img-btn:hover { background: rgba(251, 113, 133, .12); }

/* Item header */
.item-header-card { padding: 20px 18px; }
.item-name-row { display: flex; align-items: flex-start; gap: 12px; flex-wrap: wrap; }
.item-name { font-family: var(--d-f-display); font-size: 22px; font-weight: 700; color: var(--pixel-text); margin: 0; line-height: 1.3; word-break: break-word; }
.status-badge { font-family: var(--d-f-mono); font-size: 11px; padding: 3px 10px; border: 1px solid; border-radius: 999px; letter-spacing: .02em; white-space: nowrap; flex-shrink: 0; }
.item-description { margin-top: 12px; padding: 12px 14px; border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); background: var(--pixel-bg-secondary); color: var(--pixel-text-secondary); font-size: 13px; line-height: 1.6; white-space: pre-wrap; word-break: break-word; }

/* Details card */
.detail-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 14px; }
.detail-item { display: flex; flex-direction: column; gap: 4px; }
.detail-label { font-size: 11px; color: var(--pixel-text-secondary); font-family: var(--d-f-mono); }
.detail-value { font-size: 14px; color: var(--pixel-text); }
.detail-value.highlight { color: var(--pixel-primary); font-weight: 600; }

/* ===== STATS CARD (CORE FEATURE) ===== */
.stats-card { border-color: rgba(34, 211, 238, .35); box-shadow: var(--d-shadow-sm), 0 0 28px -10px rgba(34, 211, 238, .25); position: relative; overflow: hidden; }
.stats-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: var(--d-grad); }
.stat-hero { text-align: center; padding: 16px 0 12px; }
.stat-hero-label { font-family: var(--d-f-mono); font-size: 11px; color: var(--pixel-text-secondary); letter-spacing: .15em; margin-bottom: 8px; text-transform: uppercase; }
.stat-hero-value { font-family: var(--d-f-display); font-size: 30px; font-weight: 700; color: var(--pixel-primary); line-height: 1.2; }
.stat-hero-unit { font-family: var(--d-f-mono); font-size: 11px; color: var(--pixel-text-secondary); margin-top: 4px; }
.stat-divider { height: 1px; background: var(--pixel-border); margin: 4px 0; }
.stat-rows { display: flex; flex-direction: column; gap: 4px; padding: 8px 0; }
.stat-row { display: flex; justify-content: space-between; align-items: center; transition: background .15s ease; padding: 5px 8px; border-radius: 6px; }
.stat-row:hover { background: rgba(34, 211, 238, .06); }
.stat-row-label { font-size: 12px; color: var(--pixel-text-secondary); }
.stat-row-value { font-family: var(--d-f-mono); font-size: 13px; color: var(--pixel-text); }
.stat-row-value.accent { color: var(--pixel-accent); }
.stat-row-value.warning { color: var(--pixel-warning); }
.stat-extra { padding-top: 4px; }

/* Action buttons */
.actions-card { display: flex; gap: 8px; flex-wrap: wrap; }

/* Pixel buttons */
.pixel-btn { font-family: var(--d-f-body); font-weight: 600; font-size: 13px; padding: 9px 14px; border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); background: var(--pixel-card-bg); color: var(--pixel-text); cursor: pointer; display: inline-flex; align-items: center; gap: 6px; white-space: nowrap; transition: border-color .2s ease, color .2s ease, background .2s ease, box-shadow .2s ease; }
.pixel-btn:hover { border-color: var(--pixel-text-secondary); }
.pixel-btn:disabled { opacity: .5; cursor: not-allowed; }
.pixel-btn.primary { background: var(--d-grad); border: 0; color: #0a0b10; box-shadow: 0 8px 22px -12px rgba(99, 102, 241, .8); }
.pixel-btn.primary:hover { box-shadow: 0 12px 28px -10px rgba(99, 102, 241, .95); }
[data-theme="light"] .pixel-btn.primary { color: #fff; }
.pixel-btn.warning { background: var(--pixel-warning); border: 0; color: #0a0b10; }
.pixel-btn.warning:hover { background: #fcd34d; }
.pixel-btn.danger { background: var(--pixel-accent); border: 0; color: #fff; }
.pixel-btn.danger:hover { background: #f43f5e; }
.pixel-btn.small { font-size: 12px; padding: 6px 10px; }
.btn-icon { font-size: 14px; }
.inline { display: inline-block; width: 14px; height: 14px; border-width: 2px; }

/* Additional costs section */
.costs-section { margin-top: 4px; }
.costs-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.costs-header .card-title { margin-bottom: 0; }

/* Add cost form */
.add-cost-form { background: var(--pixel-bg-secondary); border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); padding: 12px; margin-bottom: 12px; }
.form-row { display: flex; gap: 12px; flex-wrap: wrap; }
.form-field { display: flex; flex-direction: column; gap: 4px; flex: 1; min-width: 120px; }
.field-label { font-family: var(--d-f-mono); font-size: 11px; color: var(--pixel-text-secondary); letter-spacing: .02em; }

.pixel-input { background: var(--pixel-bg-secondary); border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); color: var(--pixel-text); font-family: var(--d-f-body); font-size: 13px; padding: 9px 11px; outline: none; width: 100%; box-sizing: border-box; transition: border-color .2s ease, box-shadow .2s ease; }
.pixel-input:focus { border-color: var(--pixel-primary); box-shadow: 0 0 0 3px rgba(34, 211, 238, .16); }
.pixel-input::placeholder { color: var(--pixel-text-secondary); opacity: .55; }
.pixel-textarea { background: var(--pixel-bg-secondary); border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); color: var(--pixel-text); font-family: var(--d-f-body); font-size: 13px; padding: 9px 11px; outline: none; width: 100%; box-sizing: border-box; resize: vertical; min-height: 64px; transition: border-color .2s ease, box-shadow .2s ease; }
.pixel-textarea:focus { border-color: var(--pixel-primary); box-shadow: 0 0 0 3px rgba(34, 211, 238, .16); }
.pixel-textarea::placeholder { color: var(--pixel-text-secondary); opacity: .55; }
.form-actions { display: flex; gap: 8px; margin-top: 10px; }

/* Costs list */
.costs-list { display: flex; flex-direction: column; gap: 4px; }
.cost-item { display: flex; justify-content: space-between; align-items: center; padding: 9px 12px; background: var(--pixel-bg-secondary); border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); transition: background .15s ease; }
.cost-item:hover { background: rgba(34, 211, 238, .06); }
.cost-info { display: flex; align-items: center; gap: 12px; flex: 1; min-width: 0; }
.cost-name { font-size: 13px; color: var(--pixel-text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.cost-date { font-family: var(--d-f-mono); font-size: 11px; color: var(--pixel-text-secondary); flex-shrink: 0; }
.cost-right { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.cost-amount { font-family: var(--d-f-mono); font-size: 13px; color: var(--pixel-warning); font-weight: 600; }
.cost-delete-btn { background: none; border: 1px solid transparent; border-radius: 6px; color: var(--pixel-text-secondary); cursor: pointer; font-size: 16px; padding: 2px 6px; line-height: 1; transition: color .15s ease, border-color .15s ease; }
.cost-delete-btn:hover { color: var(--pixel-accent); border-color: var(--pixel-accent); }
.costs-total { display: flex; justify-content: space-between; align-items: center; padding: 10px 12px 4px; border-top: 1px solid var(--pixel-border); margin-top: 6px; }
.costs-total span:first-child { font-size: 12px; color: var(--pixel-text-secondary); }
.costs-total-value { font-family: var(--d-f-mono); font-size: 14px; color: var(--pixel-warning); font-weight: 700; }
.costs-empty { display: flex; align-items: center; justify-content: center; gap: 8px; padding: 20px; color: var(--pixel-text-secondary); font-size: 13px; }
.empty-icon { font-family: var(--d-f-mono); font-size: 14px; }

/* ===== MODAL ===== */
.modal-overlay { position: fixed; inset: 0; background: rgba(0, 0, 0, .7); backdrop-filter: blur(6px); display: flex; align-items: center; justify-content: center; z-index: 200; animation: pixel-fade-in .15s ease-out; }
.modal-card { background: var(--pixel-bg-secondary); border: 1px solid var(--pixel-border); border-radius: var(--d-radius); box-shadow: var(--d-shadow); padding: 22px; min-width: 320px; max-width: 90vw; max-height: 90vh; overflow-y: auto; animation: pixel-scale-in .2s ease-out; }
.modal-title { font-family: var(--d-f-mono); font-size: 12px; color: var(--pixel-primary); margin-bottom: 16px; letter-spacing: .02em; }
.danger-text { color: var(--pixel-accent); }
.modal-body { display: flex; flex-direction: column; gap: 14px; }
.modal-actions { display: flex; gap: 8px; margin-top: 16px; justify-content: flex-end; }
.modal-field { display: flex; flex-direction: column; gap: 6px; }

/* Status options */
.status-options { display: flex; flex-direction: column; gap: 6px; }
.status-option { display: flex; align-items: center; gap: 10px; padding: 9px 12px; border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); cursor: pointer; background: var(--pixel-card-bg); transition: border-color .15s ease, background .15s ease; }
.status-option:hover { border-color: var(--pixel-primary); }
.status-option.selected { border-color: var(--pixel-primary); background: rgba(34, 211, 238, .08); }
.hidden-radio { display: none; }
.status-dot { width: 12px; height: 12px; flex-shrink: 0; border-radius: 50%; }
.status-label { font-size: 13px; color: var(--pixel-text); }
.confirm-text { font-size: 13px; color: var(--pixel-text); line-height: 1.6; margin: 0; }
.confirm-text strong { color: var(--pixel-primary); }
</style>
