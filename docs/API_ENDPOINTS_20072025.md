# Documentación de Endpoints API ManusOdoo (20-07-2025)

## Autenticación

| Endpoint | Método | Descripción | Parámetros |
|----------|--------|-------------|------------|
| `/token` | POST | Obtener token JWT | `username`, `password` (admin/admin) |

## Productos

| Endpoint | Método | Descripción | Parámetros |
|----------|--------|-------------|------------|
| `/api/products` | GET | Listar productos | `page`, `limit`, `search` |
| `/api/products/{product_id}` | GET | Obtener producto por ID | - |
| `/api/products` | POST | Crear producto | Datos del producto |
| `/api/products/{product_id}` | PUT | Actualizar producto | Datos del producto |
| `/api/products/{product_id}` | DELETE | Eliminar producto | - |

## Proveedores

| Endpoint | Método | Descripción | Parámetros |
|----------|--------|-------------|------------|
| `/api/providers` | GET | Listar proveedores | `page`, `limit`, `search` |
| `/api/providers/all` | GET | Listar todos los proveedores | - |
| `/api/providers/{provider_id}` | GET | Obtener proveedor por ID | - |
| `/api/providers` | POST | Crear proveedor | Datos del proveedor |
| `/api/providers/{provider_id}` | PUT | Actualizar proveedor | Datos del proveedor |
| `/api/providers/{provider_id}` | DELETE | Eliminar proveedor | - |

## Importación Excel

| Endpoint | Método | Descripción | Parámetros |
|----------|--------|-------------|------------|
| `/api/excel-importer` | POST | Importar productos desde Excel | Archivo Excel |

## OCR de Facturas (Versión Pagada)

| Endpoint | Método | Descripción | Parámetros |
|----------|--------|-------------|------------|
| `/api/v1/mistral-ocr/process-invoice` | POST | Procesar factura con OCR | Archivo de factura |
| `/api/v1/mistral-ocr/process-document` | POST | Procesar documento genérico | Archivo de documento |
| `/api/v1/mistral-ocr/save-verified-invoice` | POST | Guardar factura verificada | Datos de factura |
| `/api/v1/mistral-ocr/process-verified-invoice` | POST | Procesar factura ya verificada | Datos de factura |
| `/api/v1/mistral-ocr/process-from-url` | POST | Procesar factura desde URL | URL de factura |
| `/api/v1/mistral-ocr/supported-formats` | GET | Obtener formatos soportados | - |

## OCR de Facturas (Versión Gratuita)

| Endpoint | Método | Descripción | Parámetros |
|----------|--------|-------------|------------|
| `/api/v1/mistral-free-ocr/process-invoice` | POST | Procesar factura con OCR gratuito | Archivo de factura |
| `/api/v1/mistral-free-ocr/create-invoice` | POST | Crear factura desde datos OCR | Datos de factura |
| `/api/v1/mistral-free-ocr/create-invoice-with-supplier` | POST | Crear factura con proveedor | Datos de factura y proveedor |

## Integración n8n

| Endpoint | Método | Descripción | Parámetros |
|----------|--------|-------------|------------|
| `/api/v1/n8n/workflows` | GET | Listar flujos de trabajo | - |
| `/api/v1/n8n/workflows/{workflow_id}/activate` | POST | Activar flujo de trabajo | - |
| `/api/v1/n8n/workflows/{workflow_id}/deactivate` | POST | Desactivar flujo de trabajo | - |
| `/api/v1/n8n/execute/ocr` | POST | Ejecutar flujo OCR | Datos para el flujo |
| `/api/v1/n8n/execute/llm-mcp` | POST | Ejecutar flujo LLM-MCP | Datos para el flujo |
| `/api/v1/n8n/executions` | GET | Listar ejecuciones | - |
| `/api/v1/n8n/executions/{execution_id}` | GET | Obtener detalles de ejecución | - |
| `/api/v1/n8n/status` | GET | Obtener estado de n8n | - |

## Facturas

| Endpoint | Método | Descripción | Parámetros |
|----------|--------|-------------|------------|
| `/api/import-ocr` | POST | Importar factura desde OCR | Datos de factura |
| `/api/purchase-orders/{po_id}/invoice` | POST | Crear factura desde orden de compra | Datos de factura |

## Interfaz Web

| Endpoint | Método | Descripción | Parámetros |
|----------|--------|-------------|------------|
| `/` | GET | Página principal | - |
| `/ocr` | GET | Interfaz OCR | - |
| `/mapeo` | GET | Interfaz de mapeo | - |
| `/docs-ui` | GET | Documentación UI | - |

## Estado del Sistema

| Endpoint | Método | Descripción | Parámetros |
|----------|--------|-------------|------------|
| `/health` | GET | Verificar estado de la API | - |

## Notas de Implementación

1. **Autenticación**: Todos los endpoints (excepto `/token` y `/health`) requieren autenticación JWT.
2. **Formato de Respuesta**: Todas las respuestas siguen el formato estándar:
   ```json
   {
     "success": true/false,
     "data": {...},
     "message": "Mensaje descriptivo",
     "errors": [...]
   }
   ```
3. **Paginación**: Los endpoints que devuelven listas soportan paginación con parámetros `page` y `limit`.
4. **Búsqueda**: Muchos endpoints soportan búsqueda con el parámetro `search`.
5. **Caché OCR**: El sistema de caché OCR está implementado pero actualmente desactivado en el código.
6. **Validación**: Se implementa validación de datos en todos los endpoints POST y PUT.

## Ejemplos de Uso

### Autenticación
```bash
curl -X POST http://localhost:8000/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin"
```

### Listar Productos
```bash
curl -X GET http://localhost:8000/api/products \
  -H "Authorization: Bearer {token}"
```

### Procesar Factura OCR
```bash
curl -X POST http://localhost:8000/api/v1/mistral-ocr/process-invoice \
  -H "Authorization: Bearer {token}" \
  -F "file=@factura.pdf"
```
