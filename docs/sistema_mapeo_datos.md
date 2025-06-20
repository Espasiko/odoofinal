# Sistema de Mapeo de Datos de Proveedores a Odoo

## Descripción General
Este proyecto contiene un sistema para mapear datos de proveedores a un formato compatible con Odoo. El sistema incluye herramientas de línea de comandos y una interfaz web para facilitar la carga, análisis y conversión de datos.

## Componentes Principales

### 1. Aplicación Web (Flask)
- **Archivo Principal**: `app_mapeo.py`
- **Función**: Proporciona una interfaz web para subir archivos de proveedores, analizarlos y convertirlos a formato Odoo.
- **Ubicación**: `/home/espasiko/mainmanusodoo/manusodoo-roto/app_mapeo.py`
- **Puerto**: Se ejecuta en `http://localhost:5000`
- **Comando de Inicio**: `python3 /home/espasiko/mainmanusodoo/manusodoo-roto/app_mapeo.py`

### 2. Script de Mapeo con IA
- **Archivo**: `ia_mapeo.py`
- **Función**: Utiliza técnicas de procesamiento de lenguaje natural para detectar categorías, normalizar nombres de productos y sugerir correcciones.
- **Ubicación**: `/home/espasiko/mainmanusodoo/manusodoo-roto/ia_mapeo.py`

### 3. Convertidor de Proveedores
- **Archivo**: `convertidor_proveedores.py`
- **Función**: Contiene funciones para leer archivos de diferentes proveedores y generar plantillas de productos para Odoo.

### 4. Directorios Importantes
- **Ejemplos**: `/home/espasiko/mainmanusodoo/manusodoo-roto/ejemplos` - Contiene archivos de ejemplo de proveedores.
- **Salida para Odoo**: `/home/espasiko/mainmanusodoo/manusodoo-roto/odoo_import` - Donde se guardan los archivos convertidos listos para importar a Odoo.
- **Plantillas Web**: `/home/espasiko/mainmanusodoo/manusodoo-roto/templates` - Plantillas HTML para la interfaz web.

## Instrucciones de Uso
1. **Iniciar la Aplicación Web**: Ejecuta `python3 app_mapeo.py` desde el directorio del proyecto.
2. **Acceder a la Interfaz**: Abre un navegador y ve a `http://localhost:5000`.
3. **Subir Archivos**: Usa la interfaz para subir archivos de proveedores y analizarlos.
4. **Revisar Resultados**: Los resultados y archivos convertidos se guardarán en el directorio de salida.

## Notas
- Asegúrate de tener instaladas todas las dependencias necesarias antes de ejecutar la aplicación. Puedes encontrarlas en `requirements.txt`.
- Si el servidor no está corriendo, no podrás acceder a la interfaz web. Asegúrate de iniciarlo primero.
