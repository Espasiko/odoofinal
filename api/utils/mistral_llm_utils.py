import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def parse_mistral_response(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Analiza la respuesta JSON de la API de Mistral y extrae la lista de productos.
    """
    logger.debug(f"Recibida respuesta de Mistral para parsear: {response_data}")

    try:
        content_str = response_data['choices'][0]['message']['content']
        data = json.loads(content_str)

        if isinstance(data, dict) and 'productos' in data:
            productos = data['productos']
            if isinstance(productos, list):
                logger.info(f"Respuesta parseada con éxito. {len(productos)} productos encontrados en la clave 'productos'.")
                return productos
            else:
                logger.error(f"La clave 'productos' no contiene una lista. Contenido: {productos}")
                return []
        else:
            logger.error(f"La respuesta de la IA no es un diccionario o no contiene la clave 'productos'. Respuesta: {data}")
            return []

    except (KeyError, IndexError) as e:
        logger.error(f"Error de estructura en la respuesta de Mistral: {e}. Respuesta completa: {response_data}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Error al decodificar el JSON de la respuesta de Mistral: {e}. Contenido: {content_str}")
        return []
    except Exception as e:
        logger.error(f"Error inesperado al parsear la respuesta de Mistral: {e}. Respuesta: {response_data}")
        return []
