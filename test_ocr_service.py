#!/usr/bin/env python3
"""
Script de prueba para verificar el funcionamiento del servicio OCR refactorizado
"""
import os
import json
import logging
from api.services.mistral_free_ocr_service import get_mistral_free_ocr_service

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_ocr_service():
    """
    Prueba el servicio OCR con una factura de ejemplo
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
    
    # Obtener el servicio OCR
    ocr_service = get_mistral_free_ocr_service()
    
    # Procesar la factura
    result = ocr_service.process_invoice_file(factura_path)
    
    # Verificar el resultado
    if result.get('success', False):
        logger.info("✅ Procesamiento OCR exitoso")
        
        # Guardar resultado en un archivo JSON para análisis
        output_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "ocr_test_result.json"
        )
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Resultado guardado en: {output_path}")
        
        # Mostrar datos principales extraídos
        invoice_data = result.get('invoice_data', {})
        logger.info("Datos principales extraídos:")
        logger.info(f"- Número de factura: {invoice_data.get('invoice_number', 'No encontrado')}")
        logger.info(f"- Fecha: {invoice_data.get('invoice_date', 'No encontrada')}")
        logger.info(f"- Proveedor: {invoice_data.get('supplier_name', 'No encontrado')}")
        logger.info(f"- Total: {invoice_data.get('total_amount', 'No encontrado')}")
        
        # Mostrar líneas de factura si existen
        lines = invoice_data.get('line_items', [])
        if lines:
            logger.info(f"- Líneas de factura: {len(lines)}")
            for i, line in enumerate(lines[:3], 1):
                logger.info(f"  {i}. {line.get('description', 'Sin descripción')} - {line.get('qty', 0)} x {line.get('price_unit', 0)} = {line.get('subtotal', 0)}")
            if len(lines) > 3:
                logger.info(f"  ... y {len(lines) - 3} líneas más")
    else:
        logger.error(f"❌ Error en procesamiento OCR: {result.get('error', 'Error desconocido')}")

if __name__ == "__main__":
    test_ocr_service()
