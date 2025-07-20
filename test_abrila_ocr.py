#!/usr/bin/env python3
"""
Script de prueba para verificar la extracción de datos de facturas ABRILA con OCR optimizado
"""
import os
import json
import logging
from api.ocr_optimizado import extract_text_from_pdf, extract_structured_data

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_abrila_extraction(pdf_path):
    """
    Prueba la extracción de datos de una factura ABRILA
    
    Args:
        pdf_path: Ruta al archivo PDF de la factura
    """
    if not os.path.exists(pdf_path):
        logger.error(f"El archivo {pdf_path} no existe")
        return
    
    logger.info(f"Procesando factura ABRILA: {pdf_path}")
    
    # Extraer texto con OCR optimizado
    text, doc_type = extract_text_from_pdf(pdf_path, detect_type=True)
    
    logger.info(f"Tipo de documento detectado: {doc_type}")
    logger.info(f"Longitud del texto extraído: {len(text)} caracteres")
    
    # Forzar el tipo de documento a 'abrila' para asegurar el procesamiento correcto
    structured_data = extract_structured_data(text, doc_type='abrila')
    
    # Mostrar resultados
    logger.info("Datos estructurados extraídos:")
    logger.info(f"Número de factura: {structured_data.get('invoice_number')}")
    logger.info(f"Fecha de factura: {structured_data.get('invoice_date')}")
    logger.info(f"Proveedor: {structured_data.get('supplier_name')}")
    logger.info(f"CIF/NIF proveedor: {structured_data.get('supplier_vat')}")
    logger.info(f"Cliente: {structured_data.get('customer_name')}")
    logger.info(f"CIF/NIF cliente: {structured_data.get('customer_vat')}")
    logger.info(f"Base imponible: {structured_data.get('base_imponible')}")
    logger.info(f"IVA: {structured_data.get('iva_amount')}")
    logger.info(f"Total: {structured_data.get('total_amount')}")
    
    # Mostrar líneas de productos
    logger.info(f"Líneas de productos encontradas: {len(structured_data.get('lines', []))}")
    for i, line in enumerate(structured_data.get('lines', []), 1):
        logger.info(f"Línea {i}:")
        logger.info(f"  - Código: {line.get('product_code')}")
        logger.info(f"  - Descripción: {line.get('name')}")
        logger.info(f"  - Cantidad: {line.get('quantity')}")
        logger.info(f"  - Precio unitario: {line.get('price_unit')}")
        logger.info(f"  - Descuento: {line.get('discount')}%")
        logger.info(f"  - Subtotal: {line.get('price_subtotal')}")
    
    # Guardar resultados en un archivo JSON para análisis posterior
    output_file = os.path.splitext(pdf_path)[0] + "_result.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(structured_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Resultados guardados en {output_file}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        logger.error("Uso: python test_abrila_ocr.py <ruta_al_pdf>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    test_abrila_extraction(pdf_path)
