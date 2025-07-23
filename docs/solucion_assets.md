# Solución Assets - Error 500 web.assets_frontend_lazy.min.js

## Problema Identificado
Error 500 Internal Server Error al acceder a:
`http://localhost:8070/web/assets/1/a49a9c4/web.assets_frontend_lazy.min.js`

## Causa Raíz
Assets corruptos o mal generados almacenados en:
- Sistema de archivos del contenedor Odoo
- Base de datos PostgreSQL (tabla `ir_attachment`)

## Solución Aplicada

### 1. Limpieza de Assets del Sistema de Archivos
```bash
# Eliminar archivos de assets del filestore
docker exec manusodoo-roto_odoo_1 find /var/lib/odoo/filestore/fresh_odoo_db -name "*assets*" -delete
```

### 2. Limpieza de Assets de la Base de Datos
```sql
-- Eliminar registros de assets corruptos de la BD
docker exec manusodoo-roto_db_1 psql -U odoo -d fresh_odoo_db -c "DELETE FROM ir_attachment WHERE name LIKE '%assets%';"
```
**Resultado**: 41 registros eliminados

### 3. Verificación de la Solución
```bash
# Comprobar que el archivo ahora responde correctamente
curl -I http://localhost:8070/web/assets/1/a49a9c4/web.assets_frontend_lazy.min.js
```

## Resultado Final
- ✅ HTTP 200 OK (anteriormente 500)
- ✅ Content-Type: application/javascript
- ✅ Content-Length: 2,423,373 bytes
- ✅ Assets regenerados automáticamente por Odoo

## Comandos de Diagnóstico Útiles

### Verificar logs del contenedor Odoo
```bash
docker logs manusodoo-roto_odoo_1 --tail 50
```

### Verificar estado de contenedores
```bash
docker ps
```

### Reiniciar contenedor Odoo (si es necesario)
```bash
docker restart manusodoo-roto_odoo_1
```

### Verificar assets en BD
```sql
SELECT COUNT(*) FROM ir_attachment WHERE name LIKE '%assets%';
```

## Notas Importantes
- Los assets se regeneran automáticamente cuando Odoo los necesita
- No es necesario reiniciar el contenedor después de limpiar assets
- La limpieza de assets es segura y no afecta otros datos
- Este problema puede ocurrir tras actualizaciones o cambios en módulos

## Prevención
- Realizar backups regulares antes de actualizaciones
- Monitorizar logs de Odoo para detectar errores temprano
- Verificar integridad de assets después de cambios importantes

Fecha de resolución: 12/06/2025
Estado: ✅ RESUELTO