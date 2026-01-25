import { useState } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { Layout, Menu, Avatar, Dropdown, Typography, Space } from 'antd';
import {
  DashboardOutlined,
  LineChartOutlined,
  InboxOutlined,
  CoffeeOutlined,
  ShoppingOutlined,
  AppstoreOutlined,
  WalletOutlined,
  FileTextOutlined,
  SettingOutlined,
  LogoutOutlined,
  UserOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from '@ant-design/icons';
import { useAuthStore } from '@/store/authStore';
import { formatRole } from '@/utils/formatters';
import { NAV_ITEMS, ROUTES, APP_VERSION, RELEASE_DATE } from '@/utils/constants';

const { Header, Sider, Content } = Layout;
const { Text } = Typography;

const iconMap: Record<string, React.ReactNode> = {
  DashboardOutlined: <DashboardOutlined />,
  LineChartOutlined: <LineChartOutlined />,
  InboxOutlined: <InboxOutlined />,
  CoffeeOutlined: <CoffeeOutlined />,
  ShoppingOutlined: <ShoppingOutlined />,
  AppstoreOutlined: <AppstoreOutlined />,
  WalletOutlined: <WalletOutlined />,
  FileTextOutlined: <FileTextOutlined />,
  SettingOutlined: <SettingOutlined />,
};

const AppLayout = () => {
  const [collapsed, setCollapsed] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  const handleLogout = () => {
    logout();
    navigate(ROUTES.LOGIN);
  };

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: (
        <div>
          <div style={{ fontWeight: 500 }}>{user?.first_name || 'Пользователь'}</div>
          <div style={{ fontSize: 12, color: '#999' }}>
            {user?.role ? formatRole(user.role) : ''}
          </div>
        </div>
      ),
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'Выйти',
      onClick: handleLogout,
    },
  ];

  // Filter navigation items based on user role
  const navItems = NAV_ITEMS.filter((item) =>
    item.roles.includes(user?.role || '')
  ).map((item) => ({
    key: item.key,
    icon: iconMap[item.icon],
    label: item.label,
    onClick: () => navigate(item.path),
  }));

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* Desktop Sidebar */}
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        breakpoint="lg"
        collapsedWidth={80}
        className="hide-mobile"
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
        }}
      >
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            fontSize: collapsed ? 20 : 18,
            fontWeight: 'bold',
          }}
        >
          {collapsed ? '☕' : 'Vending Admin'}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={navItems}
        />
        {!collapsed && (
          <div
            style={{
              position: 'absolute',
              bottom: 16,
              left: 0,
              right: 0,
              padding: '0 16px',
              textAlign: 'center',
            }}
          >
            <Text
              style={{
                fontSize: 11,
                color: 'rgba(255, 255, 255, 0.45)',
                display: 'block',
              }}
            >
              v{APP_VERSION}
            </Text>
            <Text
              style={{
                fontSize: 10,
                color: 'rgba(255, 255, 255, 0.35)',
                display: 'block',
                marginTop: 2,
              }}
            >
              {new Date(RELEASE_DATE).toLocaleDateString('ru-RU', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
              })}
            </Text>
          </div>
        )}
      </Sider>

      <Layout style={{ marginLeft: collapsed ? 80 : 200, transition: 'margin-left 0.2s' }} className="hide-mobile">
        <Header
          style={{
            padding: '0 24px',
            background: '#fff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            boxShadow: '0 1px 4px rgba(0,21,41,.08)',
          }}
        >
          <Space>
            {collapsed ? (
              <MenuUnfoldOutlined
                style={{ fontSize: 18, cursor: 'pointer' }}
                onClick={() => setCollapsed(false)}
              />
            ) : (
              <MenuFoldOutlined
                style={{ fontSize: 18, cursor: 'pointer' }}
                onClick={() => setCollapsed(true)}
              />
            )}
          </Space>

          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
            <Space style={{ cursor: 'pointer' }}>
              <Avatar icon={<UserOutlined />} />
              <Text>{user?.first_name || 'Пользователь'}</Text>
            </Space>
          </Dropdown>
        </Header>

        <Content style={{ margin: '24px 16px', padding: 24, minHeight: 280 }}>
          <Outlet />
        </Content>
      </Layout>

      {/* Mobile Layout */}
      <Layout className="hide-desktop">
        <Header
          style={{
            padding: '0 16px',
            background: '#fff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            boxShadow: '0 1px 4px rgba(0,21,41,.08)',
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            zIndex: 100,
          }}
        >
          <Text strong style={{ fontSize: 16 }}>
            ☕ Vending Admin
          </Text>

          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
            <Avatar icon={<UserOutlined />} style={{ cursor: 'pointer' }} />
          </Dropdown>
        </Header>

        <Content style={{ marginTop: 64, marginBottom: 50, padding: 16 }}>
          <Outlet />
        </Content>

        {/* Bottom Navigation */}
        <div
          style={{
            position: 'fixed',
            bottom: 0,
            left: 0,
            right: 0,
            background: '#fff',
            borderTop: '1px solid #f0f0f0',
            padding: '8px 0',
            zIndex: 100,
          }}
        >
          <Menu
            mode="horizontal"
            selectedKeys={[location.pathname]}
            items={navItems.slice(0, 5)} // Show only first 5 items in mobile
            style={{
              justifyContent: 'space-around',
              border: 'none',
            }}
          />
        </div>
      </Layout>
    </Layout>
  );
};

export default AppLayout;
