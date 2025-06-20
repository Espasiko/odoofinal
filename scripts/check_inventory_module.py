import xmlrpc.client

# Conexión a Odoo
url = 'http://localhost:8069'
db = 'manus_odoo-bd'
username = 'yo@mail.com'
password = 'admin'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Verificar si el módulo de Inventario está instalado
module_name = 'stock'
module_installed = models.execute_kw(db, uid, password, 'ir.module.module', 'search', [[['name', '=', module_name], ['state', '=', 'installed']]])

if module_installed:
    print(f'El módulo de Inventario ({module_name}) está instalado y activado.')
    # Obtener información adicional sobre el módulo
    module_info = models.execute_kw(db, uid, password, 'ir.module.module', 'read', [module_installed[0], ['name', 'state', 'shortdesc']])
    print(f'Detalles del módulo: Nombre: {module_info[0]["name"]}, Estado: {module_info[0]["state"]}, Descripción: {module_info[0]["shortdesc"]}')
else:
    print(f'El módulo de Inventario ({module_name}) no está instalado o no está activado.')
    # Buscar el módulo para ver si está disponible para instalación
    module_available = models.execute_kw(db, uid, password, 'ir.module.module', 'search', [[['name', '=', module_name]]])
    if module_available:
        module_info = models.execute_kw(db, uid, password, 'ir.module.module', 'read', [module_available[0], ['name', 'state', 'shortdesc']])
        print(f'El módulo está disponible pero no instalado. Estado: {module_info[0]["state"]}. Puedes instalarlo desde Configuración > Módulos.')
    else:
        print(f'El módulo de Inventario no está disponible en tu sistema.')

# Verificar la configuración de inventario para un producto de ejemplo
product_name = 'A/A PORTATIL + CALEFACCION'
product_id = models.execute_kw(db, uid, password, 'product.template', 'search', [[['name', '=', product_name]]])

if product_id:
    product_id = product_id[0]
    product_info = models.execute_kw(db, uid, password, 'product.template', 'read', [product_id, ['type', 'name', 'tracking', 'available_in_pos']])
    print(f'Configuración del producto {product_name}:')
    print(f'  - Tipo: {product_info[0]["type"]}')
    print(f'  - Rastreo de inventario: {product_info[0]["tracking"]}')
    print(f'  - Disponible en PoS: {product_info[0]["available_in_pos"]}')
else:
    print(f'No se encontró el producto con nombre {product_name}')
