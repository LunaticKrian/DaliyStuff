<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'

const props = withDefaults(defineProps<{
  modelValue: string
  placeholder?: string
  width?: string
  dropUp?: boolean
  markedDates?: string[]
  restrictToMarked?: boolean
}>(), {
  placeholder: '选择日期',
  width: 'auto',
  dropUp: false,
  markedDates: () => [],
  restrictToMarked: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const open = ref(false)

const markedSet = computed(() => new Set(props.markedDates))

const weekDays = ['日', '一', '二', '三', '四', '五', '六']
const monthNames = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']

const today = new Date()
const viewYear = ref(today.getFullYear())
const viewMonth = ref(today.getMonth())

const displayText = computed(() => props.modelValue || '')

const calendarDays = computed(() => {
  const y = viewYear.value
  const m = viewMonth.value
  const firstDay = new Date(y, m, 1).getDay()
  const daysInMonth = new Date(y, m + 1, 0).getDate()
  const prevDays = new Date(y, m, 0).getDate()

  const days: { date: string; day: number; inMonth: boolean; isToday: boolean; selected: boolean; marked: boolean; disabled: boolean }[] = []

  const mark = (ds: string) => ({
    marked: markedSet.value.has(ds),
    disabled: props.restrictToMarked && !markedSet.value.has(ds),
  })

  for (let i = firstDay - 1; i >= 0; i--) {
    const d = prevDays - i
    const pm = m === 0 ? 11 : m - 1
    const py = m === 0 ? y - 1 : y
    const ds = fmt(py, pm, d)
    days.push({ date: ds, day: d, inMonth: false, isToday: false, selected: false, ...mark(ds) })
  }

  for (let d = 1; d <= daysInMonth; d++) {
    const ds = fmt(y, m, d)
    days.push({ date: ds, day: d, inMonth: true, isToday: ds === fmtToday(), selected: ds === props.modelValue, ...mark(ds) })
  }

  const rem = 42 - days.length
  for (let d = 1; d <= rem; d++) {
    const nm = m === 11 ? 0 : m + 1
    const ny = m === 11 ? y + 1 : y
    const ds = fmt(ny, nm, d)
    days.push({ date: ds, day: d, inMonth: false, isToday: false, selected: false, ...mark(ds) })
  }

  return days
})

// Year range for quick select
const yearPage = ref(0)
const yearGrid = computed(() => {
  const base = viewYear.value + yearPage.value * 12
  const years: number[] = []
  for (let i = -7; i <= 4; i++) years.push(base + i)
  return years
})

function fmt(y: number, m: number, d: number): string {
  return `${y}-${String(m + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`
}

function fmtToday(): string {
  const t = new Date()
  return fmt(t.getFullYear(), t.getMonth(), t.getDate())
}

// Sub-panel: 'days' | 'months' | 'years'
const subPanel = ref<'days' | 'months' | 'years'>('days')

function toggle(e: MouseEvent) {
  e.stopPropagation()
  open.value = !open.value
  subPanel.value = 'days'
  yearPage.value = 0
  if (open.value && props.modelValue) {
    const [y, m] = props.modelValue.split('-').map(Number)
    if (y && m) { viewYear.value = y; viewMonth.value = m - 1 }
  }
}

function selectDate(date: string) {
  if (props.restrictToMarked && !markedSet.value.has(date)) return
  emit('update:modelValue', date)
  open.value = false
}

function clearDate() {
  emit('update:modelValue', '')
  open.value = false
}

function prevMonth() {
  if (viewMonth.value === 0) { viewMonth.value = 11; viewYear.value-- }
  else viewMonth.value--
}

function nextMonth() {
  if (viewMonth.value === 11) { viewMonth.value = 0; viewYear.value++ }
  else viewMonth.value++
}

function goToday() {
  const t = new Date()
  viewYear.value = t.getFullYear()
  viewMonth.value = t.getMonth()
  subPanel.value = 'days'
}

function showMonths() { subPanel.value = 'months' }
function showYears() { subPanel.value = 'years'; yearPage.value = 0 }

function pickMonth(m: number) {
  viewMonth.value = m
  subPanel.value = 'days'
}

function pickYear(y: number) {
  viewYear.value = y
  subPanel.value = 'months'
}

function yearPagePrev() { yearPage.value-- }
function yearPageNext() { yearPage.value++ }

function onPanelClick(e: MouseEvent) { e.stopPropagation() }

function onDocClick() {
  if (open.value) open.value = false
}

onMounted(() => document.addEventListener('click', onDocClick))
onBeforeUnmount(() => document.removeEventListener('click', onDocClick))

watch(() => props.modelValue, (v) => {
  if (v) {
    const [y, m] = v.split('-').map(Number)
    if (y && m) { viewYear.value = y; viewMonth.value = m - 1 }
  }
})
</script>

<template>
  <div class="px-datepicker" :class="{ 'drop-up': dropUp }" :style="{ width }">
    <div class="px-date-trigger" :class="{ active: open }" @click="toggle">
      <span class="px-date-text" :class="{ placeholder: !modelValue }">
        {{ displayText || placeholder }}
      </span>
      <span class="px-date-icon">📅</span>
    </div>
    <div
      class="px-date-panel"
      :class="{ visible: open }"
      @click="onPanelClick"
    >
      <!-- Navigation -->
      <div class="px-date-nav">
        <button class="px-nav-btn" @click="prevMonth">◀</button>
        <button class="px-nav-label" @click="showYears">{{ viewYear }}年</button>
        <button class="px-nav-label" @click="showMonths">{{ viewMonth + 1 }}月</button>
        <button class="px-nav-btn" @click="nextMonth">▶</button>
      </div>

      <!-- Day grid -->
      <template v-if="subPanel === 'days'">
        <div class="px-week-header">
          <span v-for="d in weekDays" :key="d" class="px-week-day">{{ d }}</span>
        </div>
        <div class="px-days-grid">
          <div
            v-for="(d, i) in calendarDays"
            :key="i"
            class="px-day"
            :class="{ outside: !d.inMonth, today: d.isToday, selected: d.selected, marked: d.marked, disabled: d.disabled }"
            @click="selectDate(d.date)"
          >{{ d.day }}</div>
        </div>
      </template>

      <!-- Month grid -->
      <div v-if="subPanel === 'months'" class="px-sub-grid months-grid">
        <button
          v-for="(name, idx) in monthNames"
          :key="idx"
          class="px-sub-cell"
          :class="{ active: idx === viewMonth }"
          @click="pickMonth(idx)"
        >{{ name }}</button>
      </div>

      <!-- Year grid -->
      <div v-if="subPanel === 'years'">
        <div class="px-year-nav">
          <button class="px-nav-btn sm" @click="yearPagePrev">◀</button>
          <span class="px-year-range">{{ yearGrid[0] }} - {{ yearGrid[yearGrid.length - 1] }}</span>
          <button class="px-nav-btn sm" @click="yearPageNext">▶</button>
        </div>
        <div class="px-sub-grid years-grid">
          <button
            v-for="y in yearGrid"
            :key="y"
            class="px-sub-cell"
            :class="{ active: y === viewYear }"
            @click="pickYear(y)"
          >{{ y }}</button>
        </div>
      </div>

      <!-- Footer -->
      <div class="px-date-footer">
        <button class="px-footer-btn" @click="goToday">今天</button>
        <button class="px-footer-btn clear" @click="clearDate">清除</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&display=swap');

.px-datepicker {
  --pixel-bg:#0b0d14; --pixel-bg-secondary:#14171f; --pixel-card-bg:#161924;
  --pixel-border:rgba(255,255,255,.10); --pixel-primary:#22d3ee; --pixel-accent:#fb7185;
  --pixel-warning:#fbbf24; --pixel-success:#34d399; --pixel-text:#f4f6fb; --pixel-text-secondary:#9aa3b2;
  --d-grad:linear-gradient(135deg,#818cf8 0%,#7c5cff 40%,#22d3ee 100%);
  --d-radius-sm:10px; --d-shadow:0 18px 44px -22px rgba(0,0,0,.7);
  --d-f-body:'Inter','PingFang SC',system-ui,sans-serif;
  position: relative; font-family: var(--d-f-body); font-size: 13px;
}
[data-theme="light"] .px-datepicker {
  --pixel-bg:#f4f5fa; --pixel-bg-secondary:#eef0f7; --pixel-card-bg:#ffffff;
  --pixel-border:rgba(17,20,40,.12); --pixel-primary:#0891b2; --pixel-accent:#e11d48;
  --pixel-warning:#d97706; --pixel-success:#059669; --pixel-text:#0f1326; --pixel-text-secondary:#4b5568;
  --d-grad:linear-gradient(135deg,#6366f1 0%,#7c3aed 40%,#0891b2 100%);
  --d-shadow:0 18px 44px -22px rgba(17,20,40,.24);
}

.px-date-trigger { display: flex; align-items: center; justify-content: space-between; gap: 8px; background: var(--pixel-bg-secondary); border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); color: var(--pixel-text); padding: 9px 12px; cursor: pointer; user-select: none; transition: border-color .2s ease, box-shadow .2s ease; }
.px-date-trigger:hover { border-color: var(--pixel-primary); }
.px-date-trigger.active { border-color: var(--pixel-primary); box-shadow: 0 0 0 3px rgba(34,211,238,.16); }
.px-date-text { flex: 1; letter-spacing: .02em; }
.px-date-text.placeholder { color: var(--pixel-text-secondary); opacity: .6; }
.px-date-icon { font-size: 13px; flex-shrink: 0; }

.px-date-panel { position: absolute; top: calc(100% + 6px); left: 0; z-index: 300; background: var(--pixel-card-bg); border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); box-shadow: var(--d-shadow); width: 268px; padding: 10px; visibility: hidden; opacity: 0; pointer-events: none; transition: opacity .14s ease, visibility .14s ease; }
.px-date-panel.visible { visibility: visible; opacity: 1; pointer-events: auto; }
.px-datepicker.drop-up .px-date-panel { top: auto; bottom: calc(100% + 6px); }

.px-date-nav { display: flex; align-items: center; gap: 4px; padding: 2px 0 8px; }
.px-nav-btn { background: var(--pixel-bg-secondary); border: 1px solid var(--pixel-border); border-radius: 7px; color: var(--pixel-text-secondary); font-size: 10px; padding: 3px 8px; cursor: pointer; font-family: var(--d-f-body); transition: border-color .15s, color .15s; }
.px-nav-btn:hover { border-color: var(--pixel-primary); color: var(--pixel-primary); }
.px-nav-btn.sm { padding: 2px 7px; font-size: 9px; }
.px-nav-label { background: none; border: 1px solid transparent; border-radius: 7px; color: var(--pixel-text); font-family: var(--d-f-body); font-size: 13px; font-weight: 600; padding: 3px 7px; cursor: pointer; transition: border-color .15s, background .15s; }
.px-nav-label:hover { border-color: var(--pixel-primary); background: rgba(34,211,238,.08); }

.px-week-header { display: grid; grid-template-columns: repeat(7, 1fr); margin-bottom: 4px; }
.px-week-day { text-align: center; font-size: 10px; color: var(--pixel-text-secondary); padding: 4px 0; font-family: var(--d-f-body); }

.px-days-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 3px; }
.px-day { text-align: center; padding: 6px 0; cursor: pointer; font-size: 12.5px; color: var(--pixel-text); border: 1px solid transparent; border-radius: 7px; transition: background .12s, color .12s, border-color .12s; }
.px-day:hover { background: rgba(34,211,238,.12); border-color: rgba(34,211,238,.4); }
.px-day.outside { color: var(--pixel-text-secondary); opacity: .35; }
.px-day.outside:hover { opacity: .7; }
.px-day.today { border-color: var(--pixel-primary); font-weight: 700; }
.px-day.selected { background: var(--d-grad); color: #0a0b10; border-color: transparent; font-weight: 700; }
[data-theme="light"] .px-day.selected { color: #fff; }
.px-day.selected:hover { background: var(--d-grad); }

.px-day.marked { position: relative; font-weight: 700; }
.px-day.marked::after { content: ''; position: absolute; bottom: 2px; left: 50%; transform: translateX(-50%); width: 4px; height: 4px; border-radius: 50%; background: var(--pixel-success); }
.px-day.selected.marked::after { background: rgba(10,11,20,.7); }
.px-day.disabled { color: var(--pixel-text-secondary); opacity: .28; cursor: not-allowed; }
.px-day.disabled:hover { background: none; border-color: transparent; opacity: .28; }
.px-day.disabled.marked { opacity: 1; }

.px-sub-grid { display: grid; gap: 5px; }
.px-sub-grid.months-grid { grid-template-columns: repeat(3, 1fr); }
.px-sub-grid.years-grid { grid-template-columns: repeat(4, 1fr); }
.px-sub-cell { background: var(--pixel-bg-secondary); border: 1px solid var(--pixel-border); border-radius: 8px; color: var(--pixel-text); font-family: var(--d-f-body); font-size: 12px; padding: 7px 2px; text-align: center; cursor: pointer; transition: border-color .12s, background .12s, color .12s; }
.px-sub-cell:hover { border-color: var(--pixel-primary); background: rgba(34,211,238,.08); }
.px-sub-cell.active { border-color: transparent; background: var(--d-grad); color: #0a0b10; font-weight: 600; }
[data-theme="light"] .px-sub-cell.active { color: #fff; }

.px-year-nav { display: flex; align-items: center; justify-content: space-between; padding: 2px 0 8px; }
.px-year-range { font-size: 11px; color: var(--pixel-text-secondary); font-family: var(--d-f-body); }

.px-date-footer { display: flex; justify-content: space-between; margin-top: 8px; padding-top: 8px; border-top: 1px solid var(--pixel-border); }
.px-footer-btn { background: var(--pixel-bg-secondary); border: 1px solid var(--pixel-border); border-radius: 7px; color: var(--pixel-text-secondary); font-family: var(--d-f-body); font-size: 11px; padding: 4px 12px; cursor: pointer; transition: border-color .15s, color .15s; }
.px-footer-btn:hover { border-color: var(--pixel-primary); color: var(--pixel-primary); }
.px-footer-btn.clear:hover { border-color: var(--pixel-accent); color: var(--pixel-accent); }
</style>

