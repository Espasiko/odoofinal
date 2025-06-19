import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';

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
  // Campos legacy para compatibilidad
  tax_calculation_method?: string;
  discount_type?: string;
  payment_term?: string;
  incentive_rules?: string;
  status?: string;
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
  customer_id: number;
  customer_name: string;
  product_id: number;
  product_name: string;
  quantity: number;
  unit_price: number;
  total: number;
  date: string;
  status: string;
}

export interface InventoryItem {
  id: number;
  product_id: [number, string]; // [id, name] del producto
  location_id: [number, string]; // [id, name] de la ubicación
  quantity: number;
  lot_id?: [number, string] | null; // [id, name] del lote (opcional)
  package_id?: [number, string] | null; // [id, name] del paquete (opcional)
  owner_id?: [number, string] | null; // [id, name] del propietario (opcional)
  // Campos de compatibilidad
  product_name?: string; // Nombre del producto
  location?: string; // Nombre de la ubicación
  last_updated?: string; // Campo calculado
}

export interface CategoryData {
  name: string;
  percentage: number;
}

export interface DashboardStats {
  // Estadísticas básicas
  totalProducts: number;
  totalSales: number;
  totalCustomers: number;
  totalProviders: number;
  pendingOrders: number;
  monthlyRevenue: number;
  
  // Estadísticas de productos
  productStats: {
    totalActive: number;
    totalInactive: number;
    totalCategories: number;
    averagePrice: number;
    totalValue: number;
  };
  
  // Estadísticas de ventas
  salesStats: {
    todaySales: number;
    weekSales: number;
    monthSales: number;
    yearSales: number;
    averageOrderValue: number;
  };
  
  // Estadísticas de stock
  stockStats: {
    lowStockProducts: number;
    outOfStockProducts: number;
    totalStockValue: number;
    averageStockLevel: number;
  };
  
  // Estadísticas de proveedores
  providerStats: {
    totalActive: number;
    totalInactive: number;
    averagePaymentTerm: number;
  };
  
  // Listas detalladas
  topCategories: Array<{
    id: number;
    name: string;
    productCount: number;
    totalValue: number;
    percentage: number;
  }>;
  
  recentSales: Array<{
    id: number;
    customerName: string;
    productName: string;
    quantity: number;
    unitPrice: number;
    total: number;
    date: string;
    status: string;
  }>;
  
  lowStockProducts: Array<{
    id: number;
    name: string;
    currentStock: number;
    minimumStock: number;
    category: string;
    price: number;
  }>;
  
  topSellingProducts: Array<{
    id: number;
    name: string;
    totalSold: number;
    revenue: number;
    category: string;
  }>;
  
  recentCustomers: Array<{
    id: number;
    name: string;
    email: string;
    totalPurchases: number;
    lastPurchase: string;
  }>;
  
  recentProviders: Array<{
    id: number;
    name: string;
    email: string;
    totalProducts: number;
    lastUpdate: string;
  }>;
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

export interface SessionResponse {
  uid: number;
  username: string;
  name: string;
  session_id: string;
  db: string;
}

class OdooService {
  private apiClient: AxiosInstance;
  private token: string | null = null;
  private isAuthenticated: boolean = false;
  private refreshPromise: Promise<string> | null = null;

