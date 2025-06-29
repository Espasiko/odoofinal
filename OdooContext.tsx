import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import axios from 'axios';

interface AuthContextType {
  auth: { accessToken: string; refreshToken: string } | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const OdooProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [auth, setAuth] = useState<{ accessToken: string; refreshToken: string } | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);

  useEffect(() => {
    const fetchToken = async () => {
      try {
        const response = await axios.post(`${API_URL}/token`, {
          username: import.meta.env.VITE_ODOO_USERNAME || 'yo@mail.com',
          password: import.meta.env.VITE_ODOO_PASSWORD || 'admin',
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
    } else {
      fetchToken();
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
      return true;
    } catch (error) {
      console.error('Error al iniciar sesión:', error);
      setIsAuthenticated(false);
      return false;
    }
  };

  const logout = () => {
    setAuth(null);
    setIsAuthenticated(false);
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
  };

  return (
    <AuthContext.Provider value={{ auth, isAuthenticated, login, logout }}>
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
