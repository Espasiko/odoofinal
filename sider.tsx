import React from 'react';
import { Layout, Menu, Typography } from 'antd';
import {
  DashboardOutlined,
  ShoppingOutlined,
  InboxOutlined,
  ShoppingCartOutlined,
  UserOutlined,
  SettingOutlined,
  TeamOutlined,

} from '@ant-design/icons';
import { useMenu } from '@refinedev/core';
import { Link } from 'react-router-dom';

const { Sider: AntdSider } = Layout;
const { Title: AntTitle } = Typography;

const Sider: React.FC = () => {
  const { menuItems, selectedKey } = useMenu();

  return (
    <AntdSider
      width={260}
      style={{
        backgroundColor: '#1f1f1f',
        overflow: 'auto',
        height: '100vh',
        position: 'fixed',
        left: 0,
        top: 0,
        bottom: 0,
      }}
    >
      <div style={{ padding: '16px', textAlign: 'center' }}>
        <AntTitle level={4} style={{ color: '#fff', margin: '12px 0' }}>
          Electrodomésticos ERP
        </AntTitle>
      </div>
      <Menu
        theme="dark"
        selectedKeys={[selectedKey]}
        mode="inline"
        style={{ backgroundColor: '#1f1f1f' }}
        items={[
          {
            key: 'dashboard',
            icon: <DashboardOutlined />,
            label: <Link to="/dashboard">Dashboard</Link>,
          },
          {
            key: 'products',
            icon: <ShoppingOutlined />,
            label: <Link to="/products">Productos</Link>,
          },
          {
            key: 'inventory',
            icon: <InboxOutlined />,
            label: <Link to="/inventory">Inventario</Link>,
          },
          {
            key: 'sales',
            icon: <ShoppingCartOutlined />,
            label: <Link to="/sales">Ventas</Link>,
          },
          {
            key: 'customers',
            icon: <UserOutlined />,
            label: <Link to="/customers">Clientes</Link>,
          },

          {
            key: 'providers',
            icon: <TeamOutlined />,
            label: <Link to="/providers">Proveedores</Link>,
          },

          {
            key: 'settings',
            icon: <SettingOutlined />,
            label: <Link to="/settings">Configuración</Link>,
          },
        ]}
      />
      <div style={{ textAlign: 'center', position: 'absolute', bottom: '16px', width: '100%' }}>
        <Typography.Text style={{ color: '#888' }}>
          v1.0.0 © 2025
        </Typography.Text>
      </div>
    </AntdSider>
  );
};

export default Sider;
