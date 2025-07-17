# Análisis de Logs y Fallos en Importación - 16/07/2025

## Fallos Identificados en la Importación de Excel

Tras analizar los logs de FastAPI, se han identificado los siguientes problemas en el proceso de importación de Excel:

### 1. Falta de Códigos de Referencia
```
WARNING:api.routes.excel_importer:Se encontraron 50 productos sin ID o referencia en el chunk actual
WARNING:api.routes.excel_importer:Lote 1: 50 de 50 productos sin ID
```
- **Problema**: Los productos importados no tienen `default_code` ni `barcode`, lo que impide su correcta identificación y actualización.
- **Impacto**: Esto causa la creación de duplicados en lugar de actualizar productos existentes.

### 2. Errores en la Búsqueda de Productos Existentes
```
WARNING:root:find_existing_product: No se proporcionó default_code ni barcode para buscar
```
- **Problema**: La función `find_existing_product` no puede localizar productos existentes sin un código de referencia.
- **Impacto**: Cada importación crea nuevos productos en lugar de actualizar los existentes.

### 3. Problemas en el Procesamiento LLM
```
WARNING:api.utils.mistral_llm_utils:[LLM] No se encontraron productos en el JSON
```
- **Problema**: El modelo LLM no está identificando correctamente los productos en el JSON proporcionado.
- **Impacto**: Fallos en la interpretación y normalización de datos antes de la importación.

## Estado de los Contenedores Docker

Todos los contenedores están funcionando correctamente:
- **FastAPI**: Servicio de backend (puerto 8000)
- **Odoo 18**: Servicio principal de Odoo (puerto 8069)
- **Adminer**: Gestor de base de datos (puerto 8080)
- **PostgreSQL**: Base de datos (puerto 5432)

## Recomendaciones Técnicas

### 1. Mejoras en la Importación de Excel
- **Validación previa**: Implementar validación de datos antes de procesar el chunk para asegurar que todos los productos tengan al menos un identificador único.
- **Normalización de códigos**: Añadir un paso de normalización para generar códigos de referencia basados en el nombre o características del producto cuando no existan.
- **Logging mejorado**: Ampliar el logging para incluir más detalles sobre los productos que fallan, incluyendo nombres y otros identificadores disponibles.

### 2. Optimización del Procesamiento LLM
- **Ajuste de prompts**: Revisar y optimizar los prompts utilizados para la extracción de productos del JSON.
- **Validación estructural**: Implementar validación de esquema JSON antes de procesar con LLM.
- **Fallback manual**: Añadir opción para revisión y corrección manual cuando el LLM no pueda identificar productos.

### 3. Mejoras en la Detección de Duplicados
- **Búsqueda multifactor**: Implementar búsqueda de productos existentes basada en múltiples factores (nombre, proveedor, categoría) cuando no exista código de referencia.
- **Fuzzy matching**: Añadir capacidad de coincidencia aproximada para nombres de productos similares.
- **Heurísticas de proveedor**: Utilizar información del proveedor para mejorar la detección de productos existentes.

## Próximos Pasos
1. Modificar `excel_importer.py` para mejorar la validación de datos antes de la importación.
2. Actualizar `mistral_llm_utils.py` para optimizar la extracción de productos del JSON.
3. Implementar un sistema de generación automática de códigos de referencia para productos sin identificador.
4. Añadir una interfaz de resolución manual de conflictos para productos sin identificación clara.
5. Mejorar la documentación del formato esperado de Excel para incluir requisitos de campos obligatorios.