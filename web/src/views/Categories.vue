<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { listCategories, createCategory, updateCategory, deleteCategory } from '../api/metadata'
import type { Category } from '../types/item'
import { useNotifyStore } from '../stores/notification'

const notify = useNotifyStore()

interface CategoryForm {
  name: string
  icon: string
  color: string
  sort_order: number
  parent_id: number | null
}

const categories = ref<Category[]>([])
const loading = ref(true)
const error = ref('')

// Create form state
const showCreateForm = ref(false)
const createForm = ref<CategoryForm>({
  name: '',
  icon: '▦',
  color: '#41a6f6',
  sort_order: 0,
  parent_id: null,
})
const creating = ref(false)
const createError = ref('')

// Edit state
const editingId = ref<number | null>(null)
const editForm = ref<CategoryForm>({
  name: '',
  icon: '',
  color: '#41a6f6',
  sort_order: 0,
  parent_id: null,
})
const saving = ref(false)
const editError = ref('')

// Delete state
const deleteTarget = ref<Category | null>(null)
const deleting = ref(false)
const deleteError = ref('')

// Parent options: exclude currently editing category and its descendants
const parentOptions = computed(() => {
  const excludeId = editingId.value
  if (!excludeId) return categories.value
  return categories.value.filter(c => c.id !== excludeId)
})

function resetCreateForm() {
  createForm.value = {
    name: '',
    icon: '▦',
    color: '#41a6f6',
    sort_order: categories.value.length,
    parent_id: null,
  }
  createError.value = ''
}

function resetEditForm() {
  editingId.value = null
  editForm.value = { name: '', icon: '', color: '#41a6f6', sort_order: 0, parent_id: null }
  editError.value = ''
}

async function loadCategories() {
  loading.value = true
  error.value = ''
  try {
    categories.value = await listCategories()
  } catch (e: any) {
    error.value = '加载分类失败'
    console.error('Load categories error', e)
  } finally {
    loading.value = false
  }
}

async function handleCreate() {
  if (!createForm.value.name.trim()) {
    createError.value = '分类名称不能为空'
    return
  }
  creating.value = true
  createError.value = ''
  try {
    const payload: any = {
      name: createForm.value.name.trim(),
      icon: createForm.value.icon || undefined,
      color: createForm.value.color || undefined,
      sort_order: createForm.value.sort_order || undefined,
      parent_id: createForm.value.parent_id || undefined,
    }
    const newCat = await createCategory(payload)
    categories.value.push(newCat)
    showCreateForm.value = false
    resetCreateForm()
    notify.success('分类已创建')
  } catch (e: any) {
    createError.value = '创建失败，请重试'
    notify.error(createError.value)
    console.error('Create category error', e)
  } finally {
    creating.value = false
  }
}

function startEdit(cat: Category) {
  editingId.value = cat.id
  editForm.value = {
    name: cat.name,
    icon: cat.icon || '▦',
    color: cat.color || '#41a6f6',
    sort_order: cat.sort_order,
    parent_id: cat.parent_id,
  }
  editError.value = ''
}

async function handleSave() {
  if (!editForm.value.name.trim()) {
    editError.value = '分类名称不能为空'
    return
  }
  saving.value = true
  editError.value = ''
  try {
    const payload: any = {
      name: editForm.value.name.trim(),
      icon: editForm.value.icon || undefined,
      color: editForm.value.color || undefined,
      sort_order: editForm.value.sort_order || undefined,
      parent_id: editForm.value.parent_id || undefined,
    }
    const updated = await updateCategory(editingId.value!, payload)
    const idx = categories.value.findIndex(c => c.id === updated.id)
    if (idx !== -1) categories.value[idx] = updated
    resetEditForm()
    notify.success('分类已更新')
  } catch (e: any) {
    editError.value = '保存失败，请重试'
    notify.error(editError.value)
    console.error('Update category error', e)
  } finally {
    saving.value = false
  }
}

function confirmDelete(cat: Category) {
  deleteTarget.value = cat
  deleteError.value = ''
}

async function handleDelete() {
  if (!deleteTarget.value) return
  deleting.value = true
  deleteError.value = ''
  try {
    await deleteCategory(deleteTarget.value.id)
    categories.value = categories.value.filter(c => c.id !== deleteTarget.value!.id)
    deleteTarget.value = null
    notify.success('分类已删除')
  } catch (e: any) {
    if (e?.response?.status === 400) {
      deleteError.value = '该分类下存在物品，无法删除'
    } else {
      deleteError.value = '删除失败，请重试'
    }
    console.error('Delete category error', e)
  } finally {
    deleting.value = false
  }
}

