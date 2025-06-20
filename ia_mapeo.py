#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Asistente de mapeo con IA para datos de proveedores a Odoo

Este script utiliza técnicas de procesamiento de lenguaje natural para mejorar
el mapeo de datos de proveedores a Odoo, detectando automáticamente categorías,
normalizando nombres de productos y sugiriendo correcciones.
"""

import os
import re
import pandas as pd
import numpy as np
from collections import Counter
from difflib import SequenceMatcher
from convertidor_proveedores import leer_archivo, detectar_proveedor

# Configuración
DIR_EJEMPLOS = "/home/espasiko/mainmanusodoo/manusodoo-roto/ejemplos"
DIR_SALIDA = "/home/espasiko/mainmanusodoo/manusodoo-roto/odoo_import"

# Patrones comunes en nombres de productos
PATRONES_PRODUCTO = {
    'marca': r'\(([^)]+)\)',  # Texto entre paréntesis, ej: (BALAY)
    'medidas': r'\b\d+[.,]?\d*\s*[xX]\s*\d+[.,]?\d*(?:\s*[xX]\s*\d+[.,]?\d*)?\b',  # ej: 60x40 o 180x60x70
    'capacidad': r'\b\d+\s*(?:KG|kg|Kg|L|l)\b',  # ej: 9KG o 12L
    'potencia': r'\b\d+\s*(?:W|w|kW|kw)\b',  # ej: 1200W
    'revoluciones': r'\b\d+\s*(?:RPM|rpm)\b',  # ej: 1400RPM
    'eficiencia': r'"([A-Z])"',  # Letra entre comillas, ej: "A"
}

# Categorías comunes y sus palabras clave
CATEGORIAS_COMUNES = {
    'Lavadoras': ['lavadora', 'lavasecadora', 'carga frontal', 'carga superior'],
    'Frigoríficos': ['frigorífico', 'combi', 'refrigerador', 'nevera'],
    'Lavavajillas': ['lavavajillas', 'lavaplatos'],
    'Hornos': ['horno', 'microondas', 'cocina'],
    'Campanas': ['campana', 'extractor'],
    'Secadoras': ['secadora'],
    'Congeladores': ['congelador', 'arcón'],
    'Pequeño Electrodoméstico': ['batidora', 'cafetera', 'tostadora', 'plancha', 'aspirador'],
}

def extraer_atributos(nombre):
    """Extrae atributos estructurados de un nombre de producto"""
    if not isinstance(nombre, str):
        return {}
    
    atributos = {}
    
    # Extraer marca
    marca_match = re.search(PATRONES_PRODUCTO['marca'], nombre)
    if marca_match:
        atributos['marca'] = marca_match.group(1).strip()
    
    # Extraer otros atributos
    for attr, patron in PATRONES_PRODUCTO.items():
        if attr == 'marca':
            continue  # Ya procesado
        
        match = re.search(patron, nombre)
        if match:
            atributos[attr] = match.group(0).strip()
    
    return atributos

def inferir_categoria(nombre, codigo=None):
    """Infiere la categoría de un producto basado en su nombre y código"""
    if not isinstance(nombre, str):
        return None
    
    nombre_lower = nombre.lower()
    
    # Buscar coincidencias con palabras clave de categorías
    for categoria, palabras_clave in CATEGORIAS_COMUNES.items():
        for palabra in palabras_clave:
            if palabra.lower() in nombre_lower:
                return categoria
    
    # Si no hay coincidencia clara, intentar inferir por el código
    if codigo and isinstance(codigo, str):
        # Implementar lógica específica según patrones de códigos
        pass
    
    return None

def normalizar_nombre(nombre, atributos):
    """Normaliza el nombre del producto para un formato consistente"""
    if not isinstance(nombre, str):
        return nombre
    
    # Eliminar información redundante que ya está en los atributos
    nombre_normalizado = nombre
    
    # Eliminar la marca entre paréntesis si ya la tenemos como atributo
    if 'marca' in atributos:
        nombre_normalizado = re.sub(r'\([^)]+\)', '', nombre_normalizado)
    
    # Limpiar espacios múltiples y al inicio/final
    nombre_normalizado = re.sub(r'\s+', ' ', nombre_normalizado).strip()
    
    return nombre_normalizado

def detectar_duplicados(df, umbral=0.85):
    """Detecta posibles productos duplicados basados en similitud de nombres"""
    duplicados = []
    nombres = df['nombre'].tolist()
    
    for i in range(len(nombres)):
        for j in range(i+1, len(nombres)):
            if isinstance(nombres[i], str) and isinstance(nombres[j], str):
                similitud = SequenceMatcher(None, nombres[i], nombres[j]).ratio()
                if similitud >= umbral:
                    duplicados.append({
                        'indice1': i,
                        'indice2': j,
                        'nombre1': nombres[i],
                        'nombre2': nombres[j],
                        'similitud': similitud
                    })
    
    return duplicados

def sugerir_categorias(df):
    """Sugiere categorías para productos basado en patrones y similitudes"""
    # Productos con categoría ya asignada
    productos_con_categoria = df[df['categoria'].notna()]
    
    # Productos sin categoría
    productos_sin_categoria = df[df['categoria'].isna()]
    
    sugerencias = {}
    
    for idx, row in productos_sin_categoria.iterrows():
        nombre = row['nombre']
        if not isinstance(nombre, str):
            continue
        
        # Intentar inferir categoría por el nombre
        categoria_inferida = inferir_categoria(nombre, row.get('codigo'))
        
        if categoria_inferida:
            sugerencias[idx] = {
                'nombre': nombre,
                'categoria_sugerida': categoria_inferida,
                'confianza': 'alta' if any(palabra.lower() in nombre.lower() 
                                         for palabra in CATEGORIAS_COMUNES[categoria_inferida]) else 'media'
            }
        else:
            # Buscar productos similares con categoría asignada
            mejor_similitud = 0
            mejor_categoria = None
            
            for _, prod_con_cat in productos_con_categoria.iterrows():
                if isinstance(prod_con_cat['nombre'], str):
                    similitud = SequenceMatcher(None, nombre.lower(), 
                                              prod_con_cat['nombre'].lower()).ratio()
                    if similitud > mejor_similitud and similitud > 0.6:
                        mejor_similitud = similitud
                        mejor_categoria = prod_con_cat['categoria']
            
            if mejor_categoria:
                sugerencias[idx] = {
                    'nombre': nombre,
                    'categoria_sugerida': mejor_categoria,
                    'confianza': 'baja',
                    'similitud': mejor_similitud
                }
    
    return sugerencias

def enriquecer_datos(df):
    """Enriquece los datos con atributos extraídos y categorías inferidas"""
    # Crear copia para no modificar el original
    df_enriquecido = df.copy()
    
    # Extraer atributos de los nombres
    atributos_lista = []
    for nombre in df_enriquecido['nombre']:
        atributos_lista.append(extraer_atributos(nombre))
    
    # Añadir columnas de atributos
    todos_atributos = set()
    for attrs in atributos_lista:
        todos_atributos.update(attrs.keys())
    
    for attr in todos_atributos:
        df_enriquecido[f'attr_{attr}'] = [a.get(attr, None) for a in atributos_lista]
    
    # Inferir categorías donde falten
    for idx, row in df_enriquecido.iterrows():
        if pd.isna(row['categoria']) or not row['categoria']:
            categoria_inferida = inferir_categoria(row['nombre'], row.get('codigo'))
            if categoria_inferida:
                df_enriquecido.at[idx, 'categoria'] = categoria_inferida
                df_enriquecido.at[idx, 'categoria_inferida'] = True
    
    # Normalizar nombres
    for idx, row in df_enriquecido.iterrows():
        atributos = {k.replace('attr_', ''): v for k, v in row.items() 
                    if k.startswith('attr_') and pd.notna(v)}
        df_enriquecido.at[idx, 'nombre_normalizado'] = normalizar_nombre(row['nombre'], atributos)
    
    return df_enriquecido

def analizar_archivo(ruta_archivo):
    """Analiza un archivo de proveedor y muestra información enriquecida"""
    nombre_archivo = os.path.basename(ruta_archivo)
    proveedor = detectar_proveedor(nombre_archivo)
    
    if not proveedor:
        print(f"No se pudo detectar el proveedor para: {nombre_archivo}")
        return None
    
    print(f"\n{'=' * 50}")
    print(f"ANÁLISIS IA: {nombre_archivo} (Proveedor: {proveedor})")
    print(f"{'=' * 50}")
    
    # Leer archivo
    df = leer_archivo(ruta_archivo)
    if df is None:
        print("No se pudo leer el archivo")
        return None
    
    # Procesar según el proveedor (simplificado para este ejemplo)
    productos = []
    
    # Extraer productos según el formato del proveedor
    if proveedor == 'BSH':
        # Buscar columnas relevantes
        if 'CÓDIGO' in df.columns and 'DESCRIPCIÓN' in df.columns:
            categoria_actual = None
            
            for _, row in df.iterrows():
                # Verificar si es una fila de categoría
                if pd.notna(row['CÓDIGO']) and isinstance(row['CÓDIGO'], str) and \
                   (pd.isna(row['DESCRIPCIÓN']) or not str(row['DESCRIPCIÓN']).strip()):
                    categoria_actual = row['CÓDIGO'].strip()
                
                # Si tiene código y descripción, es un producto
                elif pd.notna(row['CÓDIGO']) and pd.notna(row['DESCRIPCIÓN']) and \
                     isinstance(row['CÓDIGO'], str) and row['CÓDIGO'].strip():
                    productos.append({
                        'codigo': row['CÓDIGO'].strip(),
                        'nombre': row['DESCRIPCIÓN'].strip(),
                        'categoria': categoria_actual,
                        'precio': row.get('TOTAL') if pd.notna(row.get('TOTAL')) else None,
                        'precio_venta': row.get('P.V.P FINAL CLIENTE') if pd.notna(row.get('P.V.P FINAL CLIENTE')) else None
                    })
    elif proveedor == 'CECOTEC':
        # Procesar formato CECOTEC con columnas __EMPTY_*
        categoria_actual = None
        
        for _, row in df.iterrows():
            # Verificar si es una fila de categoría (solo tiene la columna CECOTEC con valor y sin __EMPTY_1)
            if pd.notna(row.get('CECOTEC')) and isinstance(row.get('CECOTEC'), str) and \
               (pd.isna(row.get('__EMPTY_1')) or not str(row.get('__EMPTY_1')).strip()):
                categoria_actual = row.get('CECOTEC').strip()
            
            # Si tiene código y descripción, es un producto
            elif pd.notna(row.get('CECOTEC')) and pd.notna(row.get('__EMPTY_1')) and \
                 (isinstance(row.get('CECOTEC'), (int, str))) and str(row.get('CECOTEC')).strip():
                
                # Extraer código (puede ser numérico o string)
                codigo = str(row.get('CECOTEC')).strip()
                
                productos.append({
                    'codigo': codigo,
                    'nombre': str(row.get('__EMPTY_1')).strip(),
                    'categoria': categoria_actual,
                    'precio': row.get('__EMPTY_5') if pd.notna(row.get('__EMPTY_5')) else None,
                    'precio_venta': row.get('__EMPTY_9') if pd.notna(row.get('__EMPTY_9')) else None
                })
    
    elif proveedor == 'ALMCE':
        # Implementar extracción para ALMCE
        pass
    
    # Convertir a DataFrame
    if productos:
        df_productos = pd.DataFrame(productos)
        
        # Enriquecer datos
        df_enriquecido = enriquecer_datos(df_productos)
        
        # Mostrar estadísticas
        print(f"\nProductos encontrados: {len(df_enriquecido)}")
        
        # Distribución de categorías
        categorias = df_enriquecido['categoria'].dropna().value_counts()
        print("\nDistribución de categorías:")
        for cat, count in categorias.items():
            print(f"  - {cat}: {count} productos")
        
        # Productos sin categoría
        sin_categoria = df_enriquecido['categoria'].isna().sum()
        if sin_categoria > 0:
            print(f"\nProductos sin categoría: {sin_categoria}")
            
            # Sugerir categorías
            sugerencias = sugerir_categorias(df_enriquecido)
            if sugerencias:
                print("\nSugerencias de categorías:")
                for idx, sugerencia in list(sugerencias.items())[:5]:  # Mostrar solo las primeras 5
                    print(f"  - {sugerencia['nombre']}: {sugerencia['categoria_sugerida']} (confianza: {sugerencia['confianza']})")
                if len(sugerencias) > 5:
                    print(f"    ... y {len(sugerencias) - 5} más")
        
        # Detectar posibles duplicados
        duplicados = detectar_duplicados(df_enriquecido)
        if duplicados:
            print(f"\nPosibles productos duplicados: {len(duplicados)}")
            for dup in duplicados[:3]:  # Mostrar solo los primeros 3
                print(f"  - Similitud {dup['similitud']:.2f}: {dup['nombre1']} | {dup['nombre2']}")
            if len(duplicados) > 3:
                print(f"    ... y {len(duplicados) - 3} más")
        
        # Atributos extraídos
        atributos_cols = [col for col in df_enriquecido.columns if col.startswith('attr_')]
        if atributos_cols:
            print("\nAtributos extraídos:")
            for attr in atributos_cols:
                attr_name = attr.replace('attr_', '')
                count = df_enriquecido[attr].notna().sum()
                if count > 0:
                    print(f"  - {attr_name}: encontrado en {count} productos")
        
        return df_enriquecido
    else:
        print("No se encontraron productos en el archivo")
        return None

def mapear_a_formato_odoo(df_enriquecido, proveedor):
    """Mapea los datos enriquecidos al formato esperado por Odoo"""
    if df_enriquecido is None or len(df_enriquecido) == 0:
        return None
    
    # Función para convertir valores False o NaN a cadenas vacías
    def safe_str(value, default=""):
        return str(value) if value is not False and pd.notna(value) else default
    
    # Crear DataFrame para Odoo
    datos_odoo = []
    
    # Mapear campos según el tipo de dato (proveedor o producto)
    # Para este ejemplo, asumimos que estamos mapeando productos
    for idx, row in df_enriquecido.iterrows():
        datos_odoo.append({
            'name': safe_str(row['nombre_normalizado'], row['nombre']),
            'default_code': safe_str(row.get('codigo', f"PROD-{idx}"), f"PROD-{idx}"),
            'categ_id': safe_str(row.get('categoria', '')),
            'list_price': row.get('precio_venta', 0.0) if pd.notna(row.get('precio_venta')) else 0.0,
            'standard_price': row.get('precio', 0.0) if pd.notna(row.get('precio')) else 0.0,
            # Campos adicionales para Odoo
            'type': 'product',
            'sale_ok': True,
            'purchase_ok': True,
            'active': True
        })
    
    df_odoo = pd.DataFrame(datos_odoo)
    return df_odoo

def main():
    print("ASISTENTE DE MAPEO CON IA PARA DATOS DE PROVEEDORES")
    print("=" * 50)
    
    # Listar archivos disponibles
    archivos = [f for f in os.listdir(DIR_EJEMPLOS) 
               if f.lower().endswith(('.csv', '.xlsx', '.xls'))]
    
    if not archivos:
        print(f"No se encontraron archivos CSV o Excel en {DIR_EJEMPLOS}")
        return
    
    print(f"\nArchivos disponibles en {DIR_EJEMPLOS}:")
    for i, archivo in enumerate(archivos, 1):
        print(f"{i}. {archivo}")
    
    # Seleccionar archivo para análisis
    try:
        seleccion = int(input("\nSeleccione un número de archivo para analizar (0 para salir): "))
        if seleccion == 0:
            return
        if 1 <= seleccion <= len(archivos):
            archivo_seleccionado = os.path.join(DIR_EJEMPLOS, archivos[seleccion-1])
            df_enriquecido = analizar_archivo(archivo_seleccionado)
            
            if df_enriquecido is not None:
                # Mapear a formato Odoo
                proveedor = detectar_proveedor(os.path.basename(archivo_seleccionado))
                df_odoo = mapear_a_formato_odoo(df_enriquecido, proveedor)
                
                if df_odoo is not None and len(df_odoo) > 0:
                    print(f"\nDatos mapeados al formato Odoo: {len(df_odoo)} productos listos para importar")
                
                # Preguntar si desea guardar el análisis
                if input("\n¿Desea guardar el análisis enriquecido? (s/n): ").lower() == 's':
                    if not os.path.exists(DIR_SALIDA):
                        os.makedirs(DIR_SALIDA)
                    
                    nombre_base = os.path.splitext(os.path.basename(archivo_seleccionado))[0]
                    ruta_salida = os.path.join(DIR_SALIDA, f"{nombre_base}_enriquecido.csv")
                    df_enriquecido.to_csv(ruta_salida, index=False)
                    print(f"Análisis guardado en: {ruta_salida}")
                    
                    if df_odoo is not None and len(df_odoo) > 0:
                        ruta_odoo = os.path.join(DIR_SALIDA, f"{nombre_base}_odoo.csv")
                        df_odoo.to_csv(ruta_odoo, index=False)
                        print(f"Archivo para Odoo guardado en: {ruta_odoo}")
        else:
            print("Selección no válida")
    except ValueError:
        print("Por favor, ingrese un número válido")

if __name__ == "__main__":
    main()