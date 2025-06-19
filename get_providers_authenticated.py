import requests
from requests.auth import HTTPBasicAuth
import json

def get_auth_token():
    """Obtiene un token de autenticación"""
    auth_url = "http://localhost:8000/token"
    
    # Usuario y contraseña según la configuración
    username = "yo@mail.com"
    password = "admin"
    
    # Datos para la autenticación según el esquema OAuth2
    data = {
        "username": username,
        "password": password,
        "grant_type": "password"
    }
    
    # Headers necesarios para el formulario
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    try:
        print(f"Intentando autenticar con usuario: {username}")
        response = requests.post(
            auth_url,
            data=data,
            headers=headers
        )
        
        # Si la autenticación falla, probar con el otro usuario
        if response.status_code == 401:
            print("Primer intento fallido, probando con usuario alternativo...")
            data["username"] = "admin"
            response = requests.post(
                auth_url,
                data=data,
                headers=headers
            )
        
        response.raise_for_status()
        token_data = response.json()
        return token_data["access_token"]
    except Exception as e:
        print(f"Error en la autenticación: {str(e)}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"Respuesta del servidor: {e.response.text}")
        return None

def get_providers(token):
    """Obtiene la lista de proveedores usando el token de autenticación"""
    headers = {
        "Authorization": f"Bearer {token}",
        "accept": "application/json"
    }
    
    # Intentar con diferentes endpoints de proveedores
    endpoints = [
        "/api/v1/providers/all",
        "/api/v1/providers"
    ]
    
    for endpoint in endpoints:
        url = f"http://localhost:8000{endpoint}"
        try:
            print(f"\nIntentando obtener proveedores desde {endpoint}...")
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                print("✓ Proveedores obtenidos exitosamente")
                return response.json()
            else:
                print(f"✗ Error {response.status_code}: {response.text}")
        except Exception as e:
            print(f"✗ Error al conectar con {endpoint}: {str(e)}")
    
    return None

def main():
    print("=== INICIANDO OBTENCIÓN DE PROVEEDORES ===\n")
    
    # 1. Obtener token de autenticación
    print("Paso 1: Autenticando...")
    token = get_auth_token()
    
    if not token:
        print("\n✗ No se pudo autenticar. Verifica las credenciales y que el servidor esté en ejecución.")
        return
    
    print("\n✓ Autenticación exitosa")
    
    # 2. Obtener lista de proveedores
    print("\nPaso 2: Obteniendo proveedores...")
    providers = get_providers(token)
    
    if not providers:
        print("\n✗ No se pudieron obtener los proveedores")
        return
    
    # 3. Mostrar resultados
    print("\n=== PROVEEDORES ENCONTRADOS ===\n")
    
    # Verificar si es una respuesta paginada o una lista directa
    if isinstance(providers, dict) and 'data' in providers:
        # Respuesta paginada
        providers_list = providers['data']
        total = providers.get('total', len(providers_list))
        print(f"Total de proveedores: {total}\n")
    else:
        # Lista directa
        providers_list = providers
        print(f"Total de proveedores: {len(providers_list)}\n")
    
    # Mostrar los primeros 10 proveedores
    for i, provider in enumerate(providers_list[:10], 1):
        print(f"{i}. ID: {provider.get('id', 'N/A')}")
        print(f"   Nombre: {provider.get('name', 'Sin nombre')}")
        print(f"   Email: {provider.get('email', 'No especificado')}")
        print(f"   Teléfono: {provider.get('phone', 'No especificado')}")
        print()
    
    if len(providers_list) > 10:
        print(f"... y {len(providers_list) - 10} proveedores más")
    
    # Guardar resultados en un archivo
    output_file = "proveedores_api.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(providers_list, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ Lista de proveedores guardada en '{output_file}'")

if __name__ == "__main__":
    main()
