/** 可视化图表组件 */

import React from 'react';
import { Card, Row, Col } from 'antd';
import { Line, Bar, Gauge } from '@ant-design/charts';

/** 资金曲线图 */
export const EquityCurve = ({ data, height = 300 }) => {
  const config = {
    data,
    xField: 'step',
    yField: 'value',
    height,
    smooth: true,
    animation: {
      appear: {
        animation: 'path-in',
        duration: 1000,
      },
    },
    color: '#1890ff',
    xAxis: {
      label: {
        autoRotate: true,
        autoHide: false,
      },
    },
    yAxis: {
      label: {
        formatter: (value) => `¥${(value / 10000).toFixed(0)}万`,
      },
    },
    tooltip: {
      formatter: (datum) => {
        return { name: '组合价值', value: `¥${datum.value.toFixed(2)}` };
      },
    },
  };

  return <Line {...config} />;
};

/** 收益对比图 */
export const ReturnComparison = ({ data, height = 250 }) => {
  const config = {
    data,
    xField: 'strategy',
    yField: 'return',
    seriesField: 'type',
    isGroup: true,
    height,
    color: ['#1890ff', '#13c2c2', '#722ed1'],
    columnWidthRatio: 0.5,
    yAxis: {
      label: {
        formatter: (value) => `${(value * 100).toFixed(1)}%`,
      },
    },
    tooltip: {
      formatter: (datum) => {
        return { name: datum.type, value: `${(datum.return * 100).toFixed(2)}%` };
      },
    },
  };

  return <Bar {...config} />;
};

/** 回撤分析图 */
export const DrawdownChart = ({ data, height = 200 }) => {
  const config = {
    data,
    xField: 'step',
    yField: 'drawdown',
    height,
    color: '#ff4d4f',
    areaStyle: {
      fill: 'l(270) 0:#ff4d4f 1:#ff7875',
    },
    yAxis: {
      label: {
        formatter: (value) => `${(value * 100).toFixed(1)}%`,
      },
    },
    tooltip: {
      formatter: (datum) => {
        return { name: '回撤', value: `${(datum.drawdown * 100).toFixed(2)}%` };
      },
    },
  };

  return <Line {...config} />;
};

/** 绩效仪表盘 */
export const PerformanceGauge = ({ value, title, height = 180 }) => {
  const config = {
    percent: value,
    height,
    range: {
      color: ['#ff4d4f', '#faad14', '#52c41a'],
    },
    indicator: {
      pointer: {
        style: {
          stroke: '#d0d0d0',
        },
      },
      pin: {
        style: {
          stroke: '#d0d0d0',
        },
      },
    },
    statistic: {
      content: {
        formatter: () => `${(value * 100).toFixed(1)}%`,
        style: { fontSize: '24px' },
      },
    },
  };

  return <Gauge {...config} />;
};

/** 交易分布图 */
export const TradeDistribution = ({ data, height = 250 }) => {
  const config = {
    data,
    binField: 'return',
    stackField: 'type',
    color: ['#1890ff', '#ff4d4f'],
    height,
    tooltip: {
      formatter: (datum) => {
        return { name: datum.type, value: `${datum.count} 笔` };
      },
    },
  };

  return <Histogram {...config} />;
};

/** 参数热力图 */
export const ParameterHeatmap = ({ data, height = 300 }) => {
  const config = {
    data,
    xField: 'param1',
    yField: 'param2',
    colorField: 'score',
    height,
    color: ['#ffffff', '#1890ff', '#0050b3'],
    label: {
      style: {
        fill: '#000',
      },
      formatter: (datum) => `${(datum.score * 100).toFixed(1)}%`,
    },
    tooltip: {
      formatter: (datum) => {
        return {
          name: `${datum.param1}/${datum.param2}`,
          value: `得分：${(datum.score * 100).toFixed(1)}%`,
        };
      },
    },
  };

  return <Heatmap {...config} />;
};

/** 综合绩效卡片 */
export const PerformanceCard = ({ metrics }) => {
  return (
    <Row gutter={16}>
      <Col span={6}>
        <Card size="small" title="总收益率">
          <div style={{ fontSize: 24, color: metrics.total_return >= 0 ? '#52c41a' : '#ff4d4f' }}>
            {(metrics.total_return * 100).toFixed(2)}%
          </div>
        </Card>
      </Col>
      <Col span={6}>
        <Card size="small" title="夏普比率">
          <div style={{ fontSize: 24, color: metrics.sharpe_ratio >= 1 ? '#52c41a' : '#faad14' }}>
            {metrics.sharpe_ratio.toFixed(2)}
          </div>
        </Card>
      </Col>
      <Col span={6}>
        <Card size="small" title="最大回撤">
          <div style={{ fontSize: 24, color: '#ff4d4f' }}>
            {(metrics.max_drawdown * 100).toFixed(2)}%
          </div>
        </Card>
      </Col>
      <Col span={6}>
        <Card size="small" title="胜率">
          <div style={{ fontSize: 24, color: metrics.win_rate >= 0.5 ? '#52c41a' : '#faad14' }}>
            {(metrics.win_rate * 100).toFixed(1)}%
          </div>
        </Card>
      </Col>
    </Row>
  );
};
