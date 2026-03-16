/**
 * 任务列表组件
 * 展示任务列表和状态
 */

import React from 'react';
import { List, Space, Tag, Progress, Button, Popconfirm } from 'antd';
import { ClockCircleOutlined, CheckCircleOutlined, CloseCircleOutlined, StopOutlined } from '@ant-design/icons';
import PropTypes from 'prop-types';

const statusConfig = {
  pending: { color: 'default', icon: <ClockCircleOutlined />, text: '待处理' },
  queued: { color: 'blue', icon: <ClockCircleOutlined />, text: '队列中' },
  running: { color: 'processing', icon: <ClockCircleOutlined />, text: '运行中' },
  completed: { color: 'success', icon: <CheckCircleOutlined />, text: '已完成' },
  failed: { color: 'error', icon: <CloseCircleOutlined />, text: '失败' },
  cancelled: { color: 'warning', icon: <CloseCircleOutlined />, text: '已取消' }
};

function TaskList({
  tasks,
  onCancel,
  loading = false,
  showCancel = true
}) {
  const renderItem = (item) => {
    const status = statusConfig[item?.status] || statusConfig.pending;
    const progress = item?.result?.progress || (item.status === 'completed' ? 100 : 0);
    
    return (
      <List.Item
        actions={showCancel && (item.status === 'pending' || item.status === 'queued') ? [
          <Popconfirm
            title="确定取消此任务？"
            onConfirm={() => onCancel?.(item)}
            key="cancel"
          >
            <Button type="link" size="small" danger icon={<StopOutlined />}>
              取消
            </Button>
          </Popconfirm>
        ] : []}
      >
        <List.Item.Meta
          title={
            <Space>
              <span>{item.strategy}</span>
              <Tag color={status.color} icon={status.icon}>
                {status.text}
              </Tag>
            </Space>
          }
          description={
            <div>
              <div>步数：{item.steps?.toLocaleString()}</div>
              <Progress 
                percent={Math.round(progress)} 
                size="small"
                status={item.status === 'failed' ? 'exception' : 'normal'}
              />
            </div>
          }
        />
      </List.Item>
    );
  };

  return (
    <List
      loading={loading}
      dataSource={tasks}
      renderItem={renderItem}
      locale={{ emptyText: '暂无任务' }}
    />
  );
}

TaskList.propTypes = {
  tasks: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string,
      strategy: PropTypes.string,
      steps: PropTypes.number,
      status: PropTypes.string,
      result: PropTypes.shape({
        progress: PropTypes.number
      })
    })
  ),
  onCancel: PropTypes.func,
  loading: PropTypes.bool,
  showCancel: PropTypes.bool
};

export default TaskList;
