#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar tipos de productos con el campo correcto para Odoo 18
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

def check_product_types():
    """Verifica los tipos de productos importados usando el campo correcto"""
    models, uid = conectar_odoo()
    if not models or not uid:
        return
    
    try:
        print("📦 Verificando tipos de productos (usando campo 'type')...")
        
        # Contar productos por tipo usando el campo correcto 'type'
        for product_type, description in [('product', 'Goods/Productos'), ('consu', 'Consumibles'), ('service', 'Servicios')]:
            count = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                'product.template', 'search_count',
                [[['type', '=', product_type]]]
            )
            print(f"  - {description}: {count} productos")
        
        # Buscar productos CECOTEC específicamente
        cecotec_products = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
            'product.template', 'search_count',
            [[['name', 'ilike', 'CECOTEC']]]
        )
        print(f"  - Productos CECOTEC: {cecotec_products}")
        
        # Mostrar algunos productos CECOTEC como ejemplo
        if cecotec_products > 0:
            cecotec_ids = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                'product.template', 'search',
                [[['name', 'ilike', 'CECOTEC']]],
                {'limit': 5}
            )
            
            cecotec_data = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                'product.template', 'read',
                [cecotec_ids],
                {'fields': ['name', 'type', 'list_price']}
            )
            
            print(f"\n📋 Ejemplos de productos CECOTEC:")
            for product in cecotec_data:
                tipo_es = {'product': 'Producto', 'consu': 'Consumible', 'service': 'Servicio'}.get(product['type'], product['type'])
                print(f"  - {product['name']} | Tipo: {tipo_es} | Precio: {product['list_price']}€")
        
        # Verificar productos marcados incorrectamente como consumibles
        consu_count = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
            'product.template', 'search_count',
            [[['type', '=', 'consu']]]
        )
        
        if consu_count > 0:
            print(f"\n⚠️  ALERTA: Hay {consu_count} productos marcados como consumibles")
            print("   Considere ejecutar el script de corrección si estos deberían ser productos")
        else:
            print(f"\n✅ No hay productos marcados incorrectamente como consumibles")
            
    except Exception as e:
        print(f"❌ Error verificando productos: {e}")

def main():
    """Función principal"""
    print("=== VERIFICACIÓN DE TIPOS DE PRODUCTOS ===")
    print(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    check_product_types()

if __name__ == '__main__':
    main()
