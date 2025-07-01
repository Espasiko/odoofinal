// NUEVO COMPONENTE SIMPLIFICADO
import React, { useState, useRef } from 'react';
import { Button, Card, Input, List, message, Progress, Typography } from 'antd';
import axios from 'axios';
import { useOdoo } from '../OdooContext';

const { Title, Text } = Typography;

interface ProductInfo {
  id: number;
  name: string;
  error?: string;
}
interface ImportResult {
  created: ProductInfo[];
  failed: ProductInfo[];
  totalIntentados: number;
  totalCreados: number;
  totalFallidos: number;
}

const ImportExcelChunk: React.FC = () => {
  const fileRef = useRef<File | null>(null);
  const [fileName, setFileName] = useState<string>('');
  
  const [providerName, setProviderName] = useState('');
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('');
  const [results, setResults] = useState<ImportResult>({
    created: [],
    failed: [],
    totalIntentados: 0,
    totalCreados: 0,
    totalFallidos: 0,
  });

  const { auth, api, isAuthenticated } = useOdoo();
  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const handleUpload = async () => {
    if (!isAuthenticated) {
      message.loading('Obteniendo token…', 1);
      // Espera breve a que el interceptor complete la solicitud de token
      await new Promise(r => setTimeout(r, 1200));
      if (!isAuthenticated) {
        message.error('No se pudo obtener token. Intenta de nuevo en unos segundos.');
        return;
      }
    }
    if (!fileRef.current) {
      message.error('Selecciona un archivo Excel primero.');
      return;
    }
    if (!providerName.trim()) {
      message.error('Introduce el nombre del proveedor.');
      return;
    }

    setUploading(true);
    setStatus('Subiendo archivo...');
    setProgress(0);

    const formData = new FormData();
    formData.append('file', fileRef.current);
    formData.append('start_row', '0');
    formData.append('chunk_size', '25');
    formData.append('proveedor_nombre', providerName.trim());

    try {
      const res = await api.post(`${API_URL}/api/v1/mistral-llm/process-excel`, formData, {
        headers: {
          
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (evt) => {
          const pct = Math.round((evt.loaded * 100) / (evt.total ?? 1));
          setProgress(pct);
          setStatus(pct === 100 ? 'Procesando datos…' : `Subiendo: ${pct}%`);
        },
      });

      const d = res.data;
      setResults({
        created: d.productos_creados ?? [],
        failed: d.productos_fallidos ?? [],
        totalIntentados: d.total_intentados ?? 0,
        totalCreados: d.total_creados ?? 0,
        totalFallidos: d.total_fallidos ?? 0,
      });
      setStatus('Importación completada.');
      message.success(`Creados: ${d.total_creados}, fallidos: ${d.total_fallidos}`);
    } catch (err: any) {
      console.error(err);
      setStatus('Error durante la importación');
      message.error(err?.message ?? 'Error desconocido');
    } finally {
      setUploading(false);
    }
  };

  return (
    <Card style={{ maxWidth: 800, margin: '20px auto' }}>
      <Title level={3}>Importar Productos desde Excel</Title>

      <Input
        placeholder="Nombre del Proveedor (obligatorio)"
        value={providerName}
        onChange={(e) => setProviderName(e.target.value)}
        disabled={uploading}
        style={{ marginBottom: 12 }}
      />

      <input
        type="file"
        accept=".xlsx,.xls"
        onChange={(e) => {
          fileRef.current = e.target.files?.[0] ?? null;
          const f = e.target.files?.[0] ?? null;
          setFileName(fileRef.current?.name ?? '');
          if (fileRef.current) {
            setStatus('Archivo seleccionado.');
          }
        }}
        disabled={uploading}
      />

      <Button
        type="primary"
        onClick={handleUpload}
        disabled={!fileRef.current || !providerName.trim() || uploading}
        style={{ marginTop: 16 }}
      >
        {uploading ? 'Procesando…' : 'Subir y Procesar'}
      </Button>

      {status && (
        <div style={{ marginTop: 16 }}>
          <Text strong>Estado: </Text>
          <Text>{status}</Text>
          {progress > 0 && <Progress percent={progress} style={{ marginTop: 8 }} />}
        </div>
      )}

      {results.totalIntentados > 0 && (
        <div style={{ marginTop: 20 }}>
          <Title level={4}>Resultados</Title>
          <p>
            Intentados: {results.totalIntentados} | Creados:{' '}
            <span style={{ color: 'green' }}>{results.totalCreados}</span> | Fallidos:{' '}
            <span style={{ color: 'red' }}>{results.totalFallidos}</span>
          </p>

          {results.created.length > 0 && (
            <>
              <Text strong>Productos creados</Text>
              <List
                size="small"
                bordered
                dataSource={results.created}
                renderItem={(it) => <List.Item>{it.name} (ID: {it.id})</List.Item>}
                style={{ margin: '8px 0', maxHeight: 200, overflowY: 'auto' }}
              />
            </>
          )}

          {results.failed.length > 0 && (
            <>
              <Text strong>Productos fallidos</Text>
              <List
                size="small"
                bordered
                dataSource={results.failed}
                renderItem={(it) => <List.Item>{it.name} - Error: {it.error}</List.Item>}
                style={{ margin: '8px 0', maxHeight: 200, overflowY: 'auto' }}
              />
            </>
          )}
        </div>
      )}
    </Card>
  );
};

export default ImportExcelChunk;