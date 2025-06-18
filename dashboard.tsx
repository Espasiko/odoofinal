import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Typography, Progress, Space } from 'antd';
import { ShoppingOutlined, InboxOutlined, ShoppingCartOutlined, UserOutlined } from '@ant-design/icons';
import { odooService, DashboardStats, CategoryData } from './src/services/odooService';

const { Title } = Typography;

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats>({
    totalProducts: 0,
    totalSales: 0,
    totalCustomers: 0,
    totalProviders: 0,
    pendingOrders: 0,
    monthlyRevenue: 0,
    productStats: {
      totalActive: 0,
      totalInactive: 0,
      totalCategories: 0,
      averagePrice: 0,
      totalValue: 0,
    },
    salesStats: {
      todaySales: 0,
      weekSales: 0,
      monthSales: 0,
      yearSales: 0,
      averageOrderValue: 0,
    },
    stockStats: {
      lowStockProducts: 0,
      outOfStockProducts: 0,
      totalStockValue: 0,
      averageStockLevel: 0,
    },
    providerStats: {
      totalActive: 0,
      totalInactive: 0,
      averagePaymentTerm: 0,
    },
    topCategories: [],
    recentSales: [],
    lowStockProducts: [],
    topSellingProducts: [],
    recentCustomers: [],
    recentProviders: [],
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        // Try to login first with default credentials
        const loginSuccess = await odooService.login('admin', 'admin_password_secure');
        if (loginSuccess) {
          const dashboardStats = await odooService.getDashboardStats();
          setStats(dashboardStats);
        } else {
          throw new Error('Authentication failed');
        }
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
        // Fallback to default data if API fails
        setStats({
          totalProducts: 248,
          totalSales: 156,
          totalCustomers: 156,
          totalProviders: 45,
          pendingOrders: 12,
          monthlyRevenue: 42500,
          productStats: {
            totalActive: 230,
            totalInactive: 18,
            totalCategories: 15,
            averagePrice: 125.50,
            totalValue: 31125.00,
          },
          salesStats: {
            todaySales: 2500,
            weekSales: 15000,
            monthSales: 42500,
            yearSales: 510000,
            averageOrderValue: 275.50,
          },
          stockStats: {
            lowStockProducts: 15,
            outOfStockProducts: 3,
            totalStockValue: 125000,
            averageStockLevel: 45.2,
          },
          providerStats: {
            totalActive: 42,
            totalInactive: 3,
            averagePaymentTerm: 30,
          },
          topCategories: [
            { id: 1, name: 'Electrodomésticos', productCount: 85, totalValue: 15000, percentage: 45 },
            { id: 2, name: 'Electrónicos', productCount: 65, totalValue: 12000, percentage: 30 },
            { id: 3, name: 'Hogar', productCount: 45, totalValue: 8500, percentage: 25 },
          ],
          recentSales: [
            { id: 1, customerName: 'María García', productName: 'Refrigerador Samsung', quantity: 1, unitPrice: 899.99, total: 899.99, date: '2024-01-15', status: 'completed' },
            { id: 2, customerName: 'Juan Pérez', productName: 'Lavadora LG', quantity: 1, unitPrice: 599.99, total: 599.99, date: '2024-01-14', status: 'completed' },
          ],
          lowStockProducts: [
            { id: 1, name: 'Microondas Panasonic', currentStock: 2, minimumStock: 5, category: 'Electrodomésticos', price: 199.99 },
            { id: 2, name: 'Televisor Sony 55"', currentStock: 1, minimumStock: 3, category: 'Electrónicos', price: 799.99 },
          ],
          topSellingProducts: [
            { id: 1, name: 'Refrigerador Samsung', totalSold: 25, revenue: 22499.75, category: 'Electrodomésticos' },
            { id: 2, name: 'Lavadora LG', totalSold: 18, revenue: 10799.82, category: 'Electrodomésticos' },
          ],
          recentCustomers: [
            { id: 1, name: 'María García', email: 'maria@email.com', totalPurchases: 3, lastPurchase: '2024-01-15' },
            { id: 2, name: 'Juan Pérez', email: 'juan@email.com', totalPurchases: 2, lastPurchase: '2024-01-14' },
          ],
          recentProviders: [
            { id: 1, name: 'Samsung Electronics', email: 'contact@samsung.com', totalProducts: 45, lastUpdate: '2024-01-10' },
            { id: 2, name: 'LG Corporation', email: 'info@lg.com', totalProducts: 32, lastUpdate: '2024-01-08' },
          ],
        });
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  return (
    <div className="dashboard-container">
      <Title level={3} style={{ marginBottom: '24px', color: '#fff' }}>Dashboard</Title>
      
      {/* Tarjetas de estadísticas */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card style={{ background: '#1f1f1f', borderRadius: '8px' }}>
            <Statistic
              title="Total Productos"
              value={stats.totalProducts}
              valueStyle={{ color: '#1890ff' }}
              prefix={<ShoppingOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card style={{ background: '#1f1f1f', borderRadius: '8px' }}>
            <Statistic
              title="Productos con Stock Bajo"
              value={stats.stockStats?.lowStockProducts || 0}
              valueStyle={{ color: '#ff4d4f' }}
              prefix={<InboxOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card style={{ background: '#1f1f1f', borderRadius: '8px' }}>
            <Statistic
              title="Ventas del Mes"
              value={stats.monthlyRevenue}
              valueStyle={{ color: '#52c41a' }}
              prefix={<ShoppingCartOutlined />}
              suffix="€"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card style={{ background: '#1f1f1f', borderRadius: '8px' }}>
            <Statistic
              title="Clientes Activos"
              value={stats.totalCustomers}
              valueStyle={{ color: '#722ed1' }}
              prefix={<UserOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* Gráficos y datos adicionales */}
      <Row gutter={[16, 16]} style={{ marginTop: '24px' }}>
        <Col xs={24} lg={12}>
          <Card title="Evolución de Ventas" style={{ background: '#1f1f1f', borderRadius: '8px' }}>
            {/* Aquí iría un gráfico de líneas con Chart.js o similar */}
            <div style={{ height: '200px', background: '#141414', borderRadius: '4px', padding: '16px' }}>
              {/* Placeholder para el gráfico */}
              <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Typography.Text style={{ color: '#888' }}>Gráfico de evolución de ventas</Typography.Text>
              </div>
            </div>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="Productos por Categoría" style={{ background: '#1f1f1f', borderRadius: '8px' }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              {Array.isArray(stats.topCategories) ? stats.topCategories.map((category, index) => (
                <div key={index}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography.Text>{category.name}</Typography.Text>
                    <Typography.Text>{category.percentage}%</Typography.Text>
                  </div>
                  <Progress percent={category.percentage} showInfo={false} strokeColor="#1890ff" />
                </div>
              )) : null}
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;
