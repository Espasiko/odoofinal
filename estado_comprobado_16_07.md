# Estado comprobado del proyecto Manusodoo-Roto (16/07/2025)

## 1. Infraestructura y configuración real
- **Odoo 18 (ERP)**, desplegado en Docker, imagen oficial.
- **FastAPI** como backend de integración, versión 0.109.1.
- **Frontend React** (Vite 6.3.5, React 18.x, Ant Design 5.x).
- **Base de datos PostgreSQL 15** (`fresh_odoo_db`).
- **Adminer** para gestión visual de la BD.
- **Docker Compose** orquesta todo (versión 3.8), con volúmenes persistentes (`odoo-db-data`, `odoo-web-data`).
- **Credenciales**: admin/admin para Odoo y API, odoo/odoo para la BD.
- **Puertos**: Odoo 8069, FastAPI 8000, Adminer 8080, PostgreSQL 5432 (interno) y 5434 (externo).
- **Variables de entorno** y configuración en `.env` y `docker-compose.yml`.
- **Prohibido borrar volúmenes Docker** sin permiso explícito.
- **Repositorio principal**: https://github.com/Espasiko/odoofinal/tree/version-consolidada-13-07 (rama fastmal).

## 2. Estado funcional comprobado
- **Importación masiva de productos/proveedores** desde Excels heterogéneos, usando LLM (Groq/Mistral) para normalizar y validar, y cargando en Odoo.
- **OCR de facturas**: extracción avanzada de datos con validación de CIF/NIF, códigos de producto y separación de impuestos.
- **CRUD y dashboards**: ventas, clientes, productos, estadísticas históricas.
- **Validación cruzada**: Excel → LLM → Odoo → Factura.
- **Logs detallados y trazabilidad** en cada paso.
- **Integración real**: productos y proveedores en Odoo, pero faltan mejoras en visualización y edición en frontend.

## 3. Datos reales en Odoo y BD
- **Empresa principal**: "El Pelotazo" (NIF: 75236270G, email: lorecomiendo11@gmail.com, dirección en Roquetas de Mar).
- **Usuarios**: admin, demo, portal, plantillas.
- **Proveedores**: NEVIR, BECKEN, etc. correctamente enlazados a productos.
- **Productos**: hasta 1000, con relaciones proveedor-producto en `product_supplierinfo`.
- **Facturas**: no se detectaron facturas asociadas a "El Pelotazo" en este momento.
- **Estructura de tablas y campos usados**:
  - `product_template`: id, name, default_code, list_price, standard_price, categ_id, active.
  - `product_supplierinfo`: id, product_tmpl_id, partner_id, min_qty, price, currency_id.
  - `res_partner`: id, name, vat, email, y campos de contacto.
  - `account_move`: id, partner_id, amount_total, invoice_date, state, move_type.

## 4. Addons y módulos relevantes
- **barcode_scanning_sale_purchase**: permite escaneo de códigos de barras en ventas y compras, añade campo barcode a líneas de pedido y movimientos de stock. Desarrollado por Cybrosys Techno Solutions.
- **Dependencias**: purchase, sale_management, stock.
- **Archivos clave**: `__manifest__.py`, `README.rst`, modelos y vistas XML, recursos gráficos.

## 5. Herramientas MCP activas
- **MCP Filesystem**: acceso a archivos y carpetas del proyecto real.
- **MCP Postgres**: consulta de datos y estructura de la BD real.
- **MCP Github**: consulta de ramas, archivos y metadatos del repositorio remoto.
- **MCP Knowledge-Graph**: modelado vivo del grafo de conocimiento.
- **MCP Sequential-Thinking**: desglosar problemas complejos en pasos lógicos.
- **MCP Excel-Local**: lectura y escritura de Excels reales.
- **MCP Convex/Context7**: almacenamiento y búsqueda avanzada.

## 6. Recomendaciones y próximos pasos
- Mejorar integración frontend-backend para mostrar y editar márgenes, precios de compra y categorías.
- Documentar y centralizar reglas de transformación por proveedor.
- Implementar validación previa y generación automática de códigos de referencia en importación.
- Añadir interfaz de resolución manual de conflictos en productos.
- Mantener el grafo MCP actualizado tras cada cambio relevante.

## 7. Correcciones recientes

### 7.1. Corrección de parámetros en create_supplier_invoice (16/07/2025)
- **Problema detectado**: Error en el endpoint `/api/v1/mistral-free-ocr/process-invoice` al llamar a la función `create_supplier_invoice` con parámetros no definidos en su firma (`amount_total`, `amount_tax`, `amount_untaxed`).
- **Solución implementada**: Se eliminaron los parámetros adicionales de la llamada en `mistral_free_ocr.py`.
- **Verificación**: Se comprobó que todas las demás llamadas a esta función en el código estaban correctamente implementadas.
- **Prueba realizada**: Procesamiento exitoso de factura NEVIR con OCR, detectando correctamente 6 productos con sus códigos, precios y datos completos de proveedor/cliente.
- **Impacto**: Permite el flujo completo de importación de facturas desde OCR hasta su creación en Odoo.

---

Este documento refleja el estado real, comprobado y trazable del proyecto a fecha 16/07/2025. Es la referencia para auditoría, debugging y planificación futura.
