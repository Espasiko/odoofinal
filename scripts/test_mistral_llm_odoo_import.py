import sys
import os
import json

# Añadir la raíz del proyecto al PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.services.mistral_llm_odoo_mapper import merge_chunked_llm_jsons, map_llm_json_to_odoo

# Simula cargar los JSONs de respuesta de la LLM para varios chunks
chunk_files = [
    '/home/espasiko/mainmanusodoo/manusodoo-roto/static/uploads/mistral_chunk_1.json',
    '/home/espasiko/mainmanusodoo/manusodoo-roto/static/uploads/mistral_chunk_2.json'
]
json_chunks = []
for file in chunk_files:
    if os.path.exists(file):
        with open(file, 'r') as f:
            json_chunks.append(json.load(f))
    else:
        print(f"Archivo no encontrado: {file}")

if not json_chunks:
    print("No se encontraron chunks para importar. Asegúrate de tener los archivos JSON de la LLM.")
    sys.exit(1)

# Une todos los chunks en una sola estructura
merged = merge_chunked_llm_jsons(json_chunks)

# Si no hay proveedor en los chunks, pásalo aquí
fallback_supplier = "CECOTEC"

# Mapea y crea/actualiza productos en Odoo
try:
    codigos = map_llm_json_to_odoo(merged, fallback_supplier=fallback_supplier)
    print(f"Productos creados/actualizados: {codigos}")
except Exception as e:
    print(f"Error en la importación: {e}")
