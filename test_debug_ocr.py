#!/usr/bin/env python3
"""
Script para probar el endpoint de depuración OCR y analizar los datos crudos
"""
import os
import sys
import json
import requests
from pathlib import Path

def test_debug_ocr(file_path, supplier_name=None, supplier_vat=None, customer_name=None, customer_vat=None, invoice_number=None):
    """
    Prueba el endpoint de depuración OCR con un archivo de factura y datos verificados por humano
    
    Args:
        file_path: Ruta al archivo PDF de la factura
        supplier_name: Nombre del proveedor (verificado por humano)
        supplier_vat: NIF/CIF del proveedor (verificado por humano)
        customer_name: Nombre del cliente (verificado por humano)
        customer_vat: NIF/CIF del cliente (verificado por humano)
        invoice_number: Número de factura (verificado por humano)
    """
    if not os.path.exists(file_path):
        print(f"Error: El archivo {file_path} no existe")
        return
    
    # URL del endpoint de depuración
    url = "http://localhost:8000/api/v1/debug-ocr/process-invoice"
    
    # Preparar los datos del formulario con datos verificados por humano
    data = {}
    if supplier_name:
        data['supplier_name'] = supplier_name
    if supplier_vat:
        data['supplier_vat'] = supplier_vat
    if customer_name:
        data['customer_name'] = customer_name
    if customer_vat:
        data['customer_vat'] = customer_vat
    if invoice_number:
        data['invoice_number'] = invoice_number
    
    # Preparar el archivo
    file_name = os.path.basename(file_path)
    files = {
        'file': (file_name, open(file_path, 'rb'), 'application/pdf')
    }
    
    print(f"Enviando {file_name} al endpoint de depuración OCR...")
    
    # Realizar la petición
    try:
        response = requests.post(url, data=data, files=files)
        response.raise_for_status()
        
        # Guardar la respuesta en un archivo JSON
        output_file = f"{os.path.splitext(file_name)[0]}_debug_ocr.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(response.json(), f, ensure_ascii=False, indent=2)
        
        print(f"Respuesta guardada en {output_file}")
        
        # Mostrar un resumen de los datos extraídos
        result = response.json()
        if result.get('success'):
            print("\n=== RESUMEN DE DATOS EXTRAÍDOS ===")
            
            # Datos finales procesados
            invoice_data = result.get('invoice_data', {})
            print("\n--- DATOS FINALES PROCESADOS ---")
            print(f"Número de factura: {invoice_data.get('invoice_number', 'No disponible')}")
            print(f"Fecha de factura: {invoice_data.get('invoice_date', 'No disponible')}")
            print(f"Proveedor: {invoice_data.get('supplier_name', 'No disponible')} ({invoice_data.get('supplier_vat', 'No disponible')})")
            print(f"Cliente: {invoice_data.get('customer_name', 'No disponible')} ({invoice_data.get('customer_vat', 'No disponible')})")
            print(f"Total: {invoice_data.get('total_amount', 'No disponible')} €")
            print(f"IVA: {invoice_data.get('tax_rate', 'No disponible')}% ({invoice_data.get('tax_amount', 'No disponible')} €)")
            print(f"Recargo de equivalencia: {invoice_data.get('recargo_rate', 'No disponible')}% ({invoice_data.get('recargo_equivalencia', 'No disponible')} €)")
            
            # Datos crudos de OCR
            raw_data = result.get('raw_data', {})
            raw_ocr_data = raw_data.get('ocr_data', {})
            print("\n--- DATOS CRUDOS DE OCR ---")
            for key, value in raw_ocr_data.items():
                if key != 'line_items':
                    print(f"{key}: {value}")
            
            # Datos crudos de Tabula
            raw_tabula_data = raw_data.get('tabula_data', {})
            print("\n--- DATOS CRUDOS DE TABULA ---")
            for key, value in raw_tabula_data.items():
                if key != 'line_items':
                    print(f"{key}: {value}")
            
            # Tablas extraídas por Tabula
            raw_tabula_tables = raw_data.get('tabula_tables', [])
            print(f"\n--- TABLAS EXTRAÍDAS POR TABULA ({len(raw_tabula_tables)}) ---")
            for i, table in enumerate(raw_tabula_tables):
                print(f"\nTabla {i+1}:")
                for col_name, col_data in table.items():
                    print(f"  {col_name}: {col_data}")
            
            # Análisis de discrepancias
            print("\n=== ANÁLISIS DE DISCREPANCIAS ===")
            
            # Verificar IVA y recargo de equivalencia
            if 'tax_rate' in invoice_data and 'tax_rate' in raw_ocr_data:
                if invoice_data['tax_rate'] != raw_ocr_data.get('tax_rate'):
                    print(f"Discrepancia en IVA: OCR={raw_ocr_data.get('tax_rate')}%, Final={invoice_data['tax_rate']}%")
            
            # Verificar total
            if 'total_amount' in invoice_data and 'total_amount' in raw_ocr_data:
                if invoice_data['total_amount'] != raw_ocr_data.get('total_amount'):
                    print(f"Discrepancia en total: OCR={raw_ocr_data.get('total_amount')}€, Final={invoice_data['total_amount']}€")
            
            # Verificar si los datos verificados por humano se respetaron
            print("\n=== VERIFICACIÓN DE DATOS HUMANOS ===")
            verified_fields = [k for k in invoice_data.keys() if k.endswith('_verified') and invoice_data[k] is True]
            
            if verified_fields:
                print("Campos verificados por humano encontrados:")
                for field in verified_fields:
                    base_field = field.replace('_verified', '')
                    if base_field in invoice_data:
                        print(f"  - {base_field}: {invoice_data[base_field]}")
            else:
                print("No se encontraron campos verificados por humano en el resultado.")
                
            # Verificar si los datos proporcionados por el usuario se respetaron
            input_data = {}
            if 'supplier_name' in data:
                input_data['supplier_name'] = data['supplier_name']
            if 'supplier_vat' in data:
                input_data['supplier_vat'] = data['supplier_vat']
            if 'customer_name' in data:
                input_data['customer_name'] = data['customer_name']
            if 'customer_vat' in data:
                input_data['customer_vat'] = data['customer_vat']
            if 'invoice_number' in data:
                input_data['invoice_number'] = data['invoice_number']
                
            if input_data:
                print("\nVerificación de datos proporcionados por el usuario:")
                for field, value in input_data.items():
                    if field in invoice_data:
                        if invoice_data[field] == value:
                            print(f"  - {field}: RESPETADO (✓) - {value}")
                        else:
                            print(f"  - {field}: NO RESPETADO (!) - Esperado: {value}, Obtenido: {invoice_data[field]}")
                    else:
                        print(f"  - {field}: NO ENCONTRADO (?) - {value}")
            else:
                print("No se proporcionaron datos verificados por el usuario.")
            
            
            # Verificar datos de proveedor
            if 'supplier_address' in invoice_data and 'supplier_address' in raw_ocr_data:
                if invoice_data['supplier_address'] != raw_ocr_data.get('supplier_address'):
                    print(f"Discrepancia en dirección de proveedor:")
                    print(f"  OCR: {raw_ocr_data.get('supplier_address')}")
                    print(f"  Final: {invoice_data['supplier_address']}")
            
            # Verificar líneas de factura
            ocr_lines = raw_ocr_data.get('line_items', [])
            final_lines = invoice_data.get('line_items', [])
            if len(ocr_lines) != len(final_lines):
                print(f"Discrepancia en número de líneas: OCR={len(ocr_lines)}, Final={len(final_lines)}")
        else:
            print(f"Error: {result.get('message', 'Error desconocido')}")
    
    except requests.exceptions.RequestException as e:
        print(f"Error en la petición: {str(e)}")
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        # Cerrar el archivo
        files['file'][1].close()

