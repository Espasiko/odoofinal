#!/usr/bin/env python3
"""
Script para probar la creación de un producto completo en Odoo
con todos los campos necesarios y validación de categorías
"""
import requests
import json
import logging
import sys
import time
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("test_producto")

# Cargar variables de entorno
load_dotenv()

# URL del endpoint
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1/products"

# Obtener token de autenticación
def get_auth_token():
    auth_url = f"{BASE_URL}/token"
    auth_data = {
        "username": "admin",
        "password": "admin"
    }
    try:
        logger.info(f"Intentando autenticación en {auth_url}")
        response = requests.post(auth_url, data=auth_data)
        response.raise_for_status()  # Lanzar excepción si hay error HTTP
        token = response.json().get("access_token")
        logger.info("Autenticación exitosa")
        return token
    except requests.exceptions.RequestException as e:
        logger.error(f"Error de autenticación: {str(e)}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Código de estado: {e.response.status_code}")
            logger.error(f"Respuesta: {e.response.text[:500]}")
        return None

# Función para crear un producto
def crear_producto(token, producto_data):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        logger.info(f"Enviando solicitud a {API_URL}")
        logger.info(f"Datos del producto: {json.dumps(producto_data, indent=2, ensure_ascii=False)}")
        
        response = requests.post(API_URL, headers=headers, data=json.dumps(producto_data))
        response.raise_for_status()
        
        result = response.json()
        logger.info(f"Producto creado con éxito. Código: {response.status_code}")
        logger.info(f"Respuesta: {json.dumps(result, indent=2, ensure_ascii=False)}")
        return result
    except requests.exceptions.RequestException as e:
        logger.error(f"Error al crear producto: {str(e)}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Código de estado: {e.response.status_code}")
            logger.error(f"Respuesta: {e.response.text[:500]}")
        return None

# Función para obtener un producto por ID
def obtener_producto(token, product_id):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    get_url = f"{API_URL}/{product_id}"
    try:
        logger.info(f"Obteniendo producto desde {get_url}")
        response = requests.get(get_url, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        logger.info(f"Producto obtenido con éxito. Código: {response.status_code}")
        logger.info(f"Datos del producto: {json.dumps(result, indent=2, ensure_ascii=False)}")
        return result
    except requests.exceptions.RequestException as e:
        logger.error(f"Error al obtener producto: {str(e)}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Código de estado: {e.response.status_code}")
            logger.error(f"Respuesta: {e.response.text[:500]}")
        return None

# Ejecutar el script
if __name__ == "__main__":
    # Obtener token
    token = get_auth_token()
    if not token:
        logger.error("No se pudo obtener el token de autenticación")
        sys.exit(1)
    
    # Datos del producto de prueba
    producto = {
        "name": "Televisor LED 55\" Smart TV",
        "default_code": "TV-LED-55-SMART",
        "type": "consu",
        "list_price": 499.99,
        "standard_price": 350.00,
        "category": "Electrónica",
        "description": "Televisor LED de 55 pulgadas con Smart TV, resolución 4K y conexión WiFi",
        "sale_ok": True,
        "purchase_ok": True,
        "barcode": f"8412345678901-{int(time.time())}",
        "weight": 15.5,
        "volume": 0.25
    }
    
    # Crear producto
    resultado = crear_producto(token, producto)
    
    # Si el producto se creó correctamente, obtenerlo
    if resultado and "id" in resultado:
        product_id = resultado["id"]
        producto_obtenido = obtener_producto(token, product_id)
        
        if producto_obtenido:
            # Verificar que los datos se guardaron correctamente
            logger.info("Verificando datos del producto:")
            for campo, valor in producto.items():
                if campo in producto_obtenido:
                    if str(producto_obtenido[campo]) == str(valor):
                        logger.info(f"✅ Campo '{campo}' correcto: {valor}")
                    else:
                        logger.warning(f"❌ Campo '{campo}' diferente. Esperado: {valor}, Obtenido: {producto_obtenido[campo]}")
                else:
                    logger.warning(f"❓ Campo '{campo}' no encontrado en la respuesta")
        
        logger.info("Prueba completada")
    else:
        logger.error("No se pudo crear el producto")
        sys.exit(1)
