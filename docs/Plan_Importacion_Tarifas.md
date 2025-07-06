# Plan Estratégico para la Importación de Tarifas de Proveedores (Versión Final)

## 1. El Problema: La Complejidad Variable

La importación de tarifas de proveedores a través de archivos Excel presenta un desafío significativo debido a la **alta variabilidad y falta de estandarización** entre los formatos. Un enfoque de desarrollo rígido está destinado al fracaso.

El objetivo es diseñar y construir un **sistema de importación robusto, escalable e inteligente** que pueda adaptarse a los "dialectos" de cada proveedor, normalizar sus datos y cargarlos de forma consistente en Odoo.

## 2. Problemas Identificados en el Sistema Actual

1. **No se detecta el proveedor en la subida de Excel**:
   - El proveedor (por ejemplo, Cecotec) no se está detectando desde el frontend ni se crea en Odoo 18 durante la importación.
   - Esto podría deberse a que el campo del proveedor no se está pasando correctamente desde el frontend al backend, o que el backend no está procesando/creando el proveedor en Odoo.

2. **Productos sin precio en el frontend y sin actualización al editar**:
   - Los productos aparecen sin precio en el frontend, lo que indica que el dato del precio podría no estar llegando desde Odoo al frontend.
   - Al editar, los cambios no se reflejan, sugiriendo un problema en la sincronización o en la API de actualización entre frontend y backend.

3. **No se detectan todos los productos en el Excel de Nevir**:
   - Solo se crean 3 de 5 productos al subir el archivo de Nevir, lo que podría indicar que Groq LLM no está extrayendo todos los productos del Excel o que el parseo de la respuesta no incluye todos los elementos.

4. **Falta de sección de búsqueda y filtros en el frontend**:
   - Necesitas una sección en `/src` (página de productos) para buscar por nombre, proveedor, número de producto y aplicar filtros por precio, categoría, proveedor, margen, etc.
   - Esto es esencial para cruzar datos y verificar la información subida.

## 3. Plan de Acción para Investigación y Solución

### 3.1 Problema de Detección y Creación de Proveedores
   - **Paso 1: Revisar el Frontend**:
     - Verificar en `src/ImportExcelChunk.tsx` si el campo de proveedor (casilla en la página de importar Excel) está correctamente capturando y enviando el valor al backend mediante la petición POST a `/api/v1/mistral-llm/process-excel`.
     - Comprobar si el valor del proveedor se incluye en el payload de la petición (por ejemplo, como `proveedor_nombre`).
   - **Paso 2: Revisar el Backend**:
     - Inspeccionar `api/routes/mistral_llm_excel.py` para confirmar si el endpoint recibe el nombre del proveedor y lo pasa al servicio correspondiente.
     - Verificar en `api/services/odoo_product_service.py` si hay lógica para crear un proveedor en Odoo si no existe (usando `res.partner` con `is_company=True` y `supplier=True`).
   - **Paso 3: Logs y Depuración**:
     - Revisar los logs de FastAPI durante una subida para ver si el proveedor se recibe y procesa.
     - Si no hay creación de proveedor, determinar si es un fallo de lógica o de conexión con Odoo.

