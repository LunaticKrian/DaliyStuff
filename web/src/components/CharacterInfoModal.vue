<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { updateProfile, uploadPortrait } from '../api/auth'
import { useAuthStore } from '../stores/auth'
import { useNotifyStore } from '../stores/notification'
import PixelDatePicker from './PixelDatePicker.vue'

const props = defineProps<{ visible: boolean }>()
const emit = defineEmits<{ close: [] }>()

const auth = useAuthStore()
const notify = useNotifyStore()

const loading = ref(false)
const error = ref('')

const characterName = ref('')
const selectedClass = ref('')
const customClass = ref('')
const isCustomClass = ref(false)
const birthday = ref('')
const portraitFile = ref<File | null>(null)
const portraitPreview = ref('')

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
    if (m < z.end[0] || (m === z.end[0] && day <= z.end[1])) return z
  }
  return { name: '摩羯座', icon: '♑' }
})

// Load existing data when modal opens
watch(() => props.visible, (v) => {
  if (!v) return
  error.value = ''
  portraitFile.value = null
  const u = auth.user
  characterName.value = u?.character_name || ''
  birthday.value = u?.birthday ? u.birthday.slice(0, 10) : ''
  portraitPreview.value = ''
  const cls = u?.character_class || ''
  const preset = CLASS_PRESETS.find(p => `${p.rpg}|${p.real}` === cls)
  if (preset) {
    selectedClass.value = cls
    isCustomClass.value = false
  } else if (cls) {
    selectedClass.value = cls
    customClass.value = cls
    isCustomClass.value = true
  } else {
    selectedClass.value = ''
    isCustomClass.value = false
  }
})

function selectClass(preset: typeof CLASS_PRESETS[0]) {
  selectedClass.value = `${preset.rpg}|${preset.real}`
  isCustomClass.value = false
}

function enableCustom() {
  isCustomClass.value = true
  selectedClass.value = customClass.value
}

function onCustomInput() {
  selectedClass.value = customClass.value
}

// Portrait
const fileInput = ref<HTMLInputElement | null>(null)
function triggerUpload() { fileInput.value?.click() }
function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  if (!target.files?.length) return
  const file = target.files[0]
  if (!file.type.startsWith('image/')) return
  portraitFile.value = file
  portraitPreview.value = URL.createObjectURL(file)
}

