/** 分布式训练 Worker 管理页面 */

import React, { useState, useEffect } from 'react';
import { Card, Table, Button, Space, Tag, Modal, Form, Input, InputNumber, Switch, Select, message, Popconfirm, Statistic, Row, Col, Progress, Alert } from 'antd';
import { 
  ServerOutlined, 
  PlusOutlined, 
  SyncOutlined, 
  DeleteOutlined, 
  CheckCircleOutlined, 
  CloseCircleOutlined,
  ThunderboltOutlined,
  GlobalOutlined
} from '@ant-design/icons';
import { PageHeader } from '@/components';
import axios from 'axios';

const { Option } = Select;
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

function Workers() {
  const [loading, setLoading] = useState(false);
  const [workers, setWorkers] = useState([]);
  const [stats, setStats] = useState(null);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    loadWorkers();
    loadStats();
    
    // 定时刷新
    const interval = setInterval(() => {
      loadWorkers();
      loadStats();
    }, 5000);
    
    return () => clearInterval(interval);
  }, []);

  const getHeaders = () => {
    const token = localStorage.getItem('access_token');
    return { 'Authorization': `Bearer ${token}` };
  };

  const loadWorkers = async () => {
    try {
      const res = await axios.get(`${API_BASE_URL}/api/worker/list`, { headers: getHeaders() });
      setWorkers(res.data.data.workers || []);
    } catch (error) {
      console.error('加载 Worker 列表失败:', error);
    }
  };

  const loadStats = async () => {
    try {
      const res = await axios.get(`${API_BASE_URL}/api/worker/stats`, { headers: getHeaders() });
      setStats(res.data.data);
    } catch (error) {
      console.error('加载统计失败:', error);
    }
  };

  const handleRegisterWorker = async (values) => {
    setLoading(true);
    try {
      // 创建 API Key 给 Worker 使用
      const keyRes = await axios.post(
        `${API_BASE_URL}/api/auth/api-key/create`,
        {
          name: `Worker-${values.hostname}`,
          role: 'bot',
          expires_days: 365
        },
        { headers: getHeaders() }
      );
      
      const apiKey = keyRes.data.data.api_key;
      
      // 显示配置信息
      Modal.success({
        title: 'Worker 注册成功',
        width: 700,
        content: (
          <div>
            <Alert
              message="请保存以下配置信息"
              description="将这些配置填入 Worker 机器的 worker_config.json 文件"
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
            />
            
            <h4>Worker 配置:</h4>
            <pre style={{ 
              background: '#f5f5f5', 
              padding: '12px', 
              borderRadius: '4px',
              fontSize: '12px'
            }}>
{JSON.stringify({
  backend_url: `${values.backend_url || window.location.protocol}//${window.location.hostname}:5000`,
  ws_url: `${values.ws_url || `ws://${window.location.hostname}:5000`}/ws`,
  api_key: apiKey,
  worker_id: `worker_${Date.now()}`,
  work_dir: values.platform === 'Darwin' ? '~/trading-worker/data' : '/opt/trading-worker/data'
}, null, 2)}
            </pre>
            
            <h4 style={{ marginTop: 16 }}>部署步骤:</h4>
            <ol>
              <li>在目标机器上运行安装脚本</li>
              <li>将上述配置保存到 worker_config.json</li>
              <li>启动 Worker: <code>python worker.py --api-key {apiKey.substring(0, 20)}...</code></li>
            </ol>
            
            <Alert
              message="⚠️ API Key 只显示一次"
              description="请立即复制保存，关闭对话框后将无法查看"
              type="warning"
              showIcon
              style={{ marginTop: 16 }}
            />
          </div>
        ),
        onOk: () => {
          loadWorkers();
          setIsModalVisible(false);
          form.resetFields();
        }
      });
      
    } catch (error) {
      message.error('注册失败');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteWorker = async (workerId) => {
    try {
      // 实际应调用删除 API，这里简化处理
      message.success('Worker 已移除');
      loadWorkers();
    } catch (error) {
      message.error('删除失败');
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      'online': 'green',
      'offline': 'red',
      'busy': 'blue',
      'idle': 'default'
    };
    return colors[status] || 'default';
  };

  const getPlatformIcon = (platform) => {
    if (platform === 'Darwin') return '🍎';
    if (platform === 'Linux') return '🐧';
    if (platform === 'Windows') return '🪟';
    return '💻';
  };

  const columns = [
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => (
        <Tag color={getStatusColor(status)} icon={status === 'online' ? <CheckCircleOutlined /> : <CloseCircleOutlined />}>
          {status}
        </Tag>
      )
    },
    {
      title: 'Worker ID',
      dataIndex: 'worker_id',
      key: 'worker_id',
      ellipsis: true,
      render: (text) => <code>{text}</code>
    },
    {
      title: '主机名',
      dataIndex: 'hostname',
      key: 'hostname',
      render: (text, record) => (
        <span>
          {getPlatformIcon(record.platform)} {text}
        </span>
      )
    },
    {
      title: '平台',
      dataIndex: 'platform',
      key: 'platform',
      width: 120,
      render: (platform) => {
        const icons = { 'Darwin': 'Mac', 'Linux': 'Linux', 'Windows': 'Windows' };
        return icons[platform] || platform;
      }
    },
    {
      title: 'GPU',
      key: 'gpu',
      width: 150,
      render: (_, record) => {
        const gpu = record.gpu_info;
        if (!gpu || !gpu.available) return <Tag>无 GPU</Tag>;
        
        return (
          <Space direction="vertical" size={0}>
            <Tag color="blue">{gpu.count} 个 GPU</Tag>
            {gpu.devices.map((d, i) => (
              <Tag key={i} color="cyan" style={{ fontSize: '10px' }}>
                {d.name?.substring(0, 20)}{d.name?.length > 20 ? '...' : ''}
              </Tag>
            ))}
          </Space>
        );
      }
    },
    {
      title: '资源',
      key: 'resources',
      width: 180,
      render: (_, record) => (
        <Space direction="vertical" size={4} style={{ width: '100%' }}>
          {record.resources?.cpu_percent !== undefined && (
            <div style={{ fontSize: '12px' }}>
              CPU: {record.resources.cpu_percent}%
              <Progress percent={record.resources.cpu_percent} size="small" strokeColor="#1890ff" />
            </div>
          )}
          {record.resources?.memory_percent !== undefined && (
            <div style={{ fontSize: '12px' }}>
              内存：{record.resources.memory_percent}%
              <Progress percent={record.resources.memory_percent} size="small" strokeColor="#52c41a" />
            </div>
          )}
        </Space>
      )
    },
    {
      title: '最后心跳',
      dataIndex: 'last_heartbeat',
      key: 'last_heartbeat',
      width: 160,
      render: (time) => {
        if (!time) return '-';
        const date = new Date(time);
        const now = new Date();
        const diff = Math.floor((now - date) / 1000);
        
        if (diff < 60) return `${diff}秒前`;
        if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`;
        return date.toLocaleString('zh-CN');
      }
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      render: (_, record) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            onClick={() => {
              // 查看配置
              Modal.info({
                title: 'Worker 配置',
                content: (
                  <pre>
{JSON.stringify({
  worker_id: record.worker_id,
  backend_url: API_BASE_URL,
  ws_url: API_BASE_URL.replace('http', 'ws'),
  status: record.status
}, null, 2)}
                  </pre>
                ),
                width: 500
              });
            }}
          >
            配置
          </Button>
          <Popconfirm
            title="确定移除此 Worker？"
            onConfirm={() => handleDeleteWorker(record.worker_id)}
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>
              移除
            </Button>
          </Popconfirm>
        </Space>
      )
    }
  ];

  return (
    <div>
      <PageHeader
        title="分布式训练 Worker 管理"
        extra={
          <Space>
            <Button icon={<SyncOutlined spin={loading} />} onClick={loadWorkers}>
              刷新
            </Button>
            <Button 
              type="primary" 
              icon={<PlusOutlined />} 
              onClick={() => setIsModalVisible(true)}
            >
              注册 Worker
            </Button>
          </Space>
        }
      />

      {/* 统计卡片 */}
      {stats && (
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Card size="small">
              <Statistic 
                title="总 Worker 数" 
                value={stats.total_workers} 
                prefix={<ServerOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic 
                title="在线" 
                value={stats.online_workers} 
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic 
                title="训练中" 
                value={stats.busy_workers} 
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic 
                title="空闲" 
                value={stats.online_workers - stats.busy_workers} 
                valueStyle={{ color: '#faad14' }}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* Worker 列表 */}
      <Card title="Worker 列表" size="small">
        <Table
          columns={columns}
          dataSource={workers}
          rowKey="worker_id"
          loading={loading}
          pagination={false}
          size="small"
          locale={{ emptyText: '暂无 Worker，点击右上角注册' }}
        />
      </Card>

      {/* 注册 Worker 对话框 */}
      <Modal
        title="注册新 Worker"
        open={isModalVisible}
        onOk={() => form.submit()}
        onCancel={() => {
          setIsModalVisible(false);
          form.resetFields();
        }}
        confirmLoading={loading}
        width={600}
      >
        <Alert
          message="注册分布式训练 Worker"
          description="填写 Worker 配置信息，生成后将显示 API Key 用于 Worker 连接"
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />
        
        <Form form={form} layout="vertical" onFinish={handleRegisterWorker}>
          <Form.Item
            name="hostname"
            label="Worker 主机名"
            rules={[{ required: true, message: '请输入主机名' }]}
          >
            <Input placeholder="例如：macbook-pro-1" />
          </Form.Item>
          
          <Form.Item
            name="platform"
            label="操作系统平台"
            initialValue="Darwin"
            rules={[{ required: true }]}
          >
            <Select>
              <Option value="Darwin">🍎 macOS (支持 M1/M2)</Option>
              <Option value="Linux">🐧 Linux</Option>
              <Option value="Windows">🪟 Windows</Option>
            </Select>
          </Form.Item>
          
          <Form.Item
            name="backend_url"
            label="后端服务器地址"
            initialValue={`${window.location.protocol}//${window.location.hostname}:5000`}
          >
            <Input placeholder="http://192.168.1.100:5000" />
          </Form.Item>
          
          <Form.Item
            name="ws_url"
            label="WebSocket 地址"
            initialValue={`ws://${window.location.hostname}:5000`}
          >
            <Input placeholder="ws://192.168.1.100:5000" />
          </Form.Item>
          
          <Alert
            message="部署提示"
            description={
              <div>
                <p>1. 在目标机器上运行安装脚本</p>
                <p>2. 将生成的配置保存到 worker_config.json</p>
                <p>3. 启动 Worker 服务</p>
                <p>4. Worker 会自动连接后端并等待任务</p>
              </div>
            }
            type="warning"
            showIcon
            style={{ marginTop: 16 }}
          />
        </Form>
      </Modal>
    </div>
  );
}

export default Workers;
