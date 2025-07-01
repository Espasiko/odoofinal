import { useState, useEffect, useCallback } from 'react';
import { message } from 'antd';
import { odooService, Product, PaginatedResponse } from '../services/odooService';

export interface UseProductsReturn {
  products: Product[];
  loading: boolean;
  error: string | null;
  totalProducts: number;
  currentPage: number;
  pageSize: number;
  searchTerm: string;
  setCurrentPage: (page: number) => void;
  setPageSize: (size: number) => void;
  setSearchTerm: (term: string) => void;
  refreshProducts: () => Promise<void>;
  createProduct: (productData: Omit<Product, 'id'>) => Promise<boolean>;
  updateProduct: (id: number, productData: Partial<Product>) => Promise<boolean>;
  deleteProduct: (id: number) => Promise<boolean>;
  getProductById: (id: number) => Promise<Product | null>;
}

export const useProducts = (): UseProductsReturn => {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [totalProducts, setTotalProducts] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [searchTerm, setSearchTerm] = useState('');

  const fetchProducts = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response: PaginatedResponse<Product> = await odooService.getProducts(currentPage, pageSize, 'id', 'asc', searchTerm || '');
      setProducts(response.data);
      setTotalProducts(response.total);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error al cargar productos';
      setError(errorMessage);
      message.error(errorMessage);
      console.error('Error fetching products:', err);
    } finally {
      setLoading(false);
    }
  };

  const refreshProducts = async () => {
    await fetchProducts();
  };

  const createProduct = async (productData: Omit<Product, 'id'>): Promise<boolean> => {
    try {
      setLoading(true);
      await odooService.createProduct(productData);
      message.success('Producto creado exitosamente');
      await fetchProducts(); // Refresh the list
      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error al crear producto';
      message.error(errorMessage);
      console.error('Error creating product:', err);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const updateProduct = async (id: number, productData: Partial<Product>): Promise<boolean> => {
    try {
      setLoading(true);
      await odooService.updateProduct(id, productData);
      message.success('Producto actualizado exitosamente');
      await fetchProducts(); // Refresh the list
      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error al actualizar producto';
      message.error(errorMessage);
      console.error('Error updating product:', err);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const deleteProduct = async (id: number): Promise<boolean> => {
    try {
      setLoading(true);
      await odooService.deleteProduct(id);
      message.success('Producto eliminado exitosamente');
      await fetchProducts(); // Refresh the list
      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error al eliminar producto';
      message.error(errorMessage);
      console.error('Error deleting product:', err);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const getProductById = async (id: number): Promise<Product | null> => {
    try {
      setLoading(true);
      const product = await odooService.getProduct(id);
      return product;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error al obtener producto';
      message.error(errorMessage);
      console.error('Error fetching product by id:', err);
      return null;
    } finally {
      setLoading(false);
    }
  };

  // Effect to fetch products when dependencies change
  useEffect(() => {
    fetchProducts();
  }, [currentPage, pageSize, searchTerm]);

  // Reset to first page when search term changes
  useEffect(() => {
    if (searchTerm !== '') {
      setCurrentPage(1);
    }
  }, [searchTerm]);

  return {
    products,
    loading,
    error,
    totalProducts,
    currentPage,
    pageSize,
    searchTerm,
    setCurrentPage,
    setPageSize,
    setSearchTerm,
    refreshProducts,
    createProduct,
    updateProduct,
    deleteProduct,
    getProductById
  };
};