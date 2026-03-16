/**
 * 页面标题栏组件
 * 统一的页面标题和操作按钮区域
 */

import React from 'react';
import { Space, Button } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import PropTypes from 'prop-types';

function PageHeader({
  title,
  onRefresh,
  extraActions = [],
  showRefresh = true,
  loading = false
}) {
  return (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'space-between', 
      alignItems: 'center',
      marginBottom: 16 
    }}>
      <h2 style={{ margin: 0 }}>{title}</h2>
      
      <Space>
        {extraActions.map((action, index) => (
          <Button
            key={index}
            type={action.type || 'default'}
            icon={action.icon}
            onClick={action.onClick}
            loading={action.loading}
            disabled={action.disabled}
          >
            {action.text}
          </Button>
        ))}
        
        {showRefresh && (
          <Button 
            icon={<ReloadOutlined />} 
            onClick={onRefresh}
            loading={loading}
          >
            刷新
          </Button>
        )}
      </Space>
    </div>
  );
}

PageHeader.propTypes = {
  title: PropTypes.string.isRequired,
  onRefresh: PropTypes.func,
  extraActions: PropTypes.arrayOf(
    PropTypes.shape({
      type: PropTypes.string,
      icon: PropTypes.node,
      text: PropTypes.string,
      onClick: PropTypes.func,
      loading: PropTypes.bool,
      disabled: PropTypes.bool
    })
  ),
  showRefresh: PropTypes.bool,
  loading: PropTypes.bool
};

export default PageHeader;
