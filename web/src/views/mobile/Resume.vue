<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { listResumes, getResume, createResume } from '../../api/resume'
import { useNotifyStore } from '../../stores/notification'
import type { Resume as ResumeT } from '../../types/resume'

const router = useRouter()
const notify = useNotifyStore()
const list = ref<Awaited<ReturnType<typeof listResumes>>>([])
const resume = ref<ResumeT | null>(null)
const loading = ref(true)

const d = computed(() => resume.value?.data)

async function load() {
  loading.value = true
  try {
    list.value = await listResumes()
    if (list.value.length) {
      resume.value = await getResume(list.value[0].id)
    }
  } finally { loading.value = false }
}
onMounted(load)

async function newResume() {
  try {
    const r = await createResume('我的履历', 'zh', 'pixel')
    notify.success('已创建')
    resume.value = r
    list.value.unshift({ id: r.id, title: r.title, lang: r.lang, template: r.template, revision: r.revision, updatedAt: r.updatedAt })
  } catch { notify.error('创建失败') }
}

function exportPdf() {
  // 移动端：调用系统打印对话框（可存为 PDF）。完整 html2pdf 模板渲染见 P1 后续。
  window.print()
}
</script>

<template>
  <div class="m-screen">
    <div class="m-head">
      <span class="m-head__back" @click="router.push('/me')">◂</span>
      <span class="m-head__title">冒险者履历</span>
      <span class="m-head__sub" v-if="resume">v{{ resume.revision }}</span>
    </div>

    <div v-if="loading" class="m-loading">▮ 加载中</div>
    <template v-else-if="!resume">
      <div class="m-empty">
        <div class="m-empty__ico">❒</div>
        <div class="m-empty__txt">还没有履历档案</div>
        <button class="m-btn m-btn--primary m-btn--sm m-mt" @click="newResume">▸ 创建履历</button>
      </div>
    </template>
    <template v-else-if="d">
      <!-- A4 衬线预览 -->
      <div class="a4">
        <div class="a4__name">{{ d.profile.name || '（未命名）' }}</div>
        <div class="a4__sub">{{ d.profile.title }}<span v-if="d.profile.years"> · {{ d.profile.years }} 年经验</span></div>
        <div class="a4__contact">{{ [d.profile.email, d.profile.phone, d.profile.site].filter(Boolean).join(' · ') }}</div>

        <div class="a4__h" v-if="d.timeline.length">经历</div>
        <div v-for="(t, i) in d.timeline" :key="'t' + i" class="a4__row">
          <span class="a4__date">{{ t.date }}</span>
          <span><b>{{ t.role }}</b> · {{ t.org }}<span v-if="t.desc"> — {{ t.desc }}</span></span>
        </div>

        <div class="a4__h" v-if="d.skill.length">技能</div>
        <div v-for="(s, i) in d.skill" :key="'s' + i" class="a4__row">
          <b>{{ s.cat }}：</b><span>{{ s.tags.join(' · ') }}</span>
        </div>

        <div class="a4__h" v-if="d.project.length">项目</div>
        <div v-for="(p, i) in d.project" :key="'p' + i" class="a4__row">
          <b>{{ p.name }}</b><span v-if="p.stack"> ({{ p.stack }})</span><span v-if="p.desc"> — {{ p.desc }}</span>
        </div>
      </div>

      <div class="m-card m-mt">
        <div class="m-card__title">AI 编辑 <span class="m-tag m-tag--info">NEXA</span></div>
        <div class="m-hint">对话式润色、多版本与 Undo 将在 P1 后续接入。当前可手动导出。</div>
        <button class="m-btn m-btn--block m-mt" disabled>✦ 与 NEXA 对话润色（即将上线）</button>
      </div>

      <button class="m-btn m-btn--primary m-btn--block m-mt" @click="exportPdf">▽ 导出 PDF</button>
    </template>
  </div>
</template>

<style scoped>
/* 令牌兜底：脱离 .m-deck 时也保留新视觉语言 */
.m-screen {
  --pixel-bg: #0b0d14;
  --pixel-bg-secondary: #14171f;
  --pixel-card-bg: rgba(255, 255, 255, 0.045);
  --pixel-border: rgba(255, 255, 255, 0.09);
  --pixel-primary: #22d3ee;
  --pixel-info: #38bdf8;
  --pixel-text: #f4f6fb;
  --pixel-text-secondary: #9aa3b2;
  --d-grad: linear-gradient(135deg, #818cf8 0%, #7c5cff 40%, #22d3ee 100%);
  --d-radius: 14px;
  --d-radius-sm: 10px;
  --d-shadow-sm: 0 4px 14px -8px rgba(0, 0, 0, .6);
}

/* A4 履历预览：保留纸质质感，外壳套用新语言的柔焦卡片 */
.a4 {
  background: #f4f1e8;
  color: #1a1a2e;
  padding: 20px 18px;
  border: 1px solid var(--pixel-border);
  border-radius: 14px;
  box-shadow: var(--d-shadow-sm);
  font-family: Georgia, 'Times New Roman', serif;
}
.a4__name { font-size: 19px; font-weight: 700; border-bottom: 1px solid #1a1a2e; padding-bottom: 6px; }
.a4__sub { font-size: 12px; color: #444; margin-top: 4px; }
.a4__contact { font-size: 10px; color: #666; margin-top: 3px; }
.a4__h { font-size: 12px; font-weight: 700; margin: 14px 0 6px; border-bottom: 1px solid rgba(26, 26, 46, .2); }
.a4__row { font-size: 11px; line-height: 1.7; display: flex; gap: 8px; }
.a4__date { width: 86px; flex: none; color: #666; font-size: 10px; }

@media print {
  .m-head, .m-card, .m-btn, .m-fab, .m-empty { display: none !important; }
  .m-screen { padding: 0 !important; }
  .a4 { border: none; box-shadow: none; border-radius: 0; }
}
</style>
