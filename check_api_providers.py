import requests
import json

def check_api_providers():
    base_url = "http://localhost:8000/api/v1"
    
    try:
        # Verificar endpoint de proveedores
        print(f"\nProbando endpoint: {base_url}/providers")
        response = requests.get(f"{base_url}/providers")
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            providers = response.json()
            print(f"Proveedores desde la API ({len(providers)}):")
            
            # Guardar proveedores para comparación
            api_providers = []
            for i, provider in enumerate(providers, 1):
                print(f"{i}. {provider.get('name', 'Sin nombre')} (ID: {provider.get('id', 'N/A')})")
                api_providers.append({
                    'id': provider.get('id'),
                    'name': provider.get('name')
                })
            
            # Guardar en archivo para comparación
            with open('api_providers.txt', 'w') as f:
                for p in api_providers:
                    f.write(f"{p['id']},{p['name']}\n")
                    
            return providers
        else:
            print(f"Error en la respuesta: {response.text}")
            return None
            
    except Exception as e:
        print(f"Error al conectar con la API: {str(e)}")
        return None

if __name__ == "__main__":
    print("=== VERIFICACIÓN DE PROVEEDORES EN LA API ===")
    check_api_providers()
