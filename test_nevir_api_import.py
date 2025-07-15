#!/usr/bin/env python3
"""
Script para probar la importación del Excel de Nevir a través del endpoint FastAPI.
"""
import requests
import os
import json
import logging
import sys
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('test_nevir_api_import.log')
    ]
)
logger = logging.getLogger("test_nevir_api_import")

# Cargar variables de entorno
load_dotenv()

# URL del endpoint
BASE_URL = "http://localhost:8000"
ENDPOINT = "/api/v1/importer/"
URL = f"{BASE_URL}{ENDPOINT}"

# Obtener token de autenticación
def get_auth_token():
    auth_url = f"{BASE_URL}/token"
    auth_data = {
        "username": "admin",
        "password": "admin"
    }
    logger.info(f"Solicitando token de autenticación a {auth_url}")
    response = requests.post(auth_url, data=auth_data)
    if response.status_code == 200:
        token = response.json().get("access_token")
        logger.info("Token de autenticación obtenido correctamente")
        return token
    else:
        logger.error(f"Error de autenticación: {response.status_code}")
        logger.error(response.text)
        return None

def main():
    # Archivo Excel para probar
    if len(sys.argv) > 1:
        excel_file = sys.argv[1]
    else:
        # Ruta al archivo Excel formateado
        excel_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                 'ejemplos/proveedores_exl_csv/PVP_NEVIR_FORMATEADO.xlsx')

        # Si existe la versión V2, usarla en su lugar
        v2_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                              'ejemplos/proveedores_exl_csv/PVP_NEVIR_FORMATEADO_V2.xlsx')
        if os.path.exists(v2_path):
            excel_path = v2_path
        
        excel_file = excel_path
    
    logger.info(f"Usando archivo Excel: {excel_file}")
    
    # Verificar que el archivo existe
    if not os.path.exists(excel_file):
        logger.error(f"El archivo {excel_file} no existe")
        return 1
    
    # Obtener token
    token = get_auth_token()
    if not token:
        logger.error("No se pudo obtener el token de autenticación")
        return 1
    
    # Preparar headers con el token
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # Preparar datos del formulario
    data = {
        "proveedor_nombre": "NEVIR"
    }
    
    # Preparar el archivo
    files = {
        "file": (os.path.basename(excel_file), open(excel_file, "rb"), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    }
    
    # Hacer la solicitud
    logger.info(f"Enviando solicitud a {URL}...")
    try:
        response = requests.post(URL, headers=headers, data=data, files=files)
        
        # Mostrar resultado
        logger.info(f"Código de estado: {response.status_code}")
        try:
            result = response.json()
            logger.info(json.dumps(result, indent=2, ensure_ascii=False))
            
            if response.status_code == 200:
                logger.info("✅ Importación completada con éxito")
                return 0
            else:
                logger.error("❌ Error en la importación")
                return 1
        except Exception as e:
            logger.error(f"Error al parsear la respuesta: {e}")
            logger.error(response.text[:500])
            return 1
    except Exception as e:
        logger.error(f"Error al hacer la solicitud: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
