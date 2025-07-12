import requests
import json

def test_endpoint():
    try:
        # Primero obtener token
        auth_data = {
            "username": "admin",
            "password": "admin"
        }
        
        print("Obteniendo token...")
        auth_response = requests.post("http://localhost:8000/api/v1/auth/login", data=auth_data)
        
        if auth_response.status_code != 200:
            print(f"Error en autenticación: {auth_response.status_code}")
            print(auth_response.text)
            return
            
        token = auth_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Probar el endpoint /products/all
        print("Probando /api/v1/products/all...")
        response = requests.get("http://localhost:8000/api/v1/products/all", headers=headers)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("✅ ¡Endpoint funcionando correctamente!")
            data = response.json()
            print(f"Número de productos: {len(data)}")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar al servidor")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_endpoint()