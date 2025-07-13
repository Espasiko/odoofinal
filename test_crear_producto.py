#!/usr/bin/env python3
"""
Script para probar la creación de un producto directamente en Odoo
"""
import requests
import json
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# URL del endpoint
BASE_URL = "http://localhost:8000"
ENDPOINT = "/api/v1/products/"
URL = f"{BASE_URL}{ENDPOINT}"

# Obtener token de autenticación
def get_auth_token():
    auth_url = f"{BASE_URL}/token"
    auth_data = {
        "username": "admin",
        "password": "admin"
    }
    response = requests.post(auth_url, data=auth_data)
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print(f"Error de autenticación: {response.status_code}")
        print(response.text)
        return None

# Obtener token
token = get_auth_token()
if not token:
    print("No se pudo obtener el token de autenticación")
    exit(1)

# Preparar headers con el token
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Datos del producto de prueba
producto = {
    "name": "Producto de Prueba Automatizada",
    "default_code": "TEST-001",
    "type": "consu",
    "list_price": 100.0,
    "standard_price": 80.0,
    "category": "Electrónica",
    "description": "Este es un producto de prueba creado automáticamente",
    "sale_ok": True,
    "purchase_ok": True
}

# Hacer la solicitud
print(f"Enviando solicitud a {URL}...")
response = requests.post(URL, headers=headers, data=json.dumps(producto))

# Mostrar resultado
print(f"Código de estado: {response.status_code}")
try:
    result = response.json()
    print(json.dumps(result, indent=2, ensure_ascii=False))
except Exception as e:
    print(f"Error al parsear la respuesta: {e}")
    print(response.text[:500])

# Si el producto se creó correctamente, intentar obtenerlo
if response.status_code == 201 and "id" in result:
    product_id = result["id"]
    get_url = f"{URL}{product_id}"
    print(f"\nObteniendo el producto creado desde {get_url}...")
    get_response = requests.get(get_url, headers=headers)
    print(f"Código de estado: {get_response.status_code}")
    try:
        get_result = get_response.json()
        print(json.dumps(get_result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error al parsear la respuesta: {e}")
        print(get_response.text[:500])
