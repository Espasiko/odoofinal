import xmlrpc.client

# Conexión a Odoo
url = 'http://localhost:8069'
db = 'manus_odoo-bd'
username = 'yo@mail.com'
password = 'admin'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Obtener todos los proveedores (contactos con supplier_rank > 0)
suppliers = models.execute_kw(db, uid, password, 'res.partner', 'search_read', 
                             [[['supplier_rank', '>', 0]]], 
                             {'fields': ['id', 'name', 'supplier_rank']})

print('Proveedores configurados en Odoo (con supplier_rank > 0):')
visible_suppliers = []
for supplier in suppliers:
    supplier_id = supplier['id']
    supplier_name = supplier['name']
    visible_suppliers.append(supplier_name)
    print(f'  - {supplier_name} (ID: {supplier_id}, Rank: {supplier["supplier_rank"]}')

# Obtener todos los contactos asociados a productos como proveedores
supplier_info_ids = models.execute_kw(db, uid, password, 'product.supplierinfo', 'search', [[]])
supplier_infos = models.execute_kw(db, uid, password, 'product.supplierinfo', 'read', 
                                  [supplier_info_ids, ['partner_id']])

associated_suppliers = set()
for info in supplier_infos:
    if info['partner_id']:
        associated_suppliers.add(info['partner_id'][1])

print('\nProveedores asociados a productos en Odoo (en product.supplierinfo):')
for supplier_name in associated_suppliers:
    print(f'  - {supplier_name}')

print('\nProveedores configurados pero no asociados a productos:')
for supplier_name in visible_suppliers:
    if supplier_name not in associated_suppliers:
        print(f'  - {supplier_name}')
