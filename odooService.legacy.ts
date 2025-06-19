import axios from 'axios';

// TypeScript interfaces
export interface Customer {
  id: number;
  name: string;
  email: string;
  phone: string;
  city: string;
  country: string;
  status: string;
}

export interface Provider {
  id: number;
  name: string;
  tax_calculation_method: string;
  discount_type: string;
  payment_term: string;
  incentive_rules?: string;
  status: string;
}

export interface Product {
  id: number;
  name: string;
  code: string;
  category: string;
  price: number;
  stock: number;
  image_url: string;
}

export interface Sale {
  id: number;
  reference: string;
  customer: string;
  date: string;
  total: number;
  status: string;
}

export interface CategoryData {
  name: string;
  percentage: number;
}

export interface DashboardStats {
  totalProducts: number;
  lowStock: number;
  salesThisMonth: number;
  activeCustomers: number;
  topCategories: CategoryData[];
}

class OdooService {
  private apiUrl: string;
  private token: string | null = null;
  private refreshToken: string | null = null;
  private isAuthenticated: boolean = false;

  constructor() {
    this.apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    this.token = localStorage.getItem('token') || '';
    this.refreshToken = localStorage.getItem('refreshToken') || '';
    // Verificar si hay un token válido
    this.isAuthenticated = !!this.token;
  }

  async login(username: string, password: string): Promise<boolean> {
    try {
      const formData = new FormData();
      formData.append('username', username);
      formData.append('password', password);

      const response = await axios.post(`${this.apiUrl}/token`, formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });

      if (response.data.access_token) {
        this.token = response.data.access_token;
        this.isAuthenticated = true;
        // Guardar token en localStorage
        if (this.token) {
          localStorage.setItem('token', this.token);
        }
        if (response.data.refresh_token) {
          this.refreshToken = response.data.refresh_token;
          if (this.refreshToken) {
            localStorage.setItem('refreshToken', this.refreshToken);
          }
        }
        return true;
      }
      return false;
    } catch (error) {
      console.error('Error en el servicio de login:', error);
      return false;
    }
  }

  logout(): void {
    this.token = null;
    this.isAuthenticated = false;
    // Limpiar localStorage
    localStorage.removeItem('token');
    localStorage.removeItem('refreshToken');
  }

  private getAuthHeaders() {
    return {
      'Authorization': `Bearer ${this.token || ''}`,
      'Content-Type': 'application/json',
    };
  }

  async getProducts(limit: number = 10): Promise<Product[]> {
    try {
      const response = await axios.get(`${this.apiUrl}/api/v1/products`, {
        headers: this.getAuthHeaders(),
      });
      return response.data;
    } catch (error) {
      console.error('Error obteniendo productos:', error);
      return [];
    }
  }

  async getInventory(limit: number = 10): Promise<Product[]> {
    try {
      const response = await axios.get(`${this.apiUrl}/api/v1/inventory`, {
        headers: this.getAuthHeaders(),
      });
      return response.data;
    } catch (error) {
      console.error('Error obteniendo inventario:', error);
      return [];
    }
  }

  async getSales(limit: number = 10): Promise<Sale[]> {
    try {
      const response = await axios.get(`${this.apiUrl}/api/v1/sales`, {
        headers: this.getAuthHeaders(),
      });
      return response.data;
    } catch (error) {
      console.error('Error obteniendo ventas:', error);
      return [];
    }
  }

  async getCustomers(limit: number = 10): Promise<Customer[]> {
    try {
      const response = await axios.get(`${this.apiUrl}/api/v1/customers`, {
        headers: this.getAuthHeaders(),
      });
      return response.data;
    } catch (error) {
      console.error('Error obteniendo clientes:', error);
      return [];
    }
  }

  async getProviders(limit: number = 10): Promise<Provider[]> {
    try {
      const response = await axios.get(`${this.apiUrl}/api/v1/providers`, {
        headers: this.getAuthHeaders(),
      });
      return response.data;
    } catch (error) {
      console.error('Error obteniendo proveedores:', error);
      return [];
    }
  }

  async createProvider(provider: Omit<Provider, 'id'>): Promise<Provider | null> {
    try {
      const response = await axios.post(`${this.apiUrl}/api/v1/providers`, provider, {
        headers: this.getAuthHeaders(),
      });
      return response.data;
    } catch (error) {
      console.error('Error creando proveedor:', error);
      return null;
    }
  }

  async updateProvider(id: number, provider: Partial<Provider>): Promise<Provider | null> {
    try {
      const response = await axios.put(`${this.apiUrl}/api/v1/providers/${id}`, provider, {
        headers: this.getAuthHeaders(),
      });
      return response.data;
    } catch (error) {
      console.error('Error actualizando proveedor:', error);
      return null;
    }
  }

  async deleteProvider(id: number): Promise<boolean> {
    try {
      await axios.delete(`${this.apiUrl}/api/v1/providers/${id}`, {
        headers: this.getAuthHeaders(),
      });
      return true;
    } catch (error) {
      console.error('Error eliminando proveedor:', error);
      return false;
    }
  }

  async createProduct(product: Omit<Product, 'id'>): Promise<Product | null> {
    try {
      const response = await axios.post(`${this.apiUrl}/api/v1/products`, product, {
        headers: this.getAuthHeaders(),
      });
      return response.data;
    } catch (error) {
      console.error('Error creando producto:', error);
      return null;
    }
  }

  async updateProduct(id: number, product: Partial<Product>): Promise<Product | null> {
    try {
      const response = await axios.put(`${this.apiUrl}/api/v1/products/${id}`, product, {
        headers: this.getAuthHeaders(),
      });
      return response.data;
    } catch (error) {
      console.error('Error actualizando producto:', error);
      return null;
    }
  }

  async deleteProduct(id: number): Promise<boolean> {
    try {
      await axios.delete(`${this.apiUrl}/api/v1/products/${id}`, {
        headers: this.getAuthHeaders(),
      });
      return true;
    } catch (error) {
      console.error('Error eliminando producto:', error);
      return false;
    }
  }

  async getDashboardStats(): Promise<DashboardStats> {
    try {
      const response = await axios.get(`${this.apiUrl}/api/v1/dashboard/stats`, {
        headers: this.getAuthHeaders(),
      });
      return response.data;
    } catch (error) {
      console.error('Error obteniendo estadísticas del dashboard:', error);
      return {
        totalProducts: 0,
        lowStock: 0,
        salesThisMonth: 0,
        activeCustomers: 0,
        topCategories: []
      };
    }
  }
}

export const odooService = new OdooService();