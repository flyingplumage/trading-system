/** 训练监控页面 - 支持 WebSocket 实时推送 */

import React, { useState, useEffect, useRef } from 'react';
import { Card, Table, Button, Space, Tag, Progress, Modal, Form, InputNumber, Select, message, Badge } from 'antd';
import { PlayCircleOutlined, SyncOutlined, WifiOutlined, WifiOutlined as WifiOffOutlined } from '@ant-design/icons';
import { PageHeader, StatusTag } from '@/components';
import { training, queue } from '@/services/api';

const { Option } = Select;

function TrainingPage() {
  const [loading, setLoading] = useState(false);
  const [tasks, setTasks] = useState([]);
  const [isStartVisible, setIsStartVisible] = useState(false);
  const [form] = Form.useForm();
  const wsRef = useRef(null);
  const [wsConnected, setWsConnected] = useState(false);

  useEffect(() => {
    loadTasks();
    connectWebSocket();
    
    const interval = setInterval(loadTasks, 10000);
    return () => {
      clearInterval(interval);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const connectWebSocket = () => {
    const wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:5000/ws?topics=training';
    
    try {
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onopen = () => {
        setWsConnected(true);
        console.log('[WebSocket] 已连接');
      };
      
      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('[WebSocket] 收到消息:', data);
        
        if (data.type === 'training_progress') {
          // 更新任务进度
          setTasks(prev => prev.map(t => 
            t.id === data.task_id 
              ? { ...t, progress: data.progress, metrics: data.metrics }
              : t
          ));
        } else if (data.type === 'training_complete') {
          message.success(`任务 ${data.task_id} 完成`);
          loadTasks();
        } else if (data.type === 'training_failed') {
          message.error(`任务 ${data.task_id} 失败：${data.error}`);
          loadTasks();
        }
      };
      
      wsRef.current.onclose = () => {
        setWsConnected(false);
        console.log('[WebSocket] 连接关闭');
      };
      
      wsRef.current.onerror = (error) => {
        console.error('[WebSocket] 错误:', error);
      };
    } catch (error) {
      console.error('[WebSocket] 连接失败:', error);
    }
  };

  const loadTasks = async () => {
    setLoading(true);
    try {
      const res = await training.tasks(null, 20);
      setTasks(res.data.data || []);
    } catch (error) {
      console.error('加载任务列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStart = async (values) => {
    setLoading(true);
    try {
      await training.start(
        values.strategy,
        values.steps,
        values.priority,
        values.use_queue,
        values.env_name,
        values.stock_code
      );
      message.success('训练任务已启动');
      setIsStartVisible(false);
      form.resetFields();
      loadTasks();
    } catch (error) {
      message.error('启动失败');
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    {
      title: '任务 ID',
      dataIndex: 'id',
      key: 'id',
      ellipsis: true,
      width: 80,
    },
    {
      title: '策略',
      dataIndex: 'strategy',
      key: 'strategy',
    },
    {
      title: '步数',
      dataIndex: 'steps',
      key: 'steps',
      width: 100,
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      width: 80,
      render: (p) => {
        const color = p <= 3 ? 'red' : p <= 6 ? 'orange' : 'blue';
        return <Tag color={color}>{p}</Tag>;
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status, record) => (
        <Space>
          <StatusTag status={status} />
          {status === 'running' && record.progress && (
            <span>{record.progress.toFixed(0)}%</span>
          )}
        </Space>
      ),
    },
    {
      title: '进度',
      key: 'progress',
      width: 150,
      render: (_, record) => {
        if (record.status === 'running' && record.progress) {
          return <Progress percent={record.progress.toFixed(0)} size="small" />;
        }
        if (record.status === 'completed') {
          return <Progress percent={100} status="success" size="small" />;
        }
        if (record.status === 'failed') {
          return <Progress percent={100} status="exception" size="small" />;
        }
        return '-';
      },
    },
    {
      title: '结果',
      dataIndex: 'result',
      key: 'result',
      ellipsis: true,
      render: (result) => {
        if (!result) return '-';
        try {
          const parsed = typeof result === 'string' ? JSON.parse(result) : result;
          if (parsed.portfolio_value) {
            return `¥${(parsed.portfolio_value / 10000).toFixed(1)}万`;
          }
        } catch {
          return '-';
        }
      },
    },
    {
      title: '错误',
      dataIndex: 'error',
      key: 'error',
      ellipsis: true,
      render: (error) => error ? <Tag color="red">{error.substring(0, 30)}...</Tag> : '-',
    },
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (date) => date ? date.replace('T', ' ').substring(0, 16) : '-',
    },
  ];

  return (
    <div>
      <PageHeader
        title="训练监控"
        extra={
          <Space>
            <Badge 
              count={wsConnected ? '已连接' : '未连接'} 
              status={wsConnected ? 'success' : 'error'}
              style={{ marginRight: 8 }}
            />
            <Button 
              icon={<WifiOutlined />} 
              onClick={connectWebSocket}
              disabled={wsConnected}
            >
              重连 WebSocket
            </Button>
            <Button icon={<SyncOutlined spin={loading} />} onClick={loadTasks}>
              刷新
            </Button>
            <Button 
              type="primary" 
              icon={<PlayCircleOutlined />} 
              onClick={() => setIsStartVisible(true)}
            >
              启动训练
            </Button>
          </Space>
        }
      />

      <Card size="small">
        <Table
          columns={columns}
          dataSource={tasks}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 20 }}
          size="small"
        />
      </Card>

      {/* 启动训练对话框 */}
      <Modal
        title="启动训练任务"
        open={isStartVisible}
        onOk={() => form.submit()}
        onCancel={() => {
          setIsStartVisible(false);
          form.resetFields();
        }}
        confirmLoading={loading}
      >
        <Form form={form} layout="vertical" onFinish={handleStart}>
          <Form.Item
            name="strategy"
            label="策略名称"
            rules={[{ required: true, message: '请输入策略名称' }]}
          >
            <Input placeholder="例如：momentum_v1" />
          </Form.Item>
          <Form.Item
            name="steps"
            label="训练步数"
            initialValue={10000}
            rules={[{ required: true }]}
          >
            <InputNumber style={{ width: '100%' }} min={1000} max={1000000} step={1000} />
          </Form.Item>
          <Form.Item
            name="priority"
            label="优先级"
            initialValue={5}
            rules={[{ required: true }]}
          >
            <InputNumber style={{ width: '100%' }} min={1} max={10} />
          </Form.Item>
          <Form.Item
            name="use_queue"
            label="使用队列"
            initialValue={true}
            valuePropName="checked"
          >
            <Select>
              <Option value={true}>是 (推荐)</Option>
              <Option value={false}>否 (直接执行)</Option>
            </Select>
          </Form.Item>
          <Form.Item
            name="env_name"
            label="环境名称"
            initialValue="momentum"
          >
            <Select>
              <Option value="momentum">动量策略</Option>
              <Option value="mean_reversion">均值回归</Option>
              <Option value="breakout">突破策略</Option>
            </Select>
          </Form.Item>
          <Form.Item
            name="stock_code"
            label="股票代码"
            initialValue="000001.SZ"
          >
            <Input placeholder="例如：000001.SZ" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

export default TrainingPage;
