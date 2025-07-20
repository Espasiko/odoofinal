# Guía de Configuración de n8n para Pelotazo ERP

## Introducción

Esta guía explica cómo configurar n8n para automatizar flujos de trabajo en el proyecto Pelotazo ERP, especialmente para el procesamiento OCR de facturas, gestión de inventario y cumplimiento RGPD.

## Requisitos previos

- Docker y Docker Compose instalados
- Proyecto Pelotazo ERP en ejecución (Odoo, FastAPI, PostgreSQL)
- Acceso a las credenciales de Odoo y PostgreSQL

## Inicio y detención de n8n

Para iniciar n8n:
```bash
cd /home/espasiko/mainmanusodoo/manusodoo-roto/n8n
./start_n8n.sh
```

Para detener n8n:
```bash
cd /home/espasiko/mainmanusodoo/manusodoo-roto/n8n
./stop_n8n.sh
```

## Acceso a la interfaz web

- URL: http://localhost:5678
- Usuario: (configurar en el primer inicio)
- Contraseña: (configurar en el primer inicio)

## Configuración inicial

1. Accede a http://localhost:5678
2. Crea una cuenta de administrador
3. Configura las credenciales para los servicios externos

## Configuración de credenciales

### Odoo

1. En n8n, ve a **Configuración > Credenciales**
2. Haz clic en **Crear nueva**
3. Selecciona el tipo **Odoo**
4. Configura los siguientes parámetros:
   - Nombre: Odoo Pelotazo
   - URL: http://odoo:8069
   - Base de datos: fresh_odoo_db
   - Usuario: admin
   - Contraseña: admin
5. Guarda la configuración

### HTTP Request (para FastAPI)

1. En n8n, ve a **Configuración > Credenciales**
2. Haz clic en **Crear nueva**
3. Selecciona el tipo **HTTP Request**
4. Configura los siguientes parámetros:
   - Nombre: FastAPI Pelotazo
   - URL: http://fastapi:8000
5. Guarda la configuración

## Flujos de trabajo recomendados

### 1. Procesamiento automático de facturas OCR

Este flujo de trabajo automatiza el procesamiento de facturas mediante OCR:

1. **Trigger**: Webhook o carpeta vigilada
2. **Procesamiento**: Envío del archivo a FastAPI para OCR
3. **Validación**: Verificación de datos extraídos
4. **Creación**: Creación de factura en Odoo
5. **Notificación**: Envío de notificación por email o Slack

### 2. Sincronización de inventario

Este flujo sincroniza el inventario entre diferentes sistemas:

1. **Trigger**: Programado (cada hora)
2. **Extracción**: Obtención de datos de inventario de Odoo
3. **Transformación**: Formateo de datos
4. **Carga**: Actualización en sistemas externos

### 3. Cumplimiento RGPD

Este flujo gestiona solicitudes de derechos RGPD:

1. **Trigger**: Formulario web o email
2. **Procesamiento**: Identificación del tipo de solicitud
3. **Ejecución**: Realización de la acción solicitada (acceso, eliminación, etc.)
4. **Documentación**: Registro de la solicitud y respuesta
5. **Notificación**: Confirmación al solicitante

## Consideraciones de seguridad

- No almacenar credenciales sensibles en los flujos de trabajo
- Utilizar variables de entorno para información sensible
- Revisar regularmente los logs de ejecución
- Implementar validación de datos en todos los flujos

## Solución de problemas

- **Error de conexión a Odoo**: Verificar que el contenedor de Odoo esté en ejecución y accesible desde la red Docker
- **Error de conexión a FastAPI**: Verificar que el contenedor FastAPI esté en ejecución
- **Error en procesamiento OCR**: Revisar los logs de FastAPI para identificar el problema

## Recursos adicionales

- [Documentación oficial de n8n](https://docs.n8n.io/)
- [Nodos de Odoo para n8n](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.odoo/)
- [Nodos HTTP Request para n8n](https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest/)
