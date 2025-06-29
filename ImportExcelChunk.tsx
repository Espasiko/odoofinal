import React, { useState } from 'react';
import { Upload, Button, message, Progress, Card, Typography, List, Input } from 'antd';
import type { UploadFile, UploadProps } from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import axios, { AxiosProgressEvent } from 'axios';
import { useOdoo } from './OdooContext';

const { Title, Text } = Typography;

// --- Type Definitions for Clarity and Type Safety ---

interface CreatedProduct {
  id: number;
  name: string;
}

interface FailedProduct {
  name: string;
  error: string;
}

interface ImportResults {
  productos_creados: CreatedProduct[];
  productos_fallidos: FailedProduct[];
  total_intentados: number;
  total_creados: number;
  total_fallidos: number;
}

interface HttpValidationError {
  detail?: {
    loc: (string | number)[];
    msg: string;
    type: string;
  }[];
}

const ImportExcelChunk = () => {
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [providerName, setProviderName] = useState<string>('');
  const [uploading, setUploading] = useState<boolean>(false);
  const [progress, setProgress] = useState<number>(0);
  const [status, setStatus] = useState<string>('');
  const [results, setResults] = useState<ImportResults>({
    productos_creados: [],
    productos_fallidos: [],
    total_intentados: 0,
    total_creados: 0,
    total_fallidos: 0,
  });

  const { auth } = useOdoo();
  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const handleUpload = async () => {
    if (fileList.length === 0) {
      message.error('Por favor, selecciona un archivo Excel primero.');
      return;
    }
    if (!providerName.trim()) {
      message.error('Por favor, introduce el nombre del proveedor.');
      return;
    }
    if (!auth?.accessToken) {
      message.error('Error de autenticación: No se encontró el token de acceso. Por favor, refresca la página o vuelve a iniciar sesión.');
      return;
    }

    setUploading(true);
    setProgress(0);
    setStatus('Subiendo archivo...');
    setResults({ productos_creados: [], productos_fallidos: [], total_intentados: 0, total_creados: 0, total_fallidos: 0 });

    const formData = new FormData();
    const file = fileList[0]?.originFileObj;
    if (file) {
      formData.append('file', file as Blob);
    } else {
      message.error("No se pudo acceder al archivo seleccionado. Por favor, selecciónalo de nuevo.");
      setUploading(false);
      return;
    }
    
    formData.append('start_row', '0');
    formData.append('chunk_size', '25');
    formData.append('proveedor_nombre', providerName.trim());

    try {
      const response = await axios.post<ImportResults>(
        `${API_URL}/api/v1/mistral-llm/process-excel`,
        formData,
        {
          headers: {
            'Authorization': `Bearer ${auth.accessToken}`,
          },
          onUploadProgress: (progressEvent: AxiosProgressEvent) => {
            if (progressEvent.total) {
              const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
              setProgress(percentCompleted);
              setStatus(percentCompleted === 100 ? 'Procesando datos...' : `Subiendo: ${percentCompleted}%`);
            }
          },
        }
      );

      if (response.data) {
        setStatus(`Procesamiento completado. Productos creados: ${response.data.total_creados} / ${response.data.total_intentados}`);
        setResults(response.data);
      }
    } catch (error) {
      console.error('Error durante la importación:', error);
      setStatus('Error en la importación.');
      if (axios.isAxiosError<HttpValidationError>(error) && error.response) {
        const errorMsg = error.response.data?.detail?.[0]?.msg || 'Revisa la consola para más detalles.';
        message.error(`Error del servidor: ${error.response.status}. ${errorMsg}`);
      } else {
        message.error('Ha ocurrido un error inesperado. Revisa la consola para más detalles.');
      }
    } finally {
      setUploading(false);
    }
  };

  const props: UploadProps = {
    onRemove: (file: UploadFile) => {
      const index = fileList.indexOf(file);
      const newFileList = fileList.slice();
      newFileList.splice(index, 1);
      setFileList(newFileList);
    },
    beforeUpload: (file: UploadFile) => {
      setFileList([file]);
      return false; // Prevent automatic upload
    },
    fileList,
    accept: '.xlsx, .xls',
    multiple: false,
    maxCount: 1,
  };

  return (
    <Card title="Importar Productos desde Excel por Chunks">
      <div className="upload-section" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <Input
          placeholder="Nombre del Proveedor (obligatorio)"
          value={providerName}
          onChange={(e) => setProviderName(e.target.value)}
          disabled={uploading}
        />
        <Upload {...props}>
          <Button icon={<UploadOutlined />} style={{ width: '100%' }}>Seleccionar Archivo Excel</Button>
        </Upload>
        <Button
          type="primary"
          onClick={handleUpload}
          disabled={fileList.length === 0 || uploading || !providerName.trim()}
        >
          {uploading ? 'Procesando...' : 'Subir y Procesar'}
        </Button>
      </div>
      {status && (
        <div style={{ marginTop: 20 }}>
          <Text strong>Estado: </Text>
          <Text>{status}</Text>
          {progress > 0 && <Progress percent={progress} style={{ marginTop: 8 }} />}
        </div>
      )}
      {results.total_intentados > 0 && (
        <div style={{ marginTop: 20 }}>
          <Title level={4}>Resultados de la Importación</Title>
          <Text strong>Total Intentados: </Text><Text>{results.total_intentados}</Text><br />
          <Text strong>Total Creados: </Text><Text style={{ color: 'green' }}>{results.total_creados}</Text><br />
          <Text strong>Total Fallidos: </Text><Text style={{ color: 'red' }}>{results.total_fallidos}</Text><br />
          {results.productos_creados.length > 0 && (
            <div>
              <Title level={5}>Productos Creados:</Title>
              <List
                size="small"
                bordered
                dataSource={results.productos_creados}
                renderItem={(item: CreatedProduct) => <List.Item>{item.name} (ID: {item.id})</List.Item>}
                style={{ marginTop: 8, maxHeight: 200, overflowY: 'auto' }}
              />
            </div>
          )}
          {results.productos_fallidos.length > 0 && (
            <div>
              <Title level={5}>Productos Fallidos:</Title>
              <List
                size="small"
                bordered
                dataSource={results.productos_fallidos}
                renderItem={(item: FailedProduct) => <List.Item>{item.name} - Error: {item.error}</List.Item>}
                style={{ marginTop: 8, maxHeight: 200, overflowY: 'auto' }}
              />
            </div>
          )}
        </div>
      )}
    </Card>
  );
};

export default ImportExcelChunk;
