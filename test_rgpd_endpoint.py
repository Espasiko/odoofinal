#!/usr/bin/env python3
import requests
import os
import sys
from pathlib import Path

def test_rgpd_endpoint(image_path):
    """
    Prueba el endpoint RGPD enviando una imagen
    """
    # Verificar que la imagen existe
    if not os.path.exists(image_path):
        print(f"Error: No se encontró la imagen en {image_path}")
        sys.exit(1)
    
    # URL del endpoint FastAPI
    url = "http://localhost:8000/api/v1/n8n/process-rgpd"
    
    # Preparar el archivo para enviar
    files = {
        'file': (os.path.basename(image_path), open(image_path, 'rb'), 'image/png')
    }
    
    print(f"Enviando imagen {image_path} al endpoint {url}...")
    
    try:
        # Enviar la solicitud
        response = requests.post(url, files=files)
        
        # Mostrar resultado
        print(f"Código de estado: {response.status_code}")
        print("Respuesta:")
        print(response.text)
        
        return response.json() if response.status_code == 200 else None
        
    except Exception as e:
        print(f"Error al enviar la solicitud: {e}")
        return None
    finally:
        # Cerrar el archivo
        files['file'][1].close()

if __name__ == "__main__":
    # Verificar si se proporcionó una ruta de imagen como argumento
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        # Buscar alguna imagen PNG en el directorio actual
        print("No se proporcionó una ruta de imagen. Buscando imágenes PNG en el directorio actual...")
        png_files = list(Path('.').glob('*.png'))
        
        if not png_files:
            print("No se encontraron imágenes PNG. Por favor proporcione una ruta de imagen como argumento.")
            sys.exit(1)
        
        image_path = str(png_files[0])
        print(f"Usando imagen: {image_path}")
    
    # Probar el endpoint
    test_rgpd_endpoint(image_path)
