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

def test_products_all_endpoint():
    """Prueba el endpoint /api/v1/products/all con autenticación correcta"""
    try:
        # Autenticación usando las credenciales estándar
        auth_data = {
            "username": "admin",
            "password": "admin"  # Credenciales estándar del sistema
        }
        
        print("🔐 Obteniendo token de acceso...")
        auth_response = requests.post(
            "http://localhost:8000/api/v1/auth/login", 
            data=auth_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if auth_response.status_code != 200:
            print(f"❌ Error en autenticación: {auth_response.status_code}")
            print(f"Respuesta: {auth_response.text}")
            return False
            
        token_data = auth_response.json()
        access_token = token_data["access_token"]
        print(f"✅ Token obtenido exitosamente")
        
        # Probar el endpoint /api/v1/products/all
        headers = {"Authorization": f"Bearer {access_token}"}
        
        print("📦 Probando endpoint /api/v1/products/all...")
        response = requests.get("http://localhost:8000/api/v1/products/all", headers=headers)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("🎉 ¡ÉXITO! El endpoint /api/v1/products/all funciona correctamente!")
            data = response.json()
            print(f"📊 Número de productos obtenidos: {len(data)}")
            
            if len(data) > 0:
                print("\n📋 Ejemplo de producto:")
                first_product = data[0]
                for key, value in first_product.items():
                    print(f"  {key}: {value}")
            
            return True
        else:
            print(f"❌ Error en el endpoint: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar al servidor en localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def main():
    server_process = None
    
    def signal_handler(sig, frame):
        if server_process:
            print("\n🛑 Deteniendo servidor...")
            server_process.terminate()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        print("🚀 Iniciando servidor en puerto 8000...")
        server_process = start_server()
        
        # Esperar a que el servidor se inicie completamente
        print("⏳ Esperando que el servidor se inicie...")
        time.sleep(6)
        
        # Verificar que el servidor esté respondiendo
        try:
            health_check = requests.get("http://localhost:8000/", timeout=5)
            if health_check.status_code == 200:
                print("✅ Servidor iniciado correctamente")
            else:
                print(f"⚠️  Servidor responde con código: {health_check.status_code}")
        except:
            print("❌ Servidor no responde")
            return
        
        # Ejecutar la prueba
        print("\n" + "="*50)
        print("🧪 INICIANDO PRUEBA DEL ENDPOINT /products/all")
        print("="*50)
        
        success = test_products_all_endpoint()
        
        print("\n" + "="*50)
        if success:
            print("🎊 ¡PRUEBA COMPLETADA EXITOSAMENTE!")
            print("✅ El endpoint /api/v1/products/all está funcionando correctamente")
            print("✅ La reordenación de rutas fue exitosa")
            print("✅ El problema de routing ha sido resuelto")
        else:
            print("❌ LA PRUEBA FALLÓ")
            print("❌ Revisar configuración del servidor o autenticación")
        print("="*50)
            
    finally:
        if server_process:
            print("\n🛑 Deteniendo servidor...")
            server_process.terminate()
            server_process.wait()
            print("✅ Servidor detenido")

if __name__ == "__main__":
    main()