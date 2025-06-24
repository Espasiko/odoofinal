#!/usr/bin/env python3
"""
Cliente de ejemplo para la API de Mistral OCR

Este script demuestra cómo usar la API de Mistral OCR programáticamente
desde Python para procesar documentos y extraer texto.

Uso:
    python mistral_ocr_client.py archivo.pdf
    python mistral_ocr_client.py imagen.png --include-images
"""

import requests
import json
import argparse
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

class MistralOCRClient:
    """Cliente para interactuar con la API de Mistral OCR"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.access_token: Optional[str] = None
    
    def authenticate(self, username: str = "admin", password: str = "admin_password_secure") -> bool:
        """Autenticarse con la API y obtener token de acceso"""
        try:
            response = self.session.post(
                f"{self.base_url}/token",
                data={
                    "username": username,
                    "password": password
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data.get("access_token")
            
            if self.access_token:
                # Configurar header de autorización para futuras peticiones
                self.session.headers.update({
                    "Authorization": f"Bearer {self.access_token}"
                })
                return True
            return False
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error de autenticación: {e}")
            return False
    
    def process_document(self, file_path: str, include_images: bool = True) -> Dict[str, Any]:
        """Procesar un documento con Mistral OCR"""
        if not self.access_token:
            raise ValueError("No autenticado. Llama a authenticate() primero.")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
        
        try:
            with open(file_path, 'rb') as file:
                files = {
                    'file': (os.path.basename(file_path), file, self._get_content_type(file_path))
                }
                data = {
                    'include_images': str(include_images).lower()
                }
                
                response = self.session.post(
                    f"{self.base_url}/api/v1/mistral-ocr/process-document",
                    files=files,
                    data=data
                )
                response.raise_for_status()
                return response.json()
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error procesando documento: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    print(f"Detalle del error: {error_detail}")
                except:
                    print(f"Respuesta del servidor: {e.response.text}")
            raise
    
    def _get_content_type(self, file_path: str) -> str:
        """Obtener el tipo de contenido basado en la extensión del archivo"""
        extension = Path(file_path).suffix.lower()
        content_types = {
            '.pdf': 'application/pdf',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.avif': 'image/avif',
            '.txt': 'text/plain'
        }
        return content_types.get(extension, 'application/octet-stream')
    
    def check_server_status(self) -> bool:
        """Verificar si el servidor está ejecutándose"""
        try:
            response = self.session.get(f"{self.base_url}/docs", timeout=5)
            return response.status_code == 200
        except:
            return False

def format_ocr_result(result: Dict[str, Any]) -> str:
    """Formatear el resultado del OCR para mostrar en consola"""
    output = []
    output.append("=" * 50)
    output.append("📋 RESULTADO DEL OCR")
    output.append("=" * 50)
    
    # Extraer texto
    text_content = None
    if 'data' in result and 'text' in result['data']:
        text_content = result['data']['text']
    elif 'text' in result:
        text_content = result['text']
    
    if text_content:
        output.append("\n📝 TEXTO EXTRAÍDO:")
        output.append("-" * 20)
        output.append(text_content)
        output.append("-" * 20)
    
    # Mostrar metadatos si están disponibles
    metadata = result.get('data', {}).get('metadata', {})
    if metadata:
        output.append("\n📊 METADATOS:")
        for key, value in metadata.items():
            output.append(f"  • {key}: {value}")
    
    # Información sobre imágenes
    images = result.get('data', {}).get('images', [])
    if images:
        output.append(f"\n🖼️  IMÁGENES EXTRAÍDAS: {len(images)}")
        for i, img in enumerate(images, 1):
            img_size = len(img) if isinstance(img, str) else 0
            output.append(f"  • Imagen {i}: {img_size} caracteres base64")
    
    output.append("\n" + "=" * 50)
    return "\n".join(output)

def main():
    parser = argparse.ArgumentParser(
        description="Cliente para la API de Mistral OCR",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python mistral_ocr_client.py documento.pdf
  python mistral_ocr_client.py imagen.png --include-images
  python mistral_ocr_client.py factura.jpg --base-url http://localhost:8000
  python mistral_ocr_client.py archivo.pdf --username admin --password mi_password
        """
    )
    
    parser.add_argument(
        "file_path",
        help="Ruta al archivo a procesar (PDF, PNG, JPG, JPEG, AVIF)"
    )
    parser.add_argument(
        "--include-images",
        action="store_true",
        default=True,
        help="Incluir imágenes extraídas en base64 (por defecto: True)"
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="URL base de la API (por defecto: http://localhost:8000)"
    )
    parser.add_argument(
        "--username",
        default="admin",
        help="Nombre de usuario para autenticación (por defecto: admin)"
    )
    parser.add_argument(
        "--password",
        default="admin_password_secure",
        help="Contraseña para autenticación (por defecto: admin_password_secure)"
    )
    parser.add_argument(
        "--output",
        help="Archivo donde guardar el resultado en formato JSON"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Mostrar información detallada"
    )
    
    args = parser.parse_args()
    
    # Verificar que el archivo existe
    if not os.path.exists(args.file_path):
        print(f"❌ Error: El archivo '{args.file_path}' no existe")
        sys.exit(1)
    
    # Crear cliente
    client = MistralOCRClient(args.base_url)
    
    if args.verbose:
        print(f"🔗 Conectando a: {args.base_url}")
        print(f"📄 Archivo a procesar: {args.file_path}")
        print(f"🖼️  Incluir imágenes: {args.include_images}")
    
    # Verificar que el servidor esté ejecutándose
    if not client.check_server_status():
        print(f"❌ Error: No se puede conectar al servidor en {args.base_url}")
        print("💡 Asegúrate de que el servidor FastAPI esté ejecutándose")
        sys.exit(1)
    
    if args.verbose:
        print("✅ Servidor disponible")
    
    # Autenticarse
    print("🔐 Autenticando...")
    if not client.authenticate(args.username, args.password):
        print("❌ Error: No se pudo autenticar")
        sys.exit(1)
    
    if args.verbose:
        print("✅ Autenticación exitosa")
    
    # Procesar documento
    print(f"🔍 Procesando documento: {os.path.basename(args.file_path)}")
    try:
        result = client.process_document(args.file_path, args.include_images)
        
        # Mostrar resultado
        print(format_ocr_result(result))
        
        # Guardar resultado si se especifica
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Resultado guardado en: {args.output}")
        
        print("\n✅ Procesamiento completado exitosamente")
        
    except Exception as e:
        print(f"❌ Error procesando documento: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()