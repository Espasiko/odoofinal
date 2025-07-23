# Estructura del Proyecto Manusodoo-Roto

## 1. Arquitectura General

El proyecto consiste en una integración entre Odoo 18 y una aplicación web personalizada, utilizando FastAPI como backend y React como frontend. La arquitectura está basada en contenedores Docker para facilitar el despliegue y la escalabilidad.

### Componentes Principales:

```
manusodoo-roto/
├── api/                    # Backend FastAPI
│   ├── models/             # Modelos de datos y esquemas Pydantic
│   ├── routes/             # Endpoints de la API
│   ├── services/           # Servicios de negocio y conexión con Odoo
│   └── utils/              # Utilidades y configuración
├── src/                    # Frontend React
│   ├── components/         # Componentes React reutilizables
│   ├── hooks/              # Hooks personalizados
│   ├── pages/              # Páginas de la aplicación
│   └── services/           # Servicios para comunicación con la API
├── config/                 # Configuración de Odoo
├── n8n/                    # Workflows de automatización n8n
│   ├── flujos/             # Workflows JSON exportados
│   └── docker-compose.yml  # Configuración n8n (DEPRECADO - migrado al principal)
├── addons/                 # Módulos personalizados para Odoo
│   ├── app_barcode          # Módulo para gestión de códigos de barras
│   ├── auto_database_backup # Módulo para respaldo automático de la base de datos
│   ├── odoo_turbo_ai_agent  # Integración de IA con Odoo
│   ├── pelotazo_extended    # Personalizaciones específicas para El Pelotazo
│   ├── purchase-workflow    # Flujos de trabajo de compras personalizados
│   ├── rest-framework       # Framework REST para Odoo
│   └── theme_pelotazo       # Tema personalizado para la tienda
└── docker-compose.yml      # Configuración de contenedores
```
el front esta hecho con react y vite , comandos: npm run dev , docker-compose o start.sh, script para levantar  todos los contenedores  n8n tiene su contendor tambien. lea el grafo de MCP knowledge graph para mas informacion. 
## 2. Credenciales de Acceso

### Base de Datos PostgreSQL:
- **Host**: localhost
- **Puerto**: 5432 (interno), 5434 (externo)
- **Base de Datos**: fresh_odoo_db
- **Usuario PostgreSQL**: odoo
- **Contraseña PostgreSQL**: odoo

### Usuario Administrador Odoo:
- **Email/Usuario**: admin
- **Contraseña**: admin
- **Nombre**: El pelotazo
- **ID de Usuario**: 2

### URLs de Acceso:
- **Odoo Web**: http://localhost:8069
- **Adminer (DB Manager)**: http://localhost:8080
- **FastAPI Backend**: http://localhost:8000
- **Frontend React**: http://localhost:3001
- **n8n Workflows**: http://localhost:5678

## 3. Estructura de Contenedores

El proyecto utiliza Docker Compose para gestionar los siguientes contenedores:

### 1. PostgreSQL (db)
- **Imagen**: postgres:15
- **Puertos**: 5432:5432
- **Volúmenes**: odoo-db-data
- **Configuración**: Base de datos para Odoo con usuario y contraseña "odoo"

### 2. Odoo (odoo)
- **Imagen**: odoo:18.0
- **Puertos**: 8069:8069
- **Volúmenes**: 
  - odoo-web-data: Para datos de Odoo
  - ./config: Configuración de Odoo
  - ./addons: Módulos personalizados
- **Comando**: odoo --xmlrpc-interface=0.0.0.0
- **Dependencias**: Requiere que el contenedor db esté saludable

### 3. Adminer (adminer)
- **Imagen**: adminer
- **Puertos**: 8080:8080
- **Función**: Gestión de la base de datos PostgreSQL a través de interfaz web

### 4. FastAPI (fastapi)
- **Construcción**: Dockerfile.fastapi
- **Puertos**: 8000:8000
- **Volúmenes**: ./ montado en /app
- **Variables de entorno**: Configuradas desde .env
- **Comando**: uvicorn main:app --reload --host 0.0.0.0 --port 8000
- **Dependencias**: Requiere que el contenedor odoo esté saludable

## 4. Backend (FastAPI)

### Estructura de Directorios:

