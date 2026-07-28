<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { MdEditor } from 'md-editor-v3'
import 'md-editor-v3/lib/style.css'
import { createBlog, updateBlog, listBlogs } from '../api/journals'
import { api } from '../api/client'
import type { Blog } from '../types/journal'
import { useNotifyStore } from '../stores/notification'

const router = useRouter()
const route = useRoute()
const notify = useNotifyStore()

const isEdit = computed(() => !!route.params.id)
const blogId = computed(() => Number(route.params.id) || 0)

const title = ref('')
const content = ref('')
const summary = ref('')
const coverUrl = ref('')
const tagsInput = ref('')
const status = ref<'draft' | 'published'>('draft')
const loading = ref(false)
const saving = ref(false)

const coverFileInput = ref<HTMLInputElement | null>(null)

async function loadBlog() {
  if (!isEdit.value) return
  loading.value = true
  try {
    const blogs = await listBlogs()
    const blog = blogs.find((b: Blog) => b.id === blogId.value)
    if (!blog) { notify.error('博客不存在'); router.push('/blog'); return }
    title.value = blog.title
    content.value = blog.content || ''
    summary.value = blog.summary || ''
    coverUrl.value = blog.cover_url || ''
    tagsInput.value = blog.tags.join(', ')
    status.value = blog.status
  } catch {
    notify.error('加载失败')
  } finally {
    loading.value = false
  }
}

function triggerCoverUpload() {
  coverFileInput.value?.click()
}

async function handleCoverUpload(event: Event) {
  const target = event.target as HTMLInputElement
  if (!target.files?.length) return
  const file = target.files[0]
  if (!file.type.startsWith('image/')) return
  try {
    const formData = new FormData()
    formData.append('file', file)
    const data = await api<{ url: string }>('/journals/blog/upload', {
      method: 'POST',
      body: formData,
    })
    coverUrl.value = data.url
  } catch {
    notify.error('上传失败')
  }
}

