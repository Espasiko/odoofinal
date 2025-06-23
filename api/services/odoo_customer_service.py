from typing import List, Optional
from .odoo_base_service import OdooBaseService
from ..models.schemas import Customer, CustomerCreate

class OdooCustomerService(OdooBaseService):
    """Servicio para gestión de clientes en Odoo"""
    
    def get_customers(self, offset=0, limit=100) -> List[Customer]:
        """Obtiene clientes desde Odoo"""
        try:
            if not self._models:
                self._get_connection()
        
            print(f"ODOO_SERVICE: Obteniendo clientes de Odoo con offset {offset} y límite {limit}...")
            odoo_customers = self._execute_kw(
                'res.partner',
                'search_read',
                [[['customer_rank', '>', 0]]],
                {'offset': offset, 'limit': limit, 'fields': [
                    'id', 'name', 'email', 'phone', 'mobile', 'website',
                    'street', 'street2', 'city', 'state_id', 'zip', 'country_id',
                    'vat', 'supplier_rank', 'customer_rank', 'is_company',
                    'category_id', 'comment', 'active'
                ]}
            )
            print(f"ODOO_SERVICE: Datos obtenidos: {len(odoo_customers) if odoo_customers else 0} clientes")
        
            if not odoo_customers:
                print("ODOO_SERVICE: No se pudieron leer datos, usando fallback")
                return self._get_fallback_customers()
        
            # Transformar a formato esperado
            print("ODOO_SERVICE: Transformando datos...")
            transformed_customers = []
            for c in odoo_customers:
                # Manejar state_id y country_id que pueden venir como [id, name]
                state_name = ''
                if c.get('state_id'):
                    if isinstance(c['state_id'], list) and len(c['state_id']) > 1:
                        state_name = c['state_id'][1]
                    elif isinstance(c['state_id'], str):
                        state_name = c['state_id']
                
                country_name = ''
                if c.get('country_id'):
                    if isinstance(c['country_id'], list) and len(c['country_id']) > 1:
                        country_name = c['country_id'][1]
                    elif isinstance(c['country_id'], str):
                        country_name = c['country_id']
                
                # Asegurar que los campos de texto sean strings
                email = c.get('email') or ''
                if email is False:
                    email = ''
                
                phone = c.get('phone') or ''
                if phone is False:
                    phone = ''
                
                mobile = c.get('mobile') or ''
                if mobile is False:
                    mobile = ''
                
                website = c.get('website') or ''
                if website is False:
                    website = ''
                
                street = c.get('street') or ''
                if street is False:
                    street = ''
                
                street2 = c.get('street2') or ''
                if street2 is False:
                    street2 = ''
                
                city = c.get('city') or ''
                if city is False:
                    city = ''
                
                zip_code = c.get('zip') or ''
                if zip_code is False:
                    zip_code = ''
                
                vat = c.get('vat') or ''
                if vat is False:
                    vat = ''
                
                comment = c.get('comment') or ''
                if comment is False:
                    comment = ''
                
                transformed_customers.append(Customer(
                    id=c.get('id'),
                    name=c.get('name', ''),
                    email=email,
                    phone=phone,
                    mobile=mobile,
                    website=website,
                    street=street,
                    street2=street2,
                    city=city,
                    state=state_name,
                    zip=zip_code,
                    country=country_name,
                    vat=vat,
                    supplier_rank=c.get('supplier_rank', 0),
                    customer_rank=c.get('customer_rank', 0),
                    is_company=c.get('is_company', False),
                    category_id=c.get('category_id', []),
                    comment=comment,
                    active=c.get('active', True)
                ))
        
            print(f"ODOO_SERVICE: Clientes transformados: {len(transformed_customers)}")
            return transformed_customers
        except Exception as e:
            print(f"ODOO_SERVICE: Error obteniendo clientes: {str(e)}")
            return self._get_fallback_customers()
    
    def get_customer_by_id(self, customer_id: int) -> Optional[Customer]:
        """Obtiene un cliente específico por ID"""
        try:
            customers = self._execute_kw(
                'res.partner',
                'read',
                [customer_id],
                {'fields': ['id', 'name', 'email', 'phone', 'mobile', 'website',
                           'street', 'street2', 'city', 'state_id', 'zip', 'country_id',
                           'vat', 'supplier_rank', 'customer_rank', 'is_company',
                           'category_id', 'comment', 'active']}
            )
            
            if customers:
                c = customers[0]
                
                # Manejar state_id y country_id
                state_name = ''
                if c.get('state_id'):
                    if isinstance(c['state_id'], list) and len(c['state_id']) > 1:
                        state_name = c['state_id'][1]
                    elif isinstance(c['state_id'], str):
                        state_name = c['state_id']
                
                country_name = ''
                if c.get('country_id'):
                    if isinstance(c['country_id'], list) and len(c['country_id']) > 1:
                        country_name = c['country_id'][1]
                    elif isinstance(c['country_id'], str):
                        country_name = c['country_id']
                
                return Customer(
                    id=c['id'],
                    name=c['name'],
                    email=c.get('email', ''),
                    phone=c.get('phone', ''),
                    mobile=c.get('mobile', ''),
                    website=c.get('website', ''),
                    street=c.get('street', ''),
                    street2=c.get('street2', ''),
                    city=c.get('city', ''),
                    state=state_name,
                    zip=c.get('zip', ''),
                    country=country_name,
                    vat=c.get('vat', ''),
                    supplier_rank=c.get('supplier_rank', 0),
                    customer_rank=c.get('customer_rank', 0),
                    is_company=c.get('is_company', False),
                    category_id=c.get('category_id', []),
                    comment=c.get('comment', ''),
                    active=c.get('active', True)
                )
            return None
            
        except Exception as e:
            print(f"Error obteniendo cliente {customer_id}: {e}")
            return None
    
    def create_customer(self, customer_data: CustomerCreate) -> Optional[Customer]:
        """Crea un nuevo cliente en Odoo"""
        try:
            # Preparar datos del cliente
            vals = {
                'name': customer_data.name,
                'is_company': customer_data.is_company if customer_data.is_company is not None else False,
                'supplier_rank': 0,
                'customer_rank': 1,
                'email': customer_data.email or '',
                'phone': customer_data.phone or '',
                'mobile': customer_data.mobile or '',
                'website': customer_data.website or '',
                'street': customer_data.street or '',
                'street2': customer_data.street2 or '',
                'city': customer_data.city or '',
                'zip': customer_data.zip or '',
                'vat': customer_data.vat or '',
                'comment': customer_data.comment or '',
                'active': customer_data.active if customer_data.active is not None else True
            }
            
            # Crear cliente
            customer_id = self._execute_kw(
                'res.partner',
                'create',
                [vals]
            )
            
            if customer_id:
                # Obtener el cliente creado
                return self.get_customer_by_id(customer_id)
            else:
                print("Error: No se pudo crear el cliente")
                return None
                
        except Exception as e:
            print(f"Error creando cliente: {e}")
            return None
    
    def _get_fallback_customers(self) -> List[Customer]:
        """Datos de clientes de respaldo"""
        return [
            Customer(
                id=1,
                name="Juan Pérez García",
                email="juan.perez@email.com",
                phone="+34 123 456 789",
                mobile="+34 987 654 321",
                website="",
                street="Calle Mayor 123",
                street2="Piso 3, Puerta B",
                city="Madrid",
                state="Madrid",
                zip="28001",
                country="España",
                vat="12345678Z",
                supplier_rank=0,
                customer_rank=1,
                is_company=False,
                category_id=[],
                comment="Cliente frecuente",
                active=True
            ),
            Customer(
                id=2,
                name="Empresa Tecnológica S.L.",
                email="info@empresatech.com",
                phone="+34 234 567 890",
                mobile="+34 876 543 210",
                website="https://www.empresatech.com",
                street="Polígono Industrial 456",
                street2="Nave 12",
                city="Barcelona",
                state="Barcelona",
                zip="08001",
                country="España",
                vat="ESB87654321",
                supplier_rank=0,
                customer_rank=1,
                is_company=True,
                category_id=[],
                comment="Cliente corporativo",
                active=True
            )
        ]