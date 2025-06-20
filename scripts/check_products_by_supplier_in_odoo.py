import xmlrpc.client

# Conexión a Odoo
url = 'http://localhost:8069'
db = 'manus_odoo-bd'
username = 'yo@mail.com'
password = 'admin'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Obtener todos los proveedores
suppliers = models.execute_kw(db, uid, password, 'res.partner', 'search_read', 
                             [[['supplier_rank', '>', 0]]], 
                             {'fields': ['id', 'name']})

print('Conteo de productos por proveedor en Odoo:')
total_products_with_supplier = 0
for supplier in suppliers:
    supplier_id = supplier['id']
    supplier_name = supplier['name']
    # Contar productos asociados a este proveedor
    supplier_info_ids = models.execute_kw(db, uid, password, 'product.supplierinfo', 'search', 
                                         [[['partner_id', '=', supplier_id]]])
    if supplier_info_ids:
        product_ids = models.execute_kw(db, uid, password, 'product.supplierinfo', 'read', 
                                       [supplier_info_ids, ['product_tmpl_id']])
        unique_products = set(info['product_tmpl_id'][0] for info in product_ids if info['product_tmpl_id'])
        count = len(unique_products)
        if count > 0:
            print(f'  - {supplier_name}: {count} productos')
            total_products_with_supplier += count

# Contar productos sin proveedor
all_product_ids = models.execute_kw(db, uid, password, 'product.template', 'search', [[]])
products_without_supplier = len(all_product_ids) - total_products_with_supplier
print(f'  - Sin proveedor asignado: {products_without_supplier} productos')
print(f'Total de productos en Odoo: {len(all_product_ids)}')
