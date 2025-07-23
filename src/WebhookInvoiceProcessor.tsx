import React, { useRef, useState } from 'react';
import { Card, Typography, Button, Upload, message, Progress, Input, Space, App, Alert, Divider } from 'antd';
import { UploadOutlined, SendOutlined, LinkOutlined } from '@ant-design/icons';
import { useOdoo } from './OdooContext';

const { Title, Paragraph, Text } = Typography;

const WebhookInvoiceProcessor: React.FC = () => {
  const { isAuthenticated, api } = useOdoo();
  const { message: messageApi } = App.useApp();
  const fileRef = useRef<File | null>(null);
  
  const [fileName, setFileName] = useState('');
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('');
  const [uploadedFileUrl, setUploadedFileUrl] = useState<string | null>(null);
  const [responseJson, setResponseJson] = useState<any>(null);
  const [invoiceUrl, setInvoiceUrl] = useState<string>('');
  const [processingWebhook, setProcessingWebhook] = useState(false);

  // URL del webhook de n8n
  const N8N_WEBHOOK_URL = 'http://localhost:5678/webhook/procesar-factura-url';

  // Función para subir el archivo al servidor temporal
  const handleUpload = async () => {
    if (!fileRef.current) {
      messageApi.error('Selecciona un archivo de factura (PDF).');
      return;
    }

    setUploading(true);
    setProgress(0);
    setStatus('Subiendo archivo...');
    setUploadedFileUrl(null);

    try {
      const formData = new FormData();
      formData.append('file', fileRef.current);

      // Subir el archivo a un endpoint temporal que devuelve una URL accesible
      const res = await api.post('/api/v1/files/upload-temp', formData, {
        onUploadProgress: (evt: any) => {
          const pct = Math.round((evt.loaded * 100) / (evt.total ?? 1));
          setProgress(pct);
        },
      });

      if (res.data?.url) {
        setUploadedFileUrl(res.data.url);
        setInvoiceUrl(res.data.url); // Auto-completar el campo de URL
        setStatus('Archivo subido correctamente. Ahora puedes procesarlo con el webhook.');
        messageApi.success('Archivo subido correctamente.');
      } else {
        throw new Error('No se recibió URL del servidor');
      }
    } catch (err: any) {
      console.error(err);
      setStatus('Error al subir el archivo');
      messageApi.error(err?.response?.data?.detail ?? err?.message ?? 'Error desconocido');
    } finally {
      setUploading(false);
    }
  };

  // Función para procesar la factura usando el webhook de n8n
  const processWithWebhook = async () => {
    if (!invoiceUrl) {
      messageApi.error('Ingresa una URL válida de factura.');
      return;
    }

    setProcessingWebhook(true);
    setStatus('Procesando factura con webhook...');
    setResponseJson(null);

    try {
      // Llamar al webhook de n8n con la URL de la factura
      const webhookUrl = `${N8N_WEBHOOK_URL}?url=${encodeURIComponent(invoiceUrl)}`;
      const res = await fetch(webhookUrl);
      
      if (!res.ok) {
        throw new Error(`Error ${res.status}: ${res.statusText}`);
      }
      
      const data = await res.json();
      setResponseJson(data);
      setStatus('Factura procesada correctamente con el webhook.');
      messageApi.success('Factura procesada correctamente.');
    } catch (err: any) {
      console.error(err);
      setStatus(`Error al procesar con webhook: ${err.message}`);
      messageApi.error(err.message || 'Error desconocido al procesar con webhook');
    } finally {
      setProcessingWebhook(false);
    }
  };

  // Manejar cambio de archivo
  const handleFileChange = (info: any) => {
    if (info.file.status === 'removed') {
      fileRef.current = null;
      setFileName('');
      return;
    }
    
    const file = info.file.originFileObj;
    if (file) {
      fileRef.current = file;
      setFileName(file.name);
    }
  };

  return (
    <Card title="Procesador de Facturas con Webhook" style={{ maxWidth: 800, margin: '0 auto' }}>
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        <Alert
          message="Procesamiento de Facturas con n8n"
          description="Esta herramienta te permite procesar facturas PDF utilizando el webhook de n8n. Puedes subir un archivo o proporcionar una URL directamente."
          type="info"
          showIcon
        />

        <Divider>Paso 1: Sube un archivo o proporciona una URL</Divider>
        
        <Space direction="vertical" style={{ width: '100%' }}>
          <Title level={5}>Subir archivo de factura</Title>
          <Upload
            beforeUpload={() => false}
            onChange={handleFileChange}
            maxCount={1}
            accept=".pdf"
            showUploadList={false}
          >
            <Button icon={<UploadOutlined />} disabled={uploading}>
              Seleccionar archivo
            </Button>
          </Upload>
          
          {fileName && (
            <Text type="secondary">Archivo seleccionado: {fileName}</Text>
          )}
          
          <Button 
            type="primary" 
            onClick={handleUpload} 
            loading={uploading} 
            disabled={!fileRef.current}
            style={{ marginTop: 8 }}
          >
            Subir archivo
          </Button>
          
          {uploading && <Progress percent={progress} status="active" />}
        </Space>

        <Divider>O</Divider>
        
        <Space direction="vertical" style={{ width: '100%' }}>
          <Title level={5}>URL de la factura</Title>
          <Paragraph type="secondary">
            Puedes ingresar una URL directa a un PDF de factura (Odoo, Dropbox, servidor local, etc.)
          </Paragraph>
          <Input
            placeholder="http://localhost:8069/es/my/invoices/62?access_token=4604e7d8-27bf-4153-aa21-138cce2ce9c2"
            value={invoiceUrl}
            onChange={(e) => setInvoiceUrl(e.target.value)}
            prefix={<LinkOutlined />}
            allowClear
          />
        </Space>

        <Divider>Paso 2: Procesar con webhook</Divider>
        
        <Button
          type="primary"
          icon={<SendOutlined />}
          onClick={processWithWebhook}
          loading={processingWebhook}
          disabled={!invoiceUrl}
          size="large"
          block
        >
          Procesar con webhook de n8n
        </Button>

        {status && (
          <Alert
            message="Estado"
            description={status}
            type={status.includes('Error') ? 'error' : 'success'}
            showIcon
          />
        )}

        {responseJson && (
          <Card title="Resultado del procesamiento" size="small">
            <pre style={{ maxHeight: 400, overflow: 'auto' }}>
              {JSON.stringify(responseJson, null, 2)}
            </pre>
          </Card>
        )}
      </Space>
    </Card>
  );
};

export default WebhookInvoiceProcessor;
