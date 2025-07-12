#!/usr/bin/env python3
import subprocess
import time
import requests
import signal
import sys
import json

def start_server():
    """Inicia el servidor en segundo plano"""
    cmd = ['python3', 'run_server.py']
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return process

def check_routes():
    """Verifica las rutas disponibles en el servidor"""
    try:
        print("Verificando rutas disponibles...")
        response = requests.get("http://localhost:8000/openapi.json")
        
        if response.status_code == 200:
            openapi_data = response.json()
            paths = openapi_data.get('paths', {})
            
            print("\n=== RUTAS DISPONIBLES ===")
            product_routes = []
            for path in paths:
                print(f"  {path}")
                if 'product' in path.lower():
                    product_routes.append(path)
            
            print("\n=== RUTAS DE PRODUCTOS ===")
            for route in product_routes:
                print(f"  {route}")
                
            return '/api/v1/products/all' in product_routes
        else:
            print(f"Error obteniendo rutas: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Error verificando rutas: {e}")
        return False

def test_auth():
    """Prueba la autenticación"""
    try:
        print("\nProbando autenticación...")
        
        # Probar diferentes endpoints de auth
        auth_endpoints = [
            "/api/v1/auth/login",
            "/auth/login",
            "/login",
            "/token"
        ]
        
        auth_data = {
            "username": "admin",
            "password": "admin"
        }
        
        for endpoint in auth_endpoints:
            try:
                url = f"http://localhost:8000{endpoint}"
                print(f"Probando: {url}")
                response = requests.post(url, data=auth_data)
                print(f"  Status: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"  ✅ Autenticación exitosa en {endpoint}")
                    return response.json().get("access_token"), endpoint
                elif response.status_code != 404:
                    print(f"  Respuesta: {response.text[:100]}...")
                    
            except Exception as e:
                print(f"  Error: {e}")
                
        return None, None
        
    except Exception as e:
        print(f"Error en autenticación: {e}")
        return None, None

def main():
    server_process = None
    
    def signal_handler(sig, frame):
        if server_process:
            server_process.terminate()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        print("Iniciando servidor...")
        server_process = start_server()
        
        # Esperar a que el servidor se inicie
        time.sleep(5)
        
        # Verificar rutas
        has_products_all = check_routes()
        
        if has_products_all:
            print("\n✅ La ruta /api/v1/products/all está disponible!")
        else:
            print("\n❌ La ruta /api/v1/products/all NO está disponible.")
        
        # Probar autenticación
        token, auth_endpoint = test_auth()
        
        if token:
            print(f"\n✅ Autenticación exitosa usando {auth_endpoint}")
            
            if has_products_all:
                # Probar el endpoint de productos
                headers = {"Authorization": f"Bearer {token}"}
                print("\nProbando /api/v1/products/all...")
                response = requests.get("http://localhost:8000/api/v1/products/all", headers=headers)
                
                print(f"Status Code: {response.status_code}")
                if response.status_code == 200:
                    print("✅ ¡Endpoint funcionando correctamente!")
                    data = response.json()
                    print(f"Número de productos: {len(data)}")
                else:
                    print(f"❌ Error: {response.status_code}")
                    print(response.text)
        else:
            print("\n❌ No se pudo autenticar en ningún endpoint.")
            
    finally:
        if server_process:
            print("\nDeteniendo servidor...")
            server_process.terminate()
            server_process.wait()

if __name__ == "__main__":
    main()