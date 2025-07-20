#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para verificar la compatibilidad entre Odoo 18 y n8n

Este script verifica:
1. La conexión con Odoo 18
2. La compatibilidad de los endpoints de la API de Odoo 18 con n8n
3. La estructura de datos esperada por n8n para crear facturas en Odoo 18

Autor: Equipo Pelotazo ERP
Fecha: 19/07/2025
"""

import os
import sys
import json
import requests
import xmlrpc.client
from urllib.parse import urlparse
import logging
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Configuración de Odoo
ODOO_URL = os.getenv("ODOO_URL", "http://odoo:8069")
ODOO_DB = os.getenv("ODOO_DB", "odoo")
ODOO_USERNAME = os.getenv("ODOO_USERNAME", "admin")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "admin")

# Configuración de n8n
N8N_URL = os.getenv("N8N_BASE_URL", "http://localhost:5678")
N8N_API_KEY = os.getenv("N8N_API_KEY", "pelotazo-n8n-api-token-seguro-2025")

# Colores para terminal
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
ENDC = '\033[0m'

def print_success(message):
    """Imprimir mensaje de éxito"""
    print(f"{GREEN}✓ {message}{ENDC}")

def print_warning(message):
    """Imprimir mensaje de advertencia"""
    print(f"{YELLOW}! {message}{ENDC}")

def print_error(message):
    """Imprimir mensaje de error"""
    print(f"{RED}✗ {message}{ENDC}")

def print_info(message):
    """Imprimir mensaje informativo"""
    print(f"{BLUE}ℹ {message}{ENDC}")

def check_odoo_connection():
    """Verificar la conexión con Odoo 18"""
    print_info("Verificando conexión con Odoo 18...")
    
    try:
        # Parsear URL de Odoo
        parsed_url = urlparse(ODOO_URL)
        server_url = f"{parsed_url.scheme}://{parsed_url.netloc}/xmlrpc/2/common"
        
        # Intentar conectar con Odoo
        common = xmlrpc.client.ServerProxy(server_url)
        version = common.version()
        
        if version:
            print_success(f"Conexión exitosa con Odoo: {version.get('server_version', 'Versión desconocida')}")
            
            # Verificar si es Odoo 18
            if version.get('server_version', '').startswith('18'):
                print_success("Versión de Odoo confirmada: Odoo 18")
            else:
                print_warning(f"Versión de Odoo detectada ({version.get('server_version', 'Desconocida')}) no es Odoo 18")
            
            return True, version
        else:
            print_error("No se pudo obtener la versión de Odoo")
            return False, None
    
    except Exception as e:
        print_error(f"Error al conectar con Odoo: {str(e)}")
        return False, None

def check_odoo_authentication():
    """Verificar la autenticación con Odoo 18"""
    print_info("Verificando autenticación con Odoo 18...")
    
    try:
        # Parsear URL de Odoo
        parsed_url = urlparse(ODOO_URL)
        common_url = f"{parsed_url.scheme}://{parsed_url.netloc}/xmlrpc/2/common"
        
        # Intentar autenticarse con Odoo
        common = xmlrpc.client.ServerProxy(common_url)
        uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})
        
        if uid:
            print_success(f"Autenticación exitosa con Odoo (UID: {uid})")
            return True, uid
        else:
            print_error("Autenticación fallida con Odoo")
            return False, None
    
    except Exception as e:
        print_error(f"Error al autenticarse con Odoo: {str(e)}")
        return False, None

def check_odoo_api_endpoints(uid):
    """Verificar los endpoints de la API de Odoo 18 necesarios para n8n"""
    print_info("Verificando endpoints de la API de Odoo 18...")
    
    # Endpoints a verificar
    endpoints = [
        {"model": "res.partner", "method": "search_read", "description": "Búsqueda de proveedores"},
        {"model": "account.move", "method": "create", "description": "Creación de facturas"},
        {"model": "account.move.line", "method": "create", "description": "Creación de líneas de factura"},
        {"model": "product.product", "method": "search_read", "description": "Búsqueda de productos"}
    ]
    
    try:
        # Parsear URL de Odoo
        parsed_url = urlparse(ODOO_URL)
        models_url = f"{parsed_url.scheme}://{parsed_url.netloc}/xmlrpc/2/object"
        models = xmlrpc.client.ServerProxy(models_url)
        
        all_success = True
        
        for endpoint in endpoints:
            try:
                # Verificar acceso al modelo
                has_access = models.execute_kw(
                    ODOO_DB, uid, ODOO_PASSWORD,
                    endpoint["model"], 'check_access_rights',
                    [endpoint["method"]], {'raise_exception': False}
                )
                
                if has_access:
                    print_success(f"Acceso confirmado a {endpoint['model']}.{endpoint['method']} ({endpoint['description']})")
                else:
                    print_warning(f"Sin acceso a {endpoint['model']}.{endpoint['method']} ({endpoint['description']})")
                    all_success = False
            
            except Exception as e:
                print_error(f"Error al verificar {endpoint['model']}.{endpoint['method']}: {str(e)}")
                all_success = False
        
        return all_success
    
    except Exception as e:
        print_error(f"Error al verificar endpoints de la API: {str(e)}")
        return False

def check_odoo_fields_structure():
    """Verificar la estructura de campos de Odoo 18 necesarios para n8n"""
    print_info("Verificando estructura de campos de Odoo 18...")
    
    try:
        # Parsear URL de Odoo
        parsed_url = urlparse(ODOO_URL)
        common_url = f"{parsed_url.scheme}://{parsed_url.netloc}/xmlrpc/2/common"
        models_url = f"{parsed_url.scheme}://{parsed_url.netloc}/xmlrpc/2/object"
        
        # Autenticarse con Odoo
        common = xmlrpc.client.ServerProxy(common_url)
        uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})
        
        if not uid:
            print_error("No se pudo autenticar con Odoo")
            return False
        
        # Conectar con el modelo de Odoo
        models = xmlrpc.client.ServerProxy(models_url)
        
        # Modelos a verificar
        model_fields = [
            {"model": "account.move", "description": "Facturas"},
            {"model": "account.move.line", "description": "Líneas de factura"},
            {"model": "res.partner", "description": "Proveedores"},
            {"model": "product.product", "description": "Productos"}
        ]
        
        all_success = True
        
        for model_info in model_fields:
            try:
                # Obtener campos del modelo
                fields = models.execute_kw(
                    ODOO_DB, uid, ODOO_PASSWORD,
                    model_info["model"], 'fields_get',
                    [], {'attributes': ['string', 'type', 'required']}
                )
                
                if fields:
                    print_success(f"Estructura de {model_info['description']} ({model_info['model']}) verificada: {len(fields)} campos")
                    
                    # Guardar estructura para referencia
                    with open(f"odoo18_{model_info['model'].replace('.', '_')}_fields.json", "w") as f:
                        json.dump(fields, f, indent=2)
                    
                    print_info(f"Estructura guardada en odoo18_{model_info['model'].replace('.', '_')}_fields.json")
                else:
                    print_warning(f"No se pudieron obtener los campos de {model_info['model']}")
                    all_success = False
            
            except Exception as e:
                print_error(f"Error al verificar estructura de {model_info['model']}: {str(e)}")
                all_success = False
        
        return all_success
    
    except Exception as e:
        print_error(f"Error al verificar estructura de campos: {str(e)}")
        return False

def check_n8n_odoo_nodes():
    """Verificar si n8n tiene los nodos necesarios para Odoo 18"""
    print_info("Verificando nodos de Odoo en n8n...")
    
    try:
        # Verificar si n8n está disponible
        response = requests.get(
            f"{N8N_URL}/api/v1/nodes",
            headers={"Authorization": f"Bearer {N8N_API_KEY}"},
            timeout=5
        )
        
        if response.status_code == 200:
            nodes = response.json()
            
            # Buscar nodos de Odoo
            odoo_nodes = [node for node in nodes if "odoo" in node.get("name", "").lower()]
            
            if odoo_nodes:
                print_success(f"n8n tiene {len(odoo_nodes)} nodos relacionados con Odoo")
                
                for node in odoo_nodes:
                    print_info(f"Nodo: {node.get('name')} - {node.get('displayName')}")
                
                return True
            else:
                print_warning("n8n no tiene nodos específicos para Odoo")
                print_info("Puedes usar el nodo HTTP Request para conectar con la API de Odoo")
                return False
        else:
            print_error(f"Error al obtener nodos de n8n: {response.status_code}")
            return False
    
    except Exception as e:
        print_error(f"Error al verificar nodos de n8n: {str(e)}")
        return False

def check_odoo_version_compatibility():
    """Verificar compatibilidad de versiones entre Odoo 18 y n8n"""
    print_info("Verificando compatibilidad de versiones entre Odoo 18 y n8n...")
    
    # Verificar conexión con Odoo
    connection_success, version = check_odoo_connection()
    
    if not connection_success:
        return False
    
    # Verificar autenticación con Odoo
    auth_success, uid = check_odoo_authentication()
    
    if not auth_success:
        return False
    
    # Verificar endpoints de la API
    endpoints_success = check_odoo_api_endpoints(uid)
    
    # Verificar estructura de campos
    fields_success = check_odoo_fields_structure()
    
    # Verificar nodos de Odoo en n8n
    nodes_success = check_n8n_odoo_nodes()
    
    # Resultado final
    if endpoints_success and fields_success:
        print_success("Odoo 18 es compatible con n8n")
        
        if not nodes_success:
            print_warning("No se encontraron nodos específicos para Odoo en n8n")
            print_info("Recomendación: Usar el nodo HTTP Request para conectar con la API de Odoo")
        
        return True
    else:
        print_warning("Hay problemas de compatibilidad entre Odoo 18 y n8n")
        print_info("Revisa los mensajes anteriores para más detalles")
        return False

if __name__ == "__main__":
    print("\n=== Verificación de Compatibilidad Odoo 18 - n8n ===\n")
    check_odoo_version_compatibility()
    print("\n=== Verificación Completada ===\n")
