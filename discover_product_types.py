#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para descubrir los tipos de producto válidos en Odoo
"""

import xmlrpc.client
from datetime import datetime

# Configuración
ODOO_URL = 'http://localhost:8069'
ODOO_DB = 'manus_odoo-bd'
ODOO_USERNAME = 'yo@mail.com'
ODOO_PASSWORD = 'admin'

def conectar_odoo():
    """Establece conexión con Odoo"""
    try:
        common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
        uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})
        
        if not uid:
            raise Exception("Error de autenticación")
            
        models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
        return models, uid
    except Exception as e:
        print(f"Error conectando a Odoo: {e}")
        return None, None

def discover_product_types():
    """Descubre los tipos de producto válidos"""
    models, uid = conectar_odoo()
    if not models or not uid:
        return
    
    try:
        print("🔍 Descubriendo tipos de producto válidos...")
        
        # Obtener información del campo 'type' del modelo product.template
        field_info = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
            'product.template', 'fields_get',
            [['type']]
        )
        
        if 'type' in field_info:
            type_field = field_info['type']
            print(f"📋 Campo 'type' información:")
            print(f"  - Tipo: {type_field.get('type', 'N/A')}")
            print(f"  - Descripción: {type_field.get('string', 'N/A')}")
            
            if 'selection' in type_field:
                print(f"  - Valores válidos:")
                for value, label in type_field['selection']:
                    print(f"    * '{value}' = {label}")
        
        # También obtener algunos productos existentes para ver qué tipos usan
        print(f"\n📦 Tipos de producto en uso actualmente:")
        
        # Obtener productos existentes con sus tipos
        product_ids = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
            'product.template', 'search',
            [[]],
            {'limit': 20}
        )
        
        if product_ids:
            products = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                'product.template', 'read',
                [product_ids],
                {'fields': ['name', 'type']}
            )
            
            # Contar tipos únicos
            type_counts = {}
            for product in products:
                ptype = product['type']
                if ptype in type_counts:
                    type_counts[ptype] += 1
                else:
                    type_counts[ptype] = 1
            
            for ptype, count in type_counts.items():
                print(f"  - '{ptype}': {count} productos")
                
                # Mostrar un ejemplo de cada tipo
                example = next((p for p in products if p['type'] == ptype), None)
                if example:
                    print(f"    Ejemplo: {example['name']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Función principal"""
    print("=== DESCUBRIMIENTO DE TIPOS DE PRODUCTO ===")
    print(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    discover_product_types()

if __name__ == '__main__':
    main()
