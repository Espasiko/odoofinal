# Documentación Técnica - Módulo Custom Electrodomésticos

## Estructura de la Base de Datos

### Modelos Estándar de Odoo Utilizados

#### product.template
Modelo principal para la gestión de productos.

```python
class ProductTemplate(models.Model):
    _name = 'product.template'
    _description = 'Product Template'
    
    name = fields.Char('Name', required=True)
    default_code = fields.Char('Internal Reference')
    list_price = fields.Float('Sales Price')
    standard_price = fields.Float('Cost')
    categ_id = fields.Many2one('product.category', 'Product Category')
    type = fields.Selection([
        ('consu', 'Consumable'),
        ('service', 'Service'),
        ('product', 'Storable Product')
    ], 'Product Type')
    sale_ok = fields.Boolean('Can be Sold')
    purchase_ok = fields.Boolean('Can be Purchased')
    # ... otros campos estándar
```

#### product.product
Variantes de producto basadas en product.template.

```python
class ProductProduct(models.Model):
    _name = 'product.product'
    _description = 'Product'
    
    product_tmpl_id = fields.Many2one('product.template', 'Product Template')
    # ... otros campos estándar
```

#### product.category
Categorías de productos.

```python
class ProductCategory(models.Model):
    _name = 'product.category'
    _description = 'Product Category'
    
    name = fields.Char('Name', required=True)
    parent_id = fields.Many2one('product.category', 'Parent Category')
    # ... otros campos estándar
```

#### product.supplierinfo
Información de proveedores para productos.

```python
class ProductSupplierinfo(models.Model):
    _name = 'product.supplierinfo'
    _description = 'Supplier Pricelist'
    
    name = fields.Many2one('res.partner', 'Vendor', required=True)
    product_tmpl_id = fields.Many2one('product.template', 'Product Template')
    product_id = fields.Many2one('product.product', 'Product Variant')
    price = fields.Float('Price')
    # ... otros campos estándar
```

#### stock.quant
Cantidades de stock.

```python
class StockQuant(models.Model):
    _name = 'stock.quant'
    _description = 'Quants'
    
    product_id = fields.Many2one('product.product', 'Product')
    location_id = fields.Many2one('stock.location', 'Location')
    quantity = fields.Float('Quantity')
    # ... otros campos estándar
```

#### res.partner
Proveedores y clientes.

```python
class ResPartner(models.Model):
    _name = 'res.partner'
    _description = 'Contact'
    
    name = fields.Char('Name', required=True)
    supplier_rank = fields.Integer('Supplier Rank')
    customer_rank = fields.Integer('Customer Rank')
    # ... otros campos estándar
```

### Campos Personalizados Añadidos

#### En product.template

```python
class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    x_codigo_proveedor = fields.Char('Código Proveedor')
    x_margen = fields.Float('Margen (%)')
    x_pvp_web = fields.Float('PVP Web')
    x_beneficio_unitario = fields.Float('Beneficio Unitario', compute='_compute_beneficio')
    x_marca = fields.Char('Marca')
    x_modelo = fields.Char('Modelo')
    x_historico_ventas = fields.Text('Histórico Ventas')
    x_notas_importacion = fields.Text('Notas Importación')
    x_notas = fields.Text('Notas')
    x_vendidas = fields.Integer('Unidades Vendidas')
    x_quedan_tienda = fields.Integer('Unidades en Tienda')
    x_estado_producto = fields.Selection([
        ('activo', 'Activo'),
        ('roto', 'Roto'),
        ('devuelto', 'Devuelto'),
        ('reclamacion', 'Reclamación')
    ], 'Estado del Producto', default='activo')
    
    def _compute_beneficio(self):
        for product in self:
            product.x_beneficio_unitario = product.list_price - product.standard_price
```

#### En product.category

```python
class ProductCategory(models.Model):
    _inherit = 'product.category'
    
    x_codigo_categoria = fields.Char('Código Categoría')
    x_margen_categoria = fields.Float('Margen Categoría (%)')
```

### Nuevos Modelos Creados

#### product.incident
Gestión de incidencias de productos.

