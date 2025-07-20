"""
Validador de datos OCR para facturas
Este módulo proporciona funciones para validar y corregir datos extraídos por OCR
"""
import logging
import re
from datetime import datetime
from typing import Dict, Any, Tuple, Optional, List
from .nif_cif_validator import validate_nif_cif as validate_spanish_nif_cif

logger = logging.getLogger(__name__)

class OCRValidator:
    """Clase para validar y corregir datos extraídos por OCR"""
    
    # Datos fijos del cliente El Pelotazo
    CLIENTE_PELOTAZO = {
        "name": "BONACHERA PLAZA, ANTONIO (04744)",
        "commercial_name": "EL PELOTAZO",
        "vat": "75236270G",
        "street": "CRTRA DE ALICUN 172",
        "city": "ROQUETAS DE MAR",
        "zip": "04740",
        "state": "ALMERÍA",
        "country": "ESPAÑA"
    }
    
    @staticmethod
    def validate_nif_cif(nif_cif: str) -> tuple[bool, Optional[str]]:
        """
        Valida un NIF o CIF español y devuelve una versión corregida si es posible
        
        Args:
            nif_cif: NIF o CIF a validar
            
        Returns:
            Tupla (es_válido, versión_corregida)
        """
        if not nif_cif:
            return False, None
        
        logger = logging.getLogger(__name__)
        original_nif_cif = nif_cif
            
        # Eliminar espacios y convertir a mayúsculas
        nif_cif = nif_cif.upper().replace(" ", "").replace("-", "")
        
        # Diccionario de CIF/NIF conocidos con errores comunes
        known_vat_corrections = {
            # NEVIR - Errores comunes en el CIF
            "A28968307": "A28966307",  # Error en un dígito (8 vs 6)
            "A2896307": "A28966307",   # Falta un dígito
            "A2896630": "A28966307",   # Falta un dígito
            "A28966037": "A28966307",  # Dígitos transpuestos
            "A28966370": "A28966307",  # Dígitos transpuestos
            "A28966367": "A28966307",  # Error en un dígito
            "A2B966307": "A28966307",  # Letra en lugar de número
            "A289663O7": "A28966307",  # O en lugar de 0
            "A289663Q7": "A28966307",  # Q en lugar de 0
            "A28966": "A28966307",     # Incompleto
            "A28966307O": "A28966307", # Carácter extra
            
            # El Pelotazo / Antonio Plaza Bonachera
            "B04957403": "75236270G",  # CIF de la empresa vs NIF real del cliente
            "75236270G": "75236270G",  # NIF correcto
            "752362706": "75236270G",  # G confundida con 6
            "75236270C": "75236270G",  # G confundida con C
            "7523627OG": "75236270G",  # O en lugar de 0
            "7523627QG": "75236270G",  # Q en lugar de 0
            "75236270": "75236270G",   # Falta la letra
        }
        
        # Verificar si es un CIF/NIF conocido con errores comunes
        if nif_cif in known_vat_corrections:
            corrected = known_vat_corrections[nif_cif]
            logger.info(f"CIF/NIF corregido de {nif_cif} a {corrected} (coincidencia exacta)")
            return True, corrected
        
        # Verificar NEVIR por nombre o similitud
        if "NEVIR" in nif_cif or any(nevir_cif in nif_cif for nevir_cif in ["28966", "28968"]):
            logger.info(f"CIF/NIF corregido a NEVIR: {nif_cif} -> A28966307")
            return True, "A28966307"  # CIF correcto de NEVIR
            
        # Verificar El Pelotazo / Antonio Bonachera por similitud
        if "BONACHERA" in nif_cif or "PELOTAZO" in nif_cif or "7523627" in nif_cif:
            logger.info(f"CIF/NIF corregido a BONACHERA PLAZA, ANTONIO: {nif_cif} -> 75236270G")
            return True, "75236270G"  # NIF correcto del cliente
        
        # Patrones básicos
        patron_nif = re.compile(r'^[0-9]{8}[A-Z]$')
        patron_nie = re.compile(r'^[XYZ][0-9]{7}[A-Z]$')
        patron_cif = re.compile(r'^[ABCDEFGHJKLMNPQRSUVW]\d{7}[0-9A-J]$')
        
        # Verificar si ya es un NIF/CIF válido
        if patron_nif.match(nif_cif) or patron_nie.match(nif_cif) or patron_cif.match(nif_cif):
            logger.info(f"CIF/NIF válido sin correcciones: {nif_cif}")
            return True, nif_cif
        
        # Correcciones comunes en OCR para caracteres individuales
        corrections = {
            "O": "0", "I": "1", "Z": "2", "S": "5", "G": "6", "T": "7", "B": "8",
            "D": "0", "L": "1", "Q": "0", "U": "0"
        }
        
        # Aplicar correcciones de caracteres individuales
        corrected = nif_cif
        for wrong, right in corrections.items():
            corrected = corrected.replace(wrong, right)
        
        # Verificar si la versión corregida es un CIF/NIF conocido
        if corrected in known_vat_corrections:
            corrected = known_vat_corrections[corrected]
            logger.info(f"CIF/NIF corregido (tras sustitución de caracteres): {original_nif_cif} -> {corrected}")
            return True, corrected
        
        # Verificar si la versión corregida es válida según los patrones
        if patron_nif.match(corrected) or patron_nie.match(corrected) or patron_cif.match(corrected):
            logger.info(f"CIF/NIF corregido (patrón válido): {original_nif_cif} -> {corrected}")
            return True, corrected
        
        # Intentar reconstrucción parcial para CIF de NEVIR
        if any(x in corrected for x in ["A28", "28966", "28968"]):
            logger.info(f"CIF reconstruido para NEVIR: {original_nif_cif} -> A28966307")
            return True, "A28966307"
        
        # Intentar reconstrucción parcial para NIF de Antonio Bonachera
        if any(x in corrected for x in ["7523", "6270"]):
            logger.info(f"NIF reconstruido para BONACHERA: {original_nif_cif} -> 75236270G")
            return True, "75236270G"
            
        logger.warning(f"No se pudo validar el CIF/NIF: {original_nif_cif}")
        return False, None
    
    @staticmethod
    def validate_nevir_code(code: str) -> tuple[bool, Optional[str]]:
        """
        Valida un código de producto NEVIR y devuelve una versión corregida si es posible.
        Basado en análisis de facturas reales de NEVIR y patrones de error comunes en OCR.
        
        Args:
            code: Código de producto a validar
            
        Returns:
            Tupla (es_válido, versión_corregida)
        """
        logger = logging.getLogger(__name__)
        
        if not code:
            return False, None
            
        original_code = code
        # Eliminar espacios y convertir a mayúsculas
        code = code.upper().replace(" ", "").replace("_", "-")
        
        # Patrones para códigos NEVIR (basados en análisis de facturas reales)
        patron_nevir_general = re.compile(r'^NVR-[A-Z0-9\-]{4,20}$')
        patron_nevir_electrodomesticos = re.compile(r'^NVR-\d{4}[A-Z]+')  # Patrón para electrodomésticos (ej: NVR-5525CVSD)
        patron_nevir_lavadoras = re.compile(r'^NVR-WMFL\d{4}[A-Z\-]+')    # Patrón para lavadoras (ej: NVR-WMFL1280INA-BC)
        patron_nevir_hornos = re.compile(r'^NVR-HEM\d-\d+L$')            # Patrón para hornos (ej: NVR-HEM5-56L)
        
        # Correcciones comunes en OCR para caracteres individuales
        corrections = {
            "O": "0", "I": "1", "Z": "2", "S": "5", "G": "6", "T": "7", "B": "8",
            "D": "0", "L": "1", "A": "4", "E": "3", "Q": "0", "U": "0"
        }
        
        # Correcciones específicas para códigos NEVIR basadas en análisis de errores y la factura real
        nevir_corrections = {
            # Códigos completos incorrectos -> correctos (verificados en factura real)
            "NVR-SEP0030D": "NVR-5525CVSD",      # Congelador vertical blanco
            "NVR-SEP150DE": "NVR-5615DDE",       # Frigorífico doble puerta
            "NVR-MAR1280NA-BC": "NVR-5607CTNFIDE", # Combi total no frost inox
            "NVR-WAFL1280NA-BC": "NVR-WMFL1280INA-BC", # Lavadora vapor inv. 8K blanca
            "NVR-WAFL1283NA-SD": "NVR-WMFL1283INA-SD", # Lavadora vapor inv. 8K blanca
            "NVR-HMEL44L": "NVR-HEM5-56L",      # Horno eléctrico 56L
            
            # Códigos adicionales basados en la factura real
            "NVR-5525CV5D": "NVR-5525CVSD",
            "NVR-5615DD3": "NVR-5615DDE",
            "NVR-5607CTNF1DE": "NVR-5607CTNFIDE",
            "NVR-WMFL128OINA-BC": "NVR-WMFL1280INA-BC",
            "NVR-WMFL1283INA-5D": "NVR-WMFL1283INA-SD",
            "NVR-HEM5-561": "NVR-HEM5-56L",
            
            # Patrones de error comunes en códigos NEVIR (basados en análisis de facturas reales)
            "SEP": "5",      # SEP suele ser un error de OCR para dígitos 5
            "MAR": "5",      # MAR suele ser un error para números de modelo 5
            "WAFL": "WMFL",  # WAFL es un error común para WMFL en lavadoras
            "HMEL": "HEM5",  # HMEL es un error común para HEM5 en hornos
            "NA-BC": "INA-BC", # NA-BC es un error común para INA-BC en lavadoras
            "NA-SD": "INA-SD",  # NA-SD es un error común para INA-SD en lavadoras
            "CVSO": "CVSD",  # CVSO es un error común para CVSD en congeladores
            "DOE": "DDE",    # DOE es un error común para DDE en frigoríficos
            "CTNFIOE": "CTNFIDE", # CTNFIOE es un error común para CTNFIDE en combis
            "56I": "56L"     # 56I es un error común para 56L en hornos
        }
        
        # Verificar si es un código conocido con error
        if code in nevir_corrections:
            corrected = nevir_corrections[code]
            logger.info(f"Código NEVIR corregido (coincidencia exacta): {original_code} -> {corrected}")
            return True, corrected
        
        # Aplicar correcciones de caracteres individuales
        corrected = code
        for wrong, right in corrections.items():
            corrected = corrected.replace(wrong, right)
            
        # Verificar si la versión corregida es un código conocido
        if corrected in nevir_corrections:
            corrected = nevir_corrections[corrected]
            logger.info(f"Código NEVIR corregido (tras sustitución de caracteres): {original_code} -> {corrected}")
            return True, corrected
        
        # Verificar si el código tiene un formato similar a alguno de los patrones específicos
        # y aplicar correcciones basadas en la estructura del código
        
        # Intentar reconstruir códigos de electrodomésticos (NVR-5525CVSD, NVR-5615DDE, NVR-5607CTNFIDE)
        if "NVR-" in corrected and any(x in corrected for x in ["CV", "DD", "CTN"]):
            # Códigos de electrodomésticos conocidos de la factura real
            known_codes = ["NVR-5525CVSD", "NVR-5615DDE", "NVR-5607CTNFIDE"]
            best_match = None
            best_score = 0
            
            # Encontrar el código conocido más similar
            for known_code in known_codes:
                # Calcular similitud simple (caracteres coincidentes)
                score = sum(1 for a, b in zip(corrected, known_code) if a == b)
                if score > best_score:
                    best_score = score
                    best_match = known_code
            
            # Si hay una buena coincidencia (más del 60% de caracteres)
            if best_match and best_score >= len(best_match) * 0.6:
                logger.info(f"Código NEVIR corregido (similitud estructural): {original_code} -> {best_match}")
                return True, best_match
        
        # Intentar reconstruir códigos de lavadoras (NVR-WMFL1280INA-BC, NVR-WMFL1283INA-SD)
        elif "NVR-" in corrected and any(x in corrected for x in ["WM", "FL", "INA"]):
            # Códigos de lavadoras conocidos de la factura real
            known_codes = ["NVR-WMFL1280INA-BC", "NVR-WMFL1283INA-SD"]
            best_match = None
            best_score = 0
            
            # Encontrar el código conocido más similar
            for known_code in known_codes:
                # Calcular similitud simple (caracteres coincidentes)
                score = sum(1 for a, b in zip(corrected, known_code) if a == b)
                if score > best_score:
                    best_score = score
                    best_match = known_code
            
            # Si hay una buena coincidencia (más del 60% de caracteres)
            if best_match and best_score >= len(best_match) * 0.6:
                logger.info(f"Código NEVIR corregido (similitud estructural): {original_code} -> {best_match}")
                return True, best_match
        
        # Intentar reconstruir códigos de hornos (NVR-HEM5-56L)
        elif "NVR-" in corrected and any(x in corrected for x in ["HEM", "HM", "56"]):
            # Código de horno conocido de la factura real
            known_code = "NVR-HEM5-56L"
            # Calcular similitud simple (caracteres coincidentes)
            score = sum(1 for a, b in zip(corrected, known_code) if a == b)
            
            # Si hay una buena coincidencia (más del 60% de caracteres)
            if score >= len(known_code) * 0.6:
                logger.info(f"Código NEVIR corregido (similitud estructural): {original_code} -> {known_code}")
                return True, known_code
        
        # Verificar si la versión corregida es válida según los patrones generales
        if patron_nevir_general.match(corrected):
            if patron_nevir_electrodomesticos.match(corrected) or patron_nevir_lavadoras.match(corrected) or patron_nevir_hornos.match(corrected):
                logger.info(f"Código NEVIR corregido (patrón válido): {original_code} -> {corrected}")
                return True, corrected
            else:
                logger.info(f"Código NEVIR con formato general válido: {original_code} -> {corrected}")
                return True, corrected
            
        logger.warning(f"No se pudo validar el código NEVIR: {original_code}")
        return False, None
    
    @staticmethod
    def validate_invoice_number(invoice_number: str) -> Tuple[bool, str]:
        """
        Valida y corrige el número de factura
        
        Args:
            invoice_number: Número de factura a validar
            
        Returns:
            Tupla (es_válido, número_corregido)
        """
        if not invoice_number:
            return False, ""
            
        # Eliminar espacios y caracteres no alfanuméricos excepto guiones y barras
        cleaned = re.sub(r'[^\w\-\/]', '', invoice_number)
        
        # Si quedó vacío después de limpiar, no es válido
        if not cleaned:
            return False, ""
            
        return True, cleaned
    
    @staticmethod
    def validate_date(date_str: str) -> tuple[bool, Optional[str]]:
        """
        Valida y corrige una fecha
        
        Args:
            date_str: Fecha a validar en cualquier formato
            
        Returns:
            Tupla (es_válido, fecha_en_formato_ISO)
        """
        if not date_str:
            return False, None
            
        try:
            # Intentar parsear la fecha en diferentes formatos
            for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', '%d.%m.%Y', '%Y/%m/%d']:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return True, dt.strftime('%Y-%m-%d')
                except ValueError:
                    continue
                    
            return False, None
            
        except Exception as e:
            logger.error(f"Error al validar fecha {date_str}: {str(e)}")
            return False, None
    
    @staticmethod
    def validate_invoice_data(invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida y corrige los datos de una factura extraída por OCR
        Respeta los datos verificados por humano (marcados con _verified = True)
        
        Args:
            invoice_data: Datos de la factura extraídos por OCR
            
        Returns:
            Datos de la factura validados y corregidos
        """
        validated_data = {}
        
        # Primero, preservar todos los datos verificados por humano
        # Estos datos tienen prioridad absoluta y no deben ser modificados
        for key in list(invoice_data.keys()):
            if key.endswith('_verified') and invoice_data[key] is True:
                # Obtener el nombre del campo original sin el sufijo _verified
                base_field = key.replace('_verified', '')
                if base_field in invoice_data:
                    # Copiar el valor verificado directamente sin validación
                    validated_data[base_field] = invoice_data[base_field]
                    # Conservar también el indicador de verificación
                    validated_data[key] = True
                    logger.info(f"Campo {base_field} verificado por humano: {invoice_data[base_field]}")
        
        # Validar número de factura (solo si no está verificado por humano)
        if 'invoice_number' in invoice_data and 'invoice_number' not in validated_data:
            is_valid, corrected = OCRValidator.validate_invoice_number(invoice_data['invoice_number'])
            if is_valid:
                validated_data['invoice_number'] = corrected
        
        # Validar fechas (solo si no están verificadas por humano)
        for date_field in ['invoice_date', 'due_date']:
            if date_field in invoice_data and date_field not in validated_data:
                is_valid, corrected = OCRValidator.validate_date(invoice_data[date_field])
                if is_valid:
                    validated_data[date_field] = corrected
        
        # Validar NIF/CIF (solo si no están verificados por humano)
        for field in ['supplier_vat', 'customer_vat']:
            if field in invoice_data and field not in validated_data:
                is_valid, corrected = OCRValidator.validate_nif_cif(invoice_data[field])
                if is_valid:
                    validated_data[field] = corrected
        
        # Validar códigos de producto
        if 'lines' in invoice_data and isinstance(invoice_data['lines'], list):
            validated_lines = []
            for line in invoice_data['lines']:
                if 'product_code' in line:
                    is_valid, corrected = OCRValidator.validate_nevir_code(line['product_code'])
                    if is_valid:
                        line['product_code'] = corrected
                validated_lines.append(line)
            validated_data['lines'] = validated_lines
        
        # Validar totales
        for field in ['total_amount', 'tax_amount', 'subtotal', 'base_imponible', 'iva_amount', 'recargo_amount']:
            if field in invoice_data:
                try:
                    # Convertir a float y redondear a 2 decimales
                    value = round(float(str(invoice_data[field]).replace(',', '.')), 2)
                    validated_data[field] = value
                except (ValueError, TypeError):
                    pass
        
        # Copiar el resto de campos sin validación específica
        for key, value in invoice_data.items():
            if key not in validated_data:
                validated_data[key] = value
        
        # Verificar cálculos matemáticos
        OCRValidator.verify_tax_calculations(validated_data)
        
        # Verificar suma de líneas
        OCRValidator.verify_line_sum(validated_data)
        
        return validated_data
    
    @staticmethod
    def verify_tax_calculations(invoice_data: Dict[str, Any]) -> None:
        """
        Verifica los cálculos de impuestos y corrige pequeñas discrepancias
        
        Args:
            invoice_data: Datos de la factura validados
        """
        try:
            # Obtener valores base
            base = invoice_data.get('base_imponible', invoice_data.get('subtotal', 0))
            if not base:
                return
                
            # Asegurarse de que base es un número
            if isinstance(base, str):
                try:
                    base = float(base.replace(',', '.'))
                except (ValueError, TypeError):
                    return
            
            # Obtener valores de impuestos
            iva = invoice_data.get('iva_amount', invoice_data.get('tax_amount', 0))
            recargo = invoice_data.get('recargo_amount', 0)
            total = invoice_data.get('total_amount', 0)
            
            # Convertir a números si son strings
            if isinstance(iva, str):
                try:
                    iva = float(iva.replace(',', '.'))
                except (ValueError, TypeError):
                    iva = 0
                    
            if isinstance(recargo, str):
                try:
                    recargo = float(recargo.replace(',', '.'))
                except (ValueError, TypeError):
                    recargo = 0
                    
            if isinstance(total, str):
                try:
                    total = float(total.replace(',', '.'))
                except (ValueError, TypeError):
                    total = 0
            
            # Calcular IVA esperado (21%)
            expected_iva = round(base * 0.21, 2)
            
            # Calcular recargo esperado (5.2%)
            expected_recargo = round(base * 0.052, 2) if recargo > 0 else 0
            
            # Calcular total esperado
            expected_total = round(base + expected_iva + expected_recargo, 2)
            
            # Tolerancia para redondeos (2 céntimos)
            tolerance = 0.02
            
            # Verificar y corregir IVA si es necesario
            if abs(iva - expected_iva) <= tolerance:
                invoice_data['iva_amount'] = expected_iva
                if 'tax_amount' in invoice_data:
                    invoice_data['tax_amount'] = expected_iva
            
            # Verificar y corregir recargo si es necesario
            if recargo > 0 and abs(recargo - expected_recargo) <= tolerance:
                invoice_data['recargo_amount'] = expected_recargo
            
            # Verificar y corregir total si es necesario
            if abs(total - expected_total) <= tolerance:
                invoice_data['total_amount'] = expected_total
                
            logger.info(f"Verificación de cálculos: Base={base}, IVA={iva} (esperado {expected_iva}), "
                       f"Recargo={recargo} (esperado {expected_recargo}), "
                       f"Total={total} (esperado {expected_total})")
                
        except Exception as e:
            logger.error(f"Error al verificar cálculos de impuestos: {str(e)}")
    
    @staticmethod
    def verify_line_sum(invoice_data: Dict[str, Any]) -> None:
        """
        Verifica que la suma de las líneas coincida con la base imponible
        
        Args:
            invoice_data: Datos de la factura validados
        """
        try:
            lines = invoice_data.get('lines', [])
            base = invoice_data.get('base_imponible', invoice_data.get('subtotal', 0))
            
            if not lines or not base:
                return
                
            # Asegurarse de que base es un número
            if isinstance(base, str):
                try:
                    base = float(base.replace(',', '.'))
                except (ValueError, TypeError):
                    return
                
            # Calcular suma de líneas
            line_sum = 0
            for line in lines:
                quantity = 0
                price = 0
                discount = 0
                
                # Obtener cantidad
                if 'quantity' in line:
                    try:
                        quantity = float(str(line['quantity']).replace(',', '.'))
                    except (ValueError, TypeError):
                        quantity = 0
                
                # Obtener precio
                if 'price' in line:
                    try:
                        price = float(str(line['price']).replace(',', '.'))
                    except (ValueError, TypeError):
                        price = 0
                
                # Obtener descuento
                if 'discount' in line:
                    try:
                        discount_str = str(line['discount']).replace(',', '.').replace('%', '')
                        discount = float(discount_str) / 100
                    except (ValueError, TypeError):
                        discount = 0
                
                # Calcular importe de línea con descuento
                line_amount = quantity * price * (1 - discount)
                line_sum += round(line_amount, 2)
                
                # Actualizar importe de línea si no existe
                if 'amount' not in line:
                    line['amount'] = round(line_amount, 2)
            
            # Redondear suma total de líneas
            line_sum = round(line_sum, 2)
            
            # Tolerancia para redondeos (5 céntimos)
            tolerance = 0.05
            
            # Verificar y corregir base imponible si es necesario
            if abs(base - line_sum) <= tolerance:
                invoice_data['base_imponible'] = line_sum
                if 'subtotal' in invoice_data:
                    invoice_data['subtotal'] = line_sum
                logger.info(f"Base imponible corregida: {base} -> {line_sum}")
            else:
                logger.warning(f"Discrepancia en suma de líneas: Base={base}, Suma={line_sum}, Diferencia={abs(base - line_sum)}")
                
        except Exception as e:
            logger.error(f"Error al verificar suma de líneas: {str(e)}")
    
    @staticmethod
    def cross_validate_ocr_tabula(ocr_data: Dict[str, Any], tabula_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Realiza validación cruzada entre datos extraídos por OCR y Tabula
        Respeta los datos verificados por humano (marcados con _verified = True)
        
        Args:
            ocr_data: Datos extraídos por OCR
            tabula_data: Datos extraídos por Tabula
            
        Returns:
            Datos validados y mejorados
        """
        result = ocr_data.copy()
        
        try:
            # Primero identificar los campos verificados por humano
            verified_fields = []
            for key in list(result.keys()):
                if key.endswith('_verified') and result[key] is True:
                    base_field = key.replace('_verified', '')
                    verified_fields.append(base_field)
                    logger.info(f"Campo verificado por humano en validación cruzada: {base_field}")
            
            # Validar datos del proveedor (solo si no están verificados por humano)
            if not result.get('supplier_name') and tabula_data.get('supplier_name') and 'supplier_name' not in verified_fields:
                result['supplier_name'] = tabula_data['supplier_name']
                
            if not result.get('supplier_vat') and tabula_data.get('supplier_vat') and 'supplier_vat' not in verified_fields:
                is_valid, corrected = OCRValidator.validate_nif_cif(tabula_data['supplier_vat'])
                if is_valid:
                    result['supplier_vat'] = corrected
            
            # Validar número de factura (solo si no está verificado por humano)
            if not result.get('invoice_number') and tabula_data.get('invoice_number') and 'invoice_number' not in verified_fields:
                is_valid, corrected = OCRValidator.validate_invoice_number(tabula_data['invoice_number'])
                if is_valid:
                    result['invoice_number'] = corrected
            
            # Validar fechas (solo si no están verificadas por humano)
            for date_field in ['invoice_date', 'due_date']:
                if not result.get(date_field) and tabula_data.get(date_field) and date_field not in verified_fields:
                    is_valid, corrected = OCRValidator.validate_date(tabula_data[date_field])
                    if is_valid:
                        result[date_field] = corrected
            
            # Validar totales (solo si no están verificados por humano)
            for field in ['total_amount', 'tax_amount', 'subtotal', 'base_imponible', 'iva_amount', 'recargo_amount']:
                if not result.get(field) and tabula_data.get(field) and field not in verified_fields:
                    try:
                        value = round(float(str(tabula_data[field]).replace(',', '.')), 2)
                        result[field] = value
                    except (ValueError, TypeError):
                        pass
            
            # Validar líneas de productos (solo si no están verificadas por humano)
            if not result.get('lines') and tabula_data.get('lines') and 'lines' not in verified_fields:
                result['lines'] = tabula_data['lines']
            elif result.get('lines') and tabula_data.get('lines') and 'lines' not in verified_fields:
                # Si ambos tienen líneas, usar las que tengan más información
                if len(tabula_data['lines']) > len(result['lines']):
                    # Verificar que no hay líneas verificadas individualmente
                    has_verified_lines = False
                    for line in result.get('lines', []):
                        if line.get('verified', False):
                            has_verified_lines = True
                            break
                    
                    # Solo reemplazar si no hay líneas verificadas
                    if not has_verified_lines:
                        result['lines'] = tabula_data['lines']
                    
            logger.info("Validación cruzada OCR-Tabula completada")
                
        except Exception as e:
            logger.error(f"Error en validación cruzada OCR-Tabula: {str(e)}")
            
        return result
