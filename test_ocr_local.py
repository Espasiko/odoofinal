#!/usr/bin/env python3
"""
Script para probar el servicio OCR localmente sin depender del servidor FastAPI
"""
import os
import json
import sys
from pprint import pprint

# Añadir el directorio raíz al path para poder importar los módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar el servicio OCR refactorizado
from api.services.mistral_free_ocr_service_refactored import get_mistral_free_ocr_service

def test_ocr_local():
    """
    Prueba el servicio OCR localmente con una factura de ejemplo
    """
    # Ruta a la factura de ejemplo
    factura_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "ejemplos",
        "NEVIR - FacturaF2402846.pdf"
    )
    
    if not os.path.exists(factura_path):
        print(f"Error: No se encontró el archivo de factura: {factura_path}")
        return
    
    print(f"Procesando factura: {factura_path}")
    
    # Obtener instancia del servicio OCR
    ocr_service = get_mistral_free_ocr_service()
    
    try:
        # Procesar la factura
        result = ocr_service.process_invoice_file(factura_path)
        
        # Guardar resultado en un archivo JSON para análisis
        output_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "ocr_local_result.json"
        )
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"Resultado guardado en: {output_path}")
        
        # Mostrar datos principales extraídos
        if result.get("success", False):
            print("✅ Procesamiento OCR exitoso")
            
            invoice_data = result.get("invoice_data", {})
            print("Datos principales extraídos:")
            print(f"- Número de factura: {invoice_data.get('invoice_number', 'No encontrado')}")
            print(f"- Fecha: {invoice_data.get('invoice_date', 'No encontrada')}")
            print(f"- Proveedor: {invoice_data.get('supplier_name', 'No encontrado')}")
            print(f"- Total: {invoice_data.get('total_amount', 'No encontrado')}")
            
            # Mostrar líneas de factura si existen
            lines = invoice_data.get("line_items", [])
            if lines:
                print(f"- Líneas de factura: {len(lines)}")
                for i, line in enumerate(lines[:3], 1):
                    print(f"  {i}. {line.get('name', 'Sin descripción')} - {line.get('quantity', 0)} x {line.get('price_unit', 0)} = {line.get('quantity', 0) * line.get('price_unit', 0)}")
                if len(lines) > 3:
                    print(f"  ... y {len(lines) - 3} líneas más")
        else:
            print(f"❌ Error en procesamiento OCR: {result.get('error', 'Error desconocido')}")
    
    except Exception as e:
        print(f"Error inesperado: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    test_ocr_local()
