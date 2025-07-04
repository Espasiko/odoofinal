import React, { useState, useEffect } from 'react';
import { Layout, Menu, Typography, Drawer } from 'antd';
import {
  DashboardOutlined,
  ShoppingOutlined,
  InboxOutlined,
  ShoppingCartOutlined,
  UserOutlined,
  SettingOutlined,
  TeamOutlined,
} from '@ant-design/icons';
import { NavLink, useLocation } from 'react-router-dom';

const { Sider: AntdSider } = Layout;
const { Title: AntTitle } = Typography;

const menuItems = [
  {
    key: '/dashboard',
    icon: <DashboardOutlined />,
    label: 'Dashboard',
    path: '/dashboard',
  },
  {
    key: '/products',
    icon: <ShoppingOutlined />,
    label: 'Productos',
    path: '/products',
  },
  {
    key: '/inventory',
    icon: <InboxOutlined />,
    label: 'Inventario',
    path: '/inventory',
  },
  {
    key: '/sales',
    icon: <ShoppingCartOutlined />,
    label: 'Ventas',
    path: '/sales',
  },
  {
    key: '/customers',
    icon: <UserOutlined />,
    label: 'Clientes',
    path: '/customers',
  },
  {
    key: '/providers',
    icon: <TeamOutlined />,
    label: 'Proveedores',
    path: '/providers',
  },
  {
    key: '/import-excel',
    icon: <InboxOutlined />,
    label: 'Importar Excel',
    path: '/import-excel',
  },
  {
    key: '/import-invoice',
    icon: <InboxOutlined />,
    label: 'Importar Factura',
    path: '/import-invoice',
  },
  {
    key: '/settings',
    icon: <SettingOutlined />,
    label: 'Configuración',
    path: '/settings',
  },
];

const Sider: React.FC<{ mobileOpen?: boolean; onMobileClose?: () => void }> = ({ mobileOpen = false, onMobileClose }) => {
  const [isMobile, setIsMobile] = useState(window.innerWidth < 992);
  const location = useLocation();

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 992);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const siderContent = (
    <>
      <div style={{ padding: '16px', textAlign: 'center' }}>
        <AntTitle level={4} style={{ color: '#fff', margin: '12px 0' }}>
          Electrodomésticos ERP
        </AntTitle>
      </div>
      <Menu
        theme="dark"
        selectedKeys={[location.pathname]}
        mode="inline"
        style={{ height: '100%' }}
        items={menuItems.map(item => ({
          key: item.key,
          icon: item.icon,
          onClick: () => {
            if (isMobile && onMobileClose) onMobileClose();
          },
          label: (
            <NavLink to={item.path} style={{ color: 'inherit' }}>
              {item.label}
            </NavLink>
          )
        }))}
      />
    </>
  );

  return isMobile ? (
    <Drawer
      placement="left"
      closable={false}
      onClose={onMobileClose}
      open={mobileOpen}
      width={260}
      styles={{ body: { padding: 0, background: '#1f1f1f' } }}
    >
      {siderContent}
      <div style={{ textAlign: 'center', position: 'absolute', bottom: '16px', width: '100%' }}>
        <Typography.Text style={{ color: '#888' }}>
          v1.0.0 &copy; 2025
        </Typography.Text>
      </div>
    </Drawer>
  ) : (
    <AntdSider width={260} style={{ background: '#1f1f1f', minHeight: '100vh', position: 'fixed', left: 0, top: 0 }}>
      {siderContent}
      <div style={{ textAlign: 'center', position: 'absolute', bottom: '16px', width: '100%' }}>
        <Typography.Text style={{ color: '#888' }}>
          v1.0.0 &copy; 2025
        </Typography.Text>
      </div>
    </AntdSider>
  );
};

export default Sider;
