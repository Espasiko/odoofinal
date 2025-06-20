import pandas as pd
import os
import glob
import re
from datetime import datetime

# Configuración
INPUT_DIR = "/home/espasiko/mainmanusodoo/manusodoo-roto/ejemplos"
OUTPUT_DIR = "/home/espasiko/mainmanusodoo/manusodoo-roto/odoo_import"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, f"normalized_supplier_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

# Variaciones de nombres de campos para normalizar
FIELD_VARIATIONS = {
    'CODIGO': ['CÓDIGO', 'CODIGO', 'COD', 'REFERENCIA'],
    'DESCRIPCION': ['DESCRIPCIÓN', 'DESCRIPCION', 'NOMBRE', 'PRODUCTO'],
    'IMPORTE_BRUTO': ['IMPORTE BRUTO', 'COSTE', 'PRECIO_COSTE', 'COSTO'],
    'PVP_FINAL_CLIENTE': ['P.V.P FINAL CLIENTE', 'PVP FINAL', 'PRECIO_VENTA', 'PVP'],
    'TOTAL': ['TOTAL', 'IMPORTE TOTAL'],
    'IVA_RECARGO': ['IVA 21% + RECARGO 5,2%', 'IVA', 'IMPUESTO'],
    'MARGEN': ['MARGEN', 'MARGEN %', 'GANANCIA'],
    'BENEFICIO_UNITARIO': ['BENEFICIO UNITARIO', 'BENEFICIO', 'GANANCIA UNITARIA'],
    'BENEFICIO_TOTAL': ['BENEFICIO TOTAL', 'GANANCIA TOTAL'],
    'DTO': ['DTO', 'DESCUENTO', 'DTO %'],
    'UNIDADES': ['UNID.', 'UNIDADES', 'CANTIDAD']
}

