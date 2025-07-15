#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para depurar la importación de productos NEVIR en Odoo 18.
Este script analiza el Excel formateado y compara los productos para identificar
diferencias que puedan causar fallos en la importación.
"""

import os
import sys
import json
import logging
import pandas as pd

# Añadir el directorio de servicios al path para poder importar los módulos
api_services_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'api', 'services')
sys.path.append(api_services_path)

# Importar los servicios necesarios
from odoo_product_service import OdooProductService
from odoo_provider_service import OdooProviderService
from product_category_service import ProductCategoryService

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def cargar_excel(ruta_excel):
    """
    Carga el archivo Excel formateado y extrae los datos de productos.
    """
    try:
        # Cargar datos del proveedor
        df_proveedor = pd.read_excel(ruta_excel, sheet_name="DATOS_PROVEEDOR", header=None)
        datos_proveedor = {}
        for _, row in df_proveedor.iterrows():
            if pd.notna(row[0]) and pd.notna(row[1]):
                datos_proveedor[row[0]] = row[1]
        
        # Cargar datos de productos
        df_productos = pd.read_excel(ruta_excel, sheet_name="PRODUCTOS")
        productos = df_productos.to_dict('records')
        
        return datos_proveedor, productos
    except Exception as e:
        logger.error(f"Error al cargar el archivo Excel: {str(e)}")
        raise

def analizar_productos(productos):
    """
    Analiza los productos para identificar posibles problemas.
    """
    logger.info(f"Analizando {len(productos)} productos...")
    
    # Verificar campos obligatorios
    for i, producto in enumerate(productos):
        logger.info(f"\n--- Producto {i+1}: {producto.get('nombre', 'Sin nombre')} ---")
        
        # Verificar nombre
        if 'nombre' not in producto or not producto['nombre']:
            logger.warning(f"Producto {i+1}: Falta el campo 'nombre'")
        else:
            logger.info(f"Nombre: {producto['nombre']}")
        
        # Verificar referencia
        if 'referencia_proveedor' not in producto or not producto['referencia_proveedor']:
            logger.warning(f"Producto {i+1}: Falta el campo 'referencia_proveedor'")
        else:
            logger.info(f"Referencia: {producto['referencia_proveedor']}")
        
        # Verificar categoría
        if 'categoria' not in producto or not producto['categoria']:
            logger.warning(f"Producto {i+1}: Falta el campo 'categoria'")
        else:
            logger.info(f"Categoría: {producto['categoria']}")
        
        # Verificar precios
        if 'precio_coste' not in producto:
            logger.warning(f"Producto {i+1}: Falta el campo 'precio_coste'")
        else:
            logger.info(f"Precio coste: {producto['precio_coste']}")
        
        if 'precio_venta' not in producto:
            logger.warning(f"Producto {i+1}: Falta el campo 'precio_venta'")
        else:
            logger.info(f"Precio venta: {producto['precio_venta']}")
        
        # Verificar campos adicionales importantes
        campos_adicionales = ['type', 'sale_ok', 'purchase_ok', 'active']
        for campo in campos_adicionales:
            if campo not in producto:
                logger.warning(f"Producto {i+1}: Falta el campo '{campo}'")
            else:
                logger.info(f"{campo}: {producto[campo]}")

def probar_importacion_directa(productos):
    """
    Prueba la importación directa de cada producto usando el servicio de productos.
    """
    logger.info("\n=== Probando importación directa de productos ===")
    
    odoo_service = OdooProductService()
    provider_service = OdooProviderService()
    category_service = ProductCategoryService()
    
    # Crear o actualizar proveedor NEVIR
    proveedor_data = {
        "name": "NEVIR",
        "vat": "B84691294",
        "email": "info@nevir.es",
        "supplier_rank": 1
    }
    
    try:
        proveedor_id = provider_service.create_or_update_provider(proveedor_data)
        logger.info(f"Proveedor NEVIR creado/actualizado con ID: {proveedor_id}")
    except Exception as e:
        logger.error(f"Error al crear/actualizar proveedor NEVIR: {str(e)}")
        proveedor_id = None
    
    # Probar cada producto individualmente
    for i, producto in enumerate(productos):
        nombre_producto = producto.get('nombre', f"Producto {i+1}")
        logger.info(f"\n--- Probando importación de {nombre_producto} ---")
        
        try:
            # Asegurar que el campo 'name' esté presente
            if 'name' not in producto and 'nombre' in producto:
                producto['name'] = producto['nombre']
            
            # Asegurar que los campos de precio estén correctamente mapeados
            if 'list_price' not in producto and 'precio_venta' in producto:
                producto['list_price'] = float(producto['precio_venta'])
            
            if 'standard_price' not in producto and 'precio_coste' in producto:
                producto['standard_price'] = float(producto['precio_coste'])
            
            # Asegurar que el tipo de producto sea 'consu'
            producto['type'] = 'consu'
            
            # Asegurar campos adicionales importantes
            producto['sale_ok'] = True
            producto['purchase_ok'] = True
            producto['active'] = True
            
            # Si hay proveedor, añadir la relación
            if proveedor_id:
                producto['seller_ids'] = [(0, 0, {
                    'name': proveedor_id,
                    'product_name': nombre_producto,
                    'product_code': producto.get('referencia_proveedor', ''),
                    'min_qty': 1.0,
                    'price': producto.get('standard_price', 0.0),
                })]
            
            # Crear o actualizar categoría si existe
            if 'categoria' in producto and producto['categoria']:
                try:
                    categoria_id = category_service.create_or_get_category(producto['categoria'])
                    if categoria_id:
                        producto['categ_id'] = categoria_id
                        logger.info(f"Categoría '{producto['categoria']}' encontrada/creada con ID: {categoria_id}")
                except Exception as e:
                    logger.error(f"Error al crear/obtener categoría '{producto.get('categoria')}': {str(e)}")
            
            # Intentar crear o actualizar el producto
            logger.info(f"Datos del producto a importar: {json.dumps(producto, indent=2, default=str)}")
            product_id, is_new = odoo_service.create_or_update_product(producto)
            
            if product_id:
                logger.info(f"✅ Producto {nombre_producto} {'creado' if is_new else 'actualizado'} con ID: {product_id}")
            else:
                logger.error(f"❌ Fallo al importar producto {nombre_producto}: ID nulo devuelto")
        
        except Exception as e:
            logger.error(f"❌ Error al importar producto {nombre_producto}: {str(e)}")

def main():
    """
    Función principal del script.
    """
    # Determinar la ruta del archivo Excel
    if len(sys.argv) > 1:
        excel_file = sys.argv[1]
    else:
        # Buscar la versión más reciente del Excel formateado
        base_path = os.path.dirname(os.path.abspath(__file__))
        excel_path = os.path.join(base_path, 'ejemplos/proveedores_exl_csv/PVP_NEVIR_FORMATEADO.xlsx')
        v2_path = os.path.join(base_path, 'ejemplos/proveedores_exl_csv/PVP_NEVIR_FORMATEADO_V2.xlsx')
        
        if os.path.exists(v2_path):
            excel_file = v2_path
            logger.info(f"Usando archivo Excel V2: {excel_file}")
        else:
            excel_file = excel_path
            logger.info(f"Usando archivo Excel: {excel_file}")
    
    # Cargar datos del Excel
    datos_proveedor, productos = cargar_excel(excel_file)
    logger.info(f"Datos del proveedor: {json.dumps(datos_proveedor, indent=2)}")
    logger.info(f"Se cargaron {len(productos)} productos del Excel")
    
    # Analizar productos
    analizar_productos(productos)
    
    # Probar importación directa
    probar_importacion_directa(productos)

if __name__ == "__main__":
    main()
