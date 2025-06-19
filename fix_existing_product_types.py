#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corregir productos existentes marcados como 'consu' a 'storable' (goods)
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

def fix_product_types():
    """Corrige productos marcados como consumibles a productos almacenables"""
    models, uid = conectar_odoo()
    if not models or not uid:
        return
    
    try:
        print("🔍 Buscando productos marcados como consumibles...")
        
        # Buscar productos con type = 'consu'
        product_ids = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
            'product.template', 'search',
            [[['type', '=', 'consu']]]
        )
        
        if not product_ids:
            print("✅ No se encontraron productos marcados como consumibles")
            return
        
        print(f"📦 Encontrados {len(product_ids)} productos marcados como consumibles")
        
        # Obtener nombres de los productos para mostrar
        products = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
            'product.template', 'read',
            [product_ids],
            {'fields': ['name', 'type']}
        )
        
        print("Productos a corregir:")
        for product in products[:10]:  # Mostrar solo los primeros 10
            print(f"  - {product['name']}")
        if len(products) > 10:
            print(f"  ... y {len(products) - 10} más")
        
        # Confirmar acción
        confirm = input(f"\n¿Desea cambiar {len(product_ids)} productos de 'consumible' a 'almacenable' (goods)? (s/N): ")
        if confirm.lower() not in ['s', 'si', 'sí', 'y', 'yes']:
            print("❌ Operación cancelada")
            return
        
        # Actualizar productos
        print("🔄 Actualizando productos...")
        result = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
            'product.template', 'write',
            [product_ids, {'type': 'storable'}]
        )
        
        if result:
            print(f"✅ {len(product_ids)} productos actualizados correctamente")
            print("   Tipo cambiado de 'consu' (consumible) a 'storable' (almacenable/goods)")
        else:
            print("❌ Error actualizando productos")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Función principal"""
    print("=== CORRECCIÓN DE TIPOS DE PRODUCTOS ===")
    print(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    fix_product_types()
    
    print("\n💡 Recomendación:")
    print("   Ejecute check_product_types_fixed.py para verificar los cambios")

if __name__ == '__main__':
    main()
