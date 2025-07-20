# Guía de Uso de n8n-MCP con Cascade

## Introducción

Esta guía explica cómo utilizar n8n-MCP (Model Context Protocol) con Cascade para gestionar flujos de trabajo de n8n directamente desde el asistente de IA. Esta integración es especialmente útil para el proyecto Pelotazo ERP con Odoo 18, permitiendo automatizar la creación y modificación de flujos de trabajo para procesamiento OCR de facturas y análisis con LLM.

## Requisitos Previos

- Node.js y npm instalados
- n8n configurado y ejecutándose (en Docker o localmente)
- Windsurf/Cascade configurado
- API de n8n habilitada con token de acceso

## Configuración Inicial

1. **Ejecutar el script de configuración**

   ```bash
   cd /home/espasiko/mainmanusodoo/manusodoo-roto/n8n
   ./configurar_n8n_mcp.sh
   ```

   Este script:
   - Instala n8n-mcp globalmente
   - Configura el archivo `~/.codeium/windsurf/mcp_config.json`
   - Crea un archivo `.windsurfrules` en la raíz del proyecto
   - Utiliza las variables de entorno del archivo `.env`

2. **Verificar la configuración**

   Asegúrate de que las siguientes variables estén correctamente configuradas en el archivo `.env`:
   
   ```
   N8N_API_URL=http://n8n:5678/api/v1
   N8N_API_KEY=pelotazo-n8n-api-token-seguro-2025
   N8N_WEBHOOK_URL=http://n8n:5678
   ```

3. **Reiniciar Windsurf/Cascade**

   Cierra y vuelve a abrir Windsurf/Cascade para que cargue la nueva configuración de MCP.

## Uso de n8n-MCP con Cascade

### Comandos Básicos

Cuando interactúes con Cascade, puedes pedirle que realice acciones en n8n utilizando lenguaje natural. Algunos ejemplos:

- "Muéstrame los flujos de trabajo disponibles en n8n"
- "Crea un nuevo flujo de trabajo para procesar facturas NEVIR"
- "Modifica el flujo OCR mejorado para añadir validación de CIF"
- "Ejecuta el flujo de trabajo LLM-MCP con estos datos"
- "Explícame qué hace el nodo HTTP Request en n8n"

### Herramientas Disponibles

n8n-MCP proporciona varias herramientas que Cascade puede utilizar:

#### Herramientas de Documentación

- **n8n_get_node_types**: Obtener información sobre los tipos de nodos disponibles
- **n8n_get_node_description**: Obtener documentación detallada sobre un nodo específico
- **n8n_get_node_properties**: Obtener propiedades configurables de un nodo
- **n8n_search_nodes**: Buscar nodos por nombre o funcionalidad

#### Herramientas de Gestión de Flujos (requieren API configurada)

- **n8n_list_workflows**: Listar todos los flujos de trabajo
- **n8n_get_workflow**: Obtener detalles de un flujo específico
- **n8n_create_workflow**: Crear un nuevo flujo de trabajo
- **n8n_update_workflow**: Actualizar un flujo existente
- **n8n_delete_workflow**: Eliminar un flujo de trabajo
- **n8n_activate_workflow**: Activar un flujo de trabajo
- **n8n_deactivate_workflow**: Desactivar un flujo de trabajo

#### Herramientas de Ejecución

- **n8n_execute_workflow**: Ejecutar un flujo de trabajo
- **n8n_get_execution**: Obtener detalles de una ejecución
- **n8n_list_executions**: Listar ejecuciones de un flujo

### Ejemplos de Uso

#### Ejemplo 1: Crear un flujo de trabajo OCR para facturas NEVIR

```
Quiero crear un nuevo flujo de trabajo en n8n para procesar facturas de NEVIR con OCR. 
El flujo debe recibir un archivo PDF, extraer el texto con OCR, aplicar un prompt específico 
para NEVIR y devolver los datos estructurados.
```

#### Ejemplo 2: Modificar un flujo existente

```
Necesito modificar el flujo "procesar_factura_ocr_mejorado" para añadir validación de CIF/NIF 
español. Debe verificar que el CIF/NIF cumple con el algoritmo de validación español y 
devolver un error si no es válido.
```

#### Ejemplo 3: Ejecutar un flujo y ver resultados

```
Ejecuta el flujo LLM-MCP con estos datos:
{
  "invoice_text": "Factura NEVIR\nNúmero: NVR-12345\nFecha: 19/07/2025\nCIF: B84201219\nBase Imponible: 100€\nIVA (21%): 21€\nTotal: 121€",
  "supplier_name": "NEVIR"
}
```

## Flujos de Trabajo Específicos para Odoo 18

### 1. Flujo OCR Mejorado

Este flujo está diseñado específicamente para Odoo 18, teniendo en cuenta la estructura de tablas y campos de esta versión. Incluye:

- Extracción OCR de facturas
- Prompts específicos por proveedor
- Sistema de caché para evitar reprocesamiento
- Validación de datos extraídos
- Creación de facturas en Odoo 18

### 2. Flujo LLM-MCP

Este flujo utiliza modelos de lenguaje para:

- Analizar el contenido de facturas
- Validar datos con herramientas MCP
- Proporcionar recomendaciones
- Corregir errores comunes
- Integrar con Odoo 18 para verificar proveedores y productos

### 3. Servidor MCP

Expone herramientas especializadas para:

- Validación de CIF/NIF español
- Búsqueda de proveedores en Odoo 18
- Búsqueda de productos en Odoo 18
- Validación de facturas
- Detección de duplicados

## Solución de Problemas

### Error: No se puede conectar con el servidor MCP

1. Verifica que n8n-mcp esté instalado: `npm list -g n8n-mcp`
2. Comprueba la configuración en `~/.codeium/windsurf/mcp_config.json`
3. Reinicia Windsurf/Cascade

### Error: No se puede conectar con n8n

1. Verifica que n8n esté en ejecución: `docker-compose ps`
2. Comprueba las variables de entorno en `.env`
3. Verifica que la API de n8n esté habilitada en `docker-compose.yml`

### Error: Acceso denegado a la API de n8n

1. Verifica el token de API en `.env`
2. Comprueba que coincida con el configurado en `docker-compose.yml`

## Recursos Adicionales

- [Documentación oficial de n8n-MCP](https://github.com/czlonkowski/n8n-mcp)
- [Documentación de n8n](https://docs.n8n.io/)
- [Guía de API de Odoo 18](https://www.odoo.com/documentation/18.0/developer/api.html)

---

Documento creado: 19 de julio de 2025  
Última actualización: 19 de julio de 2025
