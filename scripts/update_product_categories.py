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

# Contar productos sin categoría en el CSV
products_without_category = df[df['categ_id'].isna() | (df['categ_id'] == '')]
print(f'Total de productos sin categoría en el CSV: {len(products_without_category)}')

# Actualizar categorías en Odoo
updated_count = 0
total_products = len(df)
for idx, row in df.iterrows():
    if pd.notna(row['default_code']) and row['default_code']:
        product_id = models.execute_kw(db, uid, password, 'product.template', 'search', [[['default_code', '=', row['default_code']]]])
        if product_id and pd.notna(row['categ_id']) and row['categ_id']:
            # Buscar la categoría por nombre
            category_id = models.execute_kw(db, uid, password, 'product.category', 'search', [[['name', '=', row['categ_id']]]])
            if category_id:
                models.execute_kw(db, uid, password, 'product.template', 'write', [[product_id[0]], {'categ_id': category_id[0]}])
                updated_count += 1
                print(f'Categoría {row["categ_id"]} asignada a producto {row["name"]} (ID: {product_id[0]})')
            else:
                print(f'Categoría {row["categ_id"]} no encontrada para producto {row["name"]}')
    if (idx + 1) % 50 == 0:
        print(f'Procesados {idx + 1} de {total_products} productos...')

print(f'Total de productos actualizados con categoría: {updated_count}')
