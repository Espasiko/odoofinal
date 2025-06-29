import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def parse_mistral_response(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Analiza la respuesta JSON de la API de Mistral y extrae la lista de productos.
    Maneja el caso donde el contenido es una cadena JSON que necesita ser parseada.

    Args:
        response: El diccionario de respuesta de la API de Mistral.

    Returns:
        Una lista de diccionarios, donde cada diccionario representa un producto.
        Retorna una lista vacía si no se pueden extraer productos.
    """
    productos = []
    content_str = ""
    try:
        # La respuesta útil está en 'choices'[0]['message']['content']
        content_str = response.get('choices', [{}])[0].get('message', {}).get('content', '{}')

        # A veces, el 'content' es una cadena JSON que necesita ser parseada de nuevo.
        data = json.loads(content_str)

        # Extraer la lista de productos de la clave 'productos'
        if isinstance(data, dict) and 'productos' in data:
            productos = data.get('productos', [])
        elif isinstance(data, list):
            # Si la respuesta es directamente una lista de productos
            productos = data
        else:
            logger.warning("La respuesta JSON de Mistral no tiene el formato esperado (clave 'productos' no encontrada).")
            return []

        if not isinstance(productos, list):
            logger.warning(f"Se esperaba una lista de productos, pero se obtuvo: {type(productos)}")
            return []

        return productos

    except json.JSONDecodeError as e:
        logger.error(f"Error al decodificar la respuesta JSON de Mistral: {e}")
        logger.error(f"Contenido problemático: {content_str}")
        return []
    except (KeyError, IndexError, TypeError) as e:
        logger.error(f"Error al acceder a claves en la respuesta de Mistral: {e}")
        logger.error(f"Respuesta recibida: {response}")
        return []
    except Exception as e:
        logger.error(f"Error inesperado al parsear la respuesta de Mistral: {e}")
        return []
