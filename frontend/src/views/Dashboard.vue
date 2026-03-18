<template>
  <div class="dashboard">
    <n-h2 style="margin-top: 0">仪表盘</n-h2>

    <!-- 统计卡片 -->
    <n-grid :cols="4" :x-gap="16" :y-gap="16" style="margin-bottom: 24px">
      <n-grid-item>
        <n-card class="stat-card">
          <n-statistic label="实验总数">
            <template #prefix>
              <n-icon :component="FlaskOutline" size="24" color="#1677ff" />
            </template>
            <template #default>
              <n-number-animation :from="0" :to="stats?.experiments || 0" />
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>

      <n-grid-item>
        <n-card class="stat-card">
          <n-statistic label="模型总数">
            <template #prefix>
              <n-icon :component="RobotOutline" size="24" color="#52c41a" />
            </template>
            <template #default>
              <n-number-animation :from="0" :to="stats?.models || 0" />
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>

      <n-grid-item>
        <n-card class="stat-card">
          <n-statistic label="训练任务">
            <template #prefix>
              <n-icon :component="AnalyticsOutline" size="24" color="#faad14" />
            </template>
            <template #default>
              <n-number-animation :from="0" :to="stats?.training_tasks || 0" />
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>

      <n-grid-item>
        <n-card class="stat-card">
          <n-statistic label="系统状态">
            <template #prefix>
              <n-icon :component="CheckmarkCircleOutline" size="24" color="#52c41a" />
            </template>
            <template #default>
              <n-tag type="success" size="large" round>运行中</n-tag>
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
    </n-grid>

    <!-- 图表区域 -->
    <n-grid :cols="2" :x-gap="16" :y-gap="16" style="margin-bottom: 24px">
      <n-grid-item>
        <n-card title="训练奖励趋势" :bordered="false">
          <v-chart :option="rewardChartOption" :autoresize="true" style="height: 300px" />
        </n-card>
      </n-grid-item>

      <n-grid-item>
        <n-card title="任务状态分布" :bordered="false">
          <v-chart :option="pieChartOption" :autoresize="true" style="height: 300px" />
        </n-card>
      </n-grid-item>
    </n-grid>

    <!-- 任务队列 -->
    <n-card title="训练任务队列" :bordered="false">
      <n-data-table
        :columns="columns"
        :data="tasks"
        :loading="loading"
        :pagination="pagination"
      />
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, h, computed } from 'vue'
import type { DataTableColumns } from 'naive-ui'
import { NTag } from 'naive-ui'
import {
  FlaskOutline,
  RobotOutline,
  AnalyticsOutline,
  CheckmarkCircleOutline,
} from '@vicons/ionicons5'
import { useSystemStore } from '@/store/system'
import { systemApi, trainingApi } from '@/services/api'
import { wsService } from '@/services/websocket'
import type { TrainingTask } from '@/types'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
} from 'echarts/components'
import VChart from 'vue-echarts'

use([
  CanvasRenderer,
  LineChart,
  PieChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
])

const systemStore = useSystemStore()
const stats = systemStore.stats
const tasks = ref<TrainingTask[]>([])
const loading = ref(false)

const pagination = {
  pageSize: 10,
}

// 模拟训练奖励数据
const rewardData = ref([
  { step: 0, reward: 0.1 },
  { step: 1000, reward: 0.25 },
  { step: 2000, reward: 0.42 },
  { step: 3000, reward: 0.55 },
  { step: 4000, reward: 0.63 },
  { step: 5000, reward: 0.71 },
  { step: 6000, reward: 0.76 },
  { step: 7000, reward: 0.79 },
  { step: 8000, reward: 0.82 },
  { step: 9000, reward: 0.84 },
  { step: 10000, reward: 0.85 },
])