if __name__ == "__main__":
    # Verificar argumentos
    if len(sys.argv) < 2:
        print("Uso: python test_debug_ocr.py <ruta_factura> [nombre_proveedor] [vat_proveedor] [nombre_cliente] [vat_cliente] [numero_factura]")
        sys.exit(1)
    
    file_path = sys.argv[1]
    supplier_name = sys.argv[2] if len(sys.argv) > 2 else None
    supplier_vat = sys.argv[3] if len(sys.argv) > 3 else None
    customer_name = sys.argv[4] if len(sys.argv) > 4 else None
    customer_vat = sys.argv[5] if len(sys.argv) > 5 else None
    invoice_number = sys.argv[6] if len(sys.argv) > 6 else None
    
    # Mostrar los datos verificados por humano que se enviarán
    print("\n=== DATOS VERIFICADOS POR HUMANO ===")
    if supplier_name:
        print(f"Nombre del proveedor: {supplier_name}")
    if supplier_vat:
        print(f"NIF/CIF del proveedor: {supplier_vat}")
    if customer_name:
        print(f"Nombre del cliente: {customer_name}")
    if customer_vat:
        print(f"NIF/CIF del cliente: {customer_vat}")
    if invoice_number:
        print(f"Número de factura: {invoice_number}")
    print("\n")
    
    test_debug_ocr(file_path, supplier_name, supplier_vat, customer_name, customer_vat, invoice_number)
