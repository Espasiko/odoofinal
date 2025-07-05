import React from 'react';
import { Table, Card, Typography, Space, Button, Tag, Spin, Alert, Input } from 'antd';
import { EditOutlined, DeleteOutlined, PlusOutlined, SearchOutlined } from '@ant-design/icons';
import { useInventory } from "../hooks/useInventory";

const { Title } = Typography;
const { Search } = Input;

const Inventory: React.FC = () => {
  const {
    inventory,
    loading,
    error,
    totalItems,
    currentPage,
    pageSize,
    searchTerm,
    setCurrentPage,
    setPageSize,
    setSearchTerm,
    refreshInventory,
    updateInventoryItem,
    deleteInventoryItem
  } = useInventory();

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
    },
    {
      title: 'Producto',
      key: 'product_name',
      render: (record: any) => {
        // Usar product_name si está disponible, sino extraer de product_id
        const productName = record.product_name || (record.product_id && record.product_id[1]) || 'N/A';
        return productName;
      },
    },
    {
      title: 'Ubicación',
      key: 'location',
      render: (record: any) => {
        // Usar location si está disponible, sino extraer de location_id
        const locationName = record.location || (record.location_id && record.location_id[1]) || 'N/A';
        return <Tag color="blue">{locationName}</Tag>;
      },
    },
    {
      title: 'Cantidad',
      dataIndex: 'quantity',
      key: 'quantity',
    },
    {
      title: 'Última Actualización',
      dataIndex: 'last_updated',
      key: 'last_updated',
      render: (text: string) => {
        if (!text) return 'N/A';
        return new Date(text).toLocaleDateString();
      },
    },
    {
      title: 'Estado',
      key: 'status',
      render: (record: any) => {
        const quantity = record.quantity || 0;
        const available = quantity; // Definimos 'available' correctamente
        let color = 'green';
        let status = 'En Stock';
        if (available < 5) {
          color = 'red';
          status = 'Stock Bajo';
        } else if (available < 10) {
          color = 'orange';
          status = 'Stock Limitado';
        }
        return <Tag color={color}>{status + ' (' + available + ')'} </Tag>;
      },
    },
    {
      title: 'Acciones',
      key: 'actions',
      render: (_: any, record: any) => (
        <Space size="middle">
          <Button 
            type="text" 
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          />
          <Button 
            type="text" 
            danger 
            icon={<DeleteOutlined />}
            onClick={() => handleDelete(record.id)}
          />
        </Space>
      ),
    },
  ];

  const handleEdit = (record: any) => {
    // TODO: Implementar modal de edición
    console.log('Editar:', record);
  };

  const handleDelete = async (id: number) => {
    // TODO: Implementar confirmación de eliminación
    await deleteInventoryItem(id);
  };

  const handleSearch = (value: string) => {
    setSearchTerm(value);
  };

  if (error) {
    return (
      <div style={{ padding: '20px' }}>
        <Alert
          message="Error al cargar inventario"
          description={error}
          type="error"
          showIcon
          action={
            <Button size="small" onClick={refreshInventory}>
              Reintentar
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <div style={{ padding: '20px' }}>
      <Space style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between' }}>
        <Title level={3} style={{ margin: 0, color: '#fff' }}>Inventario</Title>
        <Space>
          <Search
            placeholder="Buscar productos..."
            allowClear
            enterButton={<SearchOutlined />}
            size="middle"
            onSearch={handleSearch}
            onChange={(e) => e.target.value === '' && setSearchTerm('')}
            style={{ width: 300 }}
          />
          <Button type="primary" icon={<PlusOutlined />}>
            Ajustar Stock
          </Button>
        </Space>
      </Space>
      
      <Card style={{ background: '#1f1f1f', borderRadius: '8px' }}>
        <Spin spinning={loading}>
          <Table 
            columns={columns} 
            dataSource={inventory} 
            rowKey="id"
            pagination={{
              current: currentPage,
              pageSize: pageSize,
              total: totalItems,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total, range) => 
                `${range[0]}-${range[1]} de ${total} elementos`,
              onChange: (page, size) => {
                setCurrentPage(page);
                if (size !== pageSize) {
                  setPageSize(size);
                }
              },
            }}
          />
        </Spin>
      </Card>
    </div>
  );
};

export default Inventory;
