import xmlrpc.client

# Conexión a Odoo
url = 'http://localhost:8069'
db = 'manus_odoo-bd'
username = 'yo@mail.com'
password = 'admin'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Crear categoría 'Freidoras' si no existe
freidoras_cat_id = models.execute_kw(db, uid, password, 'product.category', 'search', [[['name', '=', 'Freidoras']]])
if not freidoras_cat_id:
    freidoras_cat_id = models.execute_kw(db, uid, password, 'product.category', 'create', [{'name': 'Freidoras'}])
    print(f'Creada categoría "Freidoras" con ID: {freidoras_cat_id}')
else:
    freidoras_cat_id = freidoras_cat_id[0]
    print(f'Categoría "Freidoras" ya existe con ID: {freidoras_cat_id}')

# Crear categoría PoS 'Freidoras' si no existe
pos_freidoras_cat_id = models.execute_kw(db, uid, password, 'pos.category', 'search', [[['name', '=', 'Freidoras']]])
if not pos_freidoras_cat_id:
    pos_freidoras_cat_id = models.execute_kw(db, uid, password, 'pos.category', 'create', [{'name': 'Freidoras'}])
    print(f'Creada categoría PoS "Freidoras" con ID: {pos_freidoras_cat_id}')
else:
    pos_freidoras_cat_id = pos_freidoras_cat_id[0]
    print(f'Categoría PoS "Freidoras" ya existe con ID: {pos_freidoras_cat_id}')

# Obtener ID de la categoría 'Otros Electrodomésticos'
otros_cat_id = models.execute_kw(db, uid, password, 'product.category', 'search', [[['name', '=', 'Otros Electrodomésticos']]])
if otros_cat_id:
    otros_cat_id = otros_cat_id[0]
    print(f'Categoría "Otros Electrodomésticos" encontrada con ID: {otros_cat_id}')
else:
    otros_cat_id = models.execute_kw(db, uid, password, 'product.category', 'create', [{'name': 'Otros Electrodomésticos'}])
    print(f'Creada categoría "Otros Electrodomésticos" con ID: {otros_cat_id}')

# Obtener productos en la categoría 'Aires Acondicionados' (ID: 7)
air_products = models.execute_kw(db, uid, password, 'product.template', 'search_read', 
                                [[['categ_id', '=', 7]]], 
                                {'fields': ['id', 'name', 'default_code']})

print(f'Total de productos en "Aires Acondicionados": {len(air_products)}')

# Reasignar productos
freidoras_count = 0
otros_count = 0
remain_count = 0
for product in air_products:
    prod_name = product['name'].lower()
    prod_id = product['id']
    if any(term in prod_name for term in ['freidora', 'airfryer', 'papel', 'accesorio']):
        # Reasignar a 'Freidoras'
        models.execute_kw(db, uid, password, 'product.template', 'write', [[prod_id], {'categ_id': freidoras_cat_id}])
        # Añadir etiqueta 'Accesorios' si es un accesorio
        if any(term in prod_name for term in ['papel', 'accesorio']):
            tag_id = models.execute_kw(db, uid, password, 'product.tag', 'search', [[['name', '=', 'Accesorios']]])
            if not tag_id:
                tag_id = models.execute_kw(db, uid, password, 'product.tag', 'create', [{'name': 'Accesorios'}])
            else:
                tag_id = tag_id[0]
            models.execute_kw(db, uid, password, 'product.template', 'write', [[prod_id], {'product_tag_ids': [(4, tag_id)]}])
        freidoras_count += 1
        print(f'Reasignado "{product["name"]}" a "Freidoras"')
    elif 'hielo' in prod_name:
        # Reasignar a 'Otros Electrodomésticos'
        models.execute_kw(db, uid, password, 'product.template', 'write', [[prod_id], {'categ_id': otros_cat_id}])
        otros_count += 1
        print(f'Reasignado "{product["name"]}" a "Otros Electrodomésticos"')
    else:
        remain_count += 1
        print(f'Manteniendo "{product["name"]}" en "Aires Acondicionados"')

print(f'Resumen: {freidoras_count} productos a "Freidoras", {otros_count} a "Otros Electrodomésticos", {remain_count} permanecen en "Aires Acondicionados"')

# Renombrar categoría 'Aire Acondicionado' (ID: 38) para evitar confusión
single_air_cat_id = 38
single_air_products = models.execute_kw(db, uid, password, 'product.template', 'search', [[['categ_id', '=', single_air_cat_id]]])
if not single_air_products:
    models.execute_kw(db, uid, password, 'product.category', 'write', [[single_air_cat_id], {'name': 'Aire Acondicionado (Obsoleto)'}])
    print('Renombrada categoría "Aire Acondicionado" (ID: 38) a "Aire Acondicionado (Obsoleto)" ya que no tiene productos asignados')
else:
    print(f'No se renombró "Aire Acondicionado" (ID: 38) porque tiene {len(single_air_products)} productos asignados')
