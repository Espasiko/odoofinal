#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar el significado real de los tipos de producto
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

def verify_product_meanings():
    """Verifica el significado real de los tipos de producto"""
    models, uid = conectar_odoo()
    if not models or not uid:
        return
    
    try:
        print("🔍 Verificando significado de tipos de producto...")
        
        # Obtener información del campo 'type'
        field_info = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
            'product.template', 'fields_get',
            [['type']]
        )
        
        print("📋 Tipos de producto válidos y sus significados:")
        if 'type' in field_info and 'selection' in field_info['type']:
            for value, label in field_info['type']['selection']:
                print(f"  - '{value}' = {label}")
        
        print(f"\n📦 Análisis de productos actuales:")
        
        # Obtener todos los productos y sus tipos
        product_ids = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
            'product.template', 'search',
            [[]],
            {'limit': 50}
        )
        
        if product_ids:
            products = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                'product.template', 'read',
                [product_ids],
                {'fields': ['name', 'type']}
            )
            
            # Agrupar por tipo
            by_type = {}
            for product in products:
                ptype = product['type']
                if ptype not in by_type:
                    by_type[ptype] = []
                by_type[ptype].append(product['name'])
            
            for ptype, names in by_type.items():
                print(f"\n🏷️  Tipo '{ptype}' ({len(names)} productos):")
                for name in names[:5]:  # Mostrar solo los primeros 5
                    print(f"    - {name}")
                if len(names) > 5:
                    print(f"    ... y {len(names) - 5} más")
        
        # Verificar productos específicos mencionados por el usuario
        productos_usuario = [
            "1 SARTEN POLKA 18 (NEGRO MANGO TURQUESA)",
            "CAFETERA 66 DROP&THERMO TIME",
            "colchon blandito",
            "150 PIEZAS DE PAPEL FREIDORA AIRE DE 5 A 6,5L"
        ]
        
        print(f"\n🎯 Verificando productos específicos mencionados:")
        for nombre in productos_usuario:
            product_ids = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                'product.template', 'search',
                [[['name', '=', nombre]]]
            )
            
            if product_ids:
                product_data = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                    'product.template', 'read',
                    [product_ids],
                    {'fields': ['name', 'type']}
                )
                
                for product in product_data:
                    tipo_significado = {
                        'consu': 'Goods (Productos físicos)',
                        'service': 'Service (Servicios)',
                        'combo': 'Combo',
                        'storable': 'Storable (Personalizado)'
                    }.get(product['type'], product['type'])
                    
                    print(f"  ✅ {product['name']}")
                    print(f"      Tipo actual: '{product['type']}' = {tipo_significado}")
            else:
                print(f"  ❌ No encontrado: {nombre}")
        
        print(f"\n💡 CONCLUSIÓN:")
        print(f"En tu sistema Odoo:")
        print(f"  - 'consu' = Goods (productos físicos) ✅")
        print(f"  - 'service' = Services (servicios)")
        print(f"  - 'combo' = Combo products")
        print(f"  - 'storable' = Tipo personalizado (usado por productos CECOTEC)")
        print(f"\nSi los productos están marcados como 'consu', ¡están CORRECTOS!")
        print(f"'consu' significa 'Goods' (productos físicos), no 'consumibles'.")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Función principal"""
    print("=== VERIFICACIÓN DE SIGNIFICADOS DE TIPOS DE PRODUCTO ===")
    print(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    verify_product_meanings()

if __name__ == '__main__':
    main()
