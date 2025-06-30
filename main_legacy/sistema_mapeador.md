# Sistema Mapeador de Productos

## Arquitectura del Sistema

El sistema de mapeo de productos se ha desarrollado como una solución para integrar datos de diferentes proveedores en un formato estandarizado para Odoo. La arquitectura se compone de los siguientes componentes principales:

### 1. Interfaz Web (app_mapeo.py)
- Servidor Flask que proporciona una interfaz web para la carga de archivos
- Manejo de subida de archivos y procesamiento asíncrono
- Visualización de resultados y descarga de archivos procesados

### 2. Motor de Procesamiento (convertidor_proveedores.py)
- Sistema de detección automática de proveedores basado en patrones de nombres de archivo
- Procesadores específicos para cada proveedor (ALMCE, BSH, CECOTEC)
- Normalización de datos y mapeo a formato estándar

## Logros Alcanzados

1. **Detección Automática de Proveedores**
   - Implementación de sistema de patrones para identificar proveedores
   - Soporte para múltiples formatos de nombre de archivo

2. **Procesamiento de Archivos**
   - Lectura de archivos CSV y Excel
   - Normalización de nombres de columnas
   - Mapeo de datos a estructura Odoo

3. **Integración con Odoo**
   - Generación de archivos JSON compatibles
   - Mapeo de categorías de productos
   - Gestión de datos de proveedores

## Estado Actual

- El sistema procesa correctamente archivos de CECOTEC con algunas discrepancias en campos específicos
- Se requiere ajuste en el procesamiento de archivos BSH para el campo 'CÓDIGO'
- Pendiente: Configuración de categorías de productos en Odoo

## Próximos Pasos

1. Mejorar el mapeo de categorías de productos
2. Optimizar la detección de campos en archivos BSH
3. Implementar validación adicional de datos
4. Expandir soporte para más proveedores