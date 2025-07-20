"""
Servicio de extracción de tablas de facturas PDF utilizando Tabula
"""
import os
import logging
import tempfile
import pandas as pd
import re
from typing import List, Dict, Any, Optional, Tuple
import tabula
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class TabulaExtractionService:
    """
    Servicio para extraer tablas de facturas PDF utilizando Tabula
    """
    
    def __init__(self):
        """Inicializa el servicio de extracción de tablas"""
        self.temp_dir = tempfile.gettempdir()
        logger.info(f"TabulaExtractionService inicializado. Directorio temporal: {self.temp_dir}")
    
    def extract_tables(self, pdf_path: str) -> List[pd.DataFrame]:
        """
        Extrae todas las tablas de un archivo PDF usando diferentes métodos de Tabula
        
        Args:
            pdf_path: Ruta al archivo PDF
            
        Returns:
            List[pd.DataFrame]: Lista de DataFrames con las tablas extraídas
        """
        if not os.path.exists(pdf_path):
            logger.error(f"El archivo PDF no existe: {pdf_path}")
            return []
        
        try:
            # Intentar diferentes métodos de extracción
            all_tables = []
            
            # Método 1: Stream (para tablas sin líneas) - Priorizado basado en análisis
            logger.info(f"Extrayendo tablas del PDF con método stream: {pdf_path}")
            stream_tables = tabula.read_pdf(
                pdf_path,
                pages='all',
                multiple_tables=True,
                lattice=False,
                stream=True,
                encoding='utf-8',
                guess=True
            )
            if stream_tables and len(stream_tables) > 0:
                logger.info(f"Se encontraron {len(stream_tables)} tablas con método stream")
                all_tables.extend(stream_tables)
            
            # Método 2: Lattice (para tablas con líneas)
            logger.info(f"Extrayendo tablas del PDF con método lattice: {pdf_path}")
            lattice_tables = tabula.read_pdf(
                pdf_path,
                pages='all',
                multiple_tables=True,
                lattice=True,
                stream=False,
                encoding='utf-8'
            )
            if lattice_tables and len(lattice_tables) > 0:
                logger.info(f"Se encontraron {len(lattice_tables)} tablas con método lattice")
                all_tables.extend(lattice_tables)
            
            # Método 3: Áreas específicas para facturas (mitad inferior de la página)
            # Este método es especialmente útil para facturas donde las tablas de productos
            # suelen estar en la parte inferior
            logger.info(f"Extrayendo tablas del PDF con método de área específica: {pdf_path}")
            area_tables = tabula.read_pdf(
                pdf_path,
                pages='all',
                multiple_tables=True,
                area=[50, 0, 100, 100],  # [top, left, bottom, right] como porcentajes
                relative_area=True
            )
            if area_tables and len(area_tables) > 0:
                logger.info(f"Se encontraron {len(area_tables)} tablas con método de área específica")
                all_tables.extend(area_tables)
            
            # Eliminar tablas vacías o duplicadas
            filtered_tables = []
            for table in all_tables:
                if not table.empty and not any(table.equals(t) for t in filtered_tables):
                    filtered_tables.append(table)
            
            # Reemplazar NaN por cadenas vacías en todas las tablas
            tables = [table.fillna("") for table in filtered_tables]
            
            logger.info(f"Se encontraron {len(tables)} tablas únicas en el PDF")
            return tables
        except Exception as e:
            logger.error(f"Error al extraer tablas del PDF: {e}")
            return []
    
    def find_invoice_table(self, tables: List[pd.DataFrame]) -> Optional[pd.DataFrame]:
        """
        Encuentra la tabla principal de la factura (la que contiene los productos)
        
        Args:
            tables: Lista de DataFrames con las tablas extraídas
            
        Returns:
            Optional[pd.DataFrame]: DataFrame con la tabla de productos, o None si no se encuentra
        """
        if not tables:
            return None
        
        # Criterios para identificar la tabla de productos
        keywords = ['referencia', 'ref', 'código', 'descripción', 'desc', 'cantidad', 'cant', 
                   'precio', 'importe', 'dto', 'descuento', 'iva', 'total']
        
        best_table = None
        max_score = 0
        
        for table in tables:
            if table.empty:
                continue
                
            # Convertir columnas a string para búsqueda
            table_str = table.astype(str)
            
            # Calcular puntuación basada en coincidencias de palabras clave
            score = 0
            for keyword in keywords:
                # Buscar en nombres de columnas
                for col in table.columns:
                    if keyword in str(col).lower():
                        score += 3
                
                # Buscar en primera fila (puede contener encabezados)
                if not table.empty and len(table) > 0:
                    for val in table.iloc[0].astype(str):
                        if keyword in str(val).lower():
                            score += 2
            
            # Dar preferencia a tablas más grandes
            score += min(len(table), 10)  # Máximo 10 puntos por tamaño
            
            if score > max_score:
                max_score = score
                best_table = table
        
        if best_table is not None and max_score > 5:  # Umbral mínimo de confianza
            logger.info(f"Tabla de factura encontrada con puntuación: {max_score}")
            return best_table
        else:
            logger.warning("No se encontró una tabla de factura confiable")
            return None
    
    def find_tax_table(self, tables: List[pd.DataFrame]) -> Optional[pd.DataFrame]:
        """
        Encuentra la tabla de impuestos de la factura
        
        Args:
            tables: Lista de DataFrames con las tablas extraídas
            
        Returns:
            Optional[pd.DataFrame]: DataFrame con la tabla de impuestos, o None si no se encuentra
        """
        if not tables:
            return None
        
        # Criterios para identificar la tabla de impuestos
        keywords = ['base', 'imponible', 'iva', '%', 'impuesto', 'recargo', 'equivalencia', 
                   'r.e.', 're', 'total']
        
        best_table = None
        max_score = 0
        
        for table in tables:
            if table.empty:
                continue
                
            # Convertir a string para búsqueda
            table_str = table.astype(str)
            table_text = ' '.join([' '.join(map(str, row)) for row in table.values])
            table_text = table_text.lower()
            
            # Calcular puntuación
            score = 0
            for keyword in keywords:
                if keyword in table_text:
                    score += 2
            
            # Preferencia a tablas pequeñas (las tablas de impuestos suelen ser pequeñas)
            if len(table) <= 5:
                score += 3
            
            if score > max_score:
                max_score = score
                best_table = table
        
        if best_table is not None and max_score > 4:  # Umbral mínimo
            logger.info(f"Tabla de impuestos encontrada con puntuación: {max_score}")
            return best_table
        else:
            logger.warning("No se encontró una tabla de impuestos confiable")
            return None
    
    def extract_recargo_equivalencia(self, tables: List[pd.DataFrame]) -> Optional[float]:
        """
        Extrae el porcentaje de recargo de equivalencia de las tablas
        
        Args:
            tables: Lista de DataFrames con las tablas extraídas
            
        Returns:
            Optional[float]: Porcentaje de recargo de equivalencia, o None si no se encuentra
        """
        # Primero intentar con la tabla de impuestos
        tax_table = self.find_tax_table(tables)
        if tax_table is not None:
            # Convertir toda la tabla a texto para buscar
            table_text = ' '.join([' '.join(map(str, row)) for row in tax_table.values])
            table_text = table_text.lower()
            
            # Buscar menciones de recargo
            if any(term in table_text for term in ['recargo', 'r.e.', 'r.eq', 'r e q']):
                # Buscar valores comunes de recargo
                for recargo in ['5.2', '5,2', '1.4', '1,4', '0.5', '0,5']:
                    if recargo in table_text:
                        # Convertir a float (reemplazando coma por punto)
                        return float(recargo.replace(',', '.'))
        
        # Si no se encuentra en la tabla de impuestos, buscar en todas las tablas
        for table in tables:
            if table.empty:
                continue
                
            table_text = ' '.join([' '.join(map(str, row)) for row in table.values])
            table_text = table_text.lower()
            
            if any(term in table_text for term in ['recargo', 'r.e.', 'r.eq', 'r e q']):
                # Buscar valores comunes de recargo
                for recargo in ['5.2', '5,2', '1.4', '1,4', '0.5', '0,5']:
                    if recargo in table_text:
                        return float(recargo.replace(',', '.'))
        
        return None
    
    def enhance_invoice_data(self, invoice_data: Dict[str, Any], pdf_path: str) -> Dict[str, Any]:
        """
        Mejora los datos de la factura con información extraída de las tablas
        
        Args:
            invoice_data: Datos de la factura extraídos por OCR
            pdf_path: Ruta al archivo PDF
            
        Returns:
            Dict[str, Any]: Datos de la factura mejorados
        """
        # Extraer tablas del PDF
        tables = self.extract_tables_from_pdf(pdf_path)
        if not tables:
            logger.warning("No se pudieron extraer tablas del PDF")
            return invoice_data
        
        # Copia de los datos originales
        enhanced_data = invoice_data.copy()
        
        # Extraer recargo de equivalencia si no está presente
        if not enhanced_data.get('recargo_equivalencia') or enhanced_data.get('recargo_equivalencia') is None:
            recargo = self.extract_recargo_equivalencia(tables)
            if recargo is not None:
                logger.info(f"Recargo de equivalencia encontrado con Tabula: {recargo}%")
                enhanced_data['recargo_equivalencia'] = recargo
                enhanced_data['recargo_rate'] = recargo
                
                # Actualizar recargo en líneas de factura
                if 'line_items' in enhanced_data and isinstance(enhanced_data['line_items'], list):
                    for line in enhanced_data['line_items']:
                        if isinstance(line, dict):
                            line['recargo_rate'] = recargo
        
        # Intentar mejorar otros datos si es necesario
        # TODO: Implementar mejoras adicionales basadas en tablas
        
        return enhanced_data
        
    def extract_tables_from_pdf(self, pdf_path: str) -> List[pd.DataFrame]:
        """
        Alias para el método extract_tables para mantener compatibilidad con el código existente
        
        Args:
            pdf_path: Ruta al archivo PDF
            
        Returns:
            List[pd.DataFrame]: Lista de DataFrames con las tablas extraídas
        """
        return self.extract_tables(pdf_path)
        
    def extract_invoice_data(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extrae todos los datos posibles de una factura PDF usando Tabula
        
        Args:
            pdf_path: Ruta al archivo PDF
            
        Returns:
            Dict[str, Any]: Datos extraídos de la factura
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
        
        # Extraer tablas del PDF
        tables = self.extract_tables_from_pdf(pdf_path)
        if not tables:
            logger.warning("No se pudieron extraer tablas del PDF")
            return invoice_data
        
        # Convertir todas las tablas a texto para búsqueda
        all_text = ""
        for table in tables:
            if not table.empty:
                # Reemplazar valores NaN por cadenas vacías antes de convertir a string
                table_clean = table.fillna("")
                all_text += table_clean.to_string(index=False) + "\n\n"
        
        # Buscar datos en el texto combinado de todas las tablas
        # Número de factura
        invoice_patterns = [
            r'(?:Factura|Fra\.?|Núm\.?|N°|Nº|No\.?|Número)[\s:]*([A-Za-z0-9\-\/]+)',
            r'(?:Invoice|Number|No\.?)[\s:]*([A-Za-z0-9\-\/]+)'
        ]
        for pattern in invoice_patterns:
            match = re.search(pattern, all_text, re.IGNORECASE)
            if match:
                invoice_data["invoice_number"] = match.group(1).strip()
                break
        
        # Fecha de factura
        date_patterns = [
            r'(?:Fecha|Date|Emitido|Emisión)[\s:]*([0-9]{1,2}[\/\-\.][0-9]{1,2}[\/\-\.][0-9]{2,4})',
            r'(?:Fecha|Date|Emitido|Emisión)[\s:]*([0-9]{4}[\/\-\.][0-9]{1,2}[\/\-\.][0-9]{1,2})'
        ]
        for pattern in date_patterns:
            match = re.search(pattern, all_text, re.IGNORECASE)
            if match:
                invoice_data["invoice_date"] = match.group(1).strip()
                break
        
        # Fecha de vencimiento
        due_patterns = [
            r'(?:Vencimiento|Due|Fecha de vencimiento|Vence)[\s:]*([0-9]{1,2}[\/\-\.][0-9]{1,2}[\/\-\.][0-9]{2,4})',
            r'(?:Vencimiento|Due|Fecha de vencimiento|Vence)[\s:]*([0-9]{4}[\/\-\.][0-9]{1,2}[\/\-\.][0-9]{1,2})'
        ]
        for pattern in due_patterns:
            match = re.search(pattern, all_text, re.IGNORECASE)
            if match:
                invoice_data["due_date"] = match.group(1).strip()
                break
        
        # Buscar datos de proveedor y cliente en las primeras tablas
        for table in tables[:2]:  # Normalmente en las primeras tablas
            if table.empty:
                continue
            
            # Reemplazar NaN por cadenas vacías
            table_clean = table.fillna("")
            table_text = table_clean.to_string(index=False)
            
            # Nombre del proveedor
            if not invoice_data["supplier_name"]:
                for i, row in table.iterrows():
                    row_text = " ".join([str(x) for x in row.values if pd.notna(x)])
                    if len(row_text.strip()) > 3 and not re.match(r'^[0-9\s\.\/\-\:]+$', row_text.strip()):
                        invoice_data["supplier_name"] = row_text.strip()
                        break
            
            # NIF/CIF del proveedor
            vat_patterns = [
                r'(?:NIF|CIF|VAT|Tax ID)[\s:]*([A-Za-z0-9\-]+)',
                r'([A-Z][0-9]{8}[A-Z])',  # Formato NIF/CIF español
                r'([0-9]{8}[A-Z])'  # Formato NIF español sin letra inicial
            ]
            for pattern in vat_patterns:
                match = re.search(pattern, table_text, re.IGNORECASE)
                if match:
                    invoice_data["supplier_vat"] = match.group(1).strip() if len(match.groups()) > 0 else match.group(0).strip()
                    break
        
        # Buscar importes en tablas que parecen contener totales
        for table in tables:
            if table.empty:
                continue
            
            # Reemplazar NaN por cadenas vacías
            table_clean = table.fillna("")
            table_text = table_clean.to_string(index=False).lower()
            
            # Total
            if "total" in table_text:
                for i, row in table.iterrows():
                    row_text = " ".join([str(x) for x in row.values if pd.notna(x)]).lower()
                    if "total" in row_text:
                        # Buscar un número en esta fila
                        amount_match = re.search(r'([0-9\.\,]+)', row_text)
                        if amount_match:
                            try:
                                amount_str = amount_match.group(1).replace('.', '').replace(',', '.')
                                invoice_data["total_amount"] = float(amount_str)
                            except ValueError:
                                pass
            
            # Base imponible / Subtotal
            if "base" in table_text or "subtotal" in table_text or "imponible" in table_text:
                for i, row in table.iterrows():
                    row_text = " ".join([str(x) for x in row.values if pd.notna(x)]).lower()
                    if "base" in row_text or "subtotal" in row_text or "imponible" in row_text:
                        # Buscar un número en esta fila
                        amount_match = re.search(r'([0-9\.\,]+)', row_text)
                        if amount_match:
                            try:
                                amount_str = amount_match.group(1).replace('.', '').replace(',', '.')
                                invoice_data["subtotal"] = float(amount_str)
                            except ValueError:
                                pass
            
            # IVA
            if "iva" in table_text or "vat" in table_text or "impuesto" in table_text:
                for i, row in table.iterrows():
                    row_text = " ".join([str(x) for x in row.values if pd.notna(x)]).lower()
                    if "iva" in row_text or "vat" in row_text or "impuesto" in row_text:
                        # Buscar un número en esta fila
                        amount_match = re.search(r'([0-9\.\,]+)', row_text)
                        if amount_match:
                            try:
                                amount_str = amount_match.group(1).replace('.', '').replace(',', '.')
                                invoice_data["tax_amount"] = float(amount_str)
                            except ValueError:
                                pass
                        
                        # Buscar porcentaje de IVA
                        rate_match = re.search(r'([0-9\.\,]+)[\s]*%', row_text)
                        if rate_match:
                            try:
                                rate_str = rate_match.group(1).replace(',', '.')
                                invoice_data["tax_rate"] = float(rate_str)
                            except ValueError:
                                pass
        
        # Extraer recargo de equivalencia
        recargo = self.extract_recargo_equivalencia(tables)
        if recargo is not None:
            invoice_data["recargo_equivalencia"] = recargo
            invoice_data["recargo_rate"] = recargo
        
        # Intentar extraer líneas de productos
        invoice_table = self.find_invoice_table(tables)
        if invoice_table is not None and not invoice_table.empty:
            # Reemplazar NaN por cadenas vacías
            invoice_table = invoice_table.fillna("")
            lines = []
            for i, row in invoice_table.iterrows():
                # Ignorar filas que parecen encabezados o totales
                row_text = " ".join([str(x) for x in row.values if pd.notna(x)]).lower()
                if "total" in row_text or "subtotal" in row_text or row_text.strip() == "":
                    continue
                
                # Crear línea de producto
                line = {
                    "quantity": None,
                    "description": "",
                    "price_unit": None,
                    "price_total": None
                }
                
                # Intentar extraer datos de la línea
                for col in invoice_table.columns:
                    col_name = str(col).lower()
                    cell_value = row[col]
                    
                    # Ya hemos reemplazado NaN por cadenas vacías, pero por si acaso
                    if pd.isna(cell_value) or cell_value == "":
                        continue
                    
                    cell_str = str(cell_value)
                    
                    # Descripción
                    if "desc" in col_name or len(cell_str) > 15:
                        line["description"] = cell_str.strip()
                    
                    # Cantidad
                    elif "cant" in col_name or "uds" in col_name or "unid" in col_name:
                        try:
                            line["quantity"] = float(cell_str.replace('.', '').replace(',', '.'))
                        except ValueError:
                            pass
                    
                    # Precio unitario
                    elif "precio" in col_name or "unit" in col_name:
                        try:
                            line["price_unit"] = float(cell_str.replace('.', '').replace(',', '.'))
                        except ValueError:
                            pass
                    
                    # Precio total
                    elif "total" in col_name or "importe" in col_name:
                        try:
                            line["price_total"] = float(cell_str.replace('.', '').replace(',', '.'))
                        except ValueError:
                            pass
                
                # Añadir línea si tiene al menos descripción o cantidad
                if line["description"] or line["quantity"]:
                    lines.append(line)
            
            if lines:
                invoice_data["lines"] = lines
        
        return invoice_data
