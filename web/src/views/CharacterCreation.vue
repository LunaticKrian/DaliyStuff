<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { updateProfile, uploadPortrait } from '../api/auth'
import { useAuthStore } from '../stores/auth'
import { useNotifyStore } from '../stores/notification'
import PixelDatePicker from '../components/PixelDatePicker.vue'

const router = useRouter()
const auth = useAuthStore()
const notify = useNotifyStore()

const loading = ref(false)
const error = ref('')

// Form state
const portraitFile = ref<File | null>(null)
const portraitPreview = ref('')
const characterName = ref('')
const selectedClass = ref('')
const customClass = ref('')
const isCustomClass = ref(false)
const birthday = ref('')

// Class presets
const CLASS_PRESETS = [
  { rpg: '农夫', real: '程序员', icon: '♧' },
  { rpg: '魔法师', real: 'UI设计师', icon: '✦' },
  { rpg: '学者', real: '大学生', icon: '◈' },
  { rpg: '战士', real: '后端工程师', icon: '⚔' },
  { rpg: '盗贼', real: '产品经理', icon: '◎' },
  { rpg: '牧师', real: '运维工程师', icon: '✚' },
  { rpg: '猎人', real: '测试工程师', icon: '▣' },
  { rpg: '商人', real: '项目经理', icon: '◆' },
  { rpg: '吟游诗人', real: '自媒体运营', icon: '♪' },
  { rpg: '炼金术士', real: '数据分析师', icon: '⚗' },
  { rpg: '铁匠', real: '硬件工程师', icon: '⚒' },
  { rpg: '流浪者', real: '自由职业', icon: '☆' },
]

function selectClass(preset: typeof CLASS_PRESETS[0]) {
  selectedClass.value = `${preset.rpg}|${preset.real}`
  isCustomClass.value = false
}

function enableCustom() {
  isCustomClass.value = true
  selectedClass.value = ''
}

function onCustomInput() {
  selectedClass.value = customClass.value
}

// Zodiac
const ZODIAC_LIST = [
  { name: '摩羯座', icon: '♑', end: [1, 19] },
  { name: '水瓶座', icon: '♒', end: [2, 18] },
  { name: '双鱼座', icon: '♓', end: [3, 20] },
  { name: '白羊座', icon: '♈', end: [4, 19] },
  { name: '金牛座', icon: '♉', end: [5, 20] },
  { name: '双子座', icon: '♊', end: [6, 21] },
  { name: '巨蟹座', icon: '♋', end: [7, 22] },
  { name: '狮子座', icon: '♌', end: [8, 22] },
  { name: '处女座', icon: '♍', end: [9, 22] },
  { name: '天秤座', icon: '♎', end: [10, 23] },
  { name: '天蝎座', icon: '♏', end: [11, 22] },
  { name: '射手座', icon: '♐', end: [12, 21] },
]

const zodiac = computed(() => {
  if (!birthday.value) return null
  const d = new Date(birthday.value)
  const m = d.getMonth() + 1
  const day = d.getDate()
  for (const z of ZODIAC_LIST) {
    if (m < z.end[0] || (m === z.end[0] && day <= z.end[1])) {
      return z
    }
  }
  return { name: '摩羯座', icon: '♑' }
})

// Portrait upload
const fileInput = ref<HTMLInputElement | null>(null)

function triggerUpload() {
  fileInput.value?.click()
}

function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  if (!target.files?.length) return
  const file = target.files[0]
  if (!file.type.startsWith('image/')) return
  portraitFile.value = file
  portraitPreview.value = URL.createObjectURL(file)
}

function handleDrop(event: DragEvent) {
  event.preventDefault()
  const file = event.dataTransfer?.files[0]
  if (!file || !file.type.startsWith('image/')) return
  portraitFile.value = file
  portraitPreview.value = URL.createObjectURL(file)
}

function handleDragOver(event: DragEvent) {
  event.preventDefault()
}

