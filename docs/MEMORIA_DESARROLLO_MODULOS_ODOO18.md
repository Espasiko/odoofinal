# Memoria de Desarrollo de Módulos Personalizados en Odoo 18

## Resumen Ejecutivo

Este documento detalla el proceso completo de desarrollo e instalación de módulos personalizados en Odoo 18, incluyendo los problemas encontrados y las soluciones implementadas durante el desarrollo del proyecto Pelotazo.

## 1. Contexto del Proyecto

### 1.1 Objetivo
Desarrollo de módulos personalizados para Odoo 18 en el contexto del sistema Pelotazo, incluyendo:
- Creación de módulos desde cero
- Instalación de módulos de terceros
- Integración con sistemas de IA
- Gestión de recursos estáticos

### 1.2 Entorno Tecnológico
- **Plataforma**: Odoo 18
- **Containerización**: Docker y docker-compose
- **Base de Datos**: PostgreSQL
- **Lenguajes**: Python, XML, JavaScript
- **Control de Versiones**: Git

## 2. Estructura de Módulos Odoo 18

### 2.1 Estructura Estándar
```
módulo_personalizado/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   └── modelo.py
├── views/
│   └── vista.xml
├── data/
│   └── datos.xml
├── static/
│   ├── description/
│   │   └── icon.png
│   ├── src/
│   │   ├── css/
│   │   ├── js/
│   │   └── xml/
└── security/
    └── ir.model.access.csv
```

### 2.2 Archivos Clave

#### __manifest__.py
Contiene los metadatos del módulo:
```python
{
    'name': 'Nombre del Módulo',
    'version': '18.0.1.0.0',
    'depends': ['base', 'mail'],
    'data': [
        'data/datos.xml',
        'views/vista.xml',
    ],
    'installable': True,
    'auto_install': False,
}
```

## 3. Desarrollo del Módulo odoo_turbo_ai_agent

### 3.1 Descripción
Módulo personalizado desarrollado para integración con sistemas de IA, ubicado en `/addons/odoo_turbo_ai_agent/`.

### 3.2 Componentes
- **Modelos personalizados**: Clases Python que extienden funcionalidad base
- **Vistas XML**: Interfaces de usuario personalizadas
- **Datos iniciales**: Configuración predeterminada en XML
- **Recursos estáticos**: Imágenes, CSS, JavaScript

## 4. Problemas Encontrados y Soluciones

### 4.1 Error: Imagen Demasiado Grande

#### Problema
```
Error: Image is too big (50 Mpx max)
```

#### Causa
- Imagen `chatgpt.png` de 8192x8192 píxeles (67 Mpx)
- Excedía el límite de 50 Mpx establecido por Odoo
- Referencias en `mail_channel_data.xml` y `user_partner_data.xml`

#### Solución Implementada

1. **Análisis del problema**:
   ```bash
   file chatgpt.png
   # Resultado: JPEG image data, 8192 x 8192
   ```

2. **Redimensionamiento con Python**:
   ```python
   from PIL import Image
   
   # Cargar imagen original
   img = Image.open('chatgpt.png')
   
   # Redimensionar a 512x512 píxeles
   img_resized = img.resize((512, 512))
   
   # Guardar imagen redimensionada
   img_resized.save('chatgpt_resized.png')
   ```

3. **Actualización de referencias XML**:
   ```xml
   <!-- Antes -->
   <field name="image_128" type="base64" file="odoo_turbo_ai_agent/static/description/chatgpt.png"/>
   
   <!-- Después -->
   <field name="image_128" type="base64" file="odoo_turbo_ai_agent/static/description/chatgpt_resized.png"/>
   ```

### 4.2 Error: FileNotFoundError

#### Problema
```
FileNotFoundError: odoo_turbo_ai_agent/static/description/chatgpt.png
```

#### Causa
- Referencias inconsistentes en archivos XML
- `mail_channel_data.xml` corregido pero `user_partner_data.xml` no
- Imagen original eliminada pero referencias no actualizadas

#### Solución
1. **Identificación de archivos afectados**:
   ```bash
   grep -r "chatgpt.png" addons/odoo_turbo_ai_agent/
   ```

2. **Actualización sistemática**:
   - Corregir `user_partner_data.xml`
   - Verificar todos los archivos XML
   - Asegurar consistencia en referencias

## 5. Proceso de Actualización de Módulos

### 5.1 Procedimiento Estándar

