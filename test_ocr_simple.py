#!/usr/bin/env python3
"""
Script de prueba simplificado para verificar el funcionamiento del servicio OCR refactorizado
"""
import os
import sys
import json
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Añadir el directorio raíz al path para importar los módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar los servicios refactorizados directamente
from api.services.mistral_ocr_client import mistral_ocr_client
from api.services.document_processing_service import document_processing_service
from api.services.invoice_extraction_service import invoice_extraction_service

def test_ocr_components():
    """
    Prueba los componentes individuales del servicio OCR refactorizado
    """
    # Ruta a la factura de ejemplo
    factura_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "ejemplos",
        "NEVIR - FacturaF2402846.pdf"
    )
    
    if not os.path.exists(factura_path):
        logger.error(f"No se encontró el archivo de factura: {factura_path}")
        return
    
    logger.info(f"Procesando factura: {factura_path}")
    
    try:
        # Paso 1: Leer el archivo
        with open(factura_path, 'rb') as f:
            file_content = f.read()
        
        # Paso 2: Procesar el archivo a imágenes base64
        base64_images = document_processing_service.process_file_to_base64_images(
            file_content, 
            'application/pdf'
        )
        
        if not base64_images:
            logger.error("No se pudieron extraer imágenes del archivo")
            return
        
        logger.info(f"✅ Extracción de imágenes exitosa: {len(base64_images)} imágenes")
        
        # Paso 3: Extraer texto OCR de la primera imagen
        ocr_text = mistral_ocr_client.extract_text_from_image(base64_images[0])
        
        if not ocr_text:
            logger.error("No se pudo extraer texto OCR de la imagen")
            return
        
        logger.info(f"✅ Extracción de texto OCR exitosa: {len(ocr_text)} caracteres")
        logger.info(f"Primeros 200 caracteres del texto OCR: {ocr_text[:200]}...")
        
        # Paso 4: Extraer datos estructurados del texto OCR
        initial_data = invoice_extraction_service.extract_invoice_data_from_text(ocr_text)
        logger.info(f"✅ Extracción inicial de datos exitosa")
        
        # Paso 5: Procesar con agente de facturas para mejorar los datos
        enhanced_data = mistral_ocr_client.process_with_invoice_agent(ocr_text, initial_data)
        logger.info(f"✅ Procesamiento con agente de facturas exitoso")
        
        # Guardar resultado en un archivo JSON para análisis
        result = {
            'success': True,
            'invoice_data': enhanced_data,
            'ocr_text': ocr_text[:500] + "..." if len(ocr_text) > 500 else ocr_text
        }
        
        output_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "ocr_test_result.json"
        )
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Resultado guardado en: {output_path}")
        
        # Mostrar datos principales extraídos
        logger.info("Datos principales extraídos:")
        logger.info(f"- Número de factura: {enhanced_data.get('invoice_number', 'No encontrado')}")
        logger.info(f"- Fecha: {enhanced_data.get('invoice_date', 'No encontrada')}")
        logger.info(f"- Proveedor: {enhanced_data.get('supplier_name', 'No encontrado')}")
        logger.info(f"- Total: {enhanced_data.get('total_amount', 'No encontrado')}")
        
        # Mostrar líneas de factura si existen
        lines = enhanced_data.get('line_items', [])
        if lines:
            logger.info(f"- Líneas de factura: {len(lines)}")
            for i, line in enumerate(lines[:3], 1):
                logger.info(f"  {i}. {line.get('description', 'Sin descripción')} - {line.get('qty', 0)} x {line.get('price_unit', 0)} = {line.get('subtotal', 0)}")
            if len(lines) > 3:
                logger.info(f"  ... y {len(lines) - 3} líneas más")
                
    except Exception as e:
        logger.error(f"❌ Error en procesamiento OCR: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    test_ocr_components()
