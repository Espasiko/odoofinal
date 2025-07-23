#!/usr/bin/env python3
"""
Script para corregir flujos de n8n identificando y reparando problemas comunes
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any
import shutil
from datetime import datetime

def backup_workflow(file_path: Path) -> Path:
    """Crear backup del workflow antes de modificarlo"""
    backup_dir = file_path.parent / "backups"
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"{file_path.stem}_{timestamp}.json"
    
    shutil.copy2(file_path, backup_path)
    print(f"  📋 Backup creado: {backup_path}")
    return backup_path

def fix_read_pdf_node(node: Dict[str, Any]) -> bool:
    """Corregir nodos readPDF añadiendo parámetros requeridos"""
    if node.get("type") != "n8n-nodes-base.readPDF":
        return False
    
    parameters = node.get("parameters", {})
    fixed = False
    
    # Añadir binaryPropertyName si no existe
    if "binaryPropertyName" not in parameters:
        parameters["binaryPropertyName"] = "data"
        fixed = True
        print(f"    ✅ Añadido binaryPropertyName: 'data'")
    
    # Añadir encrypted si no existe
    if "encrypted" not in parameters:
        parameters["encrypted"] = False
        fixed = True
        print(f"    ✅ Añadido encrypted: false")
    
    # Actualizar parámetros del nodo
    node["parameters"] = parameters
    
    return fixed

def fix_webhook_node(node: Dict[str, Any]) -> bool:
    """Corregir nodos webhook añadiendo configuraciones recomendadas"""
    if node.get("type") != "n8n-nodes-base.webhook":
        return False
    
    parameters = node.get("parameters", {})
    fixed = False
    
    # Asegurar que responseMode esté configurado
    if "responseMode" not in parameters:
        parameters["responseMode"] = "responseNode"
        fixed = True
        print(f"    ✅ Añadido responseMode: 'responseNode'")
    
    # Añadir options si no existe
    if "options" not in parameters:
        parameters["options"] = {}
        fixed = True
        print(f"    ✅ Añadido options: {{}}")
    
    node["parameters"] = parameters
    return fixed

def fix_http_request_node(node: Dict[str, Any]) -> bool:
    """Corregir nodos HTTP Request con configuraciones comunes"""
    if node.get("type") != "n8n-nodes-base.httpRequest":
        return False
    
    parameters = node.get("parameters", {})
    fixed = False
    
    # Añadir timeout por defecto si no existe
    options = parameters.get("options", {})
    if "timeout" not in options:
        options["timeout"] = 30000  # 30 segundos
        parameters["options"] = options
        fixed = True
        print(f"    ✅ Añadido timeout: 30000ms")
    
    node["parameters"] = parameters
    return fixed

def fix_code_node(node: Dict[str, Any]) -> bool:
    """Corregir nodos de código con configuraciones actualizadas"""
    if node.get("type") != "n8n-nodes-base.code":
        return False
    
    # Actualizar typeVersion si es muy antigua
    if node.get("typeVersion", 1) < 2:
        node["typeVersion"] = 2
        print(f"    ✅ Actualizado typeVersion a 2")
        return True
    
    return False

def validate_workflow_structure(workflow: Dict[str, Any]) -> List[str]:
    """Validar la estructura básica del workflow"""
    issues = []
    
    # Verificar campos requeridos
    required_fields = ["name", "nodes"]
    for field in required_fields:
        if field not in workflow:
            issues.append(f"Campo requerido faltante: {field}")
    
    # Verificar que nodes sea una lista
    if "nodes" in workflow and not isinstance(workflow["nodes"], list):
        issues.append("El campo 'nodes' debe ser una lista")
    
    # Verificar que cada nodo tenga campos básicos
    if "nodes" in workflow:
        for i, node in enumerate(workflow["nodes"]):
            if not isinstance(node, dict):
                issues.append(f"Nodo {i} no es un diccionario válido")
                continue
            
            node_required = ["name", "type"]
            for field in node_required:
                if field not in node:
                    issues.append(f"Nodo {i} ({node.get('name', 'sin nombre')}): falta campo '{field}'")
    
    return issues

def fix_workflow_file(file_path: Path) -> bool:
    """Corregir un archivo de workflow específico"""
    print(f"\n🔧 Procesando: {file_path.name}")
    
    try:
        # Leer el archivo JSON
        with open(file_path, 'r', encoding='utf-8') as f:
            workflow = json.load(f)
        
        # Validar estructura básica
        issues = validate_workflow_structure(workflow)
        if issues:
            print(f"  ❌ Problemas estructurales encontrados:")
            for issue in issues:
                print(f"    - {issue}")
            return False
        
        # Crear backup antes de modificar
        backup_path = backup_workflow(file_path)
        
        # Contadores de correcciones
        total_fixes = 0
        nodes_fixed = 0
        
        # Procesar cada nodo
        if "nodes" in workflow:
            for node in workflow["nodes"]:
                node_name = node.get("name", "sin nombre")
                node_type = node.get("type", "desconocido")
                
                print(f"  🔍 Revisando nodo: {node_name} ({node_type})")
                
                node_fixed = False
                
                # Aplicar correcciones específicas por tipo de nodo
                if fix_read_pdf_node(node):
                    node_fixed = True
                    total_fixes += 1
                
                if fix_webhook_node(node):
                    node_fixed = True
                    total_fixes += 1
                
                if fix_http_request_node(node):
                    node_fixed = True
                    total_fixes += 1
                
                if fix_code_node(node):
                    node_fixed = True
                    total_fixes += 1
                
                if node_fixed:
                    nodes_fixed += 1
        
        # Guardar el archivo corregido si hubo cambios
        if total_fixes > 0:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(workflow, f, indent=2, ensure_ascii=False)
            
            print(f"  ✅ Archivo corregido: {total_fixes} correcciones en {nodes_fixed} nodos")
            return True
        else:
            print(f"  ℹ️ No se encontraron problemas que corregir")
            # Eliminar backup si no hubo cambios
            backup_path.unlink()
            return False
    
    except json.JSONDecodeError as e:
        print(f"  ❌ Error JSON: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Error inesperado: {e}")
        return False

def main():
    """Función principal"""
    print("🛠️ Iniciando corrección de flujos de n8n")
    print("=" * 50)
    
    # Directorio de flujos
    flows_dir = Path("/home/espasiko/mainmanusodoo/manusodoo-roto/n8n/flujos")
    
    if not flows_dir.exists():
        print(f"❌ Directorio no encontrado: {flows_dir}")
        sys.exit(1)
    
    # Buscar archivos JSON
    json_files = list(flows_dir.glob("*.json"))
    
    if not json_files:
        print(f"❌ No se encontraron archivos JSON en: {flows_dir}")
        sys.exit(1)
    
    print(f"📁 Encontrados {len(json_files)} archivos JSON")
    
    # Procesar cada archivo
    fixed_count = 0
    error_count = 0
    
    for json_file in json_files:
        try:
            if fix_workflow_file(json_file):
                fixed_count += 1
        except Exception as e:
            print(f"❌ Error procesando {json_file.name}: {e}")
            error_count += 1
    
    # Resumen final
    print("\n" + "=" * 50)
    print("📊 Resumen de correcciones:")
    print(f"  📄 Archivos procesados: {len(json_files)}")
    print(f"  ✅ Archivos corregidos: {fixed_count}")
    print(f"  ❌ Archivos con errores: {error_count}")
    print(f"  ℹ️ Archivos sin cambios: {len(json_files) - fixed_count - error_count}")
    
    if fixed_count > 0:
        print(f"\n🎉 Se corrigieron {fixed_count} flujos de trabajo")
        print("💡 Los backups se guardaron en la carpeta 'backups'")
    
    print("\n🏁 Proceso completado")

if __name__ == "__main__":
    main()
