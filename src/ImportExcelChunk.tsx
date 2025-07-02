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

  const { auth, api, isAuthenticated, login } = useOdoo();
  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const CHUNK_SIZE = 50;
  const RATE_LIMIT_MS = 12000; // 5 req/min

  const handleUpload = async () => {
    // Renovar token justo antes de empezar (evita expiración a mitad de proceso)
    const ok = await login(
      import.meta.env.VITE_ODOO_USERNAME || 'yo@mail.com',
      import.meta.env.VITE_ODOO_PASSWORD || 'admin'
    );
    if (!ok) {
      message.error('No se pudo obtener token. Intenta de nuevo en unos segundos.');
      return;
    }
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
      message.error('Debes indicar el nombre del proveedor');
      return;
    }
    if (!isAuthenticated || !auth?.accessToken) {
      message.error('No se ha podido autenticar con el backend. Intenta de nuevo más tarde.');
      return;
    }

    setUploading(true);
    setStatus('Subiendo archivo...');
    setProgress(0);

    let startRow = 0;

    try {
      let totalCreated = 0;
      let totalFailed = 0;
      let keepGoing = true;

      while (keepGoing) {
        const formData = new FormData();
        formData.append('file', fileRef.current!);
        formData.append('start_row', String(startRow));
        formData.append('chunk_size', String(CHUNK_SIZE));
        formData.append('proveedor_nombre', providerName.trim());
        formData.append('only_first_sheet', 'false');

        const res = await api.post(`${API_URL}/api/v1/mistral-llm/process-excel`, formData, {
          onUploadProgress: (evt) => {
            const pct = Math.round((evt.loaded * 100) / (evt.total ?? 1));
            setProgress(pct);
            setStatus(pct === 100 ? 'Procesando datos…' : `Subiendo filas: ${pct}%`);
          },
        });

        const d = res.data;
        totalCreated += d.total_creados ?? 0;
        totalFailed += d.total_fallidos ?? 0;

        setResults(prev => ({
          created: [...(prev?.created ?? []), ...(d.productos_creados ?? [])],
          failed: [...(prev?.failed ?? []), ...(d.productos_fallidos ?? [])],
          totalIntentados: (prev?.totalIntentados ?? 0) + (d.total_intentados ?? 0),
          totalCreados: totalCreated,
          totalFallidos: totalFailed,
        }));

        if ((d.total_intentados ?? 0) === 0) {
          // El backend no encontró más productos en este bloque
          keepGoing = false;
          setStatus('Importación completada.');
          message.success(`Creados: ${totalCreated}, fallidos: ${totalFailed}`);
        } else {
          startRow += CHUNK_SIZE;
          setStatus('Esperando para continuar…');
          await new Promise(res => setTimeout(res, RATE_LIMIT_MS));
        }
      }
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