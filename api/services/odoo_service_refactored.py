from typing import List, Optional
from .odoo_product_service import OdooProductService
from .odoo_provider_service import OdooProviderService
from .odoo_customer_service import OdooCustomerService
from .odoo_sales_service import OdooSalesService
from ..models.schemas import (
    Product, ProductCreate, Provider, ProviderCreate,
    Customer, CustomerCreate, Sale, SaleCreate
)

class OdooServiceRefactored:
    """Servicio principal de Odoo que coordina todos los servicios especializados"""
    
    def __init__(self):
        self.product_service = OdooProductService()
        self.provider_service = OdooProviderService()
        self.customer_service = OdooCustomerService()
        self.sales_service = OdooSalesService()
    
    # Métodos de productos
    def get_products(self, offset=0, limit=100) -> List[Product]:
        """Obtiene productos desde Odoo"""
        return self.product_service.get_products(offset, limit)
    
    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """Obtiene un producto específico por ID"""
        return self.product_service.get_product_by_id(product_id)
    
    def create_product(self, product_data: ProductCreate) -> Optional[Product]:
        """Crea un nuevo producto en Odoo"""
        return self.product_service.create_product(product_data)
    
    def get_product_count(self) -> int:
        """Obtiene el número total de productos"""
        return self.product_service.get_product_count()
    
    # Métodos de proveedores
    def get_providers(self, offset=0, limit=100) -> List[Provider]:
        """Obtiene proveedores desde Odoo"""
        return self.provider_service.get_providers(offset, limit)
    
    def get_supplier_by_name(self, name: str) -> Optional[Provider]:
        """Busca un proveedor por nombre"""
        return self.provider_service.get_supplier_by_name(name)
    
    def create_supplier(self, supplier_data: ProviderCreate) -> Optional[Provider]:
        """Crea un nuevo proveedor en Odoo"""
        return self.provider_service.create_supplier(supplier_data)
    
    # Métodos de clientes
    def get_customers(self, offset=0, limit=100) -> List[Customer]:
        """Obtiene clientes desde Odoo"""
        return self.customer_service.get_customers(offset, limit)
    
    def get_customer_by_id(self, customer_id: int) -> Optional[Customer]:
        """Obtiene un cliente específico por ID"""
        return self.customer_service.get_customer_by_id(customer_id)
    
    def create_customer(self, customer_data: CustomerCreate) -> Optional[Customer]:
        """Crea un nuevo cliente en Odoo"""
        return self.customer_service.create_customer(customer_data)
    
    # Métodos de ventas
    def get_sales(self, offset=0, limit=100) -> List[Sale]:
        """Obtiene ventas desde Odoo"""
        return self.sales_service.get_sales(offset, limit)
    
    def create_sale(self, sale_data: SaleCreate) -> Optional[Sale]:
        """Crea una nueva venta en Odoo"""
        return self.sales_service.create_sale(sale_data)
    
    # Método create_invoice removido temporalmente hasta definir el modelo Invoice
    
    # Métodos de utilidad
    def cleanup_all_connections(self):
        """Limpia todas las conexiones de los servicios"""
        self.product_service._cleanup_connection()
        self.provider_service._cleanup_connection()
        self.customer_service._cleanup_connection()
        self.sales_service._cleanup_connection()
    
    def get_category_name(self, categ_id):
        """Obtiene el nombre de una categoría"""
        return self.product_service._get_category_name(categ_id)