def normalize_field_name(field_name):
    """Normaliza nombres de campos teniendo en cuenta tildes y variaciones."""
    if not field_name or not isinstance(field_name, str):
        return ""
    field_name = field_name.strip().upper()
    # Quitar tildes
    field_name = field_name.replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U")
    for standard_name, variations in FIELD_VARIATIONS.items():
        if field_name in [v.upper().replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U") for v in variations]:
            return standard_name
    return field_name

def find_header_row(df):
    """Encuentra la fila de encabezados buscando columnas con nombres conocidos."""
    possible_headers = ['CÓDIGO', 'CODIGO', 'DESCRIPCIÓN', 'DESCRIPCION', 'IMPORTE', 'PVP', 'P.V.P']
    for idx, row in df.iterrows():
        row_values = [str(val).strip().upper() for val in row if pd.notna(val)]
        matches = sum(1 for val in row_values if any(header in val for header in possible_headers))
        if matches >= 2:  # Requiere al menos 2 coincidencias para considerar como encabezado
            return idx
    return 0  # Si no se encuentra, asumir primera fila

def is_category_row(row, code_col_idx):
    """Determina si una fila es una categoría (sin datos numéricos asociados)."""
    code_val = row.iloc[code_col_idx] if code_col_idx < len(row) else None
    if pd.isna(code_val) or str(code_val).strip() == '':
        return True
    # Verificar si el código parece una categoría (por ejemplo, todo en mayúsculas y sin números)
    code_str = str(code_val).strip().upper()
    if code_str and not any(char.isdigit() for char in code_str):
        # Verificar si otras columnas clave tienen datos
        price_cols = [col for col in row.index if any(p in str(col).upper() for p in ['IMPORTE', 'PVP', 'TOTAL'])]
        if not price_cols or all(pd.isna(row[col]) or str(row[col]).strip() == '' for col in price_cols):
            return True
    return False

def extract_supplier_from_filename(filename):
    """Extrae el nombre del proveedor del nombre del archivo."""
    filename = os.path.basename(filename).upper()
    if 'PVP ' not in filename:
        return 'UNKNOWN'
    supplier_part = filename.split('PVP ')[1].split('.')[0]
    # Limpiar partes como '_ejemplo' o guiones
    supplier_part = supplier_part.replace('_EJEMPLO', '').split('-')[0].strip()
    return supplier_part

def infer_category_from_description(description):
    """Infiera la categoría del producto desde la descripción."""
    if pd.isna(description) or not isinstance(description, str):
        return ''
    description = description.upper()
    if 'FRIGO' in description or 'AMERICANO' in description:
        return 'Frigoríficos'
    elif 'LAVADORA' in description:
        return 'Lavadoras'
    elif 'SECADORA' in description:
        return 'Secadoras'
    elif 'TELEVISOR' in description or 'TV' in description:
        return 'Televisores'
    elif 'ASPIRADOR' in description:
        return 'Aspiradoras'
    elif 'CAFETERA' in description or 'CAFE' in description:
        return 'Cafeteras'
    elif 'BATIDORA' in description:
        return 'Batidoras'
    elif 'A/A' in description or 'AIRE ACONDICIONADO' in description:
        return 'Aire Acondicionado'
    elif 'MICROONDAS' in description or 'MICRO' in description:
        return 'Microondas'
    elif 'HORNO' in description:
        return 'Hornos'
    elif 'PLACA' in description or 'INDUCCION' in description:
        return 'Placas'
    else:
        return ''

def clean_price(value):
    """Limpia y convierte valores de precio a float."""
    if pd.isna(value):
        return 0.0
    try:
        # Si es string, quitar € y espacios, reemplazar coma por punto
        if isinstance(value, str):
            value = value.replace('€', '').replace(',', '.').strip()
        return float(value)
    except (ValueError, TypeError):
        return 0.0

# Asegurarse que el directorio de salida existe
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Lista para almacenar datos normalizados
all_data = []

# Contador total de productos
product_count = 0

# Buscar todos los archivos Excel que empiezan con PVP
excel_files = glob.glob(os.path.join(INPUT_DIR, "PVP*.xlsx"))
for file_path in excel_files:
    supplier_name = extract_supplier_from_filename(file_path)
    print(f"Procesando archivo: {file_path} (Proveedor: {supplier_name})")
    try:
        # Leer todas las hojas del archivo Excel
        xls = pd.ExcelFile(file_path)
        for sheet_name in xls.sheet_names:
            # Ignorar hojas que no son de catálogo principal
            sheet_name_upper = sheet_name.upper()
            if any(ignore_term in sheet_name_upper for ignore_term in ['DEVOLUCION', 'DEVOLUCIONES', 'RECLAMACION', 'RECLAMACIONES', 'VENDIDO', 'CALCULO', 'ROTO']):
                continue
            print(f"  - Leyendo hoja: {sheet_name}")
            try:
                # Leer las primeras 20 filas para buscar encabezados
                df_preview = pd.read_excel(file_path, sheet_name=sheet_name, nrows=20, header=None)
                header_row = find_header_row(df_preview)
                # Leer todo el archivo con el encabezado correcto
                df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
                # Leer datos después de los encabezados
                df = df.iloc[header_row:].reset_index(drop=True)
                df.columns = [normalize_field_name(col) for col in df.iloc[0]]
                df = df.iloc[1:].reset_index(drop=True)
                if df.empty:
                    print(f"  - Hoja {sheet_name} vacía después de encabezados, omitiendo.")
                    continue
                
                # Identificar columna de código
                code_col_idx = next((i for i, col in enumerate(df.columns) if col == 'CODIGO'), 0)
                
                # Filtrar filas que no son productos (categorías o vacías)
                initial_rows = len(df)
                df = df[~df.apply(lambda row: is_category_row(row, code_col_idx), axis=1)]
                filtered_rows = initial_rows - len(df)
                print(f"  - Filtradas {filtered_rows} filas no relevantes (categorías o vacías) en hoja {sheet_name}.")

                # Mapear a campos de Odoo
                odoo_data = []
                for index, row in df.iterrows():
                    product = {
                        'Name': str(row.get('DESCRIPCION', '')) if pd.notna(row.get('DESCRIPCION', '')) else '',
                        'Internal Reference': str(row.get('CODIGO', '')) if pd.notna(row.get('CODIGO', '')) else '',
                        'Sales Price': clean_price(row.get('PVP_FINAL_CLIENTE', 0.0)),
                        'Cost': clean_price(row.get('IMPORTE_BRUTO', 0.0)),
                        'Product Category': infer_category_from_description(row.get('DESCRIPCION', '')),
                        'Vendor': supplier_name,
                        'Description': '',
                        'Barcode': '',
                        'Product Type': 'Storable Product',
                        'External ID': f"{supplier_name.upper()}_{row['CODIGO']}" if row['CODIGO'] else f"{supplier_name.upper()}_{index}"
                    }
                    # Solo añadir si hay un código y un nombre
                    if product['Internal Reference'] and product['Name']:
                        odoo_data.append(product)
                        product_count += 1

                all_data.extend(odoo_data)
            except Exception as e:
                print(f"  - Error procesando hoja {sheet_name}: {e}")
    except Exception as e:
        print(f"Error leyendo archivo {file_path}: {e}")

# Convertir a DataFrame final
if all_data:
    final_df = pd.DataFrame(all_data)
    # Eliminar duplicados basados en código y proveedor
    initial_count = len(final_df)
    final_df = final_df.drop_duplicates(subset=['Internal Reference', 'Vendor'])
    deduped_count = initial_count - len(final_df)
    print(f"Eliminados {deduped_count} productos duplicados.")

    # Validación de datos
    required_fields = ['Name', 'Internal Reference']
    for idx, row in final_df.iterrows():
        for field in required_fields:
            if pd.isna(row[field]) or row[field] == '':
                print(f"Fila {idx} tiene el campo obligatorio {field} vacío. Se eliminará.")
                final_df.drop(idx, inplace=True)
                break
        else:
            # Validar tipos de datos
            if not pd.isna(row['Sales Price']) and not isinstance(row['Sales Price'], (int, float)):
                try:
                    final_df.at[idx, 'Sales Price'] = float(row['Sales Price'])
                except (ValueError, TypeError):
                    print(f"Fila {idx} tiene un valor inválido en Sales Price: {row['Sales Price']}. Se establecerá a 0.")
                    final_df.at[idx, 'Sales Price'] = 0.0
            if not pd.isna(row['Cost']) and not isinstance(row['Cost'], (int, float)):
                try:
                    final_df.at[idx, 'Cost'] = float(row['Cost'])
                except (ValueError, TypeError):
                    print(f"Fila {idx} tiene un valor inválido en Cost: {row['Cost']}. Se establecerá a 0.")
                    final_df.at[idx, 'Cost'] = 0.0

    final_df.to_csv(OUTPUT_FILE, index=False)
    print(f"Datos normalizados guardados en {OUTPUT_FILE}")
    print(f"Total de productos procesados: {len(final_df)}")
else:
    print("No se encontraron datos para procesar.")
