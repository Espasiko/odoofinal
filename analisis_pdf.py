#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import fitz  # PyMuPDF
import tabula
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
import tempfile
import subprocess
import base64
import requests
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuración
API_URL = "http://localhost:8000/api/v1/debug-ocr/raw-extraction"

def analizar_estructura_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    Analiza la estructura interna del PDF para determinar si contiene texto extraíble,
    imágenes, tablas y otras características relevantes.
    """
    resultado = {
        "nombre_archivo": os.path.basename(pdf_path),
        "tamaño_kb": os.path.getsize(pdf_path) / 1024,
        "paginas": 0,
        "bloques_texto": 0,
        "bloques_imagen": 0,
        "caracteres_texto": 0,
        "es_imagen_escaneada": False,
        "tiene_texto_extraible": False,
        "creador": "",
        "productor": "",
        "version_pdf": ""
    }
    
    try:
        # Abrir el PDF con PyMuPDF
        doc = fitz.open(pdf_path)
        resultado["paginas"] = len(doc)
        
        total_text = ""
        
        # Analizar cada página
        for page_num, page in enumerate(doc):
            page_text = page.get_text("text")
            total_text += page_text
            resultado["bloques_texto"] += len(page.get_text("blocks"))
            resultado["bloques_imagen"] += len(page.get_images())
        
        resultado["caracteres_texto"] = len(total_text)
        resultado["tiene_texto_extraible"] = resultado["caracteres_texto"] > 100
        resultado["es_imagen_escaneada"] = resultado["caracteres_texto"] < 100 and resultado["bloques_imagen"] > 0
        
        # Obtener metadatos del PDF
        metadata = doc.metadata
        if metadata:
            resultado["creador"] = metadata.get("creator", "")
            resultado["productor"] = metadata.get("producer", "")
            resultado["version_pdf"] = f"{doc.version}"
        
        doc.close()
        
        # Intentar usar pdfinfo para obtener más detalles
        try:
            with tempfile.NamedTemporaryFile(suffix=".txt") as tmp:
                subprocess.run(["pdfinfo", pdf_path], stdout=tmp, stderr=subprocess.PIPE, check=True)
                tmp.flush()
                tmp.seek(0)
                pdf_info = tmp.read().decode('utf-8')
                
                if "Creator:" in pdf_info and not resultado["creador"]:
                    resultado["creador"] = pdf_info.split("Creator:")[1].split("\n")[0].strip()
                
                if "Producer:" in pdf_info and not resultado["productor"]:
                    resultado["productor"] = pdf_info.split("Producer:")[1].split("\n")[0].strip()
        except (subprocess.SubprocessError, FileNotFoundError):
            pass  # Ignorar si pdfinfo no está disponible
            
    except Exception as e:
        logger.error(f"Error al analizar la estructura del PDF: {e}")
    
    return resultado

def probar_metodos_tabula(pdf_path: str) -> Dict[str, Any]:
    """
    Prueba diferentes métodos de extracción con Tabula y devuelve los resultados
    """
    resultado = {
        "lattice": {"tablas": 0, "filas_totales": 0, "columnas_max": 0, "muestra": None},
        "stream": {"tablas": 0, "filas_totales": 0, "columnas_max": 0, "muestra": None},
        "area_superior": {"tablas": 0, "filas_totales": 0, "columnas_max": 0, "muestra": None},
        "area_inferior": {"tablas": 0, "filas_totales": 0, "columnas_max": 0, "muestra": None},
        "mejor_metodo": "",
        "tablas_detectadas": False
    }
    
    try:
        # Método 1: Lattice (para tablas con líneas/bordes)
        lattice_tables = tabula.read_pdf(
            pdf_path, 
            pages='all', 
            multiple_tables=True, 
            lattice=True, 
            stream=False
        )
        
        if lattice_tables:
            resultado["lattice"]["tablas"] = len(lattice_tables)
            resultado["lattice"]["filas_totales"] = sum(len(table) for table in lattice_tables if not table.empty)
            resultado["lattice"]["columnas_max"] = max((len(table.columns) for table in lattice_tables if not table.empty), default=0)
            if lattice_tables and not lattice_tables[0].empty:
                # Convertir a diccionario para serialización JSON
                resultado["lattice"]["muestra"] = lattice_tables[0].head(3).replace({np.nan: None}).to_dict()
        
        # Método 2: Stream (para tablas sin líneas)
        stream_tables = tabula.read_pdf(
            pdf_path, 
            pages='all', 
            multiple_tables=True, 
            lattice=False, 
            stream=True
        )
        
        if stream_tables:
            resultado["stream"]["tablas"] = len(stream_tables)
            resultado["stream"]["filas_totales"] = sum(len(table) for table in stream_tables if not table.empty)
            resultado["stream"]["columnas_max"] = max((len(table.columns) for table in stream_tables if not table.empty), default=0)
            if stream_tables and not stream_tables[0].empty:
                resultado["stream"]["muestra"] = stream_tables[0].head(3).replace({np.nan: None}).to_dict()
        
        # Método 3: Área específica (mitad superior de la página)
        area_superior_tables = tabula.read_pdf(
            pdf_path, 
            pages='1', 
            multiple_tables=True, 
            area=[0, 0, 50, 100],  # [top, left, bottom, right] como porcentajes
            relative_area=True
        )
        
        if area_superior_tables:
            resultado["area_superior"]["tablas"] = len(area_superior_tables)
            resultado["area_superior"]["filas_totales"] = sum(len(table) for table in area_superior_tables if not table.empty)
            resultado["area_superior"]["columnas_max"] = max((len(table.columns) for table in area_superior_tables if not table.empty), default=0)
            if area_superior_tables and not area_superior_tables[0].empty:
                resultado["area_superior"]["muestra"] = area_superior_tables[0].head(3).replace({np.nan: None}).to_dict()
        
        # Método 4: Área específica (mitad inferior de la página)
        area_inferior_tables = tabula.read_pdf(
            pdf_path, 
            pages='1', 
            multiple_tables=True, 
            area=[50, 0, 100, 100],  # [top, left, bottom, right] como porcentajes
            relative_area=True
        )
        
        if area_inferior_tables:
            resultado["area_inferior"]["tablas"] = len(area_inferior_tables)
            resultado["area_inferior"]["filas_totales"] = sum(len(table) for table in area_inferior_tables if not table.empty)
            resultado["area_inferior"]["columnas_max"] = max((len(table.columns) for table in area_inferior_tables if not table.empty), default=0)
            if area_inferior_tables and not area_inferior_tables[0].empty:
                resultado["area_inferior"]["muestra"] = area_inferior_tables[0].head(3).replace({np.nan: None}).to_dict()
        
        # Determinar el mejor método
        metodos = ["lattice", "stream", "area_superior", "area_inferior"]
        mejor_metodo = max(metodos, key=lambda m: resultado[m]["filas_totales"])
        resultado["mejor_metodo"] = mejor_metodo
        resultado["tablas_detectadas"] = any(resultado[m]["tablas"] > 0 for m in metodos)
        
    except Exception as e:
        logger.error(f"Error al probar métodos de extracción: {e}")
    
    return resultado

def enviar_a_endpoint(pdf_path: str) -> Dict[str, Any]:
    """
    Envía el PDF al endpoint de extracción y devuelve la respuesta
    """
    try:
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
        response = requests.post(API_URL, json=payload)
        
        if response.status_code != 200:
            logger.error(f"Error en la solicitud: {response.status_code} {response.reason}")
            return {}
        
        return response.json()
        
    except Exception as e:
        logger.error(f"Error al enviar al endpoint: {e}")
        return {}

def generar_recomendaciones(estructura: Dict[str, Any], tabula_resultados: Dict[str, Any], endpoint_resultados: Dict[str, Any]) -> List[str]:
    """
    Genera recomendaciones basadas en el análisis del PDF
    """
    recomendaciones = []
    
    # Verificar si el PDF es principalmente una imagen escaneada
    if estructura["es_imagen_escaneada"]:
        recomendaciones.append("El PDF parece ser principalmente una imagen escaneada con poco texto extraíble.")
        recomendaciones.append("Considerar usar solo OCR para este tipo de facturas, ya que Tabula no funcionará bien con imágenes.")
        recomendaciones.append("Si es necesario usar Tabula, primero procesar el PDF con OCR para generar una versión con texto extraíble.")
    
    # Verificar si Tabula detectó tablas directamente pero no a través del endpoint
    if tabula_resultados["tablas_detectadas"] and not endpoint_resultados.get("tables", []):
        recomendaciones.append(f"Tabula detectó tablas usando el método '{tabula_resultados['mejor_metodo']}', pero no a través del endpoint.")
        recomendaciones.append("Modificar el servicio de extracción para usar este método específico.")
    
    # Si no se detectaron tablas con ningún método
    if not tabula_resultados["tablas_detectadas"]:
        recomendaciones.append("No se detectaron tablas con ningún método de Tabula.")
        if estructura["tiene_texto_extraible"]:
            recomendaciones.append("Aunque el PDF tiene texto extraíble, las tablas podrían no tener una estructura clara para Tabula.")
            recomendaciones.append("Considerar usar expresiones regulares o patrones específicos para extraer datos tabulares del texto OCR.")
    
    # Recomendaciones basadas en el mejor método
    if tabula_resultados["tablas_detectadas"]:
        mejor = tabula_resultados["mejor_metodo"]
        recomendaciones.append(f"El mejor método para este PDF es '{mejor}' con {tabula_resultados[mejor]['tablas']} tablas y {tabula_resultados[mejor]['filas_totales']} filas.")
        
        if mejor == "lattice":
            recomendaciones.append("Este PDF tiene tablas con líneas/bordes bien definidos. Usar lattice=True en Tabula.")
        elif mejor == "stream":
            recomendaciones.append("Este PDF tiene tablas sin líneas/bordes claros. Usar stream=True en Tabula.")
        else:
            recomendaciones.append(f"Este PDF requiere extracción por áreas específicas. Usar el área '{mejor}'.")
    
    return recomendaciones

def main():
    """Función principal"""
    if len(sys.argv) != 2:
        print("Uso: python analisis_pdf.py <ruta_al_pdf>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    if not os.path.exists(pdf_path):
        print(f"Error: El archivo {pdf_path} no existe")
        sys.exit(1)
    
    print(f"Analizando archivo: {pdf_path}")
    
    # 1. Analizar la estructura interna del PDF
    print("\n=== ANÁLISIS DE ESTRUCTURA DEL PDF ===\n")
    estructura = analizar_estructura_pdf(pdf_path)
    
    print(f"Información general del PDF:")
    print(f"- Nombre: {estructura['nombre_archivo']}")
    print(f"- Tamaño: {estructura['tamaño_kb']:.2f} KB")
    print(f"- Páginas: {estructura['paginas']}")
    print(f"- Bloques de texto: {estructura['bloques_texto']}")
    print(f"- Bloques de imagen: {estructura['bloques_imagen']}")
    print(f"- Caracteres de texto: {estructura['caracteres_texto']}")
    print(f"- Creador: {estructura['creador']}")
    print(f"- Productor: {estructura['productor']}")
    print(f"- Versión PDF: {estructura['version_pdf']}")
    
    if estructura["es_imagen_escaneada"]:
        print("\n⚠️ Este PDF parece ser principalmente una imagen escaneada con poco texto extraíble.")
        print("   Esto puede dificultar la extracción de tablas con Tabula.")
    elif not estructura["tiene_texto_extraible"]:
        print("\n⚠️ Este PDF no contiene suficiente texto extraíble.")
        print("   Es probablemente una imagen escaneada sin OCR previo.")
    else:
        print("\n✓ Este PDF contiene texto extraíble que podría ser procesado por Tabula.")
    
    # 2. Probar diferentes métodos de extracción con Tabula
    print("\n=== PRUEBAS DE EXTRACCIÓN CON TABULA ===\n")
    tabula_resultados = probar_metodos_tabula(pdf_path)
    
    print("Método 1: Lattice (tablas con líneas/bordes)")
    print(f"- Tablas detectadas: {tabula_resultados['lattice']['tablas']}")
    print(f"- Filas totales: {tabula_resultados['lattice']['filas_totales']}")
    print(f"- Columnas máximas: {tabula_resultados['lattice']['columnas_max']}")
    
    print("\nMétodo 2: Stream (tablas sin líneas)")
    print(f"- Tablas detectadas: {tabula_resultados['stream']['tablas']}")
    print(f"- Filas totales: {tabula_resultados['stream']['filas_totales']}")
    print(f"- Columnas máximas: {tabula_resultados['stream']['columnas_max']}")
    
    print("\nMétodo 3: Área superior de la página")
    print(f"- Tablas detectadas: {tabula_resultados['area_superior']['tablas']}")
    print(f"- Filas totales: {tabula_resultados['area_superior']['filas_totales']}")
    print(f"- Columnas máximas: {tabula_resultados['area_superior']['columnas_max']}")
    
    print("\nMétodo 4: Área inferior de la página")
    print(f"- Tablas detectadas: {tabula_resultados['area_inferior']['tablas']}")
    print(f"- Filas totales: {tabula_resultados['area_inferior']['filas_totales']}")
    print(f"- Columnas máximas: {tabula_resultados['area_inferior']['columnas_max']}")
    
    if tabula_resultados["tablas_detectadas"]:
        print(f"\n✓ Mejor método: {tabula_resultados['mejor_metodo']}")
        
        # Mostrar muestra de la tabla detectada con el mejor método
        mejor = tabula_resultados["mejor_metodo"]
        if tabula_resultados[mejor]["muestra"]:
            print("\nMuestra de tabla detectada:")
            for col, values in tabula_resultados[mejor]["muestra"].items():
                print(f"  {col}: {list(values.values())[:3]}")
    else:
        print("\n⚠️ No se detectaron tablas con ningún método de Tabula.")
    
    # 3. Enviar al endpoint y comparar resultados
    print("\n=== ENVIANDO AL ENDPOINT DE EXTRACCIÓN ===\n")
    endpoint_resultados = enviar_a_endpoint(pdf_path)
    
    if endpoint_resultados:
        print("✓ Solicitud al endpoint exitosa")
        
        # Guardar la respuesta en un archivo JSON
        output_filename = os.path.splitext(os.path.basename(pdf_path))[0] + "_analisis.json"
        with open(output_filename, "w") as f:
            json.dump({
                "estructura_pdf": estructura,
                "tabula_resultados": tabula_resultados,
                "endpoint_resultados": endpoint_resultados
            }, f, indent=2)
        
        print(f"Análisis completo guardado en {output_filename}")
        
        # Verificar si el endpoint detectó tablas
        tablas_endpoint = endpoint_resultados.get("tables", [])
        print(f"Tablas detectadas por el endpoint: {len(tablas_endpoint)}")
    else:
        print("⚠️ Error al enviar al endpoint o respuesta inválida")
    
    # 4. Generar recomendaciones
    print("\n=== RECOMENDACIONES ===\n")
    recomendaciones = generar_recomendaciones(estructura, tabula_resultados, endpoint_resultados)
    
    for i, rec in enumerate(recomendaciones, 1):
        print(f"{i}. {rec}")
    
    # 5. Resumen final
    print("\n=== RESUMEN FINAL ===\n")
    if tabula_resultados["tablas_detectadas"]:
        print(f"✓ Tabula puede extraer tablas de este PDF usando el método '{tabula_resultados['mejor_metodo']}'.")
        if not endpoint_resultados.get("tables", []):
            print("⚠️ Sin embargo, el endpoint no está detectando estas tablas correctamente.")
            print("   Se recomienda modificar el servicio de extracción para usar el método adecuado.")
    else:
        print("⚠️ Tabula no puede extraer tablas de este PDF con ningún método.")
        if estructura["es_imagen_escaneada"]:
            print("   Esto se debe a que el PDF es principalmente una imagen escaneada.")
            print("   Se recomienda usar solo OCR o pre-procesar el PDF con OCR antes de usar Tabula.")
        else:
            print("   Esto puede deberse a que las tablas no tienen una estructura clara para Tabula.")
            print("   Se recomienda usar expresiones regulares o patrones específicos para extraer datos del texto OCR.")

if __name__ == "__main__":
    main()
