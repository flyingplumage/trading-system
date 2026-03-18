<template>
  <div class="data">
    <n-h2 style="margin-top: 0">数据管理</n-h2>
    <n-text depth="3" style="display: block; margin-bottom: 24px">
      股票行情数据下载与管理
    </n-text>

    <n-grid :cols="4" :x-gap="16" :y-gap="16" style="margin-bottom: 24px">
      <n-grid-item>
        <n-card class="stat-card" title="数据源">
          <n-statistic value="Tushare Pro" />
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card class="stat-card" title="股票数量">
          <n-statistic :value="4800">
            <template #suffix>只</template>
          </n-statistic>
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card class="stat-card" title="数据日期">
          <n-statistic :value="new Date().toLocaleDateString('zh-CN')" />
        </n-card>
      </n-grid-item>
      <n-grid-item>
        <n-card class="stat-card" title="存储占用">
          <n-statistic :value="2.4">
            <template #suffix>GB</template>
          </n-statistic>
        </n-card>
      </n-grid-item>
    </n-grid>

    <n-card title="数据更新" :bordered="false" style="margin-bottom: 24px">
      <n-space>
        <n-button type="primary" @click="handleUpdateDaily">
          <template #icon>
            <n-icon :component="DownloadOutline" />
          </template>
          更新日线数据
        </n-button>
        <n-button @click="handleUpdateStockList">
          <template #icon>
            <n-icon :component="RefreshOutline" />
          </template>
          更新股票列表
        </n-button>
        <n-button @click="handleCleanCache">
          <template #icon>
            <n-icon :component="TrashOutline" />
          </template>
          清理缓存
        </n-button>
      </n-space>

      <n-alert title="更新说明" type="info" style="margin-top: 16px">
        日线数据每日 16:00 后自动更新，也可手动触发。股票列表每周更新一次。
      </n-alert>
    </n-card>

    <n-card title="股票池" :bordered="false">
      <n-data-table
        :columns="columns"
        :data="stockPool"
        :loading="loading"
        :pagination="pagination"
        :scroll-x="800"
      />
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, h, onMounted } from 'vue'
import type { DataTableColumns } from 'naive-ui'
import { message } from 'naive-ui'
import { NTag } from 'naive-ui'
import {
  DownloadOutline,
  RefreshOutline,
  TrashOutline,
  StarOutline,
} from '@vicons/ionicons5'

const loading = ref(false)

const stockPool = ref([
  { ts_code: '000001.SZ', name: '平安银行', industry: '银行', market: 'SZSE', list_date: '1991-04-03' },
  { ts_code: '000002.SZ', name: '万科 A', industry: '房地产', market: 'SZSE', list_date: '1991-01-29' },
  { ts_code: '600000.SH', name: '浦发银行', industry: '银行', market: 'SSE', list_date: '1999-11-10' },
  { ts_code: '600036.SH', name: '招商银行', industry: '银行', market: 'SSE', list_date: '2002-04-09' },
  { ts_code: '600519.SH', name: '贵州茅台', industry: '白酒', market: 'SSE', list_date: '2001-08-27' },
])

const pagination = { pageSize: 10 }

const renderMarketTag = (market: string) => {
  const config: Record<string, { type: string; text: string }> = {
    SSE: { type: 'success', text: '沪市' },
    SZSE: { type: 'info', text: '深市' },
  }
  const cfg = config[market] || { type: 'default', text: market }
  return h(NTag, { type: cfg.type as any, size: 'small' }, { default: () => cfg.text })
}

const columns: DataTableColumns = [
  { title: '代码', key: 'ts_code', width: 120 },
  { title: '名称', key: 'name', width: 100 },
  { title: '行业', key: 'industry' },
  {
    title: '市场',
    key: 'market',
    width: 80,
    render: (row) => renderMarketTag(row.market),
  },
  { title: '上市日期', key: 'list_date', width: 120 },
  {
    title: '操作',
    key: 'action',
    width: 80,
    render: () =>
      h(NTag, { type: 'default', size: 'small', icon: () => h(StarOutline) }, { default: () => '关注' }),
  },
]

const handleUpdateDaily = async () => {
  message.info('开始更新日线数据...')
  // TODO: 调用后端 API
  setTimeout(() => {
    message.success('日线数据更新完成')
  }, 2000)
}

const handleUpdateStockList = async () => {
  message.info('开始更新股票列表...')
  // TODO: 调用后端 API
  setTimeout(() => {
    message.success('股票列表更新完成')
  }, 2000)
}

const handleCleanCache = () => {
  message.success('缓存已清理')
}

onMounted(() => {
  // 加载股票池数据
})
</script>

<style scoped>
.data {
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
