/**
 * 实验卡片组件
 * 展示实验信息和操作
 */

import React from 'react';
import { Card, Space, Tag, Button, Descriptions, Progress } from 'antd';
import { ExperimentOutlined, CheckCircleOutlined, CloseCircleOutlined, ClockCircleOutlined } from '@ant-design/icons';
import PropTypes from 'prop-types';

const statusConfig = {
  pending: { color: 'default', icon: <ClockCircleOutlined />, text: '待处理' },
  queued: { color: 'blue', icon: <ClockCircleOutlined />, text: '队列中' },
  running: { color: 'processing', icon: <ClockCircleOutlined />, text: '运行中' },
  completed: { color: 'success', icon: <CheckCircleOutlined />, text: '已完成' },
  failed: { color: 'error', icon: <CloseCircleOutlined />, text: '失败' },
  stopped: { color: 'warning', icon: <CloseCircleOutlined />, text: '已停止' }
};

function ExperimentCard({
  experiment,
  onDetail,
  onDelete,
  loading = false
}) {
  const status = statusConfig[experiment?.status] || statusConfig.pending;
  
  const metrics = experiment?.metrics ? JSON.parse(experiment.metrics) : {};
  
  return (
    <Card
      title={
        <Space>
          <ExperimentOutlined />
          {experiment?.name || '未命名实验'}
        </Space>
      }
      extra={
        <Tag color={status.color} icon={status.icon}>
          {status.text}
        </Tag>
      }
      loading={loading}
      size="small"
    >
      <Descriptions column={1} size="small">
        <Descriptions.Item label="策略">
          {experiment?.strategy || '-'}
        </Descriptions.Item>
        <Descriptions.Item label="收益">
          {metrics.total_return ? `${(metrics.total_return * 100).toFixed(1)}%` : '-'}
        </Descriptions.Item>
        <Descriptions.Item label="夏普比率">
          {metrics.sharpe_ratio ? metrics.sharpe_ratio.toFixed(2) : '-'}
        </Descriptions.Item>
        <Descriptions.Item label="创建时间">
          {experiment?.created_at ? experiment.created_at.substring(0, 16) : '-'}
        </Descriptions.Item>
      </Descriptions>
      
      {experiment?.status === 'running' && (
        <Progress percent={metrics.progress || 0} size="small" style={{ marginTop: 12 }} />
      )}
      
      <Space style={{ marginTop: 12, width: '100%', justifyContent: 'flex-end' }}>
        <Button size="small" onClick={() => onDetail?.(experiment)}>
          详情
        </Button>
        <Button 
          size="small" 
          danger 
          disabled={experiment?.status === 'running'}
          onClick={() => onDelete?.(experiment)}
        >
          删除
        </Button>
      </Space>
    </Card>
  );
}

ExperimentCard.propTypes = {
  experiment: PropTypes.shape({
    id: PropTypes.string,
    name: PropTypes.string,
    strategy: PropTypes.string,
    status: PropTypes.string,
    metrics: PropTypes.string,
    created_at: PropTypes.string
  }),
  onDetail: PropTypes.func,
  onDelete: PropTypes.func,
  loading: PropTypes.bool
};

export default ExperimentCard;
