#!/usr/bin/env python3
"""
Script de prueba para verificar que Mistral OCR funciona correctamente
con la extracción de datos de facturas implementada.
"""

import requests
import json
from pathlib import Path

def test_mistral_ocr():
    """Prueba el servicio Mistral OCR con un documento de ejemplo"""
    
    # URL del servidor
    base_url = "http://localhost:8002"
    
    # Primero, obtener token de autenticación
    auth_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    print("🔐 Obteniendo token de autenticación...")
    auth_response = requests.post(f"{base_url}/token", data=auth_data)
    
    if auth_response.status_code != 200:
        print(f"❌ Error de autenticación: {auth_response.status_code}")
        print(auth_response.text)
        return
    
    token = auth_response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    print("✅ Token obtenido correctamente")
    
    # Buscar un archivo PDF de ejemplo
    test_files = [
        "/home/espasiko/mainmanusodoo/manusodoo-roto/Nueva carpeta/Facturas originales.pdf",
        "/home/espasiko/mainmanusodoo/manusodoo-roto/examples/sample_invoice.pdf"
    ]
    
    test_file = None
    for file_path in test_files:
        if Path(file_path).exists():
            test_file = file_path
            break
    
    if not test_file:
        print("⚠️  No se encontró archivo de prueba. Creando uno de ejemplo...")
        # Crear un archivo de texto simple para prueba
        test_file = "/tmp/test_invoice.txt"
        with open(test_file, "w") as f:
            f.write("""
            FACTURA
            
            Número: FAC-2024-001
            Fecha: 15/01/2024
            
            Proveedor: Empresa Test S.L.
            CIF: B12345678
            
            Cliente: Cliente Ejemplo S.A.
            CIF: A87654321
            
            Concepto: Servicios de consultoría
            Cantidad: 1
            Precio: 1000.00 €
            
            Subtotal: 1000.00 €
            IVA (21%): 210.00 €
            Total: 1210.00 €
            """)
    
    print(f"📄 Usando archivo de prueba: {test_file}")
    
    # Probar el endpoint de Mistral OCR
    print("🔍 Procesando documento con Mistral OCR...")
    
    with open(test_file, "rb") as f:
        files = {"file": (Path(test_file).name, f, "application/pdf")}
        
        response = requests.post(
            f"{base_url}/api/v1/mistral-ocr/process-document",
            files=files,
            headers=headers
        )
    
    print(f"📊 Respuesta del servidor: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Documento procesado exitosamente!")
        print(f"📝 Texto extraído: {len(result.get('extracted_data', {}).get('full_text', ''))} caracteres")
        print(f"🏷️  Datos extraídos: {json.dumps(result.get('extracted_data', {}), indent=2, ensure_ascii=False)}")
    else:
        print(f"❌ Error procesando documento: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_mistral_ocr()