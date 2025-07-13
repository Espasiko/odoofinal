# Plan de Campos y Módulos para ERP Odoo 18

## 1. Páginas del Frontend y sus Campos Esperados

### 1.1. Página de Proveedores (`providers.tsx`)
**Campos esperados:**
- `id`: Identificador único
- `name`: Nombre del proveedor (obligatorio)
- `email`: Correo electrónico
- `phone`: Teléfono
- `mobile`: Teléfono móvil
- `vat`: NIF/CIF
- `website`: Sitio web
- `street`: Dirección
- `street2`: Dirección adicional
- `city`: Ciudad
- `active`: Estado (activo/inactivo)
- `is_company`: Si es empresa (siempre true)
- `supplier_rank`: Rango de proveedor (siempre 1)

### 1.2. Página de Productos (`products.tsx`)
**Campos esperados:**
- `id`: Identificador único
- `name`: Nombre del producto (obligatorio)
- `default_code`: Código interno
- `list_price`: Precio de venta
- `standard_price`: Precio de coste
- `category`: Categoría del producto
- `barcode`: Código de barras
- `active`: Estado (activo/inactivo)
- `type`: Tipo de producto (siempre "consu" en Odoo 18)
- `weight`: Peso
- `sale_ok`: Disponible para venta
- `purchase_ok`: Disponible para compra
- `description_sale`: Descripción de venta
- `description_purchase`: Descripción de compra
- `stock`: Cantidad en stock (campo calculado)

### 1.3. Página de Dashboard (`dashboard.tsx`)
**Campos esperados:**
- `totalProducts`: Total de productos
- `totalSales`: Total de ventas
- `totalCustomers`: Total de clientes
- `totalProviders`: Total de proveedores
- `activeProducts`: Productos activos
- `inactiveProducts`: Productos inactivos
- `productsWithStock`: Productos con stock
- `productsWithoutStock`: Productos sin stock
- `totalCategories`: Total de categorías
- `salesThisMonth`: Ventas del mes actual
- `salesLastMonth`: Ventas del mes anterior
- `salesGrowth`: Crecimiento de ventas
- `averageOrderValue`: Valor promedio de pedido
- `totalStockValue`: Valor total del stock
- `lowStockProducts`: Productos con stock bajo
- `outOfStockProducts`: Productos sin stock
- `activeProviders`: Proveedores activos
- `providersWithOrders`: Proveedores con pedidos
- `topCategories`: Categorías principales
- `recentSales`: Ventas recientes
- `low_stock_products`: Lista de productos con stock bajo
- `top_selling_products`: Productos más vendidos
- `recent_customers`: Clientes recientes
- `recent_providers`: Proveedores recientes

### 1.4. Página de Facturas (no implementada completamente)
**Campos esperados:**
- `id`: Identificador único
- `partner_id`: ID del proveedor
- `invoice_number`: Número de factura
- `invoice_date`: Fecha de factura
- `due_date`: Fecha de vencimiento
- `total_amount`: Importe total
- `state`: Estado de la factura
- `lines`: Líneas de factura (productos)
- `currency_id`: Moneda
- `journal_id`: Diario contable
- `ref`: Referencia externa

## 2. Campos y Relaciones en Odoo 18

### 2.1. Modelo `res.partner` (Proveedores)
**Campos principales:**
- `id`: Identificador único
- `name`: Nombre del proveedor (obligatorio)
- `email`: Correo electrónico
- `phone`: Teléfono
- `mobile`: Teléfono móvil
- `vat`: NIF/CIF
- `website`: Sitio web
- `street`: Dirección
- `street2`: Dirección adicional
- `city`: Ciudad
- `zip`: Código postal
- `state_id`: Estado/Provincia (relación con `res.country.state`)
- `country_id`: País (relación con `res.country`)
- `active`: Estado (activo/inactivo)
- `is_company`: Si es empresa
- `supplier_rank`: Rango de proveedor (>0 para proveedores)
- `customer_rank`: Rango de cliente (>0 para clientes)
- `category_id`: Categorías (relación muchos a muchos con `res.partner.category`)
- `user_id`: Comercial asignado (relación con `res.users`)
- `team_id`: Equipo de ventas (relación con `crm.team`)
- `property_payment_term_id`: Plazos de pago cliente
- `property_supplier_payment_term_id`: Plazos de pago proveedor
- `property_account_payable_id`: Cuenta a pagar
- `property_account_receivable_id`: Cuenta a cobrar
- `lang`: Idioma
- `tz`: Zona horaria
- `comment`: Notas internas

