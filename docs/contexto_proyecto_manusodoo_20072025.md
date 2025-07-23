# Contexto del Proyecto ManusOdoo (20-07-2025)

## Arquitectura del Sistema

ManusOdoo es un sistema integrado que conecta los siguientes componentes:

- **Odoo 18**: ERP principal para gestión de productos, proveedores, clientes y ventas
- **FastAPI**: Backend que proporciona servicios REST y conecta con Odoo mediante XML-RPC
- **React**: Frontend para interfaz de usuario (dashboard y gestión)
- **PostgreSQL**: Base de datos para Odoo y otros servicios
- **n8n**: Plataforma de automatización de flujos de trabajo
- **Adminer**: Gestor de base de datos web

## Credenciales y Configuración Actual

### Base de Datos PostgreSQL
- **Host**: localhost (5432 interno, 5434 externo)
- **Base de Datos**: fresh_odoo_db
- **Usuario PostgreSQL**: odoo
- **Contraseña PostgreSQL**: odoo

### Usuario Administrador Odoo
- **Email/Usuario**: admin
- **Contraseña**: admin
- **Nombre**: El pelotazo
- **ID de Usuario**: 2

### URLs de Acceso
- **Odoo Web**: http://localhost:8069
- **Adminer (DB Manager)**: http://localhost:8080
- **FastAPI Backend**: http://localhost:8000
- **Frontend React**: http://localhost:3001
- **n8n (Automatización)**: http://localhost:5678

### Configuración de API y Servicios
- **API Key Mistral (OCR)**: V27eNNH4b7Er1k9WPxYHRaEf9gLsKqmH
- **API Key Groq (LLM)**: [GROQ_API_KEY_PLACEHOLDER]
- **Modelo Groq**: llama-3.1-8b-instant
- **Proveedor LLM Actual**: mistral
- **Token n8n API**: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJlNzE4M2QyYy1lMTNjLTQ4NGYtOWY5Zi03ZmQ1Y2U3ZmE1ZmYiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzUyOTQ0ODI4fQ.Sx3wsxu1-KJuaa3SFb8qMUfT59F8x7M1VIcyJvzO0Ts
- **Webhook URL n8n**: http://n8n:5678
- **Secret Key JWT**: odoo_middleware_secret_key
- **Duración Token**: 180 minutos

## Estado Actual del Sistema

### Componentes Operativos
- La integración entre Odoo y FastAPI está funcionando correctamente
- El sistema de importación Excel está implementado con procesamiento por lotes (chunks)
- El sistema OCR para facturas tiene implementado un sistema de caché, pero actualmente está desactivado (comentado en el código)
- n8n está configurado y tiene flujos de trabajo creados en /n8n/flujos/ pero requiere activación

### Mejoras Recientes (Julio 2025)
1. **Sistema de Caché OCR**: Implementado pero actualmente desactivado (comentado en el código)
2. **Prompts Específicos por Proveedor**: Creados para NEVIR, ABRILA y MIELECTRO en provider_prompts.py
3. **Validador OCR Mejorado**: Implementado en nif_cif_validator.py para validación de CIF/NIF
4. **Flujos de Trabajo n8n**: Creados flujos iniciales (procesar_factura_ocr.json, llm_mcp_client_factura.json, etc.)

## Estructura del Proyecto

```
manusodoo-roto/
├── api/                    # Backend FastAPI
│   ├── models/             # Modelos de datos y esquemas Pydantic
│   ├── routes/             # Endpoints de la API
│   ├── services/           # Servicios de negocio y conexión con Odoo
│   ├── ocr_cache/          # Sistema de caché para OCR
│   └── utils/              # Utilidades y configuración
├── src/                    # Frontend React
│   ├── components/         # Componentes React reutilizables
│   ├── hooks/              # Hooks personalizados
│   ├── pages/              # Páginas de la aplicación
│   └── services/           # Servicios para comunicación con la API
├── config/                 # Configuración de Odoo
├── addons/                 # Módulos personalizados para Odoo
├── n8n/                    # Configuración y flujos de n8n
│   └── flujos/             # Flujos de trabajo definidos
└── docker-compose.yml      # Configuración de contenedores
```

## Servicios y Funcionalidades Principales

