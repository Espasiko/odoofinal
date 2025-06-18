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
modules = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    'ir.module.module', 'search_read',
    [[('state','=','installed')], ['name','shortdesc','state']]
)
for m in modules:
    print(f"{m['name']}: {m['shortdesc']}")