import xmlrpc.client

# Conexión a Odoo
url = 'http://localhost:8069'
db = 'manus_odoo-bd'
username = 'yo@mail.com'
password = 'admin'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Buscar el producto por nombre
product_name = 'A/A PORTATIL + CALEFACCION'
product_id = models.execute_kw(db, uid, password, 'product.template', 'search', [[['name', '=', product_name]]])

if product_id:
    product_id = product_id[0]
    print(f'Producto encontrado: {product_name} con ID {product_id}')
    
    # Leer la configuración actual del producto
    current_product = models.execute_kw(db, uid, password, 'product.template', 'read', [product_id, ['type', 'name', 'route_ids']])
    print(f'Configuración actual del producto: Tipo: {current_product[0]["type"]}, Nombre: {current_product[0]["name"]}, Rutas: {current_product[0]["route_ids"]}')
    
    # Buscar la ruta de reabastecimiento 'Comprar'
    route_buy_id = models.execute_kw(db, uid, password, 'stock.location.route', 'search', [[['name', 'ilike', 'Buy']]])
    if route_buy_id:
        route_buy_id = route_buy_id[0]
        print(f'Ruta de reabastecimiento "Comprar" encontrada con ID {route_buy_id}')
        
        # Actualizar el producto para incluir la ruta de reabastecimiento 'Comprar'
        try:
            models.execute_kw(db, uid, password, 'product.template', 'write', [[product_id], {'route_ids': [(4, route_buy_id)]}])
            print(f'Ruta de reabastecimiento "Comprar" añadida al producto {product_name}')
        except Exception as e:
            print(f'Error al añadir la ruta de reabastecimiento: {e}')
    else:
        print('No se encontró la ruta de reabastecimiento "Comprar".')
    
    # Verificar la configuración actualizada
    updated_product = models.execute_kw(db, uid, password, 'product.template', 'read', [product_id, ['type', 'name', 'route_ids']])
    print(f'Configuración actualizada del producto: Tipo: {updated_product[0]["type"]}, Nombre: {updated_product[0]["name"]}, Rutas: {updated_product[0]["route_ids"]}')
else:
    print(f'No se encontró el producto con nombre {product_name}')
