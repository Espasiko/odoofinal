#!/usr/bin/env python3
"""
Script para comparar diferentes métodos de OCR (Original, Mejorado y OCR XChange)
Ejecutar: python3 test_ocr_comparison.py <ruta_archivo_pdf_o_imagen>
"""
import os
import sys
import json
import base64
import requests
import time
import re
import logging
import cv2
import numpy as np
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
from difflib import SequenceMatcher
from typing import Dict, Any, List, Tuple

# Configuración
API_URL = "http://localhost:8000/api/v1/debug-ocr/raw-extraction"

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Directorio para guardar resultados
RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resultados_ocr")
os.makedirs(RESULTS_DIR, exist_ok=True)

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
        'clahe_grid_size': (8, 8)
    },
    'abrila': {
        'blur_kernel': (3, 3),
        'threshold_block_size': 11,
        'threshold_c': 2,
        'morph_kernel_size': 1,
        'clahe_clip_limit': 2.5,
        'clahe_grid_size': (8, 8)
    },
    'bsh': {
        'blur_kernel': (5, 5),
        'threshold_block_size': 11,
        'threshold_c': 2,
        'morph_kernel_size': 1,
        'clahe_clip_limit': 3.0,
        'clahe_grid_size': (4, 4)
    },
    'general': {
        'blur_kernel': (3, 3),
        'threshold_block_size': 11,
        'threshold_c': 2,
        'morph_kernel_size': 1,
        'clahe_clip_limit': 2.0,
        'clahe_grid_size': (8, 8)
    }
}

def detect_document_type(image):
    """Detecta el tipo de documento basado en el texto extraído"""
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

def get_optimal_tesseract_config(doc_type):
    """Obtiene la configuración óptima de Tesseract para el tipo de documento"""
    return TESSERACT_CONFIGS.get(doc_type, TESSERACT_CONFIGS['general'])

def preprocess_image_original(image):
    """Preprocesamiento básico de imagen para OCR (método original)"""
    # Convertir a escala de grises si es necesario
    if isinstance(image, np.ndarray):
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
    else:  # PIL Image
        gray = np.array(image.convert('L'))
    
    # Aplicar umbralización simple
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary

def preprocess_image(image, doc_type='general'):
    """Preprocesamiento avanzado de imagen para OCR con parámetros específicos por tipo de documento"""
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
    
    # Aplicar ecualización de histograma adaptativa (CLAHE)
    clahe = cv2.createCLAHE(
        clipLimit=params['clahe_clip_limit'],
        tileGridSize=params['clahe_grid_size']
    )
    equalized = clahe.apply(blurred)
    
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

def deskew_image(image):
    """Corrige la inclinación de la imagen"""
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

def extract_text_original(image):
    """Extrae texto usando OCR básico"""
    processed = preprocess_image_original(image)
    text = pytesseract.image_to_string(processed, lang='spa')
    return text

def extract_text_improved(image, doc_type='general'):
    """Extrae texto usando OCR mejorado con configuración específica"""
    processed = preprocess_image(image, doc_type)
    deskewed = deskew_image(processed)
    config = get_optimal_tesseract_config(doc_type)
    text = pytesseract.image_to_string(deskewed, lang='spa', config=config)
    return text

def extract_text_from_pdf(pdf_path, method='original', detect_type=True):
    """Extrae texto de un PDF usando el método especificado"""
    images = convert_from_path(pdf_path, dpi=300)
    doc_type = 'general'
    if detect_type and images and method == 'improved':
        doc_type = detect_document_type(images[0])
        logger.info(f"Tipo de documento detectado: {doc_type}")
    
    text = ""
    for i, img in enumerate(images):
        logger.info(f"Procesando página {i+1}/{len(images)}")
        if method == 'original':
            text += extract_text_original(img) + "\n\n"
        elif method == 'improved':
            text += extract_text_improved(img, doc_type) + "\n\n"
    
    return text, doc_type

def count_words(text):
    """Cuenta el número de palabras en un texto"""
    return len(re.findall(r'\w+', text))

def count_numbers(text):
    """Cuenta el número de números en un texto"""
    return len(re.findall(r'\d+', text))

def count_product_codes(text):
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

def calculate_similarity(text1, text2):
    """Calcula la similitud entre dos textos"""
    return SequenceMatcher(None, text1, text2).ratio()

def truncate_value(value, max_length):
    """Trunca un valor a una longitud máxima"""
    if isinstance(value, (int, float)):
        value = str(value)
    if not isinstance(value, str):
        return str(value)
    if len(value) > max_length:
        return value[:max_length - 3] + "..."
    return value

