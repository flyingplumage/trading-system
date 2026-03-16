/**
 * 进度卡片组件
 * 用于显示训练进度、任务进度等
 */

import React from 'react';
import { Card, Progress, Descriptions } from 'antd';
import PropTypes from 'prop-types';

function ProgressCard({
  title,
  percent,
  status = 'active',
  loading = false,
  extraInfo = [],
  children
}) {
  return (
    <Card 
      title={title} 
      loading={loading}
      extra={children}
    >
      <Progress 
        percent={Math.round(percent)} 
        status={status === 'failed' ? 'exception' : 'active'}
        size="small"
      />
      
      {extraInfo.length > 0 && (
        <Descriptions 
          column={2} 
          size="small" 
          style={{ marginTop: 16 }}
        >
          {extraInfo.map((item, index) => (
            <Descriptions.Item key={index} label={item.label}>
              {item.value}
            </Descriptions.Item>
          ))}
        </Descriptions>
      )}
    </Card>
  );
}

ProgressCard.propTypes = {
  title: PropTypes.string.isRequired,
  percent: PropTypes.number.isRequired,
  status: PropTypes.oneOf(['active', 'success', 'exception', 'normal']),
  loading: PropTypes.bool,
  extraInfo: PropTypes.arrayOf(
    PropTypes.shape({
      label: PropTypes.string,
      value: PropTypes.node
    })
  ),
  children: PropTypes.node
};

export default ProgressCard;
