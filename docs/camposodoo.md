# Campos Permitidos en Odoo 18 - Documentación Completa

## 📋 Resumen Ejecutivo

Esta documentación detalla todos los campos disponibles para la importación de productos, categorías y proveedores en Odoo 18, basada en el análisis de las plantillas encontradas en las carpetas `odoo_import` y `plantillasodoo`.

## 🛍️ Campos de Productos

### Campos Básicos Obligatorios

| Campo | Descripción | Formato | Ejemplo |
|-------|-------------|---------|----------|
| `External ID` | Identificador único del producto | `product_template_xxxxx` | `product_template_01951` |
| `Name` | Nombre del producto | Texto libre | `FRIGORÍFICO PUERTA FRANCESA BOLERO` |
| `Product Type` | Tipo de producto | `product` o `service` | `product` |
| `Internal Reference` | Código interno/referencia | Alfanumérico | `01951` |
| `Sales Price` | Precio de venta | Decimal con coma | `869,0` |
| `Cost` | Precio de coste | Decimal con coma | `521,66` |

### Campos Básicos Opcionales

| Campo | Descripción | Formato | Ejemplo |
|-------|-------------|---------|----------|
| `Barcode` | Código de barras | EAN-13 | `8436044530234` |
| `Weight` | Peso del producto | Decimal | `2,5` |
| `Sales Description` | Descripción para ventas | Texto libre | `Producto para venta` |

### Campos Avanzados de Configuración

| Campo | Descripción | Valores | Por Defecto |
|-------|-------------|---------|-------------|
| `sale_ok` | Disponible para venta | `True`/`False` | `True` |
| `purchase_ok` | Disponible para compra | `True`/`False` | `True` |
| `active` | Producto activo | `True`/`False` | `True` |
| `available_in_pos` | Disponible en TPV | `True`/`False` | `True` |
| `to_weight` | Producto a peso | `True`/`False` | `False` |
| `is_published` | Publicado en web | `True`/`False` | `True` |
| `website_sequence` | Secuencia en web | Numérico | `10` |

### Campos de Categorización

| Campo | Descripción | Formato | Ejemplo |
|-------|-------------|---------|----------|
| `categ_id` | Categoría del producto | Ruta jerárquica | `All/Saleable/Electrodomésticos` |
| `seller_ids/partner_id` | Proveedor | External ID | `res_partner_cecotec` |
| `product_tag_ids` | Etiquetas del producto | External ID | `tag_cecotec` |
| `public_categ_ids` | Categorías públicas | Ruta | `Electrodomésticos/CECOTEC` |
| `pos_categ_ids` | Categorías TPV | Texto | `Electrodomésticos` |

### Campos de Impuestos

| Campo | Descripción | Formato | Ejemplo |
|-------|-------------|---------|----------|
| `taxes_id` | Impuestos de venta | External ID | `account_tax_sale_21` |
| `supplier_taxes_id` | Impuestos de compra | External ID | `account_tax_purchase_21` |

### Campos de Descripción

| Campo | Descripción | Formato | Ejemplo |
|-------|-------------|---------|----------|
| `description_sale` | Descripción de venta | Texto libre | `Producto FRIGORÍFICO para venta` |
| `description_purchase` | Descripción de compra | Texto libre | `Producto FRIGORÍFICO para compra` |

## 🏷️ Campos de Categorías de Producto

### Campos Básicos

| Campo | Descripción | Formato | Ejemplo |
|-------|-------------|---------|----------|
| `id` | External ID de categoría | Texto | `product.product_category_all` |
| `name` | Nombre de la categoría | Texto libre | `All` |
| `parent_id` | Categoría padre | External ID | `product.product_category_all` |
| `child_id` | Categorías hijas | External ID | `All / Deliveries` |

### Campos Contables

| Campo | Descripción | Formato | Ejemplo |
|-------|-------------|---------|----------|
| `property_account_expense_categ_id` | Cuenta de gastos | External ID | `account.1_account_common_600` |
| `property_account_income_categ_id` | Cuenta de ingresos | External ID | `account.1_account_common_7000` |
| `property_stock_account_input_categ_id` | Cuenta entrada stock | External ID | `account.1_stock_input` |
| `property_stock_account_output_categ_id` | Cuenta salida stock | External ID | `account.1_stock_output` |
| `property_stock_valuation_account_id` | Cuenta valoración inventario | External ID | `account.1_inventory_valuation` |

