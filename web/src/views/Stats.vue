<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick, computed } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import {
  getOverview, getByCategory, getDailyCostRank, getTrends,
  getWarrantyAlerts,
  type OverviewStats, type CategoryStat, type DailyCostRankItem,
  type MonthlyTrendPoint, type WarrantyAlert,
} from '../api/stats'
import { formatCurrency } from '../utils/format'

const router = useRouter()

// ── State ──
const loading = ref(true)
const overview = ref<OverviewStats | null>(null)
const categoryStats = ref<CategoryStat[]>([])
const costRank = ref<DailyCostRankItem[]>([])
const trends = ref<MonthlyTrendPoint[]>([])
const warrantyAlerts = ref<WarrantyAlert[]>([])

// ── Filters ──
const startDate = ref('')
const endDate = ref('')
const period = ref<'month' | 'quarter' | 'year'>('month')

// ── Chart refs ──
const pieChartRef = ref<HTMLDivElement>()
const rankChartRef = ref<HTMLDivElement>()
const trendChartRef = ref<HTMLDivElement>()

// Keep track of chart instances for cleanup
const chartInstances: echarts.ECharts[] = []

// ── Pixel constants ──
const COLORS = ['#41a6f6', '#b13e53', '#38b764', '#ef7d57', '#73eff7', '#ffcd75', '#5d275d', '#182548']

const statusLabel: Record<string, string> = {
  ACTIVE: '使用中', IDLE: '闲置', RETIRED: '退役', SOLD: '已售', DISCARDED: '已弃',
}
const statusColorMap: Record<string, string> = {
  ACTIVE: '#38b764', IDLE: '#ef7d57', RETIRED: '#7b8faa', SOLD: '#41a6f6', DISCARDED: '#b13e53',
}

