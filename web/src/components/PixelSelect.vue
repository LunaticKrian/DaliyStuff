<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'

export interface PixelOption {
  value: any
  label: string
}

const props = withDefaults(defineProps<{
  modelValue: any
  options: PixelOption[]
  placeholder?: string
  width?: string
  hidePlaceholder?: boolean
}>(), {
  placeholder: '请选择',
  width: 'auto',
  hidePlaceholder: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: any]
}>()

const open = ref(false)
const triggerRef = ref<HTMLElement | null>(null)
const dropdownRef = ref<HTMLElement | null>(null)

const selectedLabel = computed(() => {
  const opt = props.options.find(o => o.value === props.modelValue)
  return opt ? opt.label : props.placeholder
})

function toggle() {
  open.value = !open.value
}

function select(val: any) {
  emit('update:modelValue', val)
  open.value = false
}

function onClickOutside(e: MouseEvent) {
  if (!open.value) return
  const target = e.target as HTMLElement
  if (
    triggerRef.value?.contains(target) ||
    dropdownRef.value?.contains(target)
  ) return
  open.value = false
}

onMounted(() => {
  document.addEventListener('click', onClickOutside, true)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', onClickOutside, true)
})
</script>

<template>
  <div class="px-select" :style="{ width }">
    <div
      ref="triggerRef"
      class="px-select-trigger"
      :class="{ active: open }"
      @click="toggle"
    >
      <span class="px-select-text" :class="{ placeholder: modelValue === '' || modelValue === null || modelValue === undefined }">
        {{ selectedLabel }}
      </span>
      <span class="px-select-arrow" :class="{ open }">▼</span>
    </div>
    <div v-if="open" ref="dropdownRef" class="px-select-dropdown">
      <div
        v-if="!hidePlaceholder"
        class="px-select-option"
        :class="{ selected: modelValue === '' || modelValue === null || modelValue === undefined }"
        @click="select(options[0]?.value === undefined ? '' : null)"
      >
        {{ placeholder }}
      </div>
      <div
        v-for="opt in options"
        :key="String(opt.value)"
        class="px-select-option"
        :class="{ selected: opt.value === modelValue }"
        @click="select(opt.value)"
      >
        {{ opt.label }}
      </div>
    </div>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&display=swap');

/* 自带令牌兜底（通常继承页面；浮层用实心底） */
.px-select {
  --pixel-bg:#0b0d14; --pixel-bg-secondary:#14171f; --pixel-card-bg:#161924;
  --pixel-border:rgba(255,255,255,.10); --pixel-primary:#22d3ee; --pixel-accent:#fb7185;
  --pixel-text:#f4f6fb; --pixel-text-secondary:#9aa3b2;
  --d-radius-sm:10px; --d-shadow:0 18px 44px -22px rgba(0,0,0,.7);
  --d-f-body:'Inter','PingFang SC',system-ui,sans-serif;
  position: relative; font-family: var(--d-f-body); font-size: 13px;
}
[data-theme="light"] .px-select {
  --pixel-bg:#f4f5fa; --pixel-bg-secondary:#eef0f7; --pixel-card-bg:#ffffff;
  --pixel-border:rgba(17,20,40,.12); --pixel-primary:#0891b2; --pixel-accent:#e11d48;
  --pixel-text:#0f1326; --pixel-text-secondary:#4b5568; --d-shadow:0 18px 44px -22px rgba(17,20,40,.24);
}

.px-select-trigger { display: flex; align-items: center; justify-content: space-between; gap: 8px; background: var(--pixel-bg-secondary); border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); color: var(--pixel-text); padding: 9px 12px; cursor: pointer; user-select: none; transition: border-color .2s ease, box-shadow .2s ease; }
.px-select-trigger:hover { border-color: var(--pixel-primary); }
.px-select-trigger.active { border-color: var(--pixel-primary); box-shadow: 0 0 0 3px rgba(34,211,238,.16); }
.px-select-text { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.px-select-text.placeholder { color: var(--pixel-text-secondary); opacity: .6; }
.px-select-arrow { font-size: 9px; color: var(--pixel-text-secondary); transition: transform .2s ease; flex-shrink: 0; }
.px-select-arrow.open { transform: rotate(180deg); }

.px-select-dropdown { position: absolute; top: calc(100% + 6px); left: 0; right: 0; z-index: 300; background: var(--pixel-card-bg); border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); box-shadow: var(--d-shadow); max-height: 240px; overflow-y: auto; padding: 4px; animation: px-select-in .14s ease-out; }
@keyframes px-select-in { from { opacity: 0; transform: translateY(-4px); } to { opacity: 1; transform: translateY(0); } }

.px-select-option { padding: 8px 11px; cursor: pointer; color: var(--pixel-text); border-radius: 8px; transition: background .12s ease, color .12s ease; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.px-select-option:hover { background: rgba(34,211,238,.1); color: var(--pixel-primary); }
.px-select-option.selected { background: rgba(34,211,238,.16); color: var(--pixel-primary); font-weight: 600; }
</style>

