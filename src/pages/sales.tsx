import React, { useState, useEffect } from 'react';
import { Table, Card, Typography, Space, Button, Tag } from 'antd';
import { EditOutlined, DeleteOutlined, PlusOutlined } from '@ant-design/icons';
import { odooService, Sale } from '../services/odooService';

const { Title } = Typography;

const Sales: React.FC = () => {
  const [sales, setSales] = useState<Sale[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSales = async () => {
      try {
        const salesResponse = await odooService.getSales({ page: 1, limit: 100 });
        setSales(salesResponse.data);
      } catch (error) {
        console.error('Error fetching sales:', error);
        // Fallback to default data if API fails
        setSales([
          {
            id: 1,
            customer_id: 1,
            customer_name: 'María García',
            product_id: 1,
            product_name: 'Producto A',
            quantity: 2,
            unit_price: 649.99,
            total: 1299.99,
            date: '2025-05-20',
            status: 'Completado',
          },
          {
            id: 2,
            customer_id: 2,
            customer_name: 'Juan Pérez',
            product_id: 2,
            product_name: 'Producto B',
            quantity: 1,
            unit_price: 849.50,
            total: 849.50,
            date: '2025-05-21',
            status: 'Pendiente',
          },
          {
            id: 3,
            customer_id: 3,
            customer_name: 'Ana Martínez',
            product_id: 3,
            product_name: 'Producto C',
            quantity: 1,
            unit_price: 1599.99,
            total: 1599.99,
            date: '2025-05-22',
            status: 'Completado',
          },
          {
            id: 4,
            customer_id: 4,
            customer_name: 'Carlos Rodríguez',
            product_id: 4,
            product_name: 'Producto D',
            quantity: 1,
            unit_price: 399.99,
            total: 399.99,
            date: '2025-05-23',
            status: 'Cancelado',
          },
          {
            id: 5,
            customer_id: 5,
            customer_name: 'Laura Sánchez',
            product_id: 5,
            product_name: 'Producto E',
            quantity: 1,
            unit_price: 749.99,
            total: 749.99,
            date: '2025-05-24',
            status: 'Pendiente',
          },
        ]);
      } finally {
        setLoading(false);
      }
    };

    fetchSales();
  }, []);

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
    },
    {
      title: 'Cliente',
      dataIndex: 'customer_name',
      key: 'customer_name',
    },
    {
      title: 'Producto',
      dataIndex: 'product_name',
      key: 'product_name',
    },
    {
      title: 'Cantidad',
      dataIndex: 'quantity',
      key: 'quantity',
    },
    {
      title: 'Precio Unitario',
      dataIndex: 'unit_price',
      key: 'unit_price',
      render: (price: number) => `${price.toFixed(2)} €`,
    },
    {
      title: 'Total',
      dataIndex: 'total',
      key: 'total',
      render: (total: number) => `${total.toFixed(2)} €`,
    },
    {
      title: 'Fecha',
      dataIndex: 'date',
      key: 'date',
    },
    {
      title: 'Estado',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        let color = 'green';
        if (status === 'Pendiente') {
          color = 'orange';
        } else if (status === 'Cancelado') {
          color = 'red';
        }
        return <Tag color={color}>{status}</Tag>;
      },
    },
    {
      title: 'Acciones',
      key: 'actions',
      render: (_: any, record: any) => (
        <Space size="middle">
          <Button type="text" icon={<EditOutlined />} />
          <Button type="text" danger icon={<DeleteOutlined />} />
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '20px' }}>
      <Space style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between' }}>
        <Title level={3} style={{ margin: 0, color: '#fff' }}>Ventas</Title>
        <Button type="primary" icon={<PlusOutlined />}>
          Nueva Venta
        </Button>
      </Space>
      
      <Card style={{ background: '#1f1f1f', borderRadius: '8px' }}>
        <Table 
          columns={columns} 
          dataSource={sales} 
          rowKey="id"
          pagination={{ pageSize: 10 }}
          loading={loading}
        />
      </Card>
    </div>
  );
};

export default Sales;
