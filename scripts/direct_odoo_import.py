#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para importar productos directamente a Odoo usando XML-RPC
"""

import sys
import pandas as pd
import xmlrpc.client
from datetime import datetime

# Configuración de conexión a Odoo (usando las credenciales proporcionadas)
URL = "http://localhost:8069"
DB = "manus_odoo-bd"
USERNAME = "yo@mail.com"
PASSWORD = "admin"
CSV_FILE = "/home/espasiko/mainmanusodoo/manusodoo-roto/odoo_import/PVP_CECOTEC_template_corrected.csv"

# Conexión a Odoo
print("Conectando a Odoo...")
common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common")
uid = common.authenticate(DB, USERNAME, PASSWORD, {})
if not uid:
    print("Error de autenticación con Odoo. Verifica las credenciales.")
    sys.exit(1)
models = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object")
print("Conexión a Odoo establecida con éxito.")

# Leer el archivo CSV
df = pd.read_csv(CSV_FILE)

# Contadores
successful = 0
total = len(df)  # Procesar todos los productos

print(f"Iniciando importación de {total} productos a Odoo...")

# Iterar sobre todos los productos del CSV
for index, row in df.iterrows():
    # Preparar los datos del producto
    product_data = {
        "name": row['name'],
        "default_code": str(row['default_code']),
        "list_price": row['list_price'],
        "standard_price": row['standard_price'],
        # "type": "storable",  # 'storable' no es válido
    # "type": "product",  # 'product' no es válido según actualización
    "type": "consu",  # Usar 'consu' según documentación reciente de Odoo 18
        "sale_ok": True,
        "purchase_ok": True,
        "active": True
    }
    
    # Intentar crear el producto en Odoo
    try:
        product_id = models.execute_kw(DB, uid, PASSWORD, 'product.template', 'create', [product_data])
        if product_id:
            successful += 1
            print(f"Producto {successful}/{total} importado: {row['name']} (ID: {product_id})")
        else:
            print(f"Error al importar {row['name']}: No se recibió ID de producto")
    except Exception as e:
        print(f"Error al importar {row['name']}: {str(e)}")

# Resumen
print("-" * 50)
print(f"Importación completada a las {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Total de productos procesados: {total}")
print(f"Productos importados con éxito: {successful}")
print(f"Errores: {total - successful}")
