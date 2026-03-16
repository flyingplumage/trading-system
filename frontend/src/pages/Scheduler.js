/** 调度器监控页面 */

import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Progress, Table, Tag, Space, Button, Descriptions, Alert } from 'antd';
import { 
  DashboardOutlined, 
  LaptopOutlined, 
  ReloadOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined
} from '@ant-design/icons';
import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5000';

function Scheduler() {
  const [loading, setLoading] = useState(false);
  const [schedulerStatus, setSchedulerStatus] = useState(null);
  const [recommendedConfig, setRecommendedConfig] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000); // 30 秒刷新
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      // 获取调度器状态
      const statusRes = await axios.get(`${API_BASE}/api/scheduler/status`);
      setSchedulerStatus(statusRes.data.data);

      // 获取推荐配置
      const configRes = await axios.get(`${API_BASE}/api/scheduler/config`);
      setRecommendedConfig(configRes.data.data);
    } catch (err) {
      console.error('加载调度器数据失败:', err);
      setError('加载调度器数据失败，请确保后端服务运行正常');
    } finally {
      setLoading(false);
    }
  };

  if (error) {
    return (
      <div>
        <h2>调度器监控</h2>
        <Alert
          message="错误"
          description={error}
          type="error"
          showIcon
          action={
            <Button size="small" onClick={loadData}>重试</Button>
          }
        />
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <h2>调度器监控</h2>
        <Button icon={<ReloadOutlined />} onClick={loadData} loading={loading}>
          刷新
        </Button>
      </div>

      {schedulerStatus && (
        <>
          {/* 资源信息 */}
          <Card title="系统资源" style={{ marginBottom: 16 }}>
            <Row gutter={16}>
              <Col span={6}>
                <Statistic
                  title="CPU 核心数"
                  value={schedulerStatus.resource?.cpu_cores || 0}
                  prefix={<DashboardOutlined />}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="CPU 使用率"
                  value={schedulerStatus.resource?.cpu_usage_percent || 0}
                  precision={1}
                  suffix="%"
                  valueStyle={{ 
                    color: (schedulerStatus.resource?.cpu_usage_percent || 0) > 80 ? '#ff4d4f' : '#3f8600'
                  }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="内存总量"
                  value={(schedulerStatus.resource?.memory_total_gb || 0).toFixed(1)}
                  prefix={<LaptopOutlined />}
                  suffix="GB"
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="内存使用率"
                  value={schedulerStatus.resource?.memory_usage_percent || 0}
                  precision={1}
                  suffix="%"
                  valueStyle={{ 
                    color: (schedulerStatus.resource?.memory_usage_percent || 0) > 80 ? '#ff4d4f' : '#3f8600'
                  }}
                />
              </Col>
            </Row>

            {schedulerStatus.resource?.gpu_available && (
              <Row gutter={16} style={{ marginTop: 16 }}>
                <Col span={6}>
                  <Statistic
                    title="GPU 可用"
                    value="是"
                    prefix={<CheckCircleOutlined />}
                    valueStyle={{ color: '#52c41a' }}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="GPU 显存"
                    value={schedulerStatus.resource?.gpu_memory_gb || 0}
                    precision={1}
                    suffix="GB"
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="GPU 使用率"
                    value={schedulerStatus.resource?.gpu_usage_percent || 0}
                    precision={1}
                    suffix="%"
                  />
                </Col>
              </Row>
            )}
          </Card>

          {/* 推荐配置 */}
          {recommendedConfig && (
            <Card title="推荐训练配置" style={{ marginBottom: 16 }}>
              <Descriptions column={3} bordered>
                <Descriptions.Item label="并行环境数">
                  {recommendedConfig.config?.n_envs || '-'}
                </Descriptions.Item>
                <Descriptions.Item label="学习率">
                  {recommendedConfig.config?.learning_rate || '-'}
                </Descriptions.Item>
                <Descriptions.Item label="Batch Size">
                  {recommendedConfig.config?.batch_size || '-'}
                </Descriptions.Item>
                <Descriptions.Item label="N Steps">
                  {recommendedConfig.config?.n_steps || '-'}
                </Descriptions.Item>
                <Descriptions.Item label="N Epochs">
                  {recommendedConfig.config?.n_epochs || '-'}
                </Descriptions.Item>
                <Descriptions.Item label="使用 GPU">
                  {recommendedConfig.config?.use_gpu ? (
                    <Tag color="green">是</Tag>
                  ) : (
                    <Tag>否</Tag>
                  )}
                </Descriptions.Item>
              </Descriptions>
              
              {recommendedConfig.reason && (
                <Alert
                  message="推荐说明"
                  description={recommendedConfig.reason}
                  type="info"
                  showIcon
                  style={{ marginTop: 16 }}
                />
              )}
            </Card>
          )}
        </>
      )}

      {!schedulerStatus && (
        <Alert
          message="调度器不可用"
          description="请确保 qframe.scheduler 模块已安装"
          type="warning"
          showIcon
        />
      )}
    </div>
  );
}

export default Scheduler;
