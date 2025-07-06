# Guía de Estilos - El Pelotazo ERP

## Estructura Simplificada de Estilos

La aplicación utiliza un sistema de estilos simplificado que se basa en tres componentes principales:

### 1. Tema Centralizado (`darkTheme.ts`)

El archivo `darkTheme.ts` en la raíz del proyecto es el punto central para todas las personalizaciones de color y estilo. Este archivo configura el tema oscuro de Ant Design y define:

- Colores primarios y de fondo
- Estilos específicos para componentes (Layout, Menu, Table, Card, Button, etc.)
- Configuraciones de texto, bordes y otros elementos visuales

**Ventaja**: Al centralizar la configuración de estilos, se evita la duplicación y se facilita el mantenimiento.

### 2. Estilos Globales (`src/index.css`)

El archivo `src/index.css` contiene únicamente:

- Estilos básicos para elementos HTML (body, code, etc.)
- Ajustes responsivos que no pueden configurarse a través del tema
- Configuraciones específicas para el layout y contenedores

Se han eliminado todas las duplicaciones con `darkTheme.ts` para evitar conflictos.

### 3. Estilos Específicos de Componentes

Los componentes de Ant Design y React Refine aplican sus propios estilos, que son modificados por la configuración en `darkTheme.ts`.

## Cómo Realizar Cambios de Estilo

### Para cambios globales de color o tema:

1. Modifica el archivo `darkTheme.ts`
2. Busca la sección relevante (token o components)
3. Actualiza los valores manteniendo los comentarios explicativos

```typescript
// Ejemplo: Cambiar el color primario
token: {
  colorPrimary: '#1890ff', // Cambiar este valor
  // otros tokens...
}
```

### Para ajustes de layout o responsividad:

1. Modifica el archivo `src/index.css`
2. Mantén los cambios específicos de layout separados de los estilos de componentes

```css
/* Ejemplo: Ajustar padding en móvil */
@media (max-width: 768px) {
  .ant-layout-content {
    padding: 12px; /* Cambiar este valor */
  }
}
```

### Para estilos específicos de componentes:

Si necesitas personalizar un componente específico que no está cubierto por `darkTheme.ts`:

1. Primero intenta añadir la configuración al objeto `components` en `darkTheme.ts`
2. Si no es posible, añade estilos específicos en `src/index.css` con comentarios claros

## Buenas Prácticas

1. **Evita usar `!important`** a menos que sea absolutamente necesario
2. **Documenta** cualquier cambio de estilo con comentarios
3. **Prueba en diferentes tamaños de pantalla** para asegurar responsividad
4. **Mantén la coherencia** con el diseño existente

## Resolución de Problemas

Si encuentras problemas con los estilos:

1. Usa las herramientas de desarrollo del navegador para inspeccionar el elemento
2. Verifica la especificidad CSS y el orden de carga
3. Comprueba si hay estilos inline que puedan estar sobrescribiendo tus cambios
4. Asegúrate de que los cambios en `darkTheme.ts` se están aplicando correctamente

---

Esta guía fue creada para simplificar el mantenimiento de estilos en El Pelotazo ERP.
