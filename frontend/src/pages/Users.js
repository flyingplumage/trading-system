/** 用户管理页面 */

import React, { useState, useEffect } from 'react';
import { Card, Table, Button, Space, Modal, Form, Input, Select, Tag, Switch, message, Popconfirm } from 'antd';
import { UserAddOutlined, EditOutlined, DeleteOutlined, KeyOutlined, SyncOutlined } from '@ant-design/icons';
import { PageHeader } from '@/components';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const { Option } = Select;

function Users() {
  const [loading, setLoading] = useState(false);
  const [users, setUsers] = useState([]);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [isApiModalVisible, setIsApiModalVisible] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [apiKeys, setApiKeys] = useState([]);
  const [form] = Form.useForm();
  const [apiForm] = Form.useForm();

  useEffect(() => {
    loadUsers();
    loadApiKeys();
  }, []);

  const getHeaders = () => {
    const token = localStorage.getItem('access_token');
    return { 'Authorization': `Bearer ${token}` };
  };

  const loadUsers = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE_URL}/api/auth/users`, { headers: getHeaders() });
      setUsers(res.data.data || []);
    } catch (error) {
      console.error('加载用户失败:', error);
      if (error.response?.status === 403) {
        message.error('需要管理员权限');
      }
    } finally {
      setLoading(false);
    }
  };

  const loadApiKeys = async () => {
    try {
      const res = await axios.get(`${API_BASE_URL}/api/auth/api-key/list`, { headers: getHeaders() });
      setApiKeys(res.data.data || []);
    } catch (error) {
      console.error('加载 API Key 失败:', error);
    }
  };

  const handleCreateUser = async (values) => {
    try {
      await axios.post(`${API_BASE_URL}/api/auth/register`, values, { headers: getHeaders() });
      message.success('用户创建成功');
      setIsModalVisible(false);
      form.resetFields();
      loadUsers();
    } catch (error) {
      message.error('创建失败：' + (error.response?.data?.detail || '未知错误'));
    }
  };

  const handleUpdateUser = async (username, values) => {
    try {
      await axios.put(`${API_BASE_URL}/api/auth/users/${username}`, values, { headers: getHeaders() });
      message.success('用户更新成功');
      setIsModalVisible(false);
      form.resetFields();
      loadUsers();
    } catch (error) {
      message.error('更新失败');
    }
  };

  const handleDeleteUser = async (username) => {
    try {
      await axios.delete(`${API_BASE_URL}/api/auth/users/${username}`, { headers: getHeaders() });
      message.success('用户已删除');
      loadUsers();
    } catch (error) {
      message.error('删除失败');
    }
  };

  const handleCreateApiKey = async (values) => {
    try {
      const res = await axios.post(`${API_BASE_URL}/api/auth/api-key/create`, values, { headers: getHeaders() });
      message.success(`API Key 已创建：${res.data.data.api_key}`);
      Modal.success({
        title: 'API Key 已创建',
        content: (
          <div>
            <p><strong>密钥：</strong><code style={{ background: '#f5f5f5', padding: '4px 8px' }}>{res.data.data.api_key}</code></p>
            <p style={{ color: '#ff4d4f' }}>⚠️ 密钥只显示一次，请立即复制保存！</p>
            <p><strong>名称：</strong>{res.data.data.name}</p>
            <p><strong>角色：</strong>{res.data.data.role}</p>
            <p><strong>过期时间：</strong>{res.data.data.expires_days} 天</p>
          </div>
        ),
        width: 500,
      });
      setIsApiModalVisible(false);
      apiForm.resetFields();
      loadApiKeys();
    } catch (error) {
      message.error('创建失败：' + (error.response?.data?.detail || '未知错误'));
    }
  };

  const handleRevokeApiKey = async (key) => {
    try {
      await axios.post(`${API_BASE_URL}/api/auth/api-key/revoke/${encodeURIComponent(key)}`, null, { headers: getHeaders() });
      message.success('API Key 已撤销');
      loadApiKeys();
    } catch (error) {
      message.error('撤销失败');
    }
  };

  const getRoleColor = (role) => {
    const colors = {
      admin: 'red',
      developer: 'blue',
      user: 'green',
      bot: 'purple'
    };
    return colors[role] || 'default';
  };

  const columns = [
    {
      title: '用户 ID',
      dataIndex: 'user_id',
      key: 'user_id',
      ellipsis: true,
    },
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
    },
    {
      title: '角色',
      dataIndex: 'role',
      key: 'role',
      render: (role) => <Tag color={getRoleColor(role)}>{role}</Tag>,
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      key: 'email',
      ellipsis: true,
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => date ? date.substring(0, 16).replace('T', ' ') : '-',
    },
    {
      title: '最后登录',
      dataIndex: 'last_login',
      key: 'last_login',
      render: (date) => date ? date.substring(0, 16).replace('T', ' ') : '从未',
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (active) => active ? <Tag color="green">激活</Tag> : <Tag color="red">停用</Tag>,
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<KeyOutlined />}
            onClick={() => {
              setCurrentUser(record);
              apiForm.setFieldsValue({ username: record.username });
              setIsApiModalVisible(true);
            }}
          >
            API Key
          </Button>
          {record.username !== 'admin' && (
            <Popconfirm
              title="确定删除此用户？"
              onConfirm={() => handleDeleteUser(record.username)}
            >
              <Button type="link" size="small" danger icon={<DeleteOutlined />}>
                删除
              </Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  const apiKeyColumns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
    },
    {
      title: '角色',
      dataIndex: 'role',
      key: 'role',
      render: (role) => <Tag color={getRoleColor(role)}>{role}</Tag>,
    },
    {
      title: '密钥 (前缀)',
      dataIndex: 'key_prefix',
      key: 'key_prefix',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => date ? date.substring(0, 16).replace('T', ' ') : '-',
    },
    {
      title: '过期时间',
      dataIndex: 'expires_at',
      key: 'expires_at',
      render: (date) => date ? date.substring(0, 16).replace('T', ' ') : '-',
    },
    {
      title: '使用次数',
      dataIndex: 'usage_count',
      key: 'usage_count',
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (active) => active ? <Tag color="green">激活</Tag> : <Tag color="red">停用</Tag>,
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Popconfirm
          title="确定撤销此 API Key？"
          onConfirm={() => handleRevokeApiKey(record.key_prefix.replace('...', ''))}
        >
          <Button type="link" size="small" danger>
            撤销
          </Button>
        </Popconfirm>
      ),
    },
  ];

  return (
    <div>
      <PageHeader
        title="用户管理"
        extra={
          <Space>
            <Button icon={<SyncOutlined spin={loading} />} onClick={loadUsers}>
              刷新
            </Button>
            <Button type="primary" icon={<UserAddOutlined />} onClick={() => setIsModalVisible(true)}>
              创建用户
            </Button>
            <Button icon={<KeyOutlined />} onClick={() => setIsApiModalVisible(true)}>
              创建 API Key
            </Button>
          </Space>
        }
      />

      {/* 用户列表 */}
      <Card title="用户列表" size="small" style={{ marginBottom: 16 }}>
        <Table
          columns={columns}
          dataSource={users}
          rowKey="username"
          loading={loading}
          pagination={false}
          size="small"
        />
      </Card>

      {/* API Key 列表 */}
      <Card title="API Key 列表" size="small">
        <Table
          columns={apiKeyColumns}
          dataSource={apiKeys}
          rowKey="key_prefix"
          pagination={false}
          size="small"
          locale={{ emptyText: '暂无 API Key' }}
        />
      </Card>

      {/* 创建用户对话框 */}
      <Modal
        title="创建用户"
        open={isModalVisible}
        onOk={() => form.submit()}
        onCancel={() => {
          setIsModalVisible(false);
          form.resetFields();
        }}
      >
        <Form form={form} layout="vertical" onFinish={handleCreateUser}>
          <Form.Item
            name="username"
            label="用户名"
            rules={[
              { required: true, message: '请输入用户名' },
              { min: 3, message: '至少 3 个字符' }
            ]}
          >
            <Input placeholder="用户名" />
          </Form.Item>
          <Form.Item
            name="password"
            label="密码"
            rules={[
              { required: true, message: '请输入密码' },
              { min: 6, message: '至少 6 个字符' }
            ]}
          >
            <Input.Password placeholder="密码" />
          </Form.Item>
          <Form.Item
            name="email"
            label="邮箱"
            rules={[{ type: 'email', message: '请输入有效的邮箱' }]}
          >
            <Input placeholder="邮箱 (可选)" />
          </Form.Item>
          <Form.Item
            name="role"
            label="角色"
            initialValue="user"
            rules={[{ required: true }]}
          >
            <Select>
              <Option value="user">普通用户 (只读)</Option>
              <Option value="developer">开发者 (读写)</Option>
              <Option value="admin">管理员</Option>
              <Option value="bot">机器人 (智能体)</Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      {/* 创建 API Key 对话框 */}
      <Modal
        title="创建 API Key"
        open={isApiModalVisible}
        onOk={() => apiForm.submit()}
        onCancel={() => {
          setIsApiModalVisible(false);
          apiForm.resetFields();
        }}
      >
        <Form form={apiForm} layout="vertical" onFinish={handleCreateApiKey}>
          <Form.Item
            name="name"
            label="名称"
            rules={[{ required: true, message: '请输入名称' }]}
          >
            <Input placeholder="例如：OpenClaw-Lyra" />
          </Form.Item>
          <Form.Item
            name="role"
            label="角色"
            initialValue="bot"
            rules={[{ required: true }]}
          >
            <Select>
              <Option value="bot">机器人 (智能体推荐)</Option>
              <Option value="user">普通用户</Option>
              <Option value="developer">开发者</Option>
            </Select>
          </Form.Item>
          <Form.Item
            name="expires_days"
            label="有效期 (天)"
            initialValue={365}
            rules={[{ required: true }]}
          >
            <Input type="number" min={1} max={3650} />
          </Form.Item>
          <Form.Item>
            <p style={{ color: '#ff4d4f', fontSize: 12 }}>
              ⚠️ API Key 创建后只显示一次，请立即复制保存！
            </p>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

export default Users;
