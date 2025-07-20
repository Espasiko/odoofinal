#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time
import logging
from pathlib import Path
import cv2
import numpy as np
import pytesseract
from pdf2image import convert_from_path

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ruta base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Función de preprocesamiento original
def preprocess_image_original(image):
    # Convertir a escala de grises
    gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
    
    # Aplicar umbral fijo
    _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    
    # Eliminar ruido
    kernel = np.ones((1, 1), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    
    return binary

# Función de preprocesamiento mejorada
def preprocess_image_mejorado(image):
    # Convertir a array numpy si es necesario
    if not isinstance(image, np.ndarray):
        image = np.array(image)
    
    # Convertir a escala de grises
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    else:
        gray = image
    
    # Aplicar desenfoque gaussiano para reducir ruido
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Aplicar umbralización adaptativa (mejor que umbral fijo)
    binary = cv2.adaptiveThreshold(
        blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 11, 2
    )
    
    # Eliminar ruido con operaciones morfológicas
    kernel = np.ones((1, 1), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    
    return binary

# Función para corregir inclinación
def deskew_image(image):
    """
    Corrige la inclinación de la imagen para mejorar el OCR
    """
    # Detectar bordes
    edges = cv2.Canny(image, 50, 150, apertureSize=3)
    
    # Detectar líneas
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=100, maxLineGap=10)
    
    if lines is not None and len(lines) > 0:
        angles = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if x2 - x1 != 0:  # Evitar división por cero
                angle = np.arctan((y2 - y1) / (x2 - x1)) * 180 / np.pi
                angles.append(angle)
        
        if angles:
            # Calcular ángulo promedio
            median_angle = np.median(angles)
            
            # Rotar imagen si el ángulo es significativo
            if abs(median_angle) > 0.5:
                (h, w) = image.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                rotated = cv2.warpAffine(image, M, (w, h), 
                                       flags=cv2.INTER_CUBIC, 
                                       borderMode=cv2.BORDER_REPLICATE)
                return rotated
    
    return image

# Función OCR original
def extract_text_original(pdf_path):
    """
    Extrae texto usando la configuración original de OCR
    """
    images = convert_from_path(pdf_path)
    
    text = ""
    for img in images:
        processed_img = preprocess_image_original(img)
        text += pytesseract.image_to_string(processed_img, lang='spa', config='--dpi 300 --psm 6')
    
    return text

# Función OCR mejorada
def extract_text_mejorado(pdf_path):
    """
    Extrae texto usando la configuración mejorada de OCR
    """
    images = convert_from_path(pdf_path, dpi=300)
    
    text = ""
    for img in images:
        processed_img = preprocess_image_mejorado(img)
        deskewed_img = deskew_image(processed_img)
        text += pytesseract.image_to_string(
            deskewed_img, 
            lang='spa', 
            config='--oem 1 --psm 6 --dpi 300'
        )
    
    return text

def test_ocr_comparison(pdf_path):
    """
    Compara los resultados de OCR entre el método original y el mejorado
    """
    logger.info(f"Procesando archivo: {pdf_path}")
    
    # Medir tiempo y extraer texto con método original
    start_time = time.time()
    text_original = extract_text_original(pdf_path)
    original_time = time.time() - start_time
    
    # Medir tiempo y extraer texto con método mejorado
    start_time = time.time()
    text_mejorado = extract_text_mejorado(pdf_path)
    mejorado_time = time.time() - start_time
    
    # Calcular longitud de texto extraído
    len_original = len(text_original)
    len_mejorado = len(text_mejorado)
    
    # Calcular diferencia porcentual
    if len_original > 0:
        diff_percent = ((len_mejorado - len_original) / len_original) * 100
    else:
        diff_percent = 0
    
    # Mostrar resultados
    logger.info(f"Resultados para {os.path.basename(pdf_path)}:")
    logger.info(f"  Método original: {len_original} caracteres en {original_time:.2f} segundos")
    logger.info(f"  Método mejorado: {len_mejorado} caracteres en {mejorado_time:.2f} segundos")
    logger.info(f"  Diferencia: {diff_percent:.2f}% más texto extraído")
    
    # Guardar resultados en archivos para comparación
    output_dir = os.path.join(BASE_DIR, "resultados_ocr")
    os.makedirs(output_dir, exist_ok=True)
    
    base_filename = os.path.splitext(os.path.basename(pdf_path))[0]
    
    with open(os.path.join(output_dir, f"{base_filename}_original.txt"), "w", encoding="utf-8") as f:
        f.write(text_original)
    
    with open(os.path.join(output_dir, f"{base_filename}_mejorado.txt"), "w", encoding="utf-8") as f:
        f.write(text_mejorado)
    
    logger.info(f"Resultados guardados en {output_dir}")
    
    return {
        "original_chars": len_original,
        "mejorado_chars": len_mejorado,
        "original_time": original_time,
        "mejorado_time": mejorado_time,
        "diff_percent": diff_percent
    }

def main():
    """
    Función principal para ejecutar pruebas de OCR
    """
    # Verificar argumentos
    if len(sys.argv) < 2:
        logger.info("Uso: python test_ocr_mejorado.py <ruta_pdf>")
        logger.info("Ejemplo: python test_ocr_mejorado.py ../ejemplos/NEVIR\\ -\\ FacturaF2402846.pdf")
        return
    
    pdf_path = sys.argv[1]
    
    if not os.path.exists(pdf_path):
        logger.error(f"El archivo {pdf_path} no existe")
        return
    
    # Ejecutar prueba
    results = test_ocr_comparison(pdf_path)
    
    # Mostrar resumen final
    logger.info("\nResumen de resultados:")
    logger.info(f"Caracteres extraídos (original): {results['original_chars']}")
    logger.info(f"Caracteres extraídos (mejorado): {results['mejorado_chars']}")
    logger.info(f"Tiempo de procesamiento (original): {results['original_time']:.2f} segundos")
    logger.info(f"Tiempo de procesamiento (mejorado): {results['mejorado_time']:.2f} segundos")
    logger.info(f"Diferencia en texto extraído: {results['diff_percent']:.2f}%")

if __name__ == "__main__":
    main()
