import { ThemeConfig, theme } from 'antd';

/**
 * Tema oscuro unificado para El Pelotazo ERP
 * 
 * Este tema centraliza todas las personalizaciones de color y estilo
 * para mantener una apariencia consistente en toda la aplicación.
 */
export const darkTheme: ThemeConfig = {
  // Tokens globales de diseño
  token: {
    colorPrimary: '#1890ff',           // Color primario para botones y elementos destacados
    colorBgBase: '#141414',            // Color de fondo base para toda la aplicación
    colorBgContainer: '#1f1f1f',       // Color de fondo para contenedores (cards, tables)
    colorBgElevated: '#1f1f1f',        // Color de fondo para elementos elevados (modales, dropdowns)
    colorText: '#ffffff',              // Color de texto principal
    colorTextSecondary: '#d9d9d9',     // Color de texto secundario
    colorBorder: '#303030',            // Color de bordes
    borderRadius: 6,                   // Radio de borde para elementos
  },
  
  // Personalizaciones específicas por componente
  components: {
    Layout: {
      bodyBg: '#141414',               // Fondo del cuerpo principal
      headerBg: '#1f1f1f',             // Fondo del encabezado
      siderBg: '#1f1f1f',              // Fondo de la barra lateral
    },
    Menu: {
      darkItemBg: '#1f1f1f',           // Fondo de elementos del menú
      darkItemHoverBg: '#303030',      // Fondo al pasar el cursor sobre elementos del menú
      darkItemSelectedBg: '#1890ff',   // Fondo de elemento seleccionado en el menú
    },
    Table: {
      headerBg: '#1f1f1f',             // Fondo del encabezado de tabla
      headerColor: '#ffffff',          // Color del texto del encabezado
      colorText: '#ffffff',            // Color del texto en celdas
      colorTextHeading: '#ffffff',     // Color del texto de encabezados
      rowHoverBg: '#303030',           // Fondo al pasar el cursor sobre filas
      borderColor: '#303030',          // Color de bordes de tabla
      colorBgContainer: '#1f1f1f',     // Fondo del contenedor de tabla
      colorFillAlter: '#1f1f1f',       // Color alterno para filas
      colorFillContent: '#ffffff',     // Color de relleno para contenido
    },
    Card: {
      colorBgContainer: '#1f1f1f',     // Fondo de tarjetas
    },
    Button: {
      defaultColor: '#ffffff',         // Color de texto para botones por defecto
      defaultBg: '#1f1f1f',            // Fondo para botones por defecto
      defaultBorderColor: '#303030',   // Color de borde para botones por defecto
    },
    Modal: {
      contentBg: '#1f1f1f',            // Fondo del contenido de modales
      headerBg: '#1f1f1f',             // Fondo del encabezado de modales
      titleColor: '#ffffff',           // Color del título de modales
    },
    Input: {
      colorBgContainer: '#141414',     // Fondo de inputs
      colorBorder: '#303030',          // Borde de inputs
      colorText: '#ffffff',            // Color de texto en inputs
    },
    Select: {
      colorBgContainer: '#141414',     // Fondo de selects
      colorBorder: '#303030',          // Borde de selects
      optionSelectedBg: '#303030',     // Fondo de opción seleccionada
    },
    Form: {
      labelColor: '#ffffff',           // Color de etiquetas de formulario
    }
  },
  
  // Usa el algoritmo de tema oscuro de Ant Design como base
  algorithm: theme.darkAlgorithm,
};
