import requests

API_URL = "https://api.mistral.ai/v1/chat/completions"
API_KEY = "zrJPQKEI6yJ7cIHloQOymRVNzZaYNDs4"

with open("/home/espasiko/mainmanusodoo/manusodoo-roto/ejemplos/proveedores_exl_csv/PVP_CECOTEC_fulltext.txt", "r", encoding="utf-8") as f:
    excel_text = f.read()

prompt = f"""
Procesa toda la información contenida en el siguiente archivo Excel de proveedor.\nEl archivo contiene varias hojas (productos, ventas, devoluciones, notas, etc.).\nExtrae y estructura en un JSON toda la información útil para la gestión del negocio, incluyendo pero no limitado a:\n\n- Datos del proveedor (si aparecen)\n- Listado de productos, con todos sus campos (código, nombre, descripción, unidades, precios, márgenes, stock, etc.)\n- Ventas, devoluciones, notas, históricos, totales, etc., asociando cada dato a su producto si es posible\n- Cualquier otra información relevante para compras, inventario, contabilidad o análisis\n\nEl texto de cada hoja empieza con '--- HOJA: <nombre> ---'.\nReconoce el contexto de cada hoja y los campos de cada columna, aunque los encabezados cambien o haya celdas vacías.\n\nDevuélveme el resultado en un JSON estructurado por secciones (ejemplo: 'productos', 'ventas', 'devoluciones', 'notas', 'totales', 'otros').\n\nAquí tienes el contenido del archivo:\n\n""" + excel_text

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

data = {
    "model": "mistral-large-latest",
    "messages": [
        {"role": "user", "content": prompt}
    ],
    "temperature": 0.1,
    "max_tokens": 4096
}

response = requests.post(API_URL, json=data, headers=headers)
print(response.status_code)
print(response.json())
