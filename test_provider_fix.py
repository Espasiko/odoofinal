#!/usr/bin/env python3
"""
Script de prueba para verificar la funcionalidad de find_or_create_provider
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

from api.services.odoo_provider_service import odoo_provider_service
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_find_or_create_provider():
    """
    Prueba la funcionalidad de find_or_create_provider
    """
    print("=== PRUEBA DE FIND_OR_CREATE_PROVIDER ===")
    
    # Caso 1: Proveedor que probablemente no existe
    test_provider_name = "Proveedor Test Excel Import 2025"
    
    print(f"\n1. Probando con proveedor: '{test_provider_name}'")
    result = odoo_provider_service.find_or_create_provider(test_provider_name)
    
    if result:
        print(f"   ✅ Resultado: {result}")
        print(f"   - ID: {result['id']}")
        print(f"   - Nombre: {result['name']}")
        print(f"   - Acción: {result['action']}")
    else:
        print("   ❌ Error: No se pudo encontrar ni crear el proveedor")
    
    # Caso 2: Intentar encontrar el mismo proveedor (debería encontrarlo ahora)
    print(f"\n2. Probando nuevamente con el mismo proveedor: '{test_provider_name}'")
    result2 = odoo_provider_service.find_or_create_provider(test_provider_name)
    
    if result2:
        print(f"   ✅ Resultado: {result2}")
        print(f"   - ID: {result2['id']}")
        print(f"   - Nombre: {result2['name']}")
        print(f"   - Acción: {result2['action']}")
        
        if result and result2['action'] == 'found' and result2['id'] == result['id']:
            print("   ✅ Correcto: El proveedor se encontró en la segunda búsqueda")
        else:
            print("   ⚠️  Advertencia: Comportamiento inesperado en la segunda búsqueda")
    else:
        print("   ❌ Error: No se pudo encontrar el proveedor en la segunda búsqueda")
    
    # Caso 3: Proveedor con nombre vacío
    print(f"\n3. Probando con nombre vacío")
    result3 = odoo_provider_service.find_or_create_provider("")
    
    if result3 is None:
        print("   ✅ Correcto: Nombre vacío devuelve None")
    else:
        print("   ❌ Error: Nombre vacío debería devolver None")
    
    # Caso 4: Proveedor con espacios
    print(f"\n4. Probando con nombre con espacios")
    result4 = odoo_provider_service.find_or_create_provider("  Proveedor con Espacios  ")
    
    if result4:
        print(f"   ✅ Resultado: {result4}")
        print(f"   - Nombre limpio: '{result4['name']}'")
    else:
        print("   ❌ Error: No se pudo procesar nombre con espacios")
    
    print("\n=== FIN DE PRUEBAS ===")

def test_product_creation_with_provider():
    """
    Prueba la creación de productos con el nuevo sistema de proveedores
    """
    print("\n=== PRUEBA DE CREACIÓN DE PRODUCTO CON PROVEEDOR ===")
    
    from api.services.odoo_product_service import OdooProductService
    
    product_service = OdooProductService()
    
    # Producto de prueba
    test_product = {
        'nombre': 'Producto Test Excel Import',
        'referencia_proveedor': 'TEST-001',
        'precio_coste': 10.50,
        'categoria': 'Categoría Test',
        'descripcion': 'Producto de prueba para importación Excel'
    }
    
    test_provider = "Proveedor Test Excel Import 2025"
    
    print(f"Creando producto: {test_product['nombre']}")
    print(f"Con proveedor: {test_provider}")
    
    try:
        odoo_dict = product_service.front_to_odoo_product_dict(test_product, test_provider)
        print(f"   ✅ Diccionario Odoo generado: {odoo_dict}")
        
        # Verificar que el proveedor se incluyó
        if 'supplier_id' in odoo_dict:
            print(f"   ✅ Proveedor incluido con ID: {odoo_dict['supplier_id']}")
        else:
            print("   ⚠️  Advertencia: No se incluyó información del proveedor")
            
    except Exception as e:
        print(f"   ❌ Error al generar diccionario Odoo: {e}")
    
    print("\n=== FIN DE PRUEBA DE PRODUCTO ===")

if __name__ == "__main__":
    try:
        test_find_or_create_provider()
        test_product_creation_with_provider()
    except Exception as e:
        logger.error(f"Error en las pruebas: {e}", exc_info=True)
        print(f"\n❌ Error general en las pruebas: {e}")