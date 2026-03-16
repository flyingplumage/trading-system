/**
 * 指标面板组件
 * 展示多个关键指标
 */

import React from 'react';
import { Card, Row, Col, Statistic } from 'antd';
import PropTypes from 'prop-types';

function MetricPanel({
  title,
  metrics,
  loading = false,
  columns = 4
}) {
  return (
    <Card title={title} loading={loading} size="small">
      <Row gutter={16}>
        {metrics.map((metric, index) => (
          <Col span={24 / columns} key={index}>
            <Statistic
              title={metric.label}
              value={metric.value}
              prefix={metric.prefix}
              suffix={metric.suffix}
              precision={metric.precision || 0}
              valueStyle={{ 
                color: metric.color || undefined,
                fontSize: metric.fontSize || undefined
              }}
            />
          </Col>
        ))}
      </Row>
    </Card>
  );
}

MetricPanel.propTypes = {
  title: PropTypes.string.isRequired,
  metrics: PropTypes.arrayOf(
    PropTypes.shape({
      label: PropTypes.string.isRequired,
      value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
      prefix: PropTypes.node,
      suffix: PropTypes.string,
      precision: PropTypes.number,
      color: PropTypes.string,
      fontSize: PropTypes.string
    })
  ).isRequired,
  loading: PropTypes.bool,
  columns: PropTypes.number
};

export default MetricPanel;
