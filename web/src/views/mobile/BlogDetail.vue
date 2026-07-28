<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { listBlogs, deleteBlog } from '../../api/journals'
import { formatDate } from '../../utils/format'
import { useNotifyStore } from '../../stores/notification'
import type { Blog } from '../../types/journal'

const route = useRoute()
const router = useRouter()
const notify = useNotifyStore()
const id = Number(route.params.id)
const blog = ref<Blog | null>(null)
const loading = ref(true)
const notFound = computed(() => !loading.value && !blog.value)

async function load() {
  loading.value = true
  try {
    const all = await listBlogs()
    blog.value = all.find((b) => b.id === id) || null
  } finally { loading.value = false }
}
onMounted(load)

async function onDelete() {
  if (!confirm('删除此日志？')) return
  try { await deleteBlog(id); notify.success('已删除'); router.replace('/blog') } catch { notify.error('删除失败') }
}
</script>

<template>
  <div class="m-screen">
    <div class="m-head">
      <span class="m-head__back" @click="router.push('/blog')">◂</span>
      <span class="m-head__title">日志</span>
    </div>

    <div v-if="loading" class="m-loading">▮ 加载中</div>
    <div v-else-if="notFound" class="m-empty"><div class="m-empty__ico">▤</div><div class="m-empty__txt">日志不存在</div></div>
    <template v-else-if="blog">
      <div class="m-card">
        <div class="m-between"><span class="m-hint">{{ formatDate(blog.created_at) }}</span><span class="m-tag" :class="{ 'm-tag--ok': blog.status === 'published' }">{{ blog.status === 'published' ? '已发布' : '草稿' }}</span></div>
        <div style="font-weight: 700; font-size: 18px; margin: 8px 0;">{{ blog.title }}</div>
        <div class="m-hint m-mb" v-if="blog.summary">{{ blog.summary }}</div>
        <div class="m-flex m-gap m-wrap m-mb" v-if="blog.tags?.length"><span v-for="t in blog.tags" :key="t" class="m-tag">#{{ t }}</span></div>
        <hr class="m-divider" />
        <div style="white-space: pre-wrap; line-height: 1.7; font-size: 14px;">{{ blog.content || '（无内容）' }}</div>
      </div>
      <div class="m-grid-2 m-mt">
        <button class="m-btn" @click="router.push(`/blog/${id}/edit`)">✎ 编辑</button>
        <button class="m-btn m-btn--danger" @click="onDelete">✕ 删除</button>
      </div>
    </template>
  </div>
</template>