### 1. Importación de Excel
- **Componente Frontend**: ImportExcelChunk.tsx
- **Procesamiento**: Por lotes (chunks) con tamaño configurable (50 por defecto)
- **Validación**: Campos obligatorios, tipos de datos, referencias
- **Características**: Rate limiting, renovación de token JWT, manejo de errores

### 2. Procesamiento OCR de Facturas
- **Servicio Principal**: mistral_ocr_service.py
- **Caché**: ocr_cache_service.py implementado pero desactivado en el código actual
- **Validación**: nif_cif_validator.py, ocr_validator.py
- **Prompts Específicos**: provider_prompts.py con templates por proveedor
- **Características**: Extracción de datos estructurados, validación, normalización

### 3. Gestión de Productos
- **Servicio Principal**: odoo_product_service.py
- **Categorización**: product_categorization.py
- **Transformación**: product_transform.py
- **Características**: Creación/actualización de productos, gestión de categorías, proveedores

### 4. Automatización con n8n
- **Configuración**: n8n/docker-compose.yml
- **Flujos**: Creados el 19/07/2025 en n8n/flujos/
- **Integración**: Conexión con Odoo y FastAPI mediante webhooks y API

## Problemas Conocidos y Soluciones

### 1. Frontend-Backend
- **Problema**: El frontend espera categ_id como array [id, nombre]
- **Solución**: Modificar odoo_product_service.py para devolver el formato correcto

### 2. Información de Proveedores
- **Problema**: seller_ids no siempre se incluye completo en productos importados
- **Solución**: Asegurar que seller_ids se incluya correctamente en todos los productos

### 3. Campos Numéricos
- **Problema**: Posibles errores de tipo en campos numéricos
- **Solución**: Implementar conversión explícita de tipos para todos los campos numéricos

### 4. Navegación Post-Importación
- **Problema**: No existe redirección automática tras importación exitosa
- **Solución**: Añadir botón para navegar a la página de productos después de importar

### 5. Duplicación de Datos
- **Problema**: Proveedores duplicados en Odoo con nombres ligeramente diferentes
- **Problema**: Productos duplicados con códigos similares pero no idénticos
- **Problema**: Inconsistencias en relaciones product_supplierinfo
- **Problema**: Inconsistencias en la configuración de la base de datos

### 6. Sistema de Caché OCR
- **Problema**: El sistema de caché OCR está implementado pero desactivado en el código
- **Solución**: Activar el sistema de caché eliminando los comentarios en mistral_free_ocr.py

## Planes y Objetivos Actuales

### 1. Plan de Consolidación Excel-OCR-Odoo
- Implementar sistema unificado de importación y procesamiento
- Mejorar validación cruzada y revisión visual
- Documentar flujo completo

### 2. Mejoras OCR para Facturas
- Activar sistema de caché OCR (actualmente comentado en el código)
- Optimizar extracción de datos de proveedor
- Implementar aplicación correcta de descuentos e impuestos
- Mejorar vinculación de productos
- Completar la implementación de validación de CIF/NIF y separación de impuestos

### 3. Desarrollo de Flujos n8n
- Mejorar flujo OCR según ejemplos de documentación oficial
- Implementar flujos adicionales para automatización de tareas

### 4. Optimización de Rendimiento
- Implementar caché para categorías y proveedores frecuentes
- Optimizar procesamiento de archivos Excel grandes
- Mejorar feedback visual durante importaciones

## Herramientas y Utilidades

### 1. Scripts de Sistema
- **start.sh**: Inicia todos los servicios (Docker, API, opcionalmente frontend)
- **stop.sh**: Detiene todos los servicios
- **backup.sh**: Crea backup del sistema
- **dev-dashboard.sh**: Inicia dashboard en modo desarrollo

### 2. Comandos Docker Útiles
```bash
# Ver logs
docker-compose logs -f fastapi
docker-compose logs -f odoo
docker-compose logs -f n8n

# Reiniciar servicios
docker-compose restart fastapi
docker-compose restart odoo

# Ver estado
docker-compose ps
```

