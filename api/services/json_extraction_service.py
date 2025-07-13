"""
Servicio para extraer datos JSON de texto
"""
import json
import re
import logging

logger = logging.getLogger(__name__)

def extract_json_from_text(text: str) -> dict:
    """
    Extrae objeto JSON de un texto, maneja casos donde el JSON está embebido en markdown
    
    Args:
        text: Texto que puede contener JSON
        
    Returns:
        dict: Objeto JSON extraído o diccionario vacío si no se encuentra
    """
    try:
        # Intentar encontrar JSON en el texto usando regex
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if json_match:
            json_str = json_match.group(1)
            return json.loads(json_str)
        
        # Si no hay bloques de código, intentar parsear todo el texto como JSON
        try:
            return json.loads(text)
        except:
            pass
        
        # Intentar encontrar el primer { y último } para extraer JSON
        start = text.find('{')
        end = text.rfind('}')
        if start >= 0 and end > start:
            json_str = text[start:end+1]
            return json.loads(json_str)
            
        return {}
    except Exception as e:
        logger.error(f"Error extrayendo JSON de texto: {str(e)}")
        return {}
