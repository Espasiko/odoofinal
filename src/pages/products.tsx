import React, { useState, useEffect, useCallback } from 'react';
import { Table, Card, Button, Tag, Space, Modal, Form, Input, InputNumber, message, Select, Row, Col } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, ExclamationCircleOutlined, ReloadOutlined } from '@ant-design/icons';
import type { TablePaginationConfig } from 'antd/es/table';
import { odooService } from "../services/odooService";
import { Product, PaginatedResponse, Provider } from '../services/odooService';

interface Category {
  id: number;
  name: string;
}

const Products: React.FC = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [selectedProvider, setSelectedProvider] = useState<string>('');
  const [categories, setCategories] = useState<Category[]>([]);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [loadingFilters, setLoadingFilters] = useState(false);
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

  // Función para cargar categorías desde caché o API
  const fetchCategories = useCallback(async () => {
    setLoadingFilters(true);
    try {
      // Intentar obtener categorías del caché
      const cachedCategories = localStorage.getItem('odoo_categories');
      const cacheTimestamp = localStorage.getItem('odoo_categories_timestamp');
      const now = Date.now();
      
      // Si hay caché y no ha expirado (5 minutos)
      if (cachedCategories && cacheTimestamp && (now - parseInt(cacheTimestamp)) < 5 * 60 * 1000) {
        setCategories(JSON.parse(cachedCategories));
        return;
      }
      
      // Si no hay caché o ha expirado, extraer categorías únicas de los productos
      const uniqueCategories: Category[] = [];
      const categoryMap = new Map<number, string>();
      
      products.forEach(product => {
        // Si categ_id es un array [id, nombre]
        if (product.categ_id && Array.isArray(product.categ_id) && product.categ_id.length >= 2) {
          const id = product.categ_id[0];
          const name = product.categ_id[1];
          if (!categoryMap.has(id)) {
            categoryMap.set(id, name);
            uniqueCategories.push({ id, name });
          }
        } 
        // Si tenemos el campo category directamente
        else if (product.category && typeof product.category === 'string') {
          // Usamos un ID negativo para categorías sin ID real
          const id = -uniqueCategories.length - 1;
          if (!categoryMap.has(id)) {
            categoryMap.set(id, product.category);
            uniqueCategories.push({ id, name: product.category });
          }
        }
      });
      
      // Guardar en caché
      localStorage.setItem('odoo_categories', JSON.stringify(uniqueCategories));
      localStorage.setItem('odoo_categories_timestamp', now.toString());
      
      setCategories(uniqueCategories);
    } catch (error) {
      console.error('Error procesando categorías:', error);
    } finally {
      setLoadingFilters(false);
    }
  }, [products]);
  
  // Función para cargar proveedores desde caché o API
  const fetchProviders = useCallback(async () => {
    setLoadingFilters(true);
    try {
      // Intentar obtener proveedores del caché
      const cachedProviders = localStorage.getItem('odoo_providers');
      const cacheTimestamp = localStorage.getItem('odoo_providers_timestamp');
      const now = Date.now();
      
      // Si hay caché y no ha expirado (5 minutos)
      if (cachedProviders && cacheTimestamp && (now - parseInt(cacheTimestamp)) < 5 * 60 * 1000) {
        setProviders(JSON.parse(cachedProviders));
        return;
      }
      
      // Si no hay caché o ha expirado, cargar desde la API
      const response = await odooService.getProviders(1, 100);
      
      // Guardar en caché
      localStorage.setItem('odoo_providers', JSON.stringify(response.data));
      localStorage.setItem('odoo_providers_timestamp', now.toString());
      
      setProviders(response.data);
    } catch (error) {
      console.error('Error cargando proveedores:', error);
    } finally {
      setLoadingFilters(false);
    }
  }, []);

  // Función para obtener el nombre del proveedor principal
  const getSupplierName = (sellerIds: any): string => {
    // Verificar si tenemos datos válidos
    if (!sellerIds) {
      return 'Sin proveedor';
    }
    
    // Si es un array de objetos (formato original esperado)
    if (Array.isArray(sellerIds) && sellerIds.length > 0) {
      // Buscar el proveedor principal (sequence = 1) o tomar el primero
      const mainSupplier = sellerIds.find(seller => seller.sequence === 1) || sellerIds[0];
      
      // Intentar obtener el nombre del partner de diferentes propiedades
      if (mainSupplier?.partner_name) {
        return mainSupplier.partner_name;
      } else if (mainSupplier?.name && typeof mainSupplier.name === 'string') {
        return mainSupplier.name;
      } else if (mainSupplier?.name && Array.isArray(mainSupplier.name) && mainSupplier.name.length > 1) {
        return mainSupplier.name[1]; // [id, nombre]
      }
      
      // Si llegamos aquí, intentamos con cualquier propiedad que pueda contener el nombre
      return mainSupplier?.product_name || 'Sin nombre';
    }
    
    // Si es un string (nombre del proveedor)
    if (typeof sellerIds === 'string' && sellerIds.trim() !== '') {
      return sellerIds;
    }
    
    // Si es un objeto con propiedad name o partner_name
    if (typeof sellerIds === 'object') {
      if ('partner_name' in sellerIds && sellerIds.partner_name) {
        return sellerIds.partner_name;
      } else if ('name' in sellerIds && sellerIds.name) {
        if (typeof sellerIds.name === 'string') {
          return sellerIds.name;
        } else if (Array.isArray(sellerIds.name) && sellerIds.name.length > 1) {
          return sellerIds.name[1]; // [id, nombre]
        }
      }
    }
    
    // Si no se pudo obtener un nombre válido
    return 'Sin proveedor';
  };

  // Función para extraer proveedores únicos de los productos
  const extractUniqueProviders = useCallback(() => {
    const uniqueProviders = new Set<string>();
    
    products.forEach(product => {
      let providerName = 'Sin proveedor';
      
      if (product.seller_ids) {
        providerName = getSupplierName(product.seller_ids);
      } else if (product.supplier_name) {
        providerName = product.supplier_name;
      }
      
      if (providerName !== 'Sin proveedor') {
        uniqueProviders.add(providerName);
      }
    });
    
    return Array.from(uniqueProviders).map(name => ({ name }));
  }, [products]);

  const fetchProducts = useCallback(async (params: TablePaginationConfig = pagination, term: string = searchTerm, category: string = selectedCategory, provider: string = selectedProvider) => {
    setLoading(true);
    try {
      const response: PaginatedResponse<Product> = await odooService.getProducts(
        params.current,
        params.pageSize,
        'id',
        'asc',
        term
      );
      
      // Filtrar productos por categoría y proveedor en el frontend
      // ya que el backend no soporta estos filtros directamente
      let filteredData = response.data;
      
      if (category) {
        filteredData = filteredData.filter(product => {
          // Si categ_id es un array [id, nombre]
          if (product.categ_id && Array.isArray(product.categ_id) && product.categ_id.length >= 2) {
            return product.categ_id[1] === category;
          }
          // Si tenemos el campo category directamente
          else if (product.category && typeof product.category === 'string') {
            return product.category === category;
          }
          return false;
        });
      }
      
      if (provider) {
        filteredData = filteredData.filter(product => {
          let providerName = 'Sin proveedor';
          
          if (product.seller_ids) {
            providerName = getSupplierName(product.seller_ids);
          } else if (product.supplier_name) {
            providerName = product.supplier_name;
          }
          
          return providerName === provider;
        });
      }
      
      setProducts(filteredData);
      setPagination(prev => ({
        ...prev,
        current: response.page,
        pageSize: response.limit,
        total: category || provider ? filteredData.length : response.total,
      }));
    } catch (error) {
      console.error('Error fetching products:', error);
      message.error('Error al cargar productos');
    } finally {
      setLoading(false);
    }
  }, [selectedCategory, selectedProvider, searchTerm]);

  useEffect(() => {
    fetchProducts(pagination, searchTerm, selectedCategory, selectedProvider);
  }, [fetchProducts, searchTerm, selectedCategory, selectedProvider]);
  
  useEffect(() => {
    if (products.length > 0) {
      fetchCategories();
      fetchProviders();
    }
  }, [products, fetchCategories, fetchProviders]);

  const handleTableChange = (newPagination: TablePaginationConfig) => {
    fetchProducts(newPagination, searchTerm, selectedCategory, selectedProvider);
  };

  // Manejar búsqueda
  const handleSearch = (value: string) => {
    setSearchTerm(value);
    fetchProducts({ ...pagination, current: 1 }, value, selectedCategory, selectedProvider);
  };
  
  // Manejar filtro de categoría
  const handleCategoryFilter = (value: string) => {
    setSelectedCategory(value);
    fetchProducts({ ...pagination, current: 1 }, searchTerm, value, selectedProvider);
  };
  
  // Manejar filtro de proveedor
  const handleProviderFilter = (value: string) => {
    setSelectedProvider(value);
    fetchProducts({ ...pagination, current: 1 }, searchTerm, selectedCategory, value);
  };
  
  // Limpiar caché y recargar datos
  const handleRefreshData = () => {
    localStorage.removeItem('odoo_categories');
    localStorage.removeItem('odoo_categories_timestamp');
    localStorage.removeItem('odoo_providers');
    localStorage.removeItem('odoo_providers_timestamp');
    message.info('Actualizando datos...');
    fetchProducts(pagination, searchTerm, selectedCategory, selectedProvider);
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
      key: 'supplier',
      width: 150,
      render: (_: any, record: Product) => {
        // Intentar obtener el proveedor de diferentes formatos posibles
        let providerName = 'Sin proveedor';
        
        if (record.seller_ids) {
          providerName = getSupplierName(record.seller_ids);
        } else if (record.supplier_name) {
          providerName = record.supplier_name;
        }
        
        return <span style={{ color: '#ffffff' }}>{providerName}</span>;
      },
    },
    {
      title: 'Categoría',
      key: 'category',
      render: (_: any, record: Product) => {
        // Si tenemos el campo category directamente
        if (record.category && typeof record.category === 'string') {
          return <span style={{ color: '#ffffff' }}>{record.category}</span>;
        }
        
        // Si tenemos categ_id como array [id, nombre]
        if (record.categ_id && Array.isArray(record.categ_id) && record.categ_id[1]) {
          return <span style={{ color: '#ffffff' }}>{record.categ_id[1]}</span>;
        }
        
        // Si tenemos categ_id como número, mostramos el ID
        if (record.categ_id && typeof record.categ_id === 'number') {
          return <span style={{ color: '#ffffff' }}>Categoría {record.categ_id}</span>;
        }
        
        return <span style={{ color: '#ffffff' }}>Sin categoría</span>;
      },
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
        {/* Cabecera con título y botones principales */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h2 style={{ margin: 0, color: '#fff' }}>Productos de Odoo</h2>
          <div style={{ display: 'flex', gap: '8px' }}>
            <Button
              icon={<ReloadOutlined />}
              onClick={handleRefreshData}
              title="Actualizar datos"
            >
              Actualizar
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              size="large"
              onClick={() => showModal()}
            >
              Nuevo Producto
            </Button>
          </div>
        </div>
        
        {/* Sección de filtros en dos filas */}
        <div style={{ marginBottom: '20px' }}>
          <Row gutter={[16, 16]}>
            {/* Primera fila: Búsqueda por nombre/código */}
            <Col xs={24} sm={24} md={24} lg={24}>
              <Input.Search
                placeholder="Buscar por nombre o código"
                allowClear
                onSearch={handleSearch}
                style={{ width: '100%' }}
                size="large"
              />
            </Col>
            
            {/* Segunda fila: Filtros por categoría y proveedor */}
            <Col xs={24} sm={12} md={12} lg={12}>
              <Select
                placeholder="Filtrar por categoría"
                style={{ width: '100%' }}
                allowClear
                loading={loadingFilters}
                onChange={handleCategoryFilter}
                value={selectedCategory || undefined}
                size="large"
              >
                {categories.map(category => (
                  <Select.Option key={category.id} value={category.name}>
                    {category.name}
                  </Select.Option>
                ))}
              </Select>
            </Col>
            <Col xs={24} sm={12} md={12} lg={12}>
              <Select
                placeholder="Filtrar por proveedor"
                style={{ width: '100%' }}
                allowClear
                loading={loadingFilters}
                onChange={handleProviderFilter}
                value={selectedProvider || undefined}
                size="large"
              >
                {providers.map((provider, index) => (
                  <Select.Option key={provider.id || index} value={provider.name}>
                    {provider.name}
                  </Select.Option>
                ))}
              </Select>
            </Col>
          </Row>
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
