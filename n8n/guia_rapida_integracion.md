# Guía Rápida de Integración n8n-FastAPI-Odoo 18

## Introducción

Esta guía proporciona instrucciones paso a paso para configurar y utilizar la integración entre n8n, FastAPI y Odoo 18 en el proyecto Pelotazo ERP. La integración permite automatizar el procesamiento OCR de facturas, validar datos con modelos de lenguaje (LLM) y crear facturas en Odoo 18.

## Requisitos Previos

- Docker y Docker Compose instalados
- Acceso a los servicios:
  - Odoo 18: http://localhost:8069
  - n8n: http://localhost:5678
  - FastAPI: http://localhost:8000
  - Adminer (DB Manager): http://localhost:8080

## 1. Configuración Inicial

### 1.1 Actualizar n8n con la nueva configuración

```bash
cd /home/espasiko/mainmanusodoo/manusodoo-roto/n8n
./actualizar_n8n.sh
```

Este script:
- Detiene n8n si está en ejecución
- Configura las claves API necesarias
- Inicia n8n con la nueva configuración
- Muestra instrucciones para importar los flujos de trabajo

### 1.2 Configurar variables de entorno para FastAPI

```bash
cd /home/espasiko/mainmanusodoo/manusodoo-roto
./actualizar_env_n8n.sh
```

Este script:
- Actualiza el archivo `.env` con las variables necesarias para la integración
- Configura las URLs y tokens de API para la comunicación entre FastAPI y n8n

## 2. Importar Flujos de Trabajo en n8n

1. Accede a n8n en http://localhost:5678
2. Ve a Flujos de trabajo > Importar
3. Importa los siguientes archivos:
   - `n8n/flujos/procesar_factura_ocr_mejorado.json`
   - `n8n/flujos/llm_mcp_client_factura.json`
   - `n8n/flujos/servidor_mcp_herramientas.json`

## 3. Verificar Compatibilidad con Odoo 18

```bash
cd /home/espasiko/mainmanusodoo/manusodoo-roto/n8n
./verificar_compatibilidad_odoo18.py
```

Este script:
- Verifica la conexión con Odoo 18
- Comprueba la compatibilidad de los endpoints de la API
- Verifica la estructura de campos necesarios
- Comprueba si n8n tiene nodos específicos para Odoo

## 4. Ejecutar Pruebas de Integración

```bash
cd /home/espasiko/mainmanusodoo/manusodoo-roto
python -m tests.integration.test_n8n_integration
```

Estas pruebas verifican:
- La conexión entre FastAPI y n8n
- La capacidad de listar flujos de trabajo
- La ejecución de flujos OCR y LLM-MCP
- La activación y desactivación de flujos

## 5. Uso de la API de n8n desde FastAPI

### 5.1 Verificar estado de conexión

```
GET http://localhost:8000/api/v1/n8n/status
```

### 5.2 Listar flujos de trabajo

```
GET http://localhost:8000/api/v1/n8n/workflows
```

### 5.3 Ejecutar flujo OCR

```
POST http://localhost:8000/api/v1/n8n/execute/ocr
Content-Type: application/json

{
  "supplier_name": "NEVIR",
  "supplier_vat": "B84201219",
  "file_path": "/ruta/a/factura.pdf"
}
```

### 5.4 Ejecutar flujo LLM-MCP

```
POST http://localhost:8000/api/v1/n8n/execute/llm-mcp
Content-Type: application/json

{
  "invoice_text": "Texto extraído de la factura...",
  "supplier_name": "NEVIR"
}
```

## 6. Flujos de Trabajo Disponibles

### 6.1 Procesamiento OCR Mejorado

Este flujo:
- Recibe una factura en PDF o imagen
- Detecta automáticamente el proveedor
- Utiliza prompts específicos para mejorar la precisión
- Implementa un sistema de caché para evitar reprocesamiento
- Valida los datos extraídos
- Crea la factura en Odoo si se solicita

Para más detalles, consulta `n8n/guia_ocr_mejorado.md`.

### 6.2 Análisis con LLM y MCP Client

Este flujo:
- Recibe texto extraído de una factura
- Analiza el contenido con un modelo de lenguaje
- Utiliza herramientas MCP para validaciones avanzadas
- Proporciona recomendaciones y correcciones

Para más detalles, consulta `n8n/guia_integracion_mcp_llm.md`.

### 6.3 Servidor MCP con Herramientas

Este flujo:
- Expone herramientas especializadas para procesamiento de facturas
- Incluye validación de CIF/NIF español
- Permite buscar proveedores y productos en Odoo
- Valida facturas y detecta duplicados

## 7. Solución de Problemas

### 7.1 Error de conexión con n8n

- Verifica que n8n esté en ejecución: `docker-compose ps`
- Comprueba que las variables de entorno estén configuradas correctamente
- Verifica que el token de API sea válido

### 7.2 Error al ejecutar flujos

- Revisa los logs de n8n: `docker-compose logs n8n`
- Verifica que los flujos estén activados en n8n
- Comprueba que las credenciales estén configuradas en los nodos

### 7.3 Error de conexión con Odoo

- Verifica que Odoo esté en ejecución: `docker-compose ps`
- Comprueba las credenciales de Odoo
- Verifica que la base de datos exista y sea accesible

## 8. Recursos Adicionales

- Documentación de n8n: https://docs.n8n.io/
- Documentación de la API de Odoo 18: https://www.odoo.com/documentation/18.0/developer/api.html
- Guía de integración MCP-LLM: `n8n/guia_integracion_mcp_llm.md`
- Guía de OCR mejorado: `n8n/guia_ocr_mejorado.md`
- Resumen de integración n8n-FastAPI: `n8n/resumen_integracion_n8n_fastapi.md`

---

Documento creado: 19 de julio de 2025  
Última actualización: 19 de julio de 2025
