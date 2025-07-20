# Guía de Integración de MCP Client con LLM en n8n

## Introducción

Esta guía explica cómo configurar y utilizar el nodo MCP Client (Model Context Protocol) en n8n para integrar modelos de lenguaje (LLM) con los flujos de trabajo de procesamiento de facturas en el proyecto Pelotazo ERP.

El protocolo MCP permite que los modelos de lenguaje accedan a herramientas externas, lo que amplía significativamente sus capacidades para realizar tareas específicas como consultas a bases de datos, validaciones complejas o interacciones con APIs externas.

## Requisitos Previos

- n8n instalado y funcionando (ver `README.md` en la carpeta n8n)
- Acceso a un servidor MCP (puede ser local o remoto)
- Credenciales para los modelos de lenguaje a utilizar (ej. API key de OpenAI, Mistral, etc.)

## Configuración del Nodo MCP Client

### 1. Instalación del Nodo MCP Client

El nodo MCP Client viene incluido en la instalación estándar de n8n desde la versión 1.0. Si estás utilizando una versión anterior, actualiza n8n o instala el paquete comunitario:

```bash
# Si necesitas instalar el paquete comunitario (solo para versiones antiguas)
n8n-node-dev add n8n-nodes-mcp-client
```

### 2. Configuración de Variables de Entorno

Para activar correctamente el nodo MCP Client, añade las siguientes variables de entorno al archivo `docker-compose.yml`:

```yaml
environment:
  # Otras variables existentes...
  
  # Variables para MCP Client
  - N8N_NODES_INCLUDE_LANGCHAIN=true
  - N8N_AI_ENABLED=true
  - N8N_AI_NODES_ENABLED=true
```

### 3. Configuración del Servidor MCP

Puedes utilizar un servidor MCP existente o crear uno propio. Para este proyecto, recomendamos:

- **Opción 1**: Utilizar el nodo MCP Server Trigger de n8n para crear tu propio servidor MCP
- **Opción 2**: Utilizar un servidor MCP externo como Langserve o similar

#### Configuración del Nodo MCP Server Trigger

1. Crea un nuevo flujo de trabajo en n8n
2. Añade el nodo "MCP Server Trigger"
3. Configura el puerto y la ruta (por defecto: `http://localhost:3000/v1/mcp`)
4. Añade las herramientas que quieres exponer (por ejemplo, nodos HTTP Request para consultar Odoo)

## Creación de un Flujo de Trabajo con MCP Client y LLM

### Ejemplo: Procesamiento Inteligente de Facturas

Hemos creado un flujo de ejemplo en `flujos/llm_mcp_client_factura.json` que puedes importar directamente en n8n. Este flujo:

1. Recibe una factura a través de un webhook
2. Extrae el texto mediante OCR
3. Analiza la factura con un LLM
4. Utiliza el nodo MCP Client para acceder a herramientas externas
5. Realiza un análisis avanzado con validaciones y recomendaciones
6. Devuelve un informe estructurado

### Pasos para Configurar el Flujo

1. **Importar el flujo de ejemplo**:
   - Ve a n8n > Flujos de trabajo > Importar
   - Selecciona el archivo `flujos/llm_mcp_client_factura.json`

2. **Configurar las credenciales**:
   - Configura las credenciales para el nodo LLM (OpenAI, Mistral, etc.)
   - Configura las credenciales para el nodo MCP Client si es necesario

3. **Configurar el endpoint MCP**:
   - En el nodo MCP Client, establece la URL del servidor MCP:
     - Para servidor local: `http://localhost:3000/v1/mcp`
     - Para servidor externo: URL proporcionada por el proveedor

4. **Activar el flujo de trabajo**:
   - Activa el flujo de trabajo para que esté disponible a través del webhook

## Herramientas MCP Útiles para Procesamiento de Facturas

Estas son algunas herramientas que puedes exponer a través del servidor MCP para mejorar el procesamiento de facturas:

1. **Validador de CIF/NIF**: Herramienta para validar números de identificación fiscal españoles
2. **Consulta de Proveedores**: Buscar información de proveedores en Odoo
3. **Validador de Productos**: Verificar si los productos existen en el catálogo
4. **Calculadora de Impuestos**: Verificar si los cálculos de IVA son correctos
5. **Detector de Duplicados**: Comprobar si una factura ya existe en el sistema

## Ejemplo de Implementación de Servidor MCP

Aquí hay un ejemplo simplificado de cómo crear un servidor MCP en n8n:

1. Crea un nuevo flujo de trabajo llamado "Servidor MCP"
2. Añade un nodo "MCP Server Trigger"
3. Configura las siguientes herramientas:

   a. **Validar CIF/NIF**:
   - Añade un nodo "Function" que valide el formato y dígito de control
   - Conecta este nodo como una herramienta al MCP Server Trigger

   b. **Buscar Proveedor**:
   - Añade un nodo "HTTP Request" que consulte la API de Odoo
   - Configura los parámetros necesarios (CIF, nombre, etc.)
   - Conecta este nodo como una herramienta al MCP Server Trigger

   c. **Verificar Producto**:
   - Similar al anterior, pero consultando productos

4. Activa el flujo de trabajo

## Consejos para Optimizar el Uso de MCP Client

1. **Prompts Específicos**: Crea prompts detallados que expliquen al LLM cómo y cuándo utilizar las herramientas MCP
2. **Manejo de Errores**: Incluye manejo de errores en caso de que el servidor MCP no esté disponible
3. **Caché de Resultados**: Implementa un sistema de caché para evitar llamadas repetidas a las mismas herramientas
4. **Monitorización**: Monitoriza el uso de las herramientas MCP para detectar problemas o patrones de uso

## Solución de Problemas

### El nodo MCP Client no aparece en n8n

- Verifica que las variables de entorno estén correctamente configuradas
- Reinicia el contenedor de n8n
- Comprueba los logs de n8n para ver si hay errores relacionados

### Error de conexión al servidor MCP

- Verifica que la URL del servidor MCP sea correcta
- Comprueba que el servidor MCP esté en funcionamiento
- Verifica las credenciales de autenticación si son necesarias

### El LLM no utiliza las herramientas MCP

- Revisa el prompt para asegurarte de que instruye al LLM a utilizar las herramientas
- Verifica que las herramientas estén correctamente expuestas en el servidor MCP
- Prueba con una temperatura más baja en el LLM para hacerlo más determinista

## Recursos Adicionales

- [Documentación oficial de MCP Client en n8n](https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.toolmcp/)
- [Especificación del protocolo MCP](https://modelcontextprotocol.io/specification/)
- [Ejemplos de flujos de trabajo con MCP](https://n8n.io/workflows/categories/ai/)

## Próximos Pasos

1. Crear flujos de trabajo específicos para diferentes tipos de facturas
2. Implementar validaciones más avanzadas utilizando herramientas MCP
3. Integrar el procesamiento de facturas con el sistema de contabilidad
4. Crear un panel de control para monitorizar el procesamiento de facturas

---

Documento creado: 19 de julio de 2025  
Última actualización: 19 de julio de 2025
