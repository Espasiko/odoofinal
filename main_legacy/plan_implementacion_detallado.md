# Plan Detallado de Implementación: OCR, TVP y Migración para Dashboard Odoo

## 1. Introducción y Objetivos

Este documento proporciona un plan detallado y pasos prácticos para implementar las funcionalidades solicitadas:

- **Integración OCR**: Procesamiento automático de facturas de proveedores.
- **Integración TVP**: Desarrollo de módulos personalizados para procesamiento de transacciones de venta.
- **Facturación Verifactu**: Cumplimiento de normativa fiscal para facturación electrónica.
- **Migración de Datos**: Carga de datos históricos de productos y proveedores desde CSV/Excel.
- **Arquitectura**: Uso de FastAPI como middleware entre el frontend Refine y el backend Odoo.

Se asume una arquitectura de tres capas como la descrita en `arquitectura_ocr_tvp.md`.

## 2. Prerrequisitos

- **Software**: Node.js (v18+ LTS), Python (3.8+), Docker (recomendado), Odoo (v16+), PostgreSQL.
- **Bibliotecas Python**: FastAPI, Uvicorn, Pandas, Openpyxl, Pytesseract, pdf2image, python-docx, python-jose[cryptography], httpx, xmlrpc.client.
- **Bibliotecas Node.js**: React, Refine.dev, Ant Design, Axios, etc. (según `package.json`).
- **Servicios Externos**: Cuentas y API Keys para Verifactu (si aplica), servicio OCR (si se usa uno externo).
- **Entorno Odoo**: Instancia de Odoo configurada (local o remota) con acceso de administrador.

## 3. Fase 1: Configuración del Backend (Odoo y FastAPI)

### 3.1 Odoo: Módulos Personalizados

**Objetivo**: Extender Odoo para almacenar los datos adicionales y facilitar la integración.

**Pasos**:
1.  **Crear estructura del módulo**: Siguiendo las convenciones de Odoo, crea un nuevo módulo (ej. `custom_electrodomesticos`).
2.  **Definir modelos extendidos**: Edita los archivos Python (`models/`) para añadir los campos personalizados (`x_...`) a `product.template`, `product.category`, `product.supplierinfo`, `account.move` como se detalla en `proceso_mapeo_migracion.md` y `integracion_facturacion_verifactu.md`.
    ```python
    # Ejemplo en models/product_template.py
    from odoo import models, fields

    class ProductTemplate(models.Model):
        _inherit = 'product.template'

        x_codigo_proveedor = fields.Char(string='Código de Proveedor')
        x_marca = fields.Char(string='Marca')
        # ... otros campos personalizados ...
    ```
3.  **Crear vistas**: Edita los archivos XML (`views/`) para mostrar los nuevos campos en la interfaz de Odoo.
    ```xml
    <!-- Ejemplo en views/product_views.xml -->
    <record id="product_template_form_view_custom_electro" model="ir.ui.view">
        <field name="name">product.template.form.custom.electro</field>
        <field name="model">product.template</field>
        <field name="inherit_id" ref="product.product_template_form_view"/>
        <field name="arch" type="xml">
            <xpath expr="//field[@name='barcode']" position="after">
                <field name="x_codigo_proveedor"/>
                <field name="x_marca"/>
                <!-- ... otros campos ... -->
            </xpath>
        </field>
    </record>
    ```
4.  **Definir seguridad**: Configura los permisos de acceso en `security/ir.model.access.csv`.
5.  **Actualizar manifest**: Asegúrate de que `__manifest__.py` incluya todas las dependencias y archivos.
6.  **Instalar/Actualizar módulo**: Reinicia Odoo y actualiza la lista de aplicaciones para instalar/actualizar tu módulo.

### 3.2 FastAPI: Configuración Inicial

**Objetivo**: Establecer el proyecto FastAPI que servirá como middleware.

**Pasos**:
1.  **Crear estructura del proyecto**: Organiza tu proyecto FastAPI (ej. `middleware/app/main.py`, `routers/`, `services/`, `models/`).
2.  **Instalar dependencias**: `pip install -r requirements.txt` (asegúrate de que incluya `fastapi`, `uvicorn`, `python-jose[cryptography]`, `pandas`, `pytesseract`, `pdf2image`, `httpx`, etc.).
3.  **Configurar CORS**: En `main.py`, configura `CORSMiddleware` para permitir peticiones desde tu frontend Refine.
    ```python
    from fastapi.middleware.cors import CORSMiddleware

    app = FastAPI()

    origins = [
        "http://localhost:5173", # Puerto por defecto de Vite
        "http://localhost:3000", # Puerto alternativo
        # Añade la URL de tu frontend desplegado si es necesario
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    ```
4.  **Implementar autenticación**: Configura OAuth2 con JWT como se muestra en `proceso_mapeo_migracion.md` (endpoint `/token`, funciones `create_access_token`, `get_current_active_user`).
5.  **Crear endpoints básicos**: Implementa endpoints iniciales (ej. `/`, `/api/v1/auth/session`) para verificar la configuración.
6.  **Variables de entorno**: Usa variables de entorno (`.env` y `python-dotenv` o configuración similar) para gestionar secretos (claves API, contraseñas Odoo, `SECRET_KEY` de JWT).

