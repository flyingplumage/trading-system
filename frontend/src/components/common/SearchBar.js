/**
 * 搜索栏组件
 * 统一的搜索和筛选功能
 */

import React, { useState } from 'react';
import { Input, Select, Space, Button } from 'antd';
import { SearchOutlined, ReloadOutlined } from '@ant-design/icons';
import PropTypes from 'prop-types';

const { Option } = Select;

function SearchBar({
  onSearch,
  onRefresh,
  filters = [],
  placeholder = '搜索...',
  showRefresh = true,
  loading = false
}) {
  const [searchText, setSearchText] = useState('');
  const [filterValues, setFilterValues] = useState({});

  const handleSearch = () => {
    onSearch?.({
      search: searchText,
      ...filterValues
    });
  };

  const handleFilterChange = (key, value) => {
    const newValues = { ...filterValues, [key]: value };
    setFilterValues(newValues);
    onSearch?.({
      search: searchText,
      ...newValues
    });
  };

  const handleRefresh = () => {
    setSearchText('');
    setFilterValues({});
    onRefresh?.();
  };

  return (
    <Space style={{ marginBottom: 16, flexWrap: 'wrap' }}>
      <Input
        placeholder={placeholder}
        value={searchText}
        onChange={(e) => setSearchText(e.target.value)}
        onPressEnter={handleSearch}
        allowClear
        style={{ width: 200 }}
        prefix={<SearchOutlined />}
      />
      
      {filters.map((filter, index) => (
        <Select
          key={index}
          placeholder={filter.placeholder}
          value={filterValues[filter.key]}
          onChange={(value) => handleFilterChange(filter.key, value)}
          allowClear
          style={{ width: filter.width || 120 }}
        >
          {filter.options.map((option) => (
            <Option key={option.value} value={option.value}>
              {option.label}
            </Option>
          ))}
        </Select>
      ))}
      
      <Space>
        <Button 
          type="primary" 
          icon={<SearchOutlined />} 
          onClick={handleSearch}
          loading={loading}
        >
          搜索
        </Button>
        
        {showRefresh && (
          <Button 
            icon={<ReloadOutlined />} 
            onClick={handleRefresh}
          >
            重置
          </Button>
        )}
      </Space>
    </Space>
  );
}

SearchBar.propTypes = {
  onSearch: PropTypes.func,
  onRefresh: PropTypes.func,
  filters: PropTypes.arrayOf(
    PropTypes.shape({
      key: PropTypes.string,
      placeholder: PropTypes.string,
      width: PropTypes.number,
      options: PropTypes.arrayOf(
        PropTypes.shape({
          value: PropTypes.string,
          label: PropTypes.string
        })
      )
    })
  ),
  placeholder: PropTypes.string,
  showRefresh: PropTypes.bool,
  loading: PropTypes.bool
};

export default SearchBar;
