import React from 'react';
// Importa el componente App de antd
import { App as AntdApp, ConfigProvider, Layout, theme } from 'antd';
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
  ThemedLayoutV2,
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



// Importar contexto de Odoo
import { OdooProvider } from './OdooContext';

const { Content } = Layout;

const App: React.FC = () => {
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

              ]}
              options={{
                syncWithLocation: true,
                warnWhenUnsavedChanges: true,
                projectId: "odoo-dashboard",
                disableTelemetry: true,
              }}
            >
              <ThemedLayoutV2 
                Header={() => <Header collapsed={false} setCollapsed={() => {}} />}
                Sider={Sider}
                Title={() => <div style={{ fontSize: "20px", fontWeight: "bold", color: "#fff" }}>Electrodomésticos ERP</div>}
              >
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
                  <Route path="*" element={<ErrorComponent />} />
                </Routes>
              </ThemedLayoutV2>
                <RefineKbar />
                <UnsavedChangesNotifier />
              </Refine>
            </AntdApp>
          </RefineKbarProvider>
        </ConfigProvider>
      </OdooProvider>
    </Router>
  );
};

export default App;
