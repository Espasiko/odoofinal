import xmlrpc.client
import pandas as pd
import os
from datetime import datetime

# Conexión a Odoo
url = 'http://localhost:8069'
db = 'manus_odoo-bd'
username = 'yo@mail.com'
password = 'admin'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Ruta al archivo CSV normalizado
csv_file = '/home/espasiko/mainmanusodoo/manusodoo-roto/odoo_import/normalized_supplier_data_20250619_215528.csv'

# Leer el CSV
print(f'Leyendo archivo CSV: {csv_file}')
try:
    df = pd.read_csv(csv_file)
    print(f'Archivo CSV leído con éxito. Total de productos: {len(df)}')
except Exception as e:
    print(f'Error al leer el CSV: {e}')
    exit(1)

# Verificar columnas esperadas
expected_columns = ['default_code', 'name', 'type', 'standard_price', 'list_price', 'categ_id', 'supplier_id', 'active', 'sale_ok', 'purchase_ok']
missing_columns = [col for col in expected_columns if col not in df.columns]
if missing_columns:
    print(f'Advertencia: Columnas esperadas no encontradas en el CSV: {missing_columns}')
    # Rellenar columnas faltantes con valores predeterminados
    for col in missing_columns:
        if col == 'type':
            df[col] = 'consu'
        elif col in ['active', 'sale_ok', 'purchase_ok']:
            df[col] = True
        elif col in ['standard_price', 'list_price']:
            df[col] = 0.0
        elif col in ['categ_id', 'supplier_id']:
            df[col] = ''
else:
    print('Todas las columnas esperadas están presentes en el CSV.')

# Agregar columnas adicionales si no existen
df['tracking'] = df.get('tracking', 'serial')  # Rastreo por ID único para inventario
df['available_in_pos'] = df.get('available_in_pos', True)  # Disponible en PoS
df['website_published'] = df.get('website_published', False)  # Publicado en web
df['reordering_min_qty'] = df.get('reordering_min_qty', 5)  # Cantidad mínima para alerta de stock bajo
df['reordering_max_qty'] = df.get('reordering_max_qty', 10)  # Cantidad máxima para reordenar

# Manejo de lotes para importación eficiente
batch_size = 50
batches = [df[i:i + batch_size] for i in range(0, len(df), batch_size)]

# Contadores para estadísticas
total_created = 0
total_updated = 0
total_errors = 0

# Procesar cada lote
for batch_idx, batch in enumerate(batches):
    print(f'Procesando lote {batch_idx + 1} de {len(batches)} ({len(batch)} productos)...')
    for index, row in batch.iterrows():
        try:
            # Buscar si el producto ya existe por default_code
            product_id = models.execute_kw(db, uid, password, 'product.template', 'search', [[['default_code', '=', row['default_code']]]])
            product_data = {
                'name': row['name'],
                'default_code': row['default_code'],
                'type': 'consu',  # Bienes físicos
                'tracking': 'lot',  # Rastreo por lote para inventario
                'available_in_pos': True,  # Disponible en Punto de Venta
                'website_published': True,  # Publicado en sitio web
                'list_price': float(row['list_price']) if pd.notna(row['list_price']) else 0.0,
                'standard_price': float(row['standard_price']) if pd.notna(row['standard_price']) else 0.0,
                'reordering_min_qty': float(row['reordering_min_qty']) if pd.notna(row['reordering_min_qty']) else 5.0,  # Cantidad mínima para reordenar (alerta de stock bajo)
                'reordering_max_qty': float(row['reordering_max_qty']) if pd.notna(row['reordering_max_qty']) else 10.0, # Cantidad máxima para reordenar
            }

            # Manejar categoría (categ_id)
            if pd.notna(row['categ_id']) and row['categ_id']:
                categ_id = models.execute_kw(db, uid, password, 'product.category', 'search', [[['name', '=', row['categ_id']]]])
                if categ_id:
                    product_data['categ_id'] = categ_id[0]
                else:
                    print(f'Categoría {row["categ_id"]} no encontrada para producto {row["name"]}')

            # Crear o actualizar producto
            if product_id:
                # Actualizar producto existente
                models.execute_kw(db, uid, password, 'product.template', 'write', [[product_id[0]], product_data])
                product_id = product_id[0]
                total_updated += 1
                print(f'Producto actualizado: {row["name"]} (ID: {product_id})')
            else:
                # Crear nuevo producto
                product_id = models.execute_kw(db, uid, password, 'product.template', 'create', [product_data])
                total_created += 1
                print(f'Producto creado: {row["name"]} (ID: {product_id})')

            # Manejar proveedor (seller_ids)
            if pd.notna(row['supplier_id']) and row['supplier_id']:
                supplier_id = models.execute_kw(db, uid, password, 'res.partner', 'search', [[['name', '=', row['supplier_id']]]])
                if supplier_id:
                    supplier_info = {
                        'partner_id': supplier_id[0],  # Usar partner_id para identificar al proveedor
                        'product_tmpl_id': product_id,
                        'price': float(row['standard_price']) if pd.notna(row['standard_price']) else 0.0,
                        'min_qty': 1,  # Cantidad mínima de pedido
                        'delay': 7,    # Tiempo de entrega en días
                    }
                    # Eliminar cualquier relación proveedor-producto existente para evitar duplicados
                    existing_supplier_info = models.execute_kw(db, uid, password, 'product.supplierinfo', 'search', 
                                                              [[['product_tmpl_id', '=', product_id], ['partner_id', '=', supplier_id[0]]]])
                    if existing_supplier_info:
                        models.execute_kw(db, uid, password, 'product.supplierinfo', 'unlink', [existing_supplier_info])
                        print(f'Relación proveedor-producto existente eliminada para {row["name"]} con proveedor {row["supplier_id"]}')
                    # Crear una nueva relación proveedor-producto
                    models.execute_kw(db, uid, password, 'product.supplierinfo', 'create', [supplier_info])
                    print(f'Proveedor {row["supplier_id"]} asociado a {row["name"]}')
                else:
                    print(f'Proveedor {row["supplier_id"]} no encontrado para producto {row["name"]}')

        except Exception as e:
            total_errors += 1
            print(f'Error al procesar producto {row.get("name", "Sin nombre")}: {e}')

    print(f'Lote {batch_idx + 1} completado. Creados: {total_created}, Actualizados: {total_updated}, Errores: {total_errors}')

# Resumen final
print('=== Resumen de Importación ===')
print(f'Total de productos creados: {total_created}')
print(f'Total de productos actualizados: {total_updated}')
print(f'Total de errores: {total_errors}')
print('Importación completada.')
