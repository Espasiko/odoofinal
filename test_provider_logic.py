#!/usr/bin/env python3
"""
Test simplificado para verificar la lógica de find_or_create_provider
sin necesidad de conexión a Odoo
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class MockOdooService:
    """Mock del servicio Odoo para testing"""
    
    def __init__(self):
        self.providers = [
            {'id': 1, 'name': 'Proveedor Existente', 'vat': 'B12345678'},
            {'id': 2, 'name': 'ACME Corp', 'vat': 'A87654321'},
        ]
        self.next_id = 3
    
    def search_read(self, model, domain, fields):
        """Simula búsqueda en Odoo"""
        if model == 'res.partner':
            # Buscar por nombre
            for condition in domain:
                if len(condition) == 3 and condition[0] == 'name' and condition[1] == 'ilike':
                    search_name = condition[2].lower()
                    for provider in self.providers:
                        if search_name in provider['name'].lower():
                            return [{'id': provider['id'], 'name': provider['name']}]
            return []
        return []
    
    def create(self, model, values):
        """Simula creación en Odoo"""
        if model == 'res.partner':
            new_provider = {
                'id': self.next_id,
                'name': values.get('name', ''),
                'vat': values.get('vat', '')
            }
            self.providers.append(new_provider)
            self.next_id += 1
            return new_provider['id']
        return None
    
    def read(self, model, ids, fields):
        """Simula lectura en Odoo"""
        if model == 'res.partner':
            result = []
            for provider in self.providers:
                if provider['id'] in ids:
                    result.append({field: provider.get(field, '') for field in fields})
            return result
        return []

def mock_find_or_create_provider(provider_name, odoo_service):
    """
    Versión mock de find_or_create_provider para testing
    """
    if not provider_name or not provider_name.strip():
        return None, None
    
    provider_name = provider_name.strip()
    
    # Buscar proveedor existente
    domain = [('name', 'ilike', provider_name), ('is_company', '=', True), ('supplier_rank', '>', 0)]
    existing_providers = odoo_service.search_read('res.partner', domain, ['id', 'name'])
    
    if existing_providers:
        provider = existing_providers[0]
        print(f"✅ Proveedor encontrado: {provider['name']} (ID: {provider['id']})")
        return provider['id'], provider['name']
    
    # Crear nuevo proveedor
    print(f"🔄 Creando nuevo proveedor: {provider_name}")
    
    provider_data = {
        'name': provider_name,
        'is_company': True,
        'supplier_rank': 1,
        'customer_rank': 0,
        'category_id': [(6, 0, [])],
    }
    
    try:
        new_provider_id = odoo_service.create('res.partner', provider_data)
        
        # Leer el proveedor creado
        created_provider = odoo_service.read('res.partner', [new_provider_id], ['id', 'name'])
        if created_provider:
            provider_info = created_provider[0]
            print(f"✅ Proveedor creado: {provider_info['name']} (ID: {provider_info['id']})")
            return provider_info['id'], provider_info['name']
        
    except Exception as e:
        print(f"❌ Error al crear proveedor: {e}")
        return None, None
    
    return None, None

def test_provider_logic():
    """Test de la lógica de proveedores"""
    print("=== INICIO DE PRUEBA DE LÓGICA DE PROVEEDORES ===")
    
    # Crear mock del servicio Odoo
    mock_odoo = MockOdooService()
    
    # Casos de prueba
    test_cases = [
        "Proveedor Existente",  # Debería encontrarlo
        "ACME",                 # Debería encontrar ACME Corp
        "Nuevo Proveedor",      # Debería crearlo
        "",                     # Debería retornar None
        "   ",                  # Debería retornar None
        "Otro Proveedor Nuevo", # Debería crearlo
    ]
    
    for i, provider_name in enumerate(test_cases, 1):
        print(f"\n--- Caso {i}: '{provider_name}' ---")
        provider_id, provider_name_result = mock_find_or_create_provider(provider_name, mock_odoo)
        
        if provider_id:
            print(f"Resultado: ID={provider_id}, Nombre='{provider_name_result}'")
        else:
            print("Resultado: No se pudo procesar el proveedor")
    
    print(f"\n--- Estado final de proveedores ---")
    for provider in mock_odoo.providers:
        print(f"ID: {provider['id']}, Nombre: '{provider['name']}'")
    
    print("\n=== FIN DE PRUEBA DE LÓGICA DE PROVEEDORES ===")

if __name__ == "__main__":
    test_provider_logic()