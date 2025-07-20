"""
Servicio de OCR gratuito con Mistral AI - Versión refactorizada
Actúa como fachada para los servicios especializados de OCR y procesamiento de documentos
"""
import logging
from typing import Dict, Any, Optional, List, Tuple
import base64

# Importar servicios especializados
from .mistral_ocr_models import InvoiceLine, OdooInvoice
from .mistral_ocr_client import mistral_ocr_client
from .document_processing_service import document_processing_service
from .invoice_extraction_service import invoice_extraction_service
from .json_extraction_service import extract_json_from_text
from .ocr_validator import OCRValidator

logger = logging.getLogger(__name__)

class MistralFreeOCRService:
    """
    Servicio de OCR gratuito con Mistral AI
    Actúa como fachada para los servicios especializados
    """
    
    def __init__(self):
        """Inicializa el servicio de OCR"""
        logger.info("Inicializando servicio de OCR gratuito con Mistral")
    
    def get_supported_formats(self) -> list[str]:
        """
        Devuelve los formatos de archivo soportados
        
        Returns:
            list[str]: Lista con las extensiones soportadas
        """
        return ['.pdf', '.jpg', '.jpeg', '.png']
    
    def validate_file_size(self, file_path: str) -> bool:
        """
        Valida que el archivo no exceda el límite de tamaño (50MB)
        
        Args:
            file_path: Ruta al archivo cuyo tamaño se va a validar
            
        Returns:
            bool: True si el tamaño es válido, False en caso contrario
        """
        import os
        import logging
        
        logger = logging.getLogger(__name__)
        
        try:
            # Obtener el tamaño del archivo en bytes usando os.path.getsize
            if not os.path.exists(file_path):
                logger.error(f"El archivo {file_path} no existe")
                return False
                
            file_size = os.path.getsize(file_path)
            
            # Asegurarse de que file_size sea un número
            if not isinstance(file_size, (int, float)):
                file_size = int(file_size)
                
            max_size_mb = 50
            file_size_mb = file_size / (1024 * 1024)
            
            logger.info(f"Tamaño del archivo: {file_size_mb:.2f} MB (máximo permitido: {max_size_mb} MB)")
            
            return file_size_mb <= max_size_mb
        except (ValueError, TypeError) as e:
            logger.error(f"Error al validar el tamaño del archivo: {e}")
            return False
    
    def process_invoice_file(self, file_path: str, provider_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Procesa un archivo de factura (PDF o imagen) y extrae datos estructurados
        usando la API de Mistral Chat y luego mejora los resultados
        con un agente especializado en análisis de facturas
        
        Args:
            file_path: Ruta al archivo de factura
            provider_info: Información previa del proveedor (opcional)
            
        Returns:
            Dict[str, Any]: Diccionario con los resultados del procesamiento
        """
        try:
            import os
            import mimetypes
            
            # Validar tamaño de archivo
            if not self.validate_file_size(file_path):
                return {
                    'success': False,
                    'error': "El archivo excede el límite de tamaño"
                }
            
            # Detectar tipo MIME
            content_type, _ = mimetypes.guess_type(file_path)
            if not content_type:
                if file_path.lower().endswith('.pdf'):
                    content_type = 'application/pdf'
                elif file_path.lower().endswith(('.jpg', '.jpeg')):
                    content_type = 'image/jpeg'
                elif file_path.lower().endswith('.png'):
                    content_type = 'image/png'
                else:
                    return {
                        'success': False,
                        'error': "Formato de archivo no soportado"
                    }
            
            # Leer contenido del archivo
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            logger.info(f"Procesando archivo de factura: {file_path} (tipo: {content_type})")
            
            # Paso 1: Procesar archivo a imágenes base64
            base64_images = document_processing_service.process_file_to_base64_images(file_content, content_type)
            if not base64_images:
                return {
                    'success': False,
                    'error': "No se pudieron extraer imágenes del archivo"
                }
            
            # Paso 2: Extraer texto OCR de la primera imagen (por ahora solo procesamos la primera página)
            ocr_text = mistral_ocr_client.extract_text_from_image(base64_images[0])
            if not ocr_text:
                return {
                    'success': False,
                    'error': "No se pudo extraer texto OCR de la imagen"
                }
            
            # Paso 3: Extraer datos estructurados del texto OCR
            initial_data = invoice_extraction_service.extract_invoice_data_from_text(ocr_text)
            
            # Guardar los datos crudos de OCR para análisis antes de cualquier modificación
            raw_ocr_data = initial_data.copy()
            
            # Paso 3: Incorporar información previa del proveedor si existe
            # IMPORTANTE: Estos datos son proporcionados por un humano y tienen prioridad
            if provider_info:
                logger.info(f"Incorporando información confiable del proveedor: {provider_info}")
                # Inyectamos los datos confiables del proveedor en los datos iniciales
                if 'supplier_name' in provider_info:
                    initial_data['supplier_name'] = provider_info['supplier_name']
                    # Marcamos este campo como verificado por humano
                    initial_data['supplier_name_verified'] = True
                if 'supplier_vat' in provider_info:
                    initial_data['supplier_vat'] = provider_info['supplier_vat']
                    # Marcamos este campo como verificado por humano
                    initial_data['supplier_vat_verified'] = True
                # Si tenemos datos del cliente (opcional)
                if 'customer_name' in provider_info:
                    initial_data['customer_name'] = provider_info['customer_name']
                    initial_data['customer_name_verified'] = True
                if 'customer_vat' in provider_info:
                    initial_data['customer_vat'] = provider_info['customer_vat']
                    initial_data['customer_vat_verified'] = True
                # Si tenemos número de factura verificado
                if 'invoice_number' in provider_info:
                    initial_data['invoice_number'] = provider_info['invoice_number']
                    initial_data['invoice_number_verified'] = True
                    logger.info(f"Número de factura verificado por humano: {provider_info['invoice_number']}")
                
                # Registrar todos los campos verificados por humano
                verified_fields = [k.replace('_verified', '') for k in initial_data.keys() if k.endswith('_verified')]
                if verified_fields:
                    logger.info(f"Campos verificados por humano: {', '.join(verified_fields)}")
                else:
                    logger.info("No se proporcionaron campos verificados por humano")
            
            # Paso 4: Mejorar los datos con un agente especializado en facturas
            logger.info("Mejorando datos con agente especializado en facturas")
            enhanced_data = mistral_ocr_client.process_with_invoice_agent(ocr_text, initial_data, provider_info)
            
            # Generar un ID único para esta extracción OCR
            import datetime
            import os
            ocr_id = f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{os.path.basename(file_path)}"
            
            # Validar los datos extraídos con OCRValidator
            logger.info("Validando datos extraídos con OCRValidator")
            validator = OCRValidator()
            enhanced_data = validator.validate_invoice_data(enhanced_data)
            
            # Devolver resultados incluyendo datos crudos para análisis
            return {
                'success': True,
                'invoice_data': enhanced_data,
                'raw_ocr_data': raw_ocr_data,  # Datos crudos del OCR inicial
                'raw_ocr_text': ocr_text,      # Texto OCR completo
                'ocr_confidence': 'unknown',    # Por ahora no tenemos esta métrica
                'ocr_id': ocr_id
            }
            
        except Exception as e:
            logger.error(f"Error procesando archivo de factura: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _extract_ocr_text(self, image_base64: str) -> str:
        """
        Extrae texto OCR de una imagen base64
        
        Args:
            image_base64: Imagen en formato base64
            
        Returns:
            str: Texto extraído de la imagen
        """
        return mistral_ocr_client.extract_text_from_image(image_base64)
    
    def _process_with_invoice_agent(self, ocr_text: str, initial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa el texto OCR con el modelo de chat de Mistral para mejorar y completar los datos extraídos
        
        Args:
            ocr_text: Texto extraído por OCR
            initial_data: Datos iniciales extraídos
            
        Returns:
            Dict[str, Any]: Datos mejorados
        """
        return mistral_ocr_client.process_with_invoice_agent(ocr_text, initial_data)
    
    def _extract_json_from_text(self, text: str) -> Dict[str, Any]:
        """
        Extrae objeto JSON de un texto, maneja casos donde el JSON está embebido en markdown
        
        Args:
            text: Texto que puede contener JSON
            
        Returns:
            Dict[str, Any]: Objeto JSON extraído o diccionario vacío si no se encuentra
        """
        return extract_json_from_text(text)
    
    def _extract_invoice_data_from_text(self, text: str) -> Dict[str, Any]:
        """
        Extrae datos estructurados de factura desde texto OCR markdown
        
        Args:
            text: Texto OCR extraído del documento
            
        Returns:
            Dict[str, Any]: Datos estructurados de la factura
        """
        return invoice_extraction_service.extract_invoice_data_from_text(text)

# Singleton para evitar múltiples instancias
_mistral_free_ocr_service = None

def get_mistral_free_ocr_service() -> MistralFreeOCRService:
    """
    Devuelve una instancia única del servicio de OCR
    
    Returns:
        MistralFreeOCRService: Instancia del servicio
    """
    global _mistral_free_ocr_service
    if _mistral_free_ocr_service is None:
        _mistral_free_ocr_service = MistralFreeOCRService()
    return _mistral_free_ocr_service
