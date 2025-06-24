#!/usr/bin/env python3
import requests
import json

def get_auth_token():
    """Obtener token de autenticación"""
    auth_url = "http://localhost:8000/token"
    auth_data = {
        "username": "yo@mail.com",
        "password": "admin"
    }
    
    try:
        response = requests.post(auth_url, data=auth_data)
        if response.status_code == 200:
            return response.json().get('access_token')
        else:
            print(f"Error de autenticación: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return None
    except Exception as e:
        print(f"Error al obtener token: {e}")
        return None

def test_supported_formats(token):
    """Probar endpoint de formatos soportados"""
    url = "http://localhost:8000/api/v1/mistral-ocr/supported-formats"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Formatos soportados - Status: {response.status_code}")
        if response.status_code == 200:
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error al probar formatos: {e}")

def test_process_document(token, file_path):
    """Probar procesamiento de documento"""
    url = "http://localhost:8000/api/v1/mistral-ocr/process-document"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(url, headers=headers, files=files)
            
        print(f"Procesamiento documento - Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("✓ Documento procesado exitosamente")
            print(f"Texto extraído: {result.get('extracted_text', '')[:200]}...")
            return result
        else:
            print(f"Error: {response.text}")
            return None
    except Exception as e:
        print(f"Error al procesar documento: {e}")
        return None

if __name__ == "__main__":
    print("=== PRUEBA MISTRAL OCR ===")
    
    # 1. Obtener token
    print("\n1. Obteniendo token de autenticación...")
    token = get_auth_token()
    
    if not token:
        print("❌ No se pudo obtener token de autenticación")
        exit(1)
    
    print(f"✓ Token obtenido: {token[:20]}...")
    
    # 2. Probar formatos soportados
    print("\n2. Probando formatos soportados...")
    test_supported_formats(token)
    
    # 3. Probar procesamiento de documento
    print("\n3. Probando procesamiento de documento...")
    file_path = "/home/espasiko/mainmanusodoo/manusodoo-roto/Nueva carpeta/Facturas originales.pdf"
    result = test_process_document(token, file_path)
    
    if result:
        print("\n✅ MISTRAL OCR ESTÁ FUNCIONANDO CORRECTAMENTE")
    else:
        print("\n❌ MISTRAL OCR NO ESTÁ PROCESANDO DOCUMENTOS")