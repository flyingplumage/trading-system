/**
 * 图表卡片组件
 * 展示图表和数据可视化
 */

import React from 'react';
import { Card } from 'antd';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import PropTypes from 'prop-types';

function ChartCard({
  title,
  data,
  type = 'line',
  xKey = 'name',
  yKeys = ['value'],
  loading = false,
  height = 300
}) {
  const renderChart = () => {
    const commonProps = {
      data,
      margin: { top: 20, right: 30, left: 20, bottom: 20 }
    };

    const gridProps = {
      strokeDasharray: '3 3',
      stroke: '#e8e8e8'
    };

    if (type === 'bar') {
      return (
        <BarChart {...commonProps}>
          <CartesianGrid {...gridProps} />
          <XAxis dataKey={xKey} />
          <YAxis />
          <Tooltip />
          <Legend />
          {yKeys.map((key, index) => (
            <Bar 
              key={key} 
              dataKey={key} 
              fill={['#1890ff', '#52c41a', '#faad14', '#f5222d'][index % 4]} 
            />
          ))}
        </BarChart>
      );
    }

    // 默认 LineChart
    return (
      <LineChart {...commonProps}>
        <CartesianGrid {...gridProps} />
        <XAxis dataKey={xKey} />
        <YAxis />
        <Tooltip />
        <Legend />
        {yKeys.map((key, index) => (
          <Line 
            key={key} 
            type="monotone" 
            dataKey={key} 
            stroke={['#1890ff', '#52c41a', '#faad14', '#f5222d'][index % 4]}
            dot={false}
          />
        ))}
      </LineChart>
    );
  };

  return (
    <Card title={title} loading={loading} size="small">
      <div style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          {renderChart()}
        </ResponsiveContainer>
      </div>
    </Card>
  );
}

ChartCard.propTypes = {
  title: PropTypes.string.isRequired,
  data: PropTypes.array.isRequired,
  type: PropTypes.oneOf(['line', 'bar']),
  xKey: PropTypes.string,
  yKeys: PropTypes.arrayOf(PropTypes.string),
  loading: PropTypes.bool,
  height: PropTypes.number
};

export default ChartCard;