### Campos de Configuración

| Campo | Descripción | Valores | Ejemplo |
|-------|-------------|---------|----------|
| `property_cost_method` | Método de coste | `standard`/`fifo`/`average` | `standard` |
| `property_valuation` | Valoración inventario | `manual_periodic`/`real_time` | `manual_periodic` |
| `removal_strategy_id` | Estrategia eliminación | External ID | `stock.removal_fifo` |
| `route_ids` | Rutas logísticas | External ID | `stock.route_warehouse0_mto` |

## 👥 Campos de Proveedores

### Información Básica

| Campo | Descripción | Formato | Ejemplo |
|-------|-------------|---------|----------|
| `supplier_id` | External ID proveedor | `res_partner_xxx` | `res_partner_cecotec` |
| `name` | Nombre del proveedor | Texto libre | `CECOTEC` |
| `currency` | Moneda | Código ISO | `EUR` |

### Lista de Precios de Proveedor

| Campo | Descripción | Formato | Ejemplo |
|-------|-------------|---------|----------|
| `supplier External ID` | ID del proveedor | External ID | `res_partner_cecotec` |
| `product reference` | Referencia del producto | Texto | `[BHB3525] BATIDORA VARILLA` |
| `quantity` | Cantidad mínima | Numérico | `1` |
| `price` | Precio del proveedor | Decimal con coma | `22,09` |

## 🎯 Atributos de Producto

### Configuración de Atributos

| Campo | Descripción | Valores | Ejemplo |
|-------|-------------|---------|----------|
| `attribute External ID` | ID del atributo | External ID | `website_sale.product_attribute_brand` |
| `Name` | Nombre del atributo | Texto libre | `Marca` |
| `display_type` | Tipo de visualización | `radio`/`select`/`color` | `radio` |
| `visibility` | Visibilidad | `visible`/`hidden` | `visible` |

## 📝 Formatos y Convenciones

### Formato de Archivos
- **Codificación**: UTF-8
- **Separador CSV**: Coma (`,`)
- **Separador decimal**: Coma (`,`)
- **Formato booleano**: `True`/`False`

### Convenciones de Nomenclatura
- **External ID productos**: `product_template_xxxxx` (5 dígitos)
- **External ID proveedores**: `res_partner_xxx`
- **External ID categorías**: `product.product_category_xxx`
- **External ID impuestos**: `account_tax_xxx_xx`

### Jerarquías
- **Categorías**: Usar `/` para separar niveles (`All/Saleable/Electrodomésticos`)
- **Cuentas contables**: Seguir plan contable español
- **Rutas**: Usar External IDs de rutas predefinidas

## 🔍 Fuentes de Información

### Archivos Analizados
1. **`/odoo_import/productoscsv-template.csv`** - 9 campos básicos
2. **`/odoo_import/Categoría de producto (product.category).csv`** - Estructura jerárquica
3. **`/odoo_import/Atributo de producto (product.attribute).csv`** - Configuración atributos
4. **`/odoo_import/Lista de precios de proveedor (product.supplierinfo).csv`** - Precios proveedor
5. **`/plantillasodoo/PVP_CECOTEC_template.csv`** - 22 campos completos
6. **`/plantillasodoo/Categoría de producto (product.category) (1).csv`** - Configuración contable

## ✅ Campos Recomendados para Importación Básica

### Mínimos Obligatorios
- `External ID`
- `Name`
- `Product Type`
- `Sales Price`
- `Cost`

### Recomendados Adicionales
- `Internal Reference`
- `categ_id`
- `supplier_id`
- `Sales Description`
- `active`
- `sale_ok`
- `purchase_ok`

### Para Tienda Online
- `Barcode`
- `Weight`
- `is_published`
- `website_sequence`
- `public_categ_ids`

### Para TPV
- `available_in_pos`
- `pos_categ_ids`
- `to_weight`

---

*Documentación generada para ManusOdoo - El Pelotazo Electrohogar*
*Versión Odoo: 18*