  constructor() {
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    
    // Crear instancia de axios con configuración base
    this.apiClient = axios.create({
      baseURL: apiUrl,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Configurar interceptores
    this.setupInterceptors();
    
    // Cargar token desde localStorage
    this.loadTokenFromStorage();
  }

  private setupInterceptors(): void {
    // Interceptor de request - agregar token automáticamente
    this.apiClient.interceptors.request.use(
      (config: any) => {
        if (this.token && config.headers) {
          config.headers.Authorization = `Bearer ${this.token}`;
        }
        
        // Log de requests en desarrollo
        if (import.meta.env.DEV) {
          console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`);
        }
        
        return config;
      },
      (error: AxiosError) => {
        console.error('❌ Request Error:', error);
        return Promise.reject(error);
      }
    );

    // Interceptor de response - manejo de errores y refresh token
    this.apiClient.interceptors.response.use(
      (response: AxiosResponse) => {
        // Log de responses exitosas en desarrollo
        if (import.meta.env.DEV) {
          console.log(`✅ API Response: ${response.status} ${response.config.url}`);
        }
        return response;
      },
      async (error: AxiosError) => {
        const originalRequest = error.config as ExtendedAxiosRequestConfig;
        
        // Manejo de error 401 - token expirado
        if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
          originalRequest._retry = true;
          
          try {
            // Intentar refrescar el token
            await this.refreshAuthToken();
            
            // Reintentar la request original
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${this.token}`;
            }
            
            return this.apiClient(originalRequest);
          } catch (refreshError) {
            // Si el refresh falla, logout
            this.logout();
            window.location.href = '/login';
            return Promise.reject(refreshError);
          }
        }
        
        // Log de errores
        const errorData = error.response?.data as any;
        console.error('❌ API Error:', {
          status: error.response?.status,
          message: errorData?.detail || error.message,
          url: error.config?.url
        });
        
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

  private async refreshAuthToken(): Promise<string> {
    // Evitar múltiples requests de refresh simultáneos
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    this.refreshPromise = this.performTokenRefresh();
    
    try {
      const newToken = await this.refreshPromise;
      return newToken;
    } finally {
      this.refreshPromise = null;
    }
  }

  private async performTokenRefresh(): Promise<string> {
    // En lugar de refresh token, hacemos login automático con credenciales por defecto
    try {
      const loginData = {
        username: 'admin',
        password: 'admin_password_secure'
      };
      
      const response = await axios.post(`${this.apiClient.defaults.baseURL}/token`, 
        new URLSearchParams({
          username: loginData.username,
          password: loginData.password
        }),
        {
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded'
          }
        }
      );
      
      const { access_token } = response.data;
       this.token = access_token;
       this.isAuthenticated = true;
       this.saveTokenToStorage(access_token);
       return access_token;
    } catch (error) {
      console.error('Error en performTokenRefresh:', error);
      throw new Error('Failed to refresh token');
    }
  }

  // Métodos públicos
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

  isLoggedIn(): boolean {
    return this.isAuthenticated && !!this.token;
  }

  async getSession(): Promise<SessionResponse> {
    const response = await this.apiClient.get<SessionResponse>('/api/v1/auth/session');
    return response.data;
  }

  // Métodos de productos
  async getProducts(): Promise<Product[]>;
  async getProducts(params: { page: number; limit: number; search?: string }): Promise<PaginatedResponse<Product>>;
  async getProducts(params?: { page: number; limit: number; search?: string }): Promise<Product[] | PaginatedResponse<Product>> {
    if (!params) {
      const response = await this.apiClient.get<Product[]>('/api/v1/products/all');
      return response.data;
    }
    const response = await this.apiClient.get<PaginatedResponse<Product>>('/api/v1/products', {
      params
    });
    return response.data;
  }

  async getProduct(id: number): Promise<Product> {
    const response = await this.apiClient.get<Product>(`/api/v1/products/${id}`);
    return response.data;
  }

  async createProduct(product: Omit<Product, 'id'>): Promise<Product> {
    const response = await this.apiClient.post<Product>('/api/v1/products', product);
    return response.data;
  }

  async updateProduct(id: number, product: Partial<Product>): Promise<Product> {
    const response = await this.apiClient.put<Product>(`/api/v1/products/${id}`, product);
    return response.data;
  }

  async deleteProduct(id: number): Promise<boolean> {
    try {
      await this.apiClient.delete(`/api/v1/products/${id}`);
      return true;
    } catch (error) {
      console.error('Error deleting product:', error);
      return false;
    }
  }

  // Métodos de proveedores
  async getProviders(): Promise<Provider[]>;
  async getProviders(params: { page: number; limit: number; search?: string }): Promise<PaginatedResponse<Provider>>;
  async getProviders(params?: { page: number; limit: number; search?: string }): Promise<Provider[] | PaginatedResponse<Provider>> {
    if (!params) {
      const response = await this.apiClient.get<Provider[]>('/api/v1/providers/all');
      return response.data;
    }
    const response = await this.apiClient.get<PaginatedResponse<Provider>>('/api/v1/providers', {
      params
    });
    return response.data;
  }

  async getProvider(id: number): Promise<Provider> {
    const response = await this.apiClient.get<Provider>(`/api/v1/providers/${id}`);
    return response.data;
  }

  async createProvider(provider: Omit<Provider, 'id'>): Promise<Provider> {
    const response = await this.apiClient.post<Provider>('/api/v1/providers', provider);
    return response.data;
  }

  async updateProvider(id: number, provider: Partial<Provider>): Promise<Provider> {
    // Filtrar sólo los campos permitidos por ProviderUpdate
    const allowedFields = [
      'name',
      'tax_calculation_method',
      'discount_type',
      'payment_term',
      'incentive_rules',
      'status'
    ];
    const filteredProvider: any = {};
    for (const key of allowedFields) {
      if (provider[key as keyof Provider] !== undefined) {
        filteredProvider[key] = provider[key as keyof Provider];
      }
    }
    const response = await this.apiClient.put<Provider>(`/api/v1/providers/${id}`, filteredProvider);
    return response.data;
  }

  async deleteProvider(id: number): Promise<boolean> {
    try {
      await this.apiClient.delete(`/api/v1/providers/${id}`);
      return true;
    } catch (error) {
      console.error('Error deleting provider:', error);
      return false;
    }
  }

  // Métodos de inventario
  async getInventory(params: { page: number; limit: number; search?: string }): Promise<PaginatedResponse<InventoryItem>> {
    const response = await this.apiClient.get<PaginatedResponse<InventoryItem>>('/api/v1/inventory', {
      params
    });
    return response.data;
  }

  async getInventoryItem(id: number): Promise<InventoryItem> {
    const response = await this.apiClient.get<InventoryItem>(`/api/v1/inventory/${id}`);
    return response.data;
  }

  async createInventoryItem(item: Omit<InventoryItem, 'id'>): Promise<InventoryItem> {
    const response = await this.apiClient.post<InventoryItem>('/api/v1/inventory', item);
    return response.data;
  }

  async updateInventoryItem(id: number, item: Partial<InventoryItem>): Promise<InventoryItem> {
    const response = await this.apiClient.put<InventoryItem>(`/api/v1/inventory/${id}`, item);
    return response.data;
  }

  async deleteInventoryItem(id: number): Promise<void> {
    await this.apiClient.delete(`/api/v1/inventory/${id}`);
  }

  // Métodos de ventas
  async getSales(params: { page: number; limit: number; search?: string }): Promise<PaginatedResponse<Sale>> {
    const response = await this.apiClient.get<PaginatedResponse<Sale>>('/api/v1/sales', {
      params
    });
    return response.data;
  }

  async getSale(id: number): Promise<Sale> {
    const response = await this.apiClient.get<Sale>(`/api/v1/sales/${id}`);
    return response.data;
  }

  async createSale(sale: Omit<Sale, 'id'>): Promise<Sale> {
    const response = await this.apiClient.post<Sale>('/api/v1/sales', sale);
    return response.data;
  }

  async updateSale(id: number, sale: Partial<Sale>): Promise<Sale> {
    const response = await this.apiClient.put<Sale>(`/api/v1/sales/${id}`, sale);
    return response.data;
  }

  async deleteSale(id: number): Promise<void> {
    await this.apiClient.delete(`/api/v1/sales/${id}`);
  }

  // Métodos de clientes
  async getCustomers(params: { page: number; limit: number; search?: string }): Promise<PaginatedResponse<Customer>> {
    const response = await this.apiClient.get<PaginatedResponse<Customer>>('/api/v1/customers', {
      params
    });
    return response.data;
  }

  async getCustomerById(id: number): Promise<Customer> {
    const response = await this.apiClient.get<Customer>(`/api/v1/customers/${id}`);
    return response.data;
  }

  async createCustomer(customer: Omit<Customer, 'id'>): Promise<Customer> {
    const response = await this.apiClient.post<Customer>('/api/v1/customers', customer);
    return response.data;
  }

  async updateCustomer(id: number, customer: Partial<Customer>): Promise<Customer> {
    const response = await this.apiClient.put<Customer>(`/api/v1/customers/${id}`, customer);
    return response.data;
  }

  async deleteCustomer(id: number): Promise<void> {
    await this.apiClient.delete(`/api/v1/customers/${id}`);
  }

  // Métodos del dashboard
  async getDashboardStats(): Promise<DashboardStats> {
    const response = await this.apiClient.get<DashboardStats>('/api/v1/dashboard/stats');
    return response.data;
  }

  async getCategories(): Promise<{ categories: Array<{ id: number; name: string; count: number }> }> {
    const response = await this.apiClient.get('/api/v1/dashboard/categories');
    return response.data;
  }

  async getDashboardCategories(): Promise<CategoryData[]> {
    const response = await this.apiClient.get<{ categories: CategoryData[] }>('/api/v1/dashboard/categories');
    return response.data.categories;
  }
}

// Exportar instancia singleton
export const odooService = new OdooService();

// Exportar clase para testing
export { OdooService };
