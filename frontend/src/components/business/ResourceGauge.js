/**
 * 资源仪表组件
 * 展示系统资源使用情况
 */

import React from 'react';
import { Card, Row, Col, Progress } from 'antd';
import { DashboardOutlined, LaptopOutlined, CheckCircleOutlined } from '@ant-design/icons';
import PropTypes from 'prop-types';

function ResourceGauge({
  title = '系统资源',
  cpuUsage = 0,
  memoryUsage = 0,
  gpuUsage = null,
  gpuMemory = null,
  loading = false
}) {
  const getColor = (usage) => {
    if (usage > 80) return '#f5222d';
    if (usage > 60) return '#faad14';
    return '#52c41a';
  };

  return (
    <Card 
      title={
        <span>
          <DashboardOutlined style={{ marginRight: 8 }} />
          {title}
        </span>
      }
      loading={loading}
      size="small"
    >
      <Row gutter={[16, 16]}>
        <Col span={12}>
          <div style={{ marginBottom: 8 }}>
            <span>CPU 使用率</span>
          </div>
          <Progress
            type="dashboard"
            percent={Math.round(cpuUsage)}
            strokeColor={getColor(cpuUsage)}
            format={(percent) => `${percent}%`}
          />
        </Col>
        <Col span={12}>
          <div style={{ marginBottom: 8 }}>
            <span><LaptopOutlined style={{ marginRight: 4 }} />内存使用率</span>
          </div>
          <Progress
            type="dashboard"
            percent={Math.round(memoryUsage)}
            strokeColor={getColor(memoryUsage)}
            format={(percent) => `${percent}%`}
          />
        </Col>
        {gpuUsage !== null && (
          <>
            <Col span={12}>
              <div style={{ marginBottom: 8 }}>
                <span><CheckCircleOutlined style={{ marginRight: 4 }} />GPU 使用率</span>
              </div>
              <Progress
                type="dashboard"
                percent={Math.round(gpuUsage)}
                strokeColor={getColor(gpuUsage)}
                format={(percent) => `${percent}%`}
              />
            </Col>
            <Col span={12}>
              <div style={{ marginBottom: 8 }}>
                <span>GPU 显存</span>
              </div>
              <Progress
                type="dashboard"
                percent={Math.round((gpuMemory?.used || 0) / (gpuMemory?.total || 1) * 100)}
                strokeColor={getColor((gpuMemory?.used || 0) / (gpuMemory?.total || 1) * 100)}
                format={() => `${gpuMemory?.used?.toFixed(1) || 0}/${gpuMemory?.total?.toFixed(1) || 0} GB`}
              />
            </Col>
          </>
        )}
      </Row>
    </Card>
  );
}

ResourceGauge.propTypes = {
  title: PropTypes.string,
  cpuUsage: PropTypes.number,
  memoryUsage: PropTypes.number,
  gpuUsage: PropTypes.number,
  gpuMemory: PropTypes.shape({
    used: PropTypes.number,
    total: PropTypes.number
  }),
  loading: PropTypes.bool
};

export default ResourceGauge;