function openCreate() {
  resetCreateForm()
  showCreateForm.value = true
}

onMounted(loadCategories)
</script>

<template>
  <div class="categories-page animate-fade-in">
    <!-- Header -->
    <div class="page-header">
      <h1 class="page-title">▦ 分类管理</h1>
      <button class="pixel-btn pixel-btn-glow primary" @click="openCreate" :disabled="loading">
        + 新增分类
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <div class="pixel-loading"></div>
      <span class="loading-text">加载中...</span>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="error-state">
      <div class="error-icon">!</div>
      <span class="error-text">{{ error }}</span>
      <button class="pixel-btn pixel-btn-glow" @click="loadCategories">重试</button>
    </div>

    <!-- Content -->
    <template v-else>
      <!-- Create Form (inline, expandable) -->
      <div v-if="showCreateForm" class="form-card animate-fade-in">
        <div class="form-header">
          <h3 class="form-title">+ 新增分类</h3>
          <button class="pixel-btn-close" @click="showCreateForm = false">✕</button>
        </div>
        <div class="form-body">
          <div class="form-grid">
            <div class="form-field">
              <label class="form-label">名称 *</label>
              <input
                v-model="createForm.name"
                type="text"
                class="pixel-input"
                placeholder="分类名称"
                maxlength="30"
                @keyup.enter="handleCreate"
              />
            </div>
            <div class="form-field">
              <label class="form-label">图标</label>
              <input
                v-model="createForm.icon"
                type="text"
                class="pixel-input icon-input"
                placeholder="▦"
                maxlength="4"
              />
            </div>
            <div class="form-field">
              <label class="form-label">颜色</label>
              <div class="color-picker-wrap">
                <input
                  v-model="createForm.color"
                  type="color"
                  class="pixel-color"
                />
                <span class="color-value">{{ createForm.color }}</span>
              </div>
            </div>
            <div class="form-field">
              <label class="form-label">排序</label>
              <input
                v-model.number="createForm.sort_order"
                type="number"
                class="pixel-input"
                min="0"
              />
            </div>
          </div>
          <div class="form-field">
            <label class="form-label">父分类</label>
            <select v-model="createForm.parent_id" class="pixel-select">
              <option :value="null">— 无 —</option>
              <option
                v-for="cat in categories"
                :key="cat.id"
                :value="cat.id"
              >{{ cat.icon || '▦' }} {{ cat.name }}</option>
            </select>
          </div>
          <div v-if="createError" class="form-error">{{ createError }}</div>
          <div class="form-actions">
            <button
              class="pixel-btn pixel-btn-glow success"
              @click="handleCreate"
              :disabled="creating"
            >
              {{ creating ? '保存中...' : '确认新增' }}
            </button>
            <button class="pixel-btn pixel-btn-glow" @click="showCreateForm = false">取消</button>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-if="categories.length === 0 && !showCreateForm" class="empty-state">
        <div class="empty-icon">▦</div>
        <div class="empty-text">还没有分类</div>
        <button class="pixel-btn pixel-btn-glow primary" @click="openCreate">+ 新增分类</button>
      </div>

      <!-- Category Grid -->
      <div v-else class="category-grid stagger-list">
        <div
          v-for="cat in categories"
          :key="cat.id"
          class="category-card pixel-card-hover"
          :class="{ editing: editingId === cat.id }"
        >
          <!-- Normal Card -->
          <template v-if="editingId !== cat.id">
            <div class="card-icon-area" :style="{ background: cat.color || '#182548' }">
              <span class="card-icon">{{ cat.icon || '▦' }}</span>
            </div>
            <div class="card-body">
              <div class="card-name">{{ cat.name }}</div>
              <div class="card-meta">
                <span v-if="cat.sort_order" class="card-sort">#{{ cat.sort_order }}</span>
                <span
                  v-if="cat.parent_id"
                  class="card-parent"
                >← {{ categories.find(c => c.id === cat.parent_id)?.name || '?' }}</span>
              </div>
            </div>
            <div class="card-color-bar" :style="{ background: cat.color || 'transparent' }"></div>
            <div class="card-actions">
              <button class="pixel-btn-sm" @click="startEdit(cat)" title="编辑">✎</button>
              <button class="pixel-btn-sm danger" @click="confirmDelete(cat)" title="删除">✕</button>
            </div>
          </template>

          <!-- Edit Form (inline) -->
          <template v-else>
            <div class="form-card inline-edit animate-fade-in">
              <div class="form-header">
                <h3 class="form-title">✎ 编辑分类</h3>
                <button class="pixel-btn-close" @click="resetEditForm">✕</button>
              </div>
              <div class="form-body">
                <div class="form-grid">
                  <div class="form-field">
                    <label class="form-label">名称 *</label>
                    <input
                      v-model="editForm.name"
                      type="text"
                      class="pixel-input"
                      placeholder="分类名称"
                      maxlength="30"
                    />
                  </div>
                  <div class="form-field">
                    <label class="form-label">图标</label>
                    <input
                      v-model="editForm.icon"
                      type="text"
                      class="pixel-input icon-input"
                      placeholder="▦"
                      maxlength="4"
                    />
                  </div>
                  <div class="form-field">
                    <label class="form-label">颜色</label>
                    <div class="color-picker-wrap">
                      <input
                        v-model="editForm.color"
                        type="color"
                        class="pixel-color"
                      />
                      <span class="color-value">{{ editForm.color }}</span>
                    </div>
                  </div>
                  <div class="form-field">
                    <label class="form-label">排序</label>
                    <input
                      v-model.number="editForm.sort_order"
                      type="number"
                      class="pixel-input"
                      min="0"
                    />
                  </div>
                </div>
                <div class="form-field">
                  <label class="form-label">父分类</label>
                  <select v-model="editForm.parent_id" class="pixel-select">
                    <option :value="null">— 无 —</option>
                    <option
                      v-for="p in parentOptions"
                      :key="p.id"
                      :value="p.id"
                    >{{ p.icon || '▦' }} {{ p.name }}</option>
                  </select>
                </div>
                <div v-if="editError" class="form-error">{{ editError }}</div>
                <div class="form-actions">
                  <button
                    class="pixel-btn pixel-btn-glow success"
                    @click="handleSave"
                    :disabled="saving"
                  >
                    {{ saving ? '保存中...' : '保存' }}
                  </button>
                  <button class="pixel-btn pixel-btn-glow" @click="resetEditForm">取消</button>
                </div>
              </div>
            </div>
          </template>
        </div>
      </div>
    </template>

    <!-- Delete Confirm Modal -->
    <Teleport to="body">
      <div v-if="deleteTarget" class="modal-overlay" @click.self="deleteTarget = null">
        <div class="modal-card animate-fade-in">
          <div class="modal-header">
            <span class="modal-icon">!</span>
            <h3 class="modal-title">确认删除</h3>
          </div>
          <div class="modal-body">
            <p class="modal-text">
              确定要删除分类 <strong>{{ deleteTarget.name }}</strong> 吗？
            </p>
            <p class="modal-hint">此操作不可撤销。</p>
            <div v-if="deleteError" class="form-error">{{ deleteError }}</div>
          </div>
          <div class="modal-actions">
            <button
              class="pixel-btn pixel-btn-glow accent"
              @click="handleDelete"
              :disabled="deleting"
            >
              {{ deleting ? '删除中...' : '确认删除' }}
            </button>
            <button class="pixel-btn pixel-btn-glow" @click="deleteTarget = null">取消</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&display=swap');

