import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';
import { message } from 'antd';

// Extender AxiosRequestConfig para incluir la propiedad _retry
interface ExtendedAxiosRequestConfig extends AxiosRequestConfig {
  _retry?: boolean;
}

// TypeScript interfaces mejoradas
export interface Customer {
  id: number;
  name: string;
  email: string;
  phone: string;
  address: string;
  total_purchases: number;
}

export interface Provider {
  id: number;
  name: string;
  email?: string;
  phone?: string;
  mobile?: string;
  vat?: string;  // NIF/CIF
  website?: string;
  street?: string;
  street2?: string;
  city?: string;
  zip?: string;
  country?: string;
  supplier_rank: number;
  is_company: boolean;
  active: boolean;
  ref?: string;  // Referencia interna
  comment?: string;  // Notas internas
}

export interface Product {
  id: number;
  name: string;
  default_code: string | null;
  list_price: number;
  standard_price: number;
  categ_id: number | null;
  barcode: string | null;
  active: boolean;
  type: string;
  weight: number;
  sale_ok: boolean;
  purchase_ok: boolean;
  available_in_pos: boolean;
  to_weight: boolean;
  is_published: boolean;
  website_sequence: number;
  description_sale: string | null;
  description_purchase: string | null;
  seller_ids: any[];
  product_tag_ids: any[];
  public_categ_ids: any[];
  pos_categ_ids: any[];
  taxes_id: any[];
  supplier_taxes_id: any[];
  // Campos opcionales que pueden o no venir
  code?: string | null;
  price?: number;
  category?: string | null;
  stock?: number | null;
  image_url?: string | null;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface ApiError {
  message: string;
  status: number;
  details?: any;
}

class OdooService {
  private apiClient: AxiosInstance;
  private token: string | null = null;
  private isAuthenticated: boolean = false;

  constructor() {
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    
    this.apiClient = axios.create({
      baseURL: apiUrl,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
    this.loadTokenFromStorage();
  }

  private setupInterceptors(): void {
    this.apiClient.interceptors.request.use(
      (config: any) => {
        if (this.token && config.headers) {
          config.headers.Authorization = `Bearer ${this.token}`;
        }
        return config;
      },
      (error: AxiosError) => {
        return Promise.reject(error);
      }
    );

    this.apiClient.interceptors.response.use(
      (response: AxiosResponse) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as ExtendedAxiosRequestConfig;
        if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
          originalRequest._retry = true;
          try {
            // Implement token refresh logic if available, otherwise logout
            this.logout();
            window.location.href = '/login';
          } catch (refreshError) {
            return Promise.reject(refreshError);
          }
        }
        return Promise.reject(this.formatError(error));
      }
    );
  }

  private formatError(error: AxiosError): ApiError {
    const errorData = error.response?.data as any;
    return {
      message: errorData?.detail || error.message || 'Error desconocido',
      status: error.response?.status || 500,
      details: error.response?.data
    };
  }

  private loadTokenFromStorage(): void {
    const storedToken = localStorage.getItem('odoo_token');
    if (storedToken) {
      this.token = storedToken;
      this.isAuthenticated = true;
    }
  }

  private saveTokenToStorage(token: string): void {
    localStorage.setItem('odoo_token', token);
    this.token = token;
    this.isAuthenticated = true;
  }

  private clearTokenFromStorage(): void {
    localStorage.removeItem('odoo_token');
    this.token = null;
    this.isAuthenticated = false;
  }

  async login(username: string, password: string): Promise<boolean> {
    try {
      const formData = new FormData();
      formData.append('username', username);
      formData.append('password', password);

      const response = await this.apiClient.post('/token', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });

      if (response.data.access_token) {
        this.saveTokenToStorage(response.data.access_token);
        return true;
      }
      return false;
    } catch (error) {
      console.error('Error en el servicio de login:', error);
      return false;
    }
  }

  logout(): void {
    this.clearTokenFromStorage();
  }

  async getProducts(page: number = 1, limit: number = 10, sortBy: string = 'id', sortOrder: 'asc' | 'desc' = 'asc', search: string = ''): Promise<PaginatedResponse<Product>> {
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        size: limit.toString(),
        sort_by: sortBy,
        sort_order: sortOrder,
        search: search,
      });

      const response = await this.apiClient.get<PaginatedResponse<Product>>(`/api/v1/products?${params.toString()}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching products:', error);
      return { data: [], total: 0, page, limit, pages: 0 };
    }
  }

  async createProduct(productData: Partial<Product>): Promise<Product> {
    try {
      const response = await this.apiClient.post<Product>('/api/v1/products', productData);
      message.success('Producto creado exitosamente');
      return response.data;
    } catch (error) {
      const apiError = this.formatError(error as AxiosError);
      message.error(`Error al crear producto: ${apiError.message}`);
      throw apiError;
    }
  }

  async updateProduct(id: number, productData: Partial<Product>): Promise<Product> {
    try {
      const response = await this.apiClient.put<Product>(`/api/v1/products/${id}`, productData);
      message.success('Producto actualizado exitosamente');
      return response.data;
    } catch (error) {
      const apiError = this.formatError(error as AxiosError);
      message.error(`Error al actualizar producto: ${apiError.message}`);
      throw apiError;
    }
  }

  async deleteProduct(id: number): Promise<void> {
    try {
      await this.apiClient.delete(`/api/v1/products/${id}`);
      message.success('Producto archivado exitosamente');
    } catch (error) {
      const apiError = this.formatError(error as AxiosError);
      message.error(`Error al archivar producto: ${apiError.message}`);
      throw apiError;
    }
  }

  isLoggedIn(): boolean {
    return this.isAuthenticated && !!this.token;
  }
}

// Exportar instancia singleton
export const odooService = new OdooService();
