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

# Leer el CSV normalizado
csv_path = '/home/espasiko/mainmanusodoo/manusodoo-roto/odoo_import/normalized_supplier_data_20250619_215528.csv'
df = pd.read_csv(csv_path)

# Obtener productos en categoría 'All' (ID: 1)
all_category_products = models.execute_kw(db, uid, password, 'product.template', 'search', 
                                         [[['categ_id', '=', 1]]])

print(f'Total de productos en categoría "All": {len(all_category_products)}')

updated_count = 0
for product_id in all_category_products:
    product = models.execute_kw(db, uid, password, 'product.template', 'read', 
                               [[product_id], ['default_code']])
    if product and 'default_code' in product[0]:
        default_code = product[0]['default_code']
        # Buscar en el CSV por default_code
        matching_row = df[df['default_code'] == default_code]
        if not matching_row.empty:
            category_name = matching_row.iloc[0]['categ_id']
            if pd.notna(category_name):
                # Buscar la categoría por nombre
                category_id = models.execute_kw(db, uid, password, 'product.category', 'search', 
                                               [[['name', '=', category_name]]])
                if category_id:
                    models.execute_kw(db, uid, password, 'product.template', 'write', 
                                     [[product_id], {'categ_id': category_id[0]}])
                    updated_count += 1
                    print(f'Producto {default_code} reasignado a categoría {category_name} (ID: {category_id[0]})')
                else:
                    print(f'Categoría {category_name} no encontrada para producto {default_code}')

print(f'Total de productos reasignados desde "All": {updated_count}')
