import React, { useState, useEffect } from 'react';
import { Table, Card, Typography, Space, Button, Tag } from 'antd';
import { EditOutlined, DeleteOutlined, PlusOutlined } from '@ant-design/icons';
import { odooService, Customer } from '../services/odooService';

const { Title } = Typography;

const Customers: React.FC = () => {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchCustomers = async () => {
      try {
        const customersData = await odooService.getCustomers({ page: 1, limit: 100 });
        setCustomers(customersData.data);
      } catch (error) {
        console.error('Error fetching customers:', error);
        // Fallback to default data if API fails
        setCustomers([
          {
            id: 1,
            name: 'María García',
            email: 'maria.garcia@example.com',
            phone: '+34 612 345 678',
            address: 'Madrid',
            total_purchases: 1250.50,
          },
          {
            id: 2,
            name: 'Juan Pérez',
            email: 'juan.perez@example.com',
            phone: '+34 623 456 789',
            address: 'Barcelona',
            total_purchases: 890.25,
          },
          {
            id: 3,
            name: 'Ana Martínez',
            email: 'ana.martinez@example.com',
            phone: '+34 634 567 890',
            address: 'Valencia',
            total_purchases: 0,
          },
          {
            id: 4,
            name: 'Carlos Rodríguez',
            email: 'carlos.rodriguez@example.com',
            phone: '+34 645 678 901',
            address: 'Sevilla',
            total_purchases: 2100.75,
          },
          {
            id: 5,
            name: 'Laura Sánchez',
            email: 'laura.sanchez@example.com',
            phone: '+34 656 789 012',
            address: 'Bilbao',
            total_purchases: 567.30,
          },
        ]);
      } finally {
        setLoading(false);
      }
    };

    fetchCustomers();
  }, []);

  const columns = [
    {
      title: 'Nombre',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'Email',
      dataIndex: 'email',
      key: 'email',
    },
    {
      title: 'Teléfono',
      dataIndex: 'phone',
      key: 'phone',
    },
    {
      title: 'Dirección',
      dataIndex: 'address',
      key: 'address',
    },
    {
      title: 'Total Compras',
      dataIndex: 'total_purchases',
      key: 'total_purchases',
      render: (value: number) => `€${value.toFixed(2)}`,
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
        <Title level={3} style={{ margin: 0, color: '#fff' }}>Clientes</Title>
        <Button type="primary" icon={<PlusOutlined />}>
          Nuevo Cliente
        </Button>
      </Space>
      
      <Card style={{ background: '#1f1f1f', borderRadius: '8px' }}>
        <Table 
          columns={columns} 
          dataSource={customers} 
          rowKey="id"
          pagination={{ pageSize: 10 }}
          loading={loading}
        />
      </Card>
    </div>
  );
};

export default Customers;
