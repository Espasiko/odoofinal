#!/usr/bin/env python3
"""
Test de integración completa para verificar el flujo de creación de productos
con proveedores usando find_or_create_provider.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class MockOdooService:
    """Mock del servicio Odoo para testing sin conexión real"""
    
    def __init__(self):
        self.providers = {
            1: {'id': 1, 'name': 'Proveedor Existente'},
            2: {'id': 2, 'name': 'ACME Corp'}
        }
        self.categories = {
            1: {'id': 1, 'name': 'All'},
            2: {'id': 2, 'name': 'Electrónicos'},
            3: {'id': 3, 'name': 'Smartphones'}
        }
        self.next_provider_id = 3
        self.next_category_id = 4
        self._models = True
    
    def _execute_kw(self, model, method, args, kwargs=None):
        if model == 'res.partner':
            if method == 'search_read':
                domain = args[0]
                # Buscar por nombre exacto
                for condition in domain:
                    if condition[0] == 'name' and condition[1] == '=':
                        search_name = condition[2]
                        for provider in self.providers.values():
                            if provider['name'] == search_name:
                                return [provider]
                return []
            elif method == 'create':
                provider_data = args[0]
                new_id = self.next_provider_id
                self.next_provider_id += 1
                self.providers[new_id] = {
                    'id': new_id,
                    'name': provider_data['name']
                }
                return new_id
        
        elif model == 'product.category':
            if method == 'search_read':
                domain = args[0]
                # Buscar categoría por nombre
                for condition in domain:
                    if condition[0] == 'name' and condition[1] == '=':
                        search_name = condition[2]
                        for category in self.categories.values():
                            if category['name'] == search_name:
                                return [category]
                return []
            elif method == 'create':
                category_data = args[0]
                new_id = self.next_category_id
                self.next_category_id += 1
                self.categories[new_id] = {
                    'id': new_id,
                    'name': category_data['name']
                }
                return new_id
        
        return None

def test_integration_complete():
    """Test completo de integración producto-proveedor"""
    print("=== TEST DE INTEGRACIÓN COMPLETA ===")
    print()
    
    # Importar y configurar el servicio con mock
    from api.services.odoo_provider_service import OdooProviderService
    from api.services.odoo_product_service import OdooProductService
    
    # Crear instancias mock
    mock_odoo = MockOdooService()
    
    # Configurar servicios con mock
    provider_service = OdooProviderService()
    provider_service._models = mock_odoo._models
    provider_service._execute_kw = mock_odoo._execute_kw
    
    product_service = OdooProductService()
    product_service._models = mock_odoo._models
    product_service._execute_kw = mock_odoo._execute_kw
    
    # Casos de prueba
    test_cases = [
        {
            'nombre': 'iPhone 15',
            'referencia_proveedor': 'IPH15-128',
            'precio_coste': 800.0,
            'precio_venta': 1200.0,
            'categoria': 'Electrónicos',
            'subcategoria': 'Smartphones',
            'descripcion': 'iPhone 15 128GB',
            'proveedor': 'ACME Corp'  # Proveedor existente
        },
        {
            'nombre': 'Samsung Galaxy S24',
            'referencia_proveedor': 'SGS24-256',
            'precio_coste': 750.0,
            'categoria': 'Electrónicos',
            'descripcion': 'Samsung Galaxy S24 256GB',
            'proveedor': 'Samsung España'  # Proveedor nuevo
        },
        {
            'nombre': 'Cable USB-C',
            'referencia_proveedor': 'USB-C-001',
            'precio_coste': 5.0,
            'categoria': 'Accesorios',
            'descripcion': 'Cable USB-C 1 metro',
            'proveedor': ''  # Sin proveedor
        }
    ]
    
    for i, producto in enumerate(test_cases, 1):
        print(f"--- Caso {i}: {producto['nombre']} ---")
        
        try:
            # Usar el método front_to_odoo_product_dict
            odoo_dict = product_service.front_to_odoo_product_dict(producto)
            
            print(f"✅ Producto procesado: {producto['nombre']}")
            print(f"   - Referencia: {odoo_dict.get('default_code', 'N/A')}")
            print(f"   - Precio coste: {odoo_dict.get('standard_price', 0)}€")
            print(f"   - Precio venta: {odoo_dict.get('list_price', 0)}€")
            print(f"   - Categoría ID: {odoo_dict.get('categ_id', 'N/A')}")
            
            if 'supplier_id' in odoo_dict:
                supplier_id = odoo_dict['supplier_id']
                supplier_name = mock_odoo.providers.get(supplier_id, {}).get('name', 'Desconocido')
                print(f"   - Proveedor: {supplier_name} (ID: {supplier_id})")
            else:
                print(f"   - Sin proveedor asociado")
            
        except Exception as e:
            print(f"❌ Error procesando producto: {e}")
        
        print()
    
    # Mostrar estado final
    print("--- Estado final de proveedores ---")
    for provider in mock_odoo.providers.values():
        print(f"ID: {provider['id']}, Nombre: '{provider['name']}'")
    
    print()
    print("--- Estado final de categorías ---")
    for category in mock_odoo.categories.values():
        print(f"ID: {category['id']}, Nombre: '{category['name']}'")
    
    print()
    print("=== FIN DEL TEST DE INTEGRACIÓN COMPLETA ===")

if __name__ == "__main__":
    test_integration_complete()