```python
class ProductIncident(models.Model):
    _name = 'product.incident'
    _description = 'Incidencias de Productos'
    _rec_name = 'reference'
    _order = 'fecha desc, id desc'
    
    reference = fields.Char('Referencia', readonly=True, default='/')
    product_tmpl_id = fields.Many2one('product.template', 'Producto', required=True)
    fecha = fields.Date('Fecha', default=fields.Date.context_today, required=True)
    tipo = fields.Selection([
        ('roto', 'Roto'),
        ('devuelto', 'Devuelto'),
        ('reclamacion', 'Reclamación')
    ], 'Tipo de Incidencia', required=True)
    motivo = fields.Text('Motivo')
    partner_id = fields.Many2one('res.partner', 'Cliente')
    importe = fields.Float('Importe')
    impuesto = fields.Float('Impuesto')
    total = fields.Float('Total', compute='_compute_total')
    reembolso = fields.Boolean('Reembolso')
    notas = fields.Text('Notas')
    state = fields.Selection([
        ('borrador', 'Borrador'),
        ('confirmado', 'Confirmado'),
        ('resuelto', 'Resuelto'),
        ('cancelado', 'Cancelado')
    ], 'Estado', default='borrador')
    
    @api.model
    def create(self, vals):
        if vals.get('reference', '/') == '/':
            vals['reference'] = self.env['ir.sequence'].next_by_code('product.incident') or '/'
        return super(ProductIncident, self).create(vals)
    
    @api.depends('importe', 'impuesto')
    def _compute_total(self):
        for incident in self:
            incident.total = incident.importe + incident.impuesto
    
    @api.model
    def create(self, vals):
        res = super(ProductIncident, self).create(vals)
        if res.product_tmpl_id and res.tipo:
            res.product_tmpl_id.write({'x_estado_producto': res.tipo})
        return res
```

#### product.sales.history
Historial de ventas de productos.

```python
class ProductSalesHistory(models.Model):
    _name = 'product.sales.history'
    _description = 'Historial de Ventas de Productos'
    _rec_name = 'reference'
    _order = 'fecha desc, id desc'
    
    reference = fields.Char('Referencia', readonly=True, default='/')
    product_tmpl_id = fields.Many2one('product.template', 'Producto', required=True)
    fecha = fields.Date('Fecha de Venta', default=fields.Date.context_today, required=True)
    cantidad = fields.Integer('Cantidad Vendida', default=1)
    precio_unitario = fields.Float('Precio Unitario')
    total = fields.Float('Total', compute='_compute_total')
    partner_id = fields.Many2one('res.partner', 'Cliente')
    factura_id = fields.Many2one('account.move', 'Factura')
    notas = fields.Text('Notas')
    
    @api.model
    def create(self, vals):
        if vals.get('reference', '/') == '/':
            vals['reference'] = self.env['ir.sequence'].next_by_code('product.sales.history') or '/'
        return super(ProductSalesHistory, self).create(vals)
    
    @api.depends('cantidad', 'precio_unitario')
    def _compute_total(self):
        for record in self:
            record.total = record.cantidad * record.precio_unitario
    
    @api.model
    def create(self, vals):
        res = super(ProductSalesHistory, self).create(vals)
        if res.product_tmpl_id and res.cantidad:
            vendidas = res.product_tmpl_id.x_vendidas or 0
            res.product_tmpl_id.write({'x_vendidas': vendidas + res.cantidad})
        return res
```

## Diagrama de Relaciones

```
+-------------------+       +-------------------+       +-------------------+
|  product.template  |------>|  product.product  |------>|    stock.quant    |
+-------------------+       +-------------------+       +-------------------+
         |                           |
         |                           |
         v                           v
+-------------------+       +-------------------+
|  product.category  |       | product.supplierinfo |
+-------------------+       +-------------------+
                                     |
                                     |
                                     v
                            +-------------------+
                            |    res.partner    |
                            +-------------------+
         |                           |
         |                           |
         v                           v
+-------------------+       +-------------------+
|  product.incident  |       | product.sales.history |
+-------------------+       +-------------------+
```

## Flujo de Datos

### Importación desde Excel

1. Los archivos Excel se procesan mediante el script `script_migracion_excel_odoo.py`
2. Se identifican los proveedores a partir del nombre del archivo
3. Se crean o actualizan productos en `product.template`
4. Se procesan las hojas especiales:
   - **VENDIDO**: Actualiza `x_vendidas` y `x_quedan_tienda` y crea registros en `product.sales.history`
   - **ROTO**, **DEVOLUCIONES**, **RECLAMACIONES**: Actualiza `x_estado_producto` y crea registros en `product.incident`

### Flujo de Incidencias

