#!/usr/bin/env python3
import requests
import json
import sys

# Configuración
API_URL = "http://localhost:8000"
USERNAME = "admin"
PASSWORD = "admin"

# Datos de ejemplo de una factura procesada por OCR
invoice_data = {
    "invoice_number": "32506198",
    "invoice_date": "2025-02-27",
    "due_date": None,
    "supplier_name": "FABRILAMP ILUMINACIÓN S.L.",
    "supplier_vat": "B41982075",
    "supplier_address": "CL. Trabajo Nº 4",
    "supplier_city": "Rincónada (La)",
    "supplier_zip": "41309",
    "customer_name": "El Pelotazo",
    "customer_vat": "B04957403",
    "subtotal": 1232.17,
    "tax_amount": 0,
    "total_amount": 1232.17,
    "tax_rate": 0,
    "payment_method": None,
    "payment_terms": None,
    "currency": "EUR",
    "line_items": [
        {
            "name": "VENTILADOR BAYOMO 5W 6980LM NIQUEL 4 ASPAS DESP. 34.5/42X50/107 D-3 COLOR...",
            "quantity": 5,
            "price_unit": 39.97,
            "discount": 10,
            "default_code": "142591403",
            "ean13": None,
            "tax_rate": 0
        },
        {
            "name": "Canon ECORAEE RD/208/2005 0.12",
            "quantity": 5,
            "price_unit": 0.12,
            "discount": 0,
            "default_code": "CANON/3",
            "ean13": None,
            "tax_rate": 0
        }
    ]
}

# Estructura 1: Como lo envía el frontend según el código
payload1 = {
    "ocr_data": {
        "invoice_data": invoice_data
    },
    "supplier_id": 1,  # ID del proveedor (ajustar según sea necesario)
    "update_if_exists": False
}

# Estructura 2: Alternativa con ocr_data conteniendo directamente los datos
payload2 = {
    "ocr_data": invoice_data,
    "supplier_id": 1,
    "update_if_exists": False
}

# Estructura 3: Alternativa con ocr_data conteniendo filename y otros campos
payload3 = {
    "ocr_data": {
        "success": True,
        "message": "Factura procesada exitosamente con Mistral Free OCR",
        "filename": "ABRILA - factura_32506198.pdf",
        "file_type": ".pdf",
        "processed_by": "admin",
        "invoice_data": invoice_data,
        "ocr_confidence": "unknown",
        "ocr_id": "20250713163144_ABRILA - factura_32506198"
    },
    "supplier_id": 1,
    "update_if_exists": False
}

def get_token():
    """Obtener token de autenticación"""
    response = requests.post(
        f"{API_URL}/token",
        data={"username": USERNAME, "password": PASSWORD}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print(f"Error al obtener token: {response.status_code}")
        print(response.text)
        sys.exit(1)

def test_create_invoice(payload):
    """Probar el endpoint de creación de facturas"""
    token = get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print("\n=== Enviando solicitud ===")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    response = requests.post(
        f"{API_URL}/api/v1/mistral-free-ocr/create-invoice",
        headers=headers,
        json=payload
    )
    
    print(f"\nCódigo de respuesta: {response.status_code}")
    try:
        print(f"Respuesta: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Respuesta: {response.text}")
    
    return response

if __name__ == "__main__":
    print("=== Probando estructura 1 (Frontend) ===")
    test_create_invoice(payload1)
    
    print("\n=== Probando estructura 2 (Directa) ===")
    test_create_invoice(payload2)
    
    print("\n=== Probando estructura 3 (Con metadata) ===")
    test_create_invoice(payload3)
