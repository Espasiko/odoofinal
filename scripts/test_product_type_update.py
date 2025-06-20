import xmlrpc.client
import os

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
    
    # Leer el valor actual del campo type
    current_product = models.execute_kw(db, uid, password, 'product.template', 'read', [product_id, ['type', 'name']])
    print(f'Tipo actual del producto: {current_product[0]["type"]}, Nombre: {current_product[0]["name"]}')
    
    # Obtener las opciones posibles para el campo type
    try:
        field_info = models.execute_kw(db, uid, password, 'ir.model.fields', 'search_read', [[['model', '=', 'product.template'], ['name', '=', 'type']]], {'fields': ['selection']})
        if field_info and 'selection' in field_info[0]:
            print(f'Opciones disponibles para el campo type: {field_info[0]["selection"]}')
        else:
            print('No se encontraron opciones para el campo type.')
    except Exception as e:
        print(f'Error al obtener opciones para el campo type: {e}')
    
    # No intentaremos actualizar el tipo hasta conocer el valor correcto
    print('No se intentará actualizar el tipo de producto hasta identificar el valor correcto.')
    
    # Verificar el estado actual
    updated_product = models.execute_kw(db, uid, password, 'product.template', 'read', [product_id, ['type', 'name']])
    print(f'Estado actual - Tipo: {updated_product[0]["type"]}, Nombre: {updated_product[0]["name"]}')
else:
    print(f'No se encontró el producto con nombre {product_name}')
