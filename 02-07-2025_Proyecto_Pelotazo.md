# 02/07/2025 - Proyecto Pelotazo - ManusOdoo

## 📋 Descripción General del Proyecto

**ManusOdoo** es un sistema completo de gestión empresarial desarrollado específicamente para "El Pelotazo". El proyecto combina **Odoo 18.0** como ERP backend con un dashboard moderno desarrollado en **React + TypeScript**, creando una solución integral que incluye funcionalidades avanzadas de IA para procesamiento de documentos y mapeo inteligente de datos.

## 🏗️ Arquitectura Técnica del Sistema

### Backend Principal - FastAPI
- **Archivo principal**: `main.py`
- **Framework**: FastAPI con autenticación OAuth2
- **Puerto**: 8000
- **Funcionalidades**: 
  - API REST completa
  - OCR avanzado con Mistral AI
  - Procesamiento inteligente de Excel
  - Interfaz web integrada
  - Autenticación JWT

### Frontend - React Dashboard
- **Framework**: React + TypeScript + Vite
- **UI Library**: Ant Design + Refine
- **Puerto**: 3001 (desarrollo)
- **Características**:
  - Dashboard responsive y moderno
  - Integración en tiempo real con Odoo
  - Componentes reutilizables
  - Gestión de estado avanzada

### ERP Backend - Odoo 18.0
- **Sistema**: Odoo 18.0 + PostgreSQL
- **Puerto**: 8069
- **Base de datos**: pelotazo
- **Empresa**: El Pelotazo
- **Idioma**: Español (España)
- **Moneda**: EUR

## 📁 Estructura Detallada de Directorios

### 🔧 **api/** - Backend FastAPI
**Función**: Middleware entre el frontend React y Odoo, proporciona API REST