const pixelTheme = {
  textStyle: { fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Microsoft YaHei', sans-serif", fontSize: 10, color: '#7b8faa' },
  grid: { top: 36, right: 16, bottom: 28, left: 48 },
}

const tooltipStyle = {
  backgroundColor: '#182548',
  borderColor: '#2e3d62',
  borderWidth: 2,
  textStyle: { color: '#f4f4f4', fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Microsoft YaHei', sans-serif", fontSize: 9 },
}

// ── Computed: status distribution from costRank ──
const statusDistribution = computed(() => {
  const counts: Record<string, number> = {}
  for (const item of costRank.value) {
    counts[item.status] = (counts[item.status] || 0) + 1
  }
  const total = costRank.value.length || 1
  return Object.entries(counts).map(([status, count]) => ({
    status,
    label: statusLabel[status] || status,
    count,
    pct: ((count / total) * 100).toFixed(1),
    color: statusColorMap[status] || '#7b8faa',
  }))
})

// ── Lifecycle summary ──
const lifecycleSummary = computed(() => {
  const counts: Record<string, number> = {}
  for (const item of costRank.value) {
    counts[item.status] = (counts[item.status] || 0) + 1
  }
  const total = costRank.value.length || 1
  const allStatuses = ['ACTIVE', 'IDLE', 'RETIRED', 'SOLD', 'DISCARDED']
  return allStatuses
    .filter(s => counts[s])
    .map(status => ({
      status,
      label: statusLabel[status],
      count: counts[status],
      pct: ((counts[status] / total) * 100).toFixed(1),
      color: statusColorMap[status],
    }))
})

// ── Data loading ──
async function loadAll() {
  loading.value = true
  disposeCharts()
  try {
    const trendParams: Record<string, string> = { period: period.value }
    if (startDate.value) trendParams.start_date = startDate.value
    if (endDate.value) trendParams.end_date = endDate.value

    const [ov, cat, rank, trend, warranty] = await Promise.all([
      getOverview(),
      getByCategory(),
      getDailyCostRank(10),
      getTrends(period.value),
      getWarrantyAlerts(90),
    ])
    overview.value = ov
    categoryStats.value = cat
    costRank.value = rank
    trends.value = trend
    warrantyAlerts.value = warranty
  } catch (e) {
    console.error('Stats load error', e)
  } finally {
    loading.value = false
    await nextTick()
    initCharts()
  }
}

// ── Chart initialization ──
function disposeCharts() {
  for (const c of chartInstances) {
    c.dispose()
  }
  chartInstances.length = 0
}

function makeChart(el: HTMLDivElement): echarts.ECharts {
  const chart = echarts.init(el)
  chartInstances.push(chart)
  return chart
}

function initCharts() {
  initPieChart()
  initRankChart()
  initTrendChart()
}

function initPieChart() {
  if (!pieChartRef.value || categoryStats.value.length === 0) return
  const chart = makeChart(pieChartRef.value)
  chart.setOption({
    ...pixelTheme,
    tooltip: {
      ...tooltipStyle,
      trigger: 'item',
      formatter: (p: any) => `${p.name}<br/>${p.value}件 (${p.percent}%)`,
    },
    series: [{
      type: 'pie',
      radius: ['30%', '60%'],
      center: ['50%', '55%'],
      itemStyle: { borderColor: '#0e1225', borderWidth: 2, borderRadius: 0 },
      label: {
        color: '#7b8faa',
        fontSize: 8,
        fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Microsoft YaHei', sans-serif",
        formatter: '{b}\n{d}%',
      },
      labelLine: { lineStyle: { color: '#2e3d62', width: 2 } },
      data: categoryStats.value.map((c, i) => ({
        name: c.category_name,
        value: c.item_count,
        itemStyle: { color: c.color || COLORS[i % COLORS.length] },
      })),
    }],
  })
}

function initRankChart() {
  if (!rankChartRef.value || costRank.value.length === 0) return
  const chart = makeChart(rankChartRef.value)
  const names = costRank.value
    .map(c => c.name.length > 8 ? c.name.slice(0, 8) + '..' : c.name)
    .reverse()
  const values = costRank.value.map(c => c.daily_cost).reverse()
  chart.setOption({
    ...pixelTheme,
    grid: { ...pixelTheme.grid, left: 80 },
    tooltip: {
      ...tooltipStyle,
      trigger: 'axis',
      formatter: (p: any) => `${p[0].name}<br/>日均: ¥${p[0].value.toFixed(2)}`,
    },
    xAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#141d38', type: [4, 4] } },
      axisLine: { show: false },
      axisLabel: {
        color: '#7b8faa', fontSize: 8,
        fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Microsoft YaHei', sans-serif",
        formatter: '¥{value}',
      },
    },
    yAxis: {
      type: 'category',
      data: names,
      axisLine: { lineStyle: { color: '#2e3d62', width: 2 } },
      axisTick: { show: false },
      axisLabel: { color: '#f4f4f4', fontSize: 8, fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Microsoft YaHei', sans-serif" },
    },
    series: [{
      type: 'bar',
      data: values,
      itemStyle: {
        color: (params: any) => {
          const i = costRank.value.length - 1 - params.dataIndex
          if (i < 1) return '#b13e53'
          if (i < 3) return '#ef7d57'
          if (i < 5) return '#ffcd75'
          return '#41a6f6'
        },
        borderColor: '#0e1225',
        borderWidth: 1,
        borderRadius: 0,
      },
      barWidth: '55%',
      label: {
        show: true,
        position: 'right',
        color: '#f4f4f4',
        fontSize: 8,
        fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Microsoft YaHei', sans-serif",
        formatter: (p: any) => '¥' + p.value.toFixed(2),
      },
    }],
  })
}

function initTrendChart() {
  if (!trendChartRef.value || trends.value.length === 0) return
  const chart = makeChart(trendChartRef.value)
  const months = trends.value.map(t => t.month.slice(5))
  const spending = trends.value.map(t => t.spending)
  let cumulative = 0
  const cumulativeData = spending.map(v => { cumulative += v; return cumulative })
  chart.setOption({
    ...pixelTheme,
    grid: { ...pixelTheme.grid, left: 56, right: 56 },
    tooltip: {
      ...tooltipStyle,
      trigger: 'axis',
      formatter: (params: any) => {
        let tip = params[0].axisValue + '<br/>'
        for (const p of params) {
          tip += `${p.seriesName}: ¥${p.value.toFixed(2)}<br/>`
        }
        return tip
      },
    },
    legend: {
      top: 4,
      right: 16,
      textStyle: { color: '#7b8faa', fontSize: 8, fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Microsoft YaHei', sans-serif" },
      itemWidth: 12,
      itemHeight: 8,
    },
    xAxis: {
      type: 'category',
      data: months,
      axisLine: { lineStyle: { color: '#2e3d62', width: 2 } },
      axisTick: { show: false },
      axisLabel: { color: '#7b8faa', fontSize: 8, fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Microsoft YaHei', sans-serif" },
    },
    yAxis: [
      {
        type: 'value',
        name: '月消费',
        nameTextStyle: { color: '#7b8faa', fontSize: 8, fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Microsoft YaHei', sans-serif" },
        splitLine: { lineStyle: { color: '#141d38', type: [4, 4] } },
        axisLine: { show: false },
        axisLabel: {
          color: '#7b8faa', fontSize: 8,
          fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Microsoft YaHei', sans-serif",
          formatter: '¥{value}',
        },
      },
      {
        type: 'value',
        name: '累计',
        nameTextStyle: { color: '#7b8faa', fontSize: 8, fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Microsoft YaHei', sans-serif" },
        splitLine: { show: false },
        axisLine: { show: false },
        axisLabel: {
          color: '#7b8faa', fontSize: 8,
          fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Microsoft YaHei', sans-serif",
          formatter: '¥{value}',
        },
      },
    ],
    series: [
      {
        name: '月消费',
        type: 'bar',
        data: spending,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#41a6f6' },
            { offset: 1, color: '#182548' },
          ]),
          borderColor: '#41a6f6',
          borderWidth: 1,
          borderRadius: 0,
        },
        barWidth: '40%',
      },
      {
        name: '累计消费',
        type: 'line',
        yAxisIndex: 1,
        data: cumulativeData,
        smooth: false,
        symbol: 'rect',
        symbolSize: 6,
        lineStyle: { color: '#ef7d57', width: 2, type: 'solid' },
        itemStyle: { color: '#ef7d57', borderColor: '#0e1225', borderWidth: 1 },
      },
    ],
  })
}

// ── Navigation ──
function goToItem(id: number) {
  router.push(`/items/${id}`)
}

// ── Lifecycle ──
function handleResize() {
  for (const c of chartInstances) {
    c.resize()
  }
}

onMounted(() => {
  loadAll()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  disposeCharts()
})
</script>

<template>
  <div class="stats-page animate-fade-in">
    <!-- Loading -->
    <div v-if="loading" class="loading-state">
      <div class="pixel-loading"></div>
      <span class="loading-text">加载中...</span>
    </div>

    <template v-else>
      <!-- ═══ Section 1: Time Range Filter Bar ═══ -->
      <div class="filter-bar">
        <div class="filter-group">
          <label class="filter-label">开始日期</label>
          <input v-model="startDate" type="date" class="pixel-input" />
        </div>
        <div class="filter-group">
          <label class="filter-label">结束日期</label>
          <input v-model="endDate" type="date" class="pixel-input" />
        </div>
        <div class="filter-group">
          <label class="filter-label">周期</label>
          <select v-model="period" class="pixel-input">
            <option value="month">MONTH</option>
            <option value="quarter">QUARTER</option>
            <option value="year">YEAR</option>
          </select>
        </div>
        <button class="pixel-btn pixel-btn-glow" @click="loadAll">刷新数据</button>
      </div>

      <!-- ═══ Section 2: Overview Cards ═══ -->
      <div class="overview-grid stagger-list">
        <div class="stat-card pixel-card-hover">
          <div class="stat-icon">&#9670;</div>
          <div class="stat-info">
            <div class="stat-value">{{ overview?.total_items ?? 0 }}</div>
            <div class="stat-label">物品总数</div>
          </div>
        </div>
        <div class="stat-card accent pixel-card-hover">
          <div class="stat-icon">$</div>
          <div class="stat-info">
            <div class="stat-value">{{ formatCurrency(overview?.total_assets_value ?? 0) }}</div>
            <div class="stat-label">资产总值</div>
          </div>
        </div>
        <div class="stat-card primary pixel-card-hover">
          <div class="stat-icon">&#9672;</div>
          <div class="stat-info">
            <div class="stat-value">{{ formatCurrency(overview?.avg_daily_cost ?? 0) }}</div>
            <div class="stat-label">日均成本</div>
          </div>
        </div>
        <div class="stat-card success pixel-card-hover">
          <div class="stat-icon">&#9654;</div>
          <div class="stat-info">
            <div class="stat-value">{{ overview?.active_items ?? 0 }}</div>
            <div class="stat-label">使用中</div>
          </div>
        </div>
      </div>

      <!-- ═══ Section 3: Category Analysis ═══ -->
      <div class="section-card pixel-card-hover">
        <h3 class="section-title">分类分析</h3>
        <div class="category-layout">
          <!-- Pie chart -->
          <div class="category-chart-col">
            <div v-if="categoryStats.length === 0" class="chart-empty">暂无数据</div>
            <div v-else ref="pieChartRef" class="chart-container chart-pie"></div>
          </div>
          <!-- Category table -->
          <div class="category-table-col">
            <div v-if="categoryStats.length === 0" class="chart-empty">暂无数据</div>
            <table v-else class="pixel-table">
              <thead>
                <tr>
                  <th>名称</th>
                  <th>数量</th>
                  <th>价值</th>
                  <th>日均</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(cat, idx) in categoryStats" :key="cat.category_id ?? idx">
                  <td>
                    <span class="color-dot" :style="{ background: cat.color || COLORS[idx % COLORS.length] }"></span>
                    {{ cat.category_name }}
                  </td>
                  <td>{{ cat.item_count }}</td>
                  <td>{{ formatCurrency(cat.total_value) }}</td>
                  <td>{{ formatCurrency(cat.avg_daily_cost) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- ═══ Section 4: Cost Analysis ═══ -->
      <div class="section-card pixel-card-hover">
        <h3 class="section-title">成本分析</h3>
        <div class="cost-layout">
          <!-- Daily cost rank bar chart -->
          <div class="cost-rank-col">
            <div v-if="costRank.length === 0" class="chart-empty">暂无数据</div>
            <div v-else ref="rankChartRef" class="chart-container chart-rank"></div>
          </div>
          <!-- Status distribution -->
          <div class="cost-status-col">
            <h4 class="sub-title">状态分布</h4>
            <div v-if="statusDistribution.length === 0" class="chart-empty-sm">暂无数据</div>
            <div v-else class="status-bars">
              <div v-for="s in statusDistribution" :key="s.status" class="status-bar-row">
                <div class="status-bar-label">{{ s.label }}</div>
                <div class="status-bar-track">
                  <div
                    class="status-bar-fill"
                    :style="{
                      width: s.pct + '%',
                      backgroundColor: s.color,
                    }"
                  ></div>
                </div>
                <div class="status-bar-count">{{ s.count }} ({{ s.pct }}%)</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ═══ Section 5: Spending Trends ═══ -->
      <div class="section-card pixel-card-hover">
        <h3 class="section-title">消费趋势</h3>
        <div v-if="trends.length === 0" class="chart-empty chart-wide">暂无数据</div>
        <div v-else ref="trendChartRef" class="chart-container chart-trend"></div>
      </div>

      <!-- ═══ Section 6: Warranty & Lifecycle ═══ -->
      <div class="section-card pixel-card-hover">
        <h3 class="section-title">保修与生命周期</h3>
        <div class="warranty-layout">
          <!-- Warranty alerts -->
          <div class="warranty-col">
            <h4 class="sub-title">
              <span class="title-icon">!</span>
              保修提醒
            </h4>
            <div v-if="warrantyAlerts.length === 0" class="chart-empty-sm">暂无提醒</div>
            <div v-else class="alert-list">
              <div
                v-for="alert in warrantyAlerts" :key="alert.id"
                class="alert-item pixel-card-hover"
                @click="goToItem(alert.id)"
              >
                <div class="alert-left">
                  <span class="alert-name">{{ alert.name }}</span>
                  <span class="alert-meta">
                    {{ formatCurrency(alert.purchase_price) }}
                  </span>
                </div>
                <span class="alert-days" :class="{ urgent: alert.days_remaining <= 7, warn: alert.days_remaining > 7 && alert.days_remaining <= 30 }">
                  {{ alert.days_remaining }}D
                </span>
              </div>
            </div>
          </div>
          <!-- Lifecycle summary -->
          <div class="lifecycle-col">
            <h4 class="sub-title">
              <span class="title-icon">&#9632;</span>
              LIFECYCLE SUMMARY
            </h4>
            <div v-if="lifecycleSummary.length === 0" class="chart-empty-sm">暂无数据</div>
            <div v-else class="lifecycle-list">
              <div v-for="item in lifecycleSummary" :key="item.status" class="lifecycle-item">
                <div class="lifecycle-header">
                  <span class="lifecycle-dot" :style="{ backgroundColor: item.color }"></span>
                  <span class="lifecycle-label">{{ item.label }}</span>
                </div>
                <div class="lifecycle-bar-row">
                  <div class="lifecycle-bar-track">
                    <div
                      class="lifecycle-bar-fill"
                      :style="{ width: item.pct + '%', backgroundColor: item.color }"
                    ></div>
                  </div>
                  <span class="lifecycle-pct">{{ item.pct }}%</span>
                </div>
                <div class="lifecycle-count">{{ item.count }} items</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&display=swap');

/* ═══════ 本页令牌：--pixel-* 重映射为高级深色（浅色自适应）═══════ */
.stats-page {
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
  gap: 20px;
  padding-bottom: 40px;
  font-family: var(--d-f-body);
  color: var(--pixel-text);
}
[data-theme="light"] .stats-page {
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

/* ===== Loading ===== */
.loading-state { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 400px; gap: 16px; }
.loading-text { font-family: var(--d-f-mono); font-size: 12px; color: var(--pixel-text-secondary); letter-spacing: .1em; }

/* ===== Filter Bar ===== */
.filter-bar { display: flex; align-items: flex-end; gap: 12px; background: var(--pixel-card-bg); backdrop-filter: blur(10px); border: 1px solid var(--pixel-border); border-radius: var(--d-radius); box-shadow: var(--d-shadow-sm); padding: 16px; flex-wrap: wrap; }
.filter-group { display: flex; flex-direction: column; gap: 6px; }
.filter-label { font-family: var(--d-f-mono); font-size: 11px; color: var(--pixel-text-secondary); letter-spacing: .04em; }

.pixel-input { background: var(--pixel-bg-secondary); border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); color: var(--pixel-text); font-family: var(--d-f-body); font-size: 13px; padding: 9px 11px; outline: none; min-width: 140px; transition: border-color .2s ease, box-shadow .2s ease; }
.pixel-input:focus { border-color: var(--pixel-primary); box-shadow: 0 0 0 3px rgba(34, 211, 238, .16); }
.pixel-input::-webkit-calendar-picker-indicator { filter: invert(1); }
[data-theme="light"] .pixel-input::-webkit-calendar-picker-indicator { filter: none; }

select.pixel-input { appearance: none; -webkit-appearance: none; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6'%3E%3Cpath d='M0 0l5 6 5-6z' fill='%237a8290'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: right 10px center; padding-right: 28px; cursor: pointer; }
select.pixel-input option { background: var(--pixel-bg-secondary); color: var(--pixel-text); }

.pixel-btn { font-family: var(--d-f-body); font-weight: 700; font-size: 13px; padding: 9px 18px; border-radius: var(--d-radius-sm); border: 0; cursor: pointer; color: #0a0b10; background: var(--d-grad); box-shadow: 0 8px 22px -10px rgba(99, 102, 241, .8); transition: box-shadow .2s ease; margin-left: auto; white-space: nowrap; }
.pixel-btn:hover { box-shadow: 0 12px 28px -8px rgba(99, 102, 241, .95); }
[data-theme="light"] .pixel-btn { color: #fff; }

/* ===== Overview Cards ===== */
.overview-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }

.stat-card { background: var(--pixel-card-bg); backdrop-filter: blur(10px); border: 1px solid var(--pixel-border); border-radius: var(--d-radius); box-shadow: var(--d-shadow-sm); padding: 22px; display: flex; align-items: center; gap: 16px; transition: border-color .2s ease, transform .12s ease, box-shadow .2s ease; }
.stat-card:hover { border-color: var(--pixel-text-secondary); transform: translateY(-2px); box-shadow: var(--d-shadow); }
.stat-card.accent .stat-icon { color: var(--pixel-accent); }
.stat-card.primary .stat-icon { color: var(--pixel-primary); }
.stat-card.success .stat-icon { color: var(--pixel-success); }

.stat-icon { font-family: var(--d-f-display); font-size: 26px; color: var(--pixel-primary); width: 56px; height: 56px; display: flex; align-items: center; justify-content: center; border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); background: var(--pixel-bg-secondary); flex-shrink: 0; }
.stat-info { flex: 1; min-width: 0; }
.stat-value { font-family: var(--d-f-display); font-size: 22px; font-weight: 700; color: var(--pixel-text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; letter-spacing: -.01em; animation: pixel-count-up 0.4s ease-out; }
.stat-label { font-family: var(--d-f-mono); font-size: 11px; color: var(--pixel-text-secondary); letter-spacing: .04em; margin-top: 4px; }

/* ===== Section Cards ===== */
.section-card { background: var(--pixel-card-bg); backdrop-filter: blur(10px); border: 1px solid var(--pixel-border); border-radius: var(--d-radius); box-shadow: var(--d-shadow-sm); padding: 20px; transition: border-color .2s ease; }
.section-card:hover { border-color: var(--pixel-text-secondary); }

.section-title { font-family: var(--d-f-display); font-size: 15px; font-weight: 700; color: var(--pixel-text); margin: 0 0 16px; padding-bottom: 10px; border-bottom: 1px solid var(--pixel-border); letter-spacing: -.01em; }
.sub-title { font-family: var(--d-f-mono); font-size: 11px; color: var(--pixel-text-secondary); margin: 0 0 12px; display: flex; align-items: center; gap: 6px; letter-spacing: .04em; }
.title-icon { color: var(--pixel-warning); }

/* ===== Category Layout ===== */
.category-layout { display: grid; grid-template-columns: 1fr 1.5fr; gap: 16px; }
.category-chart-col { min-height: 0; }
.chart-container { width: 100%; }
.chart-pie { height: 280px; }
.category-table-col { overflow-x: auto; }

/* ===== Table ===== */
.pixel-table { width: 100%; border-collapse: collapse; font-family: var(--d-f-body); font-size: 12px; color: var(--pixel-text); }
.pixel-table thead th { font-family: var(--d-f-mono); font-size: 11px; color: var(--pixel-text-secondary); letter-spacing: .04em; text-align: left; padding: 10px 12px; background: var(--pixel-bg-secondary); border-bottom: 1px solid var(--pixel-border); }
.pixel-table tbody td { padding: 10px 12px; border-bottom: 1px solid var(--pixel-border); white-space: nowrap; }
.pixel-table tbody tr:last-child td { border-bottom: 0; }
.pixel-table tbody tr { transition: background .15s ease; }
.pixel-table tbody tr:hover { background: var(--pixel-card-bg); }
.color-dot { display: inline-block; width: 10px; height: 10px; border-radius: 3px; margin-right: 8px; vertical-align: middle; }

/* ===== Cost Layout ===== */
.cost-layout { display: grid; grid-template-columns: 1.5fr 1fr; gap: 16px; }
.chart-rank { height: 320px; }

/* ===== Status Bars ===== */
.cost-status-col { display: flex; flex-direction: column; }
.status-bars { display: flex; flex-direction: column; gap: 12px; flex: 1; justify-content: center; }
.status-bar-row { display: flex; align-items: center; gap: 10px; }
.status-bar-label { font-family: var(--d-f-body); font-size: 12px; color: var(--pixel-text); width: 56px; text-align: right; flex-shrink: 0; }
.status-bar-track { flex: 1; height: 10px; background: var(--pixel-bg-secondary); border-radius: 999px; overflow: hidden; }
.status-bar-fill { height: 100%; border-radius: 999px; transition: width .4s cubic-bezier(.2, .7, .2, 1); }
.status-bar-count { font-family: var(--d-f-mono); font-size: 11px; color: var(--pixel-text-secondary); white-space: nowrap; min-width: 70px; }

/* ===== Trend Chart ===== */
.chart-trend { height: 300px; }
.chart-wide { width: 100%; }

/* ===== Warranty & Lifecycle ===== */
.warranty-layout { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.warranty-col, .lifecycle-col { min-width: 0; }

/* Alert list */
.alert-list { display: flex; flex-direction: column; gap: 8px; max-height: 320px; overflow-y: auto; }
.alert-item { display: flex; justify-content: space-between; align-items: center; padding: 10px 12px; background: var(--pixel-bg-secondary); border: 1px solid var(--pixel-border); border-radius: var(--d-radius-sm); cursor: pointer; transition: border-color .15s ease, transform .12s ease; }
.alert-item:hover { border-color: var(--pixel-warning); transform: translateX(2px); }
.alert-left { display: flex; flex-direction: column; gap: 2px; min-width: 0; flex: 1; }
.alert-name { font-size: 13px; color: var(--pixel-text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.alert-meta { font-family: var(--d-f-mono); font-size: 11px; color: var(--pixel-text-secondary); }
.alert-days { font-family: var(--d-f-mono); font-size: 12px; font-weight: 600; color: var(--pixel-warning); flex-shrink: 0; margin-left: 8px; }
.alert-days.warn { color: var(--pixel-warning); }
.alert-days.urgent { color: var(--pixel-accent); animation: pixel-blink 0.8s step-end infinite; }

/* Lifecycle list */
.lifecycle-list { display: flex; flex-direction: column; gap: 14px; }
.lifecycle-item { display: flex; flex-direction: column; gap: 5px; }
.lifecycle-header { display: flex; align-items: center; gap: 8px; }
.lifecycle-dot { width: 10px; height: 10px; border-radius: 3px; flex-shrink: 0; }
.lifecycle-label { font-family: var(--d-f-body); font-size: 12px; color: var(--pixel-text); }
.lifecycle-bar-row { display: flex; align-items: center; gap: 8px; }
.lifecycle-bar-track { flex: 1; height: 8px; background: var(--pixel-bg-secondary); border-radius: 999px; overflow: hidden; }
.lifecycle-bar-fill { height: 100%; border-radius: 999px; transition: width .4s cubic-bezier(.2, .7, .2, 1); }
.lifecycle-pct { font-family: var(--d-f-mono); font-size: 11px; color: var(--pixel-text-secondary); min-width: 40px; text-align: right; }
.lifecycle-count { font-family: var(--d-f-mono); font-size: 11px; color: var(--pixel-text-secondary); }

/* ===== Empty States ===== */
.chart-empty { display: flex; align-items: center; justify-content: center; height: 280px; font-family: var(--d-f-body); font-size: 13px; color: var(--pixel-text-secondary); }
.chart-empty-sm { display: flex; align-items: center; justify-content: center; padding: 32px; font-family: var(--d-f-body); font-size: 13px; color: var(--pixel-text-secondary); }

/* ===== Animations ===== */
@keyframes pixel-blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }

/* ===== Responsive ===== */
@media (max-width: 1024px) {
  .overview-grid { grid-template-columns: repeat(2, 1fr); }
  .category-layout { grid-template-columns: 1fr; }
  .cost-layout { grid-template-columns: 1fr; }
  .warranty-layout { grid-template-columns: 1fr; }
}

@media (max-width: 640px) {
  .overview-grid { grid-template-columns: 1fr; }
  .filter-bar { flex-direction: column; align-items: stretch; }
  .pixel-btn { margin-left: 0; }
  .pixel-input { min-width: 0; width: 100%; }
  .stat-value { font-size: 17px; }
  .stat-icon { width: 44px; height: 44px; font-size: 22px; }
}
</style>
