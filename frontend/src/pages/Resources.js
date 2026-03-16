import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Progress, Statistic, Spin, Alert, Badge, Space, Button, RefreshCw } from 'antd';
import {
  DashboardOutlined,
  HddOutlined,
  UsbOutlined,
  GoldOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined
} from '@ant-design/icons';
import { Line, Bar } from '@ant-design/charts';

const API_BASE = '';

/**
 * 资源监控页面
 * - CPU 使用率（实时图表，10 秒刷新）
 * - 内存使用率（实时图表）
 * - GPU 状态卡片（型号/显存/利用率）
 * - 磁盘空间进度条
 */
const Resources = () => {
  // 系统资源状态
  const [systemData, setSystemData] = useState(null);
  const [gpuData, setGpuData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [history, setHistory] = useState([]);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval] = useState(10000); // 10 秒刷新

  // 获取系统资源
  const fetchSystemResources = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/api/resources/system`);
      const result = await response.json();
      
      if (result.success) {
        setSystemData(result.data);
        setError(null);
        
        // 更新历史数据
        setHistory(prev => {
          const newHistory = [...prev, {
            time: new Date(result.data.timestamp).toLocaleTimeString(),
            cpu: result.data.cpu.usage_percent,
            memory: result.data.memory.usage_percent
          }];
          // 保留最近 60 条记录（10 分钟）
          return newHistory.slice(-60);
        });
      } else {
        setError('获取系统资源失败');
      }
    } catch (err) {
      setError(`请求失败：${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // 获取 GPU 资源
  const fetchGpuResources = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/resources/gpu`);
      const result = await response.json();
      
      if (result.success) {
        setGpuData(result.data);
      }
    } catch (err) {
      console.error('获取 GPU 资源失败:', err);
    }
  };

  // 初始加载
  useEffect(() => {
    fetchSystemResources();
    fetchGpuResources();
  }, []);

  // 自动刷新
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchSystemResources();
      fetchGpuResources();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh]);

  // 手动刷新
  const handleRefresh = () => {
    fetchSystemResources();
    fetchGpuResources();
  };

  // CPU 图表配置
  const cpuChartConfig = {
    data: history,
    height: 200,
    xField: 'time',
    yField: 'cpu',
    label: {
      style: {
        fill: '#aaa',
      },
    },
    point: {
      size: 3,
      shape: 'circle',
    },
    color: '#1890ff',
    animation: {
      appear: {
        animation: 'path-in',
        duration: 1000,
      },
    },
    xAxis: {
      label: {
        autoRotate: true,
        autoHide: false,
      },
    },
    yAxis: {
      min: 0,
      max: 100,
    },
  };

  // 内存图表配置
  const memoryChartConfig = {
    ...cpuChartConfig,
    yField: 'memory',
    color: '#52c41a',
  };

  // 获取使用率颜色
  const getUsageColor = (percent) => {
    if (percent < 60) return '#52c41a'; // 绿色
    if (percent < 80) return '#faad14'; // 橙色
    return '#f5222d'; // 红色
  };

  return (
    <div style={{ padding: '24px' }}>
      {/* 页面标题 */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: '24px'
      }}>
        <h1 style={{ margin: 0 }}>资源监控</h1>
        <Space>
          <Button
            icon={<ReloadOutlined spin={loading} />}
            onClick={handleRefresh}
          >
            刷新
          </Button>
          <Button
            type={autoRefresh ? 'primary' : 'default'}
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            自动刷新：{autoRefresh ? '开' : '关'}
          </Button>
        </Space>
      </div>

      {/* 错误提示 */}
      {error && (
        <Alert
          message="错误"
          description={error}
          type="error"
          showIcon
          style={{ marginBottom: '24px' }}
          closable
          onClose={() => setError(null)}
        />
      )}

      {/* 加载中 */}
      {loading && !systemData && (
        <div style={{ textAlign: 'center', padding: '48px' }}>
          <Spin size="large" tip="加载资源数据..." />
        </div>
      )}

      {/* 资源卡片 */}
      {systemData && (
        <>
          {/* 第一行：CPU 和内存统计 */}
          <Row gutter={[16, 16]} style={{ marginBottom: '16px' }}>
            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="CPU 使用率"
                  value={systemData.cpu.usage_percent}
                  precision={1}
                  suffix="%"
                  valueStyle={{ 
                    color: getUsageColor(systemData.cpu.usage_percent),
                    fontSize: '32px'
                  }}
                  prefix={<DashboardOutlined />}
                />
                <div style={{ marginTop: '8px', fontSize: '12px', color: '#666' }}>
                  <div>核心数：{systemData.cpu.count}</div>
                  <div>频率：{(systemData.cpu.frequency_mhz / 1000).toFixed(2)} GHz</div>
                </div>
              </Card>
            </Col>

            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="内存使用率"
                  value={systemData.memory.usage_percent}
                  precision={1}
                  suffix="%"
                  valueStyle={{ 
                    color: getUsageColor(systemData.memory.usage_percent),
                    fontSize: '32px'
                  }}
                  prefix={<HddOutlined />}
                />
                <div style={{ marginTop: '8px', fontSize: '12px', color: '#666' }}>
                  <div>
                    已用：{systemData.memory.used_gb.toFixed(2)} GB / 
                    总计：{systemData.memory.total_gb.toFixed(2)} GB
                  </div>
                  <div>可用：{systemData.memory.available_gb.toFixed(2)} GB</div>
                </div>
              </Card>
            </Col>

            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="磁盘使用率"
                  value={systemData.disk.usage_percent}
                  precision={1}
                  suffix="%"
                  valueStyle={{ 
                    color: getUsageColor(systemData.disk.usage_percent),
                    fontSize: '32px'
                  }}
                  prefix={<UsbOutlined />}
                />
                <div style={{ marginTop: '8px', fontSize: '12px', color: '#666' }}>
                  <div>
                    已用：{systemData.disk.used_gb.toFixed(2)} GB / 
                    总计：{systemData.disk.total_gb.toFixed(2)} GB
                  </div>
                  <div>可用：{systemData.disk.free_gb.toFixed(2)} GB</div>
                </div>
              </Card>
            </Col>

            <Col xs={24} sm={12} md={6}>
              <Card>
                <Statistic
                  title="GPU 状态"
                  value={gpuData?.available ? '可用' : '不可用'}
                  valueStyle={{ 
                    color: gpuData?.available ? '#52c41a' : '#999',
                    fontSize: '32px'
                  }}
                  prefix={gpuData?.available ? <CheckCircleOutlined /> : <CloseCircleOutlined />}
                />
                <div style={{ marginTop: '8px', fontSize: '12px', color: '#666' }}>
                  <div>GPU 数量：{gpuData?.count || 0}</div>
                  {gpuData?.gpus?.[0] && (
                    <div>型号：{gpuData.gpus[0].name}</div>
                  )}
                </div>
              </Card>
            </Col>
          </Row>

          {/* 第二行：磁盘进度条 */}
          <Row gutter={[16, 16]} style={{ marginBottom: '16px' }}>
            <Col xs={24} md={12}>
              <Card title="磁盘空间">
                <div style={{ marginBottom: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <span>已用空间</span>
                    <span>{systemData.disk.usage_percent.toFixed(1)}%</span>
                  </div>
                  <Progress
                    percent={systemData.disk.usage_percent}
                    strokeColor={getUsageColor(systemData.disk.usage_percent)}
                    format={(percent) => `${percent.toFixed(1)}%`}
                  />
                </div>
                <div style={{ marginBottom: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <span>可用空间</span>
                    <span>{systemData.disk.free_gb.toFixed(2)} GB</span>
                  </div>
                  <Progress
                    percent={(systemData.disk.free_gb / systemData.disk.total_gb) * 100}
                    strokeColor="#52c41a"
                    format={(percent) => `${percent.toFixed(1)}%`}
                  />
                </div>
              </Card>
            </Col>

            <Col xs={24} md={12}>
              <Card title="内存详情">
                <div style={{ marginBottom: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <span>已用内存</span>
                    <span>{systemData.memory.used_gb.toFixed(2)} GB</span>
                  </div>
                  <Progress
                    percent={systemData.memory.usage_percent}
                    strokeColor={getUsageColor(systemData.memory.usage_percent)}
                    format={(percent) => `${percent.toFixed(1)}%`}
                  />
                </div>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <span>可用内存</span>
                    <span>{systemData.memory.available_gb.toFixed(2)} GB</span>
                  </div>
                  <Progress
                    percent={(systemData.memory.available_gb / systemData.memory.total_gb) * 100}
                    strokeColor="#52c41a"
                    format={(percent) => `${percent.toFixed(1)}%`}
                  />
                </div>
              </Card>
            </Col>
          </Row>

          {/* 第三行：GPU 卡片 */}
          {gpuData?.available && gpuData.gpus && gpuData.gpus.length > 0 && (
            <Row gutter={[16, 16]} style={{ marginBottom: '16px' }}>
              <Col xs={24}>
                <Card 
                  title={<Space><GoldOutlined />GPU 详情</Space>}
                  extra={<Badge status="processing" text="运行中" />}
                >
                  <Row gutter={[16, 16]}>
                    {gpuData.gpus.map((gpu, index) => (
                      <Col xs={24} sm={12} md={8} key={gpu.id}>
                        <Card 
                          size="small" 
                          title={`GPU ${gpu.id}`}
                          style={{ height: '100%' }}
                        >
                          <div style={{ marginBottom: '12px' }}>
                            <div style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: '4px' }}>
                              {gpu.name}
                            </div>
                            <div style={{ fontSize: '12px', color: '#666' }}>
                              计算能力：{gpu.compute_capability || 'N/A'}
                            </div>
                          </div>
                          
                          {gpu.utilization_percent !== undefined && (
                            <div style={{ marginBottom: '12px' }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                <span>利用率</span>
                                <span>{gpu.utilization_percent.toFixed(1)}%</span>
                              </div>
                              <Progress
                                percent={gpu.utilization_percent}
                                strokeColor={getUsageColor(gpu.utilization_percent)}
                                size="small"
                              />
                            </div>
                          )}
                          
                          <div style={{ marginBottom: '12px' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                              <span>显存使用</span>
                              <span>
                                {gpu.memory_used_gb?.toFixed(2) || gpu.memory_allocated_gb?.toFixed(2) || '0'} GB / 
                                {gpu.memory_total_gb.toFixed(2)} GB
                              </span>
                            </div>
                            <Progress
                              percent={gpu.memory_used_percent || (gpu.memory_allocated_gb / gpu.memory_total_gb * 100) || 0}
                              strokeColor={getUsageColor(gpu.memory_used_percent || (gpu.memory_allocated_gb / gpu.memory_total_gb * 100) || 0)}
                              size="small"
                            />
                          </div>
                          
                          {gpu.multi_processor_count && (
                            <div style={{ fontSize: '12px', color: '#666' }}>
                              流处理器：{gpu.multi_processor_count}
                            </div>
                          )}
                        </Card>
                      </Col>
                    ))}
                  </Row>
                </Card>
              </Col>
            </Row>
          )}

          {/* 第四行：历史图表 */}
          <Row gutter={[16, 16]}>
            <Col xs={24} md={12}>
              <Card title="CPU 使用率历史">
                <Line {...cpuChartConfig} />
              </Card>
            </Col>
            <Col xs={24} md={12}>
              <Card title="内存使用率历史">
                <Line {...memoryChartConfig} />
              </Card>
            </Col>
          </Row>
        </>
      )}
    </div>
  );
};

export default Resources;