1. Se crea una incidencia en `product.incident`
2. El estado del producto (`x_estado_producto`) se actualiza automáticamente
3. La incidencia pasa por los estados: borrador → confirmado → resuelto/cancelado

### Flujo de Ventas

1. Se registra una venta en `product.sales.history`
2. El contador de unidades vendidas (`x_vendidas`) se incrementa automáticamente

## Permisos y Seguridad

### Grupos de Seguridad

- **Usuario Electrodomésticos**: Acceso de lectura y escritura básico
- **Manager Electrodomésticos**: Acceso completo incluyendo eliminación

### Reglas de Acceso

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_product_incident_user,product.incident.user,model_product_incident,base.group_user,1,1,1,0
access_product_incident_manager,product.incident.manager,model_product_incident,base.group_system,1,1,1,1
access_product_sales_history_user,product.sales.history.user,model_product_sales_history,base.group_user,1,1,1,0
access_product_sales_history_manager,product.sales.history.manager,model_product_sales_history,base.group_system,1,1,1,1
```

## Interfaz de Usuario

### Vistas Principales

#### product.template (Form View)

```xml
<record id="product_template_form_view_inherit" model="ir.ui.view">
    <field name="name">product.template.form.inherit</field>
    <field name="model">product.template</field>
    <field name="inherit_id" ref="product.product_template_form_view"/>
    <field name="arch" type="xml">
        <xpath expr="//div[@name='options']" position="inside">
            <div>
                <field name="x_estado_producto" widget="badge" 
                       decoration-success="x_estado_producto == 'activo'" 
                       decoration-danger="x_estado_producto == 'roto'" 
                       decoration-warning="x_estado_producto == 'devuelto'" 
                       decoration-info="x_estado_producto == 'reclamacion'"/>
            </div>
        </xpath>
        
        <notebook position="inside">
            <page string="Información Adicional" name="info_adicional">
                <group>
                    <group>
                        <field name="x_codigo_proveedor"/>
                        <field name="x_marca"/>
                        <field name="x_modelo"/>
                        <field name="x_vendidas"/>
                        <field name="x_quedan_tienda"/>
                    </group>
                    <group>
                        <field name="x_margen"/>
                        <field name="x_pvp_web"/>
                        <field name="x_beneficio_unitario"/>
                    </group>
                </group>
                <group string="Notas">
                    <field name="x_notas" nolabel="1" placeholder="Notas generales sobre el producto..."/>
                </group>
                <group string="Notas de Importación">
                    <field name="x_notas_importacion" nolabel="1" readonly="1"/>
                </group>
            </page>
            
            <page string="Incidencias" name="incidencias">
                <field name="incident_ids" readonly="1">
                    <tree>
                        <field name="reference"/>
                        <field name="fecha"/>
                        <field name="tipo"/>
                        <field name="motivo"/>
                        <field name="partner_id"/>
                        <field name="total" sum="Total"/>
                        <field name="state"/>
                    </tree>
                </field>
            </page>
            
            <page string="Historial de Ventas" name="historial_ventas">
                <field name="sales_history_ids" readonly="1">
                    <tree>
                        <field name="reference"/>
                        <field name="fecha"/>
                        <field name="cantidad" sum="Total Unidades"/>
                        <field name="precio_unitario"/>
                        <field name="total" sum="Total Ventas"/>
                        <field name="partner_id"/>
                        <field name="factura_id"/>
                    </tree>
                </field>
            </page>
        </notebook>
    </field>
</record>
```

#### product.incident (Form View)

```xml
<record id="view_product_incident_form" model="ir.ui.view">
    <field name="name">product.incident.form</field>
    <field name="model">product.incident</field>
    <field name="arch" type="xml">
        <form string="Incidencia de Producto">
            <header>
                <button name="action_confirm" string="Confirmar" type="object" 
                        states="borrador" class="oe_highlight"/>
                <button name="action_resolve" string="Resolver" type="object" 
                        states="confirmado" class="oe_highlight"/>
                <button name="action_cancel" string="Cancelar" type="object" 
                        states="borrador,confirmado"/>
                <button name="action_draft" string="Volver a Borrador" type="object" 
                        states="cancelado"/>
                <field name="state" widget="statusbar" 
                       statusbar_visible="borrador,confirmado,resuelto"/>
            </header>
            <sheet>
                <div class="oe_title">
                    <h1>
                        <field name="reference" readonly="1"/>
                    </h1>
                </div>
                <group>
                    <group>
                        <field name="product_tmpl_id"/>
                        <field name="fecha"/>
                        <field name="tipo"/>
                        <field name="partner_id"/>
                    </group>
                    <group>
                        <field name="importe"/>
                        <field name="impuesto"/>
                        <field name="total"/>
                        <field name="reembolso"/>
                    </group>
                </group>
                <notebook>
                    <page string="Motivo">
                        <field name="motivo" placeholder="Describa el motivo de la incidencia..."/>
                    </page>
                    <page string="Notas">
                        <field name="notas" placeholder="Notas adicionales..."/>
                    </page>
                </notebook>
            </sheet>
            <div class="oe_chatter">
                <field name="message_follower_ids" widget="mail_followers"/>
                <field name="message_ids" widget="mail_thread"/>
            </div>
        </form>
    </field>
