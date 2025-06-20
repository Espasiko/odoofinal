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
                              {'fields': ['id', 'name']})

print('Sincronizando categorías de productos a Punto de Venta (PoS):')
created_count = 0
for cat in categories:
    # Verificar si la categoría ya existe en PoS
    pos_cat_id = models.execute_kw(db, uid, password, 'pos.category', 'search', 
                                  [[['name', '=', cat['name']]]])
    if not pos_cat_id:
        # Crear la categoría en PoS
        new_pos_cat = models.execute_kw(db, uid, password, 'pos.category', 'create', 
                                       [{'name': cat['name']}])
        created_count += 1
        print(f'  - Creada categoría PoS: {cat["name"]} (ID: {new_pos_cat})')
    else:
        print(f'  - Categoría PoS ya existe: {cat["name"]} (ID: {pos_cat_id[0]})')

print(f'Total de categorías PoS creadas: {created_count}')
