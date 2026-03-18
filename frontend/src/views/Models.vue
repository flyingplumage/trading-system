<template>
  <div class="models">
    <n-h2 style="margin-top: 0">模型管理</n-h2>
    <n-text depth="3" style="display: block; margin-bottom: 16px">
      管理和部署训练好的模型
    </n-text>

    <n-grid :cols="4" :x-gap="16" :y-gap="16" style="margin-bottom: 24px">
      <n-grid-item>
        <n-card class="stat-card" title="模型总数">
          <n-statistic :value="models.length">
            <template #prefix>
              <n-icon :component="RobotOutline" size="24" color="#1677ff" />
            </template>
          </n-statistic>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card class="stat-card" title="最佳模型">
          <n-statistic :value="bestModel ? bestModel.name : '-'" />
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card class="stat-card" title="本周新增">
          <n-statistic :value="weeklyCount">
            <template #suffix>个</template>
          </n-statistic>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card class="stat-card" title="部署中">
          <n-statistic :value="deployedCount">
            <template #suffix>个</template>
          </n-statistic>
        </n-card>
      </n-grid-item>
    </n-grid>

    <n-card title="模型列表" :bordered="false">
      <template #header-extra>
        <n-button type="primary" size="small" @click="showRegisterModal">
          <template #icon>
            <n-icon :component="AddCircleOutline" />
          </template>
          注册模型
        </n-button>
      </template>

      <n-data-table
        :columns="columns"
        :data="models"
        :loading="loading"
        :pagination="pagination"
      />
    </n-card>

    <n-modal
      v-model:show="showModal"
      title="注册模型"
      preset="dialog"
      :style="{ width: '600px' }"
    >
      <n-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-placement="top"
      >
        <n-form-item label="模型名称" path="name">
          <n-input v-model:value="form.name" placeholder="请输入模型名称" />
        </n-form-item>

        <n-form-item label="策略名称" path="strategy">
          <n-input v-model:value="form.strategy" placeholder="请输入策略名称" />
        </n-form-item>

        <n-form-item label="实验 ID" path="experiment_id">
          <n-input v-model:value="form.experiment_id" placeholder="关联的实验 ID" />
        </n-form-item>

        <n-form-item label="模型路径" path="model_path">
          <n-input v-model:value="form.model_path" placeholder="/path/to/model" />
        </n-form-item>

        <n-form-item label="性能指标 (JSON)" path="metricsText">
          <n-input
            v-model:value="form.metricsText"
            type="textarea"
            :rows="6"
            placeholder='{"reward": 0.85, "sharpe": 1.5}'
          />
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
import { ref, reactive, onMounted, computed, h } from 'vue'
import type { DataTableColumns, FormInst, FormRules } from 'naive-ui'
import { message } from 'naive-ui'
import { NTag, NButton } from 'naive-ui'
import {
  RobotOutline,
  AddCircleOutline,
  CloudUploadOutline,
  TrashOutline,
} from '@vicons/ionicons5'
import { modelApi } from '@/services/api'
import type { Model } from '@/types'

const models = ref<Model[]>([])
const loading = ref(false)
const showModal = ref(false)
const formRef = ref<FormInst | null>(null)

const form = reactive({
  name: '',
  strategy: '',
  experiment_id: '',
  model_path: '',
  metricsText: '{}',
})

const rules: FormRules = {
  name: { required: true, message: '请输入模型名称', trigger: 'blur' },
  strategy: { required: true, message: '请输入策略名称', trigger: 'blur' },
  experiment_id: { required: true, message: '请输入实验 ID', trigger: 'blur' },
  model_path: { required: true, message: '请输入模型路径', trigger: 'blur' },
}

const pagination = { pageSize: 10 }

const bestModel = computed(() => models.value[0] || null)
const weeklyCount = computed(() => models.value.length)
const deployedCount = computed(() => models.value.filter(m => m.version > 1).length)

const renderVersionTag = (version: number) => {
  const type = version === 1 ? 'default' : version <= 3 ? 'info' : 'success'
  return h(NTag, { type: type as any, size: 'small' }, { default: () => `v${version}` })
}

const columns: DataTableColumns = [
  { title: '模型名称', key: 'name' },
  { title: '策略', key: 'strategy' },
  {
    title: '版本',
    key: 'version',
    width: 80,
    render: (row) => renderVersionTag(row.version),
  },
  { title: '实验 ID', key: 'experiment_id', ellipsis: true },
  {
    title: '奖励',
    key: 'metrics',
    width: 100,
    render: (row) => (row.metrics?.reward ? row.metrics.reward.toFixed(4) : '-'),
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
            icon: () => h(CloudUploadOutline),
          },
          { default: () => '部署' }
        ),
        h(
          NButton,
          {
            size: 'small',
            type: 'error',
            icon: () => h(TrashOutline),
          },
          { default: () => '删除' }
        ),
      ]),
  },
]

const loadModels = async () => {
  loading.value = true
  try {
    const res = await modelApi.list()
    if (res.success) {
      models.value = res.data || []
    }
  } catch (error) {
    console.error('加载模型失败:', error)
  } finally {
    loading.value = false
  }
}

const showRegisterModal = () => {
  form.name = ''
  form.strategy = ''
  form.experiment_id = ''
  form.model_path = ''
  form.metricsText = '{}'
  showModal.value = true
}

const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    const metrics = JSON.parse(form.metricsText)

    await modelApi.register({
      name: form.name,
      strategy: form.strategy,
      experiment_id: form.experiment_id,
      model_path: form.model_path,
      metrics,
    })

    message.success('注册成功')
    showModal.value = false
    loadModels()
  } catch (error: any) {
    if (error.message?.includes('JSON')) {
      message.error('指标必须是有效的 JSON 格式')
    }
  }
}

onMounted(() => {
  loadModels()
})
</script>

<style scoped>
.models {
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
