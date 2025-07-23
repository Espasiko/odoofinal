#!/usr/bin/env python3
"""
Test del workflow de procesamiento de PDFs en n8n
Usa el workflow existente "Facturas OCR Mistral Funcional"
"""

import requests
import json
import time
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Configuración
N8N_BASE_URL = "http://localhost:5678"
API_KEY = os.getenv('N8N_API_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJlNzE4M2QyYy1lMTNjLTQ4NGYtOWY5Zi03ZmQ1Y2U3ZmE1ZmYiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzUyOTQ0ODI4fQ.Sx3wsxu1-KJuaa3SFb8qMUfT59F8x7M1VIcyJvzO0Ts')

# ID del workflow existente (obtenido del test anterior)
WORKFLOW_ID = "6eVQ0DPnnjRb26Sf"  # "Facturas OCR Mistral Funcional"

def upload_pdf_to_server(pdf_path: str) -> Optional[str]:
    """
    Simula subir PDF a un servidor web local para que n8n pueda descargarlo
    En un entorno real, subirías a un servidor web o usarías un webhook
    """
    print(f"📄 Preparando PDF: {pdf_path}")
    
    # Por ahora, vamos a usar una URL de ejemplo
    # En un entorno real, subirías el PDF a un servidor web
    pdf_name = Path(pdf_path).name
    print(f"✅ PDF preparado: {pdf_name}")
    
    # Retornamos una URL simulada - en n8n tendrás que configurar para leer archivos locales
    return f"file://{pdf_path}"

def execute_n8n_workflow(workflow_id: str, input_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Ejecuta un workflow de n8n con datos de entrada"""
    headers = {
        'X-N8N-API-KEY': API_KEY,
        'Content-Type': 'application/json'
    }
    
    payload = {
        "data": input_data
    }
    
    try:
        print(f"🚀 Ejecutando workflow {workflow_id}...")
        response = requests.post(
            f"{N8N_BASE_URL}/api/v1/workflows/{workflow_id}/execute",
            headers=headers,
            json=payload,
            timeout=60
        )
        
        if response.status_code == 201:
            result = response.json()
            print("✅ Workflow ejecutado exitosamente")
            return result
        else:
            print(f"❌ Error ejecutando workflow: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return None

def check_execution_status(execution_id: str) -> Optional[Dict[str, Any]]:
    """Verifica el estado de una ejecución"""
    headers = {
        'X-N8N-API-KEY': API_KEY,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(
            f"{N8N_BASE_URL}/api/v1/executions/{execution_id}",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Error verificando ejecución: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error verificando ejecución: {e}")
        return None

def main():
    """Función principal"""
    print("=" * 60)
    print("🧪 TEST DE WORKFLOW PDF PROCESSING N8N")
    print("=" * 60)
    
    # Ruta del PDF de prueba
    pdf_path = "/home/espasiko/mainmanusodoo/manusodoo-roto/ejemplos/NEVIR - FacturaF2402846.pdf"
    
    if not Path(pdf_path).exists():
        print(f"❌ PDF no encontrado: {pdf_path}")
        return
    
    # Preparar PDF
    pdf_url = upload_pdf_to_server(pdf_path)
    if not pdf_url:
        print("❌ Error preparando PDF")
        return
    
    # Datos de entrada para el workflow
    input_data = {
        "pdf_url": pdf_url,
        "pdf_path": pdf_path,  # Para acceso local
        "provider": "NEVIR",
        "test_mode": True
    }
    
    print(f"\n📋 Datos de entrada:")
    print(json.dumps(input_data, indent=2, ensure_ascii=False))
    
    # Ejecutar workflow
    result = execute_n8n_workflow(WORKFLOW_ID, input_data)
    
    if result:
        execution_id = result.get('data', {}).get('executionId')
        print(f"\n🔍 ID de ejecución: {execution_id}")
        
        # Esperar un poco y verificar estado
        print("⏳ Esperando resultado...")
        time.sleep(5)
        
        execution_status = check_execution_status(execution_id)
        if execution_status:
            status = execution_status.get('status', 'unknown')
            print(f"📊 Estado de ejecución: {status}")
            
            if status == 'success':
                print("🎉 ¡Workflow ejecutado exitosamente!")
                
                # Mostrar datos de salida si están disponibles
                output_data = execution_status.get('data', {}).get('resultData', {})
                if output_data:
                    print("\n📤 Datos de salida:")
                    print(json.dumps(output_data, indent=2, ensure_ascii=False)[:1000] + "...")
            else:
                print(f"⚠️ Ejecución terminó con estado: {status}")
                error = execution_status.get('data', {}).get('resultData', {}).get('error')
                if error:
                    print(f"❌ Error: {error}")
    
    print("\n🎆 Test completado")

if __name__ == "__main__":
    main()
