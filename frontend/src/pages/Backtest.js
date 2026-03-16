/** 回测管理页面 */

import React, { useState, useEffect } from 'react';
import { Card, Table, Button, Space, Modal, Form, Input, InputNumber, Select, message, Progress, Tag } from 'antd';
import { PlayCircleOutlined, BarChartOutlined, LineChartOutlined, SyncOutlined } from '@ant-design/icons';
import { PageHeader, StatusTag } from '@/components';
import { backtest, models } from '@/services/api';

const { Option } = Select;

function BacktestPage() {
  const [loading, setLoading] = useState(false);
  const [isExecuteVisible, setIsExecuteVisible] = useState(false);
  const [isEvaluateVisible, setIsEvaluateVisible] = useState(false);
  const [executeForm] = Form.useForm();
  const [evaluateForm] = Form.useForm();
  const [modelsList, setModelsList] = useState([]);
  const [currentTask, setCurrentTask] = useState(null);
  const [result, setResult] = useState(null);

  useEffect(() => {
    loadModels();
  }, []);

  const loadModels = async () => {
    try {
      const res = await models.list();
      setModelsList(res.data.data || []);
    } catch (error) {
      console.error('加载模型列表失败:', error);
    }
  };

  const handleExecute = async (values) => {
    setLoading(true);
    try {
      const res = await backtest.execute(
        values.model_id,
        values.stock_code,
        values.env_name,
        values.initial_cash
      );
      message.success('回测已启动');
      setIsExecuteVisible(false);
      setCurrentTask(res.data.data);
      
      // 轮询任务状态
      pollTaskStatus(res.data.data.task_id);
    } catch (error) {
      message.error('启动回测失败');
    } finally {
      setLoading(false);
    }
  };

  const handleEvaluate = async (values) => {
    setLoading(true);
    try {
      const res = await backtest.evaluate(
        values.model_id,
        [values.stock_code],
        [values.env_name]
      );
      message.success('评估完成');
      setIsEvaluateVisible(false);
      setResult(res.data.data);
    } catch (error) {
      message.error('评估失败');
    } finally {
      setLoading(false);
    }
  };

  const pollTaskStatus = async (taskId) => {
    const poll = async () => {
      try {
        const res = await backtest.task(taskId);
        const task = res.data.data;
        setCurrentTask(task);
        
        if (task.status === 'completed' || task.status === 'failed') {
          setResult(task.result);
          setLoading(false);
        } else {
          setTimeout(poll, 2000);
        }
      } catch (error) {
        console.error('查询任务状态失败:', error);
        setLoading(false);
      }
    };
    poll();
  };

  const executeColumns = [
    {
      title: '指标',
      dataIndex: 'label',
      key: 'label',
      width: 150,
    },
    {
      title: '值',
      dataIndex: 'value',
      key: 'value',
      render: (value, record) => {
        if (typeof value === 'number') {
          if (record.key.includes('return') || record.key.includes('drawdown')) {
            return `${(value * 100).toFixed(2)}%`;
          }
          if (record.key.includes('sharpe')) {
            return value.toFixed(2);
          }
        }
        return value;
      },
    },
  ];

  const getResultData = () => {
    if (!result) return [];
    return [
      { key: 'total_return', label: '总收益率', value: result.total_return },
      { key: 'annual_return', label: '年化收益', value: result.annual_return },
      { key: 'sharpe_ratio', label: '夏普比率', value: result.sharpe_ratio },
      { key: 'max_drawdown', label: '最大回撤', value: result.max_drawdown },
      { key: 'win_rate', label: '胜率', value: result.win_rate },
      { key: 'total_trades', label: '交易次数', value: result.total_trades },
      { key: 'final_value', label: '最终价值', value: `¥${result.final_value?.toFixed(2)}` },
    ];
  };

  return (
    <div>
      <PageHeader
        title="回测管理"
        extra={
          <Space>
            <Button 
              type="primary" 
              icon={<PlayCircleOutlined />} 
              onClick={() => setIsExecuteVisible(true)}
            >
              执行回测
            </Button>
            <Button 
              icon={<BarChartOutlined />} 
              onClick={() => setIsEvaluateVisible(true)}
            >
              批量评估
            </Button>
          </Space>
        }
      />

      {/* 当前任务状态 */}
      {currentTask && (
        <Card title="当前任务" size="small" style={{ marginBottom: 16 }}>
          <Space size="large">
            <div>
              <div style={{ color: '#666' }}>任务 ID</div>
              <div>{currentTask.task_id?.substring(0, 20)}...</div>
            </div>
            <div>
              <div style={{ color: '#666' }}>状态</div>
              <StatusTag status={currentTask.status} />
            </div>
            {currentTask.status === 'running' && (
              <div style={{ width: 200 }}>
                <Progress percent={currentTask.result?.progress || 0} />
              </div>
            )}
          </Space>
        </Card>
      )}

      {/* 回测结果 */}
      {result && (
        <Card title="回测结果" size="small">
          <Table
            columns={executeColumns}
            dataSource={getResultData()}
            rowKey="key"
            pagination={false}
            size="small"
          />
        </Card>
      )}

      {/* 执行回测对话框 */}
      <Modal
        title="执行回测"
        open={isExecuteVisible}
        onOk={() => executeForm.submit()}
        onCancel={() => {
          setIsExecuteVisible(false);
          executeForm.resetFields();
        }}
        confirmLoading={loading}
      >
        <Form form={executeForm} layout="vertical" onFinish={handleExecute}>
          <Form.Item
            name="model_id"
            label="模型 ID"
            rules={[{ required: true, message: '请选择模型' }]}
          >
            <Select placeholder="选择模型">
              {modelsList.map(m => (
                <Option key={m.id} value={m.id}>
                  {m.name} ({m.strategy})
                </Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item
            name="stock_code"
            label="股票代码"
            initialValue="000001.SZ"
            rules={[{ required: true, message: '请输入股票代码' }]}
          >
            <Input placeholder="例如：000001.SZ" />
          </Form.Item>
          <Form.Item
            name="env_name"
            label="环境名称"
            initialValue="momentum"
            rules={[{ required: true, message: '请选择环境' }]}
          >
            <Select>
              <Option value="momentum">动量策略</Option>
              <Option value="mean_reversion">均值回归</Option>
              <Option value="breakout">突破策略</Option>
            </Select>
          </Form.Item>
          <Form.Item
            name="initial_cash"
            label="初始资金"
            initialValue={1000000}
          >
            <InputNumber style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>

      {/* 批量评估对话框 */}
      <Modal
        title="批量评估模型"
        open={isEvaluateVisible}
        onOk={() => evaluateForm.submit()}
        onCancel={() => {
          setIsEvaluateVisible(false);
          evaluateForm.resetFields();
        }}
        confirmLoading={loading}
      >
        <Form form={evaluateForm} layout="vertical" onFinish={handleEvaluate}>
          <Form.Item
            name="model_id"
            label="模型 ID"
            rules={[{ required: true, message: '请选择模型' }]}
          >
            <Select placeholder="选择模型">
              {modelsList.map(m => (
                <Option key={m.id} value={m.id}>
                  {m.name} ({m.strategy})
                </Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item
            name="stock_code"
            label="股票代码"
            initialValue="000001.SZ"
          >
            <Input placeholder="例如：000001.SZ" />
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
        </Form>
      </Modal>
    </div>
  );
}

export default BacktestPage;
