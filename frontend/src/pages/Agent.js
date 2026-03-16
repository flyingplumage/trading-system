/** OpenClaw 智能体操作页面 */

import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Button, Form, Input, InputNumber, Space, message, Descriptions } from 'antd';
import { RobotOutlined, PlayCircleOutlined } from '@ant-design/icons';
import { agent, training } from '../services/api';

function Agent() {
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState(null);
  const [form] = Form.useForm();

  useEffect(() => {
    loadStatus();
    const interval = setInterval(loadStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadStatus = async () => {
    setLoading(true);
    try {
      const res = await agent.status();
      setStatus(res.data.data);
    } catch (error) {
      message.error('加载状态失败');
    } finally {
      setLoading(false);
    }
  };

  const handleTrain = async (values) => {
    try {
      const res = await agent.train(values.strategy, values.steps);
      message.success(`训练已启动！任务 ID: ${res.data.data.task_id}`);
      form.resetFields();
      loadStatus();
    } catch (error) {
      message.error('启动训练失败');
    }
  };

  return (
    <div>
      <h2><RobotOutlined /> OpenClaw 智能体操作台</h2>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card loading={loading}>
            <Statistic
              title="实验总数"
              value={status?.experiments || 0}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card loading={loading}>
            <Statistic
              title="已注册模型"
              value={status?.models || 0}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card loading={loading}>
            <Statistic
              title="待训练任务"
              value={status?.pending_tasks || 0}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card loading={loading}>
            <Statistic
              title="系统状态"
              value={status?.status || 'unknown'}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={12}>
          <Card title="快速启动训练" icon={<PlayCircleOutlined />}>
            <Form form={form} layout="vertical" onFinish={handleTrain}>
              <Form.Item
                name="strategy"
                label="策略路径"
                rules={[{ required: true, message: '请输入策略路径' }]}
              >
                <Input placeholder="例如：neo/v4_rsi_vol" />
              </Form.Item>
              <Form.Item
                name="steps"
                label="训练步数"
                initialValue={100000}
                rules={[{ required: true }]}
              >
                <InputNumber 
                  min={10000} 
                  max={1000000} 
                  step={10000}
                  style={{ width: '100%' }}
                />
              </Form.Item>
              <Form.Item>
                <Button type="primary" htmlType="submit" icon={<PlayCircleOutlined />}>
                  启动训练
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </Col>

        <Col span={12}>
          <Card title="系统信息">
            <Descriptions column={1}>
              <Descriptions.Item label="API 地址">
                http://localhost:5000
              </Descriptions.Item>
              <Descriptions.Item label="文档地址">
                <a href="http://localhost:5000/docs" target="_blank" rel="noreferrer">
                  /docs
                </a>
              </Descriptions.Item>
              <Descriptions.Item label="智能体 API">
                GET /api/agent/status
                <br />
                POST /api/agent/train
              </Descriptions.Item>
            </Descriptions>
          </Card>
        </Col>
      </Row>
    </div>
  );
}

export default Agent;