/* ═══════ 本页令牌：深色默认 + 浅色自适应 ═══════ */
.categories-page {
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
  min-height: 100%;
  font-family: var(--d-f-body);
  color: var(--pixel-text);
}
[data-theme="light"] .categories-page {
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

/* ===== Loading / Error ===== */
.loading-state { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 300px; gap: 16px; }
.loading-text { font-family: var(--d-f-mono); font-size: 12px; color: var(--pixel-text-secondary); letter-spacing: .1em; }

.error-state { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 200px; gap: 12px; }
.error-icon { width: 48px; height: 48px; display: flex; align-items: center; justify-content: center; font-family: var(--d-f-mono); font-size: 22px; color: var(--pixel-accent); border: 1px solid var(--pixel-accent); border-radius: var(--d-radius-sm); background: var(--pixel-card-bg); }
.error-text { font-size: 14px; color: var(--pixel-accent); }

/* ===== Page Header ===== */
.page-header { display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
.page-title { font-family: var(--d-f-display); font-size: 18px; font-weight: 700; color: var(--pixel-text); margin: 0; letter-spacing: -.01em; }

/* ===== Buttons ===== */
.pixel-btn { font-family: var(--d-f-body); font-weight: 600; font-size: 13px; padding: 8px 16px; border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); background: var(--pixel-card-bg); color: var(--pixel-text); cursor: pointer; box-shadow: var(--d-shadow-sm); transition: border-color .2s ease, color .2s ease, transform .12s ease, box-shadow .2s ease; white-space: nowrap; }
.pixel-btn:hover { border-color: var(--pixel-text-secondary); color: var(--pixel-text); }
.pixel-btn:active { transform: translateY(1px); }
.pixel-btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }

