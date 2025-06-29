import React, { useState, useEffect } from 'react';
import { Upload, Button, message, Progress, Card, Typography, List, Input } from 'antd';
import { UploadOutlined } from '@ant-design/icons';
import axios from 'axios';

import { useOdoo } from '../OdooContext';

const { Title, Text } = Typography;

const ImportExcelChunk = () => {
  const [fileList, setFileList] = useState([]);
  const [providerName, setProviderName] = useState('');
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('');
  const [results, setResults] = useState({ created: [], failed: [], totalIntentados: 0, totalCreados: 0, totalFallidos: 0 });
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

    setUploading(true);
    setProgress(0);
    setStatus('Subiendo archivo...');
    setResults({ created: [], failed: [], totalIntentados: 0, totalCreados: 0, totalFallidos: 0 });

    const formData = new FormData();
    formData.append('file', fileList[0].originFileObj);
    formData.append('start_row', '0');
    formData.append('chunk_size', '25');
    formData.append('proveedor_nombre', providerName.trim());

    try {
      const response = await axios.post(
        `${API_URL}/api/v1/mistral-llm/process-excel`,
        formData,
        {
          headers: {
            'Authorization': `Bearer ${auth.accessToken}`,
            'Content-Type': 'multipart/form-data',
          },
          onUploadProgress: (progressEvent) => {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setProgress(percentCompleted);
            setStatus(percentCompleted === 100 ? 'Procesando datos...' : `Subiendo: ${percentCompleted}%`);
          },
        }
      );

      if (response.data) {
        setStatus(`Procesamiento completado. Productos creados: ${response.data.total_creados}, Fallidos: ${response.data.total_fallidos}`);
        setResults({
          created: response.data.productos_creados || [],
          failed: response.data.productos_fallidos || [],
          totalIntentados: response.data.total_intentados || 0,
          totalCreados: response.data.total_creados || 0,
          totalFallidos: response.data.total_fallidos || 0
        });
        message.success(`Importación completada. Productos creados: ${response.data.total_creados}`);
      } else {
        setStatus('Error en la respuesta del servidor.');
        message.error('Error en la respuesta del servidor.');
      }
    } catch (error) {
      console.error('Error durante la importación:', error);
      setStatus('Error durante la importación.');
      message.error(`Error durante la importación: ${error.message}`);
    } finally {
      setUploading(false);
    }
  };

  const uploadProps = {
    onRemove: (file) => {
      setFileList([]);
      setProgress(0);
      setStatus('');
      setResults({ created: [], failed: [], totalIntentados: 0, totalCreados: 0, totalFallidos: 0 });
    },
    beforeUpload: (file) => {
      const isExcel = file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' || 
                      file.type === 'application/vnd.ms-excel';
      if (!isExcel) {
        message.error('Solo se permiten archivos Excel (.xlsx, .xls).');
        return false;
      }
      setFileList([file]);
      setProgress(0);
      setStatus('Archivo seleccionado. Haz clic en "Subir y Procesar" para continuar.');
      return false; // Evita la subida automática
    },
    fileList,
    accept: '.xlsx, .xls',
    multiple: false,
  };

  return (
    <Card style={{ maxWidth: 800, margin: '20px auto' }}>
      <Title level={3}>Importar Productos desde Excel (Procesamiento por Chunks)</Title>
      <Text>Selecciona un archivo Excel para procesar e importar productos a Odoo por chunks.</Text>
      <div style={{ marginTop: 16 }}>
        <Input
          placeholder="Nombre del Proveedor (obligatorio)"
          value={providerName}
          onChange={(e) => setProviderName(e.target.value)}
          disabled={uploading}
        />
        <Upload {...uploadProps}>
          <Button icon={<UploadOutlined />}>Seleccionar Archivo Excel</Button>
        </Upload>
        <Button
          type="primary"
          onClick={handleUpload}
          disabled={fileList.length === 0 || uploading || !providerName.trim()}
          style={{ marginTop: 16 }}
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
      {results.totalIntentados > 0 && (
        <div style={{ marginTop: 20 }}>
          <Title level={4}>Resultados de la Importación</Title>
          <Text strong>Total Intentados: </Text><Text>{results.totalIntentados}</Text><br />
          <Text strong>Total Creados: </Text><Text style={{ color: 'green' }}>{results.totalCreados}</Text><br />
          <Text strong>Total Fallidos: </Text><Text style={{ color: 'red' }}>{results.totalFallidos}</Text><br />
          {results.created.length > 0 && (
            <div>
              <Title level={5}>Productos Creados:</Title>
              <List
                size="small"
                bordered
                dataSource={results.created}
                renderItem={item => <List.Item>{item.name} (ID: {item.id})</List.Item>}
                style={{ marginTop: 8, maxHeight: 200, overflowY: 'auto' }}
              />
            </div>
          )}
          {results.failed.length > 0 && (
            <div>
              <Title level={5}>Productos Fallidos:</Title>
              <List
                size="small"
                bordered
                dataSource={results.failed}
                renderItem={item => <List.Item>{item.name} - Error: {item.error}</List.Item>}
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