async function handleSave(publishStatus: 'draft' | 'published') {
  if (!title.value.trim()) { notify.error('请输入标题'); return }
  saving.value = true
  const tags = tagsInput.value.split(/[,，]/).map(t => t.trim()).filter(Boolean)
  const payload = {
    title: title.value.trim(),
    content: content.value,
    summary: summary.value || undefined,
    cover_url: coverUrl.value || undefined,
    tags,
    status: publishStatus,
  }
  try {
    if (isEdit.value) {
      await updateBlog(blogId.value, payload)
      notify.success('已保存')
    } else {
      await createBlog(payload)
      notify.success(publishStatus === 'published' ? '已发布' : '已保存草稿')
    }
    router.push('/blog')
  } catch {
    notify.error('保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(loadBlog)
</script>

<template>
  <div class="editor-page">
    <div v-if="loading" class="loading-state"><div class="pixel-loading"></div></div>

    <div v-else class="editor-layout">
      <div class="editor-top-bar">
        <button class="back-btn" @click="router.push('/blog')">◀ 返回</button>
        <div class="editor-actions">
          <button class="save-btn draft" :disabled="saving" @click="handleSave('draft')">
            {{ saving ? '...' : '保存草稿' }}
          </button>
          <button class="save-btn publish" :disabled="saving" @click="handleSave('published')">
            {{ saving ? '...' : '发布' }}
          </button>
        </div>
      </div>

      <div class="meta-section pixel-border">
        <input v-model="title" type="text" class="meta-title" placeholder="博客标题..." maxlength="200" />

        <div class="meta-row">
          <div class="meta-field">
            <label class="meta-label">封面</label>
            <div class="cover-upload" @click="triggerCoverUpload">
              <img v-if="coverUrl" :src="coverUrl" alt="Cover" class="cover-preview" />
              <span v-else class="cover-placeholder">+ 上传封面</span>
            </div>
            <input ref="coverFileInput" type="file" accept="image/*" class="hidden-input" @change="handleCoverUpload" />
          </div>
          <div class="meta-fields-col">
            <div class="meta-field">
              <label class="meta-label">摘要</label>
              <textarea v-model="summary" class="meta-textarea" placeholder="简短描述..." rows="2" maxlength="500"></textarea>
            </div>
            <div class="meta-field">
              <label class="meta-label">标签 (逗号分隔)</label>
              <input v-model="tagsInput" type="text" class="meta-input" placeholder="旅行, 技术, 生活..." />
            </div>
          </div>
        </div>
      </div>

      <div class="editor-section">
        <MdEditor v-model="content" language="zh-CN" :toolbarsExclude="['github']" />
      </div>
    </div>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&display=swap');

/* ═══════ 本页令牌 ═══════ */
.editor-page {
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
  gap: 16px;
  font-family: var(--d-f-body);
  color: var(--pixel-text);
  animation: editor-fade-in 0.3s ease-out;
}
[data-theme="light"] .editor-page {
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

@keyframes editor-fade-in { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }

.loading-state { display: flex; justify-content: center; padding: 60px; }

.editor-layout { display: flex; flex-direction: column; gap: 16px; }

.editor-top-bar { display: flex; justify-content: space-between; align-items: center; gap: 8px; flex-wrap: wrap; }

.back-btn {
  font-family: var(--d-f-body); font-size: 13px; font-weight: 500;
  padding: 7px 14px; border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm);
  background: var(--pixel-card-bg); color: var(--pixel-text-secondary); cursor: pointer;
  transition: color .2s ease, border-color .2s ease;
}
.back-btn:hover { border-color: var(--pixel-primary); color: var(--pixel-primary); }

.editor-actions { display: flex; gap: 8px; }

.save-btn {
  font-family: var(--d-f-body); font-weight: 600; font-size: 13px;
  padding: 9px 16px; border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm);
  cursor: pointer; transition: border-color .2s ease, box-shadow .2s ease, transform .1s ease;
}
.save-btn.draft { background: var(--pixel-card-bg); color: var(--pixel-text); }
.save-btn.publish { background: var(--d-grad); color: #0a0b10; border-color: transparent; box-shadow: 0 8px 22px -10px rgba(99, 102, 241, .8); }
[data-theme="light"] .save-btn.publish { color: #fff; }
.save-btn:hover:not(:disabled) { border-color: var(--pixel-primary); }
.save-btn.publish:hover:not(:disabled) { box-shadow: 0 12px 28px -8px rgba(99, 102, 241, .95); transform: translateY(-1px); }
.save-btn:active:not(:disabled) { transform: translateY(0); }
.save-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* Meta section */
.meta-section {
  background: var(--pixel-card-bg); backdrop-filter: blur(10px);
  border: 1px solid var(--pixel-border); border-radius: var(--d-radius); box-shadow: var(--d-shadow-sm);
  padding: 16px; display: flex; flex-direction: column; gap: 12px;
}

.meta-title {
  font-family: var(--d-f-display); font-size: 18px; font-weight: 700; color: var(--pixel-text);
  background: var(--pixel-bg-secondary); border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm);
  padding: 11px 13px; outline: none; width: 100%; box-sizing: border-box;
  transition: border-color .2s ease, box-shadow .2s ease;
}
.meta-title:focus { border-color: var(--pixel-primary); box-shadow: 0 0 0 3px rgba(34, 211, 238, .16); }
.meta-title::placeholder { color: var(--pixel-text-secondary); opacity: .55; }

.meta-row { display: flex; gap: 16px; }
.meta-fields-col { flex: 1; display: flex; flex-direction: column; gap: 12px; }
.meta-field { display: flex; flex-direction: column; gap: 5px; }
.meta-label { font-family: var(--d-f-mono); font-size: 11px; color: var(--pixel-text-secondary); letter-spacing: .02em; }

.meta-input, .meta-textarea {
  font-family: var(--d-f-body); font-size: 13px; color: var(--pixel-text);
  background: var(--pixel-bg-secondary); border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm);
  padding: 9px 11px; outline: none; width: 100%; box-sizing: border-box;
  transition: border-color .2s ease, box-shadow .2s ease;
}
.meta-textarea { resize: none; line-height: 1.5; }
.meta-input:focus, .meta-textarea:focus { border-color: var(--pixel-primary); box-shadow: 0 0 0 3px rgba(34, 211, 238, .16); }
.meta-input::placeholder, .meta-textarea::placeholder { color: var(--pixel-text-secondary); opacity: .55; }

.cover-upload {
  width: 200px; height: 112px;
  border: 1px dashed var(--pixel-border); border-radius: var(--d-radius-sm);
  background: var(--pixel-bg-secondary); cursor: pointer; overflow: hidden;
  display: flex; align-items: center; justify-content: center;
  transition: border-color .15s ease, background .15s ease;
}
.cover-upload:hover { border-color: var(--pixel-primary); background: color-mix(in srgb, var(--pixel-primary) 6%, var(--pixel-bg-secondary)); }
.cover-preview { width: 100%; height: 100%; object-fit: cover; }
.cover-placeholder { font-family: var(--d-f-body); font-size: 13px; font-weight: 500; color: var(--pixel-text-secondary); }

.hidden-input { display: none; }

.editor-section {
  border: 1px solid var(--pixel-border); border-radius: var(--d-radius); overflow: hidden;
  box-shadow: var(--d-shadow-sm);
}
</style>
