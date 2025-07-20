#!/usr/bin/env python3
"""
Módulo de OCR optimizado para facturas
Implementa detección automática de tipo de documento y procesamiento adaptativo
"""
import os
import re
import time
import logging
import cv2
import numpy as np
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
from typing import Dict, Any, List, Tuple, Optional, Union

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Patrones para detectar tipos de documentos
DOCUMENT_PATTERNS = {
    'nevir': ['nevir', 'facturaf24'],
    'abrila': ['abrila', '32506198'],
    'bsh': ['bsh', 'balay', 'siemens', 'bosch'],
    'general': []  # Fallback
}

# Configuraciones óptimas de Tesseract por tipo de documento
TESSERACT_CONFIGS = {
    'nevir': '--oem 1 --psm 3 -c preserve_interword_spaces=1 -c textord_tablefind_recognize_tables=1',
    'abrila': '--oem 1 --psm 1 -c preserve_interword_spaces=1',
    'bsh': '--oem 1 --psm 4 -c preserve_interword_spaces=1 -c textord_tabfind_find_tables=1',
    'general': '--oem 1 --psm 3'  # Configuración general
}

# Parámetros de preprocesamiento por tipo de documento
PREPROCESSING_PARAMS = {
    'nevir': {
        'blur_kernel': (3, 3),
        'threshold_block_size': 15,
        'threshold_c': 8,
        'morph_kernel_size': 1,
        'clahe_clip_limit': 2.0,
        'clahe_grid_size': (8, 8),
        'use_deskew': True,
        'use_clahe': True
    },
    'abrila': {
        'blur_kernel': (3, 3),
        'threshold_block_size': 11,
        'threshold_c': 2,
        'morph_kernel_size': 1,
        'clahe_clip_limit': 2.5,
        'clahe_grid_size': (8, 8),
        'use_deskew': True,
        'use_clahe': True
    },
    'bsh': {
        'blur_kernel': (5, 5),
        'threshold_block_size': 11,
        'threshold_c': 2,
        'morph_kernel_size': 1,
        'clahe_clip_limit': 3.0,
        'clahe_grid_size': (4, 4),
        'use_deskew': True,
        'use_clahe': True
    },
    'general': {
        'blur_kernel': (3, 3),
        'threshold_block_size': 11,
        'threshold_c': 2,
        'morph_kernel_size': 1,
        'clahe_clip_limit': 2.0,
        'clahe_grid_size': (8, 8),
        'use_deskew': True,
        'use_clahe': False  # Para documentos generales, CLAHE puede no ser beneficioso
    }
}

# Caché de OCR para evitar reprocesamiento
OCR_CACHE = {}

def detect_document_type(image: Union[np.ndarray, Image.Image]) -> str:
    """
    Detecta el tipo de documento basado en el texto extraído
    
    Args:
        image: Imagen a analizar (numpy array o PIL Image)
        
    Returns:
        str: Tipo de documento detectado ('nevir', 'abrila', 'bsh', 'general')
    """
    # Convertir a escala de grises si es necesario
    if isinstance(image, np.ndarray):
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
    else:  # PIL Image
        gray = np.array(image.convert('L'))
    
    # Extraer texto para detectar el tipo
    text = pytesseract.image_to_string(gray, lang='spa', config='--psm 11').lower()
    
    # Buscar patrones específicos
    for doc_type, patterns in DOCUMENT_PATTERNS.items():
        if doc_type != 'general':  # Saltamos el tipo general que es el fallback
            for pattern in patterns:
                if pattern.lower() in text:
                    logger.info(f"Tipo de documento detectado: {doc_type}")
                    return doc_type
    
    # Si no se encuentra ningún patrón específico, devolver tipo general
    logger.info("Tipo de documento no reconocido, usando configuración general")
    return 'general'

def get_optimal_tesseract_config(doc_type: str) -> str:
    """
    Obtiene la configuración óptima de Tesseract para el tipo de documento
    
    Args:
        doc_type: Tipo de documento ('nevir', 'abrila', 'bsh', 'general')
        
    Returns:
        str: Configuración de Tesseract optimizada
    """
    return TESSERACT_CONFIGS.get(doc_type, TESSERACT_CONFIGS['general'])

