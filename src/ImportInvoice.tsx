import React, { useRef, useState, useEffect } from 'react';
import { Card, Typography, Input, Checkbox, Button, Progress, message, Tabs, Divider, Space, Table, Select, Spin, Upload, InputNumber, DatePicker, App } from 'antd';
import dayjs from 'dayjs';
import type { TabsProps } from 'antd';

import { useOdoo } from './OdooContext';

const { Title, Paragraph, Text } = Typography;
const { Option } = Select;

interface Provider {
  id: number;
  name: string;
  vat?: string;
}

const ImportInvoice: React.FC = () => {
  const { isAuthenticated, auth, api, login } = useOdoo();
  const { message: messageApi } = App.useApp();
  const fileRef = useRef<File | null>(null);
  const freeFileRef = useRef<File | null>(null);

  const [fileName, setFileName] = useState('');
  const [freeFileName, setFreeFileName] = useState('');
  const [uploading, setUploading] = useState(false);
  const [freeUploading, setFreeUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [freeProgress, setFreeProgress] = useState(0);
  const [status, setStatus] = useState('');
  const [freeStatus, setFreeStatus] = useState('');
  const [createInOdoo, setCreateInOdoo] = useState(true);
  const [freeCreateInOdoo, setFreeCreateInOdoo] = useState(false);
  const [responseJson, setResponseJson] = useState<any>(null);
  const [freeResponseJson, setFreeResponseJson] = useState<any>(null);
  const [editableInvoiceData, setEditableInvoiceData] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<string>('1');
  const [providers, setProviders] = useState<Provider[]>([]);
  const [loadingProviders, setLoadingProviders] = useState<boolean>(false);
  const [selectedProvider, setSelectedProvider] = useState<number | null>(null);
  const [updateIfExists, setUpdateIfExists] = useState<boolean>(false);

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  // Cargar lista de proveedores
  const fetchProviders = async () => {
    try {
      setLoadingProviders(true);
      const response = await api.get('/api/v1/providers/all');
      setProviders(response.data || []);
    } catch (err: any) {
      console.error('Error al cargar proveedores:', err);
      messageApi.error('No se pudieron cargar los proveedores');
    } finally {
      setLoadingProviders(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchProviders();
    }
  }, [isAuthenticated]);

  // Cuando cambian los datos OCR, actualizar los datos editables
  useEffect(() => {
    if (freeResponseJson?.invoice_data) {
      setEditableInvoiceData({
        ...freeResponseJson.invoice_data,
        line_items: freeResponseJson.invoice_data.line_items?.map((item: any) => ({
          ...item
        })) || []
      });
    }
  }, [freeResponseJson]);

  const handleUpload = async () => {
    if (!fileRef.current) {
      messageApi.error('Selecciona un archivo de factura (PDF / imagen).');
      return;
    }

    // Renovar/asegurar token antes de llamar al backend
    const ok = await login(
      import.meta.env.VITE_ODOO_USERNAME || 'admin',
      import.meta.env.VITE_ODOO_PASSWORD || 'admin'
    );
    if (!ok && !isAuthenticated) {
      messageApi.error('No se pudo autenticar con el backend.');
      return;
    }

    setUploading(true);
    setProgress(0);
    setStatus('Subiendo archivo…');

    try {
      const formData = new FormData();
      formData.append('file', fileRef.current);

      const res = await api.post(
        `/api/v1/mistral-ocr/process-invoice?create_in_odoo=${createInOdoo}`,
        formData,
        {
          onUploadProgress: (evt: any) => {
            const pct = Math.round((evt.loaded * 100) / (evt.total ?? 1));
            setProgress(pct);
          },
        },
      );

      setResponseJson(res.data);
      setStatus('Factura procesada correctamente.');
      messageApi.success('Factura procesada.');
    } catch (err: any) {
      console.error(err);
      setStatus('Error al procesar la factura');
      messageApi.error(err?.response?.data?.detail ?? err?.message ?? 'Error desconocido');
    } finally {
      setUploading(false);
    }
  };

  const handleFreeUpload = async () => {
    if (!freeFileRef.current) {
      messageApi.error('Selecciona un archivo de factura (PDF / imagen).');
      return;
    }

    // Renovar/asegurar token antes de llamar al backend
    const ok = await login(
      import.meta.env.VITE_ODOO_USERNAME || 'admin',
      import.meta.env.VITE_ODOO_PASSWORD || 'admin'
    );
    if (!ok && !isAuthenticated) {
      messageApi.error('No se pudo autenticar con el backend.');
      return;
    }

    setFreeUploading(true);
    setFreeProgress(0);
    setFreeStatus('Subiendo archivo…');

    try {
      const formData = new FormData();
      formData.append('file', freeFileRef.current);

      const res = await api.post(
        `/api/v1/mistral-free-ocr/process-invoice?create_in_odoo=${freeCreateInOdoo}`,
        formData,
        {
          onUploadProgress: (evt) => {
            const pct = Math.round((evt.loaded * 100) / (evt.total ?? 1));
            setFreeProgress(pct);
          },
        },
      );

      setFreeResponseJson(res.data);
      setFreeStatus('Factura procesada correctamente con Mistral Free OCR.');
      messageApi.success('Factura procesada con Mistral Free OCR.');
      
      // Si se detectó un proveedor, buscar su ID en la lista de proveedores
      if (res.data?.invoice_data?.supplier_name) {
        const supplierName = res.data.invoice_data.supplier_name;
        const matchingProvider = providers.find(p => 
          p.name.toLowerCase().includes(supplierName.toLowerCase()) || 
          (supplierName.toLowerCase().includes(p.name.toLowerCase()) && p.name.length > 3)
        );
        
        if (matchingProvider) {
          setSelectedProvider(matchingProvider.id);
        }
      }
    } catch (err: any) {
      console.error(err);
      setFreeStatus('Error al procesar la factura con Mistral Free OCR');
      messageApi.error(err?.response?.data?.detail ?? err?.message ?? 'Error desconocido');
    } finally {
      setFreeUploading(false);
    }
  };

  // Función para enviar la factura a Odoo con el proveedor corregido
  const createInvoiceWithCorrectedSupplier = async () => {
    if (!freeResponseJson || !selectedProvider) {
      messageApi.error('Selecciona un proveedor antes de crear la factura');
      return;
    }

    try {
      setFreeUploading(true);
      
      // Clonamos los datos de la factura para modificarlos
      const modifiedInvoiceData = { ...freeResponseJson };
      
      // Reemplazamos el ID del proveedor con el seleccionado manualmente y usamos los datos editados
      const res = await api.post('/api/v1/mistral-free-ocr/create-invoice', {
        ocr_data: {
          ...modifiedInvoiceData,
          invoice_data: editableInvoiceData // Usar los datos editados por el usuario
        },
        supplier_id: selectedProvider,
        update_if_exists: updateIfExists
      });
      
      messageApi.success('Factura creada en Odoo con proveedor correcto');
      // Actualizar el estado con la respuesta
      setFreeResponseJson(res.data);
      
    } catch (err: any) {
      console.error(err);
      messageApi.error(err?.response?.data?.detail ?? err?.message ?? 'Error al crear la factura');
    } finally {
      setFreeUploading(false);
    }
  };

  // Manejadores para editar campos de la factura
  const handleInvoiceFieldChange = (field: string, value: any) => {
    setEditableInvoiceData((prev: any) => ({
      ...prev,
      [field]: value
    }));
  };

  const handleLineItemChange = (index: number, field: string, value: any) => {
    setEditableInvoiceData((prev: any) => {
      const newLineItems = [...prev.line_items];
      newLineItems[index] = {
        ...newLineItems[index],
        [field]: field === 'quantity' || field === 'price_unit' ? parseFloat(value) : value
      };
      return {
        ...prev,
        line_items: newLineItems
      };
    });
  };

  const renderInvoiceData = (data: any) => {
    if (!data || !data.invoice_data || !editableInvoiceData) return null;
    
    const invoiceData = editableInvoiceData; // Usar los datos editables
    
    // Preparar datos para la tabla de líneas de factura
    const lineItems = invoiceData.line_items?.map((item: any, index: number) => ({
      key: index,
      index: index,
      name: item.name,
      quantity: item.quantity,
      price_unit: item.price_unit,
      default_code: item.default_code || '-',
      subtotal: (item.quantity * item.price_unit).toFixed(2)
    })) || [];
    
    const columns = [
      { 
        title: 'Descripción', 
        dataIndex: 'name', 
        key: 'name',
        render: (text: string, record: any) => (
          <Input 
            value={text} 
            onChange={(e) => handleLineItemChange(record.index, 'name', e.target.value)}
            style={{ width: '100%' }}
          />
        )
      },
      { 
        title: 'Cantidad', 
        dataIndex: 'quantity', 
        key: 'quantity',
        render: (text: number, record: any) => (
          <InputNumber 
            value={text} 
            onChange={(value: number | null) => handleLineItemChange(record.index, 'quantity', value || 0)}
            min={0}
            step={0.01}
            style={{ width: '100%' }}
          />
        )
      },
      { 
        title: 'Precio', 
        dataIndex: 'price_unit', 
        key: 'price_unit', 
        render: (text: number, record: any) => (
          <InputNumber 
            value={text} 
            onChange={(value: number | null) => handleLineItemChange(record.index, 'price_unit', value || 0)}
            min={0}
            step={0.01}
            formatter={(value) => `${value} €`}
            parser={(value: string | undefined) => parseFloat(value?.replace(' €', '') || '0')}
            style={{ width: '100%' }}
          />
        )
      },
      { 
        title: 'Código', 
        dataIndex: 'default_code', 
        key: 'default_code',
        render: (text: string, record: any) => (
          <Input 
            value={text === '-' ? '' : text} 
            onChange={(e) => handleLineItemChange(record.index, 'default_code', e.target.value || null)}
            placeholder="Código"
            style={{ width: '100%' }}
          />
        )
      },
      { 
        title: 'Subtotal', 
        dataIndex: 'subtotal', 
        key: 'subtotal', 
        render: (text: string) => `${text} €` 
      }
    ];
    
    return (
      <div style={{ marginTop: 20, background: '#1f1f1f', padding: 16, borderRadius: 8, color: '#ffffff' }}>
        <Title level={4}>Datos Extraídos de la Factura</Title>
        
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '20px' }}>
          <div style={{ flex: '1 1 300px' }}>
            <Title level={5}>Información General</Title>
            <div style={{ marginBottom: '10px' }}>
              <Text strong>Número de Factura:</Text>
              <Input 
                value={invoiceData.invoice_number} 
                onChange={(e) => handleInvoiceFieldChange('invoice_number', e.target.value)}
                style={{ width: '100%', marginTop: '5px' }}
              />
            </div>
            <div style={{ marginBottom: '10px' }}>
              <Text strong>Fecha:</Text>
              <DatePicker 
                value={invoiceData.invoice_date ? dayjs(invoiceData.invoice_date) : null} 
                onChange={(date: any) => handleInvoiceFieldChange('invoice_date', date ? date.format('YYYY-MM-DD') : null)}
                style={{ width: '100%', marginTop: '5px' }}
                format="DD/MM/YYYY"
              />
            </div>
            <div style={{ marginBottom: '10px' }}>
              <Text strong>Vencimiento:</Text>
              <DatePicker 
                value={invoiceData.due_date ? dayjs(invoiceData.due_date) : null} 
                onChange={(date: any) => handleInvoiceFieldChange('due_date', date ? date.format('YYYY-MM-DD') : null)}
                style={{ width: '100%', marginTop: '5px' }}
                format="DD/MM/YYYY"
              />
            </div>
            <div style={{ marginBottom: '10px' }}>
              <Text strong>Total:</Text>
              <InputNumber 
                value={invoiceData.total_amount} 
                onChange={(value: number | null) => handleInvoiceFieldChange('total_amount', value)}
                style={{ width: '100%', marginTop: '5px' }}
                formatter={(value) => `${value} €`}
                parser={(value: string | undefined) => parseFloat(value?.replace(' €', '') || '0')}
                min={0}
                step={0.01}
              />
            </div>
            <div style={{ marginBottom: '10px' }}>
              <Text strong>Subtotal:</Text>
              <InputNumber 
                value={invoiceData.subtotal} 
                onChange={(value: number | null) => handleInvoiceFieldChange('subtotal', value)}
                style={{ width: '100%', marginTop: '5px' }}
                formatter={(value) => `${value} €`}
                parser={(value) => parseFloat(value?.replace(' €', '') || '0')}
                min={0}
                step={0.01}
              />
            </div>
            <div style={{ marginBottom: '10px' }}>
              <Text strong>Impuestos:</Text>
              <InputNumber 
                value={invoiceData.tax_amount} 
                onChange={(value: number | null) => handleInvoiceFieldChange('tax_amount', value)}
                style={{ width: '100%', marginTop: '5px' }}
                formatter={(value) => `${value} €`}
                parser={(value) => parseFloat(value?.replace(' €', '') || '0')}
                min={0}
                step={0.01}
              />
            </div>
          </div>
          
          <div style={{ flex: '1 1 300px' }}>
            <Title level={5}>Proveedor</Title>
            <p><Text strong>Nombre:</Text> {invoiceData.supplier_name}</p>
            <p><Text strong>NIF/CIF:</Text> {invoiceData.supplier_vat || '-'}</p>
            <p><Text strong>Dirección:</Text> {invoiceData.supplier_address || '-'}</p>
            <p><Text strong>Ciudad:</Text> {invoiceData.supplier_city || '-'}</p>
            <p><Text strong>CP:</Text> {invoiceData.supplier_zip || '-'}</p>
            <p><Text strong>Email:</Text> {invoiceData.supplier_email || '-'}</p>
            <p><Text strong>Teléfono:</Text> {invoiceData.supplier_phone || '-'}</p>
            
            <Divider orientation="left" plain>Corrección Manual</Divider>
            <div style={{ marginBottom: '15px' }}>
              <Text strong>Seleccionar Proveedor Correcto:</Text>
              <div style={{ marginTop: '8px', display: 'flex', alignItems: 'center' }}>
                <Select 
                  style={{ width: '100%' }} 
                  placeholder="Selecciona un proveedor" 
                  loading={loadingProviders}
                  value={selectedProvider || undefined}
                  onChange={(value: number) => setSelectedProvider(value)}
                  optionFilterProp="children"
                  showSearch
                >
                  {providers.map(provider => (
                    <Option key={provider.id} value={provider.id}>
                      {provider.name} {provider.vat ? `(${provider.vat})` : ''}
                    </Option>
                  ))}
                </Select>
                {loadingProviders && <Spin size="small" style={{ marginLeft: '10px' }} />}
              </div>
              <div>
                <Checkbox
                  checked={updateIfExists}
                  onChange={(e) => setUpdateIfExists(e.target.checked)}
                  style={{ marginTop: "10px", display: "block", marginBottom: "10px" }}
                >
                  Actualizar factura si ya existe
                </Checkbox>
                <Button 
                  type="primary" 
                  onClick={createInvoiceWithCorrectedSupplier}
                  disabled={!selectedProvider || freeUploading}
                >
                  {updateIfExists ? "Crear/Actualizar Factura" : "Crear Factura"}
                </Button>
              </div>
            </div>
          </div>
          
          <div style={{ flex: '1 1 300px' }}>
            <Title level={5}>Cliente</Title>
            <p><Text strong>Nombre:</Text> {invoiceData.customer_name || '-'}</p>
            <p><Text strong>NIF/CIF:</Text> {invoiceData.customer_vat || '-'}</p>
          </div>
        </div>
        
        <Divider />        
        <Title level={5}>Líneas de Factura</Title>
        <Table 
          dataSource={lineItems} 
          columns={columns} 
          pagination={false} 
          size="small"
          locale={{ emptyText: 'No se detectaron líneas de factura' }}
        />
      </div>
    );
  };

  const items: TabsProps['items'] = [
    {
      key: '1',
      label: 'Método Estándar',
      children: (
        <div>
          <Paragraph>
            Sube una factura en PDF o imagen para extraer los datos mediante IA y crearla/actualizarla en Odoo.
          </Paragraph>

          <input
            type="file"
            accept="application/pdf,image/*"
            onChange={(e) => {
              fileRef.current = e.target.files?.[0] ?? null;
              setFileName(fileRef.current?.name ?? '');
              if (fileRef.current) {
                setStatus('Archivo seleccionado.');
              }
            }}
            disabled={uploading}
          />
          <Paragraph>{fileName}</Paragraph>

          <Checkbox
            checked={createInOdoo}
            onChange={(e) => setCreateInOdoo(e.target.checked)}
            disabled={uploading}
          >
            Crear/Actualizar factura y proveedor en Odoo
          </Checkbox>

          <div style={{ marginTop: 16 }}>
            <Button type="primary" onClick={handleUpload} loading={uploading} disabled={!fileRef.current}>
              Procesar Factura
            </Button>
          </div>

          {uploading && (
            <Progress percent={progress} status="active" style={{ marginTop: 16 }} />
          )}

          {status && <Paragraph>{status}</Paragraph>}

          {responseJson && renderInvoiceData(responseJson)}

          {responseJson && (
            <div style={{ marginTop: 16 }}>
              <Divider>Respuesta JSON</Divider>
              <pre style={{ background: '#1e1e1e', color: '#bfbfbf', padding: 12, marginTop: 16, maxHeight: 300, overflow: 'auto' }}>
                {JSON.stringify(responseJson, null, 2)}
              </pre>
            </div>
          )}
        </div>
      ),
    },
    {
      key: '2',
      label: 'Mistral Free OCR',
      children: (
        <div>
          <Paragraph>
            Sube una factura en PDF o imagen para extraer los datos mediante Mistral Free OCR y crearla/actualizarla en Odoo.
          </Paragraph>

          <input
            type="file"
            accept="application/pdf,image/*"
            onChange={(e) => {
              freeFileRef.current = e.target.files?.[0] ?? null;
              setFreeFileName(freeFileRef.current?.name ?? '');
              if (freeFileRef.current) {
                setFreeStatus('Archivo seleccionado.');
              }
            }}
            disabled={freeUploading}
          />
          <Paragraph>{freeFileName}</Paragraph>

          <Checkbox
            checked={freeCreateInOdoo}
            onChange={(e) => setFreeCreateInOdoo(e.target.checked)}
            disabled={freeUploading}
          >
            Crear/Actualizar factura y proveedor en Odoo
          </Checkbox>

          <div style={{ marginTop: 16 }}>
            <Button type="primary" onClick={handleFreeUpload} loading={freeUploading} disabled={!freeFileRef.current}>
              Procesar con Mistral Free OCR
            </Button>
          </div>

          {freeUploading && (
            <Progress percent={freeProgress} status="active" style={{ marginTop: 16 }} />
          )}

          {freeStatus && <Paragraph>{freeStatus}</Paragraph>}

          {freeResponseJson && renderInvoiceData(freeResponseJson)}

          {freeResponseJson && (
            <div style={{ marginTop: 16 }}>
              <Divider>Respuesta JSON</Divider>
              <pre style={{ background: '#1e1e1e', color: '#bfbfbf', padding: 12, marginTop: 16, maxHeight: 300, overflow: 'auto' }}>
                {JSON.stringify(freeResponseJson, null, 2)}
              </pre>
            </div>
          )}
        </div>
      ),
    },
  ];

  return (
    <Card style={{ maxWidth: 800, margin: '20px auto' }}>
      <Title level={3}>Procesar Factura</Title>
      <Tabs defaultActiveKey="1" items={items} onChange={(key) => setActiveTab(key)} />

    </Card>
  );
};

export default ImportInvoice;
