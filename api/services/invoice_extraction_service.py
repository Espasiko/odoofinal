"""
Servicio para extracción de datos de facturas
"""
import re
import logging
from datetime import datetime
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class InvoiceExtractionService:
    """Servicio para extraer datos estructurados de facturas desde texto OCR"""
    
    def extract_invoice_data_from_text(self, text: str) -> Dict[str, Any]:
        """
        Extrae datos estructurados de factura desde texto OCR markdown
        Específicamente optimizado para facturas de Alfadyser y otros proveedores comunes
        
        Args:
            text: Texto OCR extraído del documento
            
        Returns:
            Dict[str, Any]: Datos estructurados de la factura
        """
        lines = text.split('\n')
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
            "total_amount": 0.0,
            "tax_amount": 0.0,
            "subtotal": 0.0,
            "customer_order_ref": "",
            "line_items": []
        }
        
        # Extraer número de factura
        self._extract_invoice_number(lines, invoice_data)
        
        # Extraer NIF/CIF del proveedor
        self._extract_supplier_vat(lines, invoice_data)
        
        # Extraer fecha de factura
        self._extract_invoice_date(lines, invoice_data)
        
        # Extraer datos del proveedor y cliente
        self._extract_supplier_and_customer_data(lines, invoice_data)
        
        # Extraer importes
        self._extract_amounts(lines, invoice_data)
        
        # Extraer líneas de productos
        self._extract_product_lines(lines, invoice_data)
        
        return invoice_data
    
    def _extract_invoice_number(self, lines: List[str], invoice_data: Dict[str, Any]) -> None:
        """
        Extrae el número de factura del texto OCR
        
        Args:
            lines: Líneas de texto OCR
            invoice_data: Diccionario donde guardar los datos extraídos
        """
        # Buscar número de factura específicamente para facturas Alfadyser (formato 25FVR-0012334)
        for line in lines:
            # Patrón para facturas Alfadyser (formato específico)
            matches = re.findall(r'\b(\d+[A-Z]+-\d+)\b', line)
            if matches:
                invoice_data["invoice_number"] = matches[0].strip()
                break
                
        # Si no se encontró con el patrón específico, buscar en encabezados de tablas
        if not invoice_data["invoice_number"]:
            for i, line in enumerate(lines):
                if '|  Número factura | Fecha | Cód. Cliente  |' in line and i + 2 < len(lines):
                    data_line = lines[i + 2]
                    if data_line.startswith('|'):
                        cells = [cell.strip() for cell in data_line.split('|') if cell.strip()]
                        if len(cells) >= 2:
                            invoice_data["invoice_number"] = cells[0].strip()
                            if len(cells) >= 3:
                                # Convertir fecha al formato ISO (YYYY-MM-DD)
                                date_str = cells[1].strip()
                                try:
                                    for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y', '%d-%m-%y']:
                                        try:
                                            date_obj = datetime.strptime(date_str, fmt)
                                            invoice_data["invoice_date"] = date_obj.strftime('%Y-%m-%d')
                                            break
                                        except ValueError:
                                            continue
                                except Exception:
                                    invoice_data["invoice_date"] = date_str
                            break
                            
        # Si todavía no tenemos número de factura, buscar patrones genéricos
        if not invoice_data["invoice_number"]:
            for line in lines:
                match = re.search(r'(?:Factura|Número)[\s:]*(\w+[-/]?\w*)', line, re.IGNORECASE)
                if match:
                    invoice_data["invoice_number"] = match.group(1).strip()
                    break
    
    def _extract_supplier_vat(self, lines: List[str], invoice_data: Dict[str, Any]) -> None:
        """
        Extrae el NIF/CIF del proveedor
        
        Args:
            lines: Líneas de texto OCR
            invoice_data: Diccionario donde guardar los datos extraídos
        """
        # Buscar NIF/CIF del proveedor (formato común: letra + números)
        for line in lines:
            vat_matches = re.findall(r'\b[A-Z0-9]{1}[-\s]?\d{7,8}[-\s]?[A-Z0-9]{1}\b', line, re.IGNORECASE)
            if vat_matches:
                invoice_data["supplier_vat"] = vat_matches[0].replace(' ', '').replace('-', '')
                break
            if "NIF:" in line or "CIF:" in line or "N.I.F.:" in line:
                vat_matches = re.findall(r'(?:NIF|CIF|N\.I\.F\.):?\s*([A-Z0-9]{1}[-\s]?\d{7,8}[-\s]?[A-Z0-9]{1})', line, re.IGNORECASE)
                if vat_matches:
                    invoice_data["supplier_vat"] = vat_matches[0].replace(' ', '').replace('-', '')
                    break
    
    def _extract_invoice_date(self, lines: List[str], invoice_data: Dict[str, Any]) -> None:
        """
        Extrae la fecha de factura
        
        Args:
            lines: Líneas de texto OCR
            invoice_data: Diccionario donde guardar los datos extraídos
        """
        # Buscar fecha de factura si no la tenemos ya
        if not invoice_data["invoice_date"]:
            for line in lines:
                # Buscar texto que mencione fecha de factura
                if "fecha" in line.lower() and "factura" in line.lower():
                    # Extraer fechas en formato DD/MM/YYYY o DD-MM-YYYY
                    date_matches = re.findall(r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b', line)
                    if date_matches:
                        date_str = date_matches[0]
                        try:
                            for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y', '%d-%m-%y']:
                                try:
                                    date_obj = datetime.strptime(date_str, fmt)
                                    invoice_data["invoice_date"] = date_obj.strftime('%Y-%m-%d')
                                    break
                                except ValueError:
                                    continue
                        except Exception:
                            invoice_data["invoice_date"] = date_str
                        break
    
    def _extract_supplier_and_customer_data(self, lines: List[str], invoice_data: Dict[str, Any]) -> None:
        """
        Extrae datos del proveedor y cliente
        
        Args:
            lines: Líneas de texto OCR
            invoice_data: Diccionario donde guardar los datos extraídos
        """
        # Lista de proveedores conocidos por nombre
        known_suppliers = {
            "ALFADYSER": "ALFADYSER",
            "CECOTEC": "CECOTEC",
            "BECKEN": "BECKEN-TEGALUXE",
            "TEGALUXE": "BECKEN-TEGALUXE",
            "JATA": "JATA",
            "ALMCE": "ALMCE S.L.",
            "ALMACENES": "ALMCE S.L.",
            "ABRILA": "ABRILA",
            "BSH": "BSH",
            "EAS JOHNSON": "EAS JOhNSON",
            "MI ELECTRO": "MI ELECTRO",
            "MIELECTRO": "MIELECTRO",
            "NEVIR": "NEVIR",
            "ORBEGOZO": "ORBEGOZO",
            "UFESA": "UFESA",
            "VITROKITCHEN": "VITROKITCHEN"
        }
        
        # Lista de clientes conocidos para evitar confusiones
        known_customers = ["EL PELOTAZO", "ANTONIO BONACHERA", "CARRETERA DE ALICUN", "B04957403"]
        
        # Buscar nombre del proveedor en lista de proveedores conocidos
        supplier_found = False
        for line in lines:
            # Primero verificar si esta línea contiene información de un cliente conocido
            if any(customer.lower() in line.lower() for customer in known_customers):
                # Si encontramos un cliente conocido, lo guardamos pero seguimos buscando el proveedor
                if not invoice_data["customer_name"]:
                    for customer in known_customers:
                        if customer.lower() in line.lower():
                            invoice_data["customer_name"] = "EL PELOTAZO - ANTONIO BONACHERA"
                            break
                continue
            
            # Buscar proveedores conocidos
            for supplier_key, supplier_full_name in known_suppliers.items():
                if supplier_key.lower() in line.lower():
                    invoice_data["supplier_name"] = supplier_full_name
                    supplier_found = True
                    break
            
            if supplier_found:
                break
                
        # Si encontramos un nombre de cliente pero no de proveedor en una factura Alfadyser
        # Por defecto asignamos Alfadyser como proveedor si el formato del documento sugiere que es una factura suya
        if not supplier_found and invoice_data["customer_name"] and any("FVR-" in line for line in lines):
            invoice_data["supplier_name"] = "ALFADYSER S.L."
            supplier_found = True
                
        # Si no lo encontramos específicamente, buscar secciones de "proveedor" o en encabezados
        if not supplier_found:
            for i, line in enumerate(lines[:10]):  # Buscar en primeras líneas
                if len(line.strip()) > 5 and not line.startswith('|') and not re.match(r'^\d', line):
                    # Probablemente el nombre del proveedor en el encabezado
                    invoice_data["supplier_name"] = line.strip()
                    supplier_found = True
                    
                    # Buscar dirección en las siguientes líneas
                    if i + 1 < len(lines) and len(lines[i+1].strip()) > 0:
                        invoice_data["supplier_address"] = lines[i+1].strip()
                    break
    
    def _extract_amounts(self, lines: List[str], invoice_data: Dict[str, Any]) -> None:
        """
        Extrae importes de la factura (total, base imponible, IVA)
        
        Args:
            lines: Líneas de texto OCR
            invoice_data: Diccionario donde guardar los datos extraídos
        """
        # Buscar importe total con IVA
        total_found = False
        for line in lines:
            # Buscar patrones específicos de totales
            if "total" in line.lower() or "importe" in line.lower():
                # Patrón para importes con símbolo € o EUR
                amount_matches = re.findall(r'(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})(?:\s*€|\s*EUR)?', line)
                if amount_matches:
                    try:
                        # Normalizar separadores decimales y de miles
                        amount_str = amount_matches[-1].replace('.', '').replace(',', '.')
                        invoice_data["total_amount"] = float(amount_str)
                        total_found = True
                        break
                    except ValueError:
                        pass
        
        # Buscar en tablas de resumen de importes
        if not total_found:
            for i, line in enumerate(lines):
                if '|  Base imponible |' in line and i + 2 < len(lines):
                    for j in range(i+1, min(i+5, len(lines))):
                        data_line = lines[j]
                        if '| Total |' in data_line:
                            cells = [cell.strip() for cell in data_line.split('|') if cell.strip()]
                            if len(cells) >= 2:
                                try:
                                    # Extraer el último valor como importe total
                                    amount_str = cells[-1].replace('€', '').replace('.', '').replace(',', '.').strip()
                                    invoice_data["total_amount"] = float(amount_str)
                                    total_found = True
                                    break
                                except ValueError:
                                    pass
        
        # Buscar IVA y base imponible
        tax_amount_found = False
        subtotal_found = False
        
        # Buscar en líneas que mencionan IVA
        for line in lines:
            if "iva" in line.lower() or "i.v.a" in line.lower():
                # Extraer valor del IVA
                amount_matches = re.findall(r'(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})(?:\s*€|\s*EUR)?', line)
                if amount_matches:
                    try:
                        # Normalizar separadores
                        amount_str = amount_matches[-1].replace('.', '').replace(',', '.')
                        invoice_data["tax_amount"] = float(amount_str)
                        tax_amount_found = True
                        break
                    except ValueError:
                        pass
        
        # Buscar base imponible
        for line in lines:
            if "base" in line.lower() and ("imponible" in line.lower() or "imp" in line.lower()):
                amount_matches = re.findall(r'(\d{1,3}(?:[.,]\d{3})*[.,]\d{2})(?:\s*€|\s*EUR)?', line)
                if amount_matches:
                    try:
                        amount_str = amount_matches[-1].replace('.', '').replace(',', '.')
                        invoice_data["subtotal"] = float(amount_str)
                        subtotal_found = True
                        break
                    except ValueError:
                        pass
        
        # Si tenemos total pero no tenemos alguno de los otros, hacer cálculos aproximados
        if total_found and not (tax_amount_found and subtotal_found):
            # Si tenemos base pero no IVA
            if subtotal_found and not tax_amount_found:
                # Asumimos IVA 21% (común en España)
                invoice_data["tax_amount"] = round(invoice_data["subtotal"] * 0.21, 2)
            # Si tenemos IVA pero no base
            elif tax_amount_found and not subtotal_found:
                # Calculamos la base aproximada
                invoice_data["subtotal"] = round(invoice_data["total_amount"] - invoice_data["tax_amount"], 2)
            # Si no tenemos ninguno, asumimos IVA 21%
            elif not tax_amount_found and not subtotal_found:
                # Base imponible = total / 1.21
                invoice_data["subtotal"] = round(invoice_data["total_amount"] / 1.21, 2)
                invoice_data["tax_amount"] = round(invoice_data["total_amount"] - invoice_data["subtotal"], 2)
    
    def _extract_product_lines(self, lines: List[str], invoice_data: Dict[str, Any]) -> None:
        """
        Extrae líneas de productos/servicios de la factura
        
        Args:
            lines: Líneas de texto OCR
            invoice_data: Diccionario donde guardar los datos extraídos
        """
        # Extraer líneas de productos/servicios (primero buscamos en tablas)
        product_lines = []
        table_found = False
        
        # Buscar tablas de productos
        for i, line in enumerate(lines):
            if '|  Referencia |' in line or '|  Código |' in line or '|  Descripción |' in line:
                # Determinamos los índices de las columnas
                header = line.split('|')
                col_indices = {}
                for j, col in enumerate(header):
                    col = col.strip().lower()
                    if 'referencia' in col or 'código' in col or 'ref' in col:
                        col_indices['code'] = j
                    elif 'descripción' in col or 'concepto' in col or 'detalle' in col:
                        col_indices['name'] = j
                    elif 'cantidad' in col or 'uds' in col:
                        col_indices['quantity'] = j
                    elif 'precio' in col or 'importe' in col or 'unitario' in col:
                        col_indices['price'] = j
                
                # Si encontramos al menos descripción y precio, procesamos la tabla
                if 'name' in col_indices and ('price' in col_indices or 'quantity' in col_indices):
                    table_found = True
                    
                    # Procesar filas de la tabla (excluyendo encabezados y líneas vacías)
                    for j in range(i+1, len(lines)):
                        row = lines[j]
                        if not row.startswith('|') or '---' in row:
                            continue
                        
                        cells = row.split('|')
                        if len(cells) < len(header):
                            continue
                        
                        # Crear línea de producto
                        product_line = {
                            "name": "",
                            "quantity": 1.0,
                            "price_unit": 0.0,
                            "default_code": ""
                        }
                        
                        # Extraer datos según las columnas identificadas
                        for key, idx in col_indices.items():
                            if idx < len(cells):
                                value = cells[idx].strip()
                                if key == 'name':
                                    product_line["name"] = value
                                elif key == 'code':
                                    product_line["default_code"] = value
                                elif key == 'quantity':
                                    try:
                                        # Normalizar el valor numérico
                                        value = value.replace('.', '').replace(',', '.')
                                        product_line["quantity"] = float(value)
                                    except ValueError:
                                        pass
                                elif key == 'price':
                                    try:
                                        # Normalizar y eliminar símbolo de moneda
                                        value = value.replace('€', '').replace('.', '').replace(',', '.').strip()
                                        product_line["price_unit"] = float(value)
                                    except ValueError:
                                        pass
                        
                        # Solo añadimos si tiene nombre y algún valor numérico
                        if product_line["name"] and (product_line["quantity"] > 0 or product_line["price_unit"] > 0):
                            product_lines.append(product_line)
        
        # Si no encontramos líneas en tablas, intentar encontrarlas en texto plano
        if not table_found and not product_lines:
            # Buscar líneas que coincidan con patrones de producto y precio
            for line in lines:
                # Buscar líneas con cantidad y precio
                match = re.search(r'(.+?)\s+(\d+(?:[.,]\d+)?)\s+(?:x\s+)?(\d+(?:[.,]\d+)?)', line)
                if match:
                    name = match.group(1).strip()
                    try:
                        qty = float(match.group(2).replace(',', '.'))
                        price = float(match.group(3).replace(',', '.'))
                        
                        product_lines.append({
                            "name": name,
                            "quantity": qty,
                            "price_unit": price,
                            "default_code": ""
                        })
                    except ValueError:
                        pass
        
        # Añadir las líneas de productos encontradas
        invoice_data["line_items"] = product_lines

# Instancia global del servicio
invoice_extraction_service = InvoiceExtractionService()
