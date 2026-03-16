/**
 * 错误边界组件
 * 捕获子组件树中的 JavaScript 错误
 */

import React from 'react';
import { Result, Button } from 'antd';
import { BugOutlined } from '@ant-design/icons';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null
    };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ errorInfo });
    console.error('[ErrorBoundary]', error, errorInfo);
    
    // 可以上报错误到监控系统
    // reportError(error, errorInfo);
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    });
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      const { fallback, showMessage } = this.props;

      // 自定义 fallback
      if (fallback) {
        return fallback(this.state.error, this.state.errorInfo);
      }

      // 默认错误展示
      if (showMessage) {
        return (
          <Result
            status="error"
            title="页面出错了"
            subTitle={this.state.error?.message || '抱歉，页面加载失败'}
            icon={<BugOutlined />}
            extra={[
              <Button type="primary" key="reset" onClick={this.handleReset}>
                重试
              </Button>,
              <Button key="reload" onClick={this.handleReload}>
                刷新页面
              </Button>
            ]}
          />
        );
      }

      // 静默模式
      return null;
    }

    return this.props.children;
  }
}

ErrorBoundary.defaultProps = {
  fallback: null,
  showMessage: true
};

export default ErrorBoundary;
