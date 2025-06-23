#!/usr/bin/env python3
"""
Ejemplos de uso de Mistral OCR API

Este archivo contiene ejemplos prácticos de cómo usar los endpoints
de Mistral OCR para procesar documentos y facturas.
"""

import requests
import json
import os
from typing import Dict, Any

# Configuración base
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

class MistralOCRClient:
    """Cliente para interactuar con la API de Mistral OCR"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"
        self.token = None
    
    def authenticate(self, username: str, password: str) -> bool:
        """
        Autenticar usuario y obtener token JWT
        
        Args:
            username: Nombre de usuario
            password: Contraseña
            
        Returns:
            True si la autenticación fue exitosa
        """
        try:
            response = requests.post(
                f"{self.base_url}/token",
                data={
                    "username": username,
                    "password": password
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                token_data = response.json()
                self.token = token_data.get("access_token")
                print(f"✅ Autenticación exitosa para {username}")
                return True
            else:
                print(f"❌ Error de autenticación: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error conectando al servidor: {e}")
            return False
    
    def get_headers(self) -> Dict[str, str]:
        """Obtener headers con token de autenticación"""
        if not self.token:
            raise ValueError("No hay token de autenticación. Ejecutar authenticate() primero.")
        
        return {
            "Authorization": f"Bearer {self.token}"
        }
    
    def get_supported_formats(self) -> Dict[str, Any]:
        """
        Obtener formatos de archivo soportados
        
        Returns:
            Diccionario con formatos soportados
        """
        try:
            response = requests.get(
                f"{self.api_base}/mistral-ocr/supported-formats"
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Error obteniendo formatos: {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return {}
    
    def process_document(self, file_path: str, include_images: bool = True) -> Dict[str, Any]:
        """
        Procesar un documento general con Mistral OCR
        
        Args:
            file_path: Ruta del archivo a procesar
            include_images: Si incluir imágenes extraídas
            
        Returns:
            Resultado del procesamiento OCR
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
        
        try:
            with open(file_path, 'rb') as file:
                files = {'file': (os.path.basename(file_path), file)}
                data = {'include_images': include_images}
                
                response = requests.post(
                    f"{self.api_base}/mistral-ocr/process-document",
                    files=files,
                    data=data,
                    headers=self.get_headers()
                )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Error procesando documento: {response.status_code}")
                print(f"Respuesta: {response.text}")
                return {}
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return {}
    
    def process_invoice(self, file_path: str, create_in_odoo: bool = False) -> Dict[str, Any]:
        """
        Procesar una factura con Mistral OCR
        
        Args:
            file_path: Ruta del archivo de factura
            create_in_odoo: Si crear la factura en Odoo automáticamente
            
        Returns:
            Datos extraídos de la factura
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
        
        try:
            with open(file_path, 'rb') as file:
                files = {'file': (os.path.basename(file_path), file)}
                data = {'create_in_odoo': create_in_odoo}
                
                response = requests.post(
                    f"{self.api_base}/mistral-ocr/process-invoice",
                    files=files,
                    data=data,
                    headers=self.get_headers()
                )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Error procesando factura: {response.status_code}")
                print(f"Respuesta: {response.text}")
                return {}
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return {}
    
    def process_from_url(self, document_url: str, include_images: bool = True) -> Dict[str, Any]:
        """
        Procesar un documento desde una URL
        
        Args:
            document_url: URL del documento
            include_images: Si incluir imágenes extraídas
            
        Returns:
            Resultado del procesamiento OCR
        """
        try:
            data = {
                "document_url": document_url,
                "include_images": include_images
            }
            
            response = requests.post(
                f"{self.api_base}/mistral-ocr/process-from-url",
                json=data,
                headers={**self.get_headers(), "Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Error procesando desde URL: {response.status_code}")
                print(f"Respuesta: {response.text}")
                return {}
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return {}

def example_basic_usage():
    """Ejemplo básico de uso de Mistral OCR"""
    print("🚀 Ejemplo básico de Mistral OCR")
    print("=" * 50)
    
    # Crear cliente
    client = MistralOCRClient()
    
    # Autenticar
    if not client.authenticate("yo@mail.com", "admin"):
        print("❌ No se pudo autenticar")
        return
    
    # Obtener formatos soportados
    print("\n📋 Formatos soportados:")
    formats = client.get_supported_formats()
    if formats:
        print(json.dumps(formats, indent=2, ensure_ascii=False))
    
    # Ejemplo de procesamiento de documento
    # (Requiere un archivo de prueba)
    test_file = "test_document.pdf"
    if os.path.exists(test_file):
        print(f"\n📄 Procesando documento: {test_file}")
        result = client.process_document(test_file)
        if result:
            print("✅ Documento procesado exitosamente")
            print(f"Páginas: {result.get('data', {}).get('page_count', 0)}")
            print(f"Texto extraído: {len(result.get('data', {}).get('full_text', ''))} caracteres")
    else:
        print(f"⚠️  Archivo de prueba no encontrado: {test_file}")

def example_invoice_processing():
    """Ejemplo de procesamiento de facturas"""
    print("\n💰 Ejemplo de procesamiento de facturas")
    print("=" * 50)
    
    # Crear cliente
    client = MistralOCRClient()
    
    # Autenticar
    if not client.authenticate("yo@mail.com", "admin"):
        print("❌ No se pudo autenticar")
        return
    
    # Ejemplo de procesamiento de factura
    invoice_file = "test_invoice.pdf"
    if os.path.exists(invoice_file):
        print(f"\n🧾 Procesando factura: {invoice_file}")
        
        # Procesar sin crear en Odoo
        result = client.process_invoice(invoice_file, create_in_odoo=False)
        if result:
            print("✅ Factura procesada exitosamente")
            
            invoice_data = result.get('invoice_data', {}).get('extracted_data', {})
            print(f"Número de factura: {invoice_data.get('invoice_number', 'N/A')}")
            print(f"Proveedor: {invoice_data.get('supplier_name', 'N/A')}")
            print(f"Total: {invoice_data.get('total_amount', 0)} {invoice_data.get('currency', 'EUR')}")
            print(f"Líneas de productos: {len(invoice_data.get('line_items', []))}")
            
            # Mostrar líneas de productos
            for i, line in enumerate(invoice_data.get('line_items', []), 1):
                print(f"  {i}. {line.get('description', 'N/A')} - "
                      f"Qty: {line.get('quantity', 0)} - "
                      f"Precio: {line.get('unit_price', 0)}")
        
        # Ejemplo con creación en Odoo
        print("\n🔄 Procesando factura con creación en Odoo...")
        result_with_odoo = client.process_invoice(invoice_file, create_in_odoo=True)
        if result_with_odoo:
            odoo_result = result_with_odoo.get('odoo_invoice', {})
            if odoo_result.get('created'):
                print(f"✅ Factura creada en Odoo - ID Proveedor: {odoo_result.get('supplier_id')}")
            else:
                print(f"⚠️  No se pudo crear en Odoo: {odoo_result.get('message')}")
    else:
        print(f"⚠️  Archivo de factura no encontrado: {invoice_file}")

def example_url_processing():
    """Ejemplo de procesamiento desde URL"""
    print("\n🌐 Ejemplo de procesamiento desde URL")
    print("=" * 50)
    
    # Crear cliente
    client = MistralOCRClient()
    
    # Autenticar
    if not client.authenticate("yo@mail.com", "admin"):
        print("❌ No se pudo autenticar")
        return
    
    # URL de ejemplo (debe ser un documento público)
    document_url = "https://ejemplo.com/documento.pdf"
    
    print(f"\n🔗 Procesando documento desde URL: {document_url}")
    result = client.process_from_url(document_url)
    
    if result:
        print("✅ Documento desde URL procesado exitosamente")
        print(f"Páginas: {result.get('data', {}).get('page_count', 0)}")
        print(f"Texto extraído: {len(result.get('data', {}).get('full_text', ''))} caracteres")
    else:
        print("⚠️  No se pudo procesar el documento desde la URL")

def create_test_files():
    """Crear archivos de prueba para los ejemplos"""
    print("\n📁 Creando archivos de prueba...")
    
    # Crear un PDF de prueba simple (requiere reportlab)
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        # Crear documento de prueba
        c = canvas.Canvas("test_document.pdf", pagesize=letter)
        c.drawString(100, 750, "Documento de Prueba")
        c.drawString(100, 730, "Este es un documento de ejemplo para probar Mistral OCR.")
        c.drawString(100, 710, "Contiene texto simple para verificar la extracción.")
        c.save()
        print("✅ test_document.pdf creado")
        
        # Crear factura de prueba
        c = canvas.Canvas("test_invoice.pdf", pagesize=letter)
        c.drawString(100, 750, "FACTURA")
        c.drawString(100, 730, "Número: FAC-2024-001")
        c.drawString(100, 710, "Fecha: 15/01/2024")
        c.drawString(100, 690, "Proveedor: Empresa de Prueba S.L.")
        c.drawString(100, 670, "CIF: B12345678")
        c.drawString(100, 650, "")
        c.drawString(100, 630, "Descripción: Producto de prueba")
        c.drawString(100, 610, "Cantidad: 1")
        c.drawString(100, 590, "Precio unitario: 100.00 EUR")
        c.drawString(100, 570, "")
        c.drawString(100, 550, "Subtotal: 100.00 EUR")
        c.drawString(100, 530, "IVA (21%): 21.00 EUR")
        c.drawString(100, 510, "TOTAL: 121.00 EUR")
        c.save()
        print("✅ test_invoice.pdf creado")
        
    except ImportError:
        print("⚠️  reportlab no está instalado. Instalar con: pip install reportlab")
        print("⚠️  Los archivos de prueba no se pudieron crear")

def main():
    """Función principal con todos los ejemplos"""
    print("🎯 Ejemplos de uso de Mistral OCR API")
    print("=" * 60)
    
    # Verificar si el servidor está ejecutándose
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Servidor FastAPI está ejecutándose")
        else:
            print("❌ Servidor no responde correctamente")
            return
    except Exception as e:
        print(f"❌ No se puede conectar al servidor: {e}")
        print(f"Asegúrate de que el servidor esté ejecutándose en {BASE_URL}")
        return
    
    # Crear archivos de prueba
    create_test_files()
    
    # Ejecutar ejemplos
    example_basic_usage()
    example_invoice_processing()
    example_url_processing()
    
    print("\n🎉 Ejemplos completados")
    print("\n📚 Para más información, consulta:")
    print("   - docs/mistral_ocr_integration.md")
    print("   - API docs: http://localhost:8000/docs")

if __name__ == "__main__":
    main()