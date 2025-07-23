#!/usr/bin/env python3
"""
Script para probar el workflow n8n "mistral ocr" más simple
usando la API de n8n y un PDF real de ejemplo.
"""

import requests
import json
import time
import base64
from pathlib import Path

# Configuración
N8N_BASE_URL = "http://localhost:5678"
N8N_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJlNzE4M2QyYy1lMTNjLTQ4NGYtOWY5Zi03ZmQ1Y2U3ZmE1ZmYiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzUyOTQ0ODI4fQ.Sx3wsxu1-KJuaa3SFb8qMUfT59F8x7M1VIcyJvzO0Ts"

# Headers para API
headers = {
    "X-N8N-API-KEY": N8N_API_KEY,
    "Content-Type": "application/json"
}

def get_workflow_info(workflow_id):
    """Obtiene información detallada del workflow"""
    url = f"{N8N_BASE_URL}/api/v1/workflows/{workflow_id}"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        workflow = response.json()
        print(f"✅ Workflow: {workflow.get('name', 'Sin nombre')}")
        print(f"   ID: {workflow_id}")
        print(f"   Activo: {workflow.get('active', False)}")
        print(f"   Nodos: {len(workflow.get('nodes', []))}")
        
        # Buscar webhooks
        webhooks = []
        for node in workflow.get('nodes', []):
            if node.get('type') == 'n8n-nodes-base.webhook':
                path = node.get('parameters', {}).get('path', '')
                webhooks.append(path)
        
        if webhooks:
            print(f"   Webhooks: {', '.join(webhooks)}")
        
        return workflow
    else:
        print(f"❌ Error obteniendo workflow {workflow_id}: {response.status_code}")
        return None

def test_webhook(webhook_path, data):
    """Prueba un webhook con datos específicos"""
    webhook_url = f"{N8N_BASE_URL}/webhook/{webhook_path}"
    
    print(f"\n🔄 Probando webhook: {webhook_url}")
    print(f"📤 Datos enviados: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(webhook_url, json=data, timeout=30)
        print(f"📥 Respuesta HTTP: {response.status_code}")
        
        if response.text:
            try:
                result = response.json()
                print(f"📋 Respuesta JSON: {json.dumps(result, indent=2)}")
            except:
                print(f"📋 Respuesta texto: {response.text}")
        else:
            print("📋 Sin respuesta del webhook")
            
        return response.status_code == 200
        
    except requests.exceptions.Timeout:
        print("⏰ Timeout - el webhook puede estar procesando en background")
        return True
    except Exception as e:
        print(f"❌ Error llamando webhook: {e}")
        return False

def get_recent_executions(limit=3):
    """Obtiene las ejecuciones más recientes"""
    url = f"{N8N_BASE_URL}/api/v1/executions?limit={limit}"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        executions = response.json().get('data', [])
        print(f"\n📊 Últimas {len(executions)} ejecuciones:")
        
        for exec in executions:
            status = exec.get('status', 'unknown')
            mode = exec.get('mode', 'unknown')
            workflow_id = exec.get('workflowId', 'unknown')
            started = exec.get('startedAt', '')
            
            status_icon = "✅" if status == "success" else "❌" if status == "error" else "🔄"
            print(f"   {status_icon} ID: {exec['id']} | Status: {status} | Mode: {mode} | Workflow: {workflow_id}")
            print(f"      Iniciado: {started}")
        
        return executions
    else:
        print(f"❌ Error obteniendo ejecuciones: {response.status_code}")
        return []

def main():
    print("🚀 Probando workflow n8n 'mistral ocr' simple\n")
    
    # ID del workflow "mistral ocr" 
    workflow_id = "Zha2acx2Ah3NFcHB"
    
    # 1. Obtener información del workflow
    workflow = get_workflow_info(workflow_id)
    if not workflow:
        return
    
    # 2. Verificar si está activo
    if not workflow.get('active', False):
        print("⚠️  El workflow no está activo. Intentando activar...")
        activate_url = f"{N8N_BASE_URL}/api/v1/workflows/{workflow_id}"
        activate_response = requests.put(activate_url, headers=headers, json={"active": True})
        if activate_response.status_code == 200:
            print("✅ Workflow activado")
        else:
            print(f"❌ Error activando workflow: {activate_response.status_code}")
    
    # 3. Buscar webhooks en el workflow
    webhook_paths = []
    for node in workflow.get('nodes', []):
        if node.get('type') == 'n8n-nodes-base.webhook':
            path = node.get('parameters', {}).get('path', '')
            if path:
                webhook_paths.append(path)
    
    if not webhook_paths:
        print("❌ No se encontraron webhooks en este workflow")
        return
    
    # 4. Probar cada webhook encontrado
    test_data = {
        "pdf_url": "https://www.dropbox.com/scl/fi/n5wmb0uvzfjvp5x9liqqf/ABRILA-factura_32506198.pdf?rlkey=q0s2fbz2ti9uzyiaj9t6ujr18&st=so6ezwrj&dl=1",
        "filename": "ABRILA-factura_32506198.pdf",
        "provider": "ABRILA",
        "test_mode": True,
        "extract_fields": ["total", "date", "supplier", "invoice_number"]
    }
    
    success = False
    for webhook_path in webhook_paths:
        if test_webhook(webhook_path, test_data):
            success = True
            break
        time.sleep(2)
    
    # 5. Verificar ejecuciones recientes
    time.sleep(3)
    get_recent_executions(5)
    
    if success:
        print("\n✅ Prueba completada exitosamente")
    else:
        print("\n❌ La prueba falló")

if __name__ == "__main__":
    main()
