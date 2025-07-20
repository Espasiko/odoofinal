#!/usr/bin/env python3
"""
Servicio para extraer texto de archivos PDF
"""
import logging
import os
import tempfile
import subprocess
from typing import Optional

# Configurar logging
logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extrae texto de un archivo PDF usando pdftotext (poppler-utils)
    
    Args:
        pdf_path: Ruta al archivo PDF
        
    Returns:
        str: Texto extraído del PDF
    """
    if not os.path.exists(pdf_path):
        logger.error(f"El archivo PDF no existe: {pdf_path}")
        return ""
    
    try:
        # Crear archivo temporal para la salida
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as temp_file:
            output_path = temp_file.name
        
        # Ejecutar pdftotext para extraer el texto
        # -layout mantiene el formato de texto similar al PDF
        # -enc UTF-8 asegura que la codificación sea UTF-8
        cmd = ["pdftotext", "-layout", "-enc", "UTF-8", pdf_path, output_path]
        process = subprocess.run(cmd, capture_output=True, text=True)
        
        if process.returncode != 0:
            logger.error(f"Error al ejecutar pdftotext: {process.stderr}")
            
            # Intentar con otro método si pdftotext falla
            try:
                import PyPDF2
                text = ""
                with open(pdf_path, "rb") as file:
                    reader = PyPDF2.PdfReader(file)
                    for page_num in range(len(reader.pages)):
                        text += reader.pages[page_num].extract_text() + "\n\n"
                return text
            except Exception as e:
                logger.error(f"Error al extraer texto con PyPDF2: {str(e)}")
                return ""
        
        # Leer el archivo de texto generado
        with open(output_path, "r", encoding="utf-8") as file:
            text = file.read()
        
        # Eliminar el archivo temporal
        os.unlink(output_path)
        
        return text
    
    except Exception as e:
        logger.error(f"Error al extraer texto del PDF: {str(e)}")
        
        # Intentar con PyPDF2 como respaldo
        try:
            import PyPDF2
            text = ""
            with open(pdf_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                for page_num in range(len(reader.pages)):
                    text += reader.pages[page_num].extract_text() + "\n\n"
            return text
        except Exception as e2:
            logger.error(f"Error al extraer texto con método alternativo: {str(e2)}")
            return ""
