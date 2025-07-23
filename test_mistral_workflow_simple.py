#!/usr/bin/env python3
"""
Test simple del workflow de Mistral OCR usando la API de n8n
"""

import requests
import json
import time
import os

# Configuración
N8N_BASE_URL = "http://localhost:5678"
API_KEY = os.getenv('N8N_API_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJlNzE4M2QyYy1lMTNjLTQ4NGYtOWY5Zi03ZmQ1Y2U3ZmE1ZmYiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzUyOTQ0ODI4fQ.Sx3wsxu1-KJuaa3SFb8qMUfT59F8x7M1VIcyJvzO0Ts')

# ID del workflow creado
WORKFLOW_ID = "bViy3JoOkJlzltpX"

def execute_workflow():
    """Ejecuta el workflow manualmente"""
    headers = {
        'X-N8N-API-KEY': API_KEY,
        'Content-Type': 'application/json'
    }
    
    # Datos de entrada para el workflow
    payload = {
        "startNodes": ["manual-trigger"],
        "runData": {}
    }
    
    try:
        print("🚀 Ejecutando workflow Mistral OCR...")
        response = requests.post(
            f"{N8N_BASE_URL}/api/v1/workflows/{WORKFLOW_ID}/run",
            headers=headers,
            json=payload,
            timeout=120
        )
        
        if response.status_code == 201:
            execution_data = response.json()
            execution_id = execution_data.get('id')
            print(f"✅ Workflow iniciado - Execution ID: {execution_id}")
            
            # Esperar y verificar el resultado
            return check_execution_status(execution_id)
        else:
            print(f"❌ Error ejecutando workflow: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return None

def check_execution_status(execution_id, max_wait=60):
    """Verifica el estado de la ejecución"""
    headers = {
        'X-N8N-API-KEY': API_KEY
    }
    
    print(f"⏳ Verificando estado de ejecución {execution_id}...")
    
    for i in range(max_wait):
        try:
            response = requests.get(
                f"{N8N_BASE_URL}/api/v1/executions/{execution_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                execution = response.json()
                status = execution.get('status')
                
                print(f"📊 Estado: {status} ({i+1}/{max_wait})")
                
                if status == 'success':
                    print("🎉 ¡Ejecución completada exitosamente!")
                    return execution
                elif status == 'error':
                    print("❌ Error en la ejecución")
                    print(f"Error: {execution.get('error', 'No details')}")
                    return execution
                elif status in ['running', 'waiting']:
                    time.sleep(2)
                    continue
                else:
                    print(f"⚠️ Estado desconocido: {status}")
                    return execution
            else:
                print(f"❌ Error obteniendo estado: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error verificando estado: {e}")
            time.sleep(2)
    
    print("⏰ Timeout esperando resultado")
    return None

def main():
    """Función principal"""
    print("=" * 60)
    print("🧪 TEST WORKFLOW: Facturas OCR Mistral Simple")
    print("=" * 60)
    print(f"📋 Workflow ID: {WORKFLOW_ID}")
    print(f"🔗 URL Dropbox: ABRILA factura")
    
    # Ejecutar workflow
    result = execute_workflow()
    
    if result:
        print("\n🎆 RESULTADO:")
        print("=" * 60)
        
        # Mostrar datos de salida si están disponibles
        data = result.get('data', {})
        if data:
            # Buscar el último nodo ejecutado
            for node_name, node_data in data.items():
                if node_data and len(node_data) > 0:
                    print(f"📤 Salida de {node_name}:")
                    for item in node_data[0]:
                        if 'json' in item:
                            output = json.dumps(item['json'], indent=2, ensure_ascii=False)
                            if len(output) > 1000:
                                print(output[:1000] + "\n... (truncado)")
                            else:
                                print(output)
                        break
                    break
        else:
            print("📭 No hay datos de salida disponibles")
    
    print("\n🎆 Test completado")

if __name__ == "__main__":
    main()