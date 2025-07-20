#!/usr/bin/env python3
"""
Servicio para extraer datos básicos de facturas a partir de texto OCR
"""
import re
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

# Configurar logging
logger = logging.getLogger(__name__)

def extract_basic_invoice_data(ocr_text: str) -> Dict[str, Any]:
    """
    Extrae datos básicos de una factura a partir del texto OCR
    
    Args:
        ocr_text: Texto extraído por OCR
        
    Returns:
        Dict[str, Any]: Datos básicos extraídos
    """
    # Inicializar diccionario de datos
    invoice_data = {
        "invoice_number": "",
        "invoice_date": "",
        "due_date": "",
        "supplier_name": "",
        "supplier_vat": "",
        "supplier_address": "",
        "supplier_city": "",
        "supplier_zip": "",
        "customer_name": "",
        "customer_vat": "",
        "customer_address": "",
        "customer_city": "",
        "customer_zip": "",
        "total_amount": None,
        "tax_amount": None,
        "subtotal": None,
        "tax_rate": None,
        "recargo_equivalencia": None,
        "recargo_rate": None,
        "payment_method": "",
        "payment_terms": "",
        "currency": "EUR",  # Por defecto EUR
        "lines": []
    }
    
    if not ocr_text:
        logger.warning("Texto OCR vacío, no se pueden extraer datos")
        return invoice_data
    
    # Normalizar texto
    text = ocr_text.replace('\r', ' ').replace('\n', ' ')
    
    # Extraer número de factura
    invoice_patterns = [
        r'(?:Factura|Fra\.?|Núm\.?|N°|Nº|No\.?|Número)[\s:]*([A-Za-z0-9\-\/]+)',
        r'(?:Invoice|Number|No\.?)[\s:]*([A-Za-z0-9\-\/]+)'
    ]
    for pattern in invoice_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            invoice_data["invoice_number"] = match.group(1).strip()
            break
    
    # Extraer fecha de factura
    date_patterns = [
        r'(?:Fecha|Date|Emitido|Emisión)[\s:]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
        r'(?:Fecha|Date|Emitido|Emisión)[\s:]*(\d{1,2}[\s](?:de)?[\s](?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)[\s](?:de)?[\s]\d{2,4})'
    ]
    for pattern in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            invoice_data["invoice_date"] = match.group(1).strip()
            break
    
    # Extraer fecha de vencimiento
    due_patterns = [
        r'(?:Vencimiento|Due|Fecha de vencimiento|Vence)[\s:]*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})'
    ]
    for pattern in due_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            invoice_data["due_date"] = match.group(1).strip()
            break
    
    # Extraer nombre del proveedor (buscar al principio del documento)
    text_start = ocr_text[:500]  # Primeros 500 caracteres
    lines = text_start.split('\n')
    for i, line in enumerate(lines[:5]):  # Primeras 5 líneas
        if line and len(line.strip()) > 3 and not re.match(r'^[0-9\s\.\-\:\/]+$', line.strip()):
            # Evitar líneas que son solo números, espacios o símbolos
            invoice_data["supplier_name"] = line.strip()
            break
    
    # Extraer NIF/CIF del proveedor
    vat_patterns = [
        r'(?:NIF|CIF|VAT|Tax ID)[\s:]*([A-Za-z0-9\-]+)',
        r'(?:[A-Z]\d{8}[A-Z])',  # Formato NIF/CIF español
        r'(?:\d{8}[A-Z])'  # Formato NIF español sin letra inicial
    ]
    for pattern in vat_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            invoice_data["supplier_vat"] = match.group(1).strip() if len(match.groups()) > 0 else match.group(0).strip()
            break
    
    # Extraer nombre del cliente
    customer_patterns = [
        r'(?:Cliente|Customer|Destinatario)[\s:]*([A-Za-z0-9\s\.]+)',
        r'(?:Facturar a|Bill to)[\s:]*([A-Za-z0-9\s\.]+)'
    ]
    for pattern in customer_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            invoice_data["customer_name"] = match.group(1).strip()
            break
    
    # Extraer NIF/CIF del cliente
    customer_vat_patterns = [
        r'(?:Cliente|Customer)[\s:]*[^\n]*(?:NIF|CIF|VAT)[\s:]*([A-Za-z0-9\-]+)',
        r'(?:NIF|CIF|VAT)[\s:](?:cliente|customer)?[\s:]*([A-Za-z0-9\-]+)'
    ]
    for pattern in customer_vat_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            invoice_data["customer_vat"] = match.group(1).strip()
            break
    
    # Extraer importes
    # Total
    total_patterns = [
        r'(?:Total|Importe total|Total a pagar)[\s:]*[\€\$]?[\s]*([0-9\.\,]+)',
        r'(?:TOTAL)[\s:]*[\€\$]?[\s]*([0-9\.\,]+)'
    ]
    for pattern in total_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            total_str = match.group(1).strip().replace('.', '').replace(',', '.')
            try:
                invoice_data["total_amount"] = float(total_str)
                break
            except ValueError:
                continue
    
    # IVA
    tax_patterns = [
        r'(?:IVA|VAT|Impuesto)[\s:]*[\€\$]?[\s]*([0-9\.\,]+)',
        r'(?:IVA|VAT|Impuesto)[\s:]*([0-9\.\,]+)[\s]*[\€\$]?'
    ]
    for pattern in tax_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            tax_str = match.group(1).strip().replace('.', '').replace(',', '.')
            try:
                invoice_data["tax_amount"] = float(tax_str)
                break
            except ValueError:
                continue
    
    # Subtotal
    subtotal_patterns = [
        r'(?:Base|Subtotal|Base imponible)[\s:]*[\€\$]?[\s]*([0-9\.\,]+)',
        r'(?:Base|Subtotal|Base imponible)[\s:]*([0-9\.\,]+)[\s]*[\€\$]?'
    ]
    for pattern in subtotal_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            subtotal_str = match.group(1).strip().replace('.', '').replace(',', '.')
            try:
                invoice_data["subtotal"] = float(subtotal_str)
                break
            except ValueError:
                continue
    
    # Tipo de IVA
    tax_rate_patterns = [
        r'(?:IVA|VAT)[\s:]*([0-9\.\,]+)[\s]*%',
        r'([0-9\.\,]+)[\s]*%[\s]*(?:IVA|VAT)'
    ]
    for pattern in tax_rate_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            tax_rate_str = match.group(1).strip().replace(',', '.')
            try:
                invoice_data["tax_rate"] = float(tax_rate_str)
                break
            except ValueError:
                continue
    
    # Intentar extraer líneas de productos (muy básico)
    # Buscar patrones comunes en líneas de productos
    product_lines = []
    lines = ocr_text.split('\n')
    for i, line in enumerate(lines):
        if re.search(r'\d+[\s]*(?:ud|uds|unidad|unidades|pcs|pc|u\.)', line, re.IGNORECASE):
            # Línea que contiene cantidades
            product_lines.append({
                "quantity": 1,
                "description": line.strip(),
                "price_unit": None,
                "price_total": None
            })
    
    if product_lines:
        invoice_data["lines"] = product_lines
    
    # Registrar los datos extraídos
    logger.info(f"Datos básicos extraídos del texto OCR: {invoice_data}")
    
    return invoice_data
