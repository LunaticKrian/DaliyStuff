<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { listTags, createTag, updateTag, deleteTag } from '../api/metadata'
import type { Tag } from '../types/item'
import { useNotifyStore } from '../stores/notification'

const notify = useNotifyStore()

const loading = ref(true)
const error = ref<string | null>(null)
const tags = ref<Tag[]>([])

// New tag form
const showNewForm = ref(false)
const newForm = reactive({ name: '', color: '#41a6f6' })
const saving = ref(false)

// Inline edit
const editingId = ref<number | null>(null)
const editForm = reactive({ name: '', color: '' })

async function loadTags() {
  loading.value = true
  error.value = null
  try {
    tags.value = await listTags()
  } catch (e: any) {
    error.value = e?.message || '加载标签失败'
  } finally {
    loading.value = false
  }
}

function openNewForm() {
  showNewForm.value = true
  newForm.name = ''
  newForm.color = '#41a6f6'
}

function cancelNew() {
  showNewForm.value = false
}

async function handleCreate() {
  if (!newForm.name.trim()) return
  saving.value = true
  try {
    const tag = await createTag({ name: newForm.name.trim(), color: newForm.color })
    tags.value.push(tag)
    showNewForm.value = false
    newForm.name = ''
    newForm.color = '#41a6f6'
    notify.success('标签已创建')
  } catch (e: any) {
    error.value = e?.message || '创建标签失败'
  } finally {
    saving.value = false
  }
}

function startEdit(tag: Tag) {
  editingId.value = tag.id
  editForm.name = tag.name
  editForm.color = tag.color
}

function cancelEdit() {
  editingId.value = null
}

async function handleSaveEdit(id: number) {
  if (!editForm.name.trim()) return
  saving.value = true
  try {
    const updated = await updateTag(id, { name: editForm.name.trim(), color: editForm.color })
    const idx = tags.value.findIndex(t => t.id === id)
    if (idx !== -1) tags.value[idx] = updated
    editingId.value = null
    notify.success('标签已更新')
  } catch (e: any) {
    error.value = e?.message || '更新标签失败'
  } finally {
    saving.value = false
  }
}

async function handleDelete(tag: Tag) {
  if (!window.confirm(`确定要删除标签「${tag.name}」吗？`)) return
  try {
    await deleteTag(tag.id)
    tags.value = tags.value.filter(t => t.id !== tag.id)
    notify.success('标签已删除')
  } catch (e: any) {
    error.value = e?.message || '删除标签失败'
  }
}

onMounted(loadTags)
</script>

<template>
  <div class="tags-page animate-fade-in">
    <!-- Header -->
    <div class="page-header">
      <h1 class="page-title">◎ 标签管理</h1>
      <button class="pixel-btn primary pixel-btn-glow" @click="openNewForm" :disabled="showNewForm">
        + 新增标签
      </button>
    </div>

    <!-- Error banner -->
    <div v-if="error" class="error-banner">
      <span class="error-icon">!</span>
      <span>{{ error }}</span>
      <button class="error-dismiss" @click="error = null">✕</button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <div class="pixel-loading"></div>
      <span class="loading-text">加载中...</span>
    </div>

    <template v-else>
      <!-- New tag form -->
      <div v-if="showNewForm" class="form-card pixel-border animate-fade-in">
        <div class="form-header">
          <h3 class="form-title">+ 新增标签</h3>
        </div>
        <div class="form-body">
          <div class="form-row">
            <div class="form-field">
              <label class="form-label">名称 *</label>
              <input
                v-model="newForm.name"
                type="text"
                class="pixel-input"
                placeholder="标签名称"
                maxlength="30"
                @keydown.enter="handleCreate"
              />
            </div>
            <div class="form-field field-color">
              <label class="form-label">颜色</label>
              <div class="color-picker-wrap">
                <input v-model="newForm.color" type="color" class="color-input" />
                <span class="color-value">{{ newForm.color }}</span>
              </div>
            </div>
          </div>
          <div class="form-actions">
            <button
              class="pixel-btn success pixel-btn-glow"
              @click="handleCreate"
              :disabled="!newForm.name.trim() || saving"
            >
              {{ saving ? '...' : '保存' }}
            </button>
            <button class="pixel-btn" @click="cancelNew">取消</button>
          </div>
        </div>
      </div>

      <!-- Empty state -->
      <div v-if="tags.length === 0 && !showNewForm" class="empty-state animate-fade-in">
        <div class="empty-icon">◎</div>
        <div class="empty-text">还没有标签</div>
        <button class="pixel-btn primary pixel-btn-glow" @click="openNewForm">
          + 创建第一个标签
        </button>
      </div>

      <!-- Tag grid -->
      <div v-if="tags.length > 0" class="tag-grid stagger-list">
        <div
          v-for="tag in tags"
          :key="tag.id"
          class="tag-card"
          :class="{ editing: editingId === tag.id }"
        >
          <!-- Display mode -->
          <template v-if="editingId !== tag.id">
            <div class="card-color-bar" :style="{ background: tag.color }"></div>
            <div class="card-body">
              <div class="card-top">
                <span class="color-dot" :style="{ background: tag.color }"></span>
                <span class="tag-name">{{ tag.name }}</span>
              </div>
              <span class="color-hex">{{ tag.color }}</span>
            </div>
            <div class="card-actions">
              <button class="card-action-btn" @click="startEdit(tag)" title="编辑">✎</button>
              <button class="card-action-btn danger" @click="handleDelete(tag)" title="删除">✕</button>
            </div>
          </template>

          <!-- Edit mode -->
          <template v-else>
            <div class="form-card inline-edit animate-fade-in">
              <div class="form-header">
                <h3 class="form-title">✎ 编辑标签</h3>
                <button class="close-btn" @click="cancelEdit">✕</button>
              </div>
              <div class="form-body">
                <div class="form-row">
                  <div class="form-field">
                    <label class="form-label">名称 *</label>
                    <input
                      v-model="editForm.name"
                      type="text"
                      class="pixel-input"
                      placeholder="标签名称"
                      maxlength="30"
                      @keydown.enter="handleSaveEdit(tag.id)"
                      @keydown.escape="cancelEdit"
                    />
                  </div>
                  <div class="form-field field-color">
                    <label class="form-label">颜色</label>
                    <input v-model="editForm.color" type="color" class="color-input" />
                  </div>
                </div>
                <div class="form-actions">
                  <button
                    class="pixel-btn success pixel-btn-glow"
                    @click="handleSaveEdit(tag.id)"
                    :disabled="!editForm.name.trim() || saving"
                  >
                    {{ saving ? '...' : '保存' }}
                  </button>
                  <button class="pixel-btn" @click="cancelEdit">CANCEL</button>
                </div>
              </div>
            </div>
          </template>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&display=swap');

