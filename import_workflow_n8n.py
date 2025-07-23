#!/usr/bin/env python3
import requests
import json
import os
import sys

# Configuración
N8N_API_URL = "http://localhost:5678/api/v1"
N8N_API_KEY = os.environ.get("N8N_API_KEY", "")  # Si tienes una API key configurada

def import_workflow(workflow_file):
    """Importa un workflow desde un archivo JSON a n8n"""
    print(f"Importando workflow desde {workflow_file}...")
    
    # Leer el archivo JSON
    try:
        with open(workflow_file, 'r') as f:
            workflow_data = json.load(f)
    except Exception as e:
        print(f"Error al leer el archivo: {e}")
        return False
    
    # Endpoint para crear un nuevo workflow
    url = f"{N8N_API_URL}/workflows"
    
    # Configurar headers
    headers = {
        "Content-Type": "application/json"
    }
    
    if N8N_API_KEY:
        headers["X-N8N-API-KEY"] = N8N_API_KEY
    
    # Enviar solicitud para crear el workflow
    try:
        response = requests.post(url, json=workflow_data, headers=headers)
        response.raise_for_status()
        
        # Obtener el ID del workflow creado
        workflow_id = response.json().get("data", {}).get("id")
        
        if workflow_id:
            print(f"Workflow importado correctamente con ID: {workflow_id}")
            
            # Activar el workflow
            activate_url = f"{N8N_API_URL}/workflows/{workflow_id}/activate"
            activate_response = requests.post(activate_url, headers=headers)
            
            if activate_response.status_code == 200:
                print(f"Workflow activado correctamente")
                return True
            else:
                print(f"Error al activar el workflow: {activate_response.status_code} - {activate_response.text}")
        else:
            print(f"No se pudo obtener el ID del workflow creado")
        
        return True
    except Exception as e:
        print(f"Error al importar el workflow: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python import_workflow_n8n.py <ruta_al_archivo_workflow.json>")
        sys.exit(1)
    
    workflow_file = sys.argv[1]
    if not os.path.exists(workflow_file):
        print(f"El archivo {workflow_file} no existe")
        sys.exit(1)
    
    success = import_workflow(workflow_file)
    sys.exit(0 if success else 1)
