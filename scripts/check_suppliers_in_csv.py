import pandas as pd

# Leer el CSV normalizado
csv_path = '/home/espasiko/mainmanusodoo/manusodoo-roto/odoo_import/normalized_supplier_data_20250619_215528.csv'
df = pd.read_csv(csv_path)

# Contar productos por proveedor
supplier_counts = df['supplier_id'].value_counts()

print('Conteo de productos por proveedor en el CSV normalizado:')
for supplier, count in supplier_counts.items():
    if pd.notna(supplier):
        print(f'  - {supplier}: {count} productos')

print(f'Total de proveedores únicos: {len(supplier_counts)}')
