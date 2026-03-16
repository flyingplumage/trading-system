/** 任务队列页面 */

import React, { useState, useEffect } from 'react';
import { Card, Table, Button, Space, Tag, Progress, Modal, Form, InputNumber, Select, message } from 'antd';
import { PlayCircleOutlined, StopOutlined, SyncOutlined, ClockCircleOutlined } from '@ant-design/icons';
import { PageHeader, StatusTag } from '@/components';
import { queue, training } from '@/services/api';

const { Option } = Select;

function QueuePage() {
  const [loading, setLoading] = useState(false);
  const [queueStatus, setQueueStatus] = useState({
    queued: 0,
    running: 0,
    max_concurrent: 1,
    queue_tasks: [],
    running_tasks: []
  });
  const [isConfigVisible, setIsConfigVisible] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    loadQueueStatus();
    const interval = setInterval(loadQueueStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadQueueStatus = async () => {
    setLoading(true);
    try {
      const res = await queue.status();
      setQueueStatus(res.data);
    } catch (error) {
      console.error('加载队列状态失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleConfig = async (values) => {
    try {
      await queue.config(values.max_concurrent);
      message.success('配置已更新');
      setIsConfigVisible(false);
      loadQueueStatus();
    } catch (error) {
      message.error('配置失败');
    }
  };

  const handleCancelTask = async (taskId) => {
    try {
      await queue.cancel(taskId);
      message.success('任务已取消');
      loadQueueStatus();
    } catch (error) {
      message.error('取消失败');
    }
  };

  const queueColumns = [
    {
      title: '任务 ID',
      dataIndex: 'task_id',
      key: 'task_id',
      ellipsis: true,
    },
    {
      title: '策略',
      dataIndex: 'strategy',
      key: 'strategy',
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      render: (priority) => {
        const color = priority === 1 ? 'red' : priority === 5 ? 'orange' : 'blue';
        const text = priority === 1 ? '高' : priority === 5 ? '中' : '低';
        return <Tag color={color}>{text}</Tag>;
      },
    },
    {
      title: '位置',
      dataIndex: 'position',
      key: 'position',
      render: (position) => <ClockCircleOutlined /> + ` 第${position}位`,
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Button
          type="link"
          danger
          size="small"
          onClick={() => handleCancelTask(record.task_id)}
        >
          取消
        </Button>
      ),
    },
  ];

  const runningColumns = [
    {
      title: '任务 ID',
      dataIndex: 'task_id',
      key: 'task_id',
      ellipsis: true,
    },
    {
      title: '状态',
      key: 'status',
      render: () => <StatusTag status="running" />,
    },
  ];

  return (
    <div>
      <PageHeader 
        title="任务队列" 
        onRefresh={loadQueueStatus} 
        loading={loading}
        extra={
          <Space>
            <Button icon={<SyncOutlined spin={loading} />} onClick={loadQueueStatus}>
              刷新
            </Button>
            <Button type="primary" onClick={() => setIsConfigVisible(true)}>
              配置并发
            </Button>
          </Space>
        }
      />

      {/* 队列概览 */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Space size="large">
          <div>
            <div style={{ fontSize: 24, fontWeight: 'bold', color: '#1890ff' }}>
              {queueStatus.queued}
            </div>
            <div style={{ color: '#666' }}>等待中</div>
          </div>
          <div>
            <div style={{ fontSize: 24, fontWeight: 'bold', color: '#52c41a' }}>
              {queueStatus.running}
            </div>
            <div style={{ color: '#666' }}>运行中</div>
          </div>
          <div>
            <div style={{ fontSize: 24, fontWeight: 'bold', color: '#722ed1' }}>
              {queueStatus.max_concurrent}
            </div>
            <div style={{ color: '#666' }}>最大并发</div>
          </div>
        </Space>
      </Card>

      {/* 运行中的任务 */}
      <Card title="运行中的任务" size="small" style={{ marginBottom: 16 }}>
        <Table
          columns={runningColumns}
          dataSource={queueStatus.running_tasks.map(t => ({ task_id: t.task_id }))}
          rowKey="task_id"
          pagination={false}
          size="small"
          locale={{ emptyText: '暂无运行中的任务' }}
        />
      </Card>

      {/* 等待中的任务 */}
      <Card title="等待中的任务" size="small">
        <Table
          columns={queueColumns}
          dataSource={queueStatus.queue_tasks}
          rowKey="task_id"
          pagination={false}
          size="small"
          locale={{ emptyText: '队列空闲' }}
        />
      </Card>

      {/* 配置对话框 */}
      <Modal
        title="配置并发数"
        open={isConfigVisible}
        onOk={() => form.submit()}
        onCancel={() => setIsConfigVisible(false)}
      >
        <Form form={form} layout="vertical" onFinish={handleConfig}>
          <Form.Item
            name="max_concurrent"
            label="最大并发训练任务数"
            rules={[{ required: true, message: '请输入并发数' }]}
            initialValue={queueStatus.max_concurrent}
          >
            <InputNumber min={1} max={4} style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

export default QueuePage;
