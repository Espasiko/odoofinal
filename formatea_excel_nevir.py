#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para formatear el archivo Excel de NEVIR a la estructura esperada por el endpoint de importación.
Este script lee el archivo Excel original, extrae los datos relevantes y crea un nuevo archivo Excel
con el formato correcto para que sea compatible con el sistema de importación.
"""

import pandas as pd
import numpy as np
import os
import logging
import re
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"formatea_excel_nevir_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)

logger = logging.getLogger(__name__)

class ExcelFormateador:
    """
    Clase para formatear el archivo Excel de NEVIR al formato esperado por el endpoint de importación.
    """
    
    def __init__(self, archivo_origen, archivo_destino):
        """
        Inicializa el formateador con las rutas de los archivos de origen y destino.
        
        Args:
            archivo_origen (str): Ruta al archivo Excel original de NEVIR.
            archivo_destino (str): Ruta donde se guardará el archivo Excel formateado.
        """
        self.archivo_origen = archivo_origen
        self.archivo_destino = archivo_destino
        self.datos_proveedor = {}
        self.productos = []
        
    def _limpiar_valor_monetario(self, valor):
        """
        Limpia un valor monetario eliminando el símbolo de euro y espacios,
        y convirtiendo comas a puntos para valores decimales.
        
        Args:
            valor: Valor monetario a limpiar.
            
        Returns:
            float: Valor numérico limpio o 0.0 si no es válido.
        """
        if pd.isna(valor) or valor is None or valor == "":
            return 0.0
            
        if isinstance(valor, (int, float)):
            return float(valor)
            
        # Si es string, limpiamos el formato
        if isinstance(valor, str):
            # Eliminar símbolo de euro, espacios y convertir comas a puntos
            valor_limpio = valor.replace('€', '').replace(' ', '').replace(',', '.')
            # Eliminar cualquier otro carácter no numérico excepto punto decimal
            valor_limpio = re.sub(r'[^\d.]', '', valor_limpio)
            
            try:
                return float(valor_limpio) if valor_limpio else 0.0
            except ValueError:
                logger.warning(f"No se pudo convertir '{valor}' a número. Se usará 0.0")
                return 0.0
        
        return 0.0
        
    def _extraer_datos_proveedor(self):
        """
        Extrae los datos del proveedor de la hoja DATOS_PROVEEDOR.
        """
        logger.info("Extrayendo datos del proveedor...")
        try:
            # Leer la hoja de datos del proveedor
            df_proveedor = pd.read_excel(self.archivo_origen, sheet_name="DATOS_PROVEEDOR")
            
            # Filtrar solo las filas que contienen datos del proveedor (primeras filas)
            # Buscamos las filas donde la columna A tiene un valor y la columna B también
            filas_proveedor = df_proveedor[df_proveedor.iloc[:, 0].notna() & df_proveedor.iloc[:, 1].notna()]
            
            # Extraer los datos del proveedor como un diccionario
            for _, row in filas_proveedor.iterrows():
                campo = row.iloc[0]
                valor = row.iloc[1]
                if isinstance(campo, str) and campo.strip():
                    self.datos_proveedor[campo.strip().lower()] = valor
            
            logger.info(f"Datos del proveedor extraídos: {self.datos_proveedor}")
        except Exception as e:
            logger.error(f"Error al extraer datos del proveedor: {str(e)}")
            raise
    
    def _extraer_productos(self):
        """
        Extrae los datos de productos de la hoja PRODUCTOS.
        """
        logger.info("Extrayendo datos de productos...")
        try:
            # Leer la hoja de productos sin especificar encabezado
            df_productos = pd.read_excel(self.archivo_origen, sheet_name="PRODUCTOS", header=None)
            
            # Identificar la fila de categorías principales (como "LAVADORAS")
            categorias_principales = {}
            categoria_actual = None
            
            # Recorrer las filas para identificar categorías y productos
            productos_raw = []
            
            for i in range(len(df_productos)):
                row = df_productos.iloc[i]
                
                # Verificar si es una fila de categoría principal (generalmente en columna B)
                if pd.notna(row[1]) and pd.isna(row[0]) and pd.isna(row[2]):
                    texto = str(row[1]).strip()
                    if texto and texto.isupper() and len(texto) > 3:
                        categoria_actual = texto
                        logger.info(f"Categoría principal encontrada: {categoria_actual}")
                        continue
                
                # Verificar si es una fila de producto
                # Los productos tienen un código en columna B y descripción en columna C
                if pd.notna(row[1]) and pd.notna(row[2]) and pd.notna(row[5]) and pd.notna(row[6]):
                    # Parece ser un producto
                    producto = {
                        "referencia_proveedor": str(row[1]).strip(),
                        "nombre": str(row[2]).strip(),
                        "categoria": categoria_actual if categoria_actual else "PRODUCTOS NEVIR",
                        "precio_coste": row[5],  # Se limpiará después
                        "precio_venta": row[6],  # Se limpiará después
                    }
                    
                    # Añadir subcategoría si existe (columna D)
                    if pd.notna(row[3]):
                        producto["subcategoria"] = str(row[3]).strip()
                    
                    # Añadir barcode si existe (columna E)
                    if pd.notna(row[4]):
                        producto["barcode"] = str(row[4]).strip()
                    
                    # Añadir stock si existe (columna H)
                    if pd.notna(row[7]):
                        producto["stock"] = row[7]
                    
                    # Añadir imagen_url si existe (columna J)
                    if pd.notna(row[9]):
                        producto["imagen_url"] = str(row[9]).strip()
                    
                    productos_raw.append(producto)
            
            logger.info(f"Se encontraron {len(productos_raw)} productos en bruto")
            
            # Procesar y limpiar los productos encontrados
            for producto_raw in productos_raw:
                producto = {}
                
                # Copiar referencia y nombre
                producto["referencia_proveedor"] = producto_raw["referencia_proveedor"]
                producto["nombre"] = producto_raw["nombre"]
                
                # Copiar categoría y subcategoría si existen
                if "categoria" in producto_raw:
                    producto["categoria"] = producto_raw["categoria"]
                if "subcategoria" in producto_raw:
                    producto["subcategoria"] = producto_raw["subcategoria"]
                
                # Limpiar y convertir precios
                producto["precio_coste"] = self._limpiar_valor_monetario(producto_raw["precio_coste"])
                producto["precio_venta"] = self._limpiar_valor_monetario(producto_raw["precio_venta"])
                
                # Copiar barcode si existe
                if "barcode" in producto_raw:
                    producto["barcode"] = producto_raw["barcode"]
                
                # Copiar stock si existe
                if "stock" in producto_raw:
                    try:
                        producto["stock"] = float(producto_raw["stock"])
                    except (ValueError, TypeError):
                        producto["stock"] = 0.0
                
                # Copiar imagen_url si existe
                if "imagen_url" in producto_raw:
                    producto["imagen_url"] = producto_raw["imagen_url"]
                
                # Añadir tipo de producto y campos adicionales para compatibilidad con Odoo 18
                producto["type"] = "consu"  # 'consu' para productos consumibles en Odoo 18
                producto["sale_ok"] = True  # Producto disponible para venta
                producto["purchase_ok"] = True  # Producto disponible para compra
                producto["active"] = True  # Producto activo
                
                # Añadir producto a la lista final
                self.productos.append(producto)
            
            logger.info(f"Se extrajeron y procesaron {len(self.productos)} productos")
        except Exception as e:
            logger.error(f"Error al extraer productos: {str(e)}")
            raise
    
    def _crear_hoja_datos_proveedor(self, writer):
        """
        Crea la hoja de datos del proveedor en el formato esperado.
        
        Args:
            writer: ExcelWriter de pandas para escribir en el archivo.
        """
        logger.info("Creando hoja de datos del proveedor...")
        try:
            # Crear DataFrame con los datos del proveedor en formato campo-valor
            datos = []
            for campo, valor in self.datos_proveedor.items():
                datos.append({"campo": campo, "valor": valor})
            
            df_proveedor = pd.DataFrame(datos)
            
            # Escribir en el archivo Excel
            df_proveedor.to_excel(writer, sheet_name="DATOS_PROVEEDOR", index=False)
            logger.info("Hoja de datos del proveedor creada correctamente")
        except Exception as e:
            logger.error(f"Error al crear hoja de datos del proveedor: {str(e)}")
            raise
    
    def _crear_hoja_productos(self, writer):
        """
        Crea la hoja de productos en el formato esperado.
        
        Args:
            writer: ExcelWriter de pandas para escribir en el archivo.
        """
        logger.info("Creando hoja de productos...")
        try:
            # Crear DataFrame con los productos
            df_productos = pd.DataFrame(self.productos)
            
            # Asegurar que las columnas estén en el orden esperado
            columnas_ordenadas = [
                "referencia_proveedor", "nombre", "categoria", "subcategoria",
                "precio_coste", "precio_venta", "stock", "barcode", "imagen_url"
            ]
            
            # Filtrar solo las columnas que existen
            columnas_existentes = [col for col in columnas_ordenadas if col in df_productos.columns]
            
            # Reordenar columnas
            df_productos = df_productos[columnas_existentes]
            
            # Escribir en el archivo Excel
            df_productos.to_excel(writer, sheet_name="PRODUCTOS", index=False)
            logger.info("Hoja de productos creada correctamente")
        except Exception as e:
            logger.error(f"Error al crear hoja de productos: {str(e)}")
            raise
    
    def formatear(self):
        """
        Ejecuta el proceso completo de formateo del archivo Excel.
        """
        logger.info(f"Iniciando formateo del archivo {self.archivo_origen} a {self.archivo_destino}")
        try:
            # Extraer datos del archivo original
            self._extraer_datos_proveedor()
            self._extraer_productos()
            
            # Crear nuevo archivo Excel con el formato esperado
            with pd.ExcelWriter(self.archivo_destino, engine='openpyxl') as writer:
                self._crear_hoja_datos_proveedor(writer)
                self._crear_hoja_productos(writer)
            
            logger.info(f"Archivo formateado guardado en {self.archivo_destino}")
            return True
        except Exception as e:
            logger.error(f"Error al formatear el archivo: {str(e)}")
            return False

def main():
    """
    Función principal que ejecuta el formateo del archivo Excel.
    """
    # Rutas de los archivos
    directorio_base = os.path.dirname(os.path.abspath(__file__))
    archivo_origen = os.path.join(directorio_base, "ejemplos/proveedores_exl_csv/PVP NEVIR.xlsx")
    archivo_destino = os.path.join(directorio_base, "ejemplos/proveedores_exl_csv/PVP_NEVIR_FORMATEADO.xlsx")
    
    # Crear formateador y ejecutar
    formateador = ExcelFormateador(archivo_origen, archivo_destino)
    resultado = formateador.formatear()
    
    if resultado:
        logger.info("Proceso de formateo completado con éxito")
    else:
        logger.error("El proceso de formateo falló")

if __name__ == "__main__":
    main()
