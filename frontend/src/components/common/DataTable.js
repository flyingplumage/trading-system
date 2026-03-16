/**
 * 数据表格组件
 * 统一表格配置和样式
 */

import React from 'react';
import { Table } from 'antd';
import PropTypes from 'prop-types';

function DataTable({
  columns,
  dataSource,
  rowKey = 'id',
  loading = false,
  pagination = { pageSize: 20 },
  size = 'small',
  scroll = { x: true },
  ...restProps
}) {
  return (
    <Table
      columns={columns}
      dataSource={dataSource}
      rowKey={rowKey}
      loading={loading}
      pagination={pagination}
      size={size}
      scroll={scroll}
      {...restProps}
    />
  );
}

DataTable.propTypes = {
  columns: PropTypes.array.isRequired,
  dataSource: PropTypes.array.isRequired,
  rowKey: PropTypes.oneOfType([PropTypes.string, PropTypes.func]),
  loading: PropTypes.bool,
  pagination: PropTypes.oneOfType([PropTypes.object, PropTypes.bool]),
  size: PropTypes.oneOf(['small', 'middle', 'large']),
  scroll: PropTypes.object
};

export default DataTable;
