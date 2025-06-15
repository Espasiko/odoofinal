# Memoria: Configuración y Resolución de Problemas del Servidor MCP Odoo

## Resumen Ejecutivo

Este documento detalla el proceso de instalación, configuración y resolución de problemas del servidor MCP (Model Context Protocol) para Odoo 18, incluyendo los fallos encontrados y las soluciones aplicadas.

## 1. Configuración Inicial

### 1.1 Instalación del Servidor MCP Odoo
- **Servidor instalado**: `mcp.config.usrremotemcp.odoo`
- **Herramienta principal**: `execute_method`
- **Variables de entorno configuradas**:
  - `ODOO_URL=http://localhost:8069`
  - `ODOO_DB=postgres`
  - `ODOO_USERNAME=admin`
  - `ODOO_PASSWORD=admin`

### 1.2 Parámetros de la Herramienta execute_method
- `model` (string): Modelo de Odoo a consultar
- `method` (string): Método a ejecutar
- `args` (array): Argumentos del método
- `kwargs` (object): Argumentos con nombre (opcional)

## 2. Problemas Encontrados y Soluciones

### 2.1 Error Principal: Connection Reset by Peer

**Síntoma**: 
```
Connection reset by peer durante autenticación XML-RPC
```

**Diagnóstico**:
1. Verificación del estado de contenedores Docker:
   - Contenedor Odoo: `manusodoo-roto_fastapi` - **Running**
   - Contenedor PostgreSQL: `manusodoo-roto_db_1` - **Stopped**

2. Identificación del conflicto de puertos:
   - Puerto 5432 ocupado por servicio PostgreSQL del sistema
   - PID 303 utilizando `localhost:postgresql`

**Solución Aplicada**:
1. **Detener servicio PostgreSQL del sistema**:
   ```bash
   sudo systemctl stop postgresql
   ```

2. **Iniciar contenedor PostgreSQL de Docker**:
   ```bash
   docker start manusodoo-roto_db_1
   ```

3. **Verificar estado de contenedores**:
   ```bash
   docker ps
   ```
   - Resultado: Todos los contenedores en estado `Up`

### 2.2 Verificación de la Solución

**Pruebas de Conectividad**:
1. **Test HTTP a Odoo**:
   ```bash
   curl -I http://localhost:8069
   ```
   - Resultado: `200 OK` - Servidor respondiendo correctamente

2. **Test XML-RPC directo**:
   - Script Python creado: `test_odoo_xmlrpc.py`
   - Resultado: Autenticación exitosa, consulta a `res.users` funcional

3. **Test del Servidor MCP**:
   - Búsqueda de usuarios: ✅ Exitosa
   - Lectura de datos de usuario: ✅ Exitosa
   - Consulta de productos: ✅ Exitosa

## 3. Métodos Soportados por el Servidor MCP

El servidor MCP de Odoo soporta todos los métodos estándar del ORM de Odoo:

- `search`: Buscar registros
- `read`: Leer campos específicos
- `write`: Actualizar registros
- `create`: Crear nuevos registros
- `unlink`: Eliminar registros
- `search_read`: Buscar y leer en una operación
- `search_count`: Contar registros que coinciden con criterios

## 4. Ejemplos de Uso Exitosos

### 4.1 Búsqueda de Usuarios
```json
{
  "server_name": "mcp.config.usrremotemcp.odoo",
  "tool_name": "execute_method",
  "args": {
    "model": "res.users",
    "method": "search",
    "args": [["id", "=", 2]]
  }
}
```
**Resultado**: `[2]`

### 4.2 Lectura de Datos de Usuario
```json
{
  "server_name": "mcp.config.usrremotemcp.odoo",
  "tool_name": "execute_method",
  "args": {
    "model": "res.users",
    "method": "read",
    "args": [[2], ["name", "login", "email"]]
  }
}
```
**Resultado**: Usuario Mitchell Admin con datos completos

### 4.3 Consulta de Productos
```json
{
  "server_name": "mcp.config.usrremotemcp.odoo",
  "tool_name": "execute_method",
  "args": {
    "model": "product.template",
    "method": "search_read",
    "args": [[], ["name", "default_code", "list_price"]],
    "kwargs": {"limit": 5}
  }
}
```
**Resultado**: 5 productos con nombres, códigos y precios

## 5. Estado Final

✅ **Servidor MCP Odoo completamente funcional**
✅ **Conexión XML-RPC estable**
✅ **Todos los contenedores Docker operativos**
✅ **Pruebas de funcionalidad exitosas**

## 6. Recomendaciones

1. **Monitoreo**: Verificar periódicamente el estado de los contenedores Docker
2. **Conflictos de Puerto**: Asegurar que el servicio PostgreSQL del sistema no interfiera
3. **Backup**: Mantener respaldos de la configuración del servidor MCP
4. **Documentación**: Actualizar esta memoria con nuevas funcionalidades implementadas

---

**Fecha de creación**: $(date)
**Estado**: Resuelto y Operativo
**Responsable**: Asistente IA