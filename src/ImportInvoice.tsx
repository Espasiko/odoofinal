import React, { useRef, useState, useEffect } from 'react';
import { Card, Typography, Input, Checkbox, Button, Progress, message, Tabs, Divider, Space, Table, Select, Spin, Upload, InputNumber, DatePicker, App, Form, Alert } from 'antd';
import dayjs from 'dayjs';
import type { TabsProps } from 'antd';

import { useOdoo } from './OdooContext';
import { validateNifCif, formatNifCif } from './utils/nifCifValidator';

const { Title, Paragraph, Text } = Typography;
const { Option } = Select;

interface Provider {
  id: number;
  name: string;
  vat?: string;
}

interface NifCifValidation {
  isValid: boolean;
  message?: string;
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
  const [providerVat, setProviderVat] = useState<string>('');
  const [vatValidation, setVatValidation] = useState<NifCifValidation>({ isValid: false });

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  // Cargar lista de proveedores
  const fetchProviders = async () => {
    try {
      setLoadingProviders(true);
      console.log('Iniciando solicitud de proveedores...');
      
      const response = await api.get('/api/v1/providers/all');
      console.log('Proveedores recibidos:', response.data?.length || 0);
      setProviders(response.data || []);
    } catch (err: any) {
      console.error('Error al cargar proveedores:', err);
      
      // Mostrar información detallada del error
      const errorStatus = err.response?.status;
      const errorMessage = err.response?.data?.detail || err.message;
      
      console.error(`Error ${errorStatus}: ${errorMessage}`);
      
      // Si es un error de autenticación, intentar renovar el token y reintentar
      if (errorStatus === 401) {
        messageApi.warning('Sesión expirada. Intentando renovar automáticamente...');
        
        try {
          console.log('Error 401, esperando a que el interceptor renueve el token...');
          // Esperamos un momento para que el interceptor tenga tiempo de renovar el token
          await new Promise(resolve => setTimeout(resolve, 2000));
          
          // Reintentamos la llamada
          console.log('Reintentando obtener proveedores...');
          const retryResponse = await api.get('/api/v1/providers/all');
          console.log('Reintento exitoso, proveedores recibidos:', retryResponse.data?.length || 0);
          setProviders(retryResponse.data || []);
          messageApi.success('Sesión renovada correctamente');
        } catch (retryErr: any) {
          console.error('Error después de reintentar:', retryErr);
          const retryErrorStatus = retryErr.response?.status;
          const retryErrorMessage = retryErr.response?.data?.detail || retryErr.message;
          
          console.error(`Error en reintento ${retryErrorStatus}: ${retryErrorMessage}`);
          messageApi.error(`Error de autenticación (${retryErrorStatus}). Por favor, recargue la página.`);
        }
      } else {
        messageApi.error(`Error al cargar proveedores: ${errorMessage} (${errorStatus})`);
      }
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
      // Asegurarse de que todos los campos necesarios estén inicializados
      const invoiceData = {
        ...freeResponseJson.invoice_data,
        
        // Asegurar campos del proveedor
        supplier_name: freeResponseJson.invoice_data.supplier_name || '',
        supplier_vat: freeResponseJson.invoice_data.supplier_vat || '',
        supplier_address: freeResponseJson.invoice_data.supplier_address || '',
        supplier_city: freeResponseJson.invoice_data.supplier_city || '',
        supplier_zip: freeResponseJson.invoice_data.supplier_zip || '',
        supplier_email: freeResponseJson.invoice_data.supplier_email || '',
        supplier_phone: freeResponseJson.invoice_data.supplier_phone || '',
        
        // Asegurar campos del cliente
        customer_name: freeResponseJson.invoice_data.customer_name || '',
        customer_vat: freeResponseJson.invoice_data.customer_vat || '',
        customer_address: freeResponseJson.invoice_data.customer_address || '',
        customer_city: freeResponseJson.invoice_data.customer_city || '',
        customer_zip: freeResponseJson.invoice_data.customer_zip || '',
        
        // Asegurar campos de la factura
        invoice_number: freeResponseJson.invoice_data.invoice_number || '',
        invoice_date: freeResponseJson.invoice_data.invoice_date || null,
        due_date: freeResponseJson.invoice_data.due_date || null,
        total_amount: freeResponseJson.invoice_data.total_amount || 0,
        subtotal: freeResponseJson.invoice_data.subtotal || 0,
        tax_amount: freeResponseJson.invoice_data.tax_amount || 0,
        tax_rate: freeResponseJson.invoice_data.tax_rate || 21,
        recargo_equivalencia: freeResponseJson.invoice_data.recargo_equivalencia || 0,
        recargo_rate: freeResponseJson.invoice_data.recargo_rate || 0,
        
        // Procesar líneas de factura
        line_items: freeResponseJson.invoice_data.line_items?.map((item: any, index: number) => ({
          ...item,
          index,
          // Asegurar que los nuevos campos estén inicializados
          name: item.name || '',
          quantity: item.quantity || 0,
          price_unit: item.price_unit || 0,
          default_code: item.default_code || '',
          discount: item.discount || 0,
          tax_rate: item.tax_rate || 21,
          tax_type: item.tax_type || 'iva_21', // Por defecto IVA 21%
          apply_recargo_equivalencia: item.apply_recargo_equivalencia || false,
          recargo_rate: item.recargo_rate || 0,
          subtotal: (item.quantity * item.price_unit * (1 - (item.discount || 0) / 100)).toFixed(2)
        })) || []
      };
      
      setEditableInvoiceData(invoiceData);
      
      // Si hay un NIF/CIF del proveedor en los datos OCR, actualizarlo
      if (freeResponseJson.invoice_data.supplier_vat) {
        const formattedVat = formatNifCif(freeResponseJson.invoice_data.supplier_vat);
        setProviderVat(formattedVat);
        validateProviderVat(formattedVat);
      }
      
      console.log('Datos editables inicializados:', invoiceData);
    }
  }, [freeResponseJson]);
  
  // Validar el NIF/CIF del proveedor
  const validateProviderVat = (value: string) => {
    const validation = validateNifCif(value);
    setVatValidation(validation);
    return validation.isValid;
  };

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
        `/api/v1/mistral-free-ocr/process-invoice?create_in_odoo=${createInOdoo}`,
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
      
      // Añadir información del proveedor si está disponible
      if (selectedProvider) {
        const provider = providers.find(p => p.id === selectedProvider);
        if (provider) {
          formData.append('supplier_name', provider.name);
        }
      }
      
      // Añadir NIF/CIF si está disponible y es válido
      if (providerVat && vatValidation.isValid) {
        formData.append('supplier_vat', providerVat);
      }

      const res = await api.post(
        `/api/v1/ocr/invoice?ocr_method=auto`,
        formData,
        {
          onUploadProgress: (evt) => {
            const pct = Math.round((evt.loaded * 100) / (evt.total ?? 1));
            setFreeProgress(pct);
          },
        },
      );

      setFreeResponseJson(res.data);
      setFreeStatus('Factura procesada correctamente con el método estándar.');
      messageApi.success('Factura procesada con el método estándar.');
      
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
      setFreeStatus('Error al procesar la factura con el método estándar');
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
    
    // Validar que el NIF/CIF sea válido
    if (!vatValidation.isValid) {
      messageApi.error('El NIF/CIF del proveedor no es válido. Por favor, corrígalo antes de continuar.');
      return;
    }

    try {
      setFreeUploading(true);
      
      // Clonamos los datos de la factura para modificarlos
      const modifiedInvoiceData = { ...freeResponseJson };
      
      // Preparar los datos de líneas de factura con impuestos y descuentos
      const processedLineItems = editableInvoiceData.line_items.map((line: any) => {
        // Asegurar que todos los campos necesarios estén presentes
        return {
          name: line.name || '',
          quantity: parseFloat(line.quantity) || 0,
          price_unit: parseFloat(line.price_unit) || 0,
          default_code: line.default_code || '',
          // Incluir campos de descuento e impuestos
          discount: parseFloat(line.discount) || 0,
          tax_type: line.tax_type || 'iva_21',
          apply_recargo_equivalencia: Boolean(line.apply_recargo_equivalencia)
        };
      });
      
      // Aseguramos que el NIF/CIF validado y las líneas procesadas se incluyan en los datos
      const dataToSend = {
        ...editableInvoiceData,
        supplier_vat: providerVat, // Usar el NIF/CIF validado
        line_items: processedLineItems // Usar las líneas procesadas con impuestos y descuentos
      };
      
      console.log('Enviando datos de factura:', JSON.stringify(dataToSend, null, 2));
      
      // Reemplazamos el ID del proveedor con el seleccionado manualmente y usamos los datos editados
      const res = await api.post('/api/v1/ocr/invoice/process-verified/' + freeResponseJson.result_id, {
        invoice_data: dataToSend, // Usar los datos editados por el usuario
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
      
      // Manejar diferentes tipos de campos
      let processedValue = value;
      
      if (field === 'quantity' || field === 'price_unit') {
        // Convertir a número para campos numéricos
        processedValue = parseFloat(value) || 0;
      } else if (field === 'discount') {
        // Asegurar que el descuento sea un número entre 0 y 100
        processedValue = Math.min(Math.max(parseFloat(value) || 0, 0), 100);
      } else if (field === 'apply_recargo_equivalencia') {
        // Asegurar que sea booleano
        processedValue = Boolean(value);
      } else if (field === 'tax_type') {
        // Validar que sea uno de los tipos de impuesto permitidos
        const validTaxTypes = ['iva_21', 'iva_10', 'iva_4'];
        processedValue = validTaxTypes.includes(value) ? value : 'iva_21';
      }
      
      // Actualizar el elemento de línea
      newLineItems[index] = {
        ...newLineItems[index],
        [field]: processedValue
      };
      
      // Recalcular el subtotal si cambia cantidad, precio o descuento
      if (field === 'quantity' || field === 'price_unit' || field === 'discount') {
        const quantity = parseFloat(newLineItems[index].quantity) || 0;
        const price = parseFloat(newLineItems[index].price_unit) || 0;
        const discount = parseFloat(newLineItems[index].discount) || 0;
        
        // Calcular subtotal con descuento aplicado
        const subtotalWithDiscount = quantity * price * (1 - discount / 100);
        newLineItems[index].subtotal = subtotalWithDiscount.toFixed(2);
        console.log(`Recalculando subtotal: ${quantity} * ${price} * (1 - ${discount}/100) = ${subtotalWithDiscount.toFixed(2)}`);
      }
      
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
      discount: item.discount || 0,
      tax_type: item.tax_type || 'iva_21', // Por defecto IVA 21%
      apply_recargo_equivalencia: item.apply_recargo_equivalencia || false,
      subtotal: (item.quantity * item.price_unit * (1 - (item.discount || 0) / 100)).toFixed(2)
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
        width: 80,
        render: (text: number, record: any) => (
          <InputNumber 
            value={text} 
            onChange={(value) => handleLineItemChange(record.index, 'quantity', value || 0)}
            style={{ width: '100%' }}
            min={0}
            step={0.01}
          />
        )
      },
      { 
        title: 'Precio', 
        dataIndex: 'price_unit', 
        key: 'price_unit',
        width: 100,
        render: (text: number, record: any) => (
          <InputNumber 
            value={text} 
            onChange={(value) => handleLineItemChange(record.index, 'price_unit', value || 0)}
            style={{ width: '100%' }}
            min={0}
            step={0.01}
            formatter={(value) => `${value} €`}
            parser={(value) => parseFloat(value?.replace(' €', '') || '0')}
          />
        )
      },
      { 
        title: 'Dto %', 
        dataIndex: 'discount', 
        key: 'discount',
        width: 70,
        render: (text: number, record: any) => (
          <InputNumber 
            value={text} 
            onChange={(value) => handleLineItemChange(record.index, 'discount', value || 0)}
            style={{ width: '100%' }}
            min={0}
            max={100}
            step={1}
            formatter={(value) => `${value}%`}
            parser={(value) => parseFloat(value?.replace('%', '') || '0')}
          />
        )
      },
      { 
        title: 'Impuesto', 
        dataIndex: 'tax_type', 
        key: 'tax_type',
        width: 100,
        render: (text: string, record: any) => (
          <Select
            value={text}
            onChange={(value) => handleLineItemChange(record.index, 'tax_type', value)}
            style={{ width: '100%' }}
            options={[
              { value: 'iva_21', label: 'IVA 21%' },
              { value: 'iva_10', label: 'IVA 10%' },
              { value: 'iva_4', label: 'IVA 4%' },
            ]}
          />
        )
      },
      { 
        title: 'R.E.', 
        dataIndex: 'apply_recargo_equivalencia', 
        key: 'apply_recargo_equivalencia',
        width: 60,
        render: (checked: boolean, record: any) => (
          <Checkbox
            checked={checked}
            onChange={(e) => handleLineItemChange(record.index, 'apply_recargo_equivalencia', e.target.checked)}
          />
        )
      },
      { 
        title: 'Subtotal', 
        dataIndex: 'subtotal', 
        key: 'subtotal',
        width: 100,
        render: (text: string) => `${text} €` 
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
            <div style={{ marginBottom: '10px' }}>
              <Text strong>Nombre:</Text>
              <Input 
                value={invoiceData.supplier_name} 
                onChange={(e) => handleInvoiceFieldChange('supplier_name', e.target.value)}
                style={{ width: '100%', marginTop: '5px' }}
              />
            </div>
            
            {/* Campo NIF/CIF con validación */}
            <div style={{ marginBottom: '10px' }}>
              <Text strong>NIF/CIF:</Text>
              <Form.Item 
                validateStatus={vatValidation.isValid ? 'success' : (providerVat ? 'error' : '')}
                help={!vatValidation.isValid && providerVat ? vatValidation.message : null}
                style={{ marginBottom: '0' }}
              >
                <Input 
                  value={providerVat} 
                  onChange={(e) => {
                    const formatted = formatNifCif(e.target.value);
                    setProviderVat(formatted);
                    validateProviderVat(formatted);
                    // Actualizar también en los datos editables
                    handleInvoiceFieldChange('supplier_vat', formatted);
                  }}
                  placeholder="Introduce NIF/CIF válido"
                  status={vatValidation.isValid ? '' : (providerVat ? 'error' : '')}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </div>
            
            <div style={{ marginBottom: '10px' }}>
              <Text strong>Dirección:</Text>
              <Input 
                value={invoiceData.supplier_address || ''} 
                onChange={(e) => handleInvoiceFieldChange('supplier_address', e.target.value)}
                placeholder="Dirección"
                style={{ width: '100%', marginTop: '5px' }}
              />
            </div>
            <div style={{ marginBottom: '10px' }}>
              <Text strong>Ciudad:</Text>
              <Input 
                value={invoiceData.supplier_city || ''} 
                onChange={(e) => handleInvoiceFieldChange('supplier_city', e.target.value)}
                placeholder="Ciudad"
                style={{ width: '100%', marginTop: '5px' }}
              />
            </div>
            <div style={{ marginBottom: '10px' }}>
              <Text strong>CP:</Text>
              <Input 
                value={invoiceData.supplier_zip || ''} 
                onChange={(e) => handleInvoiceFieldChange('supplier_zip', e.target.value)}
                placeholder="Código Postal"
                style={{ width: '100%', marginTop: '5px' }}
              />
            </div>
            <div style={{ marginBottom: '10px' }}>
              <Text strong>Email:</Text>
              <Input 
                value={invoiceData.supplier_email || ''} 
                onChange={(e) => handleInvoiceFieldChange('supplier_email', e.target.value)}
                placeholder="Email"
                style={{ width: '100%', marginTop: '5px' }}
              />
            </div>
            <div style={{ marginBottom: '10px' }}>
              <Text strong>Teléfono:</Text>
              <Input 
                value={invoiceData.supplier_phone || ''} 
                onChange={(e) => handleInvoiceFieldChange('supplier_phone', e.target.value)}
                placeholder="Teléfono"
                style={{ width: '100%', marginTop: '5px' }}
              />
            </div>
            
            <Divider orientation="left" plain>Corrección Manual</Divider>
            <div style={{ marginBottom: '15px' }}>
              <Text strong>Seleccionar Proveedor Correcto:</Text>
              <div style={{ marginTop: '8px', display: 'flex', alignItems: 'center' }}>
                <Select 
                  style={{ width: '100%' }} 
                  placeholder="Selecciona un proveedor" 
                  loading={loadingProviders}
                  value={selectedProvider || undefined}
                  onChange={(value: number) => {
                    setSelectedProvider(value);
                    // Buscar el proveedor seleccionado y actualizar el NIF/CIF si existe
                    const provider = providers.find(p => p.id === value);
                    if (provider && provider.vat) {
                      const formattedVat = formatNifCif(provider.vat);
                      setProviderVat(formattedVat);
                      validateProviderVat(formattedVat);
                      handleInvoiceFieldChange('supplier_vat', formattedVat);
                    }
                  }}
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
              
              {/* Alerta de NIF/CIF obligatorio */}
              {!vatValidation.isValid && (
                <Alert
                  message="NIF/CIF obligatorio"
                  description="Debes introducir un NIF/CIF válido para el proveedor antes de crear la factura."
                  type="warning"
                  showIcon
                  style={{ marginTop: '10px', marginBottom: '10px' }}
                />
              )}
              
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
                  disabled={!selectedProvider || freeUploading || !vatValidation.isValid}
                >
                  {updateIfExists ? "Crear/Actualizar Factura" : "Crear Factura"}
                </Button>
              </div>
            </div>
          </div>
          
          <div style={{ flex: '1 1 300px' }}>
            <Title level={5}>Cliente</Title>
            <div style={{ marginBottom: '10px' }}>
              <Text strong>Nombre:</Text>
              <Input 
                value={invoiceData.customer_name || ''} 
                onChange={(e) => handleInvoiceFieldChange('customer_name', e.target.value)}
                placeholder="Nombre del cliente"
                style={{ width: '100%', marginTop: '5px' }}
              />
            </div>
            <div style={{ marginBottom: '10px' }}>
              <Text strong>NIF/CIF:</Text>
              <Input 
                value={invoiceData.customer_vat || ''} 
                onChange={(e) => handleInvoiceFieldChange('customer_vat', e.target.value)}
                placeholder="NIF/CIF del cliente"
                style={{ width: '100%', marginTop: '5px' }}
              />
            </div>
            <div style={{ marginBottom: '10px' }}>
              <Text strong>Dirección:</Text>
              <Input 
                value={invoiceData.customer_address || ''} 
                onChange={(e) => handleInvoiceFieldChange('customer_address', e.target.value)}
                placeholder="Dirección del cliente"
                style={{ width: '100%', marginTop: '5px' }}
              />
            </div>
            <div style={{ marginBottom: '10px' }}>
              <Text strong>Ciudad:</Text>
              <Input 
                value={invoiceData.customer_city || ''} 
                onChange={(e) => handleInvoiceFieldChange('customer_city', e.target.value)}
                placeholder="Ciudad del cliente"
                style={{ width: '100%', marginTop: '5px' }}
              />
            </div>
            <div style={{ marginBottom: '10px' }}>
              <Text strong>CP:</Text>
              <Input 
                value={invoiceData.customer_zip || ''} 
                onChange={(e) => handleInvoiceFieldChange('customer_zip', e.target.value)}
                placeholder="Código Postal del cliente"
                style={{ width: '100%', marginTop: '5px' }}
              />
            </div>
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
      label: 'Procesar con IA',
      children: (
        <div>
          <Paragraph>
            Sube una factura en PDF o imagen para extraer los datos mediante IA avanzada y crearla/actualizarla en Odoo.
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
              Procesar con IA
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
      label: 'Método Estándar',
      children: (
        <div>
          <Paragraph>
            Sube una factura en PDF o imagen para extraer los datos mediante el método estándar y crearla/actualizarla en Odoo.
          </Paragraph>

          {/* Selección previa de proveedor */}
          <div style={{ marginBottom: 16 }}>
            <Title level={5}>Información del proveedor (opcional)</Title>
            <Paragraph type="secondary">
              Proporcionar esta información mejorará la precisión del OCR
            </Paragraph>
            
            <div style={{ display: 'flex', gap: '16px', marginBottom: '16px' }}>
              <div style={{ flex: 2 }}>
                <label>Seleccionar proveedor:</label>
                <Select
                  placeholder="Selecciona un proveedor"
                  style={{ width: '100%' }}
                  value={selectedProvider}
                  onChange={(value) => {
                    setSelectedProvider(value);
                    // Actualizar el NIF/CIF cuando se selecciona un proveedor
                    const provider = providers.find(p => p.id === value);
                    if (provider?.vat) {
                      const formattedVat = formatNifCif(provider.vat);
                      setProviderVat(formattedVat);
                      validateProviderVat(formattedVat);
                    }
                  }}
                  loading={loadingProviders}
                  disabled={freeUploading}
                  showSearch
                  optionFilterProp="children"
                  filterOption={(input, option) =>
                    option?.children?.toString().toLowerCase().includes(input.toLowerCase()) ?? false
                  }
                >
                  {providers.map(provider => (
                    <Option key={provider.id} value={provider.id}>{provider.name}</Option>
                  ))}
                </Select>
              </div>
              
              <div style={{ flex: 1 }}>
                <label>NIF/CIF del proveedor:</label>
                <Input
                  placeholder="Ej: B12345678"
                  value={providerVat}
                  onChange={(e) => {
                    const value = e.target.value;
                    setProviderVat(value);
                    validateProviderVat(value);
                  }}
                  status={providerVat && !vatValidation.isValid ? 'error' : ''}
                  disabled={freeUploading}
                />
                {providerVat && !vatValidation.isValid && (
                  <div style={{ color: 'red', fontSize: '12px' }}>
                    {vatValidation.message || 'NIF/CIF inválido'}
                  </div>
                )}
                {providerVat && vatValidation.isValid && (
                  <div style={{ color: 'green', fontSize: '12px' }}>
                    NIF/CIF válido
                  </div>
                )}
              </div>
            </div>
          </div>

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
