#!/usr/bin/env python3
"""
Script para comparar diferentes métodos de OCR y generar un informe detallado
"""
import os
import sys
import json
import time
import logging
import argparse
import pandas as pd
from pathlib import Path
from datetime import datetime
from difflib import SequenceMatcher

# Importar módulos de OCR
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api.ocr_optimizado import extract_text_from_pdf as extract_optimized_text
from api.ocr_optimizado import extract_structured_data, detect_document_type
from api.routes.ocr import extract_text_from_pdf as extract_original_text
from api.routes.ocr import extract_invoice_data as extract_original_data

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('comparacion_ocr.log')
    ]
)
logger = logging.getLogger(__name__)

def similar(a, b):
    """Calcula la similitud entre dos cadenas de texto"""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()

def count_numbers(text):
    """Cuenta la cantidad de números en un texto"""
    return sum(c.isdigit() for c in text)

def count_words(text):
    """Cuenta la cantidad de palabras en un texto"""
    if not text:
        return 0
    return len(text.split())

def extract_product_codes(text, doc_type):
    """Extrae códigos de producto según el tipo de documento"""
    import re
    
    if doc_type == 'nevir':
        # Patrón para códigos NEVIR (NVR-XXXXX)
        pattern = r'NVR-\d{5}'
        return re.findall(pattern, text)
    elif doc_type == 'abrila':
        # Patrón para códigos ABRILA
        pattern = r'\d{6,9}'
        return re.findall(pattern, text)
    else:
        # Patrón genérico para códigos de producto
        pattern = r'[A-Z0-9]{5,10}'
        return re.findall(pattern, text)

