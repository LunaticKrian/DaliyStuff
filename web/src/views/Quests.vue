<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useNotifyStore } from '../stores/notification'
import { getQuestSummary } from '../api/quests'
import {
  listTasks, createTask, updateTask, deleteTask,
  completeTask, uncompleteTask, progressTask,
} from '../api/tasks'
import type { QuestSummary, Achievement } from '../types/quest'
import type { Task, TaskCategory } from '../types/task'
import {
  CATEGORY_LIST, CATEGORY_LABELS, CATEGORY_ICONS, CATEGORY_COLORS,
} from '../types/task'

const auth = useAuthStore()
const notify = useNotifyStore()
const router = useRouter()

const loading = ref(true)
const summary = ref<QuestSummary | null>(null)
const tasks = ref<Task[]>([])

const tab = ref<'tasks' | 'achievements'>('tasks')
const showAdd = ref(false)
const addForm = ref(emptyAdd())
const editingId = ref<number | null>(null)
const editForm = ref(emptyAdd())

const hoveredAch = ref<Achievement | null>(null)
const achTooltipStyle = ref<Record<string, string>>({})

function emptyAdd() {
  return { title: '', description: '', category: 'study' as TaskCategory, target: 1, exp_reward: 10 }
}

const todayStr = computed(() =>
  new Date().toLocaleDateString('zh-CN', { month: 'long', day: 'numeric', weekday: 'long' }),
)

const todayCompleted = computed(() => tasks.value.filter(t => t.completed).length)
const todayTotal = computed(() => tasks.value.length)
const todayPercent = computed(() =>
  todayTotal.value > 0 ? Math.round((todayCompleted.value / todayTotal.value) * 100) : 0,
)

// 经验条：当前等级内进度
const expPercent = computed(() => {
  if (!summary.value) return 0
  const per = 50
  return Math.round(((per - summary.value.exp_to_next) / per) * 100)
})

const charName = computed(() => auth.user?.character_name || auth.user?.username || '冒险者')

function starsFor(exp: number) {
  if (exp >= 30) return '★★★'
  if (exp >= 20) return '★★'
  return '★'
}

function onAchHover(ach: Achievement, e: MouseEvent) {
  hoveredAch.value = ach
  const rect = (e.target as HTMLElement).getBoundingClientRect()
  achTooltipStyle.value = { position: 'fixed', left: rect.left + 'px', top: (rect.bottom + 6) + 'px', zIndex: '400' }
}
function onAchLeave() { hoveredAch.value = null }

async function loadAll() {
  loading.value = true
  try {
    const [s, t] = await Promise.all([getQuestSummary(), listTasks()])
    summary.value = s
    tasks.value = t
  } catch {
    notify.error('加载任务数据失败')
  } finally {
    loading.value = false
  }
}

async function refreshSummary() {
  try { summary.value = await getQuestSummary() } catch { /* noop */ }
}

// ── 完成 / 撤销 ──
async function onToggle(task: Task) {
  const wasCompleted = task.completed
  // 乐观更新
  task.completed = !wasCompleted
  if (task.completed) task.progress = task.target
  else if (task.target > 1) task.progress = Math.min(task.progress, task.target - 1)
  else task.progress = 0
  try {
    if (wasCompleted) {
      await uncompleteTask(task.id)
    } else {
      const r = await completeTask(task.id)
      if (r.exp_gained > 0) notify.success(`+${r.exp_gained} EXP`)
      if (r.leveled_up) notify.warning(`等级提升 → Lv.${r.level}！`)
      if (r.achievements_unlocked.length) notify.info(`解锁 ${r.achievements_unlocked.length} 个成就`)
    }
    await refreshSummary()
  } catch (e) {
    // 回滚
    task.completed = wasCompleted
    notify.error(wasCompleted ? '撤销失败' : '完成失败')
  }
}

