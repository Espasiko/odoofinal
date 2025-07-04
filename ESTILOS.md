# Guía Completa de Estilos en ManusOdoo

Este documento proporciona una explicación detallada sobre cómo funcionan los estilos CSS en el proyecto ManusOdoo, por qué puede ser desafiante modificar la apariencia, y cómo abordar cambios de estilo de manera efectiva.

## Índice

1. [Arquitectura de Estilos](#arquitectura-de-estilos)
2. [Jerarquía y Cascada CSS](#jerarquía-y-cascada-css)
3. [Sistema de Temas](#sistema-de-temas)
4. [Componentes y Estilos Encapsulados](#componentes-y-estilos-encapsulados)
5. [Estrategias para Modificar Estilos](#estrategias-para-modificar-estilos)
6. [Casos de Uso Comunes](#casos-de-uso-comunes)
7. [Solución de Problemas](#solución-de-problemas)
8. [Estrategias de Simplificación de Estilos](#estrategias-de-simplificación-de-estilos)

## Arquitectura de Estilos

El proyecto ManusOdoo utiliza un sistema de estilos multicapa que combina diferentes metodologías:

### 1. Estilos Inline en Componentes React

Gran parte de la estilización se realiza directamente en los componentes JSX usando el atributo `style`. Este enfoque proporciona la mayor especificidad y es útil para estilos específicos de componentes.

```tsx
// Ejemplo de estilos inline en sider.tsx
<AntdSider width={260} style={{ 
  background: '#1f1f1f', 
  minHeight: '100vh', 
  position: 'fixed', 
  left: 0, 
  top: 0 
}}>
```

**Ventajas**: Alta especificidad, fácil de asociar estilos con componentes específicos
**Desventajas**: Difícil de reutilizar, mezcla lógica y presentación

### 2. Hojas de Estilo Globales

El archivo `src/index.css` contiene reglas CSS globales que afectan a toda la aplicación. Estas reglas establecen estilos base y ajustes generales.

```css
/* Ejemplo de src/index.css */
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', /* ... */;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  overflow-x: hidden;
}

.ant-layout-content {
  overflow-x: hidden;
  padding: 16px;
  margin-left: 0;
  transition: margin-left 0.2s;
}
```

**Ventajas**: Estilos consistentes en toda la aplicación
**Desventajas**: Baja especificidad, pueden ser sobrescritos fácilmente

### 3. Sistema de Temas de Ant Design

El proyecto utiliza Ant Design como biblioteca de componentes, que viene con su propio sistema de temas. El tema se configura a través de `ConfigProvider` en `App.tsx`:

```tsx
// En App.tsx
<ConfigProvider theme={darkTheme}>
  {/* Contenido de la aplicación */}
</ConfigProvider>
```

El tema personalizado se define en `darkTheme.ts`:

```tsx
// En darkTheme.ts
export const darkTheme: ThemeConfig = {
  algorithm: theme.darkAlgorithm,
  token: {
    colorPrimary: '#00b96b',
    borderRadius: 6,
    // Más configuraciones de token...
  },
  components: {
    Table: {
      colorText: '#ffffff',
      // Más configuraciones específicas de componentes...
    },
    // Otros componentes...
  }
};
```

**Ventajas**: Cambios globales consistentes, integración perfecta con componentes Ant Design
**Desventajas**: Limitado a las variables de tema disponibles, no todos los estilos son configurables a través del tema

### 4. Props de Tema en Componentes

Algunos componentes de Ant Design aceptan props específicas de tema que cambian su apariencia:

```tsx
// En sider.tsx
<Menu
  theme="dark"
  selectedKeys={[location.pathname]}
  mode="inline"
  // ...
/>
```

**Ventajas**: API simple para cambios de tema a nivel de componente
**Desventajas**: Opciones limitadas (generalmente solo "light" o "dark")

### 5. Framework Refine

El proyecto utiliza Refine como framework, que aporta sus propios estilos y componentes. Estos pueden interactuar con los estilos de Ant Design y los personalizados.

## Jerarquía y Cascada CSS

La dificultad para modificar estilos a menudo proviene de la cascada CSS y las reglas de especificidad. En orden de mayor a menor prioridad:

1. **Estilos inline** (`style={...}`) - Mayor especificidad
2. **Estilos de ID** (`#header`) - Muy alta especificidad, raramente usados en este proyecto
3. **Estilos de clase, atributos y pseudo-clases** (`.ant-menu`, `[type="button"]`, `:hover`)
4. **Estilos de elemento** (`div`, `span`)
5. **Estilos heredados** - Menor especificidad

La estructura de componentes anidados también afecta a cómo los estilos se aplican y se heredan:

```
App
├── ConfigProvider (tema global)
│   └── Layout
│       ├── Sider
│       │   └── Menu
│       │       └── MenuItem
│       ├── Header
│       └── Content
│           └── Componentes de página (Products, etc.)
```

## Sistema de Temas

### Tema Oscuro Personalizado

El proyecto utiliza un tema oscuro personalizado definido en `darkTheme.ts`. Este tema modifica el algoritmo base de tema oscuro de Ant Design y personaliza tokens específicos:

```tsx
export const darkTheme: ThemeConfig = {
  algorithm: theme.darkAlgorithm,
  token: {
    colorPrimary: '#00b96b',  // Color principal
    borderRadius: 6,          // Radio de borde para componentes
    // Más configuraciones...
  },
  components: {
    // Configuraciones específicas por componente
    Table: {
      colorText: '#ffffff',
      // ...
    }
  }
};
```

### Aplicación del Tema

El tema se aplica globalmente a través de `ConfigProvider` en `App.tsx`. Esto afecta a todos los componentes Ant Design en la aplicación.

## Componentes y Estilos Encapsulados

### Encapsulamiento en Ant Design

Ant Design encapsula muchos de sus estilos dentro de sus componentes, lo que puede hacer que sean difíciles de sobrescribir. Algunos componentes proporcionan props específicas para estilización:

```tsx
// En Drawer.tsx
<Drawer
  // ...
  styles={{ 
    body: { padding: 0, background: '#1f1f1f' } 
  }}
>
```

### Selectores CSS Generados

Ant Design genera selectores CSS dinámicamente basados en la estructura de componentes. Estos selectores pueden ser complejos y difíciles de sobrescribir:

```css
/* Ejemplo de selector generado por Ant Design */
.ant-table-wrapper .ant-table-thead > tr > th {
  /* Estilos para encabezados de tabla */
}
```

## Estrategias para Modificar Estilos

### 1. Modificación del Tema Global

Para cambios consistentes en toda la aplicación, modifique el tema en `darkTheme.ts`:

```tsx
export const darkTheme: ThemeConfig = {
  // ...
  token: {
    colorPrimary: '#00b96b',  // Cambie a su color primario deseado
    // ...
  },
  components: {
    Button: {
      colorPrimary: '#00b96b',  // Específico para botones
    },
    // ...
  }
};
```

### 2. Sobrescritura con Estilos Inline

Para componentes específicos, use estilos inline para garantizar la mayor especificidad:

```tsx
<Button type="primary" style={{ backgroundColor: '#custom-color' }}>
  Botón Personalizado
</Button>
```

### 3. Clases CSS Personalizadas

Para estilos más complejos o reutilizables, considere añadir clases CSS personalizadas con alta especificidad:

```css
/* En un archivo CSS */
.my-custom-component .ant-btn-primary {
  background-color: #custom-color !important;
}
```

```tsx
<div className="my-custom-component">
  <Button type="primary">Botón Personalizado</Button>
</div>
```

### 4. Props Específicas de Componentes

Utilice las props de estilo específicas que ofrecen los componentes:

```tsx
<Table 
  columns={columns} 
  dataSource={data}
  rowClassName={() => 'custom-row'}
/>
```

## Casos de Uso Comunes

### Cambiar Colores de Fondo

Como vimos en las recientes modificaciones del sidebar, para cambiar el color de fondo:

```tsx
// Para Drawer
<Drawer
  // ...
  styles={{ body: { padding: 0, background: '#1f1f1f' } }}
>

// Para Sider
<AntdSider style={{ background: '#1f1f1f', /* ... */ }}>
```

### Mejorar Legibilidad de Texto

Para cambiar colores de texto en tablas:

```tsx
// En columnas de tabla
{
  title: 'Precio',
  dataIndex: 'price',
  render: (price) => (
    <span style={{ color: '#ffffff' }}>
      €{price}
    </span>
  )
}
```

### Ajustar Márgenes y Espaciado

Para resolver problemas de superposición o espaciado:

```tsx
<Layout
  style={{
    marginLeft: isMobile ? 0 : 260,
    transition: 'margin-left 0.3s',
  }}
>
```

## Solución de Problemas

### Inspección de Elementos

Use las herramientas de desarrollo del navegador para inspeccionar elementos y ver qué reglas CSS se están aplicando:

1. Haga clic derecho en el elemento y seleccione "Inspeccionar"
2. Examine la pestaña "Styles" para ver las reglas CSS aplicadas
3. Observe qué reglas están siendo sobrescritas (tachadas)

### Sobrescritura Forzada

Cuando sea absolutamente necesario, use `!important` para forzar la aplicación de una regla:

```css
.my-critical-style {
  color: white !important;
}
```

**Nota**: Use `!important` con moderación, ya que puede dificultar el mantenimiento futuro.

### Conflictos Comunes

Los problemas más frecuentes incluyen:

1. **Especificidad insuficiente**: Use selectores más específicos o estilos inline
2. **Orden de carga CSS**: Asegúrese de que sus estilos personalizados se carguen después de los de Ant Design
3. **Props específicas sobrescribiendo estilos**: Algunas props como `type="primary"` en Button tienen prioridad sobre ciertos estilos

## Estrategias de Simplificación de Estilos

El sistema actual de estilos puede simplificarse sin romper la apariencia, siguiendo estas recomendaciones:

### 1. Centralización de Variables y Estilos

Crear un archivo de estilos centralizado que defina todas las variables de color, espaciado y tipografía:

```tsx
// src/styles/theme.ts
export const appColors = {
  background: '#1f1f1f',
  text: '#ffffff',
  primary: '#00b96b',
  secondary: '#888888',
  // Más colores...
};

export const appStyles = {
  sider: {
    background: appColors.background,
    minHeight: '100vh',
    position: 'fixed',
    left: 0,
    top: 0,
  },
  // Más estilos reutilizables...
};
```

Luego importar y usar estos estilos en los componentes:

```tsx
import { appColors, appStyles } from './src/styles/theme';

// Luego en componentes
<AntdSider width={260} style={appStyles.sider}>
```

### 2. Migración a CSS Modules

Para una mejor encapsulación de estilos, considere migrar gradualmente a CSS Modules:

```css
/* Sider.module.css */
.sider {
  background: #1f1f1f;
  min-height: 100vh;
  position: fixed;
  left: 0;
  top: 0;
}
```

```tsx
import styles from './Sider.module.css';

<AntdSider width={260} className={styles.sider}>
```

### 3. Implementación de Styled Components

Alternativamente, para una mejor integración con React:

```tsx
import styled from 'styled-components';
import { Layout } from 'antd';
const { Sider: AntdSider } = Layout;

const StyledSider = styled(AntdSider)`
  background: #1f1f1f;
  min-height: 100vh;
  position: fixed;
  left: 0;
  top: 0;
`;

// Luego en el componente
<StyledSider width={260}>
```

### 4. Reemplazo Gradual

La migración debe ser gradual:

1. Comenzar por centralizar variables de color y dimensiones
2. Refactorizar un componente a la vez
3. Mantener compatibilidad con componentes existentes
4. Priorizar componentes más utilizados o problemáticos

### 5. Herencia de Temas

Leverage el sistema de temas de Ant Design para minimizar estilos personalizados:

```tsx
// Extender el tema oscuro con configuraciones personalizadas
export const darkTheme: ThemeConfig = {
  algorithm: theme.darkAlgorithm,
  token: {
    colorBgBase: '#1f1f1f',
    // Más configuraciones globales
  },
}
```

Esta estrategia reduce considerablemente la duplicación de código, mejora el mantenimiento y facilita cambios futuros sin afectar la apariencia actual.

## Conclusión

Comprender la interacción entre las múltiples capas de estilos en ManusOdoo es clave para modificar efectivamente la apariencia de la aplicación. Este documento proporciona las bases para navegar y modificar el sistema de estilos del proyecto.

Recuerde que los cambios de estilo deben ser probados exhaustivamente en diferentes tamaños de pantalla para garantizar una experiencia de usuario consistente y responsiva.

---

Última actualización: 2025-07-03