</record>
```

#### product.sales.history (Form View)

```xml
<record id="view_product_sales_history_form" model="ir.ui.view">
    <field name="name">product.sales.history.form</field>
    <field name="model">product.sales.history</field>
    <field name="arch" type="xml">
        <form string="Historial de Ventas">
            <sheet>
                <div class="oe_title">
                    <h1>
                        <field name="reference" readonly="1"/>
                    </h1>
                </div>
                <group>
                    <group>
                        <field name="product_tmpl_id"/>
                        <field name="fecha"/>
                        <field name="cantidad"/>
                        <field name="precio_unitario"/>
                    </group>
                    <group>
                        <field name="total"/>
                        <field name="partner_id"/>
                        <field name="factura_id"/>
                    </group>
                </group>
                <notebook>
                    <page string="Notas">
                        <field name="notas" placeholder="Notas sobre la venta..."/>
                    </page>
                </notebook>
            </sheet>
        </form>
    </field>
</record>
```

## Secuencias

```xml
<record id="seq_product_incident" model="ir.sequence">
    <field name="name">Secuencia de Incidencias</field>
    <field name="code">product.incident</field>
    <field name="prefix">INC/%(year)s/</field>
    <field name="padding">4</field>
    <field name="company_id" eval="False"/>
</record>

<record id="seq_product_sales_history" model="ir.sequence">
    <field name="name">Secuencia de Historial de Ventas</field>
    <field name="code">product.sales.history</field>
    <field name="prefix">HST/%(year)s/</field>
    <field name="padding">4</field>
    <field name="company_id" eval="False"/>
</record>
```

## Script de Migración

El script `script_migracion_excel_odoo.py` realiza las siguientes operaciones:

1. Conexión a Odoo mediante XML-RPC
2. Lectura de archivos Excel en el directorio `/home/espasiko/manusodoo/last/ejemplos/`
3. Procesamiento de hojas principales para crear/actualizar productos
4. Procesamiento de hojas especiales para crear incidencias y registros de ventas
5. Actualización de campos personalizados en productos

## Consideraciones Técnicas

### Rendimiento

- Los campos computados como `x_beneficio_unitario` pueden afectar al rendimiento si se calculan en tiempo real para muchos productos
- La migración de grandes volúmenes de datos debe realizarse por lotes para evitar problemas de memoria

### Mantenimiento

- Las actualizaciones de Odoo pueden requerir ajustes en las vistas heredadas
- Los campos personalizados (con prefijo `x_`) son persistentes entre actualizaciones

### Extensibilidad

El módulo puede extenderse para incluir:

- Integración con sistemas de gestión de almacén
- Reportes avanzados de rentabilidad
- Automatización de procesos de devolución
- Integración con tiendas online

## Solución de Problemas

### Problemas Comunes

1. **Error en la migración de datos**
   - Verificar formato de archivos Excel
   - Comprobar permisos de usuario
   - Revisar logs en `migracion_excel_odoo.log`

2. **Campos personalizados no visibles**
   - Actualizar vistas desde Desarrollo > Actualizar Lista de Vistas
   - Verificar permisos de acceso

3. **Errores en la creación de incidencias**
   - Verificar que la secuencia `product.incident` está creada
   - Comprobar restricciones de campos obligatorios

## Conclusión

Este módulo personalizado proporciona una solución completa para la gestión de productos de electrodomésticos en Odoo, con funcionalidades específicas para el seguimiento de incidencias, historial de ventas y campos personalizados. La estructura modular permite una fácil extensión y mantenimiento a largo plazo.