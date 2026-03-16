/**
 * 模型卡片组件
 * 展示模型信息和操作
 */

import React from 'react';
import { Card, Space, Tag, Button, Descriptions, Statistic } from 'antd';
import { DatabaseOutlined, DownloadOutlined } from '@ant-design/icons';
import PropTypes from 'prop-types';

function ModelCard({
  model,
  onDetail,
  onDownload,
  loading = false
}) {
  const metrics = model?.metrics ? JSON.parse(model.metrics) : {};
  
  return (
    <Card
      title={
        <Space>
          <DatabaseOutlined />
          {model?.name || '未命名模型'}
        </Space>
      }
      extra={<Tag color="blue">v{model?.version || 1}</Tag>}
      loading={loading}
      size="small"
    >
      <Descriptions column={1} size="small">
        <Descriptions.Item label="策略">
          {model?.strategy || '-'}
        </Descriptions.Item>
        <Descriptions.Item label="收益">
          {metrics.total_return ? (
            <span style={{ color: metrics.total_return > 0 ? '#52c41a' : '#f5222d' }}>
              {(metrics.total_return * 100).toFixed(1)}%
            </span>
          ) : '-'}
        </Descriptions.Item>
        <Descriptions.Item label="夏普比率">
          {metrics.sharpe_ratio ? metrics.sharpe_ratio.toFixed(2) : '-'}
        </Descriptions.Item>
        <Descriptions.Item label="胜率">
          {metrics.win_rate ? `${(metrics.win_rate * 100).toFixed(1)}%` : '-'}
        </Descriptions.Item>
      </Descriptions>
      
      <Space style={{ marginTop: 12, width: '100%', justifyContent: 'space-between' }}>
        <Statistic 
          title="实验ID" 
          value={model?.experiment_id?.substring(0, 8) || '-'} 
          valueStyle={{ fontSize: 12 }}
        />
        <Button 
          type="primary" 
          size="small" 
          icon={<DownloadOutlined />}
          onClick={() => onDownload?.(model)}
        >
          下载
        </Button>
      </Space>
    </Card>
  );
}

ModelCard.propTypes = {
  model: PropTypes.shape({
    id: PropTypes.string,
    name: PropTypes.string,
    strategy: PropTypes.string,
    version: PropTypes.number,
    experiment_id: PropTypes.string,
    metrics: PropTypes.string
  }),
  onDetail: PropTypes.func,
  onDownload: PropTypes.func,
  loading: PropTypes.bool
};

export default ModelCard;
