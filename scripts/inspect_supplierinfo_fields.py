import xmlrpc.client

# Conexión a Odoo
url = 'http://localhost:8069'
db = 'manus_odoo-bd'
username = 'yo@mail.com'
password = 'admin'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Obtener los campos del modelo product.supplierinfo
try:
    fields_info = models.execute_kw(db, uid, password, 'ir.model.fields', 'search_read', 
                                   [[['model', '=', 'product.supplierinfo']]], 
                                   {'fields': ['name', 'field_description', 'ttype']})
    if fields_info:
        print('Campos disponibles en product.supplierinfo:')
        for field in fields_info:
            print(f'  - {field["name"]} ({field["field_description"]}): Tipo {field["ttype"]}')
    else:
        print('No se encontraron campos para product.supplierinfo.')
except Exception as e:
    print(f'Error al obtener campos de product.supplierinfo: {e}')