```
api/
├── models/                 # Modelos de datos
│   ├── schemas.py          # Esquemas Pydantic para validación
│   ├── invoice_models.py   # Modelos para facturas
│   └── provider_*.py       # Modelos para proveedores
├── routes/                 # Endpoints de la API
│   ├── auth.py             # Autenticación
│   ├── products.py         # Gestión de productos
│   ├── providers.py        # Gestión de proveedores
│   ├── invoices.py         # Gestión de facturas
│   ├── mistral_ocr.py      # Integración con OCR Mistral
│   ├── mistral_llm_excel.py # Procesamiento de Excel con LLM
│   └── excel_importer.py   # Importación de Excel
├── services/               # Servicios de negocio
│   ├── odoo_base_service.py # Servicio base para Odoo
│   ├── odoo_product_service.py # Servicio para productos
│   ├── odoo_provider_service.py # Servicio para proveedores
│   ├── odoo_invoice_service.py # Servicio para facturas
│   ├── auth_service.py     # Servicio de autenticación
│   └── product_lookup.py   # Búsqueda de productos
└── utils/                  # Utilidades
    ├── config.py           # Configuración
    ├── mistral_llm_utils.py # Utilidades para Mistral LLM
    ├── parsing.py          # Análisis de datos
    └── price_utils.py      # Utilidades para precios
```

### Endpoints Principales:

- **/api/v1/products**: CRUD de productos
- **/api/v1/providers**: CRUD de proveedores
- **/api/v1/invoices**: Gestión de facturas
- **/api/v1/mistral-ocr**: Procesamiento OCR con Mistral
- **/api/v1/mistral-llm**: Procesamiento de Excel con LLM
- **/api/v1/excel-import**: Importación de Excel
- **/token**: Autenticación OAuth2
endpoints disponibles 22 07: 
POST   /token
GET    /session
GET    /api/v1/products
POST   /api/v1/products
GET    /api/v1/products/{product_id}
PUT    /api/v1/products/{product_id}
DELETE /api/v1/products/{product_id}
GET    /api/v1/providers
POST   /api/v1/providers
GET    /api/v1/providers/all
GET    /api/v1/providers/{provider_id}
PUT    /api/v1/providers/{provider_id}
DELETE /api/v1/providers/{provider_id}
POST   /api/v1/mistral-ocr/save-verified-invoice
POST   /api/v1/mistral-ocr/process-document
POST   /api/v1/mistral-ocr/process-invoice
POST   /api/v1/mistral-ocr/process-verified-invoice
POST   /api/v1/mistral-ocr/process-from-url
GET    /api/v1/mistral-ocr/supported-formats
POST   /api/v1/mistral-free-ocr/process-invoice
POST   /api/v1/mistral-free-ocr/create-invoice-with-supplier
POST   /api/v1/mistral-free-ocr/create-invoice
POST   /api/v1/invoices/import-ocr
POST   /api/v1/invoices/purchase-orders/{po_id}/invoice
POST   /api/v1/files/upload-temp
POST   /api/v1/n8n/upload
POST   /api/v1/n8n/upload-simple
POST   /api/v1/n8n/process-direct
POST   /api/v1/importer/
GET    /{full_path}
GET    /
GET    /ocr
GET    /mapeo
GET    /docs-ui
GET    /health
## 📋 REPORTE COMPLETO - Estado del Sistema OCR
✅ ENDPOINTS FUNCIONANDO CORRECTAMENTE:
/api/v1/n8n/process-direct - ✅ FUNCIONAL
Procesamiento directo con Mistral OCR
Acepta solo imágenes (PNG/JPG)
Rechaza PDFs temporalmente
Respuesta JSON estructurada
/api/v1/n8n/upload - ✅ FUNCIONAL
Webhook a n8n workflow activo
Procesa archivos a través de n8n
URL corregida: 5FJvGpjCI4SqiGqQ/webhook/demo-mistral-webhook
/api/v1/n8n/upload-simple - ✅ FUNCIONAL
Guarda archivos en carpeta compartida /tmp/pdf_upload/
Para uso con Local File Trigger de n8n
/api/v1/files/upload-temp - ✅ FUNCIONAL (requiere auth)
Error de validación corregido (size como string)
Modelo de respuesta actualizado a Dict[str, Any]
🧪 PRUEBAS REALIZADAS CON ÉXITO:
BSH-balay.png: OCR completo con datos estructurados de factura
NEVIR.png: Extracción de productos y totales
cecotec.png: Procesamiento via webhook n8n
🔧 PROBLEMAS RESUELTOS:
Error 500 en /upload-temp: Tipo de dato size corregido
Webhook 404: URL actualizada con ID de workflow
Validación de respuesta: Modelo cambiado a Dict[str, Any]
📁 RECURSOS DISPONIBLES:
Imágenes de facturas reales en /ejemplos/:
BSH-balay.png, NEVIR.png, JYSK.png, cecotec.png
alfadyser.png, almce.png, electrodirecto.png
Y muchas más en subdirectorios
🎉 ESTADO 23/07/2025 - N8N WEBHOOK RGPD OCR:
✅ WEBHOOK N8N FUNCIONANDO: http://n8n:5678/webhook/c5d076d2-ce8c-4f4b-8719-e96aebd0091f
✅ ENMASCARADO RGPD PERFECTO: 6 regiones enmascaradas (DNI, teléfonos, direcciones)
✅ PIPELINE FASTAPI: /api/v1/n8n/process-rgpd procesando PDFs e imágenes
✅ MISTRAL OCR: API procesando (42 páginas confirmadas)
❌ PENDIENTE: Nodo Mistral OCR no devuelve texto al Format OCR Response