def compare_ocr_methods(pdf_path, output_dir=None):
    """
    Compara diferentes métodos de OCR para un archivo PDF
    
    Args:
        pdf_path: Ruta al archivo PDF
        output_dir: Directorio para guardar resultados
    
    Returns:
        Dict con resultados de la comparación
    """
    if not os.path.exists(pdf_path):
        logger.error(f"El archivo {pdf_path} no existe")
        return None
    
    # Crear directorio de salida
    if not output_dir:
        output_dir = Path("resultados_ocr") / Path(pdf_path).stem
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = {
        "pdf_path": str(pdf_path),
        "filename": os.path.basename(pdf_path),
        "timestamp": datetime.now().isoformat(),
        "methods": {}
    }
    
    # Método 1: OCR original
    logger.info(f"Procesando {pdf_path} con método original")
    start_time = time.time()
    try:
        original_text = extract_original_text(pdf_path, detect_type=True)
        original_time = time.time() - start_time
        
        # Guardar texto extraído
        with open(output_dir / "original_text.txt", "w", encoding="utf-8") as f:
            f.write(original_text)
        
        # Extraer datos estructurados
        original_data = extract_original_data(original_text, pdf_path)
        
        # Guardar datos estructurados
        with open(output_dir / "original_data.json", "w", encoding="utf-8") as f:
            json.dump(original_data, f, indent=2, ensure_ascii=False)
        
        # Métricas
        results["methods"]["original"] = {
            "time": original_time,
            "char_count": len(original_text),
            "word_count": count_words(original_text),
            "number_count": count_numbers(original_text),
            "extracted_data": original_data
        }
        
        logger.info(f"OCR original completado en {original_time:.2f} segundos")
    except Exception as e:
        logger.error(f"Error en OCR original: {e}")
        results["methods"]["original"] = {"error": str(e)}
    
    # Método 2: OCR optimizado
    logger.info(f"Procesando {pdf_path} con método optimizado")
    start_time = time.time()
    try:
        optimized_text, doc_type = extract_optimized_text(pdf_path, detect_type=True, use_cache=True)
        optimized_time = time.time() - start_time
        
        # Guardar texto extraído
        with open(output_dir / "optimized_text.txt", "w", encoding="utf-8") as f:
            f.write(optimized_text)
        
        # Extraer datos estructurados
        optimized_data = extract_structured_data(optimized_text, doc_type)
        
        # Guardar datos estructurados
        with open(output_dir / "optimized_data.json", "w", encoding="utf-8") as f:
            json.dump(optimized_data, f, indent=2, ensure_ascii=False)
        
        # Extraer códigos de producto
        product_codes = extract_product_codes(optimized_text, doc_type)
        
        # Métricas
        results["methods"]["optimized"] = {
            "time": optimized_time,
            "char_count": len(optimized_text),
            "word_count": count_words(optimized_text),
            "number_count": count_numbers(optimized_text),
            "doc_type": doc_type,
            "product_codes": product_codes,
            "extracted_data": optimized_data
        }
        
        logger.info(f"OCR optimizado completado en {optimized_time:.2f} segundos (tipo: {doc_type})")
    except Exception as e:
        logger.error(f"Error en OCR optimizado: {e}")
        results["methods"]["optimized"] = {"error": str(e)}
    
    # Calcular similitud entre métodos
    if "original" in results["methods"] and "optimized" in results["methods"]:
        if "error" not in results["methods"]["original"] and "error" not in results["methods"]["optimized"]:
            original_text = results["methods"]["original"].get("extracted_text", "")
            optimized_text = results["methods"]["optimized"].get("extracted_text", "")
            
            similarity = similar(original_text, optimized_text)
            results["similarity"] = similarity
            logger.info(f"Similitud entre métodos: {similarity:.2f}")
    
    # Guardar resultados completos
    with open(output_dir / "comparison_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    return results

def batch_compare(pdf_dir, output_dir=None):
    """
    Compara métodos OCR para todos los PDFs en un directorio
    
    Args:
        pdf_dir: Directorio con archivos PDF
        output_dir: Directorio para guardar resultados
    
    Returns:
        DataFrame con resultados comparativos
    """
    pdf_dir = Path(pdf_dir)
    if not pdf_dir.exists() or not pdf_dir.is_dir():
        logger.error(f"El directorio {pdf_dir} no existe")
        return None
    
    # Crear directorio de salida
    if not output_dir:
        output_dir = Path("resultados_ocr") / f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Encontrar todos los PDFs
    pdf_files = list(pdf_dir.glob("**/*.pdf"))
    if not pdf_files:
        logger.error(f"No se encontraron archivos PDF en {pdf_dir}")
        return None
    
    logger.info(f"Procesando {len(pdf_files)} archivos PDF en {pdf_dir}")
    
    # Procesar cada PDF
    all_results = []
    for pdf_file in pdf_files:
        pdf_output_dir = output_dir / pdf_file.stem
        result = compare_ocr_methods(pdf_file, pdf_output_dir)
        if result:
            all_results.append(result)
    
    # Crear DataFrame con resultados
    if all_results:
        # Extraer métricas principales
        metrics = []
        for result in all_results:
            row = {
                "filename": result["filename"],
                "similarity": result.get("similarity", None)
            }
            
            # Métricas del método original
            if "original" in result["methods"] and "error" not in result["methods"]["original"]:
                original = result["methods"]["original"]
                row.update({
                    "original_time": original.get("time"),
                    "original_chars": original.get("char_count"),
                    "original_words": original.get("word_count"),
                    "original_numbers": original.get("number_count")
                })
            
            # Métricas del método optimizado
            if "optimized" in result["methods"] and "error" not in result["methods"]["optimized"]:
                optimized = result["methods"]["optimized"]
                row.update({
                    "optimized_time": optimized.get("time"),
                    "optimized_chars": optimized.get("char_count"),
                    "optimized_words": optimized.get("word_count"),
                    "optimized_numbers": optimized.get("number_count"),
                    "doc_type": optimized.get("doc_type"),
                    "product_codes_count": len(optimized.get("product_codes", []))
                })
            
            metrics.append(row)
        
        # Crear DataFrame
        df = pd.DataFrame(metrics)
        
        # Calcular mejoras
        if "original_chars" in df.columns and "optimized_chars" in df.columns:
            df["char_improvement"] = ((df["optimized_chars"] - df["original_chars"]) / df["original_chars"] * 100).round(2)
        
        if "original_words" in df.columns and "optimized_words" in df.columns:
            df["word_improvement"] = ((df["optimized_words"] - df["original_words"]) / df["original_words"] * 100).round(2)
        
        if "original_numbers" in df.columns and "optimized_numbers" in df.columns:
            df["number_improvement"] = ((df["optimized_numbers"] - df["original_numbers"]) / df["original_numbers"] * 100).round(2)
        
        if "original_time" in df.columns and "optimized_time" in df.columns:
            df["time_difference"] = ((df["optimized_time"] - df["original_time"]) / df["original_time"] * 100).round(2)
        
        # Guardar DataFrame
        csv_path = output_dir / "comparison_summary.csv"
        df.to_csv(csv_path, index=False)
        logger.info(f"Resumen guardado en {csv_path}")
        
        # Generar estadísticas
        stats = {
            "total_files": len(df),
            "avg_similarity": df["similarity"].mean() if "similarity" in df.columns else None,
            "avg_char_improvement": df["char_improvement"].mean() if "char_improvement" in df.columns else None,
            "avg_word_improvement": df["word_improvement"].mean() if "word_improvement" in df.columns else None,
            "avg_number_improvement": df["number_improvement"].mean() if "number_improvement" in df.columns else None,
            "avg_time_difference": df["time_difference"].mean() if "time_difference" in df.columns else None,
            "doc_types": df["doc_type"].value_counts().to_dict() if "doc_type" in df.columns else None
        }
        
        # Guardar estadísticas
        with open(output_dir / "comparison_stats.json", "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        
        return df
    
    return None

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Comparar métodos de OCR")
    parser.add_argument("input", help="Archivo PDF o directorio con PDFs")
    parser.add_argument("--output", "-o", help="Directorio para guardar resultados")
    parser.add_argument("--batch", "-b", action="store_true", help="Procesar en modo batch")
    
    args = parser.parse_args()
    
    if args.batch or os.path.isdir(args.input):
        # Modo batch
        batch_compare(args.input, args.output)
    else:
        # Modo individual
        compare_ocr_methods(args.input, args.output)

if __name__ == "__main__":
    main()