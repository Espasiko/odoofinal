#!/usr/bin/env python3
import subprocess
import time
import requests
import signal
import sys

def start_server():
    """Inicia el servidor en segundo plano"""
    cmd = ['python3', 'run_server.py']
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return process

def test_endpoint():
    """Prueba el endpoint /products/all"""
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
            return False
            
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
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar al servidor")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

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
        
        # Probar el endpoint
        success = test_endpoint()
        
        if success:
            print("\n🎉 ¡Prueba exitosa! El endpoint /products/all funciona correctamente.")
        else:
            print("\n❌ La prueba falló.")
            
    finally:
        if server_process:
            print("\nDeteniendo servidor...")
            server_process.terminate()
            server_process.wait()

if __name__ == "__main__":
    main()