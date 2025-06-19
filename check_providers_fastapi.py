import requests
import json

def get_auth_token():
    """Obtener token de autenticación"""
    auth_url = "http://localhost:8000/api/v1/auth/session"
    auth_data = {
        "username": "admin",  # Ajusta según sea necesario
        "password": "admin"   # Ajusta según sea necesario
    }
    
    try:
        response = requests.post(auth_url, json=auth_data)
        if response.status_code == 200:
            print("✓ Autenticación exitosa")
            return response.json().get('access_token')
        else:
            print(f"✗ Error de autenticación: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"✗ Error al conectar con la API de autenticación: {str(e)}")
        return None

def get_providers(token):
    """Obtener lista de proveedores"""
    url = "http://localhost:8000/api/v1/providers"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        print("\nObteniendo lista de proveedores...")
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            providers = response.json()
            print(f"✓ Se encontraron {len(providers)} proveedores")
            return providers
        else:
            print(f"✗ Error al obtener proveedores: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"✗ Error al conectar con la API de proveedores: {str(e)}")
        return []

def get_all_providers(token):
    """Obtener todos los proveedores (incluyendo inactivos)"""
    url = "http://localhost:8000/api/v1/providers/all"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        print("\nObteniendo todos los proveedores (incluyendo inactivos)...")
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            providers = response.json()
            print(f"✓ Se encontraron {len(providers)} proveedores (incluyendo inactivos)")
            return providers
        else:
            print(f"✗ Error al obtener todos los proveedores: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"✗ Error al conectar con la API de proveedores: {str(e)}")
        return []

def compare_with_odoo(api_providers):
    """Comparar proveedores de la API con los de Odoo"""
    try:
        # Leer proveedores de Odoo guardados previamente
        with open('odoo_suppliers.txt', 'r') as f:
            odoo_suppliers = {}
            for line in f:
                parts = line.strip().split(',', 1)
                if len(parts) == 2:
                    odoo_suppliers[parts[0]] = parts[1]
        
        # Mapear proveedores de la API
        api_suppliers = {str(p['id']): p['name'] for p in api_providers}
        
        # Encontrar diferencias
        only_in_odoo = set(odoo_suppliers.items()) - set(api_suppliers.items())
        only_in_api = set(api_suppliers.items()) - set(odoo_suppliers.items())
        
        print("\n=== COMPARACIÓN DE PROVEEDORES ===\n")
        print(f"Total en Odoo: {len(odoo_suppliers)}")
        print(f"Total en API: {len(api_suppliers)}\n")
        
        if only_in_odoo:
            print("Proveedores solo en Odoo:")
            for sup_id, name in only_in_odoo:
                print(f"- {name} (ID: {sup_id})")
            print()
        
        if only_in_api:
            print("Proveedores solo en la API (posiblemente datos de prueba):")
            for sup_id, name in only_in_api:
                print(f"- {name} (ID: {sup_id})")
            print()
        
        if not only_in_odoo and not only_in_api:
            print("✓ Los proveedores coinciden perfectamente entre Odoo y la API.")
            
    except Exception as e:
        print(f"✗ Error al comparar proveedores: {str(e)}")

if __name__ == "__main__":
    print("=== VERIFICACIÓN DE PROVEEDORES EN FASTAPI ===\n")
    
    # 1. Autenticación
    token = get_auth_token()
    if not token:
        print("No se pudo autenticar. Verifica las credenciales y la conexión.")
        exit(1)
    
    # 2. Obtener proveedores activos
    providers = get_providers(token)
    
    # 3. Obtener todos los proveedores (incluyendo inactivos)
    all_providers = get_all_providers(token)
    
    # 4. Mostrar información resumida
    if providers:
        print("\n=== PROVEEDORES ACTIVOS ===")
        for i, provider in enumerate(providers[:10], 1):  # Mostrar solo los primeros 10
            print(f"{i}. {provider.get('name')} (ID: {provider.get('id')})")
        if len(providers) > 10:
            print(f"... y {len(providers) - 10} más")
    
    # 5. Comparar con Odoo si hay datos
    try:
        with open('odoo_suppliers.txt', 'r'):
            compare_with_odoo(providers)
    except FileNotFoundError:
        print("\nNo se encontró el archivo de proveedores de Odoo. Ejecuta primero check_suppliers_odoo.py")
    
    print("\n=== VERIFICACIÓN COMPLETADA ===")
