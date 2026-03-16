/** 硬件配置管理页面 */

import React, { useState, useEffect } from 'react';
import { Card, Table, Form, InputNumber, Switch, Slider, Button, Space, Row, Col, Progress, Alert, Tag, message } from 'antd';
import { CpuOutlined, MemoryOutlined, HardDiskOutlined, ThunderboltOutlined, SyncOutlined } from '@ant-design/icons';
import { PageHeader } from '@/components';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

function Hardware() {
  const [loading, setLoading] = useState(false);
  const [hardwareInfo, setHardwareInfo] = useState(null);
  const [hardwareStatus, setHardwareStatus] = useState(null);
  const [config, setConfig] = useState(null);
  const [form] = Form.useForm();

  useEffect(() => {
    loadHardwareInfo();
    loadHardwareStatus();
    loadConfig();
    
    // 定时刷新状态
    const interval = setInterval(loadHardwareStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const getHeaders = () => {
    const token = localStorage.getItem('access_token');
    return { 'Authorization': `Bearer ${token}` };
  };

  const loadHardwareInfo = async () => {
    try {
      const res = await axios.get(`${API_BASE_URL}/api/hardware/info`, { headers: getHeaders() });
      setHardwareInfo(res.data.data);
    } catch (error) {
      console.error('加载硬件信息失败:', error);
    }
  };

  const loadHardwareStatus = async () => {
    try {
      const res = await axios.get(`${API_BASE_URL}/api/hardware/status`, { headers: getHeaders() });
      setHardwareStatus(res.data.data);
    } catch (error) {
      console.error('加载硬件状态失败:', error);
    }
  };

  const loadConfig = async () => {
    try {
      const res = await axios.get(`${API_BASE_URL}/api/hardware/config`, { headers: getHeaders() });
      setConfig(res.data.data);
      form.setFieldsValue({
        'cpu.max_cores': res.data.data.cpu.max_cores,
        'cpu.max_percent': res.data.data.cpu.max_percent,
        'memory.max_gb': res.data.data.memory.max_gb,
        'memory.max_percent': res.data.data.memory.max_percent,
        'gpu.enabled': res.data.data.gpu.enabled,
        'gpu.device_ids': res.data.data.gpu.device_ids,
        'gpu.memory_fraction': res.data.data.gpu.memory_fraction,
        'gpu.allow_growth': res.data.data.gpu.allow_growth,
        'training.max_concurrent_tasks': res.data.data.training.max_concurrent_tasks,
      });
    } catch (error) {
      console.error('加载配置失败:', error);
    }
  };

  const handleSaveConfig = async (values) => {
    setLoading(true);
    try {
      await axios.post(`${API_BASE_URL}/api/hardware/config`, values, { headers: getHeaders() });
      message.success('配置已保存');
      loadConfig();
    } catch (error) {
      message.error('保存失败');
    } finally {
      setLoading(false);
    }
  };

  const handleResetConfig = async () => {
    setLoading(true);
    try {
      await axios.post(`${API_BASE_URL}/api/hardware/config/reset`, {}, { headers: getHeaders() });
      message.success('配置已重置');
      loadConfig();
    } catch (error) {
      message.error('重置失败');
    } finally {
      setLoading(false);
    }
  };

  const handleRecommend = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE_URL}/api/hardware/recommend`, { headers: getHeaders() });
      const recommended = res.data.data.recommended;
      
      form.setFieldsValue({
        'cpu.max_cores': recommended.cpu_cores,
        'memory.max_gb': recommended.memory_gb,
        'gpu.device_ids': recommended.gpu_devices,
        'gpu.enabled': recommended.use_gpu,
        'training.default_batch_size': recommended.batch_size,
      });
      
      message.success('已应用推荐配置');
    } catch (error) {
      message.error('获取推荐失败');
    } finally {
      setLoading(false);
    }
  };

  if (!config || !hardwareInfo) {
    return <div>加载中...</div>;
  }

  return (
    <div>
      <PageHeader
        title="硬件配置管理"
        extra={
          <Space>
            <Button icon={<SyncOutlined spin={loading} />} onClick={loadHardwareInfo}>
              刷新
            </Button>
            <Button onClick={handleRecommend}>
              推荐配置
            </Button>
            <Button onClick={handleResetConfig}>
              重置配置
            </Button>
            <Button type="primary" onClick={() => form.submit()}>
              保存配置
            </Button>
          </Space>
        }
      />

      {/* 警告信息 */}
      {hardwareStatus?.warnings?.length > 0 && (
        <Alert
          message="资源警告"
          description={hardwareStatus.warnings.map((w, i) => <div key={i}>{w}</div>)}
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      <Row gutter={16}>
        {/* 硬件信息 */}
        <Col span={12}>
          <Card title="硬件信息" size="small" style={{ marginBottom: 16 }}>
            <Space direction="vertical" style={{ width: '100%' }} size="small">
              <div>
                <CpuOutlined /> CPU: {hardwareInfo.system_info.cpu.count_logical} 核心
                {hardwareInfo.system_info.cpu.freq_max > 0 && ` @ ${hardwareInfo.system_info.cpu.freq_max.toFixed(0)} MHz`}
              </div>
              <div>
                <MemoryOutlined /> 内存：{hardwareInfo.system_info.memory.total_gb.toFixed(1)} GB 
                (可用 {hardwareInfo.system_info.memory.available_gb.toFixed(1)} GB)
              </div>
              <div>
                <ThunderboltOutlined /> GPU: {hardwareInfo.system_info.gpu.available ? 
                  `${hardwareInfo.system_info.gpu.count} 个` : '不可用'}
                {hardwareInfo.system_info.gpu.devices.map((d, i) => (
                  <Tag key={i} color="blue">{d.name}</Tag>
                ))}
              </div>
              <div>
                <HardDiskOutlined /> 磁盘：{hardwareInfo.system_info.disk.total_gb.toFixed(0)} GB 
                (剩余 {hardwareInfo.system_info.disk.free_gb.toFixed(0)} GB)
              </div>
            </Space>
          </Card>

          {/* 实时状态 */}
          <Card title="实时状态" size="small">
            {hardwareStatus && (
              <Space direction="vertical" style={{ width: '100%' }}>
                <div>
                  <div>CPU: {hardwareStatus.current.cpu_percent}%</div>
                  <Progress 
                    percent={hardwareStatus.current.cpu_percent} 
                    strokeColor={hardwareStatus.current.cpu_percent > 80 ? '#ff4d4f' : '#52c41a'}
                  />
                </div>
                <div>
                  <div>内存：{hardwareStatus.current.memory_percent}% ({hardwareStatus.current.memory_used_gb.toFixed(1)} GB)</div>
                  <Progress 
                    percent={hardwareStatus.current.memory_percent} 
                    strokeColor={hardwareStatus.current.memory_percent > 80 ? '#ff4d4f' : '#52c41a'}
                  />
                </div>
                <div>
                  <div>磁盘：{hardwareStatus.current.disk_percent}%</div>
                  <Progress 
                    percent={hardwareStatus.current.disk_percent} 
                    strokeColor={hardwareStatus.current.disk_percent > 90 ? '#ff4d4f' : '#52c41a'}
                  />
                </div>
              </Space>
            )}
          </Card>
        </Col>

        {/* 配置表单 */}
        <Col span={12}>
          <Card title="硬件配置" size="small">
            <Form form={form} layout="vertical" onFinish={handleSaveConfig}>
              <Form.Item label="CPU 最大核心数" name={['cpu', 'max_cores']}>
                <Slider min={1} max={hardwareInfo.system_info.cpu.count_logical} marks={{ '-1': '不限' }} />
              </Form.Item>
              
              <Form.Item label="CPU 最大使用率 %" name={['cpu', 'max_percent']}>
                <InputNumber min={1} max={100} />
              </Form.Item>

              <Form.Item label="内存最大使用 (GB)" name={['memory', 'max_gb']}>
                <InputNumber min={1} max={hardwareInfo.system_info.memory.total_gb} />
              </Form.Item>

              <Form.Item label="内存最大使用率 %" name={['memory', 'max_percent']}>
                <InputNumber min={1} max={100} />
              </Form.Item>

              <Form.Item label="启用 GPU" name={['gpu', 'enabled']} valuePropName="checked">
                <Switch disabled={!hardwareInfo.system_info.gpu.available} />
              </Form.Item>

              {hardwareInfo.system_info.gpu.available && (
                <>
                  <Form.Item label="GPU 设备 IDs" name={['gpu', 'device_ids']}>
                    <InputNumber placeholder="例如：[0,1]" />
                  </Form.Item>
                  
                  <Form.Item label="显存使用比例" name={['gpu', 'memory_fraction']}>
                    <Slider min={0.1} max={1} step={0.1} />
                  </Form.Item>

                  <Form.Item label="显存动态增长" name={['gpu', 'allow_growth']} valuePropName="checked">
                    <Switch />
                  </Form.Item>
                </>
              )}

              <Form.Item label="最大并发训练任务" name={['training', 'max_concurrent_tasks']}>
                <InputNumber min={1} max={4} />
              </Form.Item>
            </Form>
          </Card>
        </Col>
      </Row>
    </div>
  );
}

export default Hardware;