1. **Detener servicio Odoo**:
   ```bash
   docker-compose stop odoo
   ```

2. **Actualizar módulo**:
   ```bash
   docker-compose run --rm odoo odoo -u nombre_modulo --stop-after-init
   ```

3. **Reiniciar servicio**:
   ```bash
   docker-compose start odoo
   ```

4. **Verificar estado**:
   ```bash
   docker-compose ps
   ```

5. **Probar funcionalidad**:
   - Acceder a http://localhost:8069/
   - Verificar instalación del módulo
   - Probar funcionalidades implementadas

### 5.2 Comandos de Diagnóstico

```bash
# Ver logs en tiempo real
docker-compose logs -f odoo

# Verificar estado de contenedores
docker-compose ps

# Acceder al contenedor de Odoo
docker-compose exec odoo bash

# Verificar archivos del módulo
ls -la /mnt/extra-addons/nombre_modulo/
```

## 6. Mejores Prácticas Identificadas

### 6.1 Desarrollo
- **Entorno consistente**: Usar Docker para evitar problemas de dependencias
- **Estructura estándar**: Seguir convenciones de Odoo para facilitar mantenimiento
- **Versionado**: Usar Git para control de cambios
- **Documentación**: Mantener documentación actualizada

### 6.2 Recursos Estáticos
- **Tamaño de imágenes**: Respetar límites de Odoo (50 Mpx máximo)
- **Formatos optimizados**: Usar PNG/JPEG optimizados
- **Referencias consistentes**: Verificar todas las referencias en archivos XML
- **Nomenclatura clara**: Usar nombres descriptivos para archivos

### 6.3 Gestión de Errores
- **Logs detallados**: Revisar logs de Odoo para diagnóstico
- **Pruebas incrementales**: Probar cambios de forma gradual
- **Rollback preparado**: Mantener versiones funcionales como respaldo
- **Documentación de errores**: Registrar problemas y soluciones

## 7. Configuración Docker

### 7.1 Servicios Configurados
- **db**: PostgreSQL para base de datos
- **odoo**: Servidor Odoo 18
- **adminer**: Interfaz web para gestión de BD
- **fastapi**: API personalizada

### 7.2 Volúmenes y Puertos
```yaml
services:
  odoo:
    ports:
      - "8069:8069"
    volumes:
      - ./addons:/mnt/extra-addons
      - odoo-data:/var/lib/odoo
  
  db:
    ports:
      - "5432:5432"
    volumes:
      - db-data:/var/lib/postgresql/data
```

## 8. Herramientas y Tecnologías

### 8.1 Desarrollo
- **Python**: Lógica de negocio y modelos
- **XML**: Vistas y datos iniciales
- **JavaScript**: Funcionalidad frontend
- **CSS**: Estilos personalizados

### 8.2 Infraestructura
- **Docker**: Containerización
- **PostgreSQL**: Base de datos
- **Nginx**: Proxy reverso (si aplica)
- **Git**: Control de versiones

### 8.3 Utilidades
- **PIL/Pillow**: Manipulación de imágenes
- **ImageMagick**: Procesamiento de imágenes (alternativa)
- **ripgrep**: Búsqueda en archivos
- **file**: Análisis de archivos

## 9. Conclusiones

### 9.1 Logros
- ✅ Desarrollo exitoso de módulo personalizado
- ✅ Resolución de problemas de recursos estáticos
- ✅ Implementación de proceso de actualización robusto
- ✅ Documentación completa del proceso

### 9.2 Lecciones Aprendidas
- **Validación temprana**: Verificar recursos antes de integración
- **Consistencia**: Mantener referencias actualizadas en todos los archivos
- **Automatización**: Crear scripts para tareas repetitivas
- **Monitoreo**: Implementar logging adecuado para diagnóstico

### 9.3 Próximos Pasos
- Implementar tests automatizados
- Crear pipeline CI/CD
- Optimizar rendimiento de módulos
- Expandir funcionalidades de IA

## 10. Referencias

- [Documentación Oficial Odoo 18](https://www.odoo.com/documentation/18.0/)
- [Guía de Desarrollo de Módulos](https://www.odoo.com/documentation/18.0/developer/)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [Python PIL Documentation](https://pillow.readthedocs.io/)

---

**Fecha de creación**: $(date +"%Y-%m-%d")
**Versión**: 1.0
**Autor**: Equipo de Desarrollo Pelotazo
**Estado**: Completado