**Subdirectorios**:
- **routes/**: Endpoints de la API
  - `auth.py` - Autenticación y autorización
  - `products.py` - Gestión de productos
  - `providers.py` - Gestión de proveedores
  - `invoices.py` - Procesamiento de facturas
  - `mistral_ocr.py` - OCR con IA
  - `excel_importer.py` - Importación de Excel
  - `web_ui.py` - Interfaz web

- **services/**: Servicios de negocio
  - `odoo_base_service.py` - Conexión base con Odoo
  - `odoo_product_service.py` - Servicios de productos
  - `odoo_provider_service.py` - Servicios de proveedores
  - `mistral_ocr_service.py` - Servicios OCR
  - `excel_preprocessor.py` - Preprocesamiento de Excel

- **models/**: Modelos Pydantic
  - `schemas.py` - Esquemas principales
  - `invoice_models.py` - Modelos de facturas
  - `provider_create.py` - Modelos de creación de proveedores

- **utils/**: Utilidades
  - `config.py` - Configuración del sistema
  - `mistral_llm_utils.py` - Utilidades de IA

### 🎨 **src/** - Frontend React
**Función**: Dashboard web moderno para gestión empresarial

**Subdirectorios**:
- **components/**: Componentes React reutilizables
- **hooks/**: Custom hooks de React
- **pages/**: Páginas principales del dashboard
- **services/**: Servicios para comunicación con APIs

### 🔌 **addons/** - Módulos Personalizados de Odoo
**Función**: Extensiones y personalizaciones específicas de Odoo

**Módulos incluidos**:
- **app_barcode/**: Gestión de códigos de barras
- **auto_database_backup/**: Backups automáticos de base de datos
- **odoo_turbo_ai_agent/**: Agente de IA integrado en Odoo
- **pelotazo_extended/**: Personalizaciones específicas para El Pelotazo
- **purchase-workflow/**: Flujo de trabajo de compras avanzado
- **theme_pelotazo/**: Tema visual personalizado

### ⚙️ **config/** - Configuraciones del Sistema
**Función**: Archivos de configuración centralizados

**Archivos**:
- `odoo.conf` - Configuración principal de Odoo
- `odoo1.conf` - Configuración alternativa
- `manusodoo2.code-workspace` - Configuración del workspace de VS Code

### 📚 **docs/** - Documentación del Proyecto
**Función**: Documentación técnica completa

**Documentos principales**:
- `MEMORIA_PROYECTO.md` - Memoria principal del proyecto
- `OCR-Mistral.md` - Documentación del sistema OCR
- `PLAN_MVP_DESARROLLO.md` - Plan de desarrollo MVP
- `GUIA_MISTRAL_OCR.md` - Guía de integración OCR
- `FastAPIFINALconfig.md` - Configuración final de FastAPI

### 🧪 **data_test/** - Datos de Prueba
**Función**: Entorno de testing y datos de prueba

**Contenido**:
- `addons/` - Addons de prueba
- `filestore/` - Almacén de archivos de prueba
- `sessions/` - Sesiones de prueba

### 🌐 **static/** - Archivos Estáticos
**Función**: Recursos estáticos del servidor web

**Contenido**:
- `favicon.ico` - Icono del sitio
- `graficos/` - Gráficos e imágenes
- `uploads/` - Archivos subidos por usuarios

### 📄 **templates/** - Plantillas HTML
**Función**: Plantillas para la interfaz web del backend

**Plantillas**:
- `index.html` - Página principal
- `analisis.html` - Página de análisis de datos
- `mistral_ocr.html` - Interfaz para OCR

### 📦 **public/** - Recursos Públicos del Frontend
**Función**: Archivos públicos accesibles desde el navegador

### 📊 **informes/** - Informes Generados
**Función**: Directorio para almacenar informes generados dinámicamente

## 🚀 Funcionalidades Principales Implementadas

### 1. **Sistema de Gestión Empresarial Completo**
- ✅ Gestión integral de productos con validación
- ✅ Control de inventario en tiempo real
- ✅ Gestión de ventas y pedidos
- ✅ CRM para gestión de clientes
- ✅ Dashboard ejecutivo con KPIs
- ✅ Integración completa con Odoo 18.0

### 2. **Sistema de Mapeo de Datos con IA**
- ✅ Procesamiento inteligente de archivos de proveedores
- ✅ Detección automática de proveedores por estructura de archivo
- ✅ Extracción automática de atributos (marca, medidas, capacidad)
- ✅ Inferencia inteligente de categorías de productos
- ✅ Normalización automática de nombres de productos
- ✅ Detección de duplicados por similitud
- ✅ Conversión automática a formato Odoo
- ✅ Generación de informes comparativos

### 3. **OCR Avanzado con Mistral AI**
- ✅ Procesamiento de múltiples formatos (PDF, PNG, JPG, JPEG, AVIF, PPTX, DOCX)
- ✅ Extracción automática de datos de facturas
- ✅ Comprensión de layout complejo y multiidioma
- ✅ Integración directa con Odoo para creación automática
- ✅ API REST segura con autenticación JWT
- ✅ Procesamiento desde URL
- ✅ Limpieza automática de archivos temporales

### 4. **Procesamiento Inteligente de Excel**
- ✅ Análisis automático de estructura de archivos
- ✅ Mapeo inteligente de columnas
- ✅ Validación y limpieza de datos
- ✅ Importación directa a Odoo
- ✅ Soporte para múltiples formatos de proveedor

## 🔧 Archivos de Configuración Principales

### Configuración del Proyecto
- **`package.json`**: Dependencias y scripts del frontend
- **`vite.config.ts`**: Configuración de Vite con proxy a FastAPI
- **`docker-compose.yml`**: Orquestación de contenedores
- **`requirements.txt`**: Dependencias Python del backend
- **`.env`**: Variables de entorno (no incluido en repo)

### Configuración de Desarrollo
- **`tsconfig.json`**: Configuración TypeScript
- **`manusodoo-roto.code-workspace`**: Workspace de VS Code
- **Scripts de gestión**: `start.sh`, `stop.sh`, `backup.sh`, `install.sh`

## 🎯 Estado Actual del Desarrollo

### ✅ **Completado y Funcional**
- Backend FastAPI completamente operativo
- Frontend React con Ant Design funcional
- Integración Odoo 18.0 establecida y probada
- Sistema OCR con Mistral AI implementado y funcional
- Procesamiento de Excel con IA operativo
- Autenticación JWT implementada
- API REST completa con documentación
- Sistema de mapeo de proveedores funcional

### 🔄 **En Desarrollo Activo**
- Expansión de módulos personalizados de Odoo
- Mejoras en el dashboard con nuevas funcionalidades
- Optimización de rendimiento
- Ampliación de capacidades de IA

### 📋 **Próximos Pasos Planificados**
- Implementación de reportes avanzados
- Integración con sistemas de pago
- Desarrollo de aplicación móvil
- Automatización de procesos empresariales
- Expansión de capacidades de BI y Analytics

## 🛠️ Tecnologías Utilizadas

### Backend
- **FastAPI**: Framework web moderno y rápido
- **Odoo 18.0**: ERP empresarial
- **PostgreSQL**: Base de datos relacional
- **Pydantic**: Validación de datos
- **Mistral AI**: Procesamiento de documentos con IA

### Frontend
- **React 18**: Framework de interfaz de usuario
- **TypeScript**: Tipado estático
- **Vite**: Herramienta de construcción rápida
- **Ant Design**: Biblioteca de componentes UI
- **Refine**: Framework para dashboards admin

### DevOps y Herramientas
- **Docker**: Containerización
- **Docker Compose**: Orquestación de servicios
- **Git**: Control de versiones
- **VS Code**: Entorno de desarrollo

## 🔒 Características de Seguridad

- **Autenticación JWT**: Tokens seguros para API
- **OAuth2**: Estándar de autorización
- **CORS configurado**: Política de origen cruzado
- **Validación de datos**: Pydantic para backend
- **Limpieza automática**: Archivos temporales
- **Variables de entorno**: Configuración sensible protegida

## 📊 Métricas del Proyecto

- **Líneas de código**: Aproximadamente 15,000+ líneas
- **Archivos de configuración**: 20+ archivos
- **Módulos de Odoo**: 6 módulos personalizados
- **Endpoints API**: 25+ endpoints funcionales
- **Componentes React**: 15+ componentes
- **Servicios backend**: 10+ servicios especializados

## 🎨 Características del Dashboard

### Páginas Principales
1. **Dashboard Ejecutivo**: KPIs y métricas en tiempo real
2. **Gestión de Productos**: CRUD completo con validación
3. **Control de Inventario**: Seguimiento de stock
4. **Gestión de Ventas**: Pedidos y facturación
5. **CRM de Clientes**: Gestión de relaciones
6. **Reportes y Analytics**: Análisis de datos
7. **Gestión de Proveedores**: CRUD y mapeo inteligente

### Funcionalidades UI/UX
- 📊 Gráficos interactivos con datos en tiempo real
- 📱 Diseño completamente responsive
- 🔄 Sincronización automática con Odoo
- 🎯 Filtros avanzados y búsqueda inteligente
- 📈 KPIs personalizables por usuario
- 🌙 Soporte para modo oscuro
- 🚀 Carga rápida y optimizada

---

**Proyecto desarrollado para El Pelotazo**  
*Sistema de gestión empresarial moderno con IA integrada*  
*Fecha de documentación: 02/07/2025*