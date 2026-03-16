/**
 * 策略卡片组件
 * 展示策略信息和操作
 */

import React from 'react';
import { Card, Space, Tag, Button, Descriptions, Rate } from 'antd';
import { RocketOutlined } from '@ant-design/icons';
import PropTypes from 'prop-types';

function StrategyCard({
  strategy,
  onDetail,
  onTrain,
  loading = false
}) {
  const performance = strategy?.performance || {};
  
  return (
    <Card
      title={
        <Space>
          <RocketOutlined />
          {strategy?.name || strategy?.id || '未命名策略'}
        </Space>
      }
      extra={
        <Tag color={strategy?.status === 'active' ? 'green' : 'default'}>
          {strategy?.status === 'active' ? '活跃' : '未激活'}
        </Tag>
      }
      loading={loading}
      size="small"
    >
      <Descriptions column={1} size="small">
        <Descriptions.Item label="描述">
          {strategy?.description || '-'}
        </Descriptions.Item>
        <Descriptions.Item label="最佳收益">
          {performance.best_return ? `${(performance.best_return * 100).toFixed(1)}%` : '-'}
        </Descriptions.Item>
        <Descriptions.Item label="夏普比率">
          {performance.best_sharpe ? performance.best_sharpe.toFixed(2) : '-'}
        </Descriptions.Item>
        <Descriptions.Item label="评分">
          <Rate disabled defaultValue={strategy?.rating || 3} size="small" />
        </Descriptions.Item>
      </Descriptions>
      
      <Space style={{ marginTop: 12, width: '100%', justifyContent: 'flex-end' }}>
        <Button size="small" onClick={() => onDetail?.(strategy)}>
          详情
        </Button>
        <Button 
          type="primary" 
          size="small"
          onClick={() => onTrain?.(strategy)}
        >
          训练
        </Button>
      </Space>
    </Card>
  );
}

StrategyCard.propTypes = {
  strategy: PropTypes.shape({
    id: PropTypes.string,
    name: PropTypes.string,
    description: PropTypes.string,
    status: PropTypes.string,
    rating: PropTypes.number,
    performance: PropTypes.shape({
      best_return: PropTypes.number,
      best_sharpe: PropTypes.number
    })
  }),
  onDetail: PropTypes.func,
  onTrain: PropTypes.func,
  loading: PropTypes.bool
};

export default StrategyCard;
