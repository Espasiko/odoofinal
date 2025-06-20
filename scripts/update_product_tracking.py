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
    current_product = models.execute_kw(db, uid, password, 'product.template', 'read', [product_id, ['type', 'name', 'tracking']])
    print(f'Configuración actual del producto: Tipo: {current_product[0]["type"]}, Nombre: {current_product[0]["name"]}, Rastreo: {current_product[0]["tracking"]}')
    
    # Intentar actualizar el rastreo de inventario a 'lot' (por lote)
    try:
        models.execute_kw(db, uid, password, 'product.template', 'write', [[product_id], {'tracking': 'lot'}])
        print(f'Rastreo de inventario actualizado a "lot" para el producto {product_name}')
    except Exception as e:
        print(f'Error al actualizar el rastreo de inventario: {e}')
        # Si falla, obtener las opciones disponibles para el campo tracking
        try:
            field_info = models.execute_kw(db, uid, password, 'ir.model.fields', 'search_read', [[['model', '=', 'product.template'], ['name', '=', 'tracking']]], {'fields': ['selection']})
            if field_info and 'selection' in field_info[0]:
                print(f'Opciones disponibles para el campo tracking: {field_info[0]["selection"]}')
            else:
                print('No se encontraron opciones para el campo tracking.')
        except Exception as e2:
            print(f'Error al obtener opciones para el campo tracking: {e2}')
    
    # Verificar la configuración actualizada
    updated_product = models.execute_kw(db, uid, password, 'product.template', 'read', [product_id, ['type', 'name', 'tracking']])
    print(f'Configuración actualizada del producto: Tipo: {updated_product[0]["type"]}, Nombre: {updated_product[0]["name"]}, Rastreo: {updated_product[0]["tracking"]}')
else:
    print(f'No se encontró el producto con nombre {product_name}')