def compare_extraction_methods(ocr_data, tabula_data, tables):
    """Compara los datos extraídos por OCR y Tabula"""
    print("\n=== COMPARACIÓN DE MÉTODOS DE EXTRACCIÓN ===\n")
    
    # Campos a comparar
    fields = [
        "invoice_number", "invoice_date", "due_date", "supplier_name", "supplier_vat",
        "supplier_address", "supplier_city", "supplier_zip", "customer_name", "customer_vat",
        "customer_address", "customer_city", "customer_zip", "total_amount", "tax_amount",
        "subtotal", "tax_rate", "recargo_equivalencia", "recargo_rate", "payment_method",
        "payment_terms", "currency"
    ]
    
    # Mostrar comparación en formato de tabla
    print(f"{'Campo':<20} | {'OCR':<30} | {'Tabula':<30} | {'Coincide':<10}")
    print("-" * 95)
    
    for field in fields:
        ocr_value = ocr_data.get(field, "")
        tabula_value = tabula_data.get("extracted_data", {}).get(field, "")
        
        # Truncar valores largos
        ocr_value = truncate_value(ocr_value, 30)
        tabula_value = truncate_value(tabula_value, 30)
        
        match = "✓" if str(ocr_value).strip() == str(tabula_value).strip() and str(ocr_value).strip() != "" else "✗"
        print(f"{field:<20} | {ocr_value:<30} | {tabula_value:<30} | {match:<10}")
    
    # Comparar líneas de productos
    print("\n=== LÍNEAS DE PRODUCTOS ===\n")
    ocr_lines = ocr_data.get("invoice_lines", [])
    tabula_lines = tabula_data.get("extracted_data", {}).get("invoice_lines", [])
    
    print(f"OCR detectó {len(ocr_lines)} líneas de productos")
    if ocr_lines:
        print("\nLíneas detectadas por OCR:")
        for i, line in enumerate(ocr_lines):
            quantity = line.get("quantity", "")
            unit_price = line.get("unit_price", "")
            total = line.get("price_subtotal", "")
            description = truncate_value(line.get("name", ""), 40)
            print(f"  {i+1}. Cant: {quantity}, Precio: {unit_price}, Total: {total}, Desc: {description}")
    
    print(f"\nTabula detectó {len(tabula_lines)} líneas de productos")
    if tabula_lines:
        print("\nLíneas detectadas por Tabula:")
        for i, line in enumerate(tabula_lines):
            quantity = line.get("quantity", "")
            unit_price = line.get("unit_price", "")
            total = line.get("total", "")
            description = truncate_value(line.get("description", ""), 40)
            print(f"  {i+1}. Cant: {quantity}, Precio: {unit_price}, Total: {total}, Desc: {description}")
    
    # Mostrar tablas extraídas por Tabula
    print("\n=== TABLAS EXTRAÍDAS POR TABULA ===\n")
    if tables and len(tables) > 0:
        for i, table in enumerate(tables):
            print(f"Tabla {i+1}:")
            try:
                # Mostrar las claves del diccionario
                keys = list(table.keys())
                print(f"  Columnas: {', '.join(keys)}")
                
                # Mostrar algunas filas de ejemplo
                if keys:
                    num_rows = min(len(table[keys[0]]), 3) if len(table[keys[0]]) > 0 else 0
                    for row_idx in range(num_rows):
                        row_data = []
                        for key in keys:
                            if row_idx < len(table[key]):
                                value = truncate_value(table[key][row_idx], 20)
                                row_data.append(f"{key}: {value}")
                        if row_data:
                            print(f"  Fila {row_idx+1}: {', '.join(row_data)}")
            except Exception as e:
                print(f"  Error al mostrar tabla: {e}")
            print()
    else:
        print("No se encontraron tablas en el documento")

def main():
    """Función principal"""
    if len(sys.argv) != 2:
        print("Uso: python test_ocr_comparison.py <ruta_al_pdf>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    if not os.path.exists(pdf_path):
        print(f"Error: El archivo {pdf_path} no existe")
        sys.exit(1)
    
    print(f"Procesando archivo: {pdf_path}")
    print(f"Tamaño del archivo: {os.path.getsize(pdf_path) / 1024:.2f} KB")
    
    # Leer el archivo PDF y convertirlo a base64
    with open(pdf_path, "rb") as f:
        pdf_base64 = base64.b64encode(f.read()).decode("utf-8")
    
    # Preparar la solicitud
    filename = os.path.basename(pdf_path)
    payload = {
        "file_base64": pdf_base64,
        "filename": filename
    }
    
    # Enviar la solicitud al endpoint
    try:
        print("\n=== ENVIANDO SOLICITUD AL ENDPOINT DE EXTRACCIÓN ===\n")
        response = requests.post(
            API_URL,
            json=payload
        )
        
        if response.status_code != 200:
            print(f"Error en la solicitud: {response.status_code} {response.reason}")
            print(f"Código de estado: {response.status_code}")
            print(f"Respuesta: {response.text}")
            sys.exit(1)
        
        # Guardar la respuesta en un archivo JSON
        output_filename = os.path.splitext(filename)[0] + "_raw_extraction.json"
        with open(output_filename, "w") as f:
            json.dump(response.json(), f, indent=2)
        
        print(f"Respuesta guardada en {output_filename}")
        
        # Extraer datos para comparación
        data = response.json()
        ocr_data = data.get("ocr_data", {})
        tabula_data = data.get("tabula_data", {})
        tables = data.get("tables", [])
        
        # Comparar métodos de extracción
        compare_extraction_methods(ocr_data, tabula_data, tables)
        
        # Mostrar recomendaciones basadas en el análisis
        print("\n=== RECOMENDACIONES ===\n")
        if not tables or len(tables) == 0:
            print("📋 No se detectaron tablas con Tabula en el endpoint. Posibles razones:")
            print("  - El PDF podría ser una imagen escaneada sin texto extraíble")
            print("  - Las tablas podrían no tener bordes o estructura clara")
            print("  - El formato podría no ser compatible con Tabula")
            print("\nSugerencias:")
            print("  1. Considerar usar solo OCR para este tipo de facturas")
            print("  2. Pre-procesar el PDF con OCR antes de usar Tabula")
            print("  3. Ajustar los parámetros de Tabula para este tipo específico de factura")
        else:
            print(f"📋 Se detectaron {len(tables)} tablas con Tabula a través del endpoint.")
            if not tabula_data.get("extracted_data", {}).get("invoice_lines", []):
                print("  ⚠️ Pero no se pudieron extraer líneas de productos.")
                print("  Considerar mejorar el algoritmo de detección de líneas de productos.")
        
    except requests.exceptions.RequestException as e:
        print(f"Error de conexión: {e}")
        sys.exit(1)
    except json.JSONDecodeError:
        print("Error al decodificar la respuesta JSON")
        sys.exit(1)
    except Exception as e:
        print(f"Error inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