### 3. Endpoints API Principales
- **/token**: Autenticación JWT (admin/admin)
- **/api/products**: CRUD de productos
- **/api/providers**: CRUD de proveedores
- **/api/excel-importer**: Importación de productos desde Excel
- **/api/v1/mistral-ocr/process-invoice**: Procesamiento OCR de facturas (versión pagada)
- **/api/v1/mistral-ocr/process-document**: Procesamiento de documentos genéricos
- **/api/v1/mistral-ocr/save-verified-invoice**: Guardar factura verificada
- **/api/v1/mistral-free-ocr/process-invoice**: Procesamiento OCR de facturas (versión gratuita)
- **/api/v1/n8n/workflows**: Gestión de flujos de trabajo n8n
- **/api/v1/n8n/execute/ocr**: Ejecutar flujo OCR en n8n
- **/health**: Verificación de estado del sistema

Para una documentación completa de todos los endpoints disponibles, consultar el archivo `/docs/API_ENDPOINTS_20072025.md`.

## Recomendaciones Técnicas

1. **Ajustes en el Backend**:
   - Modificar `odoo_product_service.py` para devolver `categ_id` como array `[id, nombre]`
   - Asegurar que `seller_ids` se incluya correctamente en todos los productos
   - Implementar conversión explícita de tipos para campos numéricos

2. **Mejoras en el Frontend**:
   - Añadir navegación post-importación
   - Implementar filtrado por proveedor en la tabla de productos
   - Mejorar visualización de errores durante importación

3. **Optimizaciones de Rendimiento**:
   - Implementar caché para categorías y proveedores frecuentes
   - Optimizar procesamiento de archivos grandes
   - Mejorar feedback visual durante operaciones largas

## Archivos Candidatos para Refactorización

### Backend (API)

#### Rutas (Routes)
1. **mistral_ocr.py** (43.51 KB)
   - Archivo principal para procesamiento OCR de facturas (versión pagada)
   - Contiene múltiples endpoints y lógica de procesamiento
   - Recomendación: Dividir en módulos más pequeños por funcionalidad

2. **mistral_free_ocr.py** (39.37 KB)
   - Versión gratuita del procesador OCR
   - Incluye sistema de caché (actualmente desactivado)
   - Recomendación: Separar lógica de validación, procesamiento y respuesta API

3. **ocr.py** (26.43 KB)
   - Router OCR original, posiblemente obsoleto pero mantenido
   - Recomendación: Evaluar si es necesario mantenerlo o puede eliminarse

4. **excel_importer.py** (22.01 KB)
   - Maneja toda la lógica de importación de Excel
   - Contiene procesamiento por chunks y validación
   - Recomendación: Separar en servicios específicos por funcionalidad

#### Servicios (Services)
1. **odoo_product_service.py** (21.33 KB) y su backup (49.92 KB)
   - Servicio para gestión de productos en Odoo
   - Requiere modificación para devolver categ_id como array [id, nombre]
   - Recomendación: Refactorizar para resolver problemas de formato y separar en servicios más específicos

2. **odoo_invoice_service.py** (42.84 KB)
   - Servicio para gestión de facturas en Odoo
   - Contiene lógica compleja de mapeo y validación
   - Recomendación: Dividir en servicios más pequeños por tipo de operación

3. **ocr_validator.py** (29.44 KB)
   - Validador OCR con lógica compleja
   - Recomendación: Dividir en módulos específicos por tipo de validación

### Frontend

1. **ImportInvoice.tsx** (39.10 KB)
   - Componente para importación de facturas
   - Extremadamente grande, candidato principal para refactorización
   - Recomendación: Dividir en componentes más pequeños y reutilizables

2. **products.tsx** (22.87 KB)
   - Página de productos con tabla y funcionalidades
   - Contiene lógica de visualización y gestión
   - Recomendación: Separar lógica de negocio de la presentación

### Problemas Comunes Identificados

1. **Archivos de respaldo (.bak)**
   - Múltiples versiones de respaldo que aumentan la complejidad
   - Recomendación: Usar control de versiones en lugar de archivos .bak

2. **Código duplicado**
   - Servicios OCR con funcionalidad similar pero en archivos separados
   - Recomendación: Crear servicios base compartidos

3. **Componentes monolíticos**
   - Tanto en frontend como backend hay componentes demasiado grandes
   - Recomendación: Aplicar principio de responsabilidad única