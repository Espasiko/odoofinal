#!/usr/bin/env python3
import requests
import base64
import json

def test_mistral_ocr():
    # Encode image to base64
    with open('/home/espasiko/mainmanusodoo/manusodoo-roto/ejemplos/BSH-balay.png', 'rb') as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')
    
    # API request
    url = "https://api.mistral.ai/v1/ocr/process"
    headers = {
        "Authorization": "Bearer qlsBKB80fbxr7YQPg9VnMKAdIIZKA11m",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "mistral-ocr-latest",
        "document": {
            "type": "image_url",
            "image_url": f"data:image/png;base64,{base64_image}"
        },
        "include_image_base64": True
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:500]}...")
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    test_mistral_ocr()

try:
    from api.services.mistral_ocr_service import get_mistral_ocr_service
    print("✓ Importación exitosa")
    
    service = get_mistral_ocr_service()
    print("✓ Servicio Mistral OCR inicializado correctamente")
    print(f"✓ Modelo configurado: {service.model}")
    print(f"✓ API Key configurada: {'Sí' if service.api_key else 'No'}")
    print(f"✓ Formatos soportados: {service.get_supported_formats()}")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()