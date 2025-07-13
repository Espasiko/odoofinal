# Estado de los Flujos de Importación en Manusodoo (12/07/2025)

## 1. Flujo de Importación de Facturas (OCR/Excel)
- El servicio `InvoiceImportService` orquesta la importación de facturas desde OCR o Excel.
- Utiliza adapters para parsear el JSON y extraer datos estructurados (proveedor, productos, líneas).
- **Gestión de proveedores:**
  - Llama a `odoo_provider_service.create_provider` para buscar por NIF/email/nombre.
  - Si el proveedor existe, lo actualiza con los nuevos datos (dirección, email, etc.).
  - Si no existe, lo crea.
- **Gestión de productos:**
  - Llama a `odoo_product_service.create_or_update_product` para cada producto de la factura.
  - Si el producto existe (por código), lo actualiza; si no, lo crea.
- **Creación de orden de compra y factura:**
  - Se crea la orden de compra y luego la factura asociada usando los servicios correspondientes.
- **Limitaciones actuales:**
  - Si falla la creación de productos/categorías, la factura puede quedar incompleta.
  - El servicio de facturas espera siempre recibir un `partner_id` válido (proveedor ya gestionado).

## 2. Flujo de Importación de Productos desde Excel
- Se normalizan y validan los datos con LLM/OCR antes de importar.
- Se crean productos, categorías y proveedores en Odoo, gestionando relaciones y evitando duplicados.
- Lógica robusta para conversión de formatos, creación/actualización de proveedores y categorías, y logs detallados.
- Se prioriza la integridad de los datos y la trazabilidad de los errores.

## 3. Propuesta de Mejora para el Flujo de Facturas
- Robustecer `odoo_provider_service` para asegurar actualización/creación correcta de proveedores.
- Confirmar que `invoice_import_service` siempre usa el método robusto de proveedores antes de crear la factura.
- No es necesario modificar `odoo_invoice_service` si recibe siempre el `partner_id` correcto.

---

## 4. Última Incidencia Detectada (12/07/2025)
- Tras importar un Excel desde la UI y otro desde el endpoint, la IA devolvió el siguiente JSON:

```
"proveedor": "ALMCE",
"result": { ... },
"productos_creados": [],
"productos_fallidos": [
  {"idx": 0, "name": "LAVADORA CORBERÓ 7KG \"A\"", "error": "No se pudo crear en Odoo", "default_code": "CLT704VIN"},
  ...
],
"total_intentados": 5,
"total_creados": 0,
"total_fallidos": 5
```

- El proveedor se ha creado correctamente, pero **los productos y las categorías no**.
- Próximo paso: **Averiguar por qué no se crean los productos/categorías** y en qué parte del flujo se produce el fallo.

---

*Documento generado automáticamente por Cascade el 12/07/2025.*
