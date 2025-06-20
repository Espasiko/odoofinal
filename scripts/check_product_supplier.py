import xmlrpc.client

# Conexión a Odoo
url = 'http://localhost:8069'
db = 'manus_odoo-bd'
username = 'yo@mail.com'
password = 'admin'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Buscar el producto por código
default_code = 'ADR(97)'
product_id = models.execute_kw(db, uid, password, 'product.template', 'search', [[['default_code', 'ilike', default_code]]])

if product_id:
    product_id = product_id[0]
    # Leer la información del producto y sus proveedores
    product_info = models.execute_kw(db, uid, password, 'product.template', 'read', [product_id, ['name', 'default_code', 'seller_ids']])
    print(f'Producto encontrado por código: {product_info[0]["name"]} con código {product_info[0]["default_code"]}')
    
    # Obtener información de los proveedores
    if product_info[0]['seller_ids']:
        sellers = models.execute_kw(db, uid, password, 'product.supplierinfo', 'read', [product_info[0]['seller_ids'], ['name']])
        if sellers:
            print('Proveedores asociados:')
            for seller in sellers:
                supplier_name = seller.get('name', 'Nombre no disponible')
                if isinstance(supplier_name, tuple):
                    supplier_name = supplier_name[1]  # Obtener el nombre del proveedor del tuple (id, name)
                print(f'  - {supplier_name}')
        else:
            print('No se encontraron detalles de proveedores.')
    else:
        print('No hay proveedores asociados a este producto.')
else:
    # Si no se encuentra por código, buscar por nombre
    product_id = models.execute_kw(db, uid, password, 'product.template', 'search', [[['name', 'ilike', default_code]]])
    if product_id:
        product_id = product_id[0]
        product_info = models.execute_kw(db, uid, password, 'product.template', 'read', [product_id, ['name', 'default_code', 'seller_ids']])
        print(f'Producto encontrado por nombre: {product_info[0]["name"]} con código {product_info[0]["default_code"]}')
        
        # Obtener información de los proveedores
        if product_info[0]['seller_ids']:
            sellers = models.execute_kw(db, uid, password, 'product.supplierinfo', 'read', [product_info[0]['seller_ids'], ['name']])
            if sellers:
                print('Proveedores asociados:')
                for seller in sellers:
                    supplier_name = seller.get('name', 'Nombre no disponible')
                    if isinstance(supplier_name, tuple):
                        supplier_name = supplier_name[1]  # Obtener el nombre del proveedor del tuple (id, name)
                    print(f'  - {supplier_name}')
            else:
                print('No se encontraron detalles de proveedores.')
        else:
            print('No hay proveedores asociados a este producto.')
    else:
        print(f'No se encontró un producto con el código o nombre {default_code}')
