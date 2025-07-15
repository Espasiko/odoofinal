#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para crear una plantilla Excel para importación de productos en Odoo 18
Fecha: 15/07/2025
"""

import pandas as pd
import os

# Crear directorio si no existe
os.makedirs('ejemplos/plantillas', exist_ok=True)

# Definir los campos necesarios para la plantilla
campos = [
    "nombre",                # Nombre del producto
    "referencia_proveedor",  # Referencia del proveedor
    "default_code",          # Código interno
    "barcode",               # Código de barras (como texto)
    "precio_venta",          # Precio de venta
    "precio_coste",          # Precio de coste
    "categoria",             # Categoría principal
    "subcategoria",          # Subcategoría
    "descripcion",           # Descripción del producto
    "stock_disponible",      # Stock disponible
    "proveedor"              # Nombre del proveedor
]

# Crear un ejemplo de producto
ejemplo = [
    "LAVADORA 8KG CON DISPLAY",         # nombre
    "NVR-WMFL1280INA-BC",              # referencia_proveedor
    "LAV-001",                         # default_code
    "8436589631254",                   # barcode (como texto)
    235.96,                            # precio_venta
    186.97,                            # precio_coste
    "LAVADORAS",                       # categoria
    "CARGA FRONTAL",                   # subcategoria
    "Lavadora de carga frontal con display digital", # descripcion
    10,                                # stock_disponible
    "NEVIR"                            # proveedor
]

# Crear DataFrame con los campos y el ejemplo
df = pd.DataFrame([ejemplo], columns=campos)

# Crear una segunda hoja con instrucciones
instrucciones = [
    ["INSTRUCCIONES PARA LA IMPORTACIÓN DE PRODUCTOS EN ODOO 18"],
    [""],
    ["1. Campos obligatorios:"],
    ["   - nombre: Nombre del producto"],
    ["   - Al menos uno de estos identificadores: referencia_proveedor, default_code o barcode"],
    [""],
    ["2. Campos recomendados:"],
    ["   - precio_venta: Precio de venta al público"],
    ["   - precio_coste: Precio de coste o compra"],
    ["   - categoria: Categoría principal del producto"],
    [""],
    ["3. Campos opcionales:"],
    ["   - subcategoria: Subcategoría del producto"],
    ["   - descripcion: Descripción detallada"],
    ["   - stock_disponible: Cantidad en stock"],
    ["   - proveedor: Nombre del proveedor"],
    [""],
    ["4. Notas importantes:"],
    ["   - El código de barras (barcode) debe ser una cadena de texto, no un número"],
    ["   - Si la categoría no existe, se creará automáticamente"],
    ["   - Si no se especifica categoría, se usará 'All' por defecto"],
    ["   - Los precios deben ser numéricos (sin símbolos de moneda)"],
    [""],
    ["5. Tipos de productos:"],
    ["   - Todos los productos se crean como tipo 'consu' (consumible)"],
    ["   - Para cambiar el tipo, edite el producto en Odoo después de importarlo"]
]

# Guardar el archivo Excel con dos hojas
with pd.ExcelWriter('ejemplos/plantillas/plantilla_productos_odoo18.xlsx', engine='openpyxl') as writer:
    df.to_excel(writer, sheet_name='Plantilla', index=False)
    
    # Crear hoja de instrucciones
    instrucciones_df = pd.DataFrame(instrucciones)
    instrucciones_df.to_excel(writer, sheet_name='Instrucciones', index=False, header=False)

print("Plantilla Excel creada con éxito en: ejemplos/plantillas/plantilla_productos_odoo18.xlsx")