/* ═══════ 本页令牌：深色默认 + 浅色自适应 ═══════ */
.tags-page {
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
[data-theme="light"] .tags-page {
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

/* ===== Header ===== */
.page-header { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; }
.page-title { font-family: var(--d-f-display); font-size: 18px; font-weight: 700; color: var(--pixel-text); margin: 0; letter-spacing: -.01em; }

/* ===== Buttons ===== */
.pixel-btn { font-family: var(--d-f-body); font-weight: 600; font-size: 13px; padding: 8px 16px; border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); background: var(--pixel-card-bg); color: var(--pixel-text); cursor: pointer; box-shadow: var(--d-shadow-sm); transition: border-color .2s ease, color .2s ease, transform .12s ease, box-shadow .2s ease; white-space: nowrap; }
.pixel-btn:hover { border-color: var(--pixel-text-secondary); color: var(--pixel-text); }
.pixel-btn:active:not(:disabled) { transform: translateY(1px); }
.pixel-btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }

.pixel-btn.primary { background: var(--d-grad); border-color: transparent; color: #0a0b10; box-shadow: 0 8px 22px -10px rgba(99, 102, 241, .8); }
.pixel-btn.primary:hover { border-color: transparent; color: #0a0b10; box-shadow: 0 12px 28px -8px rgba(99, 102, 241, .95); }
[data-theme="light"] .pixel-btn.primary { color: #fff; }

.pixel-btn.success { background: var(--pixel-success); border-color: var(--pixel-success); color: #06231a; box-shadow: 0 8px 22px -10px rgba(52, 211, 153, .7); }
.pixel-btn.success:hover { border-color: var(--pixel-success); color: #06231a; filter: brightness(1.06); }
[data-theme="light"] .pixel-btn.success { color: #fff; }

/* ===== Error ===== */
.error-banner { display: flex; align-items: center; gap: 10px; padding: 10px 14px; background: rgba(251, 113, 133, .1); border: 1px solid var(--pixel-accent); border-radius: var(--d-radius-sm); color: var(--pixel-accent); font-size: 13px; }
.error-icon { font-family: var(--d-f-mono); font-size: 12px; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; background: var(--pixel-accent); color: #fff; border-radius: 6px; flex-shrink: 0; }
.error-dismiss { margin-left: auto; background: none; border: none; color: var(--pixel-accent); font-size: 16px; cursor: pointer; padding: 4px; transition: color .15s ease; }
.error-dismiss:hover { color: var(--pixel-text); }

/* ===== Loading ===== */
.loading-state { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 300px; gap: 16px; }
.loading-text { font-family: var(--d-f-mono); font-size: 12px; color: var(--pixel-text-secondary); letter-spacing: .1em; }

/* ===== Pixel Input ===== */
.pixel-input { font-family: var(--d-f-body); font-size: 13px; padding: 9px 11px; background: var(--pixel-bg-secondary); border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); color: var(--pixel-text); outline: none; width: 100%; box-sizing: border-box; transition: border-color .2s ease, box-shadow .2s ease; }
.pixel-input::placeholder { color: var(--pixel-text-secondary); opacity: .6; }
.pixel-input:focus { border-color: var(--pixel-primary); box-shadow: 0 0 0 3px rgba(34, 211, 238, .16); }

/* ===== Form Card ===== */
.form-card { background: var(--pixel-card-bg); backdrop-filter: blur(10px); border: 1px solid var(--pixel-border); border-radius: var(--d-radius); box-shadow: var(--d-shadow-sm); }
.form-card.inline-edit { border-color: var(--pixel-primary); grid-column: 1 / -1; box-shadow: 0 0 0 3px rgba(34, 211, 238, .14), var(--d-shadow-sm); }

.form-header { display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; border-bottom: 1px solid var(--pixel-border); background: var(--pixel-bg-secondary); }
.form-title { font-family: var(--d-f-display); font-size: 13px; font-weight: 700; color: var(--pixel-primary); margin: 0; }
.close-btn { font-family: var(--d-f-mono); font-size: 13px; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; border: 1px solid var(--pixel-border); border-radius: 8px; background: var(--pixel-bg-secondary); color: var(--pixel-text-secondary); cursor: pointer; padding: 0; transition: border-color .15s ease, color .15s ease; }
.close-btn:hover { border-color: var(--pixel-accent); color: var(--pixel-accent); }

.form-body { padding: 16px; display: flex; flex-direction: column; gap: 12px; }
.form-row { display: flex; gap: 12px; align-items: flex-end; }
.form-field { display: flex; flex-direction: column; gap: 4px; flex: 1; min-width: 0; }
.field-color { flex: 0 0 150px; }
.form-label { font-family: var(--d-f-mono); font-size: 11px; color: var(--pixel-text-secondary); letter-spacing: .02em; }

.color-picker-wrap { display: flex; align-items: center; gap: 8px; }
.color-input { width: 44px; height: 38px; padding: 3px; background: var(--pixel-bg-secondary); border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); cursor: pointer; }
.color-input::-webkit-color-swatch-wrapper { padding: 2px; }
.color-input::-webkit-color-swatch { border: none; border-radius: 6px; }
.color-value { font-family: var(--d-f-mono); font-size: 11px; color: var(--pixel-text-secondary); }

.form-actions { display: flex; gap: 8px; padding-top: 4px; }

/* ===== Tag Grid ===== */
.tag-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.tag-card { background: var(--pixel-card-bg); backdrop-filter: blur(10px); border: 1px solid var(--pixel-border); border-radius: var(--d-radius); box-shadow: var(--d-shadow-sm); display: flex; flex-direction: column; overflow: hidden; transition: border-color .2s ease, transform .12s ease, box-shadow .2s ease; will-change: transform; }
.tag-card:hover { border-color: var(--pixel-primary); transform: translateY(-2px); box-shadow: var(--d-shadow); }
.tag-card.editing { grid-column: 1 / -1; border-color: var(--pixel-primary); }

.card-color-bar { height: 6px; width: 100%; flex-shrink: 0; }
.card-body { padding: 14px 16px; flex: 1; display: flex; flex-direction: column; gap: 6px; }
.card-top { display: flex; align-items: center; gap: 10px; }
.color-dot { width: 14px; height: 14px; flex-shrink: 0; border: 1px solid var(--pixel-border); border-radius: 4px; }
.tag-name { font-family: var(--d-f-display); font-size: 14px; font-weight: 700; color: var(--pixel-text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.color-hex { font-family: var(--d-f-mono); font-size: 10px; color: var(--pixel-text-secondary); letter-spacing: .02em; padding-left: 24px; }

.card-actions { display: flex; border-top: 1px solid var(--pixel-border); }
.card-action-btn { flex: 1; height: 36px; display: flex; align-items: center; justify-content: center; background: var(--pixel-bg-secondary); color: var(--pixel-text-secondary); cursor: pointer; font-size: 14px; padding: 0; border: none; border-right: 1px solid var(--pixel-border); transition: color .15s ease, background .15s ease; }
.card-action-btn:last-child { border-right: none; }
.card-action-btn:hover { color: var(--pixel-primary); background: var(--pixel-card-bg); }
.card-action-btn.danger:hover { color: var(--pixel-accent); }

/* ===== Empty State ===== */
.empty-state { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 16px; min-height: 350px; }
.empty-icon { font-size: 64px; color: var(--pixel-text-secondary); opacity: .4; line-height: 1; animation: pixel-float 3s ease-in-out infinite; }
.empty-text { font-family: var(--d-f-body); font-size: 13px; color: var(--pixel-text-secondary); }

/* ===== Responsive ===== */
@media (max-width: 1024px) {
  .tag-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 640px) {
  .tag-grid { grid-template-columns: 1fr; }
  .form-row { flex-direction: column; align-items: stretch; }
  .field-color { flex: 1; }
  .page-header { flex-direction: column; align-items: flex-start; }
}
</style>
