import { ThemeConfig, theme } from 'antd';

export const darkTheme: ThemeConfig = {
  token: {
    colorPrimary: '#1890ff',
    colorBgBase: '#141414',
    colorBgContainer: '#1f1f1f',
    colorBgElevated: '#1f1f1f',
    colorText: '#ffffff',
    colorTextSecondary: '#d9d9d9',
    colorBorder: '#303030',
    borderRadius: 6,
  },
  components: {
    Layout: {
      bodyBg: '#141414',
      headerBg: '#1f1f1f',
      siderBg: '#1f1f1f',
    },
    Menu: {
      darkItemBg: '#1f1f1f',
      darkItemHoverBg: '#303030',
      darkItemSelectedBg: '#1890ff',
    },
    Table: {
      headerBg: '#1f1f1f',
      headerColor: '#ffffff',
      colorText: '#ffffff',
      colorTextHeading: '#ffffff',
      rowHoverBg: '#303030',
      borderColor: '#303030',
      colorBgContainer: '#1f1f1f',
      colorFillAlter: '#1f1f1f',
      colorFillContent: '#ffffff',
    },
    Card: {
      colorBgContainer: '#1f1f1f',
    },
  },
  algorithm: theme.darkAlgorithm,
};
