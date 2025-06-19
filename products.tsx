import React, { useState, useEffect } from 'react';
import { Table, Card, Button, Tag, Space, Modal, Form, Input, InputNumber, Select, message } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import { odooService } from './src/services/odooService';

interface Product {
  id: number;
  name: string;
  code: string;
  category: string;
  price: number;
  stock: number;
  image_url: string;
}

const Products: React.FC = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  const [form] = Form.useForm();

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    try {
      setLoading(true);
      const data = await odooService.getProducts();
      setProducts(data);
    } catch (error) {
      console.error('Error fetching products:', error);
      message.error('Error al cargar productos');
    } finally {
      setLoading(false);
    }
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
        // Actualizar producto existente
        const updatedProduct = await odooService.updateProduct(editingProduct.id, values);
        if (updatedProduct) {
          setProducts(products.map(p => p.id === editingProduct.id ? updatedProduct : p));
          message.success('Producto actualizado exitosamente');
        } else {
          message.error('Error al actualizar el producto');
        }
      } else {
        // Crear nuevo producto
        const newProduct = await odooService.createProduct(values);
        if (newProduct) {
          setProducts([...products, newProduct]);
          message.success('Producto creado exitosamente');
        } else {
          message.error('Error al crear el producto');
        }
      }
      setIsModalVisible(false);
      setEditingProduct(null);
      form.resetFields();
    } catch (error) {
      console.error('Error submitting product:', error);
      message.error('Error al procesar el producto');
    }
  };

  const handleDelete = (product: Product) => {
    Modal.confirm({
      title: '¿Estás seguro de que quieres eliminar este producto?',
      icon: <ExclamationCircleOutlined />,
      content: `Se eliminará el producto: ${product.name}`,
      okText: 'Sí, eliminar',
      okType: 'danger',
      cancelText: 'Cancelar',
      onOk: async () => {
        try {
          await odooService.deleteProduct(product.id);
          setProducts(products.filter(p => p.id !== product.id));
          message.success('Producto eliminado exitosamente');
        } catch (error) {
          console.error('Error deleting product:', error);
          message.error('Error al eliminar el producto');
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
    },
    {
      title: 'Nombre',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'Código',
      dataIndex: 'code',
      key: 'code',
    },
    {
      title: 'Categoría',
      dataIndex: 'category',
      key: 'category',
    },
    {
      title: 'Precio',
      dataIndex: 'price',
      key: 'price',
      render: (price: number) => `€${price ? price.toFixed(2) : '0.00'}`,
    },
    {
      title: 'Stock',
      dataIndex: 'stock',
      key: 'stock',
      render: (stock: number) => {
        const stockValue = stock || 0;
        let color = 'green';
        if (stockValue < 5) {
          color = 'red';
        } else if (stockValue < 10) {
          color = 'orange';
        }
        return <Tag color={color}>{stockValue} unidades</Tag>;
      },
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
            Eliminar
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2>Productos</h2>
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
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `${range[0]}-${range[1]} de ${total} productos`,
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
          initialValues={{
            category: 'Electrodomésticos',
            price: 0,
            stock: 0
          }}
        >
          <Form.Item
            label="Nombre del Producto"
            name="name"
            rules={[{ required: true, message: 'Por favor ingresa el nombre del producto' }]}
          >
            <Input placeholder="Ej: Refrigerador Samsung" />
          </Form.Item>

          <Form.Item
            label="Código del Producto"
            name="code"
            rules={[{ required: true, message: 'Por favor ingresa el código del producto' }]}
          >
            <Input placeholder="Ej: REF-001" />
          </Form.Item>

          <Form.Item
            label="Categoría"
            name="category"
            rules={[{ required: true, message: 'Por favor selecciona una categoría' }]}
          >
            <Select placeholder="Selecciona una categoría">
              <Select.Option value="Electrodomésticos">Electrodomésticos</Select.Option>
              <Select.Option value="Electrónicos">Electrónicos</Select.Option>
              <Select.Option value="Limpieza">Limpieza</Select.Option>
              <Select.Option value="Cocina">Cocina</Select.Option>
              <Select.Option value="Climatización">Climatización</Select.Option>
              <Select.Option value="Otros">Otros</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            label="Precio (€)"
            name="price"
            rules={[{ required: true, message: 'Por favor ingresa el precio' }]}
          >
            <InputNumber
              min={0}
              step={0.01}
              precision={2}
              style={{ width: '100%' }}
              placeholder="0.00"
            />
          </Form.Item>

          <Form.Item
            label="Stock"
            name="stock"
            rules={[{ required: true, message: 'Por favor ingresa la cantidad en stock' }]}
          >
            <InputNumber
              min={0}
              style={{ width: '100%' }}
              placeholder="0"
            />
          </Form.Item>

          <Form.Item
            label="URL de Imagen"
            name="image_url"
          >
            <Input placeholder="https://example.com/imagen.jpg" />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={handleCancel}>
                Cancelar
              </Button>
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