async function onProgress(task: Task, delta: number) {
  if (task.completed) return
  const prev = task.progress
  task.progress = Math.max(0, Math.min(task.target, task.progress + delta))
  if (task.progress === task.target) {
    await onToggle(task)
    return
  }
  try {
    await progressTask(task.id, delta)
  } catch {
    task.progress = prev
    notify.error('进度更新失败')
  }
}

// ── 新增 ──
async function onAdd() {
  if (!addForm.value.title.trim()) { notify.warning('请填写任务标题'); return }
  try {
    const t = await createTask({
      title: addForm.value.title.trim(),
      description: addForm.value.description.trim() || undefined,
      category: addForm.value.category,
      target: addForm.value.target,
      exp_reward: addForm.value.exp_reward,
    })
    tasks.value.push(t)
    addForm.value = emptyAdd()
    showAdd.value = false
    await refreshSummary()
    notify.success('已添加任务')
  } catch {
    notify.error('添加失败')
  }
}

// ── 编辑 ──
function startEdit(task: Task) {
  editingId.value = task.id
  editForm.value = {
    title: task.title,
    description: task.description || '',
    category: task.category,
    target: task.target,
    exp_reward: task.exp_reward,
  }
}
function cancelEdit() { editingId.value = null }

async function saveEdit(task: Task) {
  if (!editForm.value.title.trim()) { notify.warning('标题不能为空'); return }
  try {
    const updated = await updateTask(task.id, {
      title: editForm.value.title.trim(),
      description: editForm.value.description.trim() || undefined,
      category: editForm.value.category,
      target: editForm.value.target,
      exp_reward: editForm.value.exp_reward,
    })
    Object.assign(task, updated)
    editingId.value = null
    await refreshSummary()
    notify.success('已保存')
  } catch {
    notify.error('保存失败')
  }
}

async function onDelete(task: Task) {
  if (!window.confirm(`删除任务「${task.title}」？`)) return
  try {
    await deleteTask(task.id)
    tasks.value = tasks.value.filter(t => t.id !== task.id)
    await refreshSummary()
    notify.success('已删除')
  } catch {
    notify.error('删除失败')
  }
}

onMounted(loadAll)
</script>

