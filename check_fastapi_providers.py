import requests
import json

def get_providers_from_fastapi():
    """Obtener proveedores de la API de FastAPI"""
    url = "http://localhost:8000/api/v1/providers"
    
    try:
        print("Obteniendo proveedores de la API de FastAPI...")
        response = requests.get(url, headers={"accept": "application/json"})
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Respuesta exitosa. Datos recibidos: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}...")
            return data
        else:
            print(f"✗ Error al obtener proveedores: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"✗ Error al conectar con la API de FastAPI: {str(e)}")
        return None

def compare_providers(db_suppliers, api_providers):
    """Comparar proveedores entre la base de datos y la API"""
    if not api_providers or 'data' not in api_providers:
        print("No se pudieron obtener los proveedores de la API para comparar")
        return
    
    # Mapear proveedores de la base de datos
    db_suppliers_map = {str(supplier['id']): supplier['name'] for supplier in db_suppliers}
    
    # Mapear proveedores de la API
    api_suppliers_map = {}
    for provider in api_providers.get('data', []):
        if isinstance(provider, dict) and 'id' in provider and 'name' in provider:
            api_suppliers_map[str(provider['id'])] = provider['name']
    
    # Encontrar diferencias
    only_in_db = set(db_suppliers_map.items()) - set(api_suppliers_map.items())
    only_in_api = set(api_suppliers_map.items()) - set(db_suppliers_map.items())
    
    print("\n=== COMPARACIÓN DE PROVEEDORES ===\n")
    print(f"Total en base de datos: {len(db_suppliers_map)}")
    print(f"Total en API: {len(api_suppliers_map)}\n")
    
    if only_in_db:
        print("Proveedores solo en la base de datos:")
        for sup_id, name in only_in_db:
            print(f"- {name} (ID: {sup_id})")
    
    if only_in_api:
        print("\nProveedores solo en la API (posiblemente datos de prueba):")
        for sup_id, name in only_in_api:
            print(f"- {name} (ID: {sup_id})")
    
    if not only_in_db and not only_in_api:
        print("✓ Los proveedores coinciden perfectamente entre la base de datos y la API.")

def main():
    print("=== VERIFICACIÓN DE PROVEEDORES EN FASTAPI ===\n")
    
    # 1. Obtener proveedores de la base de datos
    from check_suppliers_postgres import get_suppliers_from_db
    db_suppliers = get_suppliers_from_db()
    
    if not db_suppliers:
        print("No se pudieron obtener los proveedores de la base de datos.")
        return
    
    # 2. Obtener proveedores de la API de FastAPI
    api_providers = get_providers_from_fastapi()
    
    # 3. Comparar proveedores
    compare_providers(db_suppliers, api_providers)

if __name__ == "__main__":
    main()
