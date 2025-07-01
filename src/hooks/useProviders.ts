import { useState, useEffect, useCallback } from 'react';
import { message } from 'antd';
import { odooService, Provider, PaginatedResponse } from '../services/odooService';

export interface UseProvidersReturn {
  providers: Provider[];
  loading: boolean;
  error: string | null;
  pagination: {
    current: number;
    pageSize: number;
    total: number;
  };
  fetchProviders: (page?: number, limit?: number) => Promise<void>;
  createProvider: (provider: Omit<Provider, 'id'>) => Promise<boolean>;
  updateProvider: (id: number, provider: Partial<Provider>) => Promise<boolean>;
  deleteProvider: (id: number) => Promise<boolean>;
  refreshProviders: () => Promise<void>;
}

export const useProviders = (): UseProvidersReturn => {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0,
    pages: 0,
  });

  const fetchProviders = useCallback(async (page: number = 1, limit: number = 10, search: string = '') => {
    setLoading(true);
    setError(null);
    
    try {
      const response: PaginatedResponse<Provider> = await odooService.getProviders(page, limit, search);
      setProviders(response.data);
      setPagination({
        current: response.page,
        pageSize: response.limit,
        total: response.total,
        pages: response.pages,
      });
    } catch (err: any) {
      const errorMessage = err.message || 'Error al cargar proveedores';
      setError(errorMessage);
      message.error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  const createProvider = useCallback(async (providerData: Omit<Provider, 'id'>): Promise<boolean> => {
    setLoading(true);
    
    try {
      const newProvider = await odooService.createProvider(providerData);
      
      if (newProvider) {
        message.success('Proveedor creado exitosamente');
        await refreshProviders();
        return true;
      } else {
        throw new Error('No se pudo crear el proveedor');
      }
    } catch (err: any) {
      const errorMessage = err.message || 'Error al crear proveedor';
      setError(errorMessage);
      message.error(errorMessage);
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  const updateProvider = useCallback(async (id: number, providerData: Partial<Provider>): Promise<boolean> => {
    setLoading(true);
    
    try {
      const updatedProvider = await odooService.updateProvider(id, providerData);
      
      if (updatedProvider) {
        message.success('Proveedor actualizado exitosamente');
        await refreshProviders();
        return true;
      } else {
        throw new Error('No se pudo actualizar el proveedor');
      }
    } catch (err: any) {
      const errorMessage = err.message || 'Error al actualizar proveedor';
      setError(errorMessage);
      message.error(errorMessage);
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  const deleteProvider = useCallback(async (id: number): Promise<boolean> => {
    setLoading(true);
    
    try {
      await odooService.deleteProvider(id);
      message.success('Proveedor eliminado exitosamente');
      await refreshProviders();
      return true;
    } catch (err: any) {
      const errorMessage = err.message || 'Error al eliminar proveedor';
      setError(errorMessage);
      message.error(errorMessage);
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  const refreshProviders = useCallback(async () => {
    await fetchProviders(pagination.current, pagination.pageSize);
  }, [fetchProviders, pagination.current, pagination.pageSize]);

  // Cargar proveedores al montar el componente
  useEffect(() => {
    fetchProviders();
  }, [fetchProviders]);

  return {
    providers,
    loading,
    error,
    pagination,
    fetchProviders,
    createProvider,
    updateProvider,
    deleteProvider,
    refreshProviders,
  };
};
