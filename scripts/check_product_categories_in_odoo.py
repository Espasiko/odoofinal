import xmlrpc.client

# Conexión a Odoo
url = 'http://localhost:8069'
db = 'manus_odoo-bd'
username = 'yo@mail.com'
password = 'admin'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Obtener todas las categorías de productos
categories = models.execute_kw(db, uid, password, 'product.category', 'search_read', 
                              [[]], 
                              {'fields': ['id', 'name', 'parent_id']})

print('Categorías de productos definidas en Odoo:')
for cat in categories:
    parent = cat['parent_id'][1] if cat['parent_id'] else 'Ninguno'
    print(f'  - {cat["name"]} (ID: {cat["id"]}, Padre: {parent})')

# Contar productos por categoría
print('\nConteo de productos por categoría:')
for cat in categories:
    cat_id = cat['id']
    product_count = len(models.execute_kw(db, uid, password, 'product.template', 'search', [[['categ_id', '=', cat_id]]]))
    if product_count > 0:
        print(f'  - {cat["name"]}: {product_count} productos')

# Verificar categorías en PoS
pos_categories = models.execute_kw(db, uid, password, 'pos.category', 'search_read', 
                                  [[]], 
                                  {'fields': ['id', 'name']})

print('\nCategorías definidas en Punto de Venta (PoS):')
for pos_cat in pos_categories:
    print(f'  - {pos_cat["name"]} (ID: {pos_cat["id"]})')

# Nota: No hay un campo específico para 'sitio web', 'inventario' o 'facturación' en las categorías,
# pero las categorías de productos son generalmente utilizadas en todos los módulos si están definidas.
print('\nNota: Las categorías de productos son utilizadas generalmente en inventario, facturación, etc., siempre que estén asignadas a productos.')
