#!/usr/bin/env python3
"""
Script de prueba para verificar la API de n8n
"""
import requests
import json
import sys
import os
from pathlib import Path

# Añadir el directorio raíz al path para importar módulos
sys.path.append(str(Path(__file__).parent))

from api.utils.n8n_config import n8n_config

def test_n8n_connection():
    """Prueba la conexión básica con n8n"""
    print("🔍 Probando conexión con n8n...")
    
    # URLs a probar (interno Docker y externo)
    urls_to_test = [
        "http://n8n:5678/api/v1",  # Interno Docker
        "http://localhost:5678/api/v1"  # Externo
    ]
    
    for url in urls_to_test:
        try:
            print(f"  Probando URL: {url}")
            response = requests.get(f"{url}/workflows", timeout=5)
            print(f"  Status Code: {response.status_code}")
            
            if response.status_code == 200:
                workflows = response.json()
                print(f"  ✅ Conexión exitosa! Encontrados {len(workflows)} workflows")
                return url, workflows
            elif response.status_code == 401:
                print(f"  🔑 Requiere autenticación")
                return url, None
            else:
                print(f"  ❌ Error: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Error de conexión: {e}")
    
    return None, None

def test_n8n_with_auth():
    """Prueba la API de n8n con autenticación"""
    print("\n🔐 Probando API de n8n con autenticación...")
    
    # URLs a probar
    urls_to_test = [
        "http://n8n:5678/api/v1",  # Interno Docker
        "http://localhost:5678/api/v1"  # Externo
    ]
    
    headers = {
        "Authorization": f"Bearer {n8n_config.N8N_API_KEY}",
        "Content-Type": "application/json"
    }
    
    print(f"  API Key: {n8n_config.N8N_API_KEY[:20]}...")
    
    for url in urls_to_test:
        try:
            print(f"  Probando URL con auth: {url}")
            response = requests.get(f"{url}/workflows", headers=headers, timeout=5)
            print(f"  Status Code: {response.status_code}")
            
            if response.status_code == 200:
                workflows = response.json()
                print(f"  ✅ Autenticación exitosa! Encontrados {len(workflows)} workflows")
                
                # Mostrar información de workflows
                for workflow in workflows[:3]:  # Mostrar solo los primeros 3
                    print(f"    - {workflow.get('name', 'Sin nombre')} (ID: {workflow.get('id', 'N/A')})")
                
                return url, workflows
            elif response.status_code == 401:
                print(f"  ❌ Error de autenticación")
            else:
                print(f"  ❌ Error: {response.status_code} - {response.text[:100]}")
                
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Error de conexión: {e}")
    
    return None, None

def test_workflow_execution():
    """Prueba la ejecución de un workflow"""
    print("\n🚀 Probando ejecución de workflow...")
    
    # Primero obtener los workflows disponibles
    url, workflows = test_n8n_with_auth()
    
    if not workflows:
        print("  ❌ No se pudieron obtener workflows")
        return
    
    # Buscar un workflow de prueba
    test_workflow = None
    for workflow in workflows:
        name = workflow.get('name', '').lower()
        if 'test' in name or 'webhook' in name or 'ocr' in name:
            test_workflow = workflow
            break
    
    if not test_workflow:
        print("  ⚠️ No se encontró un workflow de prueba adecuado")
        return
    
    print(f"  Probando workflow: {test_workflow.get('name')}")
    print(f"  ID: {test_workflow.get('id')}")
    
    # Verificar si el workflow está activo
    headers = {
        "Authorization": f"Bearer {n8n_config.N8N_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        workflow_id = test_workflow.get('id')
        response = requests.get(f"{url}/workflows/{workflow_id}", headers=headers, timeout=5)
        
        if response.status_code == 200:
            workflow_details = response.json()
            is_active = workflow_details.get('active', False)
            print(f"  Estado del workflow: {'Activo' if is_active else 'Inactivo'}")
            
            if not is_active:
                print("  ⚠️ El workflow no está activo, no se puede ejecutar")
            else:
                print("  ✅ Workflow listo para ejecución")
        else:
            print(f"  ❌ Error obteniendo detalles: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Error: {e}")

def main():
    """Función principal"""
    print("🧪 Iniciando pruebas de la API de n8n")
    print("=" * 50)
    
    # Mostrar configuración actual
    print(f"📋 Configuración actual:")
    print(f"  N8N_API_URL: {n8n_config.N8N_API_URL}")
    print(f"  N8N_API_KEY: {n8n_config.N8N_API_KEY[:20]}...")
    print(f"  N8N_WEBHOOK_URL: {n8n_config.N8N_WEBHOOK_URL}")
    print()
    
    # Ejecutar pruebas
    test_n8n_connection()
    test_n8n_with_auth()
    test_workflow_execution()
    
    print("\n" + "=" * 50)
    print("🏁 Pruebas completadas")

if __name__ == "__main__":
    main()
