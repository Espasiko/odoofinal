#!/usr/bin/env python3
import requests
import os
import sys
import json
from pathlib import Path

# Configuración
API_URLS = [
    "http://localhost:8000",  # Prueba primero con localhost
    "http://fastapi:8000"     # Fallback para entorno Docker
]

# Ruta del endpoint
ENDPOINT = "/api/v1/n8n/process-rgpd"

def find_test_image():
    """Busca una imagen de prueba en directorios comunes"""
    possible_paths = [
        "./facturas",
        "./test/facturas",
        "./test/images",
        "./images",
        "./test_images"
    ]
    
    image_extensions = ['.png', '.jpg', '.jpeg', '.pdf']
    
    for path in possible_paths:
        if os.path.exists(path):
            for file in os.listdir(path):
                if any(file.lower().endswith(ext) for ext in image_extensions):
                    return os.path.join(path, file)
    
    # Si no encuentra en directorios, buscar en el directorio actual
    for file in os.listdir('.'):
        if any(file.lower().endswith(ext) for ext in image_extensions):
            return file
    
    return None

def test_rgpd_endpoint(image_path=None):
    """Prueba el endpoint de procesamiento RGPD con una imagen"""
    if not image_path:
        image_path = find_test_image()
        if not image_path:
            print("❌ No se encontró ninguna imagen de prueba")
            return False
    
    if not os.path.exists(image_path):
        print(f"❌ La imagen {image_path} no existe")
        return False
    
    print(f"🔍 Usando imagen de prueba: {image_path}")
    
    # Preparar archivo para enviar
    files = {'file': (os.path.basename(image_path), open(image_path, 'rb'))}
    
    # Intentar cada URL hasta que una funcione
    for api_url in API_URLS:
        full_url = f"{api_url}{ENDPOINT}"
        print(f"🌐 Intentando conectar a: {full_url}")
        
        try:
            response = requests.post(
                full_url,
                files=files,
                timeout=30  # Timeout amplio para permitir procesamiento
            )
            
            print(f"✅ Conexión exitosa a {api_url}")
            print(f"📊 Código de estado: {response.status_code}")
            
            # Mostrar respuesta
            try:
                response_json = response.json()
                print("\n📋 Respuesta JSON:")
                print(json.dumps(response_json, indent=2, ensure_ascii=False))
                return True
            except:
                print("\n📋 Respuesta (no es JSON):")
                print(response.text[:500])  # Limitar a 500 caracteres
                return False
                
        except requests.ConnectionError:
            print(f"❌ No se pudo conectar a {api_url}")
            continue
        except Exception as e:
            print(f"❌ Error al hacer la solicitud: {str(e)}")
            continue
    
    print("❌ No se pudo conectar a ninguna URL")
    return False

if __name__ == "__main__":
    # Si se proporciona una ruta de imagen como argumento, usarla
    image_path = sys.argv[1] if len(sys.argv) > 1 else None
    test_rgpd_endpoint(image_path)
