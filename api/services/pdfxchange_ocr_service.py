import os
import shutil
import time
import uuid
import asyncio
from pathlib import Path
import json
import re
from typing import Dict, Any, Optional, List

class PDFXChangeOCRService:
    def __init__(self, 
                 input_dir="/mnt/e/1/ejemplosPDF/entrada",
                 processing_dir="/mnt/e/1/ejemplosPDF/procesando",
                 output_dir="/mnt/e/1/ejemplosPDF/salida",
                 max_wait_time=60):
        """
        Servicio para procesar OCR usando PDF-XChange Editor a través de carpetas compartidas
        
        Args:
            input_dir: Directorio donde se colocan los PDFs a procesar
            processing_dir: Directorio donde se mueven los PDFs en procesamiento
            output_dir: Directorio donde PDF-XChange coloca los resultados
            max_wait_time: Tiempo máximo de espera en segundos
        """
        self.input_dir = input_dir
        self.processing_dir = processing_dir
        self.output_dir = output_dir
        self.max_wait_time = max_wait_time
        
        # Crear directorios si no existen
        for dir_path in [self.input_dir, self.processing_dir, self.output_dir]:
            os.makedirs(dir_path, exist_ok=True)
    
    async def process_pdf(self, pdf_content: bytes, filename: str) -> str:
        """
        Procesa un PDF con PDF-XChange Editor y devuelve el texto extraído
        
        Args:
            pdf_content: Contenido del PDF en bytes
            filename: Nombre del archivo
            
        Returns:
            Texto extraído por OCR
        """
        # Generar ID único para este archivo
        file_id = str(uuid.uuid4())
        base_name = Path(filename).stem
        unique_name = f"{base_name}_{file_id}"
        
        # Guardar PDF en carpeta de entrada
        input_path = os.path.join(self.input_dir, f"{unique_name}.pdf")
        with open(input_path, "wb") as f:
            f.write(pdf_content)
        
        # Mover a carpeta de procesamiento
        processing_path = os.path.join(self.processing_dir, f"{unique_name}.pdf")
        shutil.move(input_path, processing_path)
        
        # Esperar resultado en carpeta de salida
        output_path = os.path.join(self.output_dir, f"{unique_name}.txt")
        
        # Esperar hasta que aparezca el archivo de resultado
        wait_interval = 2
        elapsed_time = 0
        
        while elapsed_time < self.max_wait_time:
            if os.path.exists(output_path):
                # Leer resultado
                with open(output_path, "r", encoding="utf-8") as f:
                    text_result = f.read()
                
                # Limpiar archivos
                try:
                    if os.path.exists(processing_path):
                        os.remove(processing_path)
                    os.remove(output_path)
                except Exception as e:
                    print(f"Error limpiando archivos: {e}")
                    
                return text_result
            
            # Esperar antes de verificar nuevamente
            await asyncio.sleep(wait_interval)
            elapsed_time += wait_interval
        
        # Si llegamos aquí, se agotó el tiempo de espera
        if os.path.exists(processing_path):
            try:
                os.remove(processing_path)
            except:
                pass
        
        raise TimeoutError("Tiempo de espera agotado para el procesamiento OCR")
    
    def extract_invoice_data(self, ocr_text: str) -> Dict[str, Any]:
        """
        Extrae datos estructurados de una factura a partir del texto OCR
        
        Args:
            ocr_text: Texto extraído por OCR
            
        Returns:
            Diccionario con datos estructurados de la factura
        """
        invoice_data = {
            "number": None,
            "date": None,
            "partner_name": None,
            "vat": None,
            "amount_total": None,
            "lines": [],
            "due_dates": [],
            "customer_order_ref": None,
            "payment_term": None
        }
        
        # Extraer número de factura
        invoice_number_match = re.search(r'N[º°]?\s*Factura\s*[:\s]\s*([A-Z0-9\-]+)', ocr_text) or \
                              re.search(r'Factura\s*[:\s]\s*([A-Z0-9\-]+)', ocr_text) or \
                              re.search(r'([A-Z][0-9]{2}[-\s][0-9]{5,})', ocr_text)
        if invoice_number_match:
            invoice_data["number"] = invoice_number_match.group(1).strip()
        
        # Extraer fecha
        date_match = re.search(r'Fecha\s*[:\s]\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})', ocr_text) or \
                    re.search(r'(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})', ocr_text)
        if date_match:
            invoice_data["date"] = date_match.group(1).strip()
        
        # Extraer proveedor (en facturas NEVIR)
        if "NEVIR" in ocr_text:
            invoice_data["partner_name"] = "NEVIR S.A."
            vat_match = re.search(r'Nevir S\.A\.\s*-\s*([A-Z0-9]+)', ocr_text)
            if vat_match:
                invoice_data["vat"] = vat_match.group(1).strip()
        
        # Extraer total
        total_match = re.search(r'TOTAL FACTURA\s*(\d+[\.\,]\d+)', ocr_text) or \
                     re.search(r'TOTAL\s*(\d+[\.\,]\d+)', ocr_text)
        if total_match:
            invoice_data["amount_total"] = float(total_match.group(1).replace(',', '.').strip())
        
        # Extraer líneas de factura (para facturas con formato tabular)
        # Este patrón busca líneas con código de producto, cantidad, descripción y precio
        lines_pattern = r'([A-Z0-9\-]+)\s+(\d+)\s+([A-ZÁÉÍÓÚÑáéíóúñ\s\.\,\-]+)\s+(\d+[\.\,]\d+)'
        lines_matches = re.finditer(lines_pattern, ocr_text)
        
        for match in lines_matches:
            line = {
                "product_code": match.group(1).strip(),
                "quantity": int(match.group(2).strip()),
                "name": match.group(3).strip(),
                "price_unit": float(match.group(4).replace(',', '.').strip()),
                "price_subtotal": None  # Se calculará si es posible
            }
            
            # Intentar extraer precio total de la línea
            # Buscar en la misma línea o cercana
            line_text = ocr_text[match.start():match.start() + 200]  # Tomar 200 caracteres desde el inicio de la línea
            total_price_match = re.search(r'(\d+[\.\,]\d+)\s*$', line_text)
            if total_price_match:
                line["price_subtotal"] = float(total_price_match.group(1).replace(',', '.').strip())
            
            invoice_data["lines"].append(line)
        
        # Extraer forma de pago
        payment_match = re.search(r'Forma de pago\s*([A-ZÁÉÍÓÚÑáéíóúñ0-9\s\.\,\-]+)[\n\r]', ocr_text)
        if payment_match:
            invoice_data["payment_term"] = payment_match.group(1).strip()
            
        # Extraer fechas de vencimiento
        due_date_matches = re.finditer(r'Vencimiento\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})\s*(\d+[\.\,]\d+)', ocr_text)
        for match in due_date_matches:
            invoice_data["due_dates"].append({
                "date": match.group(1).strip(),
                "amount": float(match.group(2).replace(',', '.').strip())
            })
        
        return invoice_data