async function handleSave() {
  error.value = ''
  if (!characterName.value.trim()) { error.value = '请输入角色名称'; return }
  if (!selectedClass.value) { error.value = '请选择职业'; return }

  loading.value = true
  try {
    if (portraitFile.value) {
      await uploadPortrait(portraitFile.value)
    }
    await updateProfile({
      character_name: characterName.value.trim(),
      character_class: selectedClass.value,
      birthday: birthday.value || undefined,
    })
    await auth.initialize()
    notify.success('角色信息已更新')
    emit('close')
  } catch (e: any) {
    error.value = e?.data?.detail || '保存失败'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <Teleport to="body">
    <div v-if="visible" class="modal-overlay" @click.self="emit('close')">
      <div class="modal-card">
        <div class="modal-title">
          <span class="title-bracket">[</span>角色信息<span class="title-bracket">]</span>
        </div>

        <div v-if="error" class="error-banner">
          <span class="error-icon">!</span> {{ error }}
        </div>

        <!-- Portrait -->
        <div class="modal-section">
          <div class="field-label">立绘</div>
          <div class="portrait-row">
            <div class="portrait-box" @click="triggerUpload">
              <img
                v-if="portraitPreview || auth.user?.portrait_url"
                :src="portraitPreview || auth.user?.portrait_url || undefined"
                alt="Portrait"
                class="portrait-img"
              />
              <div v-else class="portrait-empty">◈</div>
            </div>
            <span class="portrait-hint">点击更换</span>
            <input ref="fileInput" type="file" accept="image/*" class="hidden-input" @change="handleFileSelect" />
          </div>
        </div>

        <!-- Name -->
        <div class="modal-section">
          <div class="field-label">角色名</div>
          <input v-model="characterName" type="text" class="pixel-input" placeholder="角色名..." maxlength="50" />
        </div>

        <!-- Class -->
        <div class="modal-section">
          <div class="field-label">职业</div>
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
            </button>
            <button class="class-card custom" :class="{ selected: isCustomClass }" @click="enableCustom">
              <span class="class-icon">✎</span>
              <span class="class-rpg">自定义</span>
            </button>
          </div>
          <div v-if="isCustomClass" class="custom-wrap">
            <input v-model="customClass" type="text" class="pixel-input" placeholder="自定义职业..." @input="onCustomInput" />
          </div>
        </div>

        <!-- Birthday -->
        <div class="modal-section">
          <div class="field-label">生日 / 星座</div>
          <div class="birthday-row">
            <PixelDatePicker v-model="birthday" placeholder="选择生日" />
            <div class="zodiac-badge" :class="{ hidden: !zodiac }">
              <span class="zodiac-icon">{{ zodiac?.icon ?? '' }}</span>
              <span class="zodiac-name">{{ zodiac?.name ?? '' }}</span>
            </div>
          </div>
        </div>

        <div class="modal-actions">
          <button class="pixel-btn primary" :disabled="loading" @click="handleSave">
            <span v-if="loading" class="pixel-loading inline"></span>
            <span v-else>保存</span>
          </button>
          <button class="pixel-btn" @click="emit('close')">取消</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&display=swap');

/* Teleport 到 body → 自带令牌（实心底，浮层不透明） */
.modal-overlay {
  --pixel-bg:#0b0d14; --pixel-bg-secondary:#14171f; --pixel-card-bg:#161924;
  --pixel-border:rgba(255,255,255,.10); --pixel-primary:#22d3ee; --pixel-accent:#fb7185;
  --pixel-warning:#fbbf24; --pixel-success:#34d399; --pixel-info:#38bdf8;
  --pixel-text:#f4f6fb; --pixel-text-secondary:#9aa3b2; --pixel-shadow:rgba(0,0,0,.5);
  --d-grad:linear-gradient(135deg,#818cf8 0%,#7c5cff 40%,#22d3ee 100%);
  --d-radius:14px; --d-radius-sm:10px; --d-radius-lg:20px;
  --d-shadow:0 18px 44px -22px rgba(0,0,0,.7);
  --d-f-display:'Space Grotesk','PingFang SC',system-ui,sans-serif;
  --d-f-body:'Inter','PingFang SC','Microsoft YaHei',system-ui,sans-serif;
  --d-f-mono:'JetBrains Mono',ui-monospace,monospace;
  position: fixed; inset: 0; background: rgba(5,6,12,.62); backdrop-filter: blur(6px);
  display: flex; align-items: center; justify-content: center; z-index: 200; padding: 16px;
  animation: pixel-fade-in .18s ease-out;
}
[data-theme="light"] .modal-overlay {
  --pixel-bg:#f4f5fa; --pixel-bg-secondary:#eef0f7; --pixel-card-bg:#ffffff;
  --pixel-border:rgba(17,20,40,.12); --pixel-primary:#0891b2; --pixel-accent:#e11d48;
  --pixel-warning:#d97706; --pixel-success:#059669; --pixel-info:#0284c7;
  --pixel-text:#0f1326; --pixel-text-secondary:#4b5568; --pixel-shadow:rgba(17,20,40,.15);
  --d-grad:linear-gradient(135deg,#6366f1 0%,#7c3aed 40%,#0891b2 100%);
  --d-shadow:0 18px 44px -22px rgba(17,20,40,.24);
}
.modal-card {
  background: var(--pixel-card-bg); border: 1px solid var(--pixel-border);
  border-radius: var(--d-radius-lg); box-shadow: var(--d-shadow);
  padding: 22px; width: 100%; min-width: 0; max-width: 520px; max-height: 90vh; overflow-y: auto;
  display: flex; flex-direction: column; gap: 18px; animation: pixel-scale-in .22s cubic-bezier(.2,.7,.2,1);
}
.modal-title { font-family: var(--d-f-display); font-size: 17px; font-weight: 700; color: var(--pixel-text); letter-spacing: -.01em; }
.title-bracket { color: var(--pixel-primary); }

.error-banner { background: rgba(251,113,133,.1); border: 1px solid rgba(251,113,133,.35); color: var(--pixel-accent); font-size: 12.5px; padding: 8px 11px; border-radius: var(--d-radius-sm); display: flex; align-items: center; gap: 8px; }
.error-icon { font-family: var(--d-f-mono); font-size: 11px; font-weight: 700; width: 16px; height: 16px; display: flex; align-items: center; justify-content: center; background: var(--pixel-accent); color: #fff; border-radius: 50%; flex-shrink: 0; }

.modal-section { display: flex; flex-direction: column; gap: 8px; }
.field-label { font-family: var(--d-f-mono); font-size: 11px; color: var(--pixel-text-secondary); letter-spacing: .04em; }

.portrait-row { display: flex; align-items: center; gap: 12px; }
.portrait-box { width: 64px; height: 84px; border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); background: var(--pixel-bg-secondary); cursor: pointer; overflow: hidden; display: flex; align-items: center; justify-content: center; transition: border-color .2s ease; }
.portrait-box:hover { border-color: var(--pixel-primary); }
.portrait-img { width: 100%; height: 100%; object-fit: cover; image-rendering: pixelated; }
.portrait-empty { font-size: 24px; color: var(--pixel-text-secondary); opacity: .4; }
.portrait-hint { font-size: 12px; color: var(--pixel-text-secondary); }
.hidden-input { display: none; }

.pixel-input { background: var(--pixel-bg-secondary); border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); color: var(--pixel-text); font-family: var(--d-f-body); font-size: 13.5px; padding: 10px 12px; outline: none; width: 100%; box-sizing: border-box; transition: border-color .2s ease, box-shadow .2s ease; }
.pixel-input:focus { border-color: var(--pixel-primary); box-shadow: 0 0 0 3px rgba(34,211,238,.16); }
.pixel-input::placeholder { color: var(--pixel-text-secondary); opacity: .55; }

.class-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
.class-card { display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 9px 2px; background: var(--pixel-bg-secondary); border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); cursor: pointer; transition: border-color .15s ease, background .15s ease, transform .12s ease; font-family: var(--d-f-body); }
.class-card:hover { border-color: var(--pixel-primary); transform: translateY(-1px); }
.class-card.selected { border-color: var(--pixel-primary); background: rgba(34,211,238,.1); }
.class-icon { font-size: 16px; }
.class-rpg { font-size: 11px; color: var(--pixel-text); }
.class-card.selected .class-rpg { color: var(--pixel-primary); font-weight: 600; }
.custom-wrap { margin-top: 8px; }

.birthday-row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.birthday-row .pixel-input { flex: 1; min-width: 140px; }
.zodiac-badge { display: flex; align-items: center; gap: 5px; border: 1px solid rgba(251,191,36,.45); background: rgba(251,191,36,.1); border-radius: 999px; padding: 5px 12px; flex-shrink: 0; visibility: visible; opacity: 1; transition: opacity .15s ease, visibility .15s ease; }
.zodiac-badge.hidden { visibility: hidden; opacity: 0; }
.zodiac-icon { font-size: 15px; }
.zodiac-name { font-family: var(--d-f-body); font-size: 12px; color: var(--pixel-warning); white-space: nowrap; }

.modal-actions { display: flex; gap: 10px; justify-content: flex-end; padding-top: 14px; border-top: 1px solid var(--pixel-border); }
.pixel-btn { font-family: var(--d-f-body); font-weight: 600; font-size: 13px; padding: 9px 18px; border-radius: var(--d-radius-sm); border: 1px solid var(--pixel-border); background: var(--pixel-bg-secondary); color: var(--pixel-text); cursor: pointer; display: flex; align-items: center; gap: 6px; transition: background .2s ease, border-color .2s ease; }
.pixel-btn:hover { border-color: var(--pixel-text-secondary); }
.pixel-btn:disabled { opacity: .5; cursor: not-allowed; }
.pixel-btn.primary { background: var(--d-grad); border-color: transparent; color: #0a0b10; font-weight: 700; box-shadow: 0 8px 22px -12px rgba(99,102,241,.8); }
[data-theme="light"] .pixel-btn.primary { color: #fff; }
.inline { display: inline-block; width: 14px; height: 14px; border-width: 2px; }

@keyframes pixel-fade-in { from { opacity: 0; } to { opacity: 1; } }
@keyframes pixel-scale-in { from { opacity: 0; transform: scale(.96) translateY(6px); } to { opacity: 1; transform: scale(1) translateY(0); } }
</style>