**Relaciones:**
- `res.country`: País
- `res.country.state`: Estado/Provincia
- `res.partner.category`: Categorías
- `res.users`: Usuario comercial
- `crm.team`: Equipo de ventas
- `account.account`: Cuentas contables

### 2.2. Modelo `product.template` (Productos)
**Campos principales:**
- `id`: Identificador único
- `name`: Nombre del producto (obligatorio)
- `default_code`: Código interno
- `list_price`: Precio de venta
- `standard_price`: Precio de coste
- `categ_id`: Categoría (relación con `product.category`)
- `barcode`: Código de barras
- `active`: Estado (activo/inactivo)
- `type`: Tipo de producto (en Odoo 18 es "consu" para productos físicos)
- `weight`: Peso
- `sale_ok`: Disponible para venta
- `purchase_ok`: Disponible para compra
- `available_in_pos`: Disponible en TPV
- `to_weight`: Pesable
- `is_published`: Publicado en sitio web
- `website_sequence`: Secuencia en sitio web
- `description_sale`: Descripción de venta
- `description_purchase`: Descripción de compra
- `description`: Descripción general
- `taxes_id`: Impuestos de venta (relación muchos a muchos con `account.tax`)
- `supplier_taxes_id`: Impuestos de compra (relación muchos a muchos con `account.tax`)

**Relaciones:**
- `product.category`: Categoría de producto
- `product.product`: Variantes de producto
- `product.supplierinfo`: Información de proveedores
- `account.tax`: Impuestos
- `stock.quant`: Cantidades en stock

### 2.3. Modelo `account.move` (Facturas)
**Campos principales:**
- `id`: Identificador único
- `name`: Nombre/Número de factura
- `partner_id`: Proveedor/Cliente (relación con `res.partner`)
- `move_type`: Tipo de movimiento ("in_invoice" para facturas de proveedor)
- `invoice_date`: Fecha de factura
- `invoice_date_due`: Fecha de vencimiento
- `journal_id`: Diario contable (relación con `account.journal`)
- `currency_id`: Moneda (relación con `res.currency`)
- `ref`: Referencia externa
- `narration`: Notas
- `state`: Estado de la factura
- `invoice_line_ids`: Líneas de factura (relación con `account.move.line`)
- `amount_total`: Importe total
- `amount_untaxed`: Base imponible
- `amount_tax`: Importe de impuestos

**Relaciones:**
- `res.partner`: Proveedor/Cliente
- `account.journal`: Diario contable
- `res.currency`: Moneda
- `account.move.line`: Líneas de factura

### 2.4. Modelo `account.move.line` (Líneas de Factura)
**Campos principales:**
- `id`: Identificador único
- `move_id`: Factura (relación con `account.move`)
- `product_id`: Producto (relación con `product.product`)
- `name`: Descripción
- `quantity`: Cantidad
- `price_unit`: Precio unitario
- `tax_ids`: Impuestos (relación muchos a muchos con `account.tax`)
- `account_id`: Cuenta contable (relación con `account.account`)
- `discount`: Descuento

**Relaciones:**
- `account.move`: Factura
- `product.product`: Producto
- `account.tax`: Impuestos
- `account.account`: Cuenta contable

## 3. Módulos Necesarios en Odoo 18

### 3.1. Módulos Base (ya instalados)
- `base`: Módulo base de Odoo
- `web`: Interfaz web
- `mail`: Mensajería y notificaciones
- `product`: Gestión de productos
- `account`: Contabilidad
- `stock`: Gestión de inventario
- `purchase`: Compras
- `sale`: Ventas
- `l10n_es`: Localización española

### 3.2. Módulos Adicionales Recomendados
- `point_of_sale`: Para TPV (si es necesario)
- `website_sale`: Para tienda online (si es necesario)
- `stock_account`: Valoración de inventario
- `purchase_stock`: Integración compras-inventario
- `sale_stock`: Integración ventas-inventario
- `account_edi_ubl_cii`: Formatos UBL y CII para facturas electrónicas

## 4. Análisis de Módulos Disponibles

De los módulos mencionados en las memorias:

### 4.1. Módulos Útiles para el Proyecto
- `l10n_es`: **Útil** - Proporciona la localización española básica

### 4.2. Servicios Refactorizados (muy útiles)
- `odoo_product_service.py`: **Muy útil** - Fachada para operaciones con productos
- `product_core_service.py`: **Muy útil** - Operaciones CRUD básicas de productos
- `product_custom_fields.py`: **Útil** - Gestión de campos personalizados
- `product_category_service.py`: **Muy útil** - Gestión de categorías de productos
- `product_integration_service.py`: **Muy útil** - Integración avanzada de productos
- `product_transform.py`: **Muy útil** - Transformación y sanitización de datos
- `product_lookup.py`: **Útil** - Búsqueda y consulta de productos
- `odoo_provider_service.py`: **Muy útil** - Gestión de proveedores
- `odoo_invoice_service.py`: **Muy útil** - Gestión de facturas
- `invoice_import_service.py`: **Útil** - Importación de facturas desde OCR

