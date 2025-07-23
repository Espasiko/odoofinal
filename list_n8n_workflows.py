#!/usr/bin/env python3
"""
Lista todos los workflows disponibles en n8n
"""

import requests
import json
import os

# Configuración
N8N_BASE_URL = "http://localhost:5678"
API_KEY = os.getenv('N8N_API_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJlNzE4M2QyYy1lMTNjLTQ4NGYtOWY5Zi03ZmQ1Y2U3ZmE1ZmYiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzUyOTQ0ODI4fQ.Sx3wsxu1-KJuaa3SFb8qMUfT59F8x7M1VIcyJvzO0Ts')

def list_workflows():
    """Lista todos los workflows disponibles"""
    headers = {
        'X-N8N-API-KEY': API_KEY,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(f"{N8N_BASE_URL}/api/v1/workflows", headers=headers, timeout=10)
        
        if response.status_code == 200:
            workflows = response.json()
            print("📋 WORKFLOWS DISPONIBLES:")
            print("=" * 60)
            
            for i, workflow in enumerate(workflows.get('data', []), 1):
                print(f"{i}. Nombre: {workflow.get('name', 'Sin nombre')}")
                print(f"   ID: {workflow.get('id')}")
                print(f"   Activo: {'✅' if workflow.get('active') else '❌'}")
                print(f"   Nodos: {len(workflow.get('nodes', []))}")
                print(f"   Creado: {workflow.get('createdAt', 'N/A')}")
                print("-" * 40)
            
            return workflows.get('data', [])
        else:
            print(f"❌ Error obteniendo workflows: {response.status_code}")
            return []
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return []

def get_workflow_details(workflow_id: str):
    """Obtiene detalles de un workflow específico"""
    headers = {
        'X-N8N-API-KEY': API_KEY,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(f"{N8N_BASE_URL}/api/v1/workflows/{workflow_id}", headers=headers, timeout=10)
        
        if response.status_code == 200:
            workflow = response.json()
            print(f"\n🔍 DETALLES DEL WORKFLOW: {workflow.get('name')}")
            print("=" * 60)
            print(f"ID: {workflow.get('id')}")
            print(f"Activo: {'✅' if workflow.get('active') else '❌'}")
            print(f"Nodos: {len(workflow.get('nodes', []))}")
            
            print("\n📋 NODOS:")
            for node in workflow.get('nodes', []):
                print(f"  - {node.get('name')} ({node.get('type')})")
            
            return workflow
        else:
            print(f"❌ Error obteniendo detalles: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return None

def main():
    print("=" * 60)
    print("📋 LISTADO DE WORKFLOWS N8N")
    print("=" * 60)
    
    workflows = list_workflows()
    
    if workflows:
        # Buscar workflows relacionados con OCR/PDF/Mistral
        relevant_workflows = []
        for workflow in workflows:
            name = workflow.get('name', '').lower()
            if any(keyword in name for keyword in ['ocr', 'pdf', 'mistral', 'factura', 'invoice']):
                relevant_workflows.append(workflow)
        
        if relevant_workflows:
            print("\n🎯 WORKFLOWS RELEVANTES PARA PDF/OCR:")
            print("=" * 60)
            for workflow in relevant_workflows:
                print(f"📄 {workflow.get('name')}")
                print(f"   ID: {workflow.get('id')}")
                print(f"   Activo: {'✅' if workflow.get('active') else '❌'}")
                
                # Obtener detalles
                get_workflow_details(workflow.get('id'))
                print()

if __name__ == "__main__":
    main()