// Submit
async function handleSubmit() {
  error.value = ''
  if (!characterName.value.trim()) {
    error.value = '请输入角色名称'
    return
  }
  if (!selectedClass.value) {
    error.value = '请选择一个职业'
    return
  }
  if (!birthday.value) {
    error.value = '请选择生日'
    return
  }

  loading.value = true
  try {
    if (portraitFile.value) {
      await uploadPortrait(portraitFile.value)
    }
    await updateProfile({
      character_name: characterName.value.trim(),
      character_class: selectedClass.value,
      birthday: birthday.value,
    })
    await auth.initialize()
    notify.success('角色创建成功！冒险开始！')
    router.push('/')
  } catch (e: any) {
    error.value = e?.data?.detail || '保存失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="creation-page">
    <div class="creation-card">
      <!-- Title -->
      <div class="creation-header">
        <div class="header-icon">▶</div>
        <h1 class="creation-title">角色创建</h1>
        <div class="header-sub">新建存档</div>
      </div>

      <!-- Error -->
      <div v-if="error" class="error-banner">
        <span class="error-icon">!</span>
        {{ error }}
      </div>

      <!-- Step 1: Portrait -->
      <section class="creation-section">
        <h2 class="section-title">
          <span class="step-num">01</span>
          <span class="step-label">立绘</span>
        </h2>
        <div
          class="portrait-upload"
          :class="{ 'has-image': portraitPreview }"
          @click="triggerUpload"
          @drop="handleDrop"
          @dragover="handleDragOver"
        >
          <img v-if="portraitPreview" :src="portraitPreview" alt="Portrait Preview" class="portrait-preview" />
          <div v-else class="portrait-placeholder">
            <div class="placeholder-icon">◈</div>
            <div class="placeholder-text">点击上传立绘</div>
            <div class="placeholder-sub">支持拖拽</div>
          </div>
        </div>
        <input ref="fileInput" type="file" accept="image/*" class="hidden-input" @change="handleFileSelect" />
      </section>

      <!-- Step 2: Name -->
      <section class="creation-section">
        <h2 class="section-title">
          <span class="step-num">02</span>
          <span class="step-label">角色名</span>
        </h2>
        <input
          v-model="characterName"
          type="text"
          class="pixel-input"
          placeholder="为你的角色取一个名字..."
          maxlength="50"
        />
      </section>

      <!-- Step 3: Class -->
      <section class="creation-section">
        <h2 class="section-title">
          <span class="step-num">03</span>
          <span class="step-label">职业</span>
        </h2>
        <div class="class-grid">
          <button
            v-for="cls in CLASS_PRESETS"
            :key="cls.rpg"
            class="class-card"
            :class="{ selected: selectedClass === `${cls.rpg}|${cls.real}` }"
            @click="selectClass(cls)"
          >
            <span class="class-icon">{{ cls.icon }}</span>
            <span class="class-rpg">{{ cls.rpg }}</span>
            <span class="class-real">{{ cls.real }}</span>
          </button>
          <button class="class-card custom" :class="{ selected: isCustomClass }" @click="enableCustom">
            <span class="class-icon">✎</span>
            <span class="class-rpg">自定义</span>
            <span class="class-real">自定义职业</span>
          </button>
        </div>
        <div v-if="isCustomClass" class="custom-input-wrap">
          <input
            v-model="customClass"
            type="text"
            class="pixel-input"
            placeholder="输入自定义职业名称..."
            maxlength="100"
            @input="onCustomInput"
          />
        </div>
      </section>

      <!-- Step 4: Birthday & Zodiac -->
      <section class="creation-section">
        <h2 class="section-title">
          <span class="step-num">04</span>
          <span class="step-label">生日 / 星座</span>
        </h2>
        <div class="birthday-row">
          <PixelDatePicker v-model="birthday" placeholder="选择生日" />
          <div class="zodiac-badge" :class="{ hidden: !zodiac }">
            <span class="zodiac-icon">{{ zodiac?.icon ?? '' }}</span>
            <span class="zodiac-name">{{ zodiac?.name ?? '' }}</span>
          </div>
        </div>
      </section>

      <!-- Submit -->
      <div class="creation-actions">
        <button class="submit-btn" :disabled="loading" @click="handleSubmit">
          <span v-if="loading" class="pixel-loading inline"></span>
          <span v-else>▶ 开始冒险</span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&display=swap');

/* ═══════ 本页令牌：深色默认 + 浅色自适应 ═══════ */
.creation-page {
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
  justify-content: center;
  align-items: flex-start;
  min-height: 100%;
  padding: 32px 16px;
  font-family: var(--d-f-body);
  color: var(--pixel-text);
  animation: pixel-fade-in 0.3s ease-out;
}
[data-theme="light"] .creation-page {
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

.creation-card {
  background: var(--pixel-card-bg);
  backdrop-filter: blur(14px);
  border: 1px solid var(--pixel-border);
  border-radius: var(--d-radius);
  box-shadow: var(--d-shadow);
  padding: 32px 28px;
  max-width: 560px;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* Header */
.creation-header { text-align: center; padding-bottom: 16px; border-bottom: 1px solid var(--pixel-border); }
.header-icon { font-size: 28px; color: var(--pixel-primary); margin-bottom: 8px; }
.creation-title { font-family: var(--d-f-display); font-size: 22px; font-weight: 700; color: var(--pixel-text); margin: 0; letter-spacing: -.01em; }
.header-sub { font-family: var(--d-f-mono); font-size: 11px; color: var(--pixel-text-secondary); letter-spacing: .15em; margin-top: 8px; text-transform: uppercase; }

/* Error */
.error-banner { display: flex; align-items: center; gap: 8px; background: rgba(251, 113, 133, .1); border: 1px solid var(--pixel-accent); border-radius: var(--d-radius-sm); color: var(--pixel-accent); font-family: var(--d-f-body); font-size: 13px; padding: 9px 12px; }
.error-icon { font-family: var(--d-f-mono); font-size: 11px; width: 18px; height: 18px; display: flex; align-items: center; justify-content: center; background: var(--pixel-accent); color: #fff; border-radius: 5px; flex-shrink: 0; }

/* Sections */
.creation-section { display: flex; flex-direction: column; gap: 12px; }
.section-title { display: flex; align-items: center; gap: 10px; margin: 0; }
.step-num { font-family: var(--d-f-mono); font-size: 11px; font-weight: 600; color: var(--pixel-primary); background: rgba(34, 211, 238, .1); border: 1px solid rgba(34, 211, 238, .4); border-radius: 999px; padding: 2px 10px; }
.step-label { font-family: var(--d-f-display); font-size: 13px; font-weight: 600; color: var(--pixel-text); letter-spacing: .02em; }

/* Portrait Upload */
.portrait-upload { width: 160px; height: 208px; border: 1px dashed var(--pixel-border); border-radius: var(--d-radius); background: var(--pixel-bg-secondary); cursor: pointer; display: flex; align-items: center; justify-content: center; transition: border-color .2s ease, background .2s ease; margin: 0 auto; }
.portrait-upload:hover { border-color: var(--pixel-primary); background: rgba(34, 211, 238, .05); }
.portrait-upload.has-image { border-style: solid; border-color: var(--pixel-primary); padding: 0; overflow: hidden; box-shadow: 0 0 0 3px rgba(34, 211, 238, .14); }
.portrait-preview { width: 100%; height: 100%; object-fit: cover; image-rendering: pixelated; }
.portrait-placeholder { display: flex; flex-direction: column; align-items: center; gap: 8px; }
.placeholder-icon { font-size: 32px; color: var(--pixel-text-secondary); opacity: .6; }
.placeholder-text { font-family: var(--d-f-body); font-size: 13px; color: var(--pixel-text-secondary); }
.placeholder-sub { font-size: 11px; color: var(--pixel-text-secondary); opacity: .6; }
.hidden-input { display: none; }

/* Pixel Input */
.pixel-input { background: var(--pixel-bg-secondary); border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); color: var(--pixel-text); font-family: var(--d-f-body); font-size: 14px; padding: 10px 12px; outline: none; width: 100%; box-sizing: border-box; transition: border-color .2s ease, box-shadow .2s ease; }
.pixel-input:focus { border-color: var(--pixel-primary); box-shadow: 0 0 0 3px rgba(34, 211, 238, .16); }
.pixel-input::placeholder { color: var(--pixel-text-secondary); opacity: .55; }

/* Class Grid */
.class-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
.class-card { display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 10px 4px; background: var(--pixel-bg-secondary); border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); cursor: pointer; transition: border-color .15s ease, background .15s ease, box-shadow .15s ease; font-family: var(--d-f-body); }
.class-card:hover { border-color: var(--pixel-primary); background: rgba(34, 211, 238, .06); }
.class-card.selected { border-color: var(--pixel-primary); background: rgba(34, 211, 238, .12); box-shadow: 0 0 0 3px rgba(34, 211, 238, .16); }
.class-icon { font-size: 18px; line-height: 1; }
.class-rpg { font-family: var(--d-f-display); font-size: 12px; font-weight: 700; color: var(--pixel-text); }
.class-card.selected .class-rpg { color: var(--pixel-primary); }
.class-real { font-size: 10px; color: var(--pixel-text-secondary); text-align: center; line-height: 1.2; }
.custom-input-wrap { margin-top: 8px; }

/* Birthday & Zodiac */
.birthday-row { display: flex; align-items: center; gap: 12px; }
.birthday-row .pixel-input { flex: 1; }
.zodiac-badge { display: flex; align-items: center; gap: 6px; border: 1px solid rgba(251, 191, 36, .4); background: rgba(251, 191, 36, .1); border-radius: var(--d-radius-sm); padding: 7px 12px; flex-shrink: 0; visibility: visible; opacity: 1; transition: opacity .15s ease, visibility .15s ease; }
.zodiac-badge.hidden { visibility: hidden; opacity: 0; }
.zodiac-icon { font-size: 16px; }
.zodiac-name { font-family: var(--d-f-body); font-size: 13px; color: var(--pixel-warning); white-space: nowrap; }

/* Submit */
.creation-actions { padding-top: 8px; border-top: 1px solid var(--pixel-border); }
.submit-btn { width: 100%; background: var(--d-grad); border: 0; color: #0a0b10; font-family: var(--d-f-body); font-weight: 700; font-size: 14px; padding: 14px; cursor: pointer; border-radius: var(--d-radius-sm); box-shadow: 0 10px 26px -10px rgba(99, 102, 241, .85); display: flex; align-items: center; justify-content: center; gap: 8px; transition: box-shadow .2s ease, transform .12s ease; }
.submit-btn:hover { box-shadow: 0 14px 32px -10px rgba(99, 102, 241, 1); }
.submit-btn:active { transform: translateY(1px); }
.submit-btn:disabled { opacity: .6; cursor: not-allowed; }
[data-theme="light"] .submit-btn { color: #fff; }
.inline { display: inline-block; width: 16px; height: 16px; border-width: 2px; }

/* Responsive */
@media (max-width: 520px) {
  .creation-card { padding: 20px 16px; }
  .class-grid { grid-template-columns: repeat(3, 1fr); }
  .birthday-row { flex-direction: column; align-items: stretch; }
  .zodiac-badge { justify-content: center; }
}

@keyframes pixel-fade-in {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
