<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { listBlogs, createBlog, updateBlog } from '../../api/journals'
import { useNotifyStore } from '../../stores/notification'

const route = useRoute()
const router = useRouter()
const notify = useNotifyStore()
const editId = computed(() => (route.params.id ? Number(route.params.id) : null))
const isEdit = computed(() => editId.value !== null)
const loading = ref(false)
const saving = ref(false)

const title = ref('')
const content = ref('')
const summary = ref('')
const tagsStr = ref('')
const status = ref<'draft' | 'published'>('draft')

async function load() {
  if (!isEdit.value) return
  loading.value = true
  try {
    const all = await listBlogs()
    const b = all.find((x) => x.id === editId.value)
    if (b) { title.value = b.title; content.value = b.content || ''; summary.value = b.summary || ''; tagsStr.value = (b.tags || []).join(', '); status.value = b.status }
  } finally { loading.value = false }
}
onMounted(load)

async function onSave(publish: boolean) {
  if (!title.value.trim()) { notify.warning('请填写标题'); return }
  saving.value = true
  const payload = {
    title: title.value.trim(),
    content: content.value,
    summary: summary.value || undefined,
    tags: tagsStr.value.split(/[,，]/).map((t) => t.trim()).filter(Boolean),
    status: publish ? 'published' as const : 'draft' as const,
  }
  try {
    if (isEdit.value && editId.value) {
      await updateBlog(editId.value, payload)
      notify.success('已保存')
      router.replace(`/blog/${editId.value}`)
    } else {
      const b = await createBlog(payload)
      notify.success(publish ? '已发布' : '已存为草稿')
      router.replace(`/blog/${b.id}`)
    }
  } catch { notify.error('保存失败') } finally { saving.value = false }
}
</script>

<template>
  <div class="m-screen">
    <div class="m-head">
      <span class="m-head__back" @click="router.back()">◂</span>
      <span class="m-head__title">{{ isEdit ? '编辑日志' : '新日志' }}</span>
    </div>

    <div v-if="loading" class="m-loading">▮ 加载中</div>
    <template v-else>
      <div class="m-field"><span class="m-field__label">标题</span><input v-model="title" class="m-input" /></div>
      <div class="m-field"><span class="m-field__label">摘要</span><input v-model="summary" class="m-input" /></div>
      <div class="m-field"><span class="m-field__label">正文</span><textarea v-model="content" class="m-textarea" style="min-height: 220px;"></textarea></div>
      <div class="m-field"><span class="m-field__label">标签（逗号分隔）</span><input v-model="tagsStr" class="m-input" placeholder="设计, 移动端" /></div>

      <div class="m-grid-2">
        <button class="m-btn" :disabled="saving" @click="onSave(false)">{{ saving ? '…' : '存草稿' }}</button>
        <button class="m-btn m-btn--primary" :disabled="saving" @click="onSave(true)">{{ saving ? '…' : '发布' }}</button>
      </div>
    </template>
  </div>
</template>
