# 🔧 Guía de Troubleshooting N8N - Manusodoo-Roto

## 🚀 Inicio Rápido

### 1. Ejecutar Diagnóstico Automático
```bash
# Ejecutar script de troubleshooting completo
python troubleshoot_n8n.py

# O ejecutar el script de prueba de API
python test_n8n_api.py
```

### 2. Verificar Estado de Servicios
```bash
# Verificar contenedores Docker
docker-compose ps

# Ver logs de n8n
docker-compose logs n8n

# Reiniciar n8n si es necesario
docker-compose restart n8n
```

## 🔍 Problemas Comunes y Soluciones

### ❌ Problema: "Connection refused" a n8n
**Síntomas:**
- No se puede conectar a `http://localhost:5678`
- Error de conexión en scripts de prueba

**Soluciones:**
1. **Verificar contenedor:**
   ```bash
   docker-compose ps | grep n8n
   ```

2. **Iniciar servicios:**
   ```bash
   docker-compose up -d n8n
   ```

3. **Verificar puertos:**
   ```bash
   netstat -tlnp | grep 5678
   ```

### ❌ Problema: "Forbidden domain" en API
**Síntomas:**
- Error 403 al acceder a la API
- Mensaje "Forbidden domain"

**Soluciones:**
1. **Verificar API Key:**
   ```bash
   # Verificar variable de entorno
   echo $N8N_API_KEY
   
   # Debe ser: pelotazo-n8n-api-token-seguro-2025
   ```

2. **Actualizar .env:**
   ```bash
   # Asegurar que .env contiene:
   N8N_API_KEY=pelotazo-n8n-api-token-seguro-2025
   ```

3. **Reiniciar n8n:**
   ```bash
   docker-compose restart n8n
   ```

### ❌ Problema: Workflows no se activan
**Síntomas:**
- Workflows aparecen como inactivos
- Error al activar desde la interfaz

**Soluciones:**
1. **Corregir archivos JSON:**
   ```bash
   python fix_n8n_workflows.py
   ```

2. **Verificar nodos problemáticos:**
   - Nodos `readPDF` sin `binaryPropertyName`
   - Nodos `webhook` sin configuración
   - Nodos `httpRequest` sin headers

3. **Importar workflows corregidos:**
   - Acceder a http://localhost:5678
   - Importar archivos JSON corregidos
   - Activar workflows manualmente

### ❌ Problema: Error 401 "Unauthorized"
**Síntomas:**
- Error de autenticación en API calls
- Token inválido

**Soluciones:**
1. **Verificar configuración:**
   ```python
   # En api/utils/n8n_config.py
   N8N_API_KEY = "pelotazo-n8n-api-token-seguro-2025"
   ```

2. **Verificar headers HTTP:**
   ```python
   headers = {
       "Authorization": f"Bearer {api_key}",
       "Content-Type": "application/json"
   }
   ```

### ❌ Problema: Webhooks no responden
**Síntomas:**
- Error 404 en endpoints webhook
- Webhooks no reciben datos

**Soluciones:**
1. **Verificar workflows activos:**
   - Workflows con webhooks deben estar activos
   - Verificar URLs de webhook en workflows

2. **Probar endpoints:**
   ```bash
   # Probar webhook básico
   curl -X POST http://localhost:5678/webhook/procesar-factura \
        -H "Content-Type: application/json" \
        -d '{"test": "data"}'
   ```

## 🛠️ Scripts de Mantenimiento

### 1. Troubleshooting Completo
```bash
python troubleshoot_n8n.py
```
**Qué hace:**
- Verifica contenedor Docker
- Prueba conectividad básica
- Valida autenticación API
- Analiza workflows disponibles
- Prueba endpoints webhook
- Verifica archivos locales
- Genera reporte detallado

### 2. Corrección de Workflows
```bash
python fix_n8n_workflows.py
```
**Qué hace:**
- Detecta parámetros faltantes en nodos
- Corrige configuración de nodos `readPDF`
- Añade headers faltantes en `httpRequest`
- Hace backup antes de modificar
- Reporta cambios realizados

### 3. Prueba de API
```bash
python test_n8n_api.py
```
**Qué hace:**
- Prueba conectividad con API
- Lista workflows disponibles
- Verifica autenticación
- Prueba ejecución de workflows

## 📋 Checklist de Verificación

### ✅ Servicios Base
- [ ] PostgreSQL ejecutándose (puerto 5432)
- [ ] Odoo ejecutándose (puerto 8069)
- [ ] n8n ejecutándose (puerto 5678)
- [ ] FastAPI ejecutándose (puerto 8000)

### ✅ Configuración n8n
- [ ] Variable `N8N_API_KEY` configurada
- [ ] API Key coincide en todos los archivos
- [ ] Workflows JSON válidos
- [ ] Workflows activos en interfaz

### ✅ Conectividad
- [ ] `http://localhost:5678` accesible
- [ ] API responde en `/api/v1/workflows`
- [ ] Webhooks responden en `/webhook/*`
- [ ] FastAPI puede conectar a n8n

### ✅ Workflows
- [ ] Workflows importados correctamente
- [ ] Nodos `readPDF` configurados
- [ ] Nodos `httpRequest` con headers
- [ ] Webhooks configurados

## 🔧 Comandos de Emergencia

### Reiniciar Todo
```bash
docker-compose down
docker-compose up -d
```

### Limpiar y Reiniciar n8n
```bash
docker-compose stop n8n
docker-compose rm -f n8n
docker-compose up -d n8n
```

### Ver Logs en Tiempo Real
```bash
# Logs de n8n
docker-compose logs -f n8n

# Logs de todos los servicios
docker-compose logs -f
```

### Verificar Variables de Entorno
```bash
# En el contenedor n8n
docker-compose exec n8n env | grep N8N

# En el sistema
env | grep N8N
```

## 📊 Interpretación de Reportes

### Estado "EXCELENTE" 🎉
- Todos los tests pasaron
- n8n completamente funcional
- Listo para usar workflows

### Estado "BUENO" ✅
- Sin errores críticos
- Algunas advertencias menores
- Funcional con limitaciones

### Estado "PROBLEMAS DETECTADOS" ❌
- Errores críticos encontrados
- Requiere intervención inmediata
- Seguir recomendaciones del reporte

## 🚨 Escalación de Problemas

### Nivel 1: Problemas Menores
- Workflows inactivos
- Configuración incorrecta
- **Solución:** Scripts automáticos

### Nivel 2: Problemas de Conectividad
- Servicios no responden
- Errores de red
- **Solución:** Reiniciar servicios

### Nivel 3: Problemas Críticos
- Contenedores no inician
- Errores de configuración base
- **Solución:** Revisar docker-compose.yml y .env

## 📞 Contacto y Soporte

### Archivos de Log Importantes
- `n8n_troubleshoot_report_*.json` - Reporte completo
- `docker-compose logs n8n` - Logs del contenedor
- `api/logs/` - Logs de FastAPI

### Información para Soporte
1. Reporte de troubleshooting
2. Logs de contenedores
3. Configuración actual (.env)
4. Versión de workflows JSON

---

## 🔄 Flujo de Troubleshooting Recomendado

1. **Ejecutar diagnóstico:** `python troubleshoot_n8n.py`
2. **Revisar reporte generado**
3. **Aplicar correcciones sugeridas**
4. **Ejecutar diagnóstico nuevamente**
5. **Verificar workflows en interfaz web**
6. **Probar integración con FastAPI**

---

*Última actualización: Enero 2025*
*Versión: 1.0*