const rewardChartOption = computed(() => ({
  tooltip: {
    trigger: 'axis',
    formatter: '{b} 步<br/>奖励：{c}',
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    top: '10%',
    containLabel: true,
  },
  xAxis: {
    type: 'category',
    name: '训练步数',
    data: rewardData.value.map((d) => d.step),
  },
  yAxis: {
    type: 'value',
    name: '奖励',
    min: 0,
    max: 1,
  },
  series: [
    {
      name: '奖励',
      type: 'line',
      smooth: true,
      data: rewardData.value.map((d) => d.reward),
      areaStyle: {
        color: 'rgba(22, 119, 255, 0.2)',
      },
      lineStyle: {
        color: '#1677ff',
        width: 2,
      },
      itemStyle: {
        color: '#1677ff',
      },
    },
  ],
}))

const pieChartOption = computed(() => {
  const statusCount: Record<string, number> = {
    pending: 0,
    running: 0,
    completed: 0,
    failed: 0,
  }
  tasks.value.forEach((task) => {
    statusCount[task.status] = (statusCount[task.status] || 0) + 1
  })

  const statusMap: Record<string, string> = {
    pending: '等待中',
    running: '运行中',
    completed: '已完成',
    failed: '失败',
  }

  const colorMap: Record<string, string> = {
    pending: '#d9d9d9',
    running: '#1677ff',
    completed: '#52c41a',
    failed: '#ff4d4f',
  }

  return {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)',
    },
    legend: {
      orient: 'vertical',
      left: 'left',
    },
    series: [
      {
        name: '任务状态',
        type: 'pie',
        radius: '60%',
        data: Object.keys(statusCount).map((key) => ({
          name: statusMap[key],
          value: statusCount[key],
          itemStyle: { color: colorMap[key] },
        })),
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)',
          },
        },
      },
    ],
  }
})

const renderStatusTag = (status: string) => {
  const config: Record<string, { type: string; icon: string }> = {
    pending: { type: 'default', icon: '⏳' },
    running: { type: 'info', icon: '🔄' },
    completed: { type: 'success', icon: '✅' },
    failed: { type: 'error', icon: '❌' },
  }
  const cfg = config[status] || { type: 'default', icon: '❓' }
  return h(NTag, { type: cfg.type as any, bordered: false }, { default: () => `${cfg.icon} ${status}` })
}

const renderPriorityTag = (priority: number) => {
  let type = 'default'
  if (priority <= 3) type = 'error'
  else if (priority <= 6) type = 'warning'
  else type = 'success'
  return h(NTag, { type: type as any, size: 'small' }, { default: () => String(priority) })
}

const columns: DataTableColumns = [
  { title: 'ID', key: 'id', width: 60 },
  { title: '策略', key: 'strategy' },
  { title: '步数', key: 'steps', width: 100 },
  {
    title: '优先级',
    key: 'priority',
    width: 80,
    render: (row) => renderPriorityTag(row.priority),
  },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render: (row) => renderStatusTag(row.status),
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 180,
    render: (row) => new Date(row.created_at).toLocaleString('zh-CN'),
  },
]

const loadData = async () => {
  loading.value = true
  try {
    const [statsRes, tasksRes] = await Promise.all([
      systemApi.getStatus(),
      trainingApi.getQueue(),
    ])
    if (statsRes.success) {
      systemStore.setStats(statsRes.data)
    }
    if (tasksRes.success) {
      tasks.value = tasksRes.data || []
    }
  } catch (error) {
    console.error('加载数据失败:', error)
  } finally {
    loading.value = false
  }
}

// WebSocket 更新
const handleTaskUpdate = (task: TrainingTask) => {
  const index = tasks.value.findIndex((t) => t.id === task.id)
  if (index > -1) {
    tasks.value[index] = { ...tasks.value[index], ...task }
    tasks.value = [...tasks.value]
  }
}

onMounted(() => {
  loadData()
  // 连接 WebSocket
  const wsUrl = `ws://${window.location.hostname}:5000/ws`
  wsService.connect(wsUrl)
  wsService.on('task_update', handleTaskUpdate)
})

onUnmounted(() => {
  wsService.off('task_update', handleTaskUpdate)
  wsService.disconnect()
})
</script>

<style scoped>
.dashboard {
  max-width: 1400px;
  margin: 0 auto;
}

.stat-card {
  transition: all 0.3s ease;
  cursor: pointer;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
</style>
