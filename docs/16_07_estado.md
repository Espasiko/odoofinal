# Estado del Proyecto Manusodoo-Roto - 16/07/2025

## Análisis de Archivos OCR, Gestión de Productos y Facturas

### Archivos Analizados

#### Archivos de Configuración y Estructura
- `/docker-compose.yml`: Define los servicios del proyecto (Odoo 18, PostgreSQL, Adminer, FastAPI)
- `/Dockerfile.fastapi`: Configuración del contenedor para el backend FastAPI con soporte OCR
- `/main.py`: Punto de entrada principal de la aplicación FastAPI
- `/requirements.txt`: Dependencias Python del proyecto
- `/.env.example`: Plantilla para variables de entorno (API keys, credenciales)
- `/vite.config.ts`: Configuración del servidor de desarrollo y build para el frontend React
- `/package.json`: Dependencias y scripts del frontend React
- `/tsconfig.json`: Configuración de TypeScript para el frontend

#### Scripts de Utilidad
- `/formatea_excel_nevir.py`: Formatea archivos Excel de NEVIR al formato esperado por el sistema
- `/test_nevir_import.py`: Script para probar la importación de productos NEVIR a Odoo
- `/verify_nevir_database.py`: Verifica la integridad de la base de datos tras importaciones

#### Backend (API)
- `/api/utils/mistral_llm_utils.py`: Utilidades para interactuar con modelos LLM (Mistral, Groq, OpenAI)
- `/api/services/ocr_cache_service.py`: Sistema de caché para resultados OCR basado en hash SHA-256
- `/api/services/provider_prompts.py`: Gestión de prompts específicos por proveedor para mejorar precisión OCR
- `/api/services/mistral_ocr_client.py`: Cliente para interactuar con la API de Mistral para OCR
- `/api/temp_main.py`: Punto de entrada mínimo para la aplicación FastAPI
- `/api/routes/excel_importer.py`: Ruta FastAPI para importación de productos desde Excel
- `/api/routes/mistral_free_ocr.py`: Ruta FastAPI para procesar facturas con OCR Mistral
- `/api/services/invoice_import_service.py`: Orquestador para importar facturas desde JSON OCR
- `/api/services/json_extraction_service.py`: Servicio para extraer datos JSON de texto
- `/api/services/mistral_free_ocr_service_refactored.py`: Versión refactorizada del servicio OCR con Mistral AI
- `/api/services/ocr_validator.py`: Validador de datos OCR para facturas
- `/api/services/odoo_product_service.py`: Fachada para gestión de productos en Odoo
- `/api/services/product_core_service.py`: Operaciones CRUD básicas de productos en Odoo
- `/api/services/product_integration_service.py`: Integración avanzada de productos con Odoo
- `/api/services/odoo_invoice_service.py`: Servicio para creación y consulta de facturas de proveedor
- `/api/services/product_lookup.py`: Funciones auxiliares para búsqueda de productos en Odoo
- `/api/services/product_transform.py`: Funciones para transformar datos de productos para Odoo

#### Frontend (React)
- `/src/App.tsx`: Componente principal que configura rutas y estructura de la aplicación
- `/src/OdooContext.tsx`: Proveedor de contexto para autenticación y gestión de tokens JWT
- `/src/ImportExcelChunk.tsx`: Componente para importación de archivos Excel en chunks
- `/src/ImportInvoice.tsx`: Componente para importación y procesamiento de facturas con OCR
- `/src/components/header.tsx`: Componente de cabecera con información de usuario y navegación
- `/src/components/sider.tsx`: Menú lateral con opciones de navegación
- `/src/hooks/useAuth.ts`: Hook personalizado para gestión de autenticación
- `/src/hooks/useProducts.ts`: Hook para operaciones CRUD de productos
- `/src/hooks/useProviders.ts`: Hook para operaciones CRUD de proveedores
- `/src/hooks/useCustomers.ts`: Hook para operaciones CRUD de clientes
- `/src/hooks/useSales.ts`: Hook para gestión de ventas
- `/src/hooks/useInventory.ts`: Hook para gestión de inventario
- `/src/hooks/useDashboard.ts`: Hook para obtener datos del dashboard
- `/src/pages/products.tsx`: Página de gestión de productos con tabla y filtros
- `/src/pages/providers.tsx`: Página de gestión de proveedores
- `/src/pages/customers.tsx`: Página de gestión de clientes
- `/src/pages/sales.tsx`: Página de gestión de ventas
- `/src/pages/inventory.tsx`: Página de gestión de inventario
- `/src/pages/dashboard.tsx`: Dashboard con estadísticas y gráficos
- `/src/services/odooService.ts`: Servicio para comunicación con la API de Odoo
- `/src/services/odooClient.ts`: Cliente HTTP para realizar peticiones a la API

### Análisis de Archivos en el Directorio Raíz

#### Docker y Configuración
- `docker-compose.yml`: Define la arquitectura completa del proyecto con 4 servicios principales:
  - `db`: PostgreSQL 15 para almacenar datos de Odoo
  - `odoo`: Odoo 18 como ERP principal
  - `adminer`: Gestor de base de datos para PostgreSQL
  - `fastapi`: Backend con FastAPI que se conecta a Odoo
- `Dockerfile.fastapi`: Configura el contenedor para FastAPI con:
  - Python 3.12
  - Tesseract OCR con soporte para español e inglés
  - Dependencias para procesamiento de imágenes y PDFs
  - Herramientas para extracción de datos de facturas

#### Configuración de Aplicaciones
- `main.py`: Punto de entrada principal de FastAPI que:
  - Configura CORS para permitir peticiones desde el frontend
  - Implementa autenticación OAuth2
  - Registra las rutas para productos, proveedores, OCR y facturas
  - Expone endpoints para salud del sistema
