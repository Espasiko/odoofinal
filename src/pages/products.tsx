import React, { useState, useEffect, useCallback } from 'react';
import { Table, Card, Button, Tag, Space, Modal, Form, Input, InputNumber, message } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import type { TablePaginationConfig } from 'antd/es/table';
import { odooService } from "../services/odooService";
import { Product, PaginatedResponse } from '../services/odooService';

const Products: React.FC = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  const [form] = Form.useForm();
  const [pagination, setPagination] = useState<TablePaginationConfig>({
    current: 1,
    pageSize: 10,
    total: 0,
    showSizeChanger: true,
    showQuickJumper: true,
    showTotal: (total, range) => `${range[0]}-${range[1]} de ${total} productos`,
  });

  const fetchProducts = useCallback(async (params: TablePaginationConfig = pagination, term: string = searchTerm) => {
    setLoading(true);
    try {
      const response: PaginatedResponse<Product> = await odooService.getProducts(
        params.current,
        params.pageSize,
        'id',
        'asc',
        term
      );
      setProducts(response.data);
      setPagination(prev => ({
        ...prev,
        current: response.page,
        pageSize: response.limit, // 'limit' en la respuesta, 'pageSize' en antd
        total: response.total,
      }));
    } catch (error) {
      console.error('Error fetching products:', error);
      message.error('Error al cargar productos');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProducts(pagination, searchTerm);
  }, [fetchProducts, searchTerm]);

  const handleTableChange = (newPagination: TablePaginationConfig) => {
    fetchProducts(newPagination, searchTerm);
  };

  // Manejar búsqueda
  const handleSearch = (value: string) => {
    setSearchTerm(value);
    fetchProducts({ ...pagination, current: 1 }, value);
  };

  const showModal = (product?: Product) => {
    setEditingProduct(product || null);
    setIsModalVisible(true);
    if (product) {
      form.setFieldsValue(product);
    } else {
      form.resetFields();
    }
  };

  const handleCancel = () => {
    setIsModalVisible(false);
    setEditingProduct(null);
    form.resetFields();
  };

  const handleSubmit = async (values: any) => {
    try {
      if (editingProduct) {
        await odooService.updateProduct(editingProduct.id, values);
      } else {
        await odooService.createProduct(values);
      }
      fetchProducts(pagination); // Recargar la tabla para ver los cambios
      setIsModalVisible(false);
      setEditingProduct(null);
      form.resetFields();
    } catch (error) {
      // El servicio ya muestra un mensaje de error, solo logueamos aquí
      console.error('Error submitting product:', error);
      // No cerramos el modal en caso de error para que el usuario pueda corregir
    }
  };

  const handleDelete = (product: Product) => {
    Modal.confirm({
      title: '¿Estás seguro de que quieres archivar este producto?',
      icon: <ExclamationCircleOutlined />,
      content: `Se archivará el producto: ${product.name}`,
      okText: 'Sí, archivar',
      okType: 'danger',
      cancelText: 'Cancelar',
      onOk: async () => {
        try {
          await odooService.deleteProduct(product.id); // 'delete' en el servicio archiva en Odoo
          fetchProducts(pagination); // Recargar la tabla para ver los cambios
        } catch (error) {
          // El servicio ya muestra un mensaje de error, solo logueamos aquí
          console.error('Error deleting product:', error);
        }
      },
    });
  };

  // Función para calcular el margen
  const calculateMargin = (listPrice: number, standardPrice: number): number => {
    if (!listPrice || !standardPrice || standardPrice === 0) return 0;
    return ((listPrice - standardPrice) / listPrice) * 100;
  };

  // Función para obtener el nombre del proveedor principal
  const getSupplierName = (sellerIds: any[]): string => {
    if (!sellerIds || sellerIds.length === 0) return 'Sin proveedor';
    // Buscar el proveedor principal (sequence más bajo o primer elemento)
    const mainSupplier = sellerIds.find(seller => seller.sequence === 1) || sellerIds[0];
    return mainSupplier?.partner_name || mainSupplier?.name || 'Sin nombre';
  };

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
      sorter: true,
      render: (text: string) => <span style={{ color: '#ffffff' }}>{text}</span>,
    },
    {
      title: 'Nombre',
      dataIndex: 'name',
      key: 'name',
      width: 200,
      sorter: true,
      render: (text: string) => <span style={{ color: '#ffffff' }}>{text}</span>,
    },
    {
      title: 'Código',
      dataIndex: 'default_code',
      key: 'default_code',
      width: 120,
      sorter: true,
      render: (text: string) => <span style={{ color: '#ffffff' }}>{text || 'Sin código'}</span>,
    },
    {
      title: 'Precio de Venta',
      dataIndex: 'list_price',
      key: 'list_price',
      width: 130,
      render: (price: number | null | undefined) => (
        <span style={{ color: '#52c41a', fontWeight: 'bold' }}>
          €{typeof price === 'number' && !isNaN(price) ? price.toFixed(2) : '0.00'}
        </span>
      ),
      sorter: true,
    },
    {
      title: 'Precio de Compra',
      dataIndex: 'standard_price',
      key: 'standard_price',
      width: 140,
      render: (price: number | null | undefined) => (
        <span style={{ color: '#ff7875', fontWeight: 'bold' }}>
          €{typeof price === 'number' && !isNaN(price) ? price.toFixed(2) : '0.00'}
        </span>
      ),
      sorter: true,
    },
    {
      title: 'Proveedor',
      dataIndex: 'seller_ids',
      key: 'supplier',
      width: 150,
      render: (sellerIds: any[]) => (
        <span style={{ color: '#ffffff' }}>
          {getSupplierName(sellerIds)}
        </span>
      ),
    },
    {
      title: 'Categoría',
      dataIndex: 'categ_id',
      key: 'categ_id',
      render: (categId: any) => (
        <span style={{ color: '#ffffff' }}>
          {categId && Array.isArray(categId) && categId[1] ? categId[1] : 'Sin categoría'}
        </span>
      ),
    },
    {
      title: 'Margen (%)',
      key: 'margin',
      width: 100,
      render: (_: any, record: Product) => {
        const margin = calculateMargin(record.list_price, record.standard_price);
        const color = margin > 30 ? '#52c41a' : margin > 15 ? '#faad14' : '#ff4d4f';
        return (
          <span style={{ color, fontWeight: 'bold' }}>
            {margin.toFixed(1)}%
          </span>
        );
      },
      sorter: (a: Product, b: Product) => {
        const marginA = calculateMargin(a.list_price, a.standard_price);
        const marginB = calculateMargin(b.list_price, b.standard_price);
        return marginA - marginB;
      },
    },
    {
      title: 'Estado',
      dataIndex: 'active',
      key: 'active',
      width: 100,
      render: (active: boolean) => (
        <Tag color={active ? 'green' : 'red'}>
          {active ? 'Activo' : 'Inactivo'}
        </Tag>
      ),
    },
    {
      title: 'Acciones',
      key: 'actions',
      width: 150,
      render: (_: any, record: Product) => (
        <Space size="middle">
          <Button
            type="primary"
            icon={<EditOutlined />}
            size="small"
            onClick={() => showModal(record)}
          >
            Editar
          </Button>
          <Button
            type="primary"
            danger
            icon={<DeleteOutlined />}
            size="small"
            onClick={() => handleDelete(record)}
          >
            Archivar
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '20px' }}>
      <Card style={{ background: '#1f1f1f', borderRadius: '8px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap', gap: '16px' }}>
          <h2 style={{ margin: 0, color: '#fff' }}>Productos de Odoo</h2>
          <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
            <Input.Search
               placeholder="Buscar por nombre o código"
               allowClear
               onSearch={handleSearch}
               style={{ maxWidth: 280 }}
             />
            <Button
               type="primary"
               icon={<PlusOutlined />}
               size="large"
               onClick={() => showModal()}
             >
              Añadir Producto
            </Button>
          </div>
        </div>
        
        <Table
          columns={columns}
          dataSource={products}
          rowKey="id"
          pagination={pagination}
          loading={loading}
          onChange={handleTableChange}
          style={{
            background: '#141414',
          }}
        />
      </Card>

      <Modal
        title={editingProduct ? 'Editar Producto' : 'Crear Nuevo Producto'}
        open={isModalVisible}
        onCancel={handleCancel}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          {/* Los campos del formulario se deben actualizar para que coincidan con el modelo Product */}
          <Form.Item
            label="Nombre del Producto"
            name="name"
            rules={[{ required: true, message: 'Por favor ingresa el nombre del producto' }]}
          >
            <Input />
          </Form.Item>

          <Form.Item
            label="Código (Referencia Interna)"
            name="default_code"
          >
            <Input />
          </Form.Item>

          <Form.Item
            label="Precio de Venta (€)"
            name="list_price"
            rules={[{ required: true, message: 'Por favor ingresa el precio' }]}
          >
            <InputNumber min={0} step={0.01} precision={2} style={{ width: '100%' }} />
          </Form.Item>

          {/* Campos informativos (solo lectura) */}
          {editingProduct && (
            <>
              <Form.Item
                label="Precio de Compra (€) - Solo lectura"
                name="standard_price"
              >
                <InputNumber 
                  disabled 
                  min={0} 
                  step={0.01} 
                  precision={2} 
                  style={{ width: '100%', backgroundColor: '#2a2a2a', color: '#ff7875' }} 
                  formatter={(value) => `€ ${value}`}
                />
              </Form.Item>

              <Form.Item
                label="Proveedor Principal - Solo lectura"
              >
                <Input 
                  disabled 
                  value={editingProduct?.seller_ids ? getSupplierName(editingProduct.seller_ids) : 'Sin proveedor'}
                  style={{ backgroundColor: '#2a2a2a', color: '#ffffff' }}
                />
              </Form.Item>

              <Form.Item
                label="Margen (%) - Calculado automáticamente"
              >
                <Input 
                  disabled 
                  value={editingProduct ? `${calculateMargin(editingProduct.list_price, editingProduct.standard_price).toFixed(1)}%` : '0.0%'}
                  style={{ 
                    backgroundColor: '#2a2a2a', 
                    color: editingProduct && calculateMargin(editingProduct.list_price, editingProduct.standard_price) > 30 ? '#52c41a' : 
                           editingProduct && calculateMargin(editingProduct.list_price, editingProduct.standard_price) > 15 ? '#faad14' : '#ff4d4f'
                  }}
                />
              </Form.Item>
            </>
          )}

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={handleCancel}>Cancelar</Button>
              <Button type="primary" htmlType="submit">
                {editingProduct ? 'Actualizar' : 'Crear'} Producto
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Products;
