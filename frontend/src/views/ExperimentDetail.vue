<template>
  <div class="experiment-detail">
    <div class="page-header">
      <n-space align="center">
        <n-button quaternary circle @click="goBack">
          <template #icon>
            <n-icon :component="ArrowBackOutline" />
          </template>
        </n-button>
        <div>
          <n-h2 style="margin: 0 0 8px 0">{{ experiment?.name || '实验详情' }}</n-h2>
          <n-text depth="3">ID: {{ experiment?.id }}</n-text>
        </div>
      </n-space>

      <n-space>
        <n-tag :type="statusType" size="large" round>
          {{ statusText }}
        </n-tag>
        <n-button type="primary" @click="handleEdit">编辑</n-button>
      </n-space>
    </div>

    <n-grid :cols="2" :x-gap="16" :y-gap="16" style="margin-top: 24px">
      <!-- 基本信息 -->
      <n-grid-item>
        <n-card title="基本信息" :bordered="false">
          <n-descriptions bordered :column="1">
            <n-descriptions-item label="实验名称">
              {{ experiment?.name }}
            </n-descriptions-item>
            <n-descriptions-item label="策略名称">
              <n-tag type="info">{{ experiment?.strategy }}</n-tag>
            </n-descriptions-item>
            <n-descriptions-item label="实验状态">
              <n-tag :type="statusType">{{ experiment?.status }}</n-tag>
            </n-descriptions-item>
            <n-descriptions-item label="创建时间">
              {{ formatDate(experiment?.created_at) }}
            </n-descriptions-item>
            <n-descriptions-item label="更新时间">
              {{ formatDate(experiment?.updated_at) }}
            </n-descriptions-item>
          </n-descriptions>
        </n-card>
      </n-grid-item>

      <!-- 性能指标 -->
      <n-grid-item>
        <n-card title="性能指标" :bordered="false">
          <n-grid :cols="2" :x-gap="8" :y-gap="8">
            <n-grid-item>
              <n-statistic label="总奖励" :value="metrics.reward || 0" :precision="4" />
            </n-grid-item>
            <n-grid-item>
              <n-statistic label="夏普比率" :value="metrics.sharpe || 0" :precision="2" />
            </n-grid-item>
            <n-grid-item>
              <n-statistic label="最大回撤" :value="metrics.max_drawdown || 0" :precision="2" suffix="%" />
            </n-grid-item>
            <n-grid-item>
              <n-statistic label="胜率" :value="metrics.win_rate || 0" :precision="2" suffix="%" />
            </n-grid-item>
          </n-grid>
        </n-card>
      </n-grid-item>
    </n-grid>

    <!-- 配置信息 -->
    <n-card title="实验配置" :bordered="false" style="margin-top: 16px">
      <n-code :code="configText" language="json" :wrap-line="true" />
    </n-card>

    <!-- 关联模型 -->
    <n-card title="关联模型" :bordered="false" style="margin-top: 16px">
      <n-data-table
        :columns="modelColumns"
        :data="relatedModels"
        :pagination="false"
        :single-line="false"
      />
    </n-card>

    <!-- 编辑弹窗 -->
    <n-modal
      v-model:show="showEditModal"
      title="编辑实验"
      preset="dialog"
      :style="{ width: '600px' }"
    >
      <n-form ref="formRef" :model="form" :rules="rules" label-placement="top">
        <n-form-item label="实验名称" path="name">
          <n-input v-model:value="form.name" placeholder="请输入实验名称" />
        </n-form-item>

        <n-form-item label="策略名称" path="strategy">
          <n-input v-model:value="form.strategy" placeholder="请输入策略名称" />
        </n-form-item>

        <n-form-item label="配置 (JSON)" path="configText">
          <n-input
            v-model:value="form.configText"
            type="textarea"
            :rows="8"
            placeholder='{"steps": 10000, "lr": 0.001}'
          />
        </n-form-item>
      </n-form>

      <template #action>
        <n-button @click="showEditModal = false">取消</n-button>
        <n-button type="primary" @click="handleSubmit">保存</n-button>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, h } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import type { DataTableColumns, FormInst, FormRules } from 'naive-ui'
import { message } from 'naive-ui'
import { NTag } from 'naive-ui'
import { ArrowBackOutline } from '@vicons/ionicons5'
import { experimentApi, modelApi } from '@/services/api'
import type { Experiment, Model } from '@/types'

const router = useRouter()
const route = useRoute()
const experiment = ref<Experiment | null>(null)
const relatedModels = ref<Model[]>([])
const loading = ref(false)
const showEditModal = ref(false)
const formRef = ref<FormInst | null>(null)

const form = reactive({
  name: '',
  strategy: '',
  configText: '{}',
})

const rules: FormRules = {
  name: { required: true, message: '请输入实验名称', trigger: 'blur' },
  strategy: { required: true, message: '请输入策略名称', trigger: 'blur' },
}

const metrics = computed(() => experiment.value?.metrics || {})
const configText = computed(() => {
  try {
    return JSON.stringify(experiment.value?.config || {}, null, 2)
  } catch {
    return '{}'
  }
})

const statusType = computed(() => {
  const map: Record<string, 'default' | 'info' | 'success' | 'error'> = {
    pending: 'default',
    running: 'info',
    completed: 'success',
    failed: 'error',
  }
  return map[experiment.value?.status || 'pending'] || 'default'
})

const statusText = computed(() => {
  const map: Record<string, string> = {
    pending: '等待中',
    running: '运行中',
    completed: '已完成',
    failed: '失败',
  }
  return map[experiment.value?.status || 'pending'] || '等待中'
})

const modelColumns: DataTableColumns = [
  { title: '模型名称', key: 'name' },
  { title: '版本', key: 'version', width: 80 },
  {
    title: '奖励',
    key: 'metrics',
    width: 100,
    render: (row) => row.metrics?.reward?.toFixed(4) || '-',
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 180,
    render: (row) => new Date(row.created_at).toLocaleString('zh-CN'),
  },
]

const goBack = () => {
  router.back()
}

const handleEdit = () => {
  if (!experiment.value) return
  form.name = experiment.value.name
  form.strategy = experiment.value.strategy
  form.configText = JSON.stringify(experiment.value.config, null, 2)
  showEditModal.value = true
}

const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    const config = JSON.parse(form.configText)

    await experimentApi.update(experiment.value!.id, {
      name: form.name,
      strategy: form.strategy,
      config,
    })

    message.success('更新成功')
    showEditModal.value = false
    loadExperiment()
  } catch (error: any) {
    if (error.message?.includes('JSON')) {
      message.error('配置必须是有效的 JSON 格式')
    }
  }
}

const formatDate = (date?: string) => {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-CN')
}

const loadExperiment = async () => {
  const id = route.params.id as string
  if (!id) return

  loading.value = true
  try {
    const res = await experimentApi.get(id)
    if (res.success) {
      experiment.value = res.data
    }
  } catch (error) {
    console.error('加载实验详情失败:', error)
    message.error('加载失败')
  } finally {
    loading.value = false
  }
}

const loadRelatedModels = async () => {
  try {
    const res = await modelApi.list()
    if (res.success) {
      const allModels = res.data || []
      relatedModels.value = allModels.filter(
        (m) => m.experiment_id === experiment.value?.id
      )
    }
  } catch (error) {
    console.error('加载关联模型失败:', error)
  }
}

onMounted(() => {
  loadExperiment()
})
</script>

<style scoped>
.experiment-detail {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.n-descriptions {
  margin-top: 16px;
}

.n-statistic {
  margin-bottom: 16px;
}
</style>
