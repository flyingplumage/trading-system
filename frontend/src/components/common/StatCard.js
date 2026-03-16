/**
 * 统计卡片组件
 * 用于 Dashboard 和监控页面的统计展示
 */

import React from 'react';
import { Card, Statistic } from 'antd';
import PropTypes from 'prop-types';

function StatCard({
  title,
  value,
  prefix,
  suffix = '',
  precision = 0,
  color = '#1890ff',
  loading = false,
  span = 6
}) {
  return (
    <Card loading={loading} style={{ height: '100%' }}>
      <Statistic
        title={title}
        value={value}
        prefix={prefix}
        suffix={suffix}
        precision={precision}
        valueStyle={{ color }}
      />
    </Card>
  );
}

StatCard.propTypes = {
  title: PropTypes.string.isRequired,
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
  prefix: PropTypes.node,
  suffix: PropTypes.string,
  precision: PropTypes.number,
  color: PropTypes.string,
  loading: PropTypes.bool,
  span: PropTypes.number
};

export default StatCard;