🚀 PRÓXIMOS PASOS RECOMENDADOS:
Resolver conexión entre nodos Mistral OCR y Format OCR Response
Investigar configuración de nodos n8n para obtener texto extraído
Probar flujo completo desde frontend React
Documentar APIs para uso en producción


## 5. Frontend (React)

### Estructura de Directorios:

```
src/
├── components/             # Componentes React (actualmente vacío)
├── hooks/                  # Hooks personalizados
│   ├── useAuth.ts          # Hook para autenticación
│   ├── useProducts.ts      # Hook para productos
│   ├── useProviders.ts     # Hook para proveedores
│   └── useDashboard.ts     # Hook para dashboard
├── pages/                  # Páginas (actualmente vacío)
├── ImportExcelChunk.tsx    # Componente para importación de Excel
├── ImportInvoice.tsx       # Componente para importación de facturas
└── services/               # Servicios
    ├── odooClient.ts       # Cliente HTTP para la API
    └── odooService.ts      # Servicios para comunicación con la API
```

### Servicios Implementados:

- **odooService.ts**: Servicio principal para comunicación con la API
  - Autenticación
  - Gestión de productos
  - Gestión de proveedores

## 6. Conexión con Odoo

La conexión con Odoo se realiza a través de XML-RPC utilizando el servicio base `OdooBaseService` que proporciona métodos para:

- Autenticación con Odoo
- Ejecución de métodos de Odoo
- Manejo de errores y reconexión

### Configuración de Conexión:

- **URL**: http://odoo:8069 (nombre del servicio Docker)
- **Base de datos**: fresh_odoo_db 
- **Usuario**: admin **Contraseña**: admin

## 7. Funcionalidades Implementadas

### 1. Gestión de Productos
- CRUD completo de productos
- Búsqueda y filtrado
- Importación desde Excel
- Integración con categorías

### 2. Gestión de Proveedores
- CRUD de proveedores (falta implementar eliminación)
- Búsqueda y filtrado
- Validación para evitar duplicados

### 3. Procesamiento OCR con Mistral
- Reconocimiento de texto en facturas
- Extracción de datos estructurados
- Integración con LLM para interpretación

### 4. Importación de Excel
- Procesamiento de archivos Excel
- Mapeo automático de columnas
- Validación de datos

### 5. Autenticación
- Sistema OAuth2 con JWT
- Protección de endpoints
- Renovación automática de tokens

## 8. Integración con IA (LLM y OCR)

### Procesamiento OCR con Mistral

#### Flujo de Procesamiento OCR:
1. **Frontend**: El usuario sube un documento (PDF/imagen) a través del componente `ImportInvoice.tsx`
2. **API**: El documento se envía al endpoint `/api/v1/mistral-ocr/process-document`
3. **Servicio OCR**: `MistralOCRService` procesa el documento usando la API de Mistral OCR
4. **Extracción de Datos**: Se extraen datos estructurados del documento (texto, tablas, metadatos)
5. **Análisis con IA**: Si es una factura, se usa IA para extraer datos específicos (proveedor, fecha, importes)
6. **Respuesta**: Los datos estructurados se devuelven al frontend para su visualización y edición
7. **Creación en Odoo**: Opcionalmente, se puede crear una factura en Odoo con los datos extraídos

#### Endpoints OCR:
- **POST /api/v1/mistral-ocr/process-document**: Procesa un documento subido
- **POST /api/v1/mistral-ocr/process-document-url**: Procesa un documento desde URL
- **GET /api/v1/mistral-ocr/supported-formats**: Obtiene formatos soportados

#### Formato de Respuesta OCR:
```json
{
  "success": true,
  "message": "Documento procesado exitosamente",
  "data": {
    "document_type": "invoice",
    "text": "...",
    "tables": [...],
    "invoice_data": {
      "supplier": "Nombre del Proveedor",
      "invoice_number": "F2023-001",
      "date": "2023-01-15",
      "total_amount": 1234.56,
      "tax_amount": 234.56,
      "items": [...]
    }
  }
}
```

### Procesamiento de Excel con LLM

