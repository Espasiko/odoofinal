import requests
import json

def check_api_endpoints():
    base_url = "http://localhost:8000"
    
    # Endpoints conocidos de FastAPI
    endpoints = [
        "/api/v1/providers",
        "/api/v1/auth/login",
        "/api/v1/auth/token",
        "/api/v1/users/me",
        "/docs",  # Documentación de FastAPI
        "/openapi.json",  # Esquema OpenAPI
        "/api/v1/dashboard/stats"
    ]
    
    print("=== VERIFICANDO ENDPOINTS DE LA API ===\n")
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        try:
            response = requests.get(url)
            print(f"{endpoint}: {response.status_code} - {response.reason}")
            
            # Si es la documentación, intentar obtener más información
            if endpoint == "/docs" and response.status_code == 200:
                print("  ✓ Documentación de la API disponible")
                
            # Si es el esquema OpenAPI, mostrar información básica
            if endpoint == "/openapi.json" and response.status_code == 200:
                try:
                    openapi = response.json()
                    print(f"  ✓ Versión OpenAPI: {openapi.get('openapi', 'N/A')}")
                    print(f"  ✓ Título: {openapi.get('info', {}).get('title', 'N/A')}")
                    print(f"  ✓ Descripción: {openapi.get('info', {}).get('description', 'N/A')[:100]}...")
                except:
                    print("  ✓ No se pudo analizar el esquema OpenAPI")
                    
        except requests.exceptions.RequestException as e:
            print(f"{endpoint}: Error - {str(e)}")
        
        print("-" * 80)

if __name__ == "__main__":
    check_api_endpoints()
