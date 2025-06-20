#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para importar productos a Odoo a través de la API FastAPI
"""

import sys
import pandas as pd
import requests
import json
from datetime import datetime

# Configuración
CSV_FILE = "/home/espasiko/mainmanusodoo/manusodoo-roto/odoo_import/PVP_CECOTEC_template_corrected.csv"
API_URL = "http://localhost:8000/api/v1/products"
# Vamos a obtener un token de acceso
LOGIN_URL = "http://localhost:8000/token"
USERNAME = "yo@mail.com"
PASSWORD = "admin"

def get_access_token():
    """Obtiene un token de acceso de la API"""
    login_data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    try:
        response = requests.post(LOGIN_URL, data=login_data, headers=headers)
        if response.status_code == 200:
            token_data = response.json()
            return token_data.get("access_token")
        else:
            print(f"Error al obtener token: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Excepción al obtener token: {str(e)}")
        return None

TOKEN = get_access_token()
if not TOKEN:
    print("No se pudo obtener el token de acceso. Terminando.")
    sys.exit(1)
else:
    print("Token de acceso obtenido con éxito.")

# Leer el archivo CSV
df = pd.read_csv(CSV_FILE)

# Contadores
successful = 0
total = len(df)

print(f"Iniciando importación de {total} productos a Odoo...")

# Iterar sobre solo el primer producto para depuración
for index, row in df.head(1).iterrows():
    # Crear el payload para la API
    product_data = {
        "name": row['name'],
        "code": str(row['default_code']),
        "price": row['list_price'],
        "stock": 0,  # Puedes ajustar esto si tienes datos de stock
        "image_url": "",  # Ajusta si tienes URLs de imágenes
        "is_active": True
    }
    
    # Enviar solicitud a la API
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(API_URL, json=product_data, headers=headers)
        
        if response.status_code == 200 or response.status_code == 201:
            successful += 1
            print(f"Producto {successful}/{total} importado: {row['name']}")
        else:
            print(f"Error al importar {row['name']}: {response.status_code} - {response.text}")
            try:
                error_detail = response.json()
                print(f"Detalles del error: {error_detail}")
            except:
                print("No se pudo obtener detalles adicionales del error.")
    except Exception as e:
        print(f"Excepción al importar {row['name']}: {str(e)}")

# Resumen
print("-" * 50)
print(f"Importación completada a las {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Total de productos procesados: {total}")
print(f"Productos importados con éxito: {successful}")
print(f"Errores: {total - successful}")
