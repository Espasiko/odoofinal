import requests
from requests.auth import HTTPBasicAuth

def get_auth_token():
    auth_url = "http://localhost:8000/token"
    data = {
        "username": "admin",
        "password": "admin",
        "grant_type": "password"
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    try:
        response = requests.post(
            auth_url,
            data=data,
            headers=headers
        )
        response.raise_for_status()
        return response.json()["access_token"]
    except Exception as e:
        print(f"Error al autenticar: {str(e)}")
        return None

def get_providers(token):
    headers = {
        "Authorization": f"Bearer {token}",
        "accept": "application/json"
    }
    
    try:
        # Primero probamos con /providers/all
        response = requests.get(
            "http://localhost:8000/api/v1/providers/all",
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json()
        
        # Si falla, probamos con /providers
        response = requests.get(
            "http://localhost:8000/api/v1/providers",
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error al obtener proveedores: {str(e)}")
        return None

if __name__ == "__main__":
    print("=== OBTENIENDO TOKEN DE AUTENTICACIÓN ===")
    token = get_auth_token()
    
    if token:
        print("✓ Token obtenido correctamente")
        print("\n=== OBTENIENDO PROVEEDORES ===")
        providers = get_providers(token)
        
        if providers:
            print(f"✓ Se encontraron {len(providers)} proveedores:")
            for i, provider in enumerate(providers[:10], 1):  # Mostrar solo los primeros 10
                print(f"{i}. {provider.get('name', 'Sin nombre')} (ID: {provider.get('id', 'N/A')})")
            
            if len(providers) > 10:
                print(f"... y {len(providers) - 10} proveedores más")
        else:
            print("✗ No se pudieron obtener los proveedores")
    else:
        print("✗ No se pudo autenticar")
