# Memoria del Flujo Completo de Creación de Facturas con Mistral Free OCR - 11/01/2025

## Resumen Ejecutivo

Este documento detalla el análisis completo del sistema de creación de facturas utilizando OCR (Reconocimiento Óptico de Caracteres) con Mistral AI en el proyecto Manusodoo-Roto.

## Arquitectura del Sistema

El sistema utiliza una arquitectura de tres capas:

1. **Frontend React** (Puerto 3001) - `src/ImportInvoice.tsx`
2. **Backend FastAPI** (Puerto 8000) - `api/routes/mistral_free_ocr.py`
3. **Odoo 18** (Puerto 8069) - Servicios de integración

## Componentes Principales

### 1. Frontend - ImportInvoice.tsx

**Ubicación**: `/home/espasiko/mainmanusodoo/manusodoo-roto/src/ImportInvoice.tsx`

**Funcionalidades**:
- Dos métodos de procesamiento: Método Estándar y Mistral Free OCR (pestañas separadas)
- Subida de archivos: Acepta PDF, JPG, JPEG, PNG
- Opciones de configuración: Checkbox para crear automáticamente en Odoo
- Visualización de progreso: Barra de progreso durante el procesamiento
- Edición de datos: Campos editables para todos los datos extraídos
- Selección manual de proveedor: Dropdown con proveedores existentes
- Gestión de líneas de factura: Tabla editable con descripción, cantidad, precio, código y subtotal

**Estados principales**:
```typescript
const [uploading, setUploading] = useState(false);
const [freeUploading, setFreeUploading] = useState(false);
const [responseJson, setResponseJson] = useState<any>(null);
const [freeResponseJson, setFreeResponseJson] = useState<any>(null);
const [editableInvoiceData, setEditableInvoiceData] = useState<any>(null);
const [providers, setProviders] = useState<Provider[]>([]);
const [selectedProvider, setSelectedProvider] = useState<number | null>(null);
```

### 2. Backend - Mistral Free OCR Service

**Ubicación**: `/home/espasiko/mainmanusodoo/manusodoo-roto/api/routes/mistral_free_ocr.py`

**Endpoints principales**:
- `POST /api/v1/mistral-free-ocr/process-invoice` - Procesamiento inicial
- `POST /api/v1/mistral-free-ocr/create-invoice` - Creación con proveedor manual

**Funcionalidades**:
- Validación de archivos (formato y tamaño máximo 50MB)
- Procesamiento OCR con modelo Pixtral-12b-2409
- Extracción estructurada de datos de facturas
- Guardado de resultados en JSON
- Creación automática de proveedores y facturas

### 3. Servicio OCR - MistralFreeOCRService

**Ubicación**: `/home/espasiko/mainmanusodoo/manusodoo-roto/api/services/mistral_free_ocr_service.py`

**Características**:
- Conversión de PDFs a imágenes temporales
- Codificación base64 para envío a API
- Modelo especializado: Pixtral-12b-2409
- Prompt estructurado para extracción de datos
- Agente especializado para mejora de datos
- Modelos Pydantic: `InvoiceLine` y `OdooInvoice`

### 4. Integración con Odoo

**Servicios de integración**:

#### OdooProviderService
**Ubicación**: `/home/espasiko/mainmanusodoo/manusodoo-roto/api/services/odoo_provider_service.py`
- Búsqueda por NIF/VAT o nombre
- Creación automática con `create_supplier()`
- Actualización de datos existentes

#### OdooInvoiceService
**Ubicación**: `/home/espasiko/mainmanusodoo/manusodoo-roto/api/services/odoo_invoice_service.py`
- Creación con `create_supplier_invoice()`
- Manejo de duplicados
- Asociación automática de productos
- Aplicación de impuestos (21% y 5.2% recargo)

## Flujo Detallado del Proceso

### 1. Subida y Procesamiento Inicial
1. Usuario selecciona archivo en `ImportInvoice.tsx`
2. Frontend envía archivo a `/api/v1/mistral-free-ocr/process-invoice`
3. Backend valida formato y tamaño
4. `MistralFreeOCRService` procesa con OCR
5. Datos extraídos se guardan en JSON
6. Respuesta enviada al frontend

### 2. Visualización y Edición
1. Frontend muestra datos extraídos en campos editables
2. Usuario puede modificar cualquier campo
3. Sistema busca proveedor coincidente automáticamente
4. Usuario puede seleccionar proveedor manualmente

### 3. Creación en Odoo
1. Usuario confirma datos y selecciona proveedor
2. Frontend envía a `/api/v1/mistral-free-ocr/create-invoice`
3. Backend valida existencia del proveedor
4. Se preparan líneas de factura
5. Se crea factura en Odoo con `create_supplier_invoice()`
6. Se registra trazabilidad en CSV

## Características Avanzadas

### Corrección Manual
- Endpoint `/create-invoice` para proveedor seleccionado manualmente
- Validación de proveedor antes de crear factura
- Todos los campos editables antes de creación
- Opción de actualización de facturas existentes

### Trazabilidad y Logging
- Registro detallado en logs
- Guardado de datos OCR en archivos JSON
- Registro de inserciones en CSV
- Manejo robusto de errores

### Seguridad
- Autenticación JWT en todas las operaciones
- Validación de formatos de archivo
- Límites de tamaño de archivo
- Sanitización de datos de entrada

## Ventajas del Sistema

1. **Flexibilidad**: Dos métodos de procesamiento disponibles
2. **Edición completa**: Todos los datos modificables antes de crear
3. **Integración robusta**: Manejo completo de proveedores y productos
4. **Interfaz intuitiva**: Pestañas separadas y organización clara
5. **Corrección manual**: Selección de proveedor cuando IA falla
6. **Trazabilidad completa**: Registro de todas las operaciones

## Archivos de Configuración

### Variables de Entorno
- `MISTRAL_API_KEY`: Clave API para Mistral
- `VITE_API_URL`: URL del backend (por defecto http://localhost:8000)
- `VITE_ODOO_USERNAME`: Usuario de Odoo
- `VITE_ODOO_PASSWORD`: Contraseña de Odoo

### Puertos Utilizados
- Frontend React: 3001
- Backend FastAPI: 8000
- Odoo: 8069

## Archivos de Datos OCR

Los datos procesados se guardan en:
`/home/espasiko/mainmanusodoo/manusodoo-roto/api/ocr_data/`

Formato: `YYYYMMDDHHMMSS_[numero_factura]_free.json`

## Próximos Pasos y Mejoras

1. Mejoras en validación de datos
2. Interfaz más intuitiva
3. Soporte para facturas rectificativas
4. Manejo de múltiples monedas
5. Integración con más proveedores de OCR

## Conclusión

El sistema proporciona una solución completa y robusta para la digitalización y procesamiento automático de facturas con capacidades avanzadas de corrección y validación manual. La arquitectura modular permite fácil mantenimiento y extensión de funcionalidades.

---

**Fecha de creación**: 11 de enero de 2025
**Versión del sistema**: Odoo 18 + FastAPI + React
**Estado**: Funcional y en producción