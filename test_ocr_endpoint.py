#!/usr/bin/env python3
"""
Script para probar el endpoint de OCR con una factura de ejemplo
"""
import os
import json
import requests
from pprint import pprint

def test_ocr_endpoint():
    """
    Prueba el endpoint de OCR con una factura de ejemplo
    """
    # URL del endpoint
    url = "http://localhost:8000/api/v1/mistral-free-ocr/process-invoice"
    
    # Ruta a la factura de ejemplo
    factura_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "ejemplos",
        "NEVIR - FacturaF2402846.pdf"
    )
    
    if not os.path.exists(factura_path):
        print(f"Error: No se encontró el archivo de factura: {factura_path}")
        return
    
    print(f"Procesando factura: {factura_path}")
    
    # Obtener token de autenticación
    auth_url = "http://localhost:8000/token"
    auth_data = {
        "username": "admin",
        "password": "admin"
    }
    
    try:
        auth_response = requests.post(auth_url, data=auth_data)
        auth_response.raise_for_status()
        token = auth_response.json().get("access_token")
        
        if not token:
            print("Error: No se pudo obtener el token de autenticación")
            return
        
        # Configurar headers con el token
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        # Configurar datos del formulario
        files = {
            "file": (os.path.basename(factura_path), open(factura_path, "rb"), "application/pdf")
        }
        data = {
            "create_in_odoo": "false"
        }
        
        # Enviar solicitud al endpoint
        response = requests.post(url, headers=headers, files=files, data=data)
        response.raise_for_status()
        
        # Procesar respuesta
        result = response.json()
        
        # Guardar resultado en un archivo JSON para análisis
        output_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "ocr_endpoint_result.json"
        )
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"Resultado guardado en: {output_path}")
        
        # Mostrar datos principales extraídos
        if result.get("success", False):
            print("✅ Procesamiento OCR exitoso")
            
            invoice_data = result.get("invoice_data", {})
            print("Datos principales extraídos:")
            print(f"- Número de factura: {invoice_data.get('invoice_number', 'No encontrado')}")
            print(f"- Fecha: {invoice_data.get('invoice_date', 'No encontrada')}")
            print(f"- Proveedor: {invoice_data.get('supplier_name', 'No encontrado')}")
            print(f"- Total: {invoice_data.get('total_amount', 'No encontrado')}")
            
            # Mostrar líneas de factura si existen
            lines = invoice_data.get("line_items", [])
            if lines:
                print(f"- Líneas de factura: {len(lines)}")
                for i, line in enumerate(lines[:3], 1):
                    print(f"  {i}. {line.get('description', 'Sin descripción')} - {line.get('qty', 0)} x {line.get('price_unit', 0)} = {line.get('subtotal', 0)}")
                if len(lines) > 3:
                    print(f"  ... y {len(lines) - 3} líneas más")
        else:
            print(f"❌ Error en procesamiento OCR: {result.get('error', 'Error desconocido')}")
    
    except requests.exceptions.RequestException as e:
        print(f"Error en la solicitud HTTP: {str(e)}")
    except Exception as e:
        print(f"Error inesperado: {str(e)}")
        import traceback
        print(traceback.format_exc())
    finally:
        # Cerrar el archivo
        if 'files' in locals() and 'file' in files:
            files['file'][1].close()

if __name__ == "__main__":
    test_ocr_endpoint()
