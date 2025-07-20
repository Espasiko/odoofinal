#!/usr/bin/env python3
"""
Script para comparar diferentes métodos de OCR (Original, Mejorado y OCR XChange)
Ejecutar: python3 test_ocr_comparison_completo.py <ruta_archivo_pdf_o_imagen> [--api] [--batch]
"""
import os
import sys
import json
import base64
import requests
import time
import re
import logging
import argparse
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

def compare_ocr_methods(pdf_path, use_api=False):
    """Compara diferentes métodos de OCR para un archivo PDF"""
    filename = os.path.basename(pdf_path)
    logger.info(f"Procesando archivo: {filename}")
    
    # Crear directorio para resultados de este archivo
    file_results_dir = os.path.join(RESULTS_DIR, os.path.splitext(filename)[0])
    os.makedirs(file_results_dir, exist_ok=True)
    
    results = {}
    doc_type = 'general'
    
    # Método 1: OCR Original
    start_time = time.time()
    logger.info("Aplicando método OCR original...")
    original_text, _ = extract_text_from_pdf(pdf_path, method='original', detect_type=False)
    original_time = time.time() - start_time
    
    # Guardar resultado del OCR original
    original_output_path = os.path.join(file_results_dir, "original_ocr.txt")
    with open(original_output_path, "w", encoding="utf-8") as f:
        f.write(original_text)
    
    # Método 2: OCR Mejorado
    start_time = time.time()
    logger.info("Aplicando método OCR mejorado...")
    improved_text, doc_type = extract_text_from_pdf(pdf_path, method='improved', detect_type=True)
    improved_time = time.time() - start_time
    
    # Guardar resultado del OCR mejorado
    improved_output_path = os.path.join(file_results_dir, "improved_ocr.txt")
    with open(improved_output_path, "w", encoding="utf-8") as f:
        f.write(improved_text)
    
    # Calcular estadísticas
    original_chars = len(original_text)
    original_words = count_words(original_text)
    original_numbers = count_numbers(original_text)
    original_codes = count_product_codes(original_text)
    
    improved_chars = len(improved_text)
    improved_words = count_words(improved_text)
    improved_numbers = count_numbers(improved_text)
    improved_codes = count_product_codes(improved_text)
    
    # Calcular similitud
    similarity = calculate_similarity(original_text, improved_text)
    
    # Calcular diferencias
    char_diff = improved_chars - original_chars
    char_diff_percent = (char_diff / original_chars * 100) if original_chars > 0 else 0
    time_diff_percent = ((improved_time - original_time) / original_time * 100) if original_time > 0 else 0
    
    # Guardar resultados
    results = {
        "filename": filename,
        "doc_type": doc_type,
        "original": {
            "time": original_time,
            "chars": original_chars,
            "words": original_words,
            "numbers": original_numbers,
            "product_codes": original_codes,
            "output_path": original_output_path
        },
        "improved": {
            "time": improved_time,
            "chars": improved_chars,
            "words": improved_words,
            "numbers": improved_numbers,
            "product_codes": improved_codes,
            "output_path": improved_output_path
        },
        "comparison": {
            "similarity": similarity,
            "char_diff": char_diff,
            "char_diff_percent": char_diff_percent,
            "time_diff_percent": time_diff_percent
        }
    }
    
    # Guardar resultados en JSON
    results_json_path = os.path.join(file_results_dir, "ocr_comparison_results.json")
    with open(results_json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    
    # Mostrar resultados
    logger.info("\n==================================================")
    logger.info(f"Resultados para {filename}")
    logger.info(f"Tipo de documento detectado: {doc_type}")
    logger.info("==================================================")
    logger.info("Método original:")
    logger.info(f"  - Tiempo: {original_time:.2f} segundos")
    logger.info(f"  - Caracteres: {original_chars}")
    logger.info(f"  - Palabras: {original_words}")
    logger.info(f"  - Números: {original_numbers}")
    logger.info(f"  - Códigos de producto: {original_codes}")
    logger.info("\nMétodo mejorado:")
    logger.info(f"  - Tiempo: {improved_time:.2f} segundos")
    logger.info(f"  - Caracteres: {improved_chars}")
    logger.info(f"  - Palabras: {improved_words}")
    logger.info(f"  - Números: {improved_numbers}")
    logger.info(f"  - Códigos de producto: {improved_codes}")
    logger.info("\nComparación:")
    logger.info(f"  - Similitud: {similarity:.2f}")
    logger.info(f"  - Diferencia de caracteres: {abs(char_diff)} ({abs(char_diff_percent):.2f}%)")
    logger.info(f"  - Mejora en caracteres: {char_diff_percent:.2f}%")
    logger.info(f"  - Diferencia en tiempo: {time_diff_percent:.2f}%")
    logger.info("==================================================")
    
    # Si se solicita usar la API, también comparar con los resultados del endpoint
    if use_api:
        try:
            # Leer el archivo PDF y convertirlo a base64
            with open(pdf_path, "rb") as f:
                pdf_base64 = base64.b64encode(f.read()).decode("utf-8")
            
            # Preparar la solicitud
            payload = {
                "file_base64": pdf_base64,
                "filename": filename
            }
            
            # Enviar la solicitud al endpoint
            logger.info("\n=== ENVIANDO SOLICITUD AL ENDPOINT DE EXTRACCIÓN ===\n")
            response = requests.post(
                API_URL,
                json=payload
            )
            
            if response.status_code != 200:
                logger.error(f"Error en la solicitud: {response.status_code} {response.reason}")
                logger.error(f"Respuesta: {response.text}")
                return results
            
            # Guardar la respuesta en un archivo JSON
            api_output_path = os.path.join(file_results_dir, "api_extraction.json")
            with open(api_output_path, "w") as f:
                json.dump(response.json(), f, indent=2)
            
            # Extraer datos para comparación
            data = response.json()
            ocr_data = data.get("ocr_data", {})
            tabula_data = data.get("tabula_data", {})
            tables = data.get("tables", [])
            
            # Comparar métodos de extracción
            compare_extraction_methods(ocr_data, tabula_data, tables)
            
            # Añadir resultados de la API a los resultados generales
            results["api"] = {
                "output_path": api_output_path,
                "ocr_data": ocr_data,
                "tabula_data": tabula_data,
                "tables_count": len(tables)
            }
            
            # Actualizar el archivo JSON con los nuevos resultados
            with open(results_json_path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error de conexión: {e}")
        except json.JSONDecodeError:
            logger.error("Error al decodificar la respuesta JSON")
        except Exception as e:
            logger.error(f"Error inesperado: {e}")
    
    return results

def main():
    """Función principal"""
    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(description='Comparar diferentes métodos de OCR para facturas')
    parser.add_argument('pdf_path', help='Ruta al archivo PDF a procesar')
    parser.add_argument('--api', action='store_true', help='Usar también la API para comparación')
    parser.add_argument('--batch', action='store_true', help='Procesar todos los PDFs en el directorio')
    args = parser.parse_args()
    
    if args.batch:
        # Modo batch: procesar todos los PDFs en el directorio
        directory = os.path.dirname(args.pdf_path) if os.path.isfile(args.pdf_path) else args.pdf_path
        pdf_files = [os.path.join(directory, f) for f in os.listdir(directory) 
                    if f.lower().endswith('.pdf') and os.path.isfile(os.path.join(directory, f))]
        
        if not pdf_files:
            logger.error(f"No se encontraron archivos PDF en {directory}")
            sys.exit(1)
        
        logger.info(f"Procesando {len(pdf_files)} archivos PDF en modo batch...")
        
        # Crear archivo de resultados consolidados
        all_results = []
        for pdf_file in pdf_files:
            try:
                result = compare_ocr_methods(pdf_file, use_api=args.api)
                all_results.append(result)
            except Exception as e:
                logger.error(f"Error procesando {pdf_file}: {e}")
        
        # Guardar resultados consolidados
        consolidated_results_path = os.path.join(RESULTS_DIR, "consolidated_results.json")
        with open(consolidated_results_path, "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2)
        
        logger.info(f"Resultados consolidados guardados en {consolidated_results_path}")
        
    else:
        # Modo individual: procesar un solo PDF
        if not os.path.exists(args.pdf_path):
            logger.error(f"Error: El archivo {args.pdf_path} no existe")
            sys.exit(1)
        
        compare_ocr_methods(args.pdf_path, use_api=args.api)

if __name__ == "__main__":
    main()