#### Flujo de Procesamiento Excel con LLM:
1. **Frontend**: El usuario sube un archivo Excel a través del componente `ImportExcelChunk.tsx`
2. **API**: El archivo se envía al endpoint `/api/v1/mistral-llm/process-excel`
3. **Preprocesamiento**: El archivo Excel se convierte a texto plano usando pandas
4. **LLM**: El texto se envía a un modelo LLM (Mistral, Groq o fallback a OpenAI)
5. **Extracción**: El LLM extrae productos estructurados del Excel en formato JSON
6. **Validación**: Se sanitizan y validan los datos extraídos
7. **Creación en Odoo**: Los productos válidos se crean en Odoo usando `OdooProductService`
8. **Respuesta**: Se devuelve un resumen de productos creados y fallidos

#### Proveedores LLM Configurados:
- **Principal**: Mistral (configurable mediante variable `LLM_PROVIDER`)
- **Alternativo**: Groq (usado como fallback)
- **Último recurso**: OpenAI (si está configurado)

#### Endpoints LLM:
- **POST /api/v1/mistral-llm/process-excel**: Procesa un archivo Excel para extraer productos
- **POST /api/v1/mistral-llm/test-minimal**: Endpoint de prueba para verificar conexión con LLM

#### Formato de Respuesta LLM:
```json
{
  "proveedor": "Nombre del Proveedor",
  "productos_creados": [
    {
      "id": 123,
      "name": "Producto 1",
      "default_code": "REF001"
    }
  ],
  "productos_fallidos": [
    {
      "idx": 5,
      "name": "Producto con error",
      "error": "Descripción del error",
      "default_code": "REF002"
    }
  ],
  "total_intentados": 10,
  "total_creados": 9,
  "total_fallidos": 1
}
```

### Integración Frontend-Backend para IA

#### Componentes Frontend:
- **ImportExcelChunk.tsx**: Interfaz para importación de Excel con procesamiento LLM
  - Permite subir archivos Excel
  - Muestra progreso de procesamiento
  - Visualiza resultados (productos creados y fallidos)

- **ImportInvoice.tsx**: Interfaz para procesamiento OCR de facturas
  - Permite subir documentos PDF/imágenes
  - Visualiza datos extraídos
  - Permite edición y validación antes de crear en Odoo

#### Servicios Backend:
- **mistral_llm_utils.py**: Utilidades para comunicación con APIs de LLM
  - Gestión de múltiples proveedores (Mistral, Groq, OpenAI)
  - Manejo de errores y reintentos
  - Parsing de respuestas JSON

- **mistral_ocr_service.py**: Servicio para procesamiento OCR
  - Integración con API de Mistral OCR
  - Extracción de datos estructurados
  - Análisis de facturas con IA

## 9. Funcionalidades Pendientes

### 1. Gestión de Categorías
- Implementar servicio dedicado para categorías
- Crear endpoints CRUD para categorías
- Desarrollar componentes frontend para gestión de categorías
- Integrar jerarquía de categorías

### 2. Mejoras en Proveedores
- Implementar eliminación segura de proveedores
- Mejorar validación y manejo de errores
- Completar componentes frontend

### 3. Gestión de Facturas
- Completar implementación de CRUD
- Implementar cancelación y archivado
- Desarrollar componentes frontend

### 4. Frontend
- Completar implementación de componentes
- Mejorar experiencia de usuario
- Implementar sistema de notificaciones

## 10. Problemas Conocidos y Soluciones

### 1. Conexión XML-RPC
- **Problema**: Cambios en las IPs de los contenedores (de localhost a nombres de servicios Docker)
- **Solución**: La configuración actual usa `http://odoo:8069` como URL de Odoo, utilizando el nombre del servicio Docker en lugar de una IP específica

### 2. Autenticación
- **Problema**: Endpoint /token no accesible
- **Solución**: En `auth.py` el endpoint está correctamente definido como `@router.post("/token", response_model=Token)` sin prefijo

### 3. Importación de Excel
- **Problema**: Error en mistral_llm_excel.py con método inexistente get_supplier_id
- **Solución**: Se usa ahora el método `resolve_supplier` para obtener IDs de proveedores

### 4. Compatibilidad con Odoo 18
- **Problema**: Campos y tipos de productos incompatibles
- **Solución**: En `front_to_odoo_product_dict` el valor por defecto para el campo `type` es `'consu'` (consumible), según comentario: "en Odoo 18 los valores válidos son 'consu', 'service', 'combo'"

## 11. Comandos Útiles

### Docker
```bash
# Iniciar todos los servicios
docker-compose up -d

# Reiniciar FastAPI
docker-compose restart fastapi

# Ver logs
docker-compose logs -f fastapi
```

### FastAPI
```bash
# Iniciar servidor de desarrollo
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Verificar conexión con Odoo
python verificar_conexion.py
```

### Odoo
```bash
# Acceder a la shell de Odoo
docker-compose exec odoo odoo shell -d fresh_odoo_db
```