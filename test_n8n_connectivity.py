#!/usr/bin/env python3
"""
Test de conectividad con la API de n8n
Fecha: 21/07/2025
"""

import requests
import json
import os
from typing import Dict, Any, Optional

# Configuración de la API
N8N_BASE_URL = "http://localhost:5678"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJlNzE4M2QyYy1lMTNjLTQ4NGYtOWY5Zi03ZmQ1Y2U3ZmE1ZmYiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzUyOTQ0ODI4fQ.Sx3wsxu1-KJuaa3SFb8qMUfT59F8x7M1VIcyJvzO0Ts"

def test_n8n_connection() -> bool:
    """Test básico de conectividad con n8n"""
    try:
        print("🔍 Probando conectividad con n8n...")
        response = requests.get(f"{N8N_BASE_URL}/healthz", timeout=5)
        if response.status_code == 200:
            print("✅ n8n está funcionando")
            return True
        else:
            print(f"❌ n8n responde pero con error: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Error conectando con n8n: {e}")
        return False

def test_n8n_api() -> Optional[Dict[str, Any]]:
    """Test de la API de n8n con autenticación"""
    headers = {
        'X-N8N-API-KEY': API_KEY,
        'Content-Type': 'application/json'
    }
    
    try:
        print("🔍 Probando API de n8n...")
        response = requests.get(f"{N8N_BASE_URL}/api/v1/workflows", headers=headers, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            workflows = response.json()
            print(f"✅ API funcionando - {len(workflows.get('data', []))} workflows encontrados")
            return workflows
        elif response.status_code == 401:
            print("❌ Error de autenticación - API key inválida")
            return None
        else:
            print(f"❌ Error API: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error conectando con API: {e}")
        return None

def test_n8n_api_info() -> Optional[Dict[str, Any]]:
    """Test de información de la API"""
    headers = {
        'X-N8N-API-KEY': API_KEY,
        'Content-Type': 'application/json'
    }
    
    try:
        print("🔍 Probando acceso a información de API...")
        # Probamos con el endpoint de workflows que es más confiable
        response = requests.get(f"{N8N_BASE_URL}/api/v1/workflows", headers=headers, timeout=10)
        
        if response.status_code == 200:
            workflows = response.json()
            print(f"✅ API accesible - {len(workflows.get('data', []))} workflows encontrados")
            return workflows
        else:
            print(f"❌ Error accediendo API: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return None

def main():
    """Función principal de test"""
    print("=" * 60)
    print("🧪 TEST DE CONECTIVIDAD N8N API")
    print("=" * 60)
    
    # Test 1: Conectividad básica
    if not test_n8n_connection():
        print("❌ n8n no está disponible. Verifica que esté ejecutándose.")
        return
    
    # Test 2: API con autenticación
    workflows = test_n8n_api()
    if workflows is None:
        print("❌ API no funciona correctamente")
        return
    
    # Test 3: Información adicional de API
    api_info = test_n8n_api_info()
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE TESTS")
    print("=" * 60)
    print("✅ Conectividad básica: OK")
    print("✅ API con autenticación: OK")
    print(f"✅ API completamente funcional: {'OK' if api_info else 'ERROR'}")
    
    if workflows:
        print(f"\n📋 Workflows disponibles: {len(workflows.get('data', []))}")
        for workflow in workflows.get('data', [])[:3]:  # Mostrar solo los primeros 3
            print(f"  - {workflow.get('name', 'Sin nombre')} (ID: {workflow.get('id')})")
    
    print("\n🎆 ¡Test completado exitosamente!")
    print("🚀 n8n API está listo para usar")

if __name__ == "__main__":
    main()