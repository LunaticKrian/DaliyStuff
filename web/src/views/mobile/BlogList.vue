<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { listBlogs } from '../../api/journals'
import { formatDate } from '../../utils/format'
import type { Blog } from '../../types/journal'

const router = useRouter()
const blogs = ref<Blog[]>([])
const loading = ref(true)

async function load() {
  loading.value = true
  try { blogs.value = await listBlogs() } finally { loading.value = false }
}
onMounted(load)
</script>

<template>
  <div class="m-screen">
    <div class="m-head">
      <span class="m-head__back" @click="router.push('/me')">◂</span>
      <span class="m-head__title">冒险日志</span>
      <span class="m-head__sub">{{ blogs.length }} 篇</span>
    </div>

    <div v-if="loading" class="m-loading">▮ 加载中</div>
    <template v-else>
      <div v-for="b in blogs" :key="b.id" class="m-card m-card--click" @click="router.push(`/blog/${b.id}`)">
        <div class="m-between">
          <span class="m-hint">{{ formatDate(b.created_at) }}</span>
          <span class="m-tag" :class="{ 'm-tag--ok': b.status === 'published', 'm-tag--warn': b.status === 'draft' }">{{ b.status === 'published' ? '已发布' : '草稿' }}</span>
        </div>
        <div style="font-weight: 700; margin-top: 6px;">{{ b.title }}</div>
        <div class="m-hint m-nowrap" style="margin-top: 4px;" v-if="b.summary">{{ b.summary }}</div>
        <div class="m-flex m-gap m-wrap" style="margin-top: 8px;" v-if="b.tags?.length">
          <span v-for="t in b.tags" :key="t" class="m-tag">#{{ t }}</span>
        </div>
      </div>
      <div v-if="!blogs.length" class="m-empty"><div class="m-empty__ico">▤</div><div class="m-empty__txt">还没有日志</div></div>
    </template>

    <button class="m-fab" @click="router.push('/blog/new')">✎</button>
  </div>
</template>
