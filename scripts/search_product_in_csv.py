import pandas as pd

# Ruta al archivo CSV normalizado
csv_file = '/home/espasiko/mainmanusodoo/manusodoo-roto/odoo_import/normalized_supplier_data_20250619_215528.csv'

# Código del producto a buscar
search_code = 'ADR(97)'

try:
    # Leer el archivo CSV
    df = pd.read_csv(csv_file)
    print(f'Archivo CSV leído con éxito. Total de filas: {len(df)}')
    
    # Buscar el producto por código
    if 'default_code' in df.columns:
        matching_products = df[df['default_code'].str.contains(search_code, case=False, na=False)]
        if not matching_products.empty:
            print(f'Producto(s) encontrado(s) en el CSV con código similar a "{search_code}":')
            for index, row in matching_products.iterrows():
                print(f'  - Código: {row["default_code"]}, Nombre: {row.get("name", "No disponible")}, Proveedor: {row.get("supplier_id", "No disponible")}')
        else:
            print(f'No se encontró un producto con código similar a "{search_code}" en la columna "default_code".')
    else:
        print('La columna "default_code" no existe en el CSV.')
except Exception as e:
    print(f'Error al leer el archivo CSV: {e}')
