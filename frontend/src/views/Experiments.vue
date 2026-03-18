<template>
  <div class="experiments">
    <div class="page-header">
      <div>
        <n-h2 style="margin: 0 0 8px 0">实验管理</n-h2>
        <n-text depth="3">管理和跟踪训练实验</n-text>
      </div>
      <n-button type="primary" @click="showCreateModal">
        <template #icon>
          <n-icon :component="AddCircleOutline" />
        </template>
        新建实验
      </n-button>
    </div>

    <n-card :bordered="false" style="margin-top: 16px">
      <n-data-table
        :columns="columns"
        :data="experiments"
        :loading="loading"
        :pagination="pagination"
      />
    </n-card>

    <n-modal
      v-model:show="showModal"
      :title="editingId ? '编辑实验' : '新建实验'"
      preset="dialog"
      :style="{ width: '600px' }"
    >
      <n-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-placement="top"
      >
        <n-form-item label="实验名称" path="name">
          <n-input v-model:value="form.name" placeholder="请输入实验名称" />
        </n-form-item>

        <n-form-item label="策略名称" path="strategy">
          <n-input v-model:value="form.strategy" placeholder="请输入策略名称" />
        </n-form-item>

        <n-form-item label="配置 (JSON 格式)" path="config">
          <n-input
            v-model:value="form.configText"
            type="textarea"
            :rows="8"
            placeholder='{"steps": 10000, "lr": 0.001}'
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
import { ref, reactive, onMounted, h } from 'vue'
import { useRouter } from 'vue-router'
import type { DataTableColumns, FormInst, FormRules } from 'naive-ui'
import { message } from 'naive-ui'
import { NTag, NButton } from 'naive-ui'
import { AddCircleOutline, CreateOutline, TrashOutline } from '@vicons/ionicons5'
import { experimentApi } from '@/services/api'
import type { Experiment } from '@/types'

const experiments = ref<Experiment[]>([])
const loading = ref(false)
const showModal = ref(false)
const editingId = ref<string | null>(null)
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

const pagination = { pageSize: 10 }

const renderStatusTag = (status: string) => {
  const config: Record<string, { type: string }> = {
    pending: { type: 'default' },
    running: { type: 'info' },
    completed: { type: 'success' },
    failed: { type: 'error' },
  }
  return h(NTag, { type: config[status]?.type as any || 'default' }, { default: () => status })
}

const router = useRouter()

const columns: DataTableColumns = [
  {
    title: '实验名称',
    key: 'name',
    render: (row) =>
      h('a', {
        style: 'color: #1677ff; cursor: pointer; text-decoration: none;',
        onClick: () => router.push(`/experiments/${row.id}`),
      }, row.name),
  },
  { title: '策略', key: 'strategy' },
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
            onClick: () => handleEdit(row),
          },
          { default: () => '编辑', icon: () => h(CreateOutline) }
        ),
        h(
          NButton,
          {
            size: 'small',
            type: 'error',
            onClick: () => handleDelete(row.id),
          },
          { default: () => '删除', icon: () => h(TrashOutline) }
        ),
      ]),
  },
]

const loadExperiments = async () => {
  loading.value = true
  try {
    const res = await experimentApi.list()
    if (res.success) {
      experiments.value = res.data || []
    }
  } catch (error) {
    console.error('加载失败:', error)
  } finally {
    loading.value = false
  }
}

const showCreateModal = () => {
  editingId.value = null
  form.name = ''
  form.strategy = ''
  form.configText = '{}'
  showModal.value = true
}

const handleEdit = (row: Experiment) => {
  editingId.value = row.id
  form.name = row.name
  form.strategy = row.strategy
  form.configText = JSON.stringify(row.config, null, 2)
  showModal.value = true
}

const handleDelete = async (id: string) => {
  try {
    await experimentApi.delete(id)
    message.success('删除成功')
    loadExperiments()
  } catch (error) {
    console.error('删除失败:', error)
  }
}

const handleSubmit = async () => {
  try {
    await formRef.value?.validate()
    const config = JSON.parse(form.configText)

    if (editingId.value) {
      await experimentApi.update(editingId.value, {
        name: form.name,
        strategy: form.strategy,
        config,
      })
      message.success('更新成功')
    } else {
      await experimentApi.create({
        name: form.name,
        strategy: form.strategy,
        config,
      })
      message.success('创建成功')
    }

    showModal.value = false
    loadExperiments()
  } catch (error: any) {
    if (error.message?.includes('JSON')) {
      message.error('配置必须是有效的 JSON 格式')
    }
  }
}

onMounted(() => {
  loadExperiments()
})
</script>

<style scoped>
.experiments {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
