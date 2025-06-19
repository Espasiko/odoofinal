import requests
import json
from requests.auth import HTTPBasicAuth

def authenticate_fastapi():
    """Autenticarse en la API de FastAPI"""
    auth_url = "http://localhost:8000/api/v1/auth/session"
    
    # Intentar con credenciales por defecto
    credentials = [
        {"username": "admin", "password": "admin"},
        {"username": "yo@mail.com", "password": "admin"},
        {"email": "admin@example.com", "password": "admin"},
        {"email": "yo@mail.com", "password": "admin"}
    ]
    
    for creds in credentials:
        try:
            print(f"Intentando autenticar con: {creds}")
            response = requests.post(
                auth_url,
                json=creds,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                token_data = response.json()
                print("✓ Autenticación exitosa")
                return token_data.get('access_token')
            else:
                print(f"✗ Error de autenticación: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"✗ Error al conectar con el servidor: {str(e)}")
    
    print("No se pudo autenticar con ninguna de las credenciales probadas")
    return None

def get_protected_data(token):
    """Obtener datos protegidos con el token de autenticación"""
    headers = {
        "Authorization": f"Bearer {token}",
        "accept": "application/json"
    }
    
    # Probar diferentes endpoints
    endpoints = [
        "/api/v1/providers",
        "/api/v1/providers/all",
        "/api/v1/dashboard/stats"
    ]
    
    for endpoint in endpoints:
        url = f"http://localhost:8000{endpoint}"
        try:
            print(f"\nProbando endpoint: {endpoint}")
            response = requests.get(url, headers=headers)
            print(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Respuesta exitosa. Datos recibidos: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}...")
            else:
                print(f"Error en la respuesta: {response.text}")
        except Exception as e:
            print(f"Error al conectar con el endpoint: {str(e)}")

def main():
    print("=== PRUEBA DE AUTENTICACIÓN EN FASTAPI ===\n")
    
    # 1. Autenticarse
    token = authenticate_fastapi()
    
    if token:
        print(f"\nToken de acceso obtenido: {token[:20]}...")
        
        # 2. Obtener datos protegidos
        print("\n=== OBTENIENDO DATOS PROTEGIDOS ===")
        get_protected_data(token)
    else:
        print("No se pudo autenticar. No se pueden obtener datos protegidos.")

if __name__ == "__main__":
    main()
