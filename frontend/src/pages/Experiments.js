/** 实验管理页面（使用业务组件重构） */

import React, { useState, useEffect } from 'react';
import { Modal, Form, Input, Select, message } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { ExperimentCard, PageHeader, SearchBar } from '@/components';
import { experiments } from '@/services/api';

function Experiments() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [form] = Form.useForm();
  const [filters, setFilters] = useState({});

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await experiments.list(filters.status, 100);
      setData(res.data.data || []);
    } catch (error) {
      message.error('加载实验列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (values) => {
    try {
      await experiments.create(values);
      message.success('实验创建成功');
      setModalVisible(false);
      form.resetFields();
      loadData();
    } catch (error) {
      message.error('创建实验失败');
    }
  };

  const handleDelete = async (experiment) => {
    try {
      await experiments.delete(experiment.id);
      message.success('实验删除成功');
      loadData();
    } catch (error) {
      message.error('删除实验失败');
    }
  };

  const handleDetail = (experiment) => {
    message.info(`查看详情：${experiment.name}`);
  };

  const statusOptions = [
    { value: 'pending', label: '待处理' },
    { value: 'running', label: '运行中' },
    { value: 'completed', label: '已完成' },
    { value: 'failed', label: '失败' },
  ];

  return (
    <div>
      <PageHeader
        title="实验管理"
        onRefresh={loadData}
        loading={loading}
        extraActions={[
          {
            type: 'primary',
            icon: <PlusOutlined />,
            text: '创建实验',
            onClick: () => setModalVisible(true)
          }
        ]}
      />

      <SearchBar
        onSearch={setFilters}
        onRefresh={() => {
          setFilters({});
          loadData();
        }}
        filters={[
          {
            key: 'status',
            placeholder: '状态',
            options: statusOptions
          }
        ]}
      />

      {/* 实验卡片网格 */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
        gap: 16
      }}>
        {data.map((exp) => (
          <ExperimentCard
            key={exp.id}
            experiment={exp}
            onDetail={handleDetail}
            onDelete={handleDelete}
          />
        ))}
      </div>

      <Modal
        title="创建实验"
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
      >
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item
            name="name"
            label="实验名称"
            rules={[{ required: true, message: '请输入实验名称' }]}
          >
            <Input placeholder="例如：v4_rsi_vol_train" />
          </Form.Item>
          <Form.Item
            name="strategy"
            label="策略路径"
            rules={[{ required: true, message: '请输入策略路径' }]}
          >
            <Input placeholder="例如：neo/v4_rsi_vol" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit">创建</Button>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

export default Experiments;
