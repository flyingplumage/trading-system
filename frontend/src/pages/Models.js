/** 模型管理页面（使用业务组件重构） */

import React, { useState, useEffect } from 'react';
import { message } from 'antd';
import { DownloadOutlined } from '@ant-design/icons';
import { ModelCard, PageHeader, SearchBar } from '@/components';
import { models } from '@/services/api';

function Models() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState([]);
  const [filters, setFilters] = useState({});

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await models.list(filters.strategy, 100);
      setData(res.data.data || []);
    } catch (error) {
      message.error('加载模型列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (model) => {
    message.info(`下载模型：${model.name}`);
    // TODO: 实现下载逻辑
  };

  const handleDetail = (model) => {
    message.info(`查看详情：${model.name}`);
  };

  return (
    <div>
      <PageHeader
        title="模型管理"
        onRefresh={loadData}
        loading={loading}
      />

      <SearchBar
        onSearch={setFilters}
        onRefresh={() => {
          setFilters({});
          loadData();
        }}
        placeholder="搜索模型..."
      />

      {/* 模型卡片网格 */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
        gap: 16
      }}>
        {data.map((model) => (
          <ModelCard
            key={model.id}
            model={model}
            onDetail={handleDetail}
            onDownload={handleDownload}
          />
        ))}
      </div>
    </div>
  );
}

export default Models;
