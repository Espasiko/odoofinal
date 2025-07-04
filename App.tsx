import React, { useState, useEffect } from 'react';
// Importa el componente App de antd
import { App as AntdApp, ConfigProvider, Layout, theme, Button } from 'antd';
import { MenuOutlined } from '@ant-design/icons';
import { darkTheme } from './darkTheme';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Refine } from '@refinedev/core';
import { RefineKbar, RefineKbarProvider } from '@refinedev/kbar';
import routerBindings, {
  NavigateToResource,
  UnsavedChangesNotifier,
} from '@refinedev/react-router-v6';
import dataProvider from '@refinedev/simple-rest';
import { 
  notificationProvider,
  ErrorComponent,
} from '@refinedev/antd';

// Importar componentes
import Sider from './sider';
import Header from './header';

// Importar páginas existentes
import Dashboard from './dashboard';
import Products from './products';
import Inventory from './inventory';
import Sales from './sales';
import Customers from './customers';

import Providers from './providers';
import ImportExcelChunk from './src/ImportExcelChunk';
import ImportInvoice from './src/ImportInvoice';



// Importar contexto de Odoo
import { OdooProvider } from './OdooContext';

const { Content } = Layout;

const App: React.FC = () => {
  const [isMobile, setIsMobile] = useState(window.innerWidth < 992);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 992);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);
  
  // URL base para la API FastAPI (backend que se conecta a Odoo)
  const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

  return (
    <Router
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true,
      }}
    >
      <OdooProvider>
        <ConfigProvider theme={darkTheme}>
          <RefineKbarProvider>
            {/* Envuelve la aplicación con el componente App de Ant Design */}
            <AntdApp>
              <Refine
                dataProvider={dataProvider(API_URL)}
                notificationProvider={notificationProvider}
              routerProvider={routerBindings}
              resources={[
                {
                  name: "dashboard",
                  list: "/dashboard",
                  meta: {
                    label: "Dashboard",
                    icon: "DashboardOutlined",
                  },
                },
                {
                  name: "products",
                  list: "/products",
                  meta: {
                    label: "Productos",
                    icon: "ShoppingOutlined",
                  },
                },
                {
                  name: "inventory",
                  list: "/inventory",
                  meta: {
                    label: "Inventario",
                    icon: "InboxOutlined",
                  },
                },
                {
                  name: "sales",
                  list: "/sales",
                  meta: {
                    label: "Ventas",
                    icon: "ShoppingCartOutlined",
                  },
                },
                {
                  name: "customers",
                  list: "/customers",
                  meta: {
                    label: "Clientes",
                    icon: "UserOutlined",
                  },
                },

                {
                  name: "providers",
                  list: "/providers",
                  meta: {
                    label: "Proveedores",
                    icon: "TeamOutlined",
                  },
                },
                {
                  name: "import-excel",
                  list: "/import-excel",
                  meta: {
                    label: "Importar Excel",
                    icon: "InboxOutlined",
                  },
                },
                {
                  name: "import-invoice",
                  list: "/import-invoice",
                  meta: {
                    label: "Importar Factura",
                    icon: "FilePdfOutlined",
                  },
                },

              ]}
              options={{
                syncWithLocation: true,
                warnWhenUnsavedChanges: true,
                projectId: "odoo-dashboard",
                disableTelemetry: true,
              }}
            >
              {isMobile && (
                <Button 
                  type="primary"
                  icon={<MenuOutlined />}
                  onClick={() => setMobileOpen(true)}
                  style={{
                    position: 'fixed',
                    top: '10px',
                    left: '10px',
                    zIndex: 1001,
                  }}
                />
              )}
              <Layout style={{ minHeight: '100vh' }}>
                <Sider mobileOpen={mobileOpen} onMobileClose={() => setMobileOpen(false)} />
                <Layout
                  style={{
                    marginLeft: isMobile ? 0 : 260,
                    transition: 'margin-left 0.3s',
                  }}
                >
                  <Header collapsed={false} setCollapsed={() => {}} />
                  <Content style={{ margin: '24px 16px 0', overflow: 'initial' }}>
                    <Routes>
                      <Route
                        index
                        element={<NavigateToResource resource="dashboard" />}
                      />
                      <Route path="/dashboard" element={<Dashboard />} />
                      <Route path="/products" element={<Products />} />
                      <Route path="/inventory" element={<Inventory />} />
                      <Route path="/sales" element={<Sales />} />
                      <Route path="/customers" element={<Customers />} />
                      <Route path="/providers" element={<Providers />} />
                      <Route path="/import-excel" element={<ImportExcelChunk />} />
                      <Route path="/import-invoice" element={<ImportInvoice />} />
                      <Route path="*" element={<ErrorComponent />} />
                    </Routes>
                    <RefineKbar />
                    <UnsavedChangesNotifier />
                  </Content>
                </Layout>
              </Layout>
            </Refine>
          </AntdApp>
        </RefineKbarProvider>
      </ConfigProvider>
    </OdooProvider>
  </Router>
  );
};

export default App;