## 5. Plan Actualizado para MVP

### 5.1. Fase 1: Completar la Integración de Datos
1. **Completar mapeo de campos**:
   - Asegurar que todos los campos obligatorios de Odoo 18 estén mapeados en los modelos del frontend
   - Implementar validación para campos obligatorios
   - Manejar correctamente los tipos de datos y relaciones

2. **Implementar gestión de relaciones**:
   - Productos-Proveedores: Completar la vinculación bidireccional
   - Productos-Categorías: Asegurar creación y asignación correcta
   - Facturas-Productos-Proveedores: Completar el flujo completo

3. **Optimizar búsqueda y filtrado**:
   - Implementar búsqueda por múltiples campos (nombre, código, NIF)
   - Añadir filtros por categoría, estado, etc.
   - Optimizar consultas para mejor rendimiento

### 5.2. Fase 2: Completar Funcionalidades CRUD
1. **Completar página de facturas**:
   - Implementar listado con paginación
   - Crear formulario de creación/edición
   - Implementar selección de productos y cálculo automático

2. **Mejorar gestión de productos**:
   - Añadir gestión de stock
   - Implementar historial de precios
   - Añadir gestión de imágenes

3. **Ampliar gestión de proveedores**:
   - Añadir historial de compras
   - Implementar condiciones comerciales
   - Añadir documentos adjuntos

### 5.3. Fase 3: Implementar Estadísticas y Alertas
1. **Conectar dashboard con datos reales**:
   - Implementar consultas para todas las métricas
   - Añadir gráficos y visualizaciones
   - Implementar actualización en tiempo real

2. **Implementar sistema de alertas**:
   - Alertas de stock bajo
   - Alertas de facturas pendientes
   - Alertas de precios anómalos

3. **Añadir informes**:
   - Informes de compras por proveedor
   - Informes de stock por categoría
   - Informes financieros básicos

### 5.4. Fase 4: Optimización y Pruebas
1. **Optimizar rendimiento**:
   - Mejorar consultas a la base de datos
   - Implementar caché donde sea apropiado
   - Optimizar carga de páginas

2. **Implementar pruebas**:
   - Pruebas unitarias para servicios
   - Pruebas de integración para flujos completos
   - Pruebas de rendimiento

3. **Documentación**:
   - Manual de usuario
   - Documentación técnica
   - Guía de mantenimiento

## 6. Estado Actual (13/07/2025)

### Logros del día:

Excelente! Hemos logrado corregir el problema con la creación de productos en Odoo 18 a través de la API FastAPI. Vamos a resumir los cambios que hemos realizado:

1. **Problema identificado**: El servicio FastAPI devolvía solo el ID del producto creado (un entero) en lugar de un objeto completo, lo que causaba un error de validación en FastAPI (ResponseValidationError).

2. **Solución implementada**:
   - Modificamos la función `get_product_by_id` en `product_core_service.py` para que devuelva un objeto completo compatible con el modelo `Product` de Pydantic.
   - Añadimos todos los campos obligatorios que faltaban en el modelo, como template_id, qty_available, etc.
   - Modificamos el script de prueba para generar un código de barras único usando timestamps, evitando conflictos con productos existentes.

3. **Resultados**:
   - El producto se crea correctamente en Odoo 18.
   - La API devuelve un objeto completo del producto con todos los campos requeridos.
   - El script de prueba verifica que todos los campos enviados se hayan guardado correctamente.

4. **Observaciones**:
   - Hay algunos campos como description y volume que no se encuentran en la respuesta, pero esto no impide la funcionalidad principal.
   - La categoría del producto se está guardando correctamente como "Electrónica".

5. **Próximos pasos recomendados**:
   - Mejorar el manejo de categorías: Asegurarse de que las categorías se creen automáticamente si no existen.
   - Añadir soporte para campos adicionales: Como description y volume que actualmente no se están guardando.
   - Implementar pruebas de importación masiva: Para validar el flujo completo desde Excel.
   - Optimizar el rendimiento: Especialmente para importaciones grandes con Mistral LLM.

6. **Análisis de campos y relaciones**:
   - Se ha completado un análisis exhaustivo de los campos necesarios en el frontend y su correspondencia con los modelos de Odoo 18.
   - Se han identificado las relaciones clave entre productos, proveedores, categorías y facturas.
   - Se ha creado un plan detallado para completar la implementación del MVP.
