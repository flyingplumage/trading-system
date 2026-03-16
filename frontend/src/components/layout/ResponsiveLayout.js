/**
 * 响应式布局组件
 * 适配移动端和桌面端
 */

import React from 'react';
import { Layout, Drawer, Menu } from 'antd';
import { MenuOutlined } from '@ant-design/icons';
import PropTypes from 'prop-types';

const { Header, Content, Sider } = Layout;

function ResponsiveLayout({
  children,
  menuItems,
  selectedKey,
  logo = 'QFrame',
  headerContent
}) {
  const [collapsed, setCollapsed] = React.useState(false);
  const [mobileMenuVisible, setMobileMenuVisible] = React.useState(false);
  const [isMobile, setIsMobile] = React.useState(false);

  React.useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
      setCollapsed(!mobile);
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const handleMenuClick = () => {
    if (isMobile) {
      setMobileMenuVisible(false);
    }
  };

  const menuContent = (
    <Menu
      theme={isMobile ? 'light' : 'dark'}
      mode={isMobile ? 'vertical' : 'inline'}
      selectedKeys={[selectedKey]}
      items={menuItems}
      onClick={handleMenuClick}
    />
  );

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* 桌面端侧边栏 */}
      {!isMobile && (
        <Sider 
          collapsible 
          collapsed={collapsed} 
          onCollapse={setCollapsed}
          breakpoint="lg"
        >
          <div style={{ 
            height: 32, 
            margin: 16, 
            background: 'rgba(255, 255, 255, 0.2)',
            borderRadius: 6,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontWeight: 'bold',
            overflow: 'hidden'
          }}>
            {logo}
          </div>
          {menuContent}
        </Sider>
      )}

      {/* 移动端菜单按钮 */}
      {isMobile && (
        <Header style={{ 
          padding: '0 16px', 
          background: '#001529',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <MenuOutlined 
            style={{ fontSize: 18, color: 'white' }}
            onClick={() => setMobileMenuVisible(true)}
          />
          <span style={{ color: 'white', fontWeight: 'bold' }}>{logo}</span>
          <div style={{ width: 18 }} />
        </Header>
      )}

      {/* 移动端抽屉菜单 */}
      <Drawer
        placement="left"
        onClose={() => setMobileMenuVisible(false)}
        open={mobileMenuVisible}
        width={250}
        styles={{ body: { padding: 0 } }}
      >
        <div style={{ 
          height: 32, 
          margin: 16, 
          background: '#001529',
          borderRadius: 6,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
          fontWeight: 'bold'
        }}>
          {logo}
        </div>
        {menuContent}
      </Drawer>

      <Layout>
        {/* 顶部栏 */}
        <Header style={{ 
          padding: isMobile ? '0 16px' : '0 24px', 
          background: '#fff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          boxShadow: '0 1px 4px rgba(0,0,0,0.1)'
        }}>
          {headerContent || <span>QFrame Dashboard</span>}
        </Header>

        {/* 内容区域 */}
        <Content style={{ 
          margin: isMobile ? '12px 8px 0' : '24px 16px 0'
        }}>
          <div
            style={{
              padding: isMobile ? 12 : 24,
              minHeight: 360,
              background: '#fff',
              borderRadius: isMobile ? 4 : 8,
            }}
          >
            {children}
          </div>
        </Content>
      </Layout>
    </Layout>
  );
}

ResponsiveLayout.propTypes = {
  children: PropTypes.node.isRequired,
  menuItems: PropTypes.array.isRequired,
  selectedKey: PropTypes.string,
  logo: PropTypes.string,
  headerContent: PropTypes.node
};

export default ResponsiveLayout;
