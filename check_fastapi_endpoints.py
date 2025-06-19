import requests

def check_fastapi_endpoints():
    """Verificar endpoints disponibles en la API de FastAPI"""
    base_url = "http://localhost:8000"
    
    # Endpoints a verificar
    endpoints = [
        "/api/v1/auth/session",
        "/api/v1/auth/token",
        "/api/v1/providers",
        "/api/v1/providers/all",
        "/api/v1/dashboard/stats",
        "/api/v1/products",
        "/api/v1/customers",
        "/api/v1/sales",
        "/api/v1/inventory",
        "/openapi.json",
        "/docs",
        "/redoc"
    ]
    
    print("=== VERIFICANDO ENDPOINTS DE FASTAPI ===\n")
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        try:
            # Probar con GET primero
            response = requests.get(url, allow_redirects=False)
            
            print(f"{endpoint}:")
            print(f"  GET - Status: {response.status_code}")
            
            # Si es un redirección, mostrar a dónde redirige
            if response.status_code in (301, 302, 303, 307, 308):
                print(f"  Redirects to: {response.headers.get('Location', 'Unknown')}")
            
            # Si es un error 405, probar con POST
            if response.status_code == 405:
                response_post = requests.post(url, json={}, allow_redirects=False)
                print(f"  POST - Status: {response_post.status_code}")
                
                # Si el POST también falla, probar con OPTIONS para ver los métodos permitidos
                if response_post.status_code == 405:
                    response_options = requests.options(url, allow_redirects=False)
                    allowed_methods = response_options.headers.get('Allow', 'N/A')
                    print(f"  Métodos permitidos: {allowed_methods}")
            
            # Si es la documentación, verificar si es accesible
            if endpoint in ['/docs', '/redoc'] and response.status_code == 200:
                print("  ✓ Documentación disponible")
            
            # Si es el esquema OpenAPI, verificar si es accesible
            if endpoint == '/openapi.json' and response.status_code == 200:
                try:
                    schema = response.json()
                    print(f"  ✓ Esquema OpenAPI disponible (versión: {schema.get('openapi', 'desconocida')})")
                except:
                    print("  ✓ Esquema OpenAPI disponible (no se pudo analizar)")
            
        except Exception as e:
            print(f"  Error al conectar: {str(e)}")
        
        print("  " + "-" * 50)

def main():
    check_fastapi_endpoints()

if __name__ == "__main__":
    main()
