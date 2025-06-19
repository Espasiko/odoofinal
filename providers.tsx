import React, { useState, useEffect } from 'react';
import { Table, Card, Typography, Space, Button, Tag, Form, Input, Select, Modal, message } from 'antd';
import { EditOutlined, DeleteOutlined, PlusOutlined, TeamOutlined } from '@ant-design/icons';
import { odooService, Provider } from './src/services/odooService';

const { Title } = Typography;
const { Option } = Select;

// La interfaz Provider ahora se importa desde odooService.ts

const Providers: React.FC = () => {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingProvider, setEditingProvider] = useState<Provider | null>(null);
  const [form] = Form.useForm();

  useEffect(() => {
    fetchProviders();
  }, []);

  const fetchProviders = async () => {
    try {
      setLoading(true);
      const data = await odooService.getProviders();
      setProviders(data);
    } catch (error) {
      console.error('Error fetching providers:', error);
      message.error('Error al cargar proveedores');
    } finally {
      setLoading(false);
    }
  };

  const showModal = (provider?: Provider) => {
    setEditingProvider(provider || null);
    if (provider) {
      form.setFieldsValue(provider);
    } else {
      form.resetFields();
    }
    setIsModalVisible(true);
  };

  const handleCancel = () => {
    setIsModalVisible(false);
    setEditingProvider(null);
    form.resetFields();
  };

  const handleSubmit = async (values: any) => {
    try {
      if (editingProvider) {
        // Actualizar proveedor existente
        const result = await odooService.updateProvider(editingProvider.id, values);
        if (result) {
          // Actualizar la lista local
          const updatedProviders = providers.map(p => 
            p.id === editingProvider.id ? { ...p, ...values } : p
          );
          setProviders(updatedProviders);
          message.success('Proveedor actualizado correctamente');
        } else {
          throw new Error('Error al actualizar el proveedor');
        }
      } else {
        // Crear nuevo proveedor
        const providerData = {
          ...values,
          is_company: true,
          supplier_rank: 1,
          active: values.active !== undefined ? values.active : true,
          // Campos legacy para compatibilidad
          status: values.active !== false ? 'Activo' : 'Inactivo',
        };
        const result = await odooService.createProvider(providerData);
        if (result) {
          // Añadir el nuevo proveedor a la lista local
          setProviders([...providers, result]);
          message.success('Proveedor creado correctamente');
        } else {
          throw new Error('Error al crear el proveedor');
        }
      }
      handleCancel();
    } catch (error) {
      console.error('Error saving provider:', error);
      message.error('Error al guardar el proveedor');
    }
  };

  const handleDelete = (id: number) => {
    Modal.confirm({
      title: '¿Estás seguro de que quieres eliminar este proveedor?',
      content: 'Esta acción no se puede deshacer.',
      okText: 'Sí, eliminar',
      okType: 'danger',
      cancelText: 'Cancelar',
      onOk: async () => {
        try {
          await odooService.deleteProvider(id);
          setProviders(providers.filter(p => p.id !== id));
          message.success('Proveedor eliminado correctamente');
        } catch (error) {
          console.error('Error deleting provider:', error);
          message.error('Error al eliminar el proveedor');
        }
      },
    });
  };

  // Funciones helper eliminadas - ahora usamos campos estándar de Odoo

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
      render: (text: string) => <strong>{text}</strong>,
    },
    {
      title: 'Email',
      dataIndex: 'email',
      key: 'email',
      render: (email: string) => email || '-',
    },
    {
      title: 'Teléfono',
      dataIndex: 'phone',
      key: 'phone',
      render: (phone: string) => phone || '-',
    },
    {
      title: 'NIF/CIF',
      dataIndex: 'vat',
      key: 'vat',
      render: (vat: string) => vat || '-',
    },
    {
      title: 'Ciudad',
      dataIndex: 'city',
      key: 'city',
      render: (city: string) => city || '-',
    },
    {
      title: 'Estado',
      dataIndex: 'active',
      key: 'active',
      render: (active: boolean) => {
        const color = active ? 'green' : 'red';
        const text = active ? 'Activo' : 'Inactivo';
        return <Tag color={color}>{text}</Tag>;
      },
    },
    {
      title: 'Acciones',
      key: 'actions',
      render: (record: Provider) => (
        <Space>
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
            onClick={() => handleDelete(record.id)}
          >
            Eliminar
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '20px' }}>
      <Card style={{ background: '#1f1f1f', borderRadius: '8px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <Title level={3} style={{ margin: 0, color: '#fff' }}>
            <TeamOutlined style={{ marginRight: '8px' }} />
            Gestión de Proveedores
          </Title>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => showModal()}
            size="large"
          >
            Nuevo Proveedor
          </Button>
        </div>
        
        <Table
          columns={columns}
          dataSource={providers}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `${range[0]}-${range[1]} de ${total} proveedores`,
          }}
          style={{
            background: '#141414',
          }}
        />
      </Card>

      <Modal
        title={editingProvider ? 'Editar Proveedor' : 'Nuevo Proveedor'}
        open={isModalVisible}
        onCancel={handleCancel}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          style={{ marginTop: '20px' }}
          initialValues={{
            is_company: true,
            supplier_rank: 1,
            active: true
          }}
        >
          <Form.Item
            label="Nombre"
            name="name"
            rules={[{ required: true, message: 'Por favor ingresa el nombre del proveedor' }]}
          >
            <Input placeholder="Nombre del proveedor" />
          </Form.Item>

          <Form.Item
            label="Email"
            name="email"
            rules={[{ type: 'email', message: 'Por favor ingresa un email válido' }]}
          >
            <Input placeholder="email@proveedor.com" />
          </Form.Item>

          <Form.Item
            label="Teléfono"
            name="phone"
          >
            <Input placeholder="+34 123 456 789" />
          </Form.Item>

          <Form.Item
            label="Teléfono Móvil"
            name="mobile"
          >
            <Input placeholder="+34 600 123 456" />
          </Form.Item>

          <Form.Item
            label="NIF/CIF"
            name="vat"
          >
            <Input placeholder="A12345678" />
          </Form.Item>

          <Form.Item
            label="Sitio Web"
            name="website"
          >
            <Input placeholder="https://www.proveedor.com" />
          </Form.Item>

          <Form.Item
            label="Dirección"
            name="street"
          >
            <Input placeholder="Calle Principal, 123" />
          </Form.Item>

          <Form.Item
            label="Dirección 2"
            name="street2"
          >
            <Input placeholder="Piso, puerta, etc." />
          </Form.Item>

          <Form.Item
            label="Ciudad"
            name="city"
          >
            <Input placeholder="Madrid" />
          </Form.Item>

          <Form.Item
            label="Código Postal"
            name="zip"
          >
            <Input placeholder="28001" />
          </Form.Item>

          <Form.Item
            label="País"
            name="country"
          >
            <Input placeholder="España" />
          </Form.Item>

          <Form.Item
            label="Referencia Interna"
            name="ref"
          >
            <Input placeholder="REF-PROV-001" />
          </Form.Item>

          <Form.Item
            label="Notas Internas"
            name="comment"
          >
            <Input.TextArea 
              rows={3} 
              placeholder="Notas adicionales sobre el proveedor" 
            />
          </Form.Item>

          <Form.Item
            label="Estado"
            name="active"
            valuePropName="checked"
          >
            <Select defaultValue={true}>
              <Option value={true}>Activo</Option>
              <Option value={false}>Inactivo</Option>
            </Select>
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={handleCancel}>
                Cancelar
              </Button>
              <Button type="primary" htmlType="submit">
                {editingProvider ? 'Actualizar' : 'Crear'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Providers;