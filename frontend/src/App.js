/** QFrame Dashboard - 主应用（带认证） */

import React, { Suspense, useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate, useLocation } from 'react-router-dom';
import { ErrorBoundary } from './components';
import { ResponsiveLayout } from './components/layout';
import { Spin, Layout, Menu, Avatar, Dropdown, Button } from 'antd';
import { 
  DashboardOutlined, 
  ExperimentOutlined, 
  DatabaseOutlined, 
  CloudUploadOutlined,
  RobotOutlined,
  UploadOutlined,
  BarChartOutlined,
  ScheduleOutlined,
  OrderedListOutlined,
  UserOutlined,
  LogoutOutlined,
  TeamOutlined
} from '@ant-design/icons';

// 懒加载页面组件
const Login = lazy(() => import('./pages/Login'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Experiments = lazy(() => import('./pages/Experiments'));
const Models = lazy(() => import('./pages/Models'));
const Training = lazy(() => import('./pages/Training'));
const Backtest = lazy(() => import('./pages/Backtest'));
const Users = lazy(() => import('./pages/Users'));
const Hardware = lazy(() => import('./pages/Hardware'));
const Workers = lazy(() => import('./pages/Workers'));
const Agent = lazy(() => import('./pages/Agent'));
const StrategyUpload = lazy(() => import('./pages/StrategyUpload'));
const Resources = lazy(() => import('./pages/Resources'));
const Scheduler = lazy(() => import('./pages/Scheduler'));
const Queue = lazy(() => import('./pages/Queue'));

// 加载占位组件
const Loading = () => (
  <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
    <Spin size="large" tip="加载中..." />
  </div>
);

// 受保护的路由组件
const ProtectedRoute = ({ children, requiredRole }) => {
  const token = localStorage.getItem('access_token');
  const userRole = localStorage.getItem('user_role');
  
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  
  if (requiredRole && userRole !== requiredRole && userRole !== 'admin') {
    return <Navigate to="/" replace />;
  }
  
  return children;
};

// 主布局组件
function MainLayout() {
  const location = useLocation();
  const [userMenu, setUserMenu] = useState({ username: '用户', role: 'user' });

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    const role = localStorage.getItem('user_role');
    if (token && role) {
      setUserMenu({ username: '用户', role });
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_role');
    window.location.href = '/login';
  };

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: <span>当前角色：{userMenu.role}</span>,
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: <span onClick={handleLogout}>退出登录</span>,
    },
  ];

  const menuItems = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: <Link to="/">Dashboard</Link>,
    },
    {
      key: '/training',
      icon: <CloudUploadOutlined />,
      label: <Link to="/training">训练监控</Link>,
    },
    {
      key: '/backtest',
      icon: <BarChartOutlined />,
      label: <Link to="/backtest">回测管理</Link>,
    },
    {
      key: '/queue',
      icon: <OrderedListOutlined />,
      label: <Link to="/queue">任务队列</Link>,
    },
    {
      key: '/experiments',
      icon: <ExperimentOutlined />,
      label: <Link to="/experiments">实验管理</Link>,
    },
    {
      key: '/models',
      icon: <DatabaseOutlined />,
      label: <Link to="/models">模型管理</Link>,
    },
    {
      key: '/users',
      icon: <TeamOutlined />,
      label: <Link to="/users">用户管理</Link>,
    },
    {
      key: '/hardware',
      icon: <ThunderboltOutlined />,
      label: <Link to="/hardware">硬件配置</Link>,
    },
    {
      key: '/workers',
      icon: <GlobalOutlined />,
      label: <Link to="/workers">分布式 Worker</Link>,
    },
    {
      key: '/agent',
      icon: <RobotOutlined />,
      label: <Link to="/agent">OpenClaw</Link>,
    },
    {
      key: '/resources',
      icon: <BarChartOutlined />,
      label: <Link to="/resources">资源监控</Link>,
    },
    {
      key: '/scheduler',
      icon: <ScheduleOutlined />,
      label: <Link to="/scheduler">调度器</Link>,
    },
  ];

  return (
    <ResponsiveLayout
      menuItems={menuItems}
      selectedKey={location.pathname}
      logo="QFrame"
      headerContent={
        <>
          <h2 style={{ margin: 0 }}>QFrame Dashboard</h2>
          <span>量化交易框架 v1.2</span>
        </>
      }
      extraHeader={
        <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
          <Button type="text" style={{ color: 'white' }}>
            <Avatar size="small" icon={<UserOutlined />} style={{ marginRight: 8 }} />
            {userMenu.username}
          </Button>
        </Dropdown>
      }
    >
      <Suspense fallback={<Loading />}>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          } />
          <Route path="/training" element={
            <ProtectedRoute>
              <Training />
            </ProtectedRoute>
          } />
          <Route path="/backtest" element={
            <ProtectedRoute>
              <Backtest />
            </ProtectedRoute>
          } />
          <Route path="/queue" element={
            <ProtectedRoute>
              <Queue />
            </ProtectedRoute>
          } />
          <Route path="/experiments" element={
            <ProtectedRoute>
              <Experiments />
            </ProtectedRoute>
          } />
          <Route path="/models" element={
            <ProtectedRoute>
              <Models />
            </ProtectedRoute>
          } />
          <Route path="/users" element={
            <ProtectedRoute requiredRole="admin">
              <Users />
            </ProtectedRoute>
          } />
          <Route path="/hardware" element={
            <ProtectedRoute>
              <Hardware />
            </ProtectedRoute>
          } />
          <Route path="/workers" element={
            <ProtectedRoute>
              <Workers />
            </ProtectedRoute>
          } />
          <Route path="/agent" element={
            <ProtectedRoute>
              <Agent />
            </ProtectedRoute>
          } />
          <Route path="/resources" element={
            <ProtectedRoute>
              <Resources />
            </ProtectedRoute>
          } />
          <Route path="/scheduler" element={
            <ProtectedRoute>
              <Scheduler />
            </ProtectedRoute>
          } />
          <Route path="/strategy" element={
            <ProtectedRoute>
              <StrategyUpload />
            </ProtectedRoute>
          } />
        </Routes>
      </Suspense>
    </ResponsiveLayout>
  );
}

function App() {
  return (
    <Router>
      <ErrorBoundary>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/*" element={<MainLayout />} />
        </Routes>
      </ErrorBoundary>
    </Router>
  );
}

export default App;
