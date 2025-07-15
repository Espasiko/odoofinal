#!/usr/bin/env python3
"""
Script para probar el flujo completo de importación de Excel a Odoo.
Este script verifica:
1. El mecanismo de fallback de Mistral a Groq
2. La correcta interpretación de los datos del Excel
3. La creación/actualización de productos en Odoo
"""
import asyncio
import logging
import json
import os
import sys
from typing import Dict, Any, List

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('test_excel_import.log')
    ]
)
logger = logging.getLogger("test_excel_import")

# Importar las funciones necesarias
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from api.utils.mistral_llm_utils import call_llm, parse_mistral_response
from api.services.odoo_product_service import OdooProductService

# Datos de ejemplo para simular un Excel preprocesado
SAMPLE_DATA = {
    "headers": ["REFERENCIA", "DESCRIPCIÓN", "PRECIO COSTE", "PRECIO VENTA", "CATEGORÍA"],
    "rows": [
        ["REF001", "Producto de prueba 1", "10.50", "19.99", "Electrónica"],
        ["REF002", "Producto de prueba 2", "5.25", "12.50", "Hogar"],
        ["REF003", "Producto de prueba 3", "15.75", "29.99", "Electrónica"]
    ]
}

async def test_llm_fallback():
    """Prueba el mecanismo de fallback de Mistral a Groq"""
    logger.info("=== PRUEBA DE FALLBACK LLM ===")
    
    # Crear un prompt que simule la interpretación de datos de Excel
    prompt = f"""
    Analiza los siguientes datos de un Excel y extrae la información de productos:
    
    {json.dumps(SAMPLE_DATA, indent=2)}
    
    Extrae la siguiente información para cada producto:
    - nombre: El nombre del producto.
    - referencia_proveedor: El código o referencia único del producto.
    - precio_venta: El precio de venta al público.
    - precio_coste: El precio de compra o coste.
    - categoria: La categoría principal del producto.
    
    Devuelve el resultado como un array de objetos JSON válido contenido dentro de un objeto JSON principal con la clave 'productos'.
    """
    
    try:
        # Llamar a la función que maneja el fallback
        logger.info("Llamando a LLM con fallback configurado...")
        response = await call_llm(prompt)
        
        if response:
            logger.info(f"Respuesta recibida del LLM: {json.dumps(response)[:200]}...")
            
            # Verificar qué proveedor respondió
            if "model" in response:
                model = response.get("model", "desconocido")
                logger.info(f"Modelo utilizado: {model}")
                if "mistral" in model.lower():
                    logger.info("✅ Respuesta recibida de Mistral")
                elif "llama" in model.lower():
                    logger.info("✅ Fallback a Groq funcionó correctamente")
                else:
                    logger.info(f"✅ Respuesta recibida de otro modelo: {model}")
            
            # Parsear la respuesta
            products = parse_mistral_response(response)
            logger.info(f"Productos extraídos: {len(products)}")
            logger.info(f"Primer producto: {json.dumps(products[0], indent=2) if products else 'Ninguno'}")
            
            return products
        else:
            logger.error("❌ No se recibió respuesta del LLM")
            return []
    except Exception as e:
        logger.error(f"❌ Error al llamar al LLM: {str(e)}")
        return []

async def test_product_creation(products: List[Dict[str, Any]]):
    """Prueba la creación/actualización de productos en Odoo"""
    logger.info("=== PRUEBA DE CREACIÓN DE PRODUCTOS ===")
    
    if not products:
        logger.error("❌ No hay productos para crear")
        return
    
    odoo_service = OdooProductService()
    productos_creados = 0
    productos_actualizados = 0
    productos_fallidos = 0
    
    for producto in products:
        try:
            # Asegurar que el campo 'name' esté presente
            if 'nombre' in producto and not producto.get('name'):
                producto['name'] = producto['nombre']
            
            # Asegurar que el tipo sea 'consu' para productos físicos en Odoo 18
            producto['type'] = 'consu'
            
            # Verificar y convertir precios
            if 'precio_venta' in producto and producto['precio_venta']:
                try:
                    producto['list_price'] = float(producto['precio_venta'])
                except (ValueError, TypeError):
                    pass
            
            if 'precio_coste' in producto and producto['precio_coste']:
                try:
                    producto['standard_price'] = float(producto['precio_coste'])
                except (ValueError, TypeError):
                    pass
            
            logger.info(f"Enviando producto a Odoo: {producto}")
            product_id, is_new = odoo_service.create_or_update_product(producto)
            
            if product_id:
                if is_new:
                    productos_creados += 1
                    logger.info(f"✅ Producto creado con ID: {product_id}")
                else:
                    productos_actualizados += 1
                    logger.info(f"✅ Producto actualizado con ID: {product_id}")
            else:
                productos_fallidos += 1
                logger.error(f"❌ Fallo al crear/actualizar producto: {producto.get('name', 'Sin nombre')}")
        except Exception as e:
            productos_fallidos += 1
            logger.error(f"❌ Error al procesar producto: {str(e)}")
    
    logger.info(f"Resumen: {productos_creados} creados, {productos_actualizados} actualizados, {productos_fallidos} fallidos")

async def main():
    """Función principal que ejecuta todas las pruebas"""
    logger.info("Iniciando pruebas de importación de Excel")
    
    # Configurar la URL de Odoo para pruebas locales
    from api.utils.config import config
    config.set_odoo_config({
        "url": "http://localhost:8069",
        "db": "fresh_odoo_db",
        "username": "admin",
        "password": "admin"
    })
    logger.info(f"Configuración de Odoo establecida: URL=http://localhost:8069")
    
    # Probar el fallback de LLM
    products = await test_llm_fallback()
    
    # Probar la creación de productos
    if products:
        await test_product_creation(products)
    
    logger.info("Pruebas completadas")

if __name__ == "__main__":
    asyncio.run(main())
