# Tema El Pelotazo para Odoo

Tema personalizado para la tienda online de El Pelotazo Electrohogar, integrado con WordPress.

## Características

- Diseño limpio y minimalista
- Colores corporativos de El Pelotazo
- Integración con menú de WordPress
- Totalmente responsive
- Optimizado para rendimiento

## Instalación

1. Copia la carpeta `theme_pelotazo` al directorio de módulos personalizados de Odoo (normalmente en `addons/`)
2. Asegúrate de que el usuario de Odoo tenga permisos para acceder al directorio
3. En Odoo, ve a **Aplicaciones > Actualizar lista de aplicaciones**
4. Busca "Tema El Pelotazo" y haz clic en Instalar
5. Ve a **Sitio Web > Configuración > Sitio Web**
6. En "Tema de sitio web", selecciona "Tema El Pelotazo"
7. Haz clic en Guardar

## Personalización

### Colores
Los colores principales están definidos en `static/src/scss/theme.scss`:
- Rojo principal: `#E31E24`
- Gris oscuro: `#333333`
- Fondo blanco: `#FFFFFF`

### Logo
Para cambiar el logo:
1. Ve a **Sitio Web > Configuración > Configuración general**
2. Sube tu logo en la sección "Empresa"
3. Tamaño recomendado: 180x50 píxeles

### Enlaces del menú
Los enlaces del menú están configurados en `views/layout.xml`. Actualiza las URLs según sea necesario.

## Estructura del proyecto

```
theme_pelotazo/
├── __init__.py
├── __manifest__.py
├── README.md
├── static/
│   └── src/
│       ├── js/
│       │   └── theme.js
│       └── scss/
│           └── theme.scss
└── views/
    ├── assets.xml
    ├── layout.xml
    └── snippets.xml
```

## Soporte

Para soporte técnico, contacta con el equipo de desarrollo.

## Licencia

Este módulo está bajo la licencia LGPL-3.
