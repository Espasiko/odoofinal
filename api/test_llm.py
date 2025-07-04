#!/usr/bin/env python3
"""
Script de prueba para verificar la integración con LLM
Ejecutar desde la raíz del proyecto con: python -m api.test_llm
"""

import asyncio
import logging
import os
import sys
import json
from dotenv import load_dotenv

# Configurar logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Asegurar que podemos importar desde el directorio api
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Cargar variables de entorno
load_dotenv()

async def test_llm_integration():
    """Prueba la integración con diferentes proveedores LLM"""
    from api.utils.mistral_llm_utils import call_llm
    from api.utils.config import config
    
    # Mostrar configuración actual
    logger.info(f"Proveedor LLM configurado: {config.LLM_PROVIDER}")
    logger.info(f"URL Mistral: {config.MISTRAL_API_URL}")
    logger.info(f"URL Groq: {config.GROQ_API_URL}")
    
    # Depuración de variables de entorno
    logger.info(f"Variable de entorno GROQ_MODEL: {os.getenv('GROQ_MODEL')}")
    logger.info(f"Valor de config.GROQ_MODEL: {config.GROQ_MODEL}")
    from api.utils.mistral_llm_utils import GROQ_MODEL
    logger.info(f"Valor de mistral_llm_utils.GROQ_MODEL: {GROQ_MODEL}")
    
    # Prompt simple para prueba
    prompt = """
    Por favor, genera un objeto JSON con la siguiente estructura:
    {
        "nombre": "Producto de prueba",
        "precio": 99.99,
        "descripcion": "Este es un producto de prueba para verificar la integración LLM",
        "categoria": "Test",
        "disponible": true
    }
    """
    
    # Probar con el proveedor configurado por defecto
    try:
        logger.info(f"Probando con proveedor por defecto ({config.LLM_PROVIDER})...")
        result = await call_llm(prompt)
        logger.info("✅ Llamada exitosa al proveedor por defecto")
        logger.info(f"Modelo usado: {result.get('model', 'desconocido')}")
        
        # Extraer y mostrar el contenido JSON
        if 'choices' in result and len(result['choices']) > 0:
            content = result['choices'][0]['message']['content']
            try:
                json_content = json.loads(content)
                logger.info(f"JSON válido recibido: {json.dumps(json_content, indent=2, ensure_ascii=False)}")
            except json.JSONDecodeError:
                logger.warning(f"Contenido no es JSON válido: {content[:100]}...")
        else:
            logger.warning(f"Formato de respuesta inesperado: {result}")
    except Exception as e:
        logger.error(f"❌ Error con proveedor por defecto: {str(e)}")
    
    # Probar con Mistral explícitamente
    try:
        logger.info("Probando con Mistral explícitamente...")
        result = await call_llm(prompt, provider="mistral")
        logger.info("✅ Llamada exitosa a Mistral")
        logger.info(f"Modelo usado: {result.get('model', 'desconocido')}")
    except Exception as e:
        logger.error(f"❌ Error con Mistral: {str(e)}")
    
    # Probar con Groq explícitamente
    try:
        logger.info("Probando con Groq explícitamente...")
        # Usar directamente call_llm con el proveedor groq
        # La corrección del modelo se hace internamente en mistral_llm_utils.py
        from api.utils.mistral_llm_utils import call_llm
        result = await call_llm(prompt, provider="groq")
        logger.info("✅ Llamada exitosa a Groq")
        logger.info(f"Modelo usado: {result.get('model', 'desconocido')}")
    except Exception as e:
        logger.error(f"❌ Error con Groq: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_llm_integration())
