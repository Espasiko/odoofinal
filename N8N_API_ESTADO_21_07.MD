# N8N API - Estado y Configuración Completa
**Fecha de actualización:** 21 de julio de 2025, 22:10

## 🔍 Investigación Completa de la API de n8n

### ✅ **Disponibilidad y Costos**
- **GRATUITA** para instancias self-hosted Community Edition
- **NO disponible** durante el trial gratuito de n8n Cloud
- **SÍ disponible** en instancias self-hosted sin restricciones de pago
- **Acceso completo** a todas las funcionalidades básicas de la API

### 🔐 **Autenticación y Configuración**

#### **API Key Configurada**
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJlNzE4M2QyYy1lMTNjLTQ4NGYtOWY5Zi03ZmQ1Y2U3ZmE1ZmYiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzUyOTQ0ODI4fQ.Sx3wsxu1-KJuaa3SFb8qMUfT59F8x7M1VIcyJvzO0Ts
```

#### **Método de Autenticación**
- **Header requerido:** `X-N8N-API-KEY`
- **Tipo de token:** JWT (JSON Web Token)
- **Base URL:** `http://localhost:5678/api/v1`

#### **Ubicación de Configuración**
- **Interfaz n8n:** User Settings → API Keys
- **Archivo .env:** Variable `N8N_API_KEY`
- **Docker Compose:** Variable de entorno `${N8N_API_KEY}`

## 🐳 **Configuración Docker**

### **Archivos Docker Compose Identificados**

#### 1. **Docker Compose Principal** (`/home/espasiko/mainmanusodoo/manusodoo-roto/docker-compose.yml`)
- **Configuración básica** de n8n
- **Puerto:** 5678:5678
- **Variables básicas:** N8N_HOST, N8N_PORT, N8N_PROTOCOL
- **Integración:** Con stack principal de ManusOdoo

#### 2. **Docker Compose Específico n8n** (`/home/espasiko/mainmanusodoo/manusodoo-roto/n8n/docker-compose.yml`)
- **Configuración avanzada** con API habilitada
- **Integración completa** con Odoo
- **Soporte LLM:** Mistral, OpenAI, Groq
- **Red:** manusodoo-roto_default
- **Volumen persistente:** n8n_storage

### **Variables de Entorno Configuradas**
```yaml
# API Configuration
- N8N_API_ENABLED=true
- N8N_API_AUTH_DISABLED=false
- N8N_API_AUTH_ACCESS_TOKEN=${N8N_API_KEY}

# Odoo Integration
- N8N_ODOO_URL=http://odoo:8069
- N8N_ODOO_DB=fresh_odoo_db
- N8N_ODOO_USER=admin
- N8N_ODOO_PASSWORD=admin

# Database
- DB_TYPE=sqlite
- DB_SQLITE_PATH=/home/node/.n8n/database.sqlite

# AI/LLM Support
- N8N_NODES_INCLUDE_LANGCHAIN=true
- N8N_AI_ENABLED=true
- N8N_AI_NODES_ENABLED=true
```

## 🚀 **Capacidades de la API**

### **Funcionalidades Principales**
1. **Gestión de Workflows**
   - Crear, leer, actualizar, eliminar workflows
   - Importar/exportar workflows
   - Gestión de tags y metadatos

2. **Control de Ejecuciones**
   - Ejecutar workflows manualmente
   - Monitorear ejecuciones en tiempo real
   - Acceder a logs y datos de ejecución
   - Gestión de ejecuciones programadas

3. **Gestión de Credenciales**
   - Crear y gestionar credenciales
   - Compartir credenciales entre workflows
   - Validar conexiones

4. **Acceso a Datos**
   - Obtener datos de ejecuciones
   - Acceder a logs detallados
   - Estadísticas de uso

### **Diferencias por Edición**

#### **Community Edition (Gratuita)**
- ✅ Acceso básico completo a la API
- ✅ Gestión de workflows y ejecuciones
- ✅ Gestión de credenciales básica
- ✅ Acceso a datos de ejecución

#### **Enterprise Edition**
- ✅ Todo lo de Community Edition
- ✅ API Keys con scopes específicos
- ✅ Role-Based Access Control (RBAC)
- ✅ Gestión avanzada de usuarios
- ✅ Auditoría detallada

## 🔧 **Integración con Scripts Existentes**

### **Script `fix_n8n_workflows.py`**
**Estado actual:** Basado en archivos JSON locales
**Mejoras posibles con API:**

1. **Descarga automática de workflows**
   ```python
   import requests
   
   headers = {'X-N8N-API-KEY': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'}
   response = requests.get('http://localhost:5678/api/v1/workflows', headers=headers)
   workflows = response.json()
   ```

2. **Aplicación de fixes en vivo**
   - Descargar workflow desde n8n
   - Aplicar correcciones automáticas
   - Subir workflow corregido
   - Mantener backup local

3. **Sincronización bidireccional**
   - Backup automático antes de modificaciones
   - Validación de cambios
   - Rollback automático en caso de error

### **Endpoints API Principales**
```
GET    /api/v1/workflows              # Listar workflows
GET    /api/v1/workflows/{id}         # Obtener workflow específico
POST   /api/v1/workflows              # Crear workflow
PUT    /api/v1/workflows/{id}         # Actualizar workflow
DELETE /api/v1/workflows/{id}         # Eliminar workflow
POST   /api/v1/workflows/{id}/execute # Ejecutar workflow
GET    /api/v1/executions             # Listar ejecuciones
GET    /api/v1/credentials            # Listar credenciales
```

## 📊 **Estado de Configuración**

### ✅ **Completado**
- [x] API Key real configurada en .env
- [x] Docker Compose actualizado con variable de entorno
- [x] Identificación de ambos archivos docker-compose.yml
- [x] Configuración de red y volúmenes
- [x] Integración con stack ManusOdoo

### 🔄 **Pendiente**
- [ ] Prueba de conectividad API
- [ ] Validación de autenticación
- [ ] Integración con script fix_n8n_workflows.py
- [ ] Documentación de endpoints específicos
- [ ] Configuración de webhooks para integración con FastAPI

## 🔗 **URLs y Accesos**
- **n8n Interface:** http://localhost:5678
- **API Base URL:** http://localhost:5678/api/v1
- **Documentación API:** http://localhost:5678/api-docs (si está habilitada)
- **Webhook Base:** http://localhost:5678/webhook/

## 🛠️ **Próximos Pasos Recomendados**

1. **Validar configuración actual**
   ```bash
   curl -H "X-N8N-API-KEY: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
        http://localhost:5678/api/v1/workflows
   ```

2. **Extender script de fixes**
   - Añadir funcionalidad de API
   - Implementar backup automático
   - Crear sistema de sincronización

3. **Integrar con FastAPI**
   - Crear endpoints para gestión de workflows
   - Implementar webhooks para notificaciones
   - Añadir monitoreo de ejecuciones

## 📝 **Notas Técnicas**
- **Timezone configurado:** Europe/Madrid
- **Log level:** Debug (para troubleshooting)
- **Encryption key:** Configurada para seguridad
- **Base de datos:** SQLite (más simple para desarrollo)
- **Red Docker:** manusodoo-roto_default (comunicación con Odoo)

---
**Documento generado automáticamente el 21/07/2025 a las 22:10**