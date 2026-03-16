/**
 * 状态标签组件
 * 统一状态标签的颜色映射
 */

import React from 'react';
import { Tag } from 'antd';
import PropTypes from 'prop-types';

const statusColorMap = {
  // 通用状态
  pending: 'default',
  queued: 'blue',
  running: 'processing',
  completed: 'success',
  failed: 'error',
  cancelled: 'warning',
  
  // 实验状态
  success: 'success',
  error: 'error',
  warning: 'warning',
  
  // 自定义映射
  active: 'processing',
  inactive: 'default',
  online: 'success',
  offline: 'default'
};

function StatusTag({ status, text, color }) {
  const tagColor = color || statusColorMap[status] || 'default';
  const displayText = text || status;
  
  return (
    <Tag color={tagColor}>
      {displayText}
    </Tag>
  );
}

StatusTag.propTypes = {
  status: PropTypes.string.isRequired,
  text: PropTypes.string,
  color: PropTypes.string
};

export default StatusTag;
export { statusColorMap };
