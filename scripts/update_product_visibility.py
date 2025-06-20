import xmlrpc.client
import pandas as pd

# Conexión a Odoo
url = 'http://localhost:8069'
db = 'manus_odoo-bd'
username = 'yo@mail.com'
password = 'admin'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Obtener todos los productos
try:
    product_ids = models.execute_kw(db, uid, password, 'product.template', 'search', [[]])
    if product_ids:
        print(f'Total de productos encontrados: {len(product_ids)}')
        updated_count = 0
        for product_id in product_ids:
            # Actualizar campos de rastreo y visibilidad
            update_data = {
                'tracking': 'lot',  # Rastreo por lote para inventario
                'available_in_pos': True,  # Disponible en Punto de Venta
                'website_published': True,  # Publicado en sitio web
            }
            models.execute_kw(db, uid, password, 'product.template', 'write', [[product_id], update_data])
            updated_count += 1
            if updated_count % 50 == 0:
                print(f'Actualizados {updated_count} productos...')
        print(f'Total de productos actualizados: {updated_count}')
    else:
        print('No se encontraron productos para actualizar.')
except Exception as e:
    print(f'Error al actualizar productos: {e}')