<template>
  <div class="quests-page animate-fade-in">
    <div class="q-layout">

      <!-- ====== LEFT: Stats Sidebar ====== -->
      <div class="q-sidebar">
        <!-- Character -->
        <div class="portrait-card pixel-border">
          <div class="pc-frame">
            <img :src="auth.user?.portrait_url || '/img/portrait.png'" alt="Character" class="pc-img" />
          </div>
          <div class="pc-info">
            <div class="pc-name">{{ charName }}</div>
            <div class="pc-level">Lv.{{ summary?.level ?? 0 }}</div>
          </div>
        </div>

        <!-- Level / EXP -->
        <div class="sp-card pixel-border">
          <div class="sp-section-header">
            <span class="sp-icon">★</span><span>等级经验</span>
            <span class="sp-badge warn">{{ summary?.exp ?? 0 }} EXP</span>
          </div>
          <div v-if="summary" class="sp-body">
            <div class="exp-bar-track">
              <div class="exp-bar-fill" :style="{ width: expPercent + '%' }"></div>
            </div>
            <div class="lm-label">距下一级 {{ summary.exp_to_next }} EXP · 当前 Lv.{{ summary.level }}</div>
          </div>
        </div>

        <!-- Streak -->
        <div class="sp-card pixel-border">
          <div class="sp-section-header">
            <span class="sp-icon flame">▮</span><span>连续打卡</span>
            <span class="sp-badge warn">{{ summary?.streak ?? 0 }} 天</span>
          </div>
          <div v-if="summary" class="sp-body streak-body">
            <div class="streak-flame">▼▼</div>
            <div class="streak-meta">
              <div class="streak-num">{{ summary.streak }}</div>
              <div class="streak-sub">DAYS · 今日 {{ todayCompleted }}/{{ todayTotal }}</div>
            </div>
          </div>
        </div>

        <!-- Today progress -->
        <div class="sp-card pixel-border">
          <div class="sp-section-header">
            <span class="sp-icon">▣</span><span>今日清单</span>
            <span class="sp-badge">{{ todayCompleted }}/{{ todayTotal }}</span>
          </div>
          <div class="sp-body">
            <div class="status-track">
              <div class="status-fill" :style="{ width: todayPercent + '%' }"></div>
            </div>
            <div class="lm-label">累计完成 {{ summary?.tasks_completed_total ?? 0 }} 个任务</div>
          </div>
        </div>

        <!-- Achievements grid -->
        <div class="sp-card pixel-border">
          <div class="sp-section-header">
            <span class="sp-icon">◈</span><span>成就</span>
            <span class="sp-badge warn">{{ summary?.achievements_completed ?? 0 }}/{{ summary?.achievements_total ?? 0 }}</span>
          </div>
          <div class="sp-body">
            <div class="ach-mini-grid">
              <div
                v-for="ach in summary?.achievements ?? []"
                :key="ach.achievement_id"
                class="ach-mini"
                :class="{ unlocked: ach.unlocked }"
                @mouseenter="onAchHover(ach, $event)"
                @mouseleave="onAchLeave"
              >{{ ach.unlocked ? ach.icon : '?' }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- ====== RIGHT: Main ====== -->
      <div class="q-main">
        <!-- Toolbar -->
        <div class="q-toolbar">
          <div class="toolbar-left">
            <button class="back-btn" @click="router.push('/')"><span>◀</span><span>角色信息</span></button>
            <h2 class="q-title"><span class="title-icon">▣</span><span>委托大厅</span><span class="q-date">{{ todayStr }}</span></h2>
          </div>
          <div class="toolbar-right">
            <button class="tab-btn" :class="{ active: tab === 'tasks' }" @click="tab = 'tasks'">▣ 今日</button>
            <button class="tab-btn" :class="{ active: tab === 'achievements' }" @click="tab = 'achievements'">★ 成就</button>
            <button class="add-btn" @click="showAdd = !showAdd">+ 新增委托</button>
          </div>
        </div>

        <!-- Add form -->
        <div v-if="showAdd" class="add-panel pixel-border">
          <input v-model="addForm.title" class="pixel-input add-title" placeholder="任务标题（如：读完高数第三章）" maxlength="120" />
          <input v-model="addForm.description" class="pixel-input" placeholder="描述（可选）" maxlength="200" />
          <div class="add-row">
            <label class="add-field">
              <span>分类</span>
              <select v-model="addForm.category" class="pixel-select">
                <option v-for="c in CATEGORY_LIST" :key="c" :value="c">{{ CATEGORY_LABELS[c] }}</option>
              </select>
            </label>
            <label class="add-field">
              <span>目标</span>
              <input v-model.number="addForm.target" type="number" min="1" max="99" class="pixel-input num" />
            </label>
            <label class="add-field">
              <span>经验</span>
              <input v-model.number="addForm.exp_reward" type="number" min="0" max="99" class="pixel-input num" />
            </label>
            <div class="add-actions">
              <button class="btn-primary" @click="onAdd">添加</button>
              <button class="btn-ghost" @click="showAdd = false">取消</button>
            </div>
          </div>
        </div>

        <!-- Loading -->
        <div v-if="loading" class="loading-state">
          <div class="pixel-loading"></div>
          <span class="loading-text">加载中...</span>
        </div>

        <template v-else>
          <!-- Tasks tab -->
          <div v-if="tab === 'tasks'" class="task-cards">
            <div
              v-for="task in tasks"
              :key="task.id"
              class="task-card pixel-border"
              :class="{ completed: task.completed, editing: editingId === task.id }"
            >
              <!-- edit mode -->
              <template v-if="editingId === task.id">
                <div class="edit-body">
                  <input v-model="editForm.title" class="pixel-input" />
                  <input v-model="editForm.description" class="pixel-input" placeholder="描述" />
                  <div class="add-row">
                    <label class="add-field"><span>分类</span>
                      <select v-model="editForm.category" class="pixel-select">
                        <option v-for="c in CATEGORY_LIST" :key="c" :value="c">{{ CATEGORY_LABELS[c] }}</option>
                      </select>
                    </label>
                    <label class="add-field"><span>目标</span>
                      <input v-model.number="editForm.target" type="number" min="1" max="99" class="pixel-input num" />
                    </label>
                    <label class="add-field"><span>经验</span>
                      <input v-model.number="editForm.exp_reward" type="number" min="0" max="99" class="pixel-input num" />
                    </label>
                  </div>
                  <div class="add-actions">
                    <button class="btn-primary" @click="saveEdit(task)">保存</button>
                    <button class="btn-ghost" @click="cancelEdit">取消</button>
                  </div>
                </div>
              </template>

              <!-- view mode -->
              <template v-else>
                <div class="task-gem" :style="{ background: CATEGORY_COLORS[task.category] }">
                  {{ CATEGORY_ICONS[task.category] }}
                </div>
                <div class="task-main">
                  <div class="task-title">{{ task.title }}</div>
                  <div v-if="task.description" class="task-desc">{{ task.description }}</div>
                  <div class="task-meta">
                    <span class="meta-stars">{{ starsFor(task.exp_reward) }}</span>
                    <span class="meta-cat">{{ CATEGORY_LABELS[task.category] }}</span>
                    <span class="meta-tag" :class="task.source">{{ task.source === 'ai' ? 'AI 生成' : '手动' }}</span>
                    <template v-if="task.target > 1">
                      <span class="meta-steps">
                        <button class="step-btn" :disabled="task.completed" @click.stop="onProgress(task, -1)">−</button>
                        <span class="step-val">{{ task.progress }}/{{ task.target }}</span>
                        <button class="step-btn" :disabled="task.completed" @click.stop="onProgress(task, 1)">+</button>
                      </span>
                    </template>
                  </div>
                </div>
                <div class="task-exp">+{{ task.exp_reward }}</div>
                <div class="task-actions">
                  <button class="icon-btn" title="编辑" @click="startEdit(task)">✎</button>
                  <button class="icon-btn danger" title="删除" @click="onDelete(task)">✕</button>
                </div>
                <button class="task-check" :class="{ done: task.completed }" @click="onToggle(task)">
                  {{ task.completed ? '✓' : '○' }}
                  <span v-if="task.completed" class="stamp">已交付</span>
                </button>
              </template>
            </div>
            <div v-if="tasks.length === 0" class="empty-hint">
              今日暂无委托，点击「+ 新增委托」开始，或用 AI 对话生成。
            </div>
          </div>

          <!-- Achievements tab -->
          <div v-if="tab === 'achievements'" class="ach-cards">
            <div
              v-for="ach in summary?.achievements ?? []"
              :key="ach.achievement_id"
              class="ach-card pixel-border"
              :class="{ unlocked: ach.unlocked, locked: !ach.unlocked }"
            >
              <div class="ac-icon">{{ ach.unlocked ? ach.icon : '?' }}</div>
              <div class="ac-content">
                <div class="ac-name">{{ ach.unlocked ? ach.name : '未解锁' }}</div>
                <div class="ac-desc">{{ ach.description }}</div>
                <div class="ac-footer">
                  <span class="ac-exp">+{{ ach.exp_reward }} EXP</span>
                  <span v-if="ach.unlocked && ach.unlocked_at" class="ac-date">{{ ach.unlocked_at.slice(0, 10) }}</span>
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- Achievement tooltip -->
    <Teleport to="body">
      <div v-if="hoveredAch" class="ach-tooltip" :style="achTooltipStyle">
        <div class="at-name">{{ hoveredAch.unlocked ? hoveredAch.name : '未解锁' }}</div>
        <div class="at-desc">{{ hoveredAch.description }}</div>
        <div class="at-exp">+{{ hoveredAch.exp_reward }} EXP</div>
        <div v-if="hoveredAch.unlocked && hoveredAch.unlocked_at" class="at-date">解锁于 {{ hoveredAch.unlocked_at.slice(0, 10) }}</div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&display=swap');

/* ═══════ 本页令牌：--pixel-* 重映射为高级深色（浅色自适应）═══════ */
.quests-page {
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

  min-height: 100%;
  font-family: var(--d-f-body);
  color: var(--pixel-text);
}
[data-theme="light"] .quests-page {
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

.q-layout { display: grid; grid-template-columns: 1fr 3fr; gap: 20px; align-items: start; }

/* ===== Sidebar ===== */
.q-sidebar { display: flex; flex-direction: column; gap: 12px; position: sticky; top: 0; }

.portrait-card {
  background: var(--pixel-card-bg); backdrop-filter: blur(10px);
  border: 1px solid var(--pixel-border); border-radius: var(--d-radius); box-shadow: var(--d-shadow-sm);
  display: flex; align-items: center; gap: 12px; padding: 12px 14px;
}
.pc-frame { width: 56px; height: 72px; border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); background: var(--pixel-bg-secondary); overflow: hidden; flex-shrink: 0; }
.pc-img { width: 100%; height: 100%; object-fit: cover; image-rendering: pixelated; }
.pc-info { display: flex; flex-direction: column; gap: 4px; min-width: 0; }
.pc-name { font-family: var(--d-f-display); font-size: 15px; font-weight: 700; color: var(--pixel-text); }
.pc-level { font-family: var(--d-f-mono); font-size: 12px; color: var(--pixel-primary); }

.sp-card {
  background: var(--pixel-card-bg); backdrop-filter: blur(10px);
  border: 1px solid var(--pixel-border); border-radius: var(--d-radius); box-shadow: var(--d-shadow-sm);
  overflow: hidden;
}
.sp-section-header { display: flex; align-items: center; gap: 8px; padding: 11px 14px; font-family: var(--d-f-mono); font-size: 12px; color: var(--pixel-text); border-bottom: 1px solid var(--pixel-border); letter-spacing: .02em; }
.sp-icon { font-size: 14px; color: var(--pixel-primary); width: 16px; text-align: center; }
.sp-icon.flame { color: var(--pixel-warning); }
.sp-badge { margin-left: auto; font-family: var(--d-f-mono); font-size: 11px; padding: 2px 9px; border: 1px solid var(--pixel-border); border-radius: 999px; color: var(--pixel-text-secondary); }
.sp-badge.warn { color: var(--pixel-warning); border-color: rgba(251, 191, 36, .4); background: rgba(251, 191, 36, .08); }
.sp-body { padding: 12px 14px; }

.exp-bar-track { height: 10px; background: var(--pixel-bg-secondary); border-radius: 999px; overflow: hidden; }
.exp-bar-fill { height: 100%; background: var(--d-grad); box-shadow: 0 0 8px rgba(124, 92, 255, .4); transition: width .4s cubic-bezier(.2, .7, .2, 1); }
.lm-label { font-family: var(--d-f-mono); font-size: 11px; color: var(--pixel-text-secondary); margin-top: 8px; }

.streak-body { display: flex; align-items: center; gap: 14px; }
.streak-flame { font-size: 13px; color: var(--pixel-warning); letter-spacing: 2px; }
.streak-num { font-family: var(--d-f-display); font-size: 24px; font-weight: 700; color: var(--pixel-warning); line-height: 1; }
.streak-sub { font-family: var(--d-f-mono); font-size: 10px; color: var(--pixel-text-secondary); margin-top: 3px; letter-spacing: .04em; }

.status-track { height: 8px; background: var(--pixel-bg-secondary); border-radius: 999px; overflow: hidden; }
.status-fill { height: 100%; background: linear-gradient(90deg, #22c55e, var(--pixel-success)); transition: width .4s cubic-bezier(.2, .7, .2, 1); }

.ach-mini-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 7px; }
.ach-mini { aspect-ratio: 1; display: flex; align-items: center; justify-content: center; background: var(--pixel-bg-secondary); border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); font-size: 18px; color: var(--pixel-text-secondary); opacity: .4; transition: transform .12s ease, border-color .15s ease; }
.ach-mini.unlocked { border-color: rgba(251, 191, 36, .5); color: var(--pixel-warning); background: rgba(251, 191, 36, .1); opacity: 1; }
.ach-mini:hover { transform: scale(1.1); }

/* ===== Main ===== */
.q-main { display: flex; flex-direction: column; gap: 16px; }
.q-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
.toolbar-left, .toolbar-right { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }

.back-btn { display: inline-flex; align-items: center; gap: 6px; background: var(--pixel-card-bg); border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); color: var(--pixel-text-secondary); font-family: var(--d-f-body); font-size: 13px; padding: 7px 12px; cursor: pointer; transition: color .2s ease, border-color .2s ease; }
.back-btn:hover { color: var(--pixel-primary); border-color: var(--pixel-primary); }

