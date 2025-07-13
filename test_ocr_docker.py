"""
Script de prueba para verificar el servicio OCR refactorizado dentro del contenedor Docker
"""
import os
import json
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Importar el servicio OCR refactorizado
from api.services.mistral_free_ocr_service_refactored import MistralFreeOCRService

def test_ocr_service():
    """
    Prueba el servicio OCR refactorizado con una factura de ejemplo
    """
    # Ruta a la factura de ejemplo
    factura_path = '/app/ejemplos/NEVIR - FacturaF2402846.pdf'
    
    if not os.path.exists(factura_path):
        logger.error(f'No se encontró el archivo de factura: {factura_path}')
        return
    
    logger.info(f'Procesando factura: {factura_path}')
    
    try:
        # Crear instancia del servicio OCR refactorizado
        ocr_service = MistralFreeOCRService()
        
        # Procesar la factura
        result = ocr_service.process_invoice_file(factura_path)
        
        # Guardar resultado en un archivo JSON para análisis
        output_path = '/app/ocr_docker_result.json'
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        logger.info(f'Resultado guardado en: {output_path}')
        
        # Mostrar datos principales extraídos
        if result.get('success', False):
            logger.info('✅ Procesamiento OCR exitoso')
            
            invoice_data = result.get('invoice_data', {})
            logger.info('Datos principales extraídos:')
            logger.info(f'- Número de factura: {invoice_data.get("invoice_number", "No encontrado")}')
            logger.info(f'- Fecha: {invoice_data.get("invoice_date", "No encontrada")}')
            logger.info(f'- Proveedor: {invoice_data.get("supplier_name", "No encontrado")}')
            logger.info(f'- Total: {invoice_data.get("total_amount", "No encontrado")}')
            
            # Mostrar líneas de factura si existen
            lines = invoice_data.get('line_items', [])
            if lines:
                logger.info(f'- Líneas de factura: {len(lines)}')
                for i, line in enumerate(lines[:3], 1):
                    logger.info(f'  {i}. {line.get("name", "Sin descripción")} - {line.get("quantity", 0)} x {line.get("price_unit", 0)} = {line.get("quantity", 0) * line.get("price_unit", 0)}')
                if len(lines) > 3:
                    logger.info(f'  ... y {len(lines) - 3} líneas más')
        else:
            logger.error(f'❌ Error en procesamiento OCR: {result.get("error", "Error desconocido")}')
    
    except Exception as e:
        logger.exception(f'Error inesperado: {str(e)}')

if __name__ == '__main__':
    test_ocr_service()
