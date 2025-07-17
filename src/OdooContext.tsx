import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import axios from 'axios';

import type { AxiosInstance, AxiosError } from 'axios';

interface AuthContextType {
  auth: { accessToken: string; refreshToken: string } | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => void;
  api: AxiosInstance;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// helper para obtener token utilizando credenciales default/env
async function fetchTokenRequest() {
  const response = await axios.post(`${API_URL}/token`, {
    username: import.meta.env.VITE_ODOO_USERNAME || 'admin',
    password: import.meta.env.VITE_ODOO_PASSWORD || 'admin',
  }, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  });
  return response.data as { access_token: string; refresh_token: string };
}

interface AuthProviderProps {
  children: ReactNode;
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const OdooProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const axiosInstance = React.useMemo(() => axios.create({ baseURL: API_URL }), []);
  const [auth, setAuth] = useState<{ accessToken: string; refreshToken: string } | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);

  useEffect(() => {
    const obtainToken = async () => {
      try {
        const response = await axios.post(`${API_URL}/token`, {
          username: import.meta.env.VITE_ODOO_USERNAME || 'admin',
          password: import.meta.env.VITE_ODOO_PASSWORD || 'admin',
        }, {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
        });
        const newToken = response.data.access_token;
        const newRefreshToken = response.data.refresh_token;
        
        setAuth({
          accessToken: newToken,
          refreshToken: newRefreshToken,
        });
        setIsAuthenticated(true);
        localStorage.setItem('accessToken', newToken);
        localStorage.setItem('refreshToken', newRefreshToken);
        
        // Configurar el token en los headers de Axios
        axiosInstance.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
        console.log('Token obtenido y configurado automáticamente');
      } catch (error) {
        console.error('Error fetching token:', error);
        setIsAuthenticated(false);
      }
    };

    const storedAccessToken = localStorage.getItem('accessToken');
    const storedRefreshToken = localStorage.getItem('refreshToken');
    if (storedAccessToken && storedRefreshToken) {
      setAuth({
        accessToken: storedAccessToken,
        refreshToken: storedRefreshToken,
      });
      setIsAuthenticated(true);
      // Configurar el token en los headers de Axios al cargar un token existente
      axiosInstance.defaults.headers.common['Authorization'] = `Bearer ${storedAccessToken}`;
      console.log('Token configurado desde localStorage');
    } else {
      obtainToken();
    }
  }, []);

  const login = async (username: string, password: string): Promise<boolean> => {
    try {
      const response = await axios.post(`${API_URL}/token`, {
        username,
        password,
      }, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });
      setAuth({
        accessToken: response.data.access_token,
        refreshToken: response.data.refresh_token,
      });
      setIsAuthenticated(true);
      localStorage.setItem('accessToken', response.data.access_token);
      localStorage.setItem('refreshToken', response.data.refresh_token);
      axiosInstance.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`;
      return true;
    } catch (error) {
      console.error('Error al iniciar sesión:', error);
      setIsAuthenticated(false);
      return false;
    }
  };

  const logout = () => {
    delete axiosInstance.defaults.headers.common['Authorization'];
    setAuth(null);
    setIsAuthenticated(false);
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
  };

  // actualizar header cuando cambia auth
  useEffect(() => {
    if (auth?.accessToken) {
      axiosInstance.defaults.headers.common['Authorization'] = `Bearer ${auth.accessToken}`;
    }
  }, [auth, axiosInstance]);

  // interceptor para renovar token en 401
  useEffect(() => {
    const id = axiosInstance.interceptors.response.use(
      (res) => res,
      async (error: AxiosError) => {
        if (error.response?.status === 401 && !(error.config as any)._retry) {
          try {
            console.log('Interceptor: Detectado error 401, intentando renovar token...');
            (error.config as any)._retry = true;
            
            // Guardar el config original para reintentarlo después
            const originalConfig = error.config!;
            
            // Intentar obtener un nuevo token
            const formData = new FormData();
            formData.append('username', import.meta.env.VITE_ODOO_USERNAME || 'admin');
            formData.append('password', import.meta.env.VITE_ODOO_PASSWORD || 'admin');
            
            const tokenResponse = await axios.post(
              `${API_URL}/token`,
              formData,
              { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
            );
            
            const newToken = tokenResponse.data.access_token;
            const newRefreshToken = tokenResponse.data.refresh_token;
            
            console.log('Interceptor: Token renovado exitosamente');
            
            // Actualizar estado y localStorage
            setAuth({ accessToken: newToken, refreshToken: newRefreshToken });
            localStorage.setItem('accessToken', newToken);
            localStorage.setItem('refreshToken', newRefreshToken);
            
            // Actualizar headers para futuras peticiones
            axiosInstance.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
            
            // Actualizar header en la petición original
            if (originalConfig.headers) {
              (originalConfig.headers as any)['Authorization'] = `Bearer ${newToken}`;
            }
            
            // Reintentar la petición original con el nuevo token
            return axiosInstance(originalConfig);
          } catch (e) {
            console.error('Interceptor: Error al renovar token:', e);
            logout();
            return Promise.reject(error);
          }
        }
        return Promise.reject(error);
      }
    );
    return () => axiosInstance.interceptors.response.eject(id);
  }, [axiosInstance]);

  return (
    <AuthContext.Provider value={{ auth, isAuthenticated, login, logout, api: axiosInstance }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useOdoo = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useOdoo debe ser utilizado dentro de un OdooProvider');
  }
  return context;
};