## 4. Fase 2: Migración de Datos CSV/Excel

**Objetivo**: Cargar datos históricos de productos y proveedores desde los archivos CSV/Excel a Odoo.

**Pasos**:
1.  **Desarrollar servicio de migración FastAPI**: Implementa la lógica detallada en `proceso_mapeo_migracion.md`:
    - Endpoint `/api/migration/upload` para recibir archivos.
    - Función `process_file` para orquestar la lectura, normalización, transformación, validación y carga.
    - Funciones auxiliares para normalizar DataFrames (`normalize_dataframe`), transformar a formato Odoo (`transform_to_odoo`), validar (`validate_data`) y cargar (`load_to_odoo`) usando `xmlrpc.client` para interactuar con Odoo.
    - Implementar procesamiento en segundo plano (`BackgroundTasks`) para no bloquear la API.
    - Endpoints `/api/migration/status/{job_id}` y `/api/migration/results/{job_id}` para seguimiento.
2.  **Refinar lógica de mapeo**: Ajusta las funciones `_convert_to_float`, `_extract_category`, `_extract_brand_model` basándote en un análisis más profundo de todos los archivos CSV/Excel.
3.  **Implementar carga de inventario**: Añade la lógica para actualizar el stock en Odoo (`stock.quant`) usando `models.execute_kw` con el método `change_product_qty` o creando/actualizando `stock.quant` directamente (requiere más cuidado).
4.  **Desarrollar interfaz en Refine**: Crea una página en el dashboard para:
    - Subir archivos CSV/Excel.
    - Seleccionar el proveedor asociado.
    - Mostrar el progreso de la migración (llamando al endpoint de estado).
    - Presentar los resultados (llamando al endpoint de resultados), incluyendo errores y advertencias.
5.  **Pruebas exhaustivas**: Prueba la migración con cada archivo de proveedor, verificando los datos cargados en Odoo y la correcta gestión de errores.

## 5. Fase 3: Integración OCR

**Objetivo**: Procesar facturas de proveedores subidas (PDF/imagen) para extraer datos y crear borradores en Odoo.

**Pasos**:
1.  **Configurar Tesseract**: Asegúrate de que Tesseract OCR esté instalado en el entorno del servidor FastAPI y que los paquetes de idioma necesarios (español) estén disponibles.
2.  **Desarrollar servicio OCR en FastAPI**: Crea un nuevo router o módulo (`services/ocr_service.py`):
    - Endpoint `/api/ocr/upload_invoice` para recibir archivos de factura.
    - Función para preprocesar imágenes/PDF (`pdf2image`, `Pillow`, `OpenCV`).
    - Función para extraer texto usando `pytesseract`.
    - Lógica para analizar el texto extraído e identificar campos clave (proveedor, NIF, número de factura, fecha, importes, líneas). Puedes usar expresiones regulares o modelos de ML más avanzados.
    - Endpoint para devolver los datos extraídos para validación del usuario.
3.  **Integrar con Odoo**: Una vez validados los datos (manual o automáticamente):
    - Llama a la API de Odoo (vía `xmlrpc.client` desde FastAPI) para crear un borrador de factura de proveedor (`account.move` con `move_type='in_invoice'`).
    - Adjunta el archivo original a la factura creada en Odoo.
4.  **Desarrollar interfaz en Refine**: Crea una página para:
    - Subir archivos de factura.
    - Mostrar los datos extraídos por OCR para validación/corrección.
    - Botón para confirmar y enviar a Odoo.
    - Visualizar el estado del procesamiento.
5.  **Pruebas**: Prueba con diferentes formatos de factura (PDF, JPG, PNG) y distintos proveedores.

## 6. Fase 4: Integración TVP y Verifactu

**Objetivo**: Implementar lógica personalizada para procesamiento de ventas y asegurar cumplimiento con Verifactu.

### 6.1 Módulos Personalizados Odoo (TVP)

**Pasos**:
1.  **Definir lógica TVP**: Especifica las reglas de negocio personalizadas para el procesamiento de transacciones de venta que difieren del estándar de Odoo.
2.  **Extender modelos Odoo**: Modifica `sale.order`, `account.move`, etc., para añadir campos o lógica necesaria para tu TVP personalizado.
3.  **Sobrescribir métodos**: Si es necesario, hereda y modifica métodos existentes (ej. `action_confirm` en `sale.order`, `action_post` en `account.move`) para incorporar tu lógica TVP.
4.  **Crear flujos de trabajo**: Define estados y transiciones específicas si el flujo estándar no es suficiente.

