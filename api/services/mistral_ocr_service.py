from typing import List, Optional, Dict, Any
import os
import base64
import requests
from mistralai import Mistral
from ..utils.config import config
import json
import logging

logger = logging.getLogger(__name__)

class MistralOCRService:
    """
    Servicio para integración con Mistral OCR API
    Proporciona capacidades avanzadas de OCR con IA para procesamiento de documentos
    """
    
    def __init__(self):
        self.api_key = config.MISTRAL_API_KEY
        if not self.api_key:
            raise ValueError("MISTRAL_API_KEY no está configurada en las variables de entorno")
        
        self.client = Mistral(api_key=self.api_key)
        self.model = "mistral-ocr-latest"
    
    def encode_file_to_base64(self, file_path: str) -> str:
        """
        Codifica un archivo a base64 para envío a la API
        
        Args:
            file_path: Ruta del archivo a codificar
            
        Returns:
            String base64 del archivo
        """
        try:
            with open(file_path, "rb") as file:
                return base64.b64encode(file.read()).decode('utf-8')
        except FileNotFoundError:
            logger.error(f"Archivo no encontrado: {file_path}")
            raise
        except Exception as e:
            logger.error(f"Error codificando archivo: {e}")
            raise
    
    def process_pdf_document(self, file_path: str, include_images: bool = True) -> Dict[str, Any]:
        """
        Procesa un documento PDF usando Mistral OCR
        
        Args:
            file_path: Ruta del archivo PDF
            include_images: Si incluir imágenes en base64 en la respuesta
            
        Returns:
            Diccionario con los datos extraídos del documento
        """
        try:
            # Codificar PDF a base64
            base64_pdf = self.encode_file_to_base64(file_path)
            
            # Procesar con Mistral OCR
            ocr_response = self.client.ocr.process(
                model=self.model,
                document={
                    "type": "document_url",
                    "document_url": f"data:application/pdf;base64,{base64_pdf}"
                },
                include_image_base64=include_images
            )
            
            logger.info(f"Documento procesado exitosamente: {file_path}")
            return self._parse_ocr_response(ocr_response)
            
        except Exception as e:
            logger.error(f"Error procesando PDF con Mistral OCR: {e}")
            raise
    
    def process_image_document(self, file_path: str, include_images: bool = True) -> Dict[str, Any]:
        """
        Procesa una imagen usando Mistral OCR
        
        Args:
            file_path: Ruta del archivo de imagen
            include_images: Si incluir imágenes en base64 en la respuesta
            
        Returns:
            Diccionario con los datos extraídos de la imagen
        """
        try:
            # Determinar el tipo MIME de la imagen
            file_extension = os.path.splitext(file_path)[1].lower()
            mime_types = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.avif': 'image/avif'
            }
            
            mime_type = mime_types.get(file_extension, 'image/jpeg')
            
            # Codificar imagen a base64
            base64_image = self.encode_file_to_base64(file_path)
            
            # Procesar con Mistral OCR
            ocr_response = self.client.ocr.process(
                model=self.model,
                document={
                    "type": "image_url",
                    "image_url": f"data:{mime_type};base64,{base64_image}"
                },
                include_image_base64=include_images
            )
            
            logger.info(f"Imagen procesada exitosamente: {file_path}")
            return self._parse_ocr_response(ocr_response)
            
        except Exception as e:
            logger.error(f"Error procesando imagen con Mistral OCR: {e}")
            raise
    
    def process_document_from_url(self, document_url: str, include_images: bool = True) -> Dict[str, Any]:
        """
        Procesa un documento desde una URL
        
        Args:
            document_url: URL del documento a procesar
            include_images: Si incluir imágenes en base64 en la respuesta
            
        Returns:
            Diccionario con los datos extraídos del documento
        """
        try:
            ocr_response = self.client.ocr.process(
                model=self.model,
                document={
                    "type": "document_url",
                    "document_url": document_url
                },
                include_image_base64=include_images
            )
            
            logger.info(f"Documento desde URL procesado exitosamente: {document_url}")
            return self._parse_ocr_response(ocr_response)
            
        except Exception as e:
            logger.error(f"Error procesando documento desde URL con Mistral OCR: {e}")
            raise
    
    def _parse_ocr_response(self, ocr_response) -> Dict[str, Any]:
        """
        Parsea la respuesta de Mistral OCR y extrae información estructurada
        
        Args:
            ocr_response: Respuesta de la API de Mistral OCR
            
        Returns:
            Diccionario con datos estructurados extraídos
        """
        try:
            # Extraer el contenido markdown del documento
            pages_content = []
            extracted_images = []
            
            if hasattr(ocr_response, 'pages') and ocr_response.pages:
                for page in ocr_response.pages:
                    if hasattr(page, 'markdown'):
                        pages_content.append(page.markdown)
                    
                    # Extraer imágenes si están disponibles
                    if hasattr(page, 'images') and page.images:
                        for img in page.images:
                            extracted_images.append({
                                'id': getattr(img, 'id', None),
                                'top_left_x': getattr(img, 'top_left_x', None),
                                'top_left_y': getattr(img, 'top_left_y', None),
                                'bottom_right_x': getattr(img, 'bottom_right_x', None),
                                'bottom_right_y': getattr(img, 'bottom_right_y', None),
                                'image_base64': getattr(img, 'image_base64', None)
                            })
            
            # Combinar todo el contenido de texto
            full_text = '\n\n'.join(pages_content)
            
            return {
                'success': True,
                'full_text': full_text,
                'pages_content': pages_content,
                'extracted_images': extracted_images,
                'page_count': len(pages_content),
                'image_count': len(extracted_images)
            }
            
        except Exception as e:
            logger.error(f"Error parseando respuesta de Mistral OCR: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def extract_invoice_data_with_ai(self, ocr_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrae datos específicos de factura usando el texto procesado por Mistral OCR
        
        Args:
            ocr_result: Resultado del procesamiento OCR
            
        Returns:
            Diccionario con datos estructurados de la factura
        """
        if not ocr_result.get('success', False):
            raise ValueError("El resultado OCR no es válido")
        
        full_text = ocr_result.get('full_text', '')
        
        # Usar Mistral para extraer datos estructurados de la factura
        try:
            # Crear prompt para extracción de datos de factura
            extraction_prompt = f"""
            Analiza el siguiente texto extraído de una factura y extrae la información en formato JSON.
            
            Texto de la factura:
            {full_text}
            
            Extrae la siguiente información y devuélvela en formato JSON:
            {{
                "invoice_number": "número de factura",
                "invoice_date": "fecha de la factura (formato DD/MM/YYYY)",
                "due_date": "fecha de vencimiento (formato DD/MM/YYYY)",
                "supplier_name": "nombre del proveedor/emisor",
                "supplier_vat": "CIF/NIF del proveedor",
                "customer_name": "nombre del cliente",
                "customer_vat": "CIF/NIF del cliente",
                "total_amount": "importe total (número)",
                "tax_amount": "importe de impuestos (número)",
                "subtotal": "subtotal sin impuestos (número)",
                "currency": "moneda",
                "payment_terms": "condiciones de pago",
                "line_items": [
                    {{
                        "description": "descripción del producto/servicio",
                        "quantity": "cantidad (número)",
                        "unit_price": "precio unitario (número)",
                        "total_price": "precio total de la línea (número)"
                    }}
                ]
            }}
            
            Si algún campo no se encuentra, usa null. Asegúrate de que la respuesta sea JSON válido.
            """
            
            # Usar Mistral Chat API para procesar el prompt
            chat_response = self.client.chat.complete(
                model="mistral-large-latest",
                messages=[
                    {
                        "role": "user",
                        "content": extraction_prompt
                    }
                ],
                response_format={"type": "json_object"}
            )
            
            # Extraer y parsear la respuesta JSON
            response_content = chat_response.choices[0].message.content
            
            try:
                extracted_data = json.loads(response_content)
            except json.JSONDecodeError as e:
                logger.warning(f"Error parseando JSON de Mistral: {e}. Respuesta: {response_content}")
                # Fallback con estructura básica
                extracted_data = {
                    'invoice_number': None,
                    'invoice_date': None,
                    'due_date': None,
                    'supplier_name': None,
                    'supplier_vat': None,
                    'customer_name': None,
                    'customer_vat': None,
                    'total_amount': 0.0,
                    'tax_amount': 0.0,
                    'subtotal': 0.0,
                    'currency': 'EUR',
                    'payment_terms': None,
                    'line_items': []
                }
            
            return {
                'extracted_data': extracted_data,
                'full_text': full_text,
                'confidence': 'high'  # Mistral OCR tiene alta precisión
            }
            
        except Exception as e:
            logger.error(f"Error extrayendo datos de factura con IA: {e}")
            raise
    
    def get_supported_formats(self) -> List[str]:
        """
        Retorna los formatos de archivo soportados por Mistral OCR
        
        Returns:
            Lista de extensiones de archivo soportadas
        """
        return [
            '.pdf', '.png', '.jpg', '.jpeg', '.avif',
            '.pptx', '.docx'
        ]
    
    def validate_file_size(self, file_path: str) -> bool:
        """
        Valida que el archivo no exceda el límite de 50MB de Mistral OCR
        
        Args:
            file_path: Ruta del archivo a validar
            
        Returns:
            True si el archivo es válido, False en caso contrario
        """
        try:
            file_size = os.path.getsize(file_path)
            max_size = 50 * 1024 * 1024  # 50MB en bytes
            return file_size <= max_size
        except Exception as e:
            logger.error(f"Error validando tamaño de archivo: {e}")
            return False

# Instancia global del servicio (lazy loading)
_mistral_ocr_service = None

def get_mistral_ocr_service() -> MistralOCRService:
    """Obtiene la instancia del servicio Mistral OCR (lazy loading)"""
    global _mistral_ocr_service
    if _mistral_ocr_service is None:
        _mistral_ocr_service = MistralOCRService()
    return _mistral_ocr_service