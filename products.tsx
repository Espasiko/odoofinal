import React, { useState, useEffect, useCallback } from 'react';
import { Table, Card, Button, Tag, Space, Modal, Form, Input, InputNumber, Select, message, Spin, Alert } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import type { TablePaginationConfig } from 'antd/es/table';
import { odooService } from './src/services/odooService';
import { Product, PaginatedResponse } from './src/services/odooService';

const Products: React.FC = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalVisible, setIsModalVisible] = useState(false);
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

  const fetchProducts = useCallback(async (params: TablePaginationConfig = pagination) => {
    setLoading(true);
    try {
      const response: PaginatedResponse<Product> = await odooService.getProducts(
        params.current,
        params.pageSize
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
  }, [pagination]);

  useEffect(() => {
    fetchProducts();
  }, []);

  const handleTableChange = (newPagination: TablePaginationConfig) => {
    fetchProducts(newPagination);
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

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
      sorter: true,
    },
    {
      title: 'Nombre',
      dataIndex: 'name',
      key: 'name',
      sorter: true,
    },
    {
      title: 'Código',
      dataIndex: 'default_code',
      key: 'default_code',
      render: (code: string) => code || <Tag>N/A</Tag>,
    },
    {
      title: 'Precio de Venta',
      dataIndex: 'list_price',
      key: 'list_price',
      render: (price: number) => `€${price ? price.toFixed(2) : '0.00'}`,
      sorter: true,
    },
    {
        title: 'Estado',
        dataIndex: 'active',
        key: 'active',
        render: (active: boolean) => (
            <Tag color={active ? 'green' : 'red'}>{active ? 'Activo' : 'Archivado'}</Tag>
        ),
    },
    {
      title: 'Acciones',
      key: 'actions',
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
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2>Productos de Odoo</h2>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          size="large"
          onClick={() => showModal()}
        >
          Añadir Producto
        </Button>
      </div>
      <Card>
        <Table
          columns={columns}
          dataSource={products}
          rowKey="id"
          pagination={pagination}
          loading={loading}
          onChange={handleTableChange}
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
