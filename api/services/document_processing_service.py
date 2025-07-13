"""
Servicio para procesamiento de documentos (PDF, imágenes) para OCR
"""
import os
import base64
import logging
import tempfile
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path
from pdf2image import convert_from_path
from PIL import Image
import io

logger = logging.getLogger(__name__)

class DocumentProcessingService:
    """Servicio para procesar documentos PDF e imágenes para OCR"""
    
    def __init__(self):
        """Inicializa el servicio de procesamiento de documentos"""
        self.supported_formats = {
            'pdf': ['application/pdf'],
            'image': ['image/jpeg', 'image/png', 'image/jpg', 'image/webp']
        }
        self.max_file_size = 10 * 1024 * 1024  # 10 MB
    
    def get_supported_formats(self) -> Dict[str, List[str]]:
        """
        Devuelve los formatos de archivo soportados
        
        Returns:
            Dict[str, List[str]]: Diccionario con los formatos soportados
        """
        return self.supported_formats
    
    def validate_file_size(self, file_size: int) -> bool:
        """
        Valida que el tamaño del archivo no exceda el límite
        
        Args:
            file_size: Tamaño del archivo en bytes
            
        Returns:
            bool: True si el tamaño es válido, False en caso contrario
        """
        return file_size <= self.max_file_size
    
    def process_file_to_base64_images(self, file_content: bytes, content_type: str) -> List[str]:
        """
        Procesa un archivo (PDF o imagen) y lo convierte en una lista de imágenes base64
        
        Args:
            file_content: Contenido del archivo en bytes
            content_type: Tipo MIME del archivo
            
        Returns:
            List[str]: Lista de imágenes en formato base64
        """
        try:
            # Verificar si es un PDF
            if content_type in self.supported_formats['pdf']:
                return self._process_pdf(file_content)
            # Verificar si es una imagen
            elif content_type in self.supported_formats['image']:
                return self._process_image(file_content)
            else:
                logger.error(f"Formato no soportado: {content_type}")
                return []
        except Exception as e:
            logger.error(f"Error procesando archivo: {str(e)}")
            return []
    
    def _process_pdf(self, pdf_content: bytes) -> List[str]:
        """
        Procesa un archivo PDF y extrae sus páginas como imágenes base64
        
        Args:
            pdf_content: Contenido del PDF en bytes
            
        Returns:
            List[str]: Lista de imágenes en formato base64
        """
        try:
            # Crear un archivo temporal para el PDF
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_file.write(pdf_content)
                temp_file_path = temp_file.name
            
            # Convertir PDF a imágenes usando pdf2image
            images = convert_from_path(temp_file_path)
            base64_images = []
            
            # Procesar cada página
            for img in images:
                # Guardar imagen en un buffer de memoria
                img_buffer = io.BytesIO()
                img.save(img_buffer, format='PNG')
                img_buffer.seek(0)
                
                # Convertir a base64
                base64_image = base64.b64encode(img_buffer.read()).decode('utf-8')
                base64_images.append(base64_image)
            
            # Eliminar archivo temporal
            os.unlink(temp_file_path)
            
            logger.info(f"PDF procesado: {len(base64_images)} páginas extraídas")
            return base64_images
            
        except Exception as e:
            logger.error(f"Error procesando PDF: {str(e)}")
            return []
    
    def _process_image(self, image_content: bytes) -> List[str]:
        """
        Procesa una imagen y la convierte a formato base64
        
        Args:
            image_content: Contenido de la imagen en bytes
            
        Returns:
            List[str]: Lista con la imagen en formato base64
        """
        try:
            # Abrir la imagen con PIL
            img = Image.open(io.BytesIO(image_content))
            
            # Convertir a RGB si es necesario (para imágenes con transparencia)
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])  # 3 es el canal alfa
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Guardar como bytes PNG
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            # Convertir a base64
            base64_image = base64.b64encode(img_byte_arr).decode('utf-8')
            
            logger.info("Imagen procesada correctamente")
            return [base64_image]
            
        except Exception as e:
            logger.error(f"Error procesando imagen: {str(e)}")
            return []

# Instancia global del servicio
document_processing_service = DocumentProcessingService()
