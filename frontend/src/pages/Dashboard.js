/** Dashboard 首页（使用业务组件重构） */

import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Table, Space } from 'antd';
import { 
  ExperimentOutlined, 
  DatabaseOutlined, 
  CloudUploadOutlined,
  CheckCircleOutlined
} from '@ant-design/icons';
import { StatCard, StatusTag, DataTable, PageHeader, MetricPanel, ChartCard } from '@/components';
import { experiments, models, agent } from '@/services/api';

function Dashboard() {
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState({
    experiments: 0,
    models: 0,
    tasks: 0,
  });
  const [recentExps, setRecentExps] = useState([]);
  const [bestModels, setBestModels] = useState([]);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const agentStatus = await agent.status();
      setStats({
        experiments: agentStatus.data.data.experiments,
        models: agentStatus.data.data.models,
        tasks: agentStatus.data.data.pending_tasks,
      });

      const expsRes = await experiments.list(null, 5);
      setRecentExps(expsRes.data.data || []);

      const modelsRes = await models.best(5);
      setBestModels(modelsRes.data.data || []);
    } catch (error) {
      console.error('加载数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const expColumns = [
    {
      title: '实验 ID',
      dataIndex: 'id',
      key: 'id',
      ellipsis: true,
    },
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '策略',
      dataIndex: 'strategy',
      key: 'strategy',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => <StatusTag status={status} />,
    },
    {
      title: '收益',
      dataIndex: ['metrics', 'total_return'],
      key: 'total_return',
      render: (value) => value ? `${(value * 100).toFixed(1)}%` : '-',
    },
    {
      title: '日期',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => date ? date.substring(0, 10) : '-',
    },
  ];

  const modelColumns = [
    {
      title: '模型 ID',
      dataIndex: 'id',
      key: 'id',
      ellipsis: true,
    },
    {
      title: '策略',
      dataIndex: 'strategy',
      key: 'strategy',
    },
    {
      title: '版本',
      dataIndex: 'version',
      key: 'version',
      render: (v) => `v${v}`,
    },
    {
      title: '收益',
      dataIndex: ['metrics', 'total_return'],
      key: 'total_return',
      render: (value) => value ? `${(value * 100).toFixed(1)}%` : '-',
    },
    {
      title: '夏普',
      dataIndex: ['metrics', 'sharpe_ratio'],
      key: 'sharpe_ratio',
      render: (value) => value ? value.toFixed(2) : '-',
    },
  ];

  const metricData = [
    { label: '总实验数', value: stats.experiments, prefix: <ExperimentOutlined />, color: '#1890ff' },
    { label: '已注册模型', value: stats.models, prefix: <DatabaseOutlined />, color: '#52c41a' },
    { label: '待训练任务', value: stats.tasks, prefix: <CloudUploadOutlined />, color: '#faad14' },
    { label: '系统状态', value: '运行中', prefix: <CheckCircleOutlined />, color: '#52c41a' },
  ];

  return (
    <div>
      <PageHeader title="Dashboard" onRefresh={loadData} loading={loading} />
      
      {/* 统计指标 */}
      <MetricPanel title="" metrics={metricData} loading={loading} columns={4} />

      {/* 最近实验和最佳模型 */}
      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col span={12}>
          <Card title="最近实验" size="small">
            <DataTable
              columns={expColumns}
              dataSource={recentExps}
              rowKey="id"
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card title="最佳模型" size="small">
            <DataTable
              columns={modelColumns}
              dataSource={bestModels}
              rowKey="id"
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
}

export default Dashboard;
