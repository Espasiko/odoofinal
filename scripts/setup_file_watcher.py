#!/usr/bin/env python3
"""
Script para configurar el sistema de File Watcher para Mistral OCR
"""

import os
import sys
import subprocess
import json

def create_directories():
    """Crear directorios necesarios para el file watcher"""
    directories = [
        '/tmp/rgpd_uploads',
        '/tmp/rgpd_results'
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"✅ Directorio creado: {directory}")
            
            # Dar permisos de escritura
            os.chmod(directory, 0o777)
            print(f"✅ Permisos configurados para: {directory}")
            
        except Exception as e:
            print(f"❌ Error creando directorio {directory}: {e}")
            return False
    
    return True

def create_n8n_workflow():
    """Crear el workflow en n8n usando la API"""
    workflow_path = "/home/espasiko/mainmanusodoo/manusodoo-roto/n8n/flujos/mistral_file_watcher_workflow.json"
    
    try:
        with open(workflow_path, 'r') as f:
            workflow_data = json.load(f)
        
        # Aquí podrías usar la API de n8n para crear el workflow
        # Por ahora solo mostramos la información
        print(f"✅ Workflow JSON cargado desde: {workflow_path}")
        print(f"📋 Workflow: {workflow_data['name']}")
        print(f"🔧 Nodos: {len(workflow_data['nodes'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error cargando workflow: {e}")
        return False

def create_test_file():
    """Crear un archivo de prueba para el file watcher"""
    test_content = """
    Este es un documento de prueba para el sistema OCR.
    
    Contiene información como:
    - Email: test@example.com
    - Número: 12345678
    - Fecha: 2025-01-23
    
    El sistema debería enmascarar los datos sensibles automáticamente.
    """
    
    test_file_path = "/tmp/rgpd_uploads/test_document.txt"
    
    try:
        with open(test_file_path, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        print(f"✅ Archivo de prueba creado: {test_file_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error creando archivo de prueba: {e}")
        return False

def show_usage_instructions():
    """Mostrar instrucciones de uso"""
    print("\n" + "="*60)
    print("🚀 INSTRUCCIONES DE USO - FILE WATCHER")
    print("="*60)
    
    print("\n1️⃣ ACTIVAR WORKFLOW EN N8N:")
    print("   - Ve a http://localhost:5678")
    print("   - Busca 'Mistral OCR File Watcher Workflow'")
    print("   - Actívalo manualmente")
    
    print("\n2️⃣ PROBAR EL SISTEMA:")
    print("   - Copia archivos a: /tmp/rgpd_uploads/")
    print("   - El workflow los procesará automáticamente")
    print("   - Los resultados aparecerán en: /tmp/rgpd_results/")
    
    print("\n3️⃣ INTEGRAR CON FASTAPI:")
    print("   - Modifica tu endpoint para guardar archivos en /tmp/rgpd_uploads/")
    print("   - El file watcher los procesará automáticamente")
    
    print("\n4️⃣ MONITOREAR:")
    print("   - Logs de n8n: Ver ejecuciones en la UI")
    print("   - Archivos procesados se eliminan automáticamente")
    print("   - Resultados se guardan como JSON")
    
    print("\n" + "="*60)

def main():
    print("🔧 Configurando sistema File Watcher para Mistral OCR...")
    
    # Crear directorios
    if not create_directories():
        print("❌ Error configurando directorios")
        sys.exit(1)
    
    # Cargar workflow
    if not create_n8n_workflow():
        print("❌ Error cargando workflow")
        sys.exit(1)
    
    # Crear archivo de prueba
    if not create_test_file():
        print("❌ Error creando archivo de prueba")
        sys.exit(1)
    
    print("\n✅ Configuración completada exitosamente!")
    
    # Mostrar instrucciones
    show_usage_instructions()

if __name__ == "__main__":
    main()