.q-title { font-family: var(--d-f-display); font-size: 18px; font-weight: 700; color: var(--pixel-text); display: flex; align-items: center; gap: 10px; margin: 0; letter-spacing: -.01em; }
.title-icon { color: var(--pixel-primary); font-size: 16px; }
.q-date { font-family: var(--d-f-mono); font-size: 11px; color: var(--pixel-text-secondary); }

.tab-btn { font-family: var(--d-f-body); font-weight: 600; font-size: 13px; padding: 7px 14px; border-radius: 999px; border: 1px solid var(--pixel-border); background: var(--pixel-card-bg); color: var(--pixel-text-secondary); cursor: pointer; transition: color .2s ease, background .2s ease, border-color .2s ease; }
.tab-btn:hover { color: var(--pixel-text); border-color: var(--pixel-text-secondary); }
.tab-btn.active { color: #0a0b10; background: var(--d-grad); border-color: transparent; }
[data-theme="light"] .tab-btn.active { color: #fff; }

.add-btn { font-family: var(--d-f-body); font-weight: 600; font-size: 13px; padding: 7px 14px; border-radius: var(--d-radius-sm); border: 1px solid rgba(251, 191, 36, .4); background: rgba(251, 191, 36, .1); color: var(--pixel-warning); cursor: pointer; transition: background .2s ease; }
.add-btn:hover { background: rgba(251, 191, 36, .16); }

/* ===== Add / Edit panel ===== */
.add-panel { background: var(--pixel-card-bg); backdrop-filter: blur(10px); border: 1px solid var(--pixel-border); border-radius: var(--d-radius); box-shadow: var(--d-shadow-sm); padding: 14px; display: flex; flex-direction: column; gap: 10px; }
.pixel-input, .pixel-select { font-family: var(--d-f-body); font-size: 13px; background: var(--pixel-bg-secondary); border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); color: var(--pixel-text); padding: 9px 11px; outline: none; transition: border-color .2s ease, box-shadow .2s ease; }
.pixel-input:focus, .pixel-select:focus { border-color: var(--pixel-primary); box-shadow: 0 0 0 3px rgba(34, 211, 238, .16); }
.pixel-input::placeholder { color: var(--pixel-text-secondary); opacity: .6; }
.pixel-select { cursor: pointer; }
.add-title { font-size: 14px; }
.add-row { display: flex; align-items: flex-end; gap: 12px; flex-wrap: wrap; }
.add-field { display: flex; flex-direction: column; gap: 5px; font-family: var(--d-f-mono); font-size: 11px; color: var(--pixel-text-secondary); }
.add-field .pixel-input.num, .add-field .pixel-select { width: 100px; }
.add-actions { display: flex; gap: 8px; margin-left: auto; }
.btn-primary { font-family: var(--d-f-body); font-weight: 700; font-size: 13px; padding: 9px 16px; border-radius: var(--d-radius-sm); border: 0; cursor: pointer; color: #0a0b10; background: var(--d-grad); box-shadow: 0 8px 22px -10px rgba(99, 102, 241, .8); transition: box-shadow .2s ease; }
.btn-primary:hover { box-shadow: 0 12px 28px -8px rgba(99, 102, 241, .95); }
[data-theme="light"] .btn-primary { color: #fff; }
.btn-ghost { font-family: var(--d-f-body); font-weight: 600; font-size: 13px; padding: 9px 16px; border-radius: var(--d-radius-sm); border: 1px solid var(--pixel-border); background: var(--pixel-card-bg); color: var(--pixel-text-secondary); cursor: pointer; transition: color .2s ease, border-color .2s ease; }
.btn-ghost:hover { color: var(--pixel-text); border-color: var(--pixel-text-secondary); }

/* ===== Task cards ===== */
.task-cards { display: flex; flex-direction: column; gap: 10px; }
.task-card { background: var(--pixel-card-bg); backdrop-filter: blur(10px); border: 1px solid var(--pixel-border); border-radius: var(--d-radius); box-shadow: var(--d-shadow-sm); display: grid; grid-template-columns: 44px 1fr auto auto 48px; gap: 12px; align-items: center; padding: 12px 14px; transition: border-color .2s ease, transform .12s ease; }
.task-card:hover { border-color: var(--pixel-primary); transform: translateY(-1px); }
.task-card.completed { background: var(--pixel-bg-secondary); opacity: .8; }
.task-card.editing { grid-template-columns: 1fr; }
.edit-body { display: flex; flex-direction: column; gap: 8px; }
.task-gem { width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; font-size: 20px; color: #0a0b10; border-radius: var(--d-radius-sm); font-family: var(--d-f-display); }
.task-main { min-width: 0; display: flex; flex-direction: column; gap: 4px; }
.task-title { font-family: var(--d-f-body); font-size: 14px; font-weight: 600; color: var(--pixel-text); }
.task-card.completed .task-title { color: var(--pixel-text-secondary); text-decoration: line-through; text-decoration-color: var(--pixel-accent); }
.task-desc { font-size: 12px; color: var(--pixel-text-secondary); line-height: 1.4; }
.task-meta { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; font-family: var(--d-f-mono); font-size: 11px; color: var(--pixel-text-secondary); }
.meta-stars { color: var(--pixel-warning); letter-spacing: 1px; }
.meta-cat { color: var(--pixel-info); }
.meta-tag { padding: 1px 7px; border: 1px solid var(--pixel-border); border-radius: 999px; }
.meta-tag.ai { color: var(--pixel-info); border-color: rgba(56, 189, 248, .4); }
.meta-steps { display: inline-flex; align-items: center; gap: 6px; }
.step-btn { width: 22px; height: 22px; background: var(--pixel-bg-secondary); border: 1px solid var(--pixel-border); border-radius: 6px; color: var(--pixel-text); cursor: pointer; font-size: 13px; line-height: 1; transition: border-color .15s ease, color .15s ease; }
.step-btn:hover:not(:disabled) { border-color: var(--pixel-primary); color: var(--pixel-primary); }
.step-btn:disabled { opacity: .4; cursor: default; }
.step-val { font-size: 11px; }
.task-exp { font-family: var(--d-f-mono); font-size: 13px; font-weight: 600; color: var(--pixel-warning); min-width: 36px; text-align: right; }
.task-actions { display: flex; flex-direction: column; gap: 4px; }
.icon-btn { width: 26px; height: 26px; background: var(--pixel-bg-secondary); border: 1px solid var(--pixel-border); border-radius: 7px; color: var(--pixel-text-secondary); cursor: pointer; font-size: 12px; line-height: 1; transition: border-color .15s ease, color .15s ease; }
.icon-btn:hover { border-color: var(--pixel-primary); color: var(--pixel-primary); }
.icon-btn.danger:hover { border-color: var(--pixel-accent); color: var(--pixel-accent); }
.task-check { width: 44px; height: 44px; background: var(--pixel-bg-secondary); border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); color: var(--pixel-text-secondary); cursor: pointer; font-size: 20px; position: relative; display: flex; align-items: center; justify-content: center; transition: border-color .2s ease, color .2s ease, background .2s ease; }
.task-check:hover { border-color: var(--pixel-success); color: var(--pixel-success); }
.task-check.done { background: var(--pixel-success); border-color: var(--pixel-success); color: #0a0b10; }
[data-theme="light"] .task-check.done { color: #fff; }
.task-check .stamp { position: absolute; top: -8px; left: 50%; transform: translateX(-50%) rotate(-12deg); font-family: var(--d-f-mono); font-size: 9px; color: var(--pixel-accent); white-space: nowrap; font-weight: 700; }

.loading-state { display: flex; flex-direction: column; align-items: center; padding: 60px 0; gap: 16px; }
.loading-text { font-family: var(--d-f-mono); font-size: 12px; color: var(--pixel-text-secondary); letter-spacing: .1em; }
.empty-hint { font-family: var(--d-f-body); font-size: 13px; color: var(--pixel-text-secondary); text-align: center; padding: 40px 0; opacity: .8; }

/* ===== Achievement cards ===== */
.ach-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 12px; }
.ach-card { background: var(--pixel-card-bg); backdrop-filter: blur(10px); border: 1px solid var(--pixel-border); border-radius: var(--d-radius); box-shadow: var(--d-shadow-sm); display: flex; gap: 14px; padding: 14px 16px; align-items: center; transition: border-color .2s ease, transform .12s ease; }
.ach-card:hover { transform: translateY(-2px); }
.ach-card.locked { opacity: .5; }
.ach-card.unlocked { border-color: rgba(251, 191, 36, .5); box-shadow: 0 0 24px -8px rgba(251, 191, 36, .3); }
.ac-icon { font-size: 26px; width: 36px; text-align: center; flex-shrink: 0; color: var(--pixel-text-secondary); }
.ach-card.unlocked .ac-icon { color: var(--pixel-warning); }
.ac-content { flex: 1; display: flex; flex-direction: column; gap: 4px; min-width: 0; }
.ac-name { font-family: var(--d-f-display); font-size: 14px; font-weight: 700; color: var(--pixel-text); }
.ach-card.unlocked .ac-name { color: var(--pixel-warning); }
.ac-desc { font-size: 12px; color: var(--pixel-text-secondary); line-height: 1.4; }
.ac-footer { display: flex; justify-content: space-between; align-items: center; margin-top: 2px; }
.ac-exp { font-family: var(--d-f-mono); font-size: 11px; color: var(--pixel-primary); }
.ac-date { font-family: var(--d-f-mono); font-size: 10px; color: var(--pixel-text-secondary); }

/* Tooltip */
.ach-tooltip { background: var(--pixel-bg-secondary); border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); padding: 10px 12px; box-shadow: var(--d-shadow); min-width: 150px; pointer-events: none; animation: tt-in .12s ease-out; }
@keyframes tt-in { from { opacity: 0; transform: translateY(-4px); } to { opacity: 1; transform: translateY(0); } }
.at-name { font-family: var(--d-f-display); font-size: 13px; font-weight: 700; color: var(--pixel-warning); margin-bottom: 5px; }
.at-desc { font-size: 11px; color: var(--pixel-text); line-height: 1.45; margin-bottom: 5px; }
.at-exp { font-family: var(--d-f-mono); font-size: 10px; color: var(--pixel-primary); }
.at-date { font-family: var(--d-f-mono); font-size: 10px; color: var(--pixel-text-secondary); margin-top: 5px; padding-top: 5px; border-top: 1px solid var(--pixel-border); }

/* ===== Responsive ===== */
@media (max-width: 900px) {
  .q-layout { grid-template-columns: 1fr; }
  .q-sidebar { position: static; }
}
</style>