.pixel-btn.primary { background: var(--d-grad); border-color: transparent; color: #0a0b10; box-shadow: 0 8px 22px -10px rgba(99, 102, 241, .8); }
.pixel-btn.primary:hover { border-color: transparent; color: #0a0b10; box-shadow: 0 12px 28px -8px rgba(99, 102, 241, .95); }
[data-theme="light"] .pixel-btn.primary { color: #fff; }

.pixel-btn.success { background: var(--pixel-success); border-color: var(--pixel-success); color: #06231a; box-shadow: 0 8px 22px -10px rgba(52, 211, 153, .7); }
.pixel-btn.success:hover { border-color: var(--pixel-success); color: #06231a; filter: brightness(1.06); }
[data-theme="light"] .pixel-btn.success { color: #fff; }

.pixel-btn.accent { background: var(--pixel-accent); border-color: var(--pixel-accent); color: #fff; box-shadow: 0 8px 22px -10px rgba(251, 113, 133, .75); }
.pixel-btn.accent:hover { border-color: var(--pixel-accent); color: #fff; filter: brightness(1.06); }

.pixel-btn-close { font-family: var(--d-f-mono); font-size: 13px; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; border: 1px solid var(--pixel-border); border-radius: 8px; background: var(--pixel-bg-secondary); color: var(--pixel-text-secondary); cursor: pointer; padding: 0; transition: border-color .15s ease, color .15s ease; }
.pixel-btn-close:hover { border-color: var(--pixel-accent); color: var(--pixel-accent); }

.pixel-btn-sm { font-size: 14px; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; border: 1px solid var(--pixel-border); background: var(--pixel-bg-secondary); color: var(--pixel-text); cursor: pointer; padding: 0; border-radius: var(--d-radius-sm); transition: border-color .15s ease, color .15s ease, background .15s ease; }
.pixel-btn-sm:hover { border-color: var(--pixel-primary); color: var(--pixel-primary); }
.pixel-btn-sm.danger:hover { border-color: var(--pixel-accent); color: var(--pixel-accent); }

/* ===== Form Card ===== */
.form-card { background: var(--pixel-card-bg); backdrop-filter: blur(10px); border: 1px solid var(--pixel-border); border-radius: var(--d-radius); box-shadow: var(--d-shadow-sm); }
.form-card.inline-edit { border-color: var(--pixel-primary); box-shadow: 0 0 0 3px rgba(34, 211, 238, .14), var(--d-shadow-sm); }

.form-header { display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; border-bottom: 1px solid var(--pixel-border); background: var(--pixel-bg-secondary); }
.form-title { font-family: var(--d-f-display); font-size: 13px; font-weight: 700; color: var(--pixel-primary); margin: 0; }
.form-body { padding: 16px; display: flex; flex-direction: column; gap: 12px; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.form-field { display: flex; flex-direction: column; gap: 4px; }
.form-label { font-family: var(--d-f-mono); font-size: 11px; color: var(--pixel-text-secondary); letter-spacing: .02em; }

.pixel-input { font-family: var(--d-f-body); font-size: 13px; padding: 9px 11px; border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); background: var(--pixel-bg-secondary); color: var(--pixel-text); outline: none; width: 100%; box-sizing: border-box; transition: border-color .2s ease, box-shadow .2s ease; }
.pixel-input:focus { border-color: var(--pixel-primary); box-shadow: 0 0 0 3px rgba(34, 211, 238, .16); }
.pixel-input::placeholder { color: var(--pixel-text-secondary); opacity: .6; }
.icon-input { text-align: center; font-size: 18px; }

.pixel-select { font-family: var(--d-f-body); font-size: 13px; padding: 9px 11px; border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); background: var(--pixel-bg-secondary); color: var(--pixel-text); outline: none; cursor: pointer; width: 100%; box-sizing: border-box; appearance: none; -webkit-appearance: none; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath d='M2 4l4 4 4-4' fill='none' stroke='%239aa3b2' stroke-width='2'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: right 10px center; padding-right: 32px; transition: border-color .2s ease, box-shadow .2s ease; }
.pixel-select:focus { border-color: var(--pixel-primary); box-shadow: 0 0 0 3px rgba(34, 211, 238, .16); }

.color-picker-wrap { display: flex; align-items: center; gap: 8px; }
.pixel-color { width: 40px; height: 38px; border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); background: var(--pixel-bg-secondary); cursor: pointer; padding: 3px; }
.pixel-color::-webkit-color-swatch-wrapper { padding: 0; }
.pixel-color::-webkit-color-swatch { border: none; border-radius: 6px; }
.color-value { font-family: var(--d-f-mono); font-size: 11px; color: var(--pixel-text-secondary); }

.form-error { font-family: var(--d-f-body); font-size: 12px; color: var(--pixel-accent); padding: 8px 10px; border: 1px solid var(--pixel-accent); border-radius: var(--d-radius-sm); background: rgba(251, 113, 133, .1); }
.form-actions { display: flex; gap: 8px; padding-top: 4px; }

/* ===== Empty State ===== */
.empty-state { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 300px; gap: 16px; }
.empty-icon { font-size: 64px; color: var(--pixel-text-secondary); opacity: .4; line-height: 1; }
.empty-text { font-family: var(--d-f-body); font-size: 13px; color: var(--pixel-text-secondary); }

/* ===== Category Grid ===== */
.category-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.category-card { background: var(--pixel-card-bg); backdrop-filter: blur(10px); border: 1px solid var(--pixel-border); border-radius: var(--d-radius); box-shadow: var(--d-shadow-sm); display: flex; flex-direction: column; transition: border-color .2s ease, transform .12s ease, box-shadow .2s ease; will-change: transform; overflow: hidden; }
.category-card:hover { border-color: var(--pixel-primary); transform: translateY(-2px); box-shadow: var(--d-shadow); }
.category-card.editing { grid-column: 1 / -1; border-color: var(--pixel-primary); }

.card-icon-area { height: 72px; display: flex; align-items: center; justify-content: center; position: relative; }
.card-icon { font-size: 32px; color: rgba(255, 255, 255, 0.95); text-shadow: 0 1px 3px rgba(0, 0, 0, .35); line-height: 1; }
.card-body { padding: 12px 14px; flex: 1; display: flex; flex-direction: column; gap: 4px; }
.card-name { font-family: var(--d-f-display); font-size: 14px; font-weight: 600; color: var(--pixel-text); word-break: break-all; line-height: 1.4; }
.card-meta { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.card-sort { font-family: var(--d-f-mono); font-size: 10px; color: var(--pixel-text-secondary); padding: 2px 7px; border: 1px solid var(--pixel-border); border-radius: 999px; background: var(--pixel-bg-secondary); }
.card-parent { font-size: 11px; color: var(--pixel-text-secondary); }
.card-color-bar { height: 4px; width: 100%; }
.card-actions { display: flex; border-top: 1px solid var(--pixel-border); }
.card-actions .pixel-btn-sm { flex: 1; box-shadow: none; border: none; border-right: 1px solid var(--pixel-border); border-radius: 0; width: auto; height: 36px; }
.card-actions .pixel-btn-sm:hover { background: var(--pixel-bg-secondary); }
.card-actions .pixel-btn-sm:last-child { border-right: none; }

/* ===== Modal ===== */
.modal-overlay { position: fixed; inset: 0; background: rgba(7, 9, 18, 0.72); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; z-index: 1000; padding: 20px; }
.modal-card { background: var(--pixel-card-bg); backdrop-filter: blur(14px); border: 1px solid var(--pixel-border); border-radius: var(--d-radius); box-shadow: var(--d-shadow); max-width: 400px; width: 100%; animation: pixel-scale-in 0.2s ease-out; }
.modal-header { display: flex; align-items: center; gap: 10px; padding: 14px 16px; border-bottom: 1px solid var(--pixel-border); background: var(--pixel-bg-secondary); }
.modal-icon { font-family: var(--d-f-mono); font-size: 14px; color: var(--pixel-accent); width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; border: 1px solid var(--pixel-accent); border-radius: 8px; }
.modal-title { font-family: var(--d-f-display); font-size: 14px; font-weight: 700; color: var(--pixel-accent); margin: 0; }
.modal-body { padding: 16px; display: flex; flex-direction: column; gap: 8px; }
.modal-text { font-size: 14px; color: var(--pixel-text); margin: 0; line-height: 1.5; }
.modal-text strong { color: var(--pixel-accent); }
.modal-hint { font-size: 12px; color: var(--pixel-text-secondary); margin: 0; }
.modal-actions { display: flex; gap: 8px; padding: 0 16px 16px; justify-content: flex-end; }

/* ===== Responsive ===== */
@media (max-width: 1024px) {
  .category-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 640px) {
  .category-grid { grid-template-columns: 1fr; }
  .form-grid { grid-template-columns: 1fr; }
  .page-header { flex-direction: column; align-items: flex-start; }
  .modal-card { max-width: 100%; }
}
</style>
