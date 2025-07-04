import React, { useRef, useState } from 'react';
import { Card, Typography, Input, Checkbox, Button, Progress, message } from 'antd';

import { useOdoo } from '../OdooContext';

const { Title, Paragraph } = Typography;

const ImportInvoice: React.FC = () => {
  const { isAuthenticated, auth, api, login } = useOdoo();
  const fileRef = useRef<File | null>(null);

  const [fileName, setFileName] = useState('');
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('');
  const [createInOdoo, setCreateInOdoo] = useState(true);
  const [responseJson, setResponseJson] = useState<any>(null);

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const handleUpload = async () => {
    if (!fileRef.current) {
      message.error('Selecciona un archivo de factura (PDF / imagen).');
      return;
    }

    // Renovar/asegurar token antes de llamar al backend
    const ok = await login(
      import.meta.env.VITE_ODOO_USERNAME || 'yo@mail.com',
      import.meta.env.VITE_ODOO_PASSWORD || 'admin'
    );
    if (!ok && !isAuthenticated) {
      message.error('No se pudo autenticar con el backend.');
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
          onUploadProgress: (evt) => {
            const pct = Math.round((evt.loaded * 100) / (evt.total ?? 1));
            setProgress(pct);
          },
        },
      );

      setResponseJson(res.data);
      setStatus('Factura procesada correctamente.');
      message.success('Factura procesada.');
    } catch (err: any) {
      console.error(err);
      setStatus('Error al procesar la factura');
      message.error(err?.response?.data?.detail ?? err?.message ?? 'Error desconocido');
    } finally {
      setUploading(false);
    }
  };

  return (
    <Card style={{ maxWidth: 800, margin: '20px auto' }}>
      <Title level={3}>Procesar Factura</Title>
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

      {responseJson && (
        <pre style={{ background: '#1e1e1e', color: '#bfbfbf', padding: 12, marginTop: 16 }}>
          {JSON.stringify(responseJson, null, 2)}
        </pre>
      )}
    </Card>
  );
};

export default ImportInvoice;
