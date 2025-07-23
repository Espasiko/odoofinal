#!/usr/bin/env python3
"""
Script para activar el workflow webhook de Mistral OCR en n8n
"""

import requests
import json
import sys

def activate_workflow():
    """Activar el workflow webhook en n8n"""
    
    # ID del workflow creado
    workflow_id = "HOaLTsXnOZ20E5kf"
    
    # URLs de n8n (intentar ambas)
    n8n_urls = [
        "http://n8n:5678",
        "http://localhost:5678"
    ]
    
    for n8n_url in n8n_urls:
        try:
            print(f"Intentando conectar a n8n en: {n8n_url}")
            
            # Obtener el workflow actual
            get_response = requests.get(f"{n8n_url}/api/v1/workflows/{workflow_id}")
            
            if get_response.status_code != 200:
                print(f"No se pudo obtener el workflow: {get_response.status_code}")
                continue
                
            workflow_data = get_response.json()
            print(f"Workflow obtenido: {workflow_data['name']}")
            
            # Activar el workflow
            workflow_data['active'] = True
            
            # Actualizar el workflow
            update_response = requests.put(
                f"{n8n_url}/api/v1/workflows/{workflow_id}",
                json=workflow_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if update_response.status_code == 200:
                print("✅ Workflow activado exitosamente!")
                
                # Verificar que está activo
                verify_response = requests.get(f"{n8n_url}/api/v1/workflows/{workflow_id}")
                if verify_response.status_code == 200:
                    verify_data = verify_response.json()
                    if verify_data.get('active'):
                        print("✅ Verificación: El workflow está activo")
                        print(f"🔗 Webhook URL: {n8n_url}/webhook/mistral-ocr-webhook")
                        return True
                    else:
                        print("❌ El workflow no se activó correctamente")
                        
            else:
                print(f"❌ Error al activar workflow: {update_response.status_code}")
                print(f"Respuesta: {update_response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error de conexión con {n8n_url}: {e}")
            continue
    
    return False

def test_webhook():
    """Probar que el webhook responde"""
    
    webhook_urls = [
        "http://n8n:5678/webhook/mistral-ocr-webhook",
        "http://localhost:5678/webhook/mistral-ocr-webhook"
    ]
    
    for webhook_url in webhook_urls:
        try:
            print(f"\n🧪 Probando webhook: {webhook_url}")
            
            # Crear un archivo de prueba simple
            test_data = {
                'test': 'webhook_test',
                'timestamp': '2025-01-27T10:00:00Z'
            }
            
            response = requests.post(
                webhook_url,
                json=test_data,
                timeout=10
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Webhook responde correctamente!")
                return True
            else:
                print(f"❌ Webhook error: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error probando webhook {webhook_url}: {e}")
            continue
    
    return False

if __name__ == "__main__":
    print("🚀 Activando workflow webhook de Mistral OCR...")
    
    if activate_workflow():
        print("\n🧪 Probando webhook...")
        test_webhook()
    else:
        print("❌ No se pudo activar el workflow")
        sys.exit(1)
    
    print("\n✅ Proceso completado!")
