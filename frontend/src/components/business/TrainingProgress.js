/**
 * 训练进度组件
 * 展示训练任务的详细进度
 */

import React from 'react';
import { Card, Progress, Descriptions, Space, Tag } from 'antd';
import { CloudUploadOutlined, ClockCircleOutlined, CheckCircleOutlined } from '@ant-design/icons';
import PropTypes from 'prop-types';

function TrainingProgress({
  task,
  showDetails = true,
  loading = false
}) {
  const progress = task?.result?.progress || 0;
  const isCompleted = task?.status === 'completed';
  const isFailed = task?.status === 'failed';
  
  return (
    <Card
      title={
        <Space>
          <CloudUploadOutlined />
          {task?.strategy || '训练任务'}
        </Space>
      }
      extra={
        <Tag color={isCompleted ? 'success' : isFailed ? 'error' : 'processing'}>
          {task?.status || 'unknown'}
        </Tag>
      }
      loading={loading}
      size="small"
    >
      <Progress
        percent={Math.round(progress)}
        status={isFailed ? 'exception' : isCompleted ? 'success' : 'active'}
        format={(percent) => `${percent}%`}
      />
      
      {showDetails && (
        <Descriptions column={2} size="small" style={{ marginTop: 16 }}>
          <Descriptions.Item label="任务 ID">
            {task?.id || '-'}
          </Descriptions.Item>
          <Descriptions.Item label="步数">
            {task?.steps?.toLocaleString() || '-'}
          </Descriptions.Item>
          <Descriptions.Item label="优先级">
            <Tag>{task?.priority || 5}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="工作线程">
            {task?.worker_id || '-'}
          </Descriptions.Item>
          <Descriptions.Item label="创建时间" span={2}>
            {task?.created_at ? task.created_at.substring(0, 16) : '-'}
          </Descriptions.Item>
          {task?.started_at && (
            <Descriptions.Item label="开始时间" span={2}>
              {task.started_at.substring(0, 16)}
            </Descriptions.Item>
          )}
          {isCompleted && task?.completed_at && (
            <>
              <Descriptions.Item label="完成时间" span={2}>
                {task.completed_at.substring(0, 16)}
              </Descriptions.Item>
              <Descriptions.Item label="最终奖励" span={2}>
                {task?.result?.final_reward?.toFixed(2) || '-'}
              </Descriptions.Item>
            </>
          )}
        </Descriptions>
      )}
    </Card>
  );
}

TrainingProgress.propTypes = {
  task: PropTypes.shape({
    id: PropTypes.number,
    strategy: PropTypes.string,
    steps: PropTypes.number,
    status: PropTypes.string,
    priority: PropTypes.number,
    worker_id: PropTypes.string,
    created_at: PropTypes.string,
    started_at: PropTypes.string,
    completed_at: PropTypes.string,
    result: PropTypes.shape({
      progress: PropTypes.number,
      final_reward: PropTypes.number
    })
  }),
  showDetails: PropTypes.bool,
  loading: PropTypes.bool
};

export default TrainingProgress;