### 6.2 Integración Verifactu

**Pasos**:
1.  **Desarrollar conector Verifactu en FastAPI**: Implementa la lógica detallada en `integracion_facturacion_verifactu.md`:
    - Clase `VerifactuClient` con métodos para enviar factura y consultar estado.
    - Endpoints FastAPI (`/api/facturas/enviar`, `/api/facturas/{id_factura}/estado`).
    - Gestión segura de API Key y certificados.
2.  **Integrar con Odoo**: Modifica tu módulo Odoo personalizado:
    - Añade los campos `x_verifactu_...` al modelo `account.move`.
    - Implementa el método `action_enviar_verifactu` que llama al endpoint de FastAPI.
    - Añade el botón "Enviar a Verifactu" en la vista de factura.
    - Considera automatizar el envío al confirmar la factura (`action_post`).
    - Implementa una acción programada (`ir.cron`) en Odoo para consultar periódicamente el estado de las facturas enviadas a Verifactu (llamando al endpoint de estado de FastAPI).
3.  **Desarrollar interfaz en Refine**: Actualiza la vista de facturas en el dashboard para:
    - Mostrar el estado de Verifactu.
    - Permitir el envío manual si no es automático.
    - Mostrar mensajes de error o confirmación.
4.  **Pruebas**: Realiza pruebas exhaustivas con el entorno de pruebas de Verifactu antes de pasar a producción.

## 7. Fase 5: Integración Frontend (Refine)

**Objetivo**: Conectar todos los componentes del backend (FastAPI) con la interfaz de usuario Refine.

**Pasos**:
1.  **Configurar Data Provider**: Asegúrate de que el `dataProvider` de Refine esté configurado para interactuar con tu API FastAPI (usando `axios` o `fetch`). Adapta el `OdooClient` existente o crea uno nuevo específico para FastAPI si es necesario (ya se hizo una adaptación en `odooClient.ts`).
2.  **Implementar flujo de autenticación**: Conecta la página de login de Refine al endpoint `/token` de FastAPI. Almacena el token JWT de forma segura (localStorage/sessionStorage) y envíalo en las cabeceras `Authorization: Bearer <token>` de las peticiones subsiguientes.
3.  **Desarrollar páginas/componentes**: Crea o adapta las páginas en Refine (`src/pages/`) para:
    - **Dashboard**: Mostrar estadísticas obtenidas del endpoint `/api/v1/dashboard/stats`.
    - **Productos, Inventario, Ventas, Clientes**: Usar los endpoints `/api/v1/...` correspondientes.
    - **Migración**: Implementar la interfaz descrita en la Fase 2.
    - **OCR**: Implementar la interfaz descrita en la Fase 3.
    - **Facturación**: Mostrar estado Verifactu y acciones relacionadas (Fase 4).
4.  **Ajustar UI/UX**: Adapta los componentes de Ant Design para una experiencia de usuario fluida y coherente.

## 8. Fase 6: Pruebas y Despliegue

**Objetivo**: Asegurar la calidad y poner el sistema en funcionamiento.

**Pasos**:
1.  **Pruebas Unitarias**: Prueba funciones individuales en FastAPI y componentes React.
2.  **Pruebas de Integración**: Verifica la comunicación entre Refine-FastAPI y FastAPI-Odoo.
3.  **Pruebas End-to-End**: Simula flujos completos de usuario (subir factura OCR, crear venta con TVP, migrar CSV).
4.  **Pruebas de Carga (Opcional)**: Evalúa el rendimiento bajo carga simulada, especialmente para la migración y OCR.
5.  **Estrategia de Despliegue**: Define cómo desplegarás los componentes:
    - **Odoo**: Servidor propio, Odoo.sh, etc.
    - **FastAPI**: Servidor propio (con Gunicorn/Uvicorn), Docker, servicios en la nube (AWS, Google Cloud, Azure).
    - **Refine**: Servir como archivos estáticos desde FastAPI, Vercel, Netlify, etc.
6.  **Configuración de Producción**: Ajusta variables de entorno, URLs, claves API para el entorno de producción.
7.  **Monitorización y Logs**: Configura herramientas para monitorizar el rendimiento y registrar errores en producción.

## 9. Documentación Final

- **Manual de Usuario**: Guía para usar el dashboard, incluyendo las nuevas funcionalidades.
- **Documentación Técnica**: Detalles de la arquitectura, configuración, API endpoints, y procesos.
- **Guía de Mantenimiento**: Procedimientos para actualizaciones, backups, y solución de problemas.

Este plan proporciona una hoja de ruta detallada. Cada paso requerirá desarrollo, pruebas y ajustes específicos según tus necesidades y la complejidad encontrada.
