#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para analizar el archivo Excel PVP JATA.xlsx
Determina el número de hojas y productos en el archivo
"""

import pandas as pd
import os

def analizar_excel_jata():
    """
    Analiza el archivo Excel PVP JATA.xlsx
    """
    archivo_excel = "/home/espasiko/mainmanusodoo/manusodoo-roto/informes/PVP JATA.xlsx"
    
    try:
        # Verificar que el archivo existe
        if not os.path.exists(archivo_excel):
            print(f"Error: El archivo {archivo_excel} no existe")
            return
        
        print(f"Analizando archivo: {archivo_excel}")
        print("=" * 50)
        
        # Leer todas las hojas del archivo Excel
        excel_file = pd.ExcelFile(archivo_excel)
        
        # Obtener nombres de las hojas
        nombres_hojas = excel_file.sheet_names
        num_hojas = len(nombres_hojas)
        
        print(f"Número total de hojas: {num_hojas}")
        print("\nNombres de las hojas:")
        for i, hoja in enumerate(nombres_hojas, 1):
            print(f"  {i}. {hoja}")
        
        print("\n" + "=" * 50)
        print("ANÁLISIS DETALLADO POR HOJA:")
        print("=" * 50)
        
        total_productos = 0
        
        # Analizar cada hoja
        for hoja in nombres_hojas:
            print(f"\n📊 Hoja: '{hoja}'")
            try:
                # Leer la hoja
                df = pd.read_excel(archivo_excel, sheet_name=hoja)
                
                # Información básica
                filas, columnas = df.shape
                print(f"   - Dimensiones: {filas} filas x {columnas} columnas")
                
                # Mostrar las primeras columnas para entender la estructura
                print(f"   - Columnas: {list(df.columns[:5])}{'...' if len(df.columns) > 5 else ''}")
                
                # Contar productos (asumiendo que cada fila es un producto, excluyendo encabezados)
                productos_en_hoja = max(0, filas - 1) if filas > 0 else 0
                print(f"   - Productos estimados: {productos_en_hoja}")
                
                # Buscar columnas que podrían contener información de productos
                columnas_producto = []
                for col in df.columns:
                    col_str = str(col).lower()
                    if any(palabra in col_str for palabra in ['producto', 'articulo', 'item', 'codigo', 'referencia', 'descripcion']):
                        columnas_producto.append(col)
                
                if columnas_producto:
                    print(f"   - Columnas de producto detectadas: {columnas_producto}")
                    # Contar productos únicos si hay una columna de código/referencia
                    if columnas_producto:
                        primera_col_producto = columnas_producto[0]
                        productos_unicos = df[primera_col_producto].dropna().nunique()
                        print(f"   - Productos únicos (por {primera_col_producto}): {productos_unicos}")
                        productos_en_hoja = productos_unicos
                
                total_productos += productos_en_hoja
                
                # Mostrar una muestra de datos
                if not df.empty:
                    print(f"   - Muestra de datos (primeras 3 filas):")
                    print(df.head(3).to_string(max_cols=5, max_colwidth=20))
                
            except Exception as e:
                print(f"   ❌ Error al leer la hoja '{hoja}': {str(e)}")
        
        print("\n" + "=" * 50)
        print("RESUMEN FINAL:")
        print("=" * 50)
        print(f"📋 Total de hojas: {num_hojas}")
        print(f"🛍️  Total de productos estimados: {total_productos}")
        
        return {
            'num_hojas': num_hojas,
            'nombres_hojas': nombres_hojas,
            'total_productos': total_productos
        }
        
    except Exception as e:
        print(f"Error al analizar el archivo: {str(e)}")
        return None

if __name__ == "__main__":
    resultado = analizar_excel_jata()
    if resultado:
        print(f"\n✅ Análisis completado exitosamente")
    else:
        print(f"\n❌ Error en el análisis")