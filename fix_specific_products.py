#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corregir productos específicos marcados como 'consu' a 'storable'
"""

import xmlrpc.client
from datetime import datetime

# Configuración
ODOO_URL = 'http://localhost:8069'
ODOO_DB = 'manus_odoo-bd'
ODOO_USERNAME = 'yo@mail.com'
ODOO_PASSWORD = 'admin'

# Productos específicos a corregir
PRODUCTOS_A_CORREGIR = [
    "1 SARTEN POLKA 18 (NEGRO MANGO TURQUESA)",
    "CAFETERA 66 DROP&THERMO TIME",
    "colchon blandito",
    "150 PIEZAS DE PAPEL FREIDORA AIRE DE 5 A 6,5L"
]

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

def fix_specific_products():
    """Corrige productos específicos"""
    models, uid = conectar_odoo()
    if not models or not uid:
        return
    
    try:
        print("🔍 Buscando productos específicos para corregir...")
        
        productos_encontrados = []
        productos_no_encontrados = []
        
        for nombre_producto in PRODUCTOS_A_CORREGIR:
            # Buscar el producto por nombre
            product_ids = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                'product.template', 'search',
                [[['name', '=', nombre_producto]]]
            )
            
            if product_ids:
                # Obtener datos del producto
                product_data = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                    'product.template', 'read',
                    [product_ids],
                    {'fields': ['id', 'name', 'type']}
                )
                
                for product in product_data:
                    productos_encontrados.append(product)
                    print(f"✅ Encontrado: {product['name']} (ID: {product['id']}, Tipo: {product['type']})")
            else:
                productos_no_encontrados.append(nombre_producto)
                print(f"❌ No encontrado: {nombre_producto}")
        
        if productos_no_encontrados:
            print(f"\n⚠️  Productos no encontrados: {len(productos_no_encontrados)}")
            for producto in productos_no_encontrados:
                print(f"  - {producto}")
        
        if not productos_encontrados:
            print("❌ No se encontraron productos para corregir")
            return
        
        # Filtrar solo los que tienen tipo 'consu'
        productos_consu = [p for p in productos_encontrados if p['type'] == 'consu']
        
        if not productos_consu:
            print("✅ Todos los productos ya tienen el tipo correcto")
            return
        
        print(f"\n📦 Productos a corregir (tipo 'consu'): {len(productos_consu)}")
        for product in productos_consu:
            print(f"  - {product['name']} (ID: {product['id']})")
        
        # Actualizar productos de 'consu' a 'storable'
        product_ids_to_update = [p['id'] for p in productos_consu]
        
        print(f"\n🔄 Actualizando {len(product_ids_to_update)} productos de 'consu' a 'storable'...")
        
        # Actualizar uno por uno para mejor control
        actualizados = 0
        errores = 0
        
        for product_id in product_ids_to_update:
            try:
                result = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                    'product.template', 'write',
                    [[product_id], {'type': 'storable'}]
                )
                
                if result:
                    actualizados += 1
                    product_name = next(p['name'] for p in productos_consu if p['id'] == product_id)
                    print(f"  ✅ {product_name}")
                else:
                    errores += 1
                    print(f"  ❌ Error actualizando producto ID {product_id}")
                    
            except Exception as e:
                errores += 1
                print(f"  ❌ Error actualizando producto ID {product_id}: {e}")
        
        print(f"\n=== RESUMEN ===")
        print(f"✅ Productos actualizados: {actualizados}")
        print(f"❌ Errores: {errores}")
        
        if actualizados > 0:
            print(f"🎉 {actualizados} productos cambiados de 'consu' a 'storable' correctamente")
            
    except Exception as e:
        print(f"❌ Error general: {e}")

def main():
    """Función principal"""
    print("=== CORRECCIÓN DE PRODUCTOS ESPECÍFICOS ===")
    print(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    fix_specific_products()

if __name__ == '__main__':
    main()