def preprocess_image(image: Union[np.ndarray, Image.Image], doc_type: str = 'general') -> np.ndarray:
    """
    Preprocesamiento avanzado de imagen para OCR con parámetros específicos por tipo de documento
    
    Args:
        image: Imagen a preprocesar (numpy array o PIL Image)
        doc_type: Tipo de documento ('nevir', 'abrila', 'bsh', 'general')
        
    Returns:
        np.ndarray: Imagen preprocesada
    """
    # Convertir a escala de grises si es necesario
    if isinstance(image, np.ndarray):
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
    else:  # PIL Image
        gray = np.array(image.convert('L'))
    
    # Obtener parámetros específicos para el tipo de documento
    params = PREPROCESSING_PARAMS.get(doc_type, PREPROCESSING_PARAMS['general'])
    
    # Aplicar desenfoque gaussiano para reducir ruido
    blurred = cv2.GaussianBlur(gray, params['blur_kernel'], 0)
    
    # Aplicar ecualización de histograma adaptativa (CLAHE) si está habilitado
    if params.get('use_clahe', False):
        clahe = cv2.createCLAHE(
            clipLimit=params['clahe_clip_limit'],
            tileGridSize=params['clahe_grid_size']
        )
        equalized = clahe.apply(blurred)
    else:
        equalized = blurred
    
    # Aplicar umbralización adaptativa
    binary = cv2.adaptiveThreshold(
        equalized,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        params['threshold_block_size'],
        params['threshold_c']
    )
    
    # Aplicar operaciones morfológicas si es necesario
    if params['morph_kernel_size'] > 0:
        kernel = np.ones((params['morph_kernel_size'], params['morph_kernel_size']), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
    
    return binary

def deskew_image(image: np.ndarray) -> np.ndarray:
    """
    Corrige la inclinación de la imagen
    
    Args:
        image: Imagen a corregir
        
    Returns:
        np.ndarray: Imagen corregida
    """
    # Asegurarse de que la imagen esté en escala de grises
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    
    # Detectar bordes
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    
    # Detectar líneas usando la transformada de Hough
    lines = cv2.HoughLines(edges, 1, np.pi/180, 100)
    
    if lines is not None and len(lines) > 0:
        # Calcular ángulos
        angles = []
        for line in lines:
            rho, theta = line[0]
            # Convertir a grados y normalizar entre -90 y 90
            angle_deg = np.degrees(theta) - 90
            if angle_deg < -45:
                angle_deg += 90
            elif angle_deg > 45:
                angle_deg -= 90
            
            # Solo considerar ángulos pequeños (menores a 30 grados)
            if abs(angle_deg) < 30:
                angles.append(angle_deg)
        
        if angles:
            # Usar la mediana para evitar valores atípicos
            median_angle = np.median(angles)
            
            # Solo corregir si el ángulo es significativo
            if abs(median_angle) > 0.5:
                # Obtener dimensiones de la imagen
                (h, w) = gray.shape[:2]
                center = (w // 2, h // 2)
                
                # Rotar la imagen
                M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                rotated = cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
                return rotated
    
    # Si no se detectaron líneas o el ángulo no es significativo, devolver la imagen original
    return gray

def extract_text_from_image(image: Union[np.ndarray, Image.Image], doc_type: str = 'general') -> str:
    """
    Extrae texto de una imagen usando OCR optimizado
    
    Args:
        image: Imagen a procesar
        doc_type: Tipo de documento
        
    Returns:
        str: Texto extraído
    """
    # Preprocesar la imagen
    processed = preprocess_image(image, doc_type)
    
    # Aplicar corrección de inclinación si está habilitado para este tipo de documento
    params = PREPROCESSING_PARAMS.get(doc_type, PREPROCESSING_PARAMS['general'])
    if params.get('use_deskew', True):
        processed = deskew_image(processed)
    
    # Obtener configuración óptima de Tesseract
    config = get_optimal_tesseract_config(doc_type)
    
    # Extraer texto
    text = pytesseract.image_to_string(processed, lang='spa', config=config)
    
    return text

def extract_text_from_pdf(pdf_path: str, detect_type: bool = True, use_cache: bool = True) -> Tuple[str, str]:
    """
    Extrae texto de un PDF usando OCR optimizado
    
    Args:
        pdf_path: Ruta al archivo PDF
        detect_type: Si se debe detectar automáticamente el tipo de documento
        use_cache: Si se debe usar caché para evitar reprocesamiento
        
    Returns:
        Tuple[str, str]: Texto extraído y tipo de documento detectado
    """
    # Verificar si el resultado está en caché
    if use_cache and pdf_path in OCR_CACHE:
        logger.info(f"Usando resultado en caché para {pdf_path}")
        return OCR_CACHE[pdf_path]
    
    # Convertir PDF a imágenes
    start_time = time.time()
    images = convert_from_path(pdf_path, dpi=300)
    
    # Detectar tipo de documento
    doc_type = 'general'
    if detect_type and images:
        doc_type = detect_document_type(images[0])
    
    # Extraer texto de cada página
    text = ""
    for i, img in enumerate(images):
        logger.info(f"Procesando página {i+1}/{len(images)}")
        text += extract_text_from_image(img, doc_type) + "\n\n"
    
    # Guardar en caché
    if use_cache:
        OCR_CACHE[pdf_path] = (text, doc_type)
    
    processing_time = time.time() - start_time
    logger.info(f"Tiempo de procesamiento: {processing_time:.2f} segundos")
    
    return text, doc_type

def clear_cache():
    """Limpia la caché de OCR"""
    global OCR_CACHE
    OCR_CACHE = {}
    logger.info("Caché de OCR limpiada")

def count_words(text: str) -> int:
    """Cuenta el número de palabras en un texto"""
    return len(re.findall(r'\w+', text))

def count_numbers(text: str) -> int:
    """Cuenta el número de números en un texto"""
    return len(re.findall(r'\d+', text))

def count_product_codes(text: str) -> int:
    """Cuenta el número de posibles códigos de producto en un texto"""
    # Patrones comunes de códigos de producto (alfanuméricos de 5-15 caracteres)
    patterns = [
        r'[A-Z0-9]{5,15}',  # Códigos alfanuméricos
        r'\d{4,6}-\d{2,4}',  # Códigos con guiones
        r'[A-Z]{2,3}\d{3,7}'  # Letras seguidas de números
    ]
    
    codes = set()
    for pattern in patterns:
        matches = re.findall(pattern, text)
        codes.update(matches)
    
    return len(codes)

def validate_cif_nif(text: str) -> List[str]:
    """
    Valida y extrae posibles CIF/NIF del texto
    
    Args:
        text: Texto a analizar
        
    Returns:
        List[str]: Lista de posibles CIF/NIF válidos
    """
    # Patrones para CIF/NIF españoles
    patterns = [
        r'[ABCDEFGHJKLMNPQRSUVW]\d{7}[0-9A-J]',  # CIF
        r'[0-9]{8}[TRWAGMYFPDXBNJZSQVHLCKE]',     # NIF
        r'[XYZ][0-9]{7}[TRWAGMYFPDXBNJZSQVHLCKE]' # NIE
    ]
    
    valid_ids = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        valid_ids.extend(matches)
    
    return valid_ids

def validate_nevir_product_codes(text: str) -> List[str]:
    """
    Valida y extrae códigos de producto NEVIR
    
    Args:
        text: Texto a analizar
        
    Returns:
        List[str]: Lista de códigos de producto NEVIR válidos
    """
    # Patrón específico para códigos NEVIR
    pattern = r'NVR-\d{4,5}'
    
    matches = re.findall(pattern, text)
    return matches

def extract_tax_info(text: str) -> Dict[str, float]:
    """
    Extrae información de impuestos (IVA y recargo de equivalencia)
    
    Args:
        text: Texto a analizar
        
    Returns:
        Dict[str, float]: Diccionario con tasas de impuestos
    """
    tax_info = {
        'iva': [],
        'recargo': []
    }
    
    # Patrones para IVA
    iva_patterns = [
        r'IVA\s*(\d+(?:[.,]\d+)?)%',
        r'(\d+(?:[.,]\d+)?)%\s*IVA',
        r'I\.V\.A\.\s*(\d+(?:[.,]\d+)?)%'
    ]
    
    # Patrones para recargo de equivalencia
    recargo_patterns = [
        r'R\.?E\.?\s*(\d+(?:[.,]\d+)?)%',
        r'RECARGO\s*(\d+(?:[.,]\d+)?)%',
        r'RECARGO DE EQUIVALENCIA\s*(\d+(?:[.,]\d+)?)%'
    ]
    
    # Extraer IVA
    for pattern in iva_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                rate = float(match.replace(',', '.'))
                if 0 <= rate <= 30:  # Validación básica
                    tax_info['iva'].append(rate)
            except ValueError:
                pass
    
    # Extraer recargo
    for pattern in recargo_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                rate = float(match.replace(',', '.'))
                if 0 <= rate <= 10:  # Validación básica
                    tax_info['recargo'].append(rate)
            except ValueError:
                pass
    
    return tax_info

def normalize_dates(text: str) -> Dict[str, str]:
    """
    Normaliza fechas encontradas en el texto
    
    Args:
        text: Texto a analizar
        
    Returns:
        Dict[str, str]: Diccionario con fechas normalizadas
    """
    dates = {
        'invoice_date': None,
        'due_date': None
    }
    
    # Patrones para fechas (DD/MM/YYYY, DD-MM-YYYY, etc.)
    date_patterns = [
        r'(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{2,4})',  # DD/MM/YYYY o DD-MM-YYYY
        r'(\d{2,4})[/\-\.](\d{1,2})[/\-\.](\d{1,2})'   # YYYY/MM/DD o YYYY-MM-DD
    ]
    
    # Buscar fechas en el texto
    all_dates = []
    for pattern in date_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            try:
                if len(match[2]) == 4:  # DD/MM/YYYY
                    day, month, year = int(match[0]), int(match[1]), int(match[2])
                elif len(match[0]) == 4:  # YYYY/MM/DD
                    year, month, day = int(match[0]), int(match[1]), int(match[2])
                else:  # DD/MM/YY
                    day, month, year = int(match[0]), int(match[1]), int(match[2])
                    if year < 100:
                        year += 2000 if year < 50 else 1900
                
                # Validación básica
                if 1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= 2100:
                    all_dates.append(f"{day:02d}/{month:02d}/{year}")
            except ValueError:
                pass
    
    # Asignar fechas (la primera como fecha de factura, la segunda como fecha de vencimiento)
    if all_dates:
        dates['invoice_date'] = all_dates[0]
        if len(all_dates) > 1:
            dates['due_date'] = all_dates[1]
    
    return dates

def extract_product_lines_abrila(text: str) -> List[Dict[str, Any]]:
    """
    Extrae líneas de productos de facturas ABRILA
    
    Args:
        text: Texto OCR
        
    Returns:
        List[Dict[str, Any]]: Lista de líneas de productos
    """
    import re
    import logging
    
    logger = logging.getLogger(__name__)
    lines = []
    
    # Dividir el texto en líneas para facilitar el procesamiento
    text_lines = text.split('\n')
    
    # Buscar la sección de productos (generalmente después de una cabecera)
    product_section_start = False
    product_section_text = ""
    
    for line in text_lines:
        if re.search(r'(Código|Referencia|Descripción|Cantidad|Precio|Dto\.?|Importe)', line, re.IGNORECASE):
            product_section_start = True
            continue
        
        if product_section_start:
            product_section_text += line + "\n"
    
    # Si no se encontró una sección específica, usar todo el texto
    if not product_section_text:
        product_section_text = text
    
    # Patrón 1: código, descripción, cantidad, precio, descuento, importe
    pattern1 = r'([0-9]{6,9})\s+([^\n]+?)\s+(\d+)\s+(\d+[.,]\d+)\s*€?\s+(\d+%)\s+(\d+[.,]\d+)\s*€?'
    
    # Patrón 2: código, descripción, cantidad, precio, importe (sin descuento)
    pattern2 = r'([0-9]{6,9})\s+([^\n]+?)\s+(\d+)\s+(\d+[.,]\d+)\s*€?\s+(\d+[.,]\d+)\s*€?'
    
    # Patrón 3: código al inicio de línea seguido de descripción y números
    pattern3 = r'^\s*([0-9]{6,9})\s+([^\n]+?)\s+(\d+)\s+(\d+[.,]\d+)'
    
    # Probar con el patrón 1 (completo)
    matches = re.finditer(pattern1, product_section_text)
    for match in matches:
        try:
            product_code = match.group(1).strip()
            description = match.group(2).strip()
            quantity = int(match.group(3).strip())
            price_unit = float(match.group(4).replace(',', '.').strip())
            discount = int(match.group(5).replace('%', '').strip())
            price_subtotal = float(match.group(6).replace(',', '.').strip())
            
            lines.append({
                'product_code': product_code,
                'name': description,
                'quantity': quantity,
                'price_unit': price_unit,
                'discount': discount,
                'price_subtotal': price_subtotal
            })
        except Exception as e:
            logger.error(f"Error parsing product line (pattern1): {match.group(0)}, Error: {str(e)}")
    
    # Si no se encontraron líneas con el patrón 1, intentar con el patrón 2
    if not lines:
        matches = re.finditer(pattern2, product_section_text)
        for match in matches:
            try:
                product_code = match.group(1).strip()
                description = match.group(2).strip()
                quantity = int(match.group(3).strip())
                price_unit = float(match.group(4).replace(',', '.').strip())
                price_subtotal = float(match.group(5).replace(',', '.').strip())
                
                # Calcular descuento si es posible
                discount = 0
                if quantity > 0 and price_unit > 0:
                    expected_subtotal = quantity * price_unit
                    if expected_subtotal > price_subtotal:
                        discount_amount = expected_subtotal - price_subtotal
                        discount = round((discount_amount / expected_subtotal) * 100)
                
                lines.append({
                    'product_code': product_code,
                    'name': description,
                    'quantity': quantity,
                    'price_unit': price_unit,
                    'discount': discount,
                    'price_subtotal': price_subtotal
                })
            except Exception as e:
                logger.error(f"Error parsing product line (pattern2): {match.group(0)}, Error: {str(e)}")
    
    # Si aún no se encontraron líneas, intentar con el patrón 3 (más simple)
    if not lines:
        # Procesar línea por línea para extraer información parcial
        for line in text_lines:
            match = re.search(pattern3, line)
            if match:
                try:
                    product_code = match.group(1).strip()
                    description = match.group(2).strip()
                    quantity = int(match.group(3).strip())
                    price_unit = float(match.group(4).replace(',', '.').strip())
                    
                    # Buscar el subtotal en la misma línea
                    subtotal_match = re.search(r'(\d+[.,]\d+)\s*€?\s*$', line)
                    price_subtotal = float(subtotal_match.group(1).replace(',', '.').strip()) if subtotal_match else quantity * price_unit
                    
                    lines.append({
                        'product_code': product_code,
                        'name': description,
                        'quantity': quantity,
                        'price_unit': price_unit,
                        'discount': 0,  # No podemos determinar el descuento con este patrón
                        'price_subtotal': price_subtotal
                    })
                except Exception as e:
                    logger.error(f"Error parsing product line (pattern3): {line}, Error: {str(e)}")
    
    # Validación final de las líneas extraídas
    validated_lines = []
    for line in lines:
        # Verificar que los valores numéricos sean razonables
        if line['quantity'] > 0 and line['price_unit'] > 0 and line['price_subtotal'] > 0:
            # Verificar que el código de producto tenga un formato válido
            if re.match(r'^[0-9]{6,9}$', line['product_code']):
                validated_lines.append(line)
    
    return validated_lines

def extract_abrila_totals(text: str) -> Dict[str, float]:
    """
    Extrae los totales de una factura ABRILA
    
    Args:
        text: Texto OCR
        
    Returns:
        Dict[str, float]: Diccionario con los totales
    """
    import re
    import logging
    
    logger = logging.getLogger(__name__)
    totals = {
        'base_imponible': None,
        'iva_amount': None,
        'total_amount': None,
        'discount_amount': None
    }
    
    # Extraer base imponible - múltiples patrones
    base_patterns = [
        r'(?:Base Imp[.\s]*|Importe Neto[:\s]*)(\d+[.,]\d+)',
        r'(?:Base Imponible)[^\n]*?(\d+[.,]\d+)',
        r'(?:Importe Neto)[^\n]*?(\d+[.,]\d+)'
    ]
    
    for pattern in base_patterns:
        base_match = re.search(pattern, text, re.IGNORECASE)
        if base_match:
            try:
                value = base_match.group(1).replace(',', '.')
                # Verificar si el valor parece razonable (mayor que 10)
                if float(value) > 10:
                    totals['base_imponible'] = float(value)
                    break
            except Exception as e:
                logger.error(f"Error parsing base imponible: {base_match.group(1)}, Error: {str(e)}")
    
    # Si no se encontró la base imponible, intentar calcularla a partir de las líneas
    if not totals['base_imponible']:
        try:
            lines = extract_product_lines_abrila(text)
            if lines:
                totals['base_imponible'] = sum(line['price_subtotal'] for line in lines)
                logger.info(f"Base imponible calculada a partir de líneas: {totals['base_imponible']}")
        except Exception as e:
            logger.error(f"Error calculando base imponible desde líneas: {str(e)}")
    
    # Extraer IVA - múltiples patrones
    iva_patterns = [
        r'(?:IVA[\s:]*|I\.V\.A\.)[^\n]*?(\d+[.,]\d+)',
        r'(?:\d+%)[^\n]*?(\d+[.,]\d+)',
        r'(?:21,00%)[^\n]*?(\d+[.,]\d+)'
    ]
    
    for pattern in iva_patterns:
        iva_match = re.search(pattern, text, re.IGNORECASE)
        if iva_match:
            try:
                value = iva_match.group(1).replace(',', '.')
                # Verificar si el valor parece razonable
                if float(value) > 1:
                    totals['iva_amount'] = float(value)
                    break
            except Exception as e:
                logger.error(f"Error parsing IVA amount: {iva_match.group(1)}, Error: {str(e)}")
    
    # Si tenemos base imponible pero no IVA, calcularlo (21% estándar)
    if totals['base_imponible'] and not totals['iva_amount']:
        totals['iva_amount'] = round(totals['base_imponible'] * 0.21, 2)
    
    # Extraer total factura - múltiples patrones
    total_patterns = [
        r'(?:Total Factura|Importe Total|TOTAL)[:\s]*(\d+[.,]\d+)',
        r'(?:TOTAL A PAGAR)[:\s]*(\d+[.,]\d+)',
        r'(?:TOTAL)[^\n]*?(\d+[.,]\d+)\s*€',
        r'(?:Importe Total)[^\n]*?(\d+[.,]\d+)'
    ]
    
    for pattern in total_patterns:
        total_match = re.search(pattern, text, re.IGNORECASE)
        if total_match:
            try:
                value = total_match.group(1).replace(',', '.')
                # Verificar si el valor parece razonable (mayor que 10)
                if float(value) > 10:
                    totals['total_amount'] = float(value)
                    break
            except Exception as e:
                logger.error(f"Error parsing total amount: {total_match.group(1)}, Error: {str(e)}")
    
    # Si tenemos base imponible e IVA pero no total, calcularlo
    if totals['base_imponible'] and totals['iva_amount'] and not totals['total_amount']:
        totals['total_amount'] = round(totals['base_imponible'] + totals['iva_amount'], 2)
    
    # Extraer descuentos
    discount_match = re.search(r'(?:Descuento|Dto\.)[:\s]*(\d+[.,]\d+)', text, re.IGNORECASE)
    if discount_match:
        try:
            totals['discount_amount'] = float(discount_match.group(1).replace(',', '.'))
        except Exception as e:
            logger.error(f"Error parsing discount amount: {discount_match.group(1)}, Error: {str(e)}")
    
    return totals

def extract_structured_data(text: str, doc_type: str = 'general') -> Dict[str, Any]:
    """
    Extrae datos estructurados del texto OCR
    
    Args:
        text: Texto OCR
        doc_type: Tipo de documento
        
    Returns:
        Dict[str, Any]: Datos estructurados extraídos
    """
    data = {
        'invoice_number': None,
        'invoice_date': None,
        'due_date': None,
        'supplier_name': None,
        'supplier_vat': None,
        'customer_name': None,
        'customer_vat': None,
        'total_amount': None,
        'base_imponible': None,
        'iva_amount': None,
        'discount_amount': None,
        'tax_info': None,
        'product_codes': None,
        'lines': []
    }
    
    # Extraer CIF/NIF
    vat_numbers = validate_cif_nif(text)
    if vat_numbers:
        data['supplier_vat'] = vat_numbers[0]
        if len(vat_numbers) > 1:
            data['customer_vat'] = vat_numbers[1]
    
    # Extraer fechas
    dates = normalize_dates(text)
    data['invoice_date'] = dates.get('invoice_date')
    data['due_date'] = dates.get('due_date')
    
    # Extraer información de impuestos
    data['tax_info'] = extract_tax_info(text)
    
    # Extraer número de factura
    invoice_patterns = [
        r'(?:N[º°]?\s*Factura[:\s]*|Factura[:\s]*N[º°]?\s*)(\w+)',
        r'(?:Factura|Fra\.)[:\s]*(\w+)',
        r'(?:Nº)[:\s]*(\w+)'
    ]
    
    for pattern in invoice_patterns:
        invoice_match = re.search(pattern, text, re.IGNORECASE)
        if invoice_match:
            data['invoice_number'] = invoice_match.group(1).strip()
            break
    
    # Procesamiento específico según el tipo de documento
    if doc_type == 'nevir':
        data['product_codes'] = validate_nevir_product_codes(text)
        data['supplier_name'] = 'NEVIR, S.A.'
        
    elif doc_type == 'abrila':
        # Extraer líneas de productos
        data['lines'] = extract_product_lines_abrila(text)
        
        # Extraer totales específicos de ABRILA
        totals = extract_abrila_totals(text)
        data['total_amount'] = totals.get('total_amount')
        data['base_imponible'] = totals.get('base_imponible')
        data['iva_amount'] = totals.get('iva_amount')
        data['discount_amount'] = totals.get('discount_amount')
        
        # Establecer nombre del proveedor
        data['supplier_name'] = 'FABRILAMP ILUMINACIÓN S.L.'
        
        # Extraer CIF específico de ABRILA si no se encontró antes
        if not data['supplier_vat']:
            abrila_vat_match = re.search(r'[Bb]\s*-?\s*\d{8}', text)
            if abrila_vat_match:
                data['supplier_vat'] = abrila_vat_match.group(0).replace(' ', '').upper()
    
    # Extraer número de factura específico para ABRILA
    if doc_type == 'abrila':
        invoice_number_patterns = [
            r'(?:N[º°]?\s*Factura[:\s]*|Factura[:\s]*N[º°]?\s*)(\w+[-/]?\w+)',
            r'(?:Factura|Fra\.)[:\s]*(\w+[-/]?\w+)',
            r'(?:N[º°])[:\s]*(\w+[-/]?\w+)',
            r'(?:Factura)\s+(\d+)',
            r'(?:Nº\s*Factura:)\s*(\d+)'
        ]
        
        for pattern in invoice_number_patterns:
            invoice_match = re.search(pattern, text, re.IGNORECASE)
            if invoice_match:
                data['invoice_number'] = invoice_match.group(1).strip()
                break
    
    # Para facturas ABRILA, establecer siempre el cliente correcto
    if doc_type == 'abrila':
        # Establecer el cliente por defecto para ABRILA
        data['customer_name'] = 'ANTONIO PLAZA BONACHERA'
        data['customer_vat'] = '75236270G'  # CIF correcto de ANTONIO PLAZA BONACHERA
        
        # Intentar extraer el cliente del texto solo para verificación
        customer_patterns = [
            r'(?:Cliente|Señores)[:\s]*([^\n]+)',
            r'(?:ANTONIO PLAZA BONACHERA)',
            r'(?:PLAZA BONACHERA)'
        ]
        
        for pattern in customer_patterns:
            customer_match = re.search(pattern, text, re.IGNORECASE)
            if customer_match:
                # Solo para logging, mantenemos el valor por defecto
                logger.info(f"Cliente encontrado en texto: {customer_match.group(0) if 'group' in dir(customer_match) else 'ANTONIO PLAZA BONACHERA'}")
                break
    
    # Validar y completar datos
    if data['lines'] and not data['total_amount']:
        # Calcular total a partir de las líneas si no se encontró
        try:
            data['total_amount'] = sum(line['price_subtotal'] for line in data['lines'])
        except Exception:
            pass
    
    return data

if __name__ == "__main__":
    # Ejemplo de uso
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python ocr_optimizado.py <ruta_archivo_pdf>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    if not os.path.exists(pdf_path):
        print(f"Error: El archivo {pdf_path} no existe")
        sys.exit(1)
    
    text, doc_type = extract_text_from_pdf(pdf_path)
    
    print(f"Tipo de documento detectado: {doc_type}")
    print(f"Texto extraído ({len(text)} caracteres):")
    print("-" * 50)
    print(text[:500] + "..." if len(text) > 500 else text)
    print("-" * 50)
    
    # Extraer datos estructurados
    data = extract_structured_data(text, doc_type)
    print("\nDatos estructurados extraídos:")
    for key, value in data.items():
        print(f"{key}: {value}")