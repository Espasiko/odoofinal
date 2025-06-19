import requests
from requests.auth import HTTPBasicAuth
import json

def get_oauth_token():
    """Obtener token OAuth2 con flujo de contraseña"""
    token_url = "http://localhost:8000/token"
    auth_data = {
        "username": "admin",  # Ajusta según sea necesario
        "password": "admin",  # Ajusta según sea necesario
        "grant_type": "password",
        "scope": ""
    }
    
    try:
        print("Obteniendo token OAuth2...")
        response = requests.post(
            token_url,
            data=auth_data,
            auth=HTTPBasicAuth("client_id", "client_secret")  # Ajusta según sea necesario
        )
        
        if response.status_code == 200:
            token_data = response.json()
            print("✓ Token obtenido con éxito")
            return token_data.get('access_token')
        else:
            print(f"✗ Error al obtener token: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"✗ Error al conectar con el servidor de autenticación: {str(e)}")
        return None

def get_providers(token):
    """Obtener lista de proveedores con el token de acceso"""
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

def main():
    print("=== VERIFICACIÓN DE PROVEEDORES CON OAUTH2 ===\n")
    
    # 1. Obtener token OAuth2
    token = get_oauth_token()
    if not token:
        print("No se pudo obtener el token de autenticación. Verifica las credenciales.")
        return
    
    # 2. Obtener proveedores
    providers = get_providers(token)
    
    if providers:
        print("\n=== LISTA DE PROVEEDORES ===")
        for i, provider in enumerate(providers[:10], 1):  # Mostrar solo los primeros 10
            print(f"{i}. {provider.get('name')} (ID: {provider.get('id')})")
        if len(providers) > 10:
            print(f"... y {len(providers) - 10} más")
    
    # 3. Comparar con Odoo si existe el archivo
    try:
        with open('odoo_suppliers.txt', 'r') as f:
            odoo_suppliers = {}
            for line in f:
                parts = line.strip().split(',', 1)
                if len(parts) == 2:
                    odoo_suppliers[parts[0]] = parts[1]
            
            api_suppliers = {str(p['id']): p['name'] for p in providers}
            
            only_in_odoo = set(odoo_suppliers.items()) - set(api_suppliers.items())
            only_in_api = set(api_suppliers.items()) - set(odoo_suppliers.items())
            
            print("\n=== COMPARACIÓN CON ODOO ===\n")
            print(f"Proveedores en Odoo: {len(odoo_suppliers)}")
            print(f"Proveedores en API: {len(api_suppliers)}")
            
            if only_in_odoo:
                print("\nProveedores solo en Odoo:")
                for sup_id, name in only_in_odoo:
                    print(f"- {name} (ID: {sup_id})")
            
            if only_in_api:
                print("\nProveedores solo en la API (posiblemente datos de prueba):")
                for sup_id, name in only_in_api:
                    print(f"- {name} (ID: {sup_id})")
            
            if not only_in_odoo and not only_in_api:
                print("\n✓ Los proveedores coinciden perfectamente entre Odoo y la API.")
                
    except FileNotFoundError:
        print("\nNo se encontró el archivo de proveedores de Odoo. Ejecuta primero check_suppliers_odoo.py")
    
    print("\n=== VERIFICACIÓN COMPLETADA ===")

if __name__ == "__main__":
    main()
