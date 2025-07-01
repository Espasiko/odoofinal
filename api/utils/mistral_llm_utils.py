import json
import logging
import os
import httpx
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Cargar configuración de la API de Mistral desde variables de entorno
MISTRAL_API_URL = os.getenv("MISTRAL_API_URL")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL")

async def call_mistral_api(prompt: str) -> Dict[str, Any]:
    """
    Llama a la API de Mistral con un prompt y devuelve la respuesta JSON.
    """
    if not all([MISTRAL_API_URL, MISTRAL_API_KEY, MISTRAL_MODEL]):
        logger.error("Faltan variables de entorno de Mistral (URL, KEY o MODEL).")
        raise ValueError("Configuración de la API de Mistral incompleta.")

    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MISTRAL_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
    }

    async with httpx.AsyncClient(timeout=300.0) as client:
        logger.info(f"Enviando petición a Mistral API. Modelo: {MISTRAL_MODEL}")
        response = await client.post(MISTRAL_API_URL, json=payload, headers=headers)
        response.raise_for_status()  # Lanza una excepción para respuestas 4xx/5xx
        logger.info("Respuesta recibida de Mistral API.")
        return response.json()

def parse_mistral_response(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Analiza la respuesta JSON de la API de Mistral y extrae la lista de productos.
    """
    logger.debug(f"Recibida respuesta de Mistral para parsear: {response}")

    try:
        content_str = response['choices'][0]['message']['content']
        data = json.loads(content_str)

        if isinstance(data, dict) and 'productos' in data:
            productos = data['productos']
            if isinstance(productos, list):
                logger.info(f"Respuesta parseada con éxito. {len(productos)} productos encontrados.")
                return productos
            else:
                logger.error(f"La clave 'productos' no contiene una lista. Contenido: {productos}")
                return []
        else:
            logger.error(f"La respuesta de la IA no es un diccionario o no contiene la clave 'productos'. Respuesta: {data}")
            return []

    except (KeyError, IndexError) as e:
        logger.error(f"Error de estructura en la respuesta de Mistral: {e}. Respuesta completa: {response}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Error al decodificar el JSON de la respuesta de Mistral: {e}. Contenido: {content_str}")
        return []
    except Exception as e:
        logger.error(f"Error inesperado al parsear la respuesta de Mistral: {e}. Respuesta: {response}")
        return []
