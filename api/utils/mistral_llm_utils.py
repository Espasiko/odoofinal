import json
import logging
import os
import httpx
from fastapi import HTTPException
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mistral").lower()

# Mistral
MISTRAL_API_URL = os.getenv("MISTRAL_API_URL", "https://api.mistral.ai/v1/chat/completions")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "mistral-large-latest")
# Groq (OpenAI-compatible)
GROQ_API_URL = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-70b-8192")
# OpenAI
OPENAI_API_URL = os.getenv("OPENAI_API_URL", "https://api.openai.com/v1/chat/completions")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

async def call_llm(prompt: str, provider: Optional[str] = None) -> Dict[str, Any]:
    """Realiza una petición a la IA indicada y devuelve la respuesta raw (json)."""
    prov = (provider or LLM_PROVIDER).lower()

    if prov == "mistral":
        url, key, model = MISTRAL_API_URL, MISTRAL_API_KEY, MISTRAL_MODEL
    elif prov == "groq":
        url, key, model = GROQ_API_URL, GROQ_API_KEY, GROQ_MODEL
    elif prov == "openai":
        url, key, model = OPENAI_API_URL, OPENAI_API_KEY, OPENAI_MODEL
    else:
        raise ValueError(f"Proveedor LLM no soportado: {prov}")

    if not key:
        raise ValueError(f"No hay API KEY para el proveedor {prov.upper()}")

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    system_json_prompt = (
        "Eres un asistente que devuelve EXCLUSIVAMENTE un objeto JSON válido sin texto extra. "
        "Escapa las comillas internas con \\\" y no incluyas bloques markdown. "
        "La clave raíz debe ser \"productos\"."
    )

    payload = {
        "model": model,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": system_json_prompt},
            {"role": "user", "content": prompt},
        ],
    }
    # response_format sólo para los LLM que lo soportan
    if prov in ("mistral", "openai"):
        payload["response_format"] = {"type": "json_object"}

    async with httpx.AsyncClient(timeout=120.0) as client:
        logger.info(f"[LLM] Enviando petición a {prov.upper()} (modelo {model})")
        try:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status == 429:
                logger.error("[LLM] Límite de peticiones alcanzado (429).")
                raise HTTPException(
                    status_code=503,
                    detail="El servicio de IA ha alcanzado el límite de peticiones. Intenta de nuevo en unos minutos."
                )
            logger.error(f"[LLM] Error HTTP {status}: {exc}")
            raise HTTPException(status_code=502, detail="Error al comunicarse con el servicio de IA")
        except httpx.RequestError as exc:
            logger.error(f"[LLM] Error de red: {exc}")
            raise HTTPException(status_code=502, detail="Error de red al comunicarse con el servicio de IA")

        body = resp.json()
        usage = body.get('usage')
        if usage:
            logger.info(f"[LLM] Tokens usados – prompt {usage.get('prompt_tokens')} + completion {usage.get('completion_tokens')} = {usage.get('total_tokens')}")
        logger.info("[LLM] Respuesta recibida correctamente")
        return body

def parse_mistral_response(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Analiza la respuesta JSON de la API de Mistral y extrae la lista de productos.
    """
    logger.debug(f"Recibida respuesta de Mistral para parsear: {response}")

    try:
        content_str = response['choices'][0]['message']['content']
        logger.debug(f"[LLM RAW FULL] {content_str}")
        logger.debug(f"[LLM RAW] {content_str[:500]}")
        import re, json as _json
        # Sanear posibles faltas de coma entre objetos dentro de la lista
        inner = content_str  # copia
        # unir objetos consecutivos "}{" -> "},{"
        inner = re.sub(r'}\s*{', '},{', inner)
        # Si el array "productos" no se cierra, ciérralo correctamente
        if '"productos"' in inner and not inner.rstrip().endswith(']}'):
            last_brace = inner.rfind('}')
            if last_brace != -1:
                inner = inner[:last_brace+1] + ']}'
        # Intentar cargar tras saneo
        try:
            data_saneada = _json.loads(inner)
            if isinstance(data_saneada, dict) and 'productos' in data_saneada:
                logger.info(f"Respuesta parseada tras saneo. {len(data_saneada['productos'])} productos.")
                return data_saneada['productos']
        except Exception as e:
            logger.debug(f"[SANITIZED FALLÓ] {e}. Intentaré con json5. Contenido: {inner[:500]}")
            try:
                import json5
                data_saneada = json5.loads(inner)
                if isinstance(data_saneada, dict) and 'productos' in data_saneada:
                    logger.info(f"Respuesta parseada con json5. {len(data_saneada['productos'])} productos.")
                    return data_saneada['productos']
            except Exception as e2:
                logger.debug(f"json5 también falló: {e2}")
        # Intentar extraer JSON puro incluso si viene rodeado de texto o bloque ```json
        if '```' in content_str:
            # Mantener sólo la parte dentro del último bloque ```json ... ``` o ``` ... ```
            parts = content_str.split('```')
            for part in parts:
                if part.strip().startswith('{'):
                    content_str = part.strip()
                    break
        else:
            # Recortar cualquier prefijo antes del primer '{' y sufijo después del último '}'
            first = content_str.find('{')
            last = content_str.rfind('}')
            if first != -1 and last != -1:
                content_str = content_str[first:last+1]
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
