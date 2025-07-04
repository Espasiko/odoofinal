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
# Usar solo MISTRAL_API_KEY para Mistral, no mezclar con otras claves
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "mistral-large-latest")

# Groq (OpenAI-compatible)
GROQ_API_URL = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")
GROQ_API_KEY = os.getenv("GROQ_API_KEY") or os.getenv("MISTRAL_LLM_API_KEY")  # Usar MISTRAL_LLM_API_KEY como fallback para Groq
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")  # Usar el modelo correcto para Groq

# OpenAI
OPENAI_API_URL = os.getenv("OPENAI_API_URL", "https://api.openai.com/v1/chat/completions")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

async def call_llm(prompt: str, provider: Optional[str] = None) -> Dict[str, Any]:
    """
    Realiza una petición a la IA indicada y devuelve la respuesta raw (json).
    Intenta con los proveedores configurados en orden de preferencia.
    """
    logger = logging.getLogger(__name__)
    prov = provider or LLM_PROVIDER
    providers = [prov]
    if prov != "groq":
        providers.append("groq")
    if prov != "openai" and "openai" not in providers:
        providers.append("openai")
    last_error = None

    for current_prov in providers:
        try:
            if current_prov == "mistral":
                url = MISTRAL_API_URL
                key = MISTRAL_API_KEY
                model = MISTRAL_MODEL
            elif current_prov == "groq":
                url = GROQ_API_URL
                key = GROQ_API_KEY
                model = GROQ_MODEL
                if "llama3-" in model:
                    model = model.replace("llama3-", "llama-3-")
                if model not in ["llama-3.1-8b-instant", "llama-3-70b", "llama-3-8b"]:
                    model = "llama-3.1-8b-instant"
            elif current_prov == "openai":
                url = OPENAI_API_URL
                key = OPENAI_API_KEY
                model = OPENAI_MODEL
            else:
                continue

            if not key:
                logger.warning(f"[LLM] Falta API KEY para {current_prov.upper()}. Probando siguiente proveedor.")
                continue

            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "system",
                        "content": "Eres un asistente que devuelve EXCLUSIVAMENTE un objeto JSON válido sin texto extra. Asegúrate de que tu respuesta sea un JSON válido con la estructura exacta que se te pide."
                    },
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
            }
            if current_prov in ("mistral", "openai"):
                payload["response_format"] = {"type": "json_object"}

            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code != 200:
                    logger.error(f"[LLM] Error HTTP {resp.status_code} de {current_prov.upper()}")
                    logger.error(f"[LLM] Respuesta de error: {resp.text[:500]}")
                    if resp.status_code in [401, 404, 429, 502, 503]:
                        last_error = f"Error {resp.status_code} con {current_prov}: {resp.text[:100]}"
                        continue
                    resp.raise_for_status()
                body = resp.json()
                logger.info(f"[LLM] Respuesta exitosa de {current_prov.upper()}")
                return body

        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            error_text = exc.response.text[:300]
            last_error = f"Error HTTP {status} con {current_prov}: {error_text[:100]}"
            logger.error(f"[LLM] {last_error}")
            continue
        except Exception as e:
            last_error = f"Error general con {current_prov}: {str(e)}"
            logger.error(f"[LLM] {last_error}")
            continue

    error_msg = last_error or "Todos los proveedores LLM fallaron por razones desconocidas"
    logger.error(f"[LLM] Fallo en todos los proveedores: {error_msg}")
    raise HTTPException(status_code=503, detail=f"No se pudo obtener respuesta de ningún proveedor LLM. {error_msg}")

def parse_mistral_response(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Parsea la respuesta de la API de Mistral/Groq/OpenAI y devuelve la lista de productos
    """
    logger.info(f"[LLM] Parseando respuesta: {str(response)[:200]}...")
    
    # Intentar extraer el contenido JSON del mensaje
    try:
        choices = response.get("choices", [])
        if not choices:
            logger.error("[LLM] No hay choices en la respuesta")
            return []
        
        message = choices[0].get("message", {})
        content = message.get("content", "")
        
        if not content:
            logger.error("[LLM] Contenido vacío en la respuesta")
            return []
        
        logger.info(f"[LLM] Contenido extraído: {content[:200]}...")
        
        # Parsear el JSON del contenido
        try:
            # A veces el modelo puede envolver el JSON en comillas o añadir texto adicional
            # Intentamos primero con el contenido tal cual
            data = json.loads(content)
            products = data.get("productos", [])
            if products:
                logger.info(f"[LLM] Productos encontrados: {len(products)}")
                return products
            else:
                logger.warning("[LLM] No se encontraron productos en el JSON")
                return []
        except json.JSONDecodeError as e:
            logger.error(f"[LLM] Error decodificando JSON: {e}")
            # Intentar extraer el JSON si está entre caracteres especiales
            import re
            json_pattern = r'(\{.*\})'
            match = re.search(json_pattern, content, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                    products = data.get("productos", [])
                    if products:
                        logger.info(f"[LLM] Productos encontrados después de regex: {len(products)}")
                        return products
                except:
                    pass
            logger.error(f"[LLM] No se pudo extraer JSON válido: {content[:500]}")
            return []
    except Exception as e:
        logger.error(f"[LLM] Error parseando respuesta: {e}")
        return []
