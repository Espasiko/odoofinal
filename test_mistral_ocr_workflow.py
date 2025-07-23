#!/usr/bin/env python3
"""
Test del workflow "Facturas OCR Mistral Directo" con PDF real
Workflow ID: pu0pfchYJoeeVWQk
"""

import requests
import json
import base64
import time
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Configuración
N8N_BASE_URL = "http://localhost:5678"
API_KEY = os.getenv('N8N_API_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJlNzE4M2QyYy1lMTNjLTQ4NGYtOWY5Zi03ZmQ1Y2U3ZmE1ZmYiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzUyOTQ0ODI4fQ.Sx3wsxu1-KJuaa3SFb8qMUfT59F8x7M1VIcyJvzO0Ts')

# ID del workflow "Facturas OCR Mistral Directo"
WORKFLOW_ID = "pu0pfchYJoeeVWQk"

def get_webhook_url(workflow_id: str) -> Optional[str]:
    """Obtiene la URL del webhook del workflow"""
    headers = {
        'X-N8N-API-KEY': API_KEY,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(f"{N8N_BASE_URL}/api/v1/workflows/{workflow_id}", headers=headers, timeout=10)
        
        if response.status_code == 200:
            workflow = response.json()
            
            # Buscar el nodo webhook
            for node in workflow.get('nodes', []):
                if node.get('type') == 'n8n-nodes-base.webhook':
                    webhook_path = node.get('parameters', {}).get('path', '')
                    if webhook_path:
                        return f"{N8N_BASE_URL}/webhook/{webhook_path}"
            
            print("❌ No se encontró webhook en el workflow")
            return None
        else:
            print(f"❌ Error obteniendo workflow: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return None

def encode_pdf_to_base64(pdf_path: str) -> Optional[str]:
    """Codifica un PDF a base64"""
    try:
        with open(pdf_path, 'rb') as pdf_file:
            pdf_content = pdf_file.read()
            return base64.b64encode(pdf_content).decode('utf-8')
    except Exception as e:
        print(f"❌ Error codificando PDF: {e}")
        return None

def send_pdf_to_webhook(webhook_url: str, pdf_path: str) -> Optional[Dict[str, Any]]:
    """Envía el PDF al webhook de n8n"""
    
    # Codificar PDF a base64
    pdf_base64 = encode_pdf_to_base64(pdf_path)
    if not pdf_base64:
        return None
    
    # Preparar payload
    payload = {
        "pdf_data": pdf_base64,
        "filename": Path(pdf_path).name,
        "provider": "NEVIR",
        "test_mode": True,
        "source": "api_test"
    }
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    try:
        print(f"🚀 Enviando PDF al webhook...")
        print(f"📄 Archivo: {Path(pdf_path).name}")
        print(f"📊 Tamaño: {len(pdf_base64)} caracteres base64")
        
        response = requests.post(webhook_url, json=payload, headers=headers, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Webhook ejecutado exitosamente")
            return result
        else:
            print(f"❌ Error en webhook: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error enviando al webhook: {e}")
        return None

def main():
    """Función principal"""
    print("=" * 60)
    print("🧪 TEST WORKFLOW: Facturas OCR Mistral Directo")
    print("=" * 60)
    
    # Ruta del PDF de prueba
    pdf_path = "/home/espasiko/mainmanusodoo/manusodoo-roto/ejemplos/NEVIR - FacturaF2402846.pdf"
    
    if not Path(pdf_path).exists():
        print(f"❌ PDF no encontrado: {pdf_path}")
        return
    
    print(f"📋 Workflow ID: {WORKFLOW_ID}")
    print(f"📄 PDF: {Path(pdf_path).name}")
    
    # Obtener URL del webhook
    webhook_url = get_webhook_url(WORKFLOW_ID)
    if not webhook_url:
        print("❌ No se pudo obtener la URL del webhook")
        return
    
    print(f"🔗 Webhook URL: {webhook_url}")
    
    # Enviar PDF al webhook
    result = send_pdf_to_webhook(webhook_url, pdf_path)
    
    if result:
        print("\n🎉 ¡RESULTADO OBTENIDO!")
        print("=" * 60)
        
        # Mostrar resultado formateado
        if isinstance(result, dict):
            # Si el resultado contiene datos de factura estructurados
            if 'proveedor' in result:
                print("📋 DATOS EXTRAÍDOS:")
                print(f"  Proveedor: {result.get('proveedor', {}).get('nombre', 'N/A')}")
                print(f"  CIF: {result.get('proveedor', {}).get('cif', 'N/A')}")
                print(f"  Factura: {result.get('factura', {}).get('numero', 'N/A')}")
                print(f"  Fecha: {result.get('factura', {}).get('fecha', 'N/A')}")
                print(f"  Total: {result.get('totales', {}).get('total', 'N/A')}")
            
            # Mostrar resultado completo (limitado)
            print("\n📤 RESULTADO COMPLETO:")
            result_str = json.dumps(result, indent=2, ensure_ascii=False)
            if len(result_str) > 2000:
                print(result_str[:2000] + "\n... (truncado)")
            else:
                print(result_str)
        else:
            print(f"📤 Resultado: {result}")
    
    print("\n🎆 Test completado")

if __name__ == "__main__":
    main()
