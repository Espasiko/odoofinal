# Plan de Acción para Mejorar el Flujo OCR de Facturas
**Fecha: 17/07/2025**

## Problemas Identificados

### 1. Datos del proveedor incompletos
- El proveedor existe en Odoo pero con datos incompletos: falta NIF/CIF, dirección completa, código postal
- Estos datos son correctamente extraídos por el OCR pero no se guardan en Odoo

### 2. Descuentos no aplicados
- El OCR detecta correctamente descuentos del 10% en varios productos
- Estos descuentos no se aplican en las líneas de factura en Odoo

### 3. Impuestos no aplicados
- El OCR detecta correctamente un impuesto del 5,2% (Recargo de Equivalencia)
- Este impuesto existe en Odoo (ID 153 y 322) pero no se aplica a la factura

### 4. Productos no vinculados
- Las líneas de factura no están vinculadas a productos reales en Odoo
- Solo se guardan como texto descriptivo sin referencias a `product_id`

## Plan de Acción

### Fase 1: Modificaciones en el backend (17/07/2025)
1. Actualizar el servicio `odoo_invoice_service.py` para incluir descuentos y manejar impuestos correctamente
2. Modificar el endpoint `mistral_free_ocr.py` para actualizar los datos del proveedor y pasar los descuentos

### Fase 2: Pruebas (18/07/2025)
1. Probar con la factura de Fabrilamp para verificar:
   - Actualización de datos del proveedor
   - Aplicación correcta de descuentos
   - Aplicación correcta de impuestos (5,2% RE)
   - Vinculación con productos existentes

### Fase 3: Mejoras en el frontend (19/07/2025)
1. Modificar el componente `ImportInvoice.tsx` para hacer obligatorio el NIF/CIF
2. Añadir validación del NIF/CIF según las normas españolas

### Fase 4: Documentación y despliegue (20/07/2025)
1. Actualizar la documentación del flujo OCR
2. Desplegar los cambios en el entorno de producción
3. Capacitar a los usuarios sobre los cambios realizados

## Soluciones Técnicas

### 1. Actualización de datos del proveedor
```python
# Código a añadir en mistral_free_ocr.py (función create_invoice_with_supplier)
# Después de la verificación del proveedor

# Actualizar datos del proveedor con la información del OCR
supplier_update_data = {}
if 'supplier_vat' in invoice_data and invoice_data['supplier_vat']:
    supplier_update_data['vat'] = invoice_data['supplier_vat']
if 'supplier_address' in invoice_data and invoice_data['supplier_address']:
    supplier_update_data['street'] = invoice_data['supplier_address']
if 'supplier_city' in invoice_data and invoice_data['supplier_city']:
    supplier_update_data['city'] = invoice_data['supplier_city']
if 'supplier_zip' in invoice_data and invoice_data['supplier_zip']:
    supplier_update_data['zip'] = invoice_data['supplier_zip']

# Actualizar proveedor si hay datos nuevos
if supplier_update_data:
    odoo_provider_service._execute_kw('res.partner', 'write', [[supplier_id], supplier_update_data])
```

### 2. Aplicación de descuentos
```python
# Modificar en mistral_free_ocr.py (creación de líneas de factura)
invoice_lines.append({
    'name': line_item.get('name', ''),
    'quantity': line_item.get('quantity', 1.0),
    'price_unit': adjust_price_for_supplier(supplier_details[0]['name'], line_item.get('price_unit', 0.0)),
    'default_code': line_item.get('default_code', ''),
    'discount': line_item.get('discount', 0.0)  # Añadir campo de descuento
})

# Modificar en odoo_invoice_service.py
line_vals = {
    "product_id": product_id or False,
    "name": l.get("name"),
    "quantity": l.get("quantity", 1.0),
    "price_unit": l.get("price_unit", 0.0),
    "discount": l.get("discount", 0.0)  # Añadir campo de descuento
}
```

### 3. Aplicación de impuestos
```python
# Modificar en odoo_invoice_service.py (aplicación de impuestos)
# Añadir impuestos según el tipo de producto y configuración del proveedor
if use_taxes:
    # Verificar si el proveedor tiene configurado Recargo de Equivalencia
    partner_data = self._execute_kw(
        "res.partner",
        "read",
        [[partner_id]],
        {"fields": ["property_account_position_id"]}
    )
    
    fiscal_position_id = partner_data[0].get('property_account_position_id', False)
    
    # Si tiene posición fiscal de Recargo de Equivalencia (ID 6)
    if fiscal_position_id and fiscal_position_id[0] == 6:
        # Aplicar IVA + RE
        if self.INVOICE_TAX_ID and self.RE_TAX_ID:
            line_vals["tax_ids"] = [(6, 0, [self.INVOICE_TAX_ID, self.RE_TAX_ID])]
    else:
        # Aplicar solo IVA normal
        if purchase_taxes:
            line_vals["tax_ids"] = [(6, 0, [purchase_taxes[0]])]
```

### 4. Mejora en la vinculación de productos
```python
# Modificar en odoo_invoice_service.py (método _ensure_product)
def _ensure_product(self, default_code: str, name: str) -> int:
    """Busca product.product por default_code o nombre, si no existe crea stub y devuelve product_id"""
    # Primero buscar por default_code
    product_domain = [("default_code", "=", default_code)]
    product_ids = self._execute_kw("product.product", "search", [product_domain], {"limit": 1})
    
    # Si no encuentra por default_code, buscar por nombre
    if not product_ids and name:
        product_domain = [("name", "ilike", name)]
        product_ids = self._execute_kw("product.product", "search", [product_domain], {"limit": 1})
    
    if product_ids:
        return product_ids[0]

    # Si no existe, crear un nuevo producto
    template_vals = {
        "name": name or default_code,
        "default_code": default_code,
        "type": "product",
    }
    template_id = self._execute_kw("product.template", "create", [[template_vals]])
    # product.product se crea automáticamente; buscarlo
    product_ids = self._execute_kw("product.product", "search", [[("product_tmpl_id", "=", template_id)]], {"limit": 1})
    return product_ids[0] if product_ids else 0
```

### 5. Validación de NIF/CIF en el frontend
- Implementar validación en tiempo real del NIF/CIF
- Desactivar el botón de envío si el NIF/CIF no es válido
- Mostrar mensaje de error específico si el formato es incorrecto
