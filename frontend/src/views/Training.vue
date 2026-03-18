<template>
  <div class="training">
    <div class="page-header">
      <div>
        <n-h2 style="margin: 0 0 8px 0">训练任务</n-h2>
        <n-text depth="3">管理和监控训练任务</n-text>
      </div>
      <n-button type="primary" @click="showCreateModal">
        <template #icon>
          <n-icon :component="AddCircleOutline" />
        </template>
        新建任务
      </n-button>
    </div>

    <n-grid :cols="4" :x-gap="16" :y-gap="16" style="margin-bottom: 24px">
      <n-grid-item>
        <n-card class="stat-card">
          <n-statistic label="等待中">
            <template #prefix>⏳</template>
            <template #default>
              <n-number-animation :to="pendingCount" />
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card class="stat-card">
          <n-statistic label="训练中">
            <template #prefix>🔄</template>
            <template #default>
              <n-number-animation :to="runningCount" />
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card class="stat-card">
          <n-statistic label="已完成">
            <template #prefix>✅</template>
            <template #default>
              <n-number-animation :to="completedCount" />
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card class="stat-card">
          <n-statistic label="失败">
            <template #prefix>❌</template>
            <template #default>
              <n-number-animation :to="failedCount" />
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
    </n-grid>

    <n-card title="任务队列" :bordered="false">
      <n-data-table
        :columns="columns"
        :data="tasks"
        :loading="loading"
        :pagination="pagination"
      />
    </n-card>

    <n-modal
      v-model:show="showModal"
      title="新建训练任务"
      preset="dialog"
      :style="{ width: '500px' }"
    >
      <n-form ref="formRef" :model="form" :rules="rules" label-placement="top">
        <n-form-item label="策略名称" path="strategy">
          <n-input v-model:value="form.strategy" placeholder="PPO, SAC, A2C 等" />
        </n-form-item>

        <n-form-item label="训练步数" path="steps">
          <n-input-number
            v-model:value="form.steps"
            :min="1000"
            :step="1000"
            placeholder="10000"
            style="width: 100%"
          />
        </n-form-item>

        <n-form-item label="优先级" path="priority">
          <n-slider v-model:value="form.priority" :min="1" :max="10" :marks="{ 1: '高', 5: '中', 10: '低' }" />
        </n-form-item>
      </n-form>

      <template #action>
        <n-button @click="showModal = false">取消</n-button>
        <n-button type="primary" @click="handleSubmit">确定</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, computed, h } from 'vue'
import type { DataTableColumns, FormInst, FormRules } from 'naive-ui'
import { message } from 'naive-ui'
import { NTag, NButton, NProgress } from 'naive-ui'
import { AddCircleOutline, PlayCircleOutline, StopCircleOutline } from '@vicons/ionicons5'
import { trainingApi } from '@/services/api'
import { wsService } from '@/services/websocket'
import type { TrainingTask } from '@/types'

const tasks = ref<TrainingTask[]>([])
const loading = ref(false)
const showModal = ref(false)
const formRef = ref<FormInst | null>(null)

const form = reactive({
  strategy: '',
  steps: 10000,
  priority: 5,
})

const rules: FormRules = {
  strategy: { required: true, message: '请输入策略名称', trigger: 'blur' },
  steps: { required: true, message: '请输入训练步数', trigger: 'blur' },
}

const pagination = { pageSize: 10 }

const pendingCount = computed(() => tasks.value.filter(t => t.status === 'pending').length)
const runningCount = computed(() => tasks.value.filter(t => t.status === 'running').length)
const completedCount = computed(() => tasks.value.filter(t => t.status === 'completed').length)
const failedCount = computed(() => tasks.value.filter(t => t.status === 'failed').length)

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

const renderProgress = (row: TrainingTask) => {
  if (row.status === 'running') {
    return h(NProgress, {
      type: 'line',
      percentage: 50,
      status: 'info',
      showIndicator: false,
      style: 'width: 100px',
    })
  }
  return '-'
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
    title: '进度',
    key: 'progress',
    width: 120,
    render: (row) => renderProgress(row),
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
  {
    title: '操作',
    key: 'actions',
    width: 150,
    render: (row) =>
      h('div', { style: 'display: flex; gap: 8px' }, [
        h(
          NButton,
          {
            size: 'small',
            type: 'info',
            disabled: row.status !== 'pending',
            icon: () => h(PlayCircleOutline),
          },
          { default: () => '启动' }
        ),
        h(
          NButton,
          {
            size: 'small',
            type: 'error',
            disabled: row.status === 'completed' || row.status === 'failed',
            icon: () => h(StopCircleOutline),
          },
          { default: () => '停止' }
        ),
      ]),
  },
]

const loadTasks = async () => {
  loading.value = true
  try {
    const res = await trainingApi.getQueue()
    if (res.success) {
      tasks.value = res.data || []
    }
  } catch (error) {
    console.error('加载任务失败:', error)
  } finally {
    loading.value = false
  }
}

const showCreateModal = () => {
  form.strategy = ''
  form.steps = 10000
  form.priority = 5
  showModal.value = true
}

const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    await trainingApi.create({
      strategy: form.strategy,
      steps: form.steps,
      priority: form.priority,
    })
    message.success('创建成功')
    showModal.value = false
    loadTasks()
  } catch (error) {
    console.error('创建失败:', error)
  }
}

// WebSocket 实时更新
const handleTaskUpdate = (task: TrainingTask) => {
  const index = tasks.value.findIndex((t) => t.id === task.id)
  if (index > -1) {
    tasks.value[index] = { ...tasks.value[index], ...task }
    tasks.value = [...tasks.value]
  } else {
    tasks.value.push(task)
  }
}

onMounted(() => {
  loadTasks()
  // 连接 WebSocket（如果后端支持）
  const wsUrl = `ws://${window.location.hostname}:5000/ws`
  wsService.connect(wsUrl)
  wsService.on('task_update', handleTaskUpdate)
  wsService.on('task_created', handleTaskUpdate)
  wsService.on('task_completed', handleTaskUpdate)
})

onUnmounted(() => {
  wsService.off('task_update', handleTaskUpdate)
  wsService.off('task_created', handleTaskUpdate)
  wsService.off('task_completed', handleTaskUpdate)
})
</script>

<style scoped>
.training {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
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