- `vite.config.ts`: Configura el servidor de desarrollo de Vite para:
  - Puerto 3001 para el frontend
  - Proxy para redirigir peticiones API a FastAPI
  - Configuración de seguridad (CSP, XSS protection)
  - Optimización de build para producción

#### Scripts de Utilidad
- `formatea_excel_nevir.py`: Script especializado que:
  - Transforma archivos Excel de NEVIR al formato estándar del sistema
  - Extrae datos del proveedor y productos
  - Normaliza valores monetarios y categorías
  - Genera un nuevo Excel con estructura compatible
- `test_nevir_import.py`: Script para pruebas de importación que:
  - Lee Excel formateado de NEVIR
  - Crea/actualiza el proveedor en Odoo
  - Crea/actualiza productos con categorías
  - Establece relaciones producto-proveedor
- `verify_nevir_database.py`: Herramienta de validación que:
  - Verifica la integridad de las tablas en Odoo
  - Comprueba relaciones entre productos y proveedores
  - Valida consistencia de datos importados
  - Genera informes detallados del estado de la base de datos

### Conclusiones del Análisis

1. **Estructura General**: 
   - Arquitectura con clara separación de responsabilidades
   - Backend: FastAPI con servicios modulares para OCR, caché y procesamiento
   - Frontend: React con componentes específicos para cada funcionalidad y hooks personalizados
   - Despliegue: Docker Compose para orquestar todos los servicios

2. **Duplicados**:
   - No se detectaron duplicados de archivos o funciones en los archivos analizados del backend
   - En el frontend se encontró un archivo de respaldo `ImportInvoice_backup.tsx` que es una versión anterior de `ImportInvoice.tsx`
   - También existe `odooService.ts.bak` como versión anterior del servicio
   - No se encontraron duplicados funcionales problemáticos en el código activo

3. **Patrones de Diseño**:
   - Singleton: Varios servicios implementan el patrón singleton para acceso global
   - Fachada: `odoo_product_service.py` implementa el patrón fachada
   - Adaptador: `invoice_import_service.py` utiliza adaptadores específicos por proveedor
   - Estrategia: `provider_prompts.py` implementa diferentes estrategias de prompts según el proveedor
   - Context API: El frontend utiliza React Context para gestión de estado global
   - Custom Hooks: Encapsulan lógica de negocio reutilizable

4. **Integración OCR**:
   - Sistema completo desde captura de imágenes hasta extracción y mejora de datos
   - Caché OCR para evitar reprocesamiento innecesario
   - Prompts específicos por proveedor para mejorar precisión
   - Validaciones robustas para NIF/CIF español y reglas por proveedor

5. **Gestión de Productos**:
   - Búsqueda inteligente por código, barcode y proveedor
   - Transformación y normalización de datos para Odoo
   - Categorización automática basada en nombre del producto y proveedor
   - Manejo de precios y márgenes con indicadores visuales
   - Implementación de caché local para categorías y proveedores

6. **Importación Excel**:
   - Sistema de importación por chunks para archivos grandes
   - Mecanismo de rate limiting (12 segundos entre chunks)
   - Renovación automática de token JWT antes de iniciar importación
   - Feedback visual detallado del progreso y resultados
   - Scripts específicos para formatear Excel de proveedores particulares (NEVIR)

7. **Importación de Facturas**:
   - Dos métodos de importación: OCR tradicional y Mistral Free OCR
   - Visualización y edición de datos extraídos antes de crear en Odoo
   - Selección manual de proveedor para facturas no identificadas
   - Opción para actualizar facturas existentes
   - Validación de datos según reglas específicas por proveedor

8. **Frontend UI/UX**:
   - Diseño responsivo con adaptación para móviles
   - Tema oscuro personalizado
   - Tablas con paginación, filtrado y ordenación
   - Indicadores visuales para márgenes de productos (verde > 30%, amarillo > 15%, rojo < 15%)
   - Formularios con validación y feedback inmediato

### Recomendaciones

1. **Optimización de Prompts OCR**:
   - Ampliar biblioteca de prompts para más proveedores
   - Implementar sistema de aprendizaje continuo basado en correcciones

2. **Mejoras en Frontend**:
   - Implementar redirección automática a página de productos tras importación
   - Añadir filtrado por proveedor en tabla de productos
   - Consolidar archivos de respaldo (.bak) y eliminar código no utilizado
   - Mejorar la gestión de caché con expiración configurable

3. **Integración Backend-Frontend**:
   - Asegurar que backend devuelva `categ_id` como array `[id, nombre]`
   - Garantizar inclusión correcta de `seller_ids` en productos importados
   - Estandarizar formato de respuestas de API para todos los endpoints

4. **Validación de Datos**:
   - Implementar validación de códigos de barras por proveedor
   - Añadir verificación de duplicados antes de crear productos
   - Mejorar validación de precios para evitar valores negativos o cero

5. **Rendimiento**:
   - Implementar virtualización para tablas con muchos datos
   - Optimizar consultas a la API con selección de campos específicos
   - Mejorar estrategia de caché para reducir llamadas a la API

6. **Documentación**:
   - Crear diagramas de secuencia para los flujos de importación
   - Documentar reglas de negocio específicas por proveedor
   - Añadir comentarios JSDoc en componentes y funciones clave

7. **Scripts de Utilidad**:
   - Generalizar `formatea_excel_nevir.py` para soportar más proveedores
   - Añadir tests automatizados para validar importaciones
   - Implementar herramientas de monitoreo para el estado de la base de datos