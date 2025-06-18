#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import xmlrpc.client
import sys

# Configuración de conexión a Odoo
ODOO_URL = 'http://localhost:8069'
ODOO_DB = 'manus_odoo-bd'
ODOO_USERNAME = 'yo@mail.com'
ODOO_PASSWORD = 'admin'

def verificar_configuracion_odoo():
    try:
        print("=== VERIFICACIÓN DE CONFIGURACIÓN ODOO 18 ===")
        print(f"URL: {ODOO_URL}")
        print(f"Base de datos: {ODOO_DB}")
        print(f"Usuario: {ODOO_USERNAME}")
        print("\n" + "="*50)
        
        # Conectar a Odoo
        common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
        uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})
        
        if not uid:
            print("❌ ERROR: No se pudo autenticar con Odoo")
            return False
            
        print(f"✅ Conexión exitosa. UID: {uid}")
        
        models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
        
        # 1. Verificar módulos instalados relacionados con inventario
        print("\n1. MÓDULOS INSTALADOS RELACIONADOS CON INVENTARIO:")
        modulos_inventario = ['stock', 'sale_stock', 'purchase_stock', 'website_sale_stock']
        
        for modulo in modulos_inventario:
            try:
                modulo_info = models.execute_kw(
                    ODOO_DB, uid, ODOO_PASSWORD,
                    'ir.module.module', 'search_read',
                    [[('name', '=', modulo)]],
                    {'fields': ['name', 'state', 'summary']}
                )
                if modulo_info:
                    estado = modulo_info[0]['state']
                    resumen = modulo_info[0].get('summary', 'Sin descripción')
                    print(f"  - {modulo}: {estado} - {resumen}")
                else:
                    print(f"  - {modulo}: No encontrado")
            except Exception as e:
                print(f"  - {modulo}: Error al verificar - {e}")
        
        # 2. Verificar campos del modelo product.template
        print("\n2. INFORMACIÓN DEL CAMPO 'type' EN product.template:")
        try:
            # Obtener información del campo type
            field_info = models.execute_kw(
                ODOO_DB, uid, ODOO_PASSWORD,
                'ir.model.fields', 'search_read',
                [[('model', '=', 'product.template'), ('name', '=', 'type')]],
                {'fields': ['name', 'field_description', 'ttype', 'selection', 'help']}
            )
            
            if field_info:
                campo = field_info[0]
                print(f"  - Nombre: {campo['name']}")
                print(f"  - Descripción: {campo['field_description']}")
                print(f"  - Tipo: {campo['ttype']}")
                print(f"  - Selección: {campo.get('selection', 'No definida')}")
                print(f"  - Ayuda: {campo.get('help', 'Sin ayuda')}")
            else:
                print("  ❌ No se encontró información del campo 'type'")
        except Exception as e:
            print(f"  ❌ Error al obtener información del campo: {e}")
        
        # 3. Verificar productos existentes y sus tipos
        print("\n3. TIPOS DE PRODUCTOS EXISTENTES EN EL SISTEMA:")
        try:
            productos_tipos = models.execute_kw(
                ODOO_DB, uid, ODOO_PASSWORD,
                'product.template', 'read_group',
                [[]],
                {'fields': ['type'], 'groupby': ['type']}
            )
            
            if productos_tipos:
                print("  Tipos encontrados en productos existentes:")
                for grupo in productos_tipos:
                    tipo = grupo['type']
                    count = grupo['type_count']
                    print(f"    - '{tipo}': {count} productos")
            else:
                print("  No se encontraron productos en el sistema")
        except Exception as e:
            print(f"  ❌ Error al obtener tipos de productos: {e}")
        
        # 4. Intentar crear un producto de prueba con tipo 'product'
        print("\n4. PRUEBA DE CREACIÓN DE PRODUCTO CON TIPO 'product':")
        try:
            # Intentar crear un producto de prueba
            producto_test_id = models.execute_kw(
                ODOO_DB, uid, ODOO_PASSWORD,
                'product.template', 'create',
                [{
                    'name': 'PRODUCTO_TEST_VERIFICACION',
                    'type': 'product',
                    'list_price': 1.0,
                    'standard_price': 1.0
                }]
            )
            
            print(f"  ✅ Producto de prueba creado exitosamente con ID: {producto_test_id}")
            
            # Eliminar el producto de prueba
            models.execute_kw(
                ODOO_DB, uid, ODOO_PASSWORD,
                'product.template', 'unlink',
                [producto_test_id]
            )
            print("  ✅ Producto de prueba eliminado")
            
        except Exception as e:
            print(f"  ❌ Error al crear producto con tipo 'product': {e}")
            
            # Intentar con tipo 'consu'
            try:
                producto_test_id = models.execute_kw(
                    ODOO_DB, uid, ODOO_PASSWORD,
                    'product.template', 'create',
                    [{
                        'name': 'PRODUCTO_TEST_VERIFICACION_CONSU',
                        'type': 'consu',
                        'list_price': 1.0,
                        'standard_price': 1.0
                    }]
                )
                
                print(f"  ✅ Producto de prueba con tipo 'consu' creado exitosamente con ID: {producto_test_id}")
                
                # Eliminar el producto de prueba
                models.execute_kw(
                    ODOO_DB, uid, ODOO_PASSWORD,
                    'product.template', 'unlink',
                    [producto_test_id]
                )
                print("  ✅ Producto de prueba 'consu' eliminado")
                
            except Exception as e2:
                print(f"  ❌ Error al crear producto con tipo 'consu': {e2}")
        
        # 5. Verificar configuración de la empresa
        print("\n5. CONFIGURACIÓN DE LA EMPRESA:")
        try:
            empresa_info = models.execute_kw(
                ODOO_DB, uid, ODOO_PASSWORD,
                'res.company', 'search_read',
                [[]],
                {'fields': ['name', 'currency_id'], 'limit': 1}
            )
            
            if empresa_info:
                empresa = empresa_info[0]
                print(f"  - Nombre: {empresa['name']}")
                print(f"  - Moneda: {empresa['currency_id'][1] if empresa['currency_id'] else 'No definida'}")
        except Exception as e:
            print(f"  ❌ Error al obtener información de la empresa: {e}")
        
        print("\n" + "="*50)
        print("✅ VERIFICACIÓN COMPLETADA")
        return True
        
    except Exception as e:
        print(f"❌ ERROR GENERAL: {e}")
        return False

if __name__ == '__main__':
    verificar_configuracion_odoo()
