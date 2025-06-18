#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import xmlrpc.client
import sys

# Configuración de conexión a Odoo
ODOO_URL = 'http://localhost:8069'
ODOO_DB = 'manus_odoo-bd'
ODOO_USERNAME = 'yo@mail.com'
ODOO_PASSWORD = 'admin'

def verificar_selection_type():
    try:
        print("=== VERIFICACIÓN DETALLADA DEL CAMPO TYPE ===")
        
        # Conectar a Odoo
        common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
        uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})
        
        if not uid:
            print("❌ ERROR: No se pudo autenticar con Odoo")
            return False
            
        models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
        
        # Método 1: Obtener información del campo desde ir.model.fields
        print("\n1. INFORMACIÓN DEL CAMPO DESDE ir.model.fields:")
        try:
            field_info = models.execute_kw(
                ODOO_DB, uid, ODOO_PASSWORD,
                'ir.model.fields', 'search_read',
                [[('model', '=', 'product.template'), ('name', '=', 'type')]],
                {'fields': ['name', 'field_description', 'ttype', 'selection', 'help']}
            )
            
            if field_info:
                campo = field_info[0]
                print(f"  - Selección definida: {campo.get('selection', 'No definida')}")
            else:
                print("  ❌ No se encontró el campo")
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        # Método 2: Usar fields_get para obtener información detallada
        print("\n2. INFORMACIÓN DEL CAMPO USANDO fields_get:")
        try:
            fields_info = models.execute_kw(
                ODOO_DB, uid, ODOO_PASSWORD,
                'product.template', 'fields_get',
                [['type']],
                {'attributes': ['string', 'help', 'type', 'selection', 'required']}
            )
            
            if 'type' in fields_info:
                type_field = fields_info['type']
                print(f"  - Tipo de campo: {type_field.get('type', 'No definido')}")
                print(f"  - Etiqueta: {type_field.get('string', 'No definida')}")
                print(f"  - Requerido: {type_field.get('required', False)}")
                print(f"  - Ayuda: {type_field.get('help', 'Sin ayuda')}")
                
                selection = type_field.get('selection', [])
                if selection:
                    print("  - Valores de selección válidos:")
                    for value, label in selection:
                        print(f"    * '{value}': {label}")
                else:
                    print("  - No se encontraron valores de selección")
            else:
                print("  ❌ No se encontró información del campo type")
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        # Método 3: Verificar directamente en el modelo
        print("\n3. VERIFICACIÓN DIRECTA EN EL MODELO:")
        try:
            # Intentar obtener un producto existente para ver su estructura
            productos = models.execute_kw(
                ODOO_DB, uid, ODOO_PASSWORD,
                'product.template', 'search_read',
                [[]],
                {'fields': ['name', 'type'], 'limit': 5}
            )
            
            if productos:
                print("  - Productos existentes y sus tipos:")
                for producto in productos:
                    print(f"    * {producto['name']}: tipo '{producto['type']}'")
            else:
                print("  - No hay productos en el sistema")
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        # Método 4: Verificar módulos que podrían afectar el campo
        print("\n4. MÓDULOS QUE PODRÍAN AFECTAR EL CAMPO TYPE:")
        try:
            modulos_relevantes = models.execute_kw(
                ODOO_DB, uid, ODOO_PASSWORD,
                'ir.module.module', 'search_read',
                [[('state', '=', 'installed'), ('name', 'ilike', 'product')]],
                {'fields': ['name', 'summary', 'state']}
            )
            
            if modulos_relevantes:
                print("  - Módulos instalados relacionados con productos:")
                for modulo in modulos_relevantes:
                    print(f"    * {modulo['name']}: {modulo.get('summary', 'Sin descripción')}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        # Método 5: Verificar herencias del modelo
        print("\n5. HERENCIAS DEL MODELO product.template:")
        try:
            model_info = models.execute_kw(
                ODOO_DB, uid, ODOO_PASSWORD,
                'ir.model', 'search_read',
                [[('model', '=', 'product.template')]],
                {'fields': ['name', 'model', 'info']}
            )
            
            if model_info:
                print(f"  - Información del modelo: {model_info[0].get('info', 'Sin información')}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        print("\n" + "="*50)
        print("✅ VERIFICACIÓN DETALLADA COMPLETADA")
        return True
        
    except Exception as e:
        print(f"❌ ERROR GENERAL: {e}")
        return False

if __name__ == '__main__':
    verificar_selection_type()
