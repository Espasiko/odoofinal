#!/usr/bin/env python3
"""
Script para probar el endpoint de OCR optimizado
"""
import os
import sys
import json
import requests
import time
from pathlib import Path

# Configuración
API_URL = "http://localhost:8000/api/v1/invoice"

def test_ocr_endpoint(pdf_path, ocr_method="auto"):
    """
    Prueba el endpoint de OCR con un archivo PDF
    
    Args:
        pdf_path: Ruta al archivo PDF
        ocr_method: Método de OCR a utilizar ('auto', 'tesseract', 'pdfxchange')
    """
    if not os.path.exists(pdf_path):
        print(f"Error: El archivo {pdf_path} no existe")
        return
    
    print(f"Probando endpoint con {pdf_path} usando método {ocr_method}")
    
    # Preparar la solicitud
    with open(pdf_path, "rb") as f:
        files = {"file": (os.path.basename(pdf_path), f, "application/pdf")}
        data = {"ocr_method": ocr_method}
        
        # Medir tiempo
        start_time = time.time()
        
        # Enviar solicitud
        try:
            response = requests.post(API_URL, files=files, data=data)
            
            # Calcular tiempo
            elapsed_time = time.time() - start_time
            
            # Verificar respuesta
            if response.status_code == 200:
                result = response.json()
                
                # Guardar resultado en archivo JSON
                output_dir = Path("resultados_ocr") / Path(pdf_path).stem
                output_dir.mkdir(parents=True, exist_ok=True)
                
                output_file = output_dir / f"endpoint_result_{ocr_method}.json"
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                
                # Mostrar resumen
                print(f"\nRespuesta exitosa ({elapsed_time:.2f} segundos)")
                print(f"Método utilizado: {result.get('method_used', 'desconocido')}")
                print(f"Calidad OCR: {result.get('ocr_quality', 0):.2f}")
                
                # Mostrar datos extraídos
                invoice_data = result.get("invoice_data", {})
                if invoice_data:
                    print("\nDatos extraídos:")
                    for key, value in invoice_data.items():
                        if isinstance(value, dict) or isinstance(value, list):
                            print(f"  {key}: {json.dumps(value, ensure_ascii=False)[:100]}...")
                        else:
                            print(f"  {key}: {value}")
                
                print(f"\nResultado completo guardado en {output_file}")
            else:
                print(f"Error: {response.status_code} - {response.text}")
        
        except Exception as e:
            print(f"Error en la solicitud: {e}")

def main():
    """Función principal"""
    if len(sys.argv) < 2:
        print("Uso: python test_endpoint_ocr.py <ruta_archivo_pdf> [método_ocr]")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    ocr_method = sys.argv[2] if len(sys.argv) > 2 else "auto"
    
    test_ocr_endpoint(pdf_path, ocr_method)

if __name__ == "__main__":
    main()