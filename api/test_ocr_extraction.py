#!/usr/bin/env python3
"""
Script de prueba para extraer datos crudos de OCR y Tabula de una factura
"""
import os
import sys
import json
import logging
import base64
from pathlib import Path
from typing import Dict, Any

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Añadir el directorio raíz al path para poder importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar servicios necesarios
from api.services.document_processing_service import document_processing_service
from api.services.mistral_ocr_client import mistral_ocr_client
from api.services.invoice_extraction_service import invoice_extraction_service
from api.services.tabula_extraction_service import TabulaExtractionService

def process_invoice(file_path: str) -> Dict[str, Any]:
    """
    Procesa una factura y devuelve los datos crudos extraídos por OCR y Tabula
    """
    if not os.path.exists(file_path):
        logger.error(f"El archivo {file_path} no existe")
        return {"error": f"El archivo {file_path} no existe"}
    
    try:
        # Determinar el tipo de contenido
        content_type = None
        if file_path.lower().endswith('.pdf'):
            content_type = 'application/pdf'
        elif file_path.lower().endswith(('.jpg', '.jpeg')):
            content_type = 'image/jpeg'
        elif file_path.lower().endswith('.png'):
            content_type = 'image/png'
        else:
            return {"error": "Formato de archivo no soportado"}
        
        # Leer contenido del archivo
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        logger.info(f"Procesando archivo: {file_path} (tipo: {content_type})")
        
        # PASO 1: Extraer datos crudos de OCR
        # Procesar archivo a imágenes base64
        base64_images = document_processing_service.process_file_to_base64_images(file_content, content_type)
        if not base64_images:
            return {"error": "No se pudieron extraer imágenes del archivo"}
        
        # Extraer texto OCR de la primera imagen
        ocr_text = mistral_ocr_client.extract_text_from_image(base64_images[0])
        if not ocr_text:
            return {"error": "No se pudo extraer texto OCR de la imagen"}
        
        # Extraer datos estructurados del texto OCR
        ocr_data = invoice_extraction_service.extract_invoice_data_from_text(ocr_text)
        
        # PASO 2: Extraer datos crudos de Tabula (si es PDF)
        tabula_data = {}
        raw_tables = []
        if content_type == 'application/pdf':
            try:
                # Crear instancia del servicio Tabula
                tabula_service = TabulaExtractionService()
                
                # Extraer datos con Tabula
                tabula_data = tabula_service.enhance_invoice_data({}, file_path)
                
                # Extraer tablas crudas
                import tabula
                raw_tables = tabula.read_pdf(file_path, pages='all', multiple_tables=True)
                raw_tables = [table.to_dict() for table in raw_tables]
            except Exception as e:
                logger.error(f"Error al extraer datos con Tabula: {str(e)}")
        
        # Devolver resultados
        return {
            "success": True,
            "raw_ocr_text": ocr_text,
            "raw_ocr_data": ocr_data,
            "raw_tabula_data": tabula_data,
            "raw_tabula_tables": raw_tables
        }
    
    except Exception as e:
        logger.error(f"Error al procesar la factura: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {"error": str(e)}

if __name__ == "__main__":
    # Verificar argumentos
    if len(sys.argv) < 2:
        print("Uso: python test_ocr_extraction.py <ruta_factura>")
        sys.exit(1)
    
    # Procesar factura
    file_path = sys.argv[1]
    result = process_invoice(file_path)
    
    # Guardar resultados en un archivo JSON
    output_file = f"{os.path.splitext(os.path.basename(file_path))[0]}_raw_extraction.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"Resultados guardados en {output_file}")
    
    # Mostrar un resumen
    print("\n=== RESUMEN DE EXTRACCIÓN ===")
    if "error" in result:
        print(f"ERROR: {result['error']}")
    else:
        print(f"OCR Text: {len(result['raw_ocr_text'])} caracteres")
        print(f"OCR Data: {len(result['raw_ocr_data'])} campos")
        print(f"Tabula Data: {len(result['raw_tabula_data'])} campos")
        print(f"Tabula Tables: {len(result['raw_tabula_tables'])} tablas")
        
        # Mostrar campos extraídos por OCR
        print("\n=== CAMPOS EXTRAÍDOS POR OCR ===")
        for key, value in result['raw_ocr_data'].items():
            print(f"{key}: {value}")
        
        # Mostrar campos extraídos por Tabula
        print("\n=== CAMPOS EXTRAÍDOS POR TABULA ===")
        for key, value in result['raw_tabula_data'].items():
            print(f"{key}: {value}")
