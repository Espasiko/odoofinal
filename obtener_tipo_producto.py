#!/usr/bin/env python3
import xmlrpc.client

ODOO_URL = 'http://localhost:8069'
ODOO_DB = 'manus_odoo-bd'
ODOO_USERNAME = 'yo@mail.com'
ODOO_PASSWORD = 'admin'

common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})
if not uid:
    print('No se pudo autenticar en Odoo')
    exit(1)
models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
fields = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    'product.template', 'fields_get',
    [], {'attributes':['type']}
)
print('Atributos del campo type en product.template:')
for k, v in fields['type'].items():
    print(f"  {k}: {v}")
if 'selection' in fields['type']:
    print('Valores posibles para el campo type en product.template:')
    for value, label in fields['type']['selection']:
        print(f"  - {value}: {label}")
else:
    print('No se encontró el atributo "selection". Estructura completa del campo:')
    import pprint
    pprint.pprint(fields['type'])