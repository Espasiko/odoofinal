#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de prueba para comparar diferentes configuraciones de OCR
con soporte para diferentes tipos de documentos (NEVIR, ABRILA, BSH)

Este script permite:
1. Comparar el OCR original vs mejorado
2. Probar diferentes configuraciones por tipo de documento
3. Medir tiempo de procesamiento y calidad de extracción
4. Guardar resultados para análisis posterior
"""

import os
import sys
import time
import re
import cv2
import numpy as np
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import logging
import argparse
from difflib import SequenceMatcher

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Directorio para guardar resultados
RESULTADOS_DIR = "/home/espasiko/mainmanusodoo/manusodoo-roto/resultados_ocr"
os.makedirs(RESULTADOS_DIR, exist_ok=True)

# Funciones de preprocesamiento

def preprocess_image_original(image):
    """
    Método de preprocesamiento original
    """
    # Convertir a array numpy si es necesario
    if not isinstance(image, np.ndarray):
        image = np.array(image)
    
    # Convertir a escala de grises
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    else:
        gray = image
    
    # Aplicar umbralización fija
    _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    
    # Eliminar ruido con operaciones morfológicas
    kernel = np.ones((1, 1), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    
    return binary

def preprocess_image_mejorado(image, doc_type='general'):
    """
    Método de preprocesamiento mejorado con soporte para diferentes tipos de documentos
    """
    # Convertir a array numpy si es necesario
    if not isinstance(image, np.ndarray):
        image = np.array(image)
    
    # Convertir a escala de grises
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    else:
        gray = image
    
    # Normalizar el histograma para mejorar el contraste
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    
    # Aplicar diferentes técnicas según el tipo de documento
    if doc_type.lower() in ['nevir', 'factura']:
        # Para facturas NEVIR: umbralización adaptativa más agresiva
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        binary = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 15, 8
        )
        
        # Operaciones morfológicas para limpiar el ruido
        kernel = np.ones((1, 1), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        
    elif doc_type.lower() in ['abrila', 'bsh']:
        # Para facturas con más detalles finos: umbralización más suave
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        binary = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Operaciones morfológicas para preservar detalles
        kernel = np.ones((1, 1), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        
    else:  # Caso general
        # Umbralización adaptativa estándar
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        binary = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Operaciones morfológicas para limpiar el ruido
        kernel = np.ones((1, 1), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    
    return binary

def deskew_image(image):
    """
    Corrige la inclinación de la imagen para mejorar el OCR
    """
    # Asegurarse de que la imagen es binaria
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    else:
        _, binary = cv2.threshold(image, 128, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    
    # Detectar bordes con parámetros optimizados
    edges = cv2.Canny(binary, 50, 200, apertureSize=3)
    
    # Detectar líneas con parámetros ajustados para mejor detección
    lines = cv2.HoughLinesP(
        edges, 
        rho=1, 
        theta=np.pi/180, 
        threshold=80,  # Umbral más bajo para detectar más líneas
        minLineLength=50,  # Líneas más cortas para documentos con texto
        maxLineGap=20  # Mayor tolerancia a huecos
    )
    
    if lines is not None and len(lines) > 0:
        angles = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if x2 - x1 != 0:  # Evitar división por cero
                # Calcular ángulo en grados
                angle = np.arctan((y2 - y1) / (x2 - x1)) * 180 / np.pi
                # Solo considerar ángulos horizontales (cercanos a 0°)
                if abs(angle) < 30:
                    angles.append(angle)
        
        if angles:
            # Usar la mediana para ser más robusto frente a valores atípicos
            median_angle = np.median(angles)
            
            # Solo corregir si el ángulo es significativo pero no demasiado grande
            if 0.5 < abs(median_angle) < 10:
                (h, w) = image.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                rotated = cv2.warpAffine(
                    image, 
                    M, 
                    (w, h), 
                    flags=cv2.INTER_CUBIC, 
                    borderMode=cv2.BORDER_REPLICATE
                )
                return rotated
    
    return image

def detect_document_type(image_or_text):
    """
    Detecta automáticamente el tipo de documento basado en el contenido
    """
    if isinstance(image_or_text, str):
        # Es texto
        text = image_or_text.upper()
    else:
        # Es imagen, convertir a texto
        text = pytesseract.image_to_string(image_or_text, lang='spa').upper()
    
    if 'NEVIR' in text:
        return 'nevir'
    elif 'ABRILA' in text or 'FABRILAMP' in text:
        return 'abrila'
    elif 'BOSCH' in text or 'BSH' in text or 'SIEMENS' in text or 'BALAY' in text:
        return 'bsh'
    else:
        return 'general'

def get_optimal_tesseract_config(doc_type='general'):
    """
    Devuelve la configuración óptima de Tesseract según el tipo de documento
    """
    # Configuración base para todos los documentos
    base_config = '--dpi 300'
    
    # Configuraciones específicas por tipo de documento
    if doc_type.lower() == 'nevir':
        # Para facturas NEVIR: enfocado en precisión de códigos de producto
        return f'{base_config} --oem 1 --psm 6 -c preserve_interword_spaces=1'
    
    elif doc_type.lower() == 'abrila':
        # Para facturas ABRILA: mejor para tablas y estructura
        return f'{base_config} --oem 1 --psm 6 -c textord_tabfind_find_tables=1'
    
    elif doc_type.lower() == 'bsh':
        # Para facturas BSH: mejor para texto denso y estructurado
        return f'{base_config} --oem 1 --psm 4 -c textord_min_linesize=2.5'
    
    else:  # Configuración general
        return f'{base_config} --oem 1 --psm 6'

# Funciones de extracción de texto

def extract_text_original(pdf_path):
    """
    Método original de extracción de texto
    """
    start_time = time.time()
    
    # Convertir PDF a imágenes
    images = convert_from_path(pdf_path)
    
    # Extraer texto
    text = ""
    for img in images:
        processed_img = preprocess_image_original(img)
        text += pytesseract.image_to_string(processed_img, lang='spa', config='--dpi 300 --psm 6')
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    return text, processing_time

def extract_text_mejorado(pdf_path, detect_type=True):
    """
    Método mejorado de extracción de texto con detección automática de tipo de documento
    """
    start_time = time.time()
    
    # Convertir PDF a imágenes con alta resolución
    images = convert_from_path(pdf_path, dpi=300)
    
    # Detectar tipo de documento en la primera página si está habilitado
    doc_type = 'general'
    if detect_type and images:
        doc_type = detect_document_type(images[0])
        logger.info(f"Tipo de documento detectado: {doc_type}")
    
    # Obtener configuración óptima de Tesseract
    tesseract_config = get_optimal_tesseract_config(doc_type)
    
    # Preprocesar imágenes y extraer texto
    text = ""
    for i, img in enumerate(images):
        logger.info(f"Procesando página {i+1}/{len(images)}")
        
        # Aplicar preprocesamiento específico para el tipo de documento
        processed_img = preprocess_image_mejorado(img, doc_type)
        
        # Aplicar corrección de inclinación
        deskewed_img = deskew_image(processed_img)
        
        # Extraer texto con configuración optimizada
        page_text = pytesseract.image_to_string(
            deskewed_img, 
            lang='spa', 
            config=tesseract_config
        )
        
        text += page_text + "\n\n"
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    return text, processing_time, doc_type

# Funciones de evaluación

def evaluate_text_quality(text):
    """
    Evalúa la calidad del texto extraído
    """
    # Contar caracteres no vacíos
    non_empty_chars = len([c for c in text if c.strip()])
    
    # Contar palabras
    words = re.findall(r'\b\w+\b', text)
    word_count = len(words)
    
    # Contar números que podrían ser códigos de producto o importes
    numbers = re.findall(r'\b\d+[.,]?\d*\b', text)
    number_count = len(numbers)
    
    # Contar posibles códigos de producto (alfanuméricos)
    product_codes = re.findall(r'\b[A-Z0-9]{5,}\b', text)
    product_code_count = len(product_codes)
    
    return {
        'char_count': non_empty_chars,
        'word_count': word_count,
        'number_count': number_count,
        'product_code_count': product_code_count,
        'sample': text[:200] + "..." if len(text) > 200 else text
    }

def compare_texts(text1, text2):
    """
    Compara dos textos y calcula su similitud
    """
    # Calcular similitud usando SequenceMatcher
    matcher = SequenceMatcher(None, text1, text2)
    similarity = matcher.ratio()
    
    # Contar caracteres diferentes
    chars1 = len([c for c in text1 if c.strip()])
    chars2 = len([c for c in text2 if c.strip()])
    char_diff = abs(chars1 - chars2)
    char_diff_percent = (char_diff / max(chars1, chars2)) * 100 if max(chars1, chars2) > 0 else 0
    
    return {
        'similarity': similarity,
        'char_diff': char_diff,
        'char_diff_percent': char_diff_percent
    }

# Función principal de prueba

def test_ocr_methods(pdf_path, force_doc_type=None):
    """
    Prueba y compara los métodos de OCR original y mejorado
    """
    filename = os.path.basename(pdf_path)
    logger.info(f"Procesando archivo: {filename}")
    
    # Extraer texto con método original
    logger.info("Aplicando método OCR original...")
    original_text, original_time = extract_text_original(pdf_path)
    
    # Guardar resultado original
    original_filename = os.path.splitext(filename)[0] + "_original.txt"
    with open(os.path.join(RESULTADOS_DIR, original_filename), "w") as f:
        f.write(original_text)
    
    # Extraer texto con método mejorado
    logger.info("Aplicando método OCR mejorado...")
    if force_doc_type:
        logger.info(f"Forzando tipo de documento: {force_doc_type}")
        # Convertir PDF a imágenes
        images = convert_from_path(pdf_path, dpi=300)
        # Obtener configuración óptima de Tesseract
        tesseract_config = get_optimal_tesseract_config(force_doc_type)
        
        start_time = time.time()
        text = ""
        for i, img in enumerate(images):
            processed_img = preprocess_image_mejorado(img, force_doc_type)
            deskewed_img = deskew_image(processed_img)
            page_text = pytesseract.image_to_string(
                deskewed_img, 
                lang='spa', 
                config=tesseract_config
            )
            text += page_text + "\n\n"
        end_time = time.time()
        
        mejorado_text = text
        mejorado_time = end_time - start_time
        detected_type = force_doc_type
    else:
        mejorado_text, mejorado_time, detected_type = extract_text_mejorado(pdf_path)
    
    # Guardar resultado mejorado
    mejorado_filename = os.path.splitext(filename)[0] + "_mejorado.txt"
    with open(os.path.join(RESULTADOS_DIR, mejorado_filename), "w") as f:
        f.write(mejorado_text)
    
    # Evaluar calidad de los textos
    original_quality = evaluate_text_quality(original_text)
    mejorado_quality = evaluate_text_quality(mejorado_text)
    
    # Comparar textos
    comparison = compare_texts(original_text, mejorado_text)
    
    # Calcular mejora porcentual en caracteres
    char_improvement = ((mejorado_quality['char_count'] - original_quality['char_count']) / 
                       original_quality['char_count'] * 100) if original_quality['char_count'] > 0 else 0
    
    # Calcular mejora porcentual en tiempo
    time_diff_percent = ((mejorado_time - original_time) / original_time * 100) if original_time > 0 else 0
    
    # Resultados
    results = {
        'filename': filename,
        'detected_type': detected_type,
        'original': {
            'time': original_time,
            'quality': original_quality
        },
        'mejorado': {
            'time': mejorado_time,
            'quality': mejorado_quality
        },
        'comparison': comparison,
        'char_improvement': char_improvement,
        'time_diff_percent': time_diff_percent
    }
    
    # Imprimir resultados
    logger.info("\n" + "=" * 50)
    logger.info(f"Resultados para {filename}")
    logger.info(f"Tipo de documento detectado: {detected_type}")
    logger.info("=" * 50)
    logger.info(f"Método original:")
    logger.info(f"  - Tiempo: {original_time:.2f} segundos")
    logger.info(f"  - Caracteres: {original_quality['char_count']}")
    logger.info(f"  - Palabras: {original_quality['word_count']}")
    logger.info(f"  - Números: {original_quality['number_count']}")
    logger.info(f"  - Códigos de producto: {original_quality['product_code_count']}")
    logger.info("\nMétodo mejorado:")
    logger.info(f"  - Tiempo: {mejorado_time:.2f} segundos")
    logger.info(f"  - Caracteres: {mejorado_quality['char_count']}")
    logger.info(f"  - Palabras: {mejorado_quality['word_count']}")
    logger.info(f"  - Números: {mejorado_quality['number_count']}")
    logger.info(f"  - Códigos de producto: {mejorado_quality['product_code_count']}")
    logger.info("\nComparación:")
    logger.info(f"  - Similitud: {comparison['similarity']:.2f}")
    logger.info(f"  - Diferencia de caracteres: {comparison['char_diff']} ({comparison['char_diff_percent']:.2f}%)")
    logger.info(f"  - Mejora en caracteres: {char_improvement:.2f}%")
    logger.info(f"  - Diferencia en tiempo: {time_diff_percent:.2f}%")
    logger.info("=" * 50)
    
    return results

# Función principal

def main():
    parser = argparse.ArgumentParser(description='Prueba de OCR mejorado con soporte para diferentes tipos de documentos')
    parser.add_argument('pdf_path', help='Ruta al archivo PDF a procesar')
    parser.add_argument('--type', choices=['nevir', 'abrila', 'bsh', 'general'], 
                        help='Forzar tipo de documento (opcional)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.pdf_path):
        logger.error(f"El archivo {args.pdf_path} no existe")
        return 1
    
    test_ocr_methods(args.pdf_path, args.type)
    return 0

if __name__ == "__main__":
    sys.exit(main())
