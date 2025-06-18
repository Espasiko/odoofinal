#!/usr/bin/env python3
import xmlrpc.client

# Configuración de conexión
url = 'http://localhost:8069'
db = 'manus_odoo-bd'
username = 'yo@mail.com'
password = 'admin'

try:
    # Autenticación
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
    uid = common.authenticate(db, username, password, {})
    
    if not uid:
        print("Error de autenticación")
        exit(1)
    
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
    
    # Verificar módulos instalados
    print("=== MÓDULOS INSTALADOS ===")
    modules = models.execute_kw(db, uid, password, 'ir.module.module', 'search_read', 
                               [[('state', '=', 'installed'), 
                                ('name', 'in', ['stock', 'inventory', 'sale', 'purchase', 'website_sale'])]], 
                               {'fields': ['name', 'state']})
    
    for module in modules:
        print(f"- {module['name']}: {module['state']}")
    
    # Verificar campo type en product.template
    print("\n=== CAMPO TYPE EN PRODUCT.TEMPLATE ===")
    field_info = models.execute_kw(db, uid, password, 'product.template', 'fields_get', 
                                  [[]], {'attributes': ['type']})
    
    type_field = field_info.get('type', {})
    selection = type_field.get('selection', [])
    
    print(f"Tipo de campo: {type_field.get('type', 'N/A')}")
    print("Valores válidos:")
    for value, label in selection:
        print(f"  - '{value}': {label}")
    
    # Verificar productos existentes y sus tipos
    print("\n=== PRODUCTOS EXISTENTES Y SUS TIPOS ===")
    products = models.execute_kw(db, uid, password, 'product.template', 'search_read', 
                                [[]], {'fields': ['name', 'type'], 'limit': 10})
    
    for product in products:
        print(f"- {product['name']}: tipo '{product['type']}'")
        
except Exception as e:
    print(f"Error: {e}")