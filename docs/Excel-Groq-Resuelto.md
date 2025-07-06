# Excel-Groq Resuelto: Solución de Parseo JSON para Importación de Productos

**Fecha**: 01/07/2025

## Logros
- Se resolvió el problema persistente de parseo de JSON en las respuestas de Groq LLM durante la importación de productos desde archivos Excel en el sistema FastAPI-Odoo.
- Se lograron crear con éxito más de 200 productos en Odoo, incluyendo nombres, precios y otros datos relevantes extraídos de archivos Excel como 'PVP ALMCE.xlsx'.
- Los productos iniciales creados incluyen 'LAVADORA CORBERÓ 7KG "A"' (ID: 69) y 'LAVADORA CORBERÓ 9KG "A"' (ID: 70), confirmando que el flujo de datos desde el frontend React, pasando por FastAPI y Groq, hasta Odoo, funciona correctamente.

## Descripción del Problema
- Las respuestas de Groq LLM contenían JSON malformado, típicamente con comas faltantes entre objetos dentro de la lista 'productos' (por ejemplo, '}{ ' en lugar de '}, {').
- Esto causaba errores repetidos de 'json.JSONDecodeError: Expecting ',' delimiter' en el backend FastAPI, bloqueando la creación de productos.
- El error persistía a pesar de múltiples intentos de ajustar el system prompt para forzar un JSON válido y escapado.

## Pasos de Solución Implementados
1. **Diagnóstico Inicial**: Identificamos el error en los logs de FastAPI al intentar parsear la respuesta de Groq en 'parse_mistral_response' dentro de 'mistral_llm_utils.py'. El log mostraba 'Expecting ',' delimiter' en posiciones específicas, indicando comas faltantes.
2. **Sanitización Básica**: Se implementó una sustitución regex para insertar comas entre objetos consecutivos ('re.sub(r'}\s*{', '},{', inner)'). Esto no resolvió el problema completamente.
3. **Cierre de Estructuras**: Se añadió lógica para asegurar que el JSON terminara con ']}' si no lo hacía, intentando cerrar la lista 'productos' y el objeto raíz.
4. **Fallback con json5**: Se incorporó la librería 'json5' como fallback para parsear JSON no estándar (tolerante a comas faltantes y comentarios). Esto se intentó después de que el parseo estándar fallara.
5. **Corrección de Llaves**: Se ajustó la lógica para contar y cerrar llaves faltantes, y luego se refinó para buscar específicamente el último '}' y agregar ']}' si el array 'productos' no estaba cerrado.
6. **Log Detallado**: Finalmente, se añadió un log completo de la respuesta bruta de Groq ('[LLM RAW FULL]') para inspeccionar el contenido exacto y diseñar mejores reglas de sanitización.
7. **Iteraciones y Pruebas**: Después de cada cambio, se reinició el contenedor FastAPI con 'docker-compose restart fastapi' y se revisaron los logs para confirmar si el error persistía o si aparecían mensajes de éxito como 'Respuesta parseada tras saneo'.

## Resultado Final
- Después de varios ajustes en 'mistral_llm_utils.py', el sistema comenzó a parsear correctamente las respuestas de Groq, permitiendo la creación de productos en Odoo.
- La combinación de sanitización regex (inserción de comas), cierre forzado de estructuras JSON, y posiblemente el log detallado para depuración, contribuyó al éxito.
- Se confirmó la creación de más de 200 productos, validando la estabilidad del flujo de importación desde Excel a través de FastAPI y Groq hasta Odoo.

## Lecciones Aprendidas
- Las respuestas de LLMs como Groq pueden ser inconsistentes en formato JSON incluso con instrucciones estrictas en el system prompt. Es crucial implementar sanitización robusta en el backend.
- Logs detallados de contenido bruto son esenciales para diagnosticar problemas de parseo.
- Herramientas como 'json5' pueden ser útiles como fallback, aunque en este caso la solución final se basó más en ajustes manuales de la estructura.

## Próximos Pasos
- Monitorear la estabilidad del parseo con archivos Excel más grandes o con datos más complejos.
- Considerar reducir el tamaño de los chunks enviados a Groq para minimizar respuestas truncadas o malformadas.
- Evaluar otros proveedores de LLM (como Mistral o OpenAI) si Groq sigue presentando problemas intermitentes.

## Ubicación del Código
- Los cambios se realizaron principalmente en '/home/espasiko/mainmanusodoo/manusodoo-roto/api/utils/mistral_llm_utils.py', función 'parse_mistral_response'.
- El código actualizado se empujó a GitHub en la rama 'fastmal' con el commit 'Fix JSON parsing for Groq LLM responses in FastAPI'.
