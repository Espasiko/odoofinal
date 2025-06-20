import xmlrpc.client
import pandas as pd
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de conexión a Odoo
url = 'http://localhost:8069'
db = 'manus_odoo-bd'
username = 'yo@mail.com'
password = 'admin'

# Conexión con Odoo
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Función para buscar o crear proveedores
def ensure_supplier(supplier_name):
    supplier_id = models.execute_kw(db, uid, password, 'res.partner', 'search', [[['name', '=', supplier_name], ['supplier_rank', '>', 0]]])
    if not supplier_id:
        supplier_id = models.execute_kw(db, uid, password, 'res.partner', 'create', [{'name': supplier_name, 'supplier_rank': 1}])
        print(f"Proveedor {supplier_name} creado con ID {supplier_id}")
    else:
        supplier_id = supplier_id[0]
        print(f"Proveedor {supplier_name} encontrado con ID {supplier_id}")
    return supplier_id

# Función para buscar o crear categorías
def ensure_category(category_path):
    category_names = category_path.split('/')
    parent_id = False
    for name in category_names:
        domain = [['name', '=', name]]
        if parent_id:
            domain.append(['parent_id', '=', parent_id])
        category_id = models.execute_kw(db, uid, password, 'product.category', 'search', [domain])
        if not category_id:
            values = {'name': name}
            if parent_id:
                values['parent_id'] = parent_id
            category_id = models.execute_kw(db, uid, password, 'product.category', 'create', [values])
            print(f"Categoría {name} creada con ID {category_id}")
        else:
            category_id = category_id[0]
            print(f"Categoría {name} encontrada con ID {category_id}")
        parent_id = category_id
    return parent_id

# Leer datos normalizados para extraer proveedores y categorías únicos
csv_path = '/home/espasiko/mainmanusodoo/manusodoo-roto/odoo_import/normalized_supplier_data_20250619_222603.csv'
data = pd.read_csv(csv_path)

# Imprimir nombres de columnas para diagnóstico
print("Columnas disponibles en el CSV:", data.columns.tolist())

# Obtener proveedores únicos
vendor_column = 'Vendor' if 'Vendor' in data.columns else None
if vendor_column:
    suppliers = data[vendor_column].str.strip().dropna().unique()
    for supplier in suppliers:
        ensure_supplier(supplier)
else:
    print("No se encontró la columna de proveedores en el CSV.")

# Obtener categorías únicas
category_column = 'Product Category' if 'Product Category' in data.columns else None
if category_column:
    categories = data[category_column].dropna().unique()
    for category in categories:
        ensure_category(category)
else:
    print("No se encontró la columna de categorías en el CSV.")

print("Pre-importación de proveedores y categorías completada.")
