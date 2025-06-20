# Crear un script de diagnóstico para descubrir los valores válidos
script_diagnostico = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de DIAGNÓSTICO - Descubrir valores válidos para product.template.type
"""

import xmlrpc.client
import sys

# Configuración de conexión a Odoo
ODOO_URL = 'http://localhost:8069'
ODOO_DB = 'manus_odoo-bd'
ODOO_USERNAME = 'yo@mail.com'
ODOO_PASSWORD = 'admin'

def conectar_odoo():
    """Establece conexión con Odoo"""
    try:
        print("Conectando a Odoo para diagnóstico...")
        common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
        uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})
        
        if not uid:
            raise Exception("Error de autenticación")
            
        models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
        print(f"✓ Conectado (UID: {uid})")
        return models, uid
    except Exception as e:
        print(f"✗ Error: {e}")
        return None, None

def diagnosticar_campo_type(models, uid):
    """Descubre qué valores son válidos para el campo 'type'"""
    try:
        print("\\n=== DIAGNÓSTICO DEL CAMPO 'type' ===")
        
        # Método 1: Obtener información del campo
        try:
            field_info = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                'product.template', 'fields_get', 
                [['type']]
            )
            
            if 'type' in field_info:
                print("Información del campo 'type':")
                print(f"  Tipo: {field_info['type'].get('type', 'N/A')}")
                print(f"  Requerido: {field_info['type'].get('required', 'N/A')}")
                print(f"  Ayuda: {field_info['type'].get('help', 'N/A')}")
                
                # Buscar opciones de selección
                if 'selection' in field_info['type']:
                    print("  ✓ VALORES VÁLIDOS ENCONTRADOS:")
                    for valor, etiqueta in field_info['type']['selection']:
                        print(f"    - '{valor}' → {etiqueta}")
                else:
                    print("  ⚠ No se encontraron opciones de selección")
            else:
                print("  ✗ Campo 'type' no encontrado")
                
        except Exception as e:
            print(f"  ✗ Error obteniendo info del campo: {e}")
        
        # Método 2: Buscar productos existentes y ver qué tipos usan
        try:
            print("\\n=== TIPOS USADOS EN PRODUCTOS EXISTENTES ===")
            productos_existentes = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                'product.template', 'search_read',
                [[]],
                {'fields': ['name', 'type'], 'limit': 10}
            )
            
            tipos_encontrados = set()
            for producto in productos_existentes:
                tipos_encontrados.add(producto['type'])
                print(f"  Producto: {producto['name'][:30]}... → type: '{producto['type']}'")
            
            print(f"\\n  ✓ TIPOS ENCONTRADOS EN USO:")
            for tipo in sorted(tipos_encontrados):
                print(f"    - '{tipo}'")
                
        except Exception as e:
            print(f"  ✗ Error consultando productos: {e}")
        
        # Método 3: Intentar crear un producto de prueba con diferentes tipos
        print("\\n=== PRUEBA DE TIPOS VÁLIDOS ===")
        tipos_a_probar = ['product', 'storable', 'consu', 'service', 'consumable']
        
        for tipo in tipos_a_probar:
            try:
                # Intentar crear un producto temporal
                producto_prueba = {
                    'name': f'PRUEBA_TIPO_{tipo.upper()}',
                    'default_code': f'TEST_{tipo.upper()}',
                    'type': tipo,
                    'list_price': 1.0
                }
                
                producto_id = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                    'product.template', 'create',
                    [producto_prueba]
                )
                
                print(f"  ✓ '{tipo}' → VÁLIDO (ID: {producto_id})")
                
                # Eliminar el producto de prueba
                models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
                    'product.template', 'unlink',
                    [producto_id]
                )
                
            except Exception as e:
                error_msg = str(e)
                if "Wrong value" in error_msg:
                    print(f"  ✗ '{tipo}' → INVÁLIDO")
                else:
                    print(f"  ⚠ '{tipo}' → Error: {error_msg[:50]}...")
        
    except Exception as e:
        print(f"✗ Error en diagnóstico: {e}")

def main():
    print("=" * 60)
    print("    DIAGNÓSTICO DE VALORES VÁLIDOS PARA 'type'")
    print("=" * 60)
    
    models, uid = conectar_odoo()
    if not models or not uid:
        print("✗ No se pudo conectar a Odoo")
        sys.exit(1)
    
    diagnosticar_campo_type(models, uid)
    
    print("\\n" + "=" * 60)
    print("              DIAGNÓSTICO COMPLETADO")
    print("=" * 60)
    print("Usa los valores marcados como VÁLIDOS en tu CSV")

if __name__ == '__main__':
    main()
'''

# Guardar el script de diagnóstico
with open('diagnostico_type_odoo.py', 'w', encoding='utf-8') as f:
    f.write(script_diagnostico)

print("✓ Script de diagnóstico creado: diagnostico_type_odoo.py")
print("\n=== INSTRUCCIONES ===")
print("1. Copia el script a tu servidor:")
print("   cp diagnostico_type_odoo.py /home/espasiko/mainmanusodoo/manusodoo-roto/odoo_import/")
print("\n2. Ejecuta el diagnóstico:")
print("   cd /home/espasiko/mainmanusodoo/manusodoo-roto/odoo_import/")
print("   python3 diagnostico_type_odoo.py")
print("\n3. El script te dirá EXACTAMENTE qué valores acepta tu Odoo")
print("4. Luego actualizaremos el CSV y script con los valores correctos")