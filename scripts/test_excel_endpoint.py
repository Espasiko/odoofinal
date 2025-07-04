#!/usr/bin/env python3
"""
Script para probar el endpoint de procesamiento de Excel
"""
import requests
import os
import json
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# URL del endpoint
BASE_URL = "http://localhost:8000"
ENDPOINT = "/api/v1/mistral-llm/process-excel"
URL = f"{BASE_URL}{ENDPOINT}"

# Obtener token de autenticación
def get_auth_token():
    auth_url = f"{BASE_URL}/token"
    auth_data = {
        "username": "yo@mail.com",
        "password": "admin"
    }
    response = requests.post(auth_url, data=auth_data)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print(f"Error de autenticación: {response.status_code}")
        print(response.text)
        return None

# Archivo Excel para probar
EXCEL_FILE = "/home/espasiko/mainmanusodoo/manusodoo-roto/backups/2025-06-30/project_full_backup/static/uploads/PVP_CECOTEC_ejemplo.xlsx"

# Verificar que el archivo existe
if not os.path.exists(EXCEL_FILE):
    print(f"El archivo {EXCEL_FILE} no existe")
    exit(1)

# Obtener token
token = get_auth_token()
if not token:
    print("No se pudo obtener el token de autenticación")
    exit(1)

# Preparar headers con el token
headers = {
    "Authorization": f"Bearer {token}"
}

# Preparar datos del formulario
data = {
    "proveedor_nombre": "CECOTEC",
    "start_row": 0,
    "chunk_size": 50,
    "only_first_sheet": True
}

# Preparar el archivo
files = {
    "file": (os.path.basename(EXCEL_FILE), open(EXCEL_FILE, "rb"), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
}

# Hacer la solicitud
print(f"Enviando solicitud a {URL}...")
response = requests.post(URL, headers=headers, data=data, files=files)

# Mostrar resultado
print(f"Código de estado: {response.status_code}")
try:
    result = response.json()
    print(json.dumps(result, indent=2, ensure_ascii=False))
except Exception as e:
    print(f"Error al parsear la respuesta: {e}")
    print(response.text[:500])