### 3.2 Problema de Precios y Actualización en el Frontend
   - **Paso 1: Verificar Datos en Odoo**:
     - Acceder a Odoo (http://localhost:8069) y comprobar manualmente algunos productos subidos para confirmar que tienen precios (`list_price` para venta y `standard_price` para coste).
   - **Paso 2: Revisar API de Lectura**:
     - Inspeccionar el endpoint de FastAPI que devuelve productos al frontend (probablemente en `api/routes/product.py` o similar) para asegurar que los campos de precio se incluyen en la respuesta.
   - **Paso 3: Revisar Frontend**:
     - En el componente de productos del frontend (probable en `/src`), verificar si los campos de precio se están renderizando correctamente desde los datos recibidos.
   - **Paso 4: Actualización al Editar**:
     - Comprobar si el frontend envía correctamente los datos editados al backend y si el endpoint de actualización en FastAPI está funcionando (probablemente un `PUT` o `PATCH` a `/api/v1/products/{id}`).
     - Revisar logs para detectar errores durante la actualización.

### 3.3 Problema de Detección de Productos en Excel de Nevir
   - **Paso 1: Inspeccionar el Archivo Excel**:
     - Abrir el archivo de Nevir para confirmar que contiene 5 productos claramente identificables en las filas.
   - **Paso 2: Revisar Respuesta de Groq**:
     - Revisar los logs de FastAPI, específicamente el `[LLM RAW FULL]` durante la subida de Nevir, para ver si Groq devuelve solo 3 productos o si devuelve más pero el parseo los pierde.
   - **Paso 3: Ajustar Prompt o Chunks**:
     - Si Groq no devuelve todos los productos, considerar ajustar el system prompt en `mistral_llm_utils.py` para enfatizar que debe extraer **todos** los productos del texto.
     - Evaluar reducir el tamaño de los chunks de datos enviados a Groq (en `api/routes/mistral_llm_excel.py`) para evitar truncamiento de respuestas.
   - **Paso 4: Parseo**:
     - Si Groq devuelve más de 3 productos pero solo se crean 3, inspeccionar `parse_mistral_response` para asegurar que no se pierden elementos durante la sanitización del JSON.

### 3.4 Sección de Búsqueda y Filtros en el Frontend
   - **Paso 1: Plan de Diseño**:
     - Identificar el componente de la página de productos en `/src` (probablemente algo como `ProductList.tsx` o similar).
     - Diseñar una sección superior con un campo de búsqueda por texto (nombre, número de producto) y dropdowns o checkboxes para filtros (proveedor, categoría, rango de precio, margen).
   - **Paso 2: Backend para Soporte de Filtros**:
     - Confirmar que los endpoints de FastAPI para listar productos permiten parámetros de búsqueda y filtrado (por ejemplo, `GET /api/v1/products?search=term&category=cat&min_price=10&max_price=100`).
   - **Paso 3: Implementación Futura**:
     - Priorizar este desarrollo como una mejora de UX para facilitar la verificación de datos subidos.

### 3.5 Plan General de Verificación de Datos Subidos
   - **Paso 1: Verificación en Odoo**:
     - Acceder a Odoo y listar productos (`Productos > Productos`) para confirmar cuántos se han creado, sus precios, proveedores asociados, categorías, etc.
     - Comprobar la tabla de proveedores (`Contactos`) para ver si Cecotec y otros se han creado correctamente.
   - **Paso 2: Campos Faltantes en Odoo**:
     - Revisar el modelo de producto en Odoo 18 (`product.template` y `product.product`) para identificar campos obligatorios o relevantes que no se estén llenando desde el JSON de Groq (por ejemplo, `default_code`, `barcode`, `uom_id`, etc.).
     - Hacer lo mismo con proveedores (`res.partner`): verificar campos como `vat`, `phone`, `email`, etc., que podrían estar vacíos.
   - **Paso 3: Cruzar Datos**:
     - Exportar un CSV desde Odoo con los productos y proveedores para compararlo con los Excels originales y detectar discrepancias (por ejemplo, productos faltantes o datos incorrectos).
   - **Paso 4: Logs de FastAPI**:
     - Revisar logs durante las subidas para detectar errores silenciosos o advertencias que indiquen pérdida de datos.
   - **Paso 5: Tablas Relevantes en Odoo**:
     - `product.template`: Plantilla base de productos (nombre, categoría, precios, etc.).
     - `product.product`: Variantes de productos (si aplica).
     - `res.partner`: Proveedores y clientes (campos de contacto y tipo de relación).
     - `product.category`: Categorías de productos (para asignar correctamente desde el JSON).
     - Confirmar que los datos subidos están en estas tablas y detectar campos vacíos que deberían llenarse.

## 4. Herramientas y Recursos para la Implementación
   - **MCP Postgres (Solo Lectura)**: Se utilizará MCP Postgres para realizar consultas de solo lectura en la base de datos de Odoo. Esto permitirá verificar los datos subidos (productos, proveedores, categorías, etc.) directamente en las tablas relevantes como `product.template`, `res.partner`, y `product.category`, asegurando que la información esté correctamente almacenada y detectando campos faltantes o errores sin riesgo de modificar datos.
   - **MCP Excel**: Este recurso se empleará para consultar y analizar la información original contenida en los archivos Excel de los proveedores. MCP Excel facilitará la comparación entre los datos fuente y los datos procesados por el backend, ayudando a identificar discrepancias o productos no detectados durante la extracción por Groq LLM.
   - **Bibliotecas de Pruebas en Python**: Se han descargado bibliotecas de pruebas de Python (como `pytest`, `unittest`, o similares) para testear exhaustivamente cada componente del sistema de importación antes de confirmar los cambios e ir a despliegue. Estas pruebas automatizadas cubrirán desde el parseo de JSON hasta la creación de productos y proveedores en Odoo, garantizando la estabilidad y precisión del flujo de datos.

## 5. Futuras Mejoras: Containerización del Frontend
   - **Containerización del Frontend React**: Aún falta containerizar el frontend React para asegurar un despliegue consistente y portátil del sistema completo. En la raíz del proyecto se encuentra un archivo `Dockerfile.frontend` que está bien estructurado para construir y servir la aplicación React usando `node:20-alpine` para el build y `nginx:alpine` como servidor. También hay un archivo `docker-compose.yml` parcialmente preparado pero no funcional todavía.
   - **Pasos Pendientes**:
     - Añadir un servicio para el frontend en `docker-compose.yml`, utilizando `Dockerfile.frontend` como base.
     - Configurar puertos (por ejemplo, mapear `3001:80` para que el frontend sea accesible en `http://localhost:3001`).
     - Asegurar que el frontend pueda comunicarse con el backend FastAPI dentro de la red Docker.
   - **Prioridad**: Este paso se realizará una vez que se resuelvan los problemas actuales relacionados con la importación de datos y la sincronización entre frontend y backend, para no olvidar integrarlo como parte del entorno Docker unificado.

## 6. Próximos Pasos Inmediatos
1. Revisar los logs de la subida de Nevir para entender por qué solo se detectaron 3 de 5 productos (buscar `[LLM RAW FULL]` en los logs de FastAPI).
2. Hacer una prueba manual en Odoo para confirmar qué datos se han subido (proveedores, productos, precios).
3. Inspeccionar el payload enviado desde el frontend durante la importación para verificar si el proveedor (Cecotec) se incluye.
4. Planificar la implementación de la sección de búsqueda y filtros en el frontend como una prioridad para facilitar la verificación de datos.
