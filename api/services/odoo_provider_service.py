from typing import List, Optional
from .odoo_base_service import OdooBaseService
from ..models.schemas import Provider, ProviderCreate

class OdooProviderService(OdooBaseService):
    """Servicio para gestión de proveedores en Odoo"""
    
    def get_providers(self, offset=0, limit=100) -> List[Provider]:
        """Obtiene proveedores desde Odoo"""
        try:
            if not self._models:
                self._get_connection()
        
            print(f"ODOO_SERVICE: Obteniendo proveedores de Odoo con offset {offset} y límite {limit}...")
            odoo_providers = self._execute_kw(
                'res.partner',
                'search_read',
                [[['is_company', '=', True], ['supplier_rank', '>', 0]]],
                {'offset': offset, 'limit': limit, 'fields': [
                    'id', 'name', 'email', 'phone', 'mobile', 'website',
                    'street', 'street2', 'city', 'state_id', 'zip', 'country_id',
                    'vat', 'supplier_rank', 'customer_rank', 'is_company',
                    'category_id', 'comment', 'active'
                ]}
            )
            print(f"ODOO_SERVICE: Datos obtenidos: {len(odoo_providers) if odoo_providers else 0} proveedores")
        
            if not odoo_providers:
                print("ODOO_SERVICE: No se pudieron leer datos, usando fallback")
                return self._get_fallback_providers()
        
            # Transformar a formato esperado
            print("ODOO_SERVICE: Transformando datos...")
            transformed_providers = []
            for p in odoo_providers:
                # Manejar state_id y country_id que pueden venir como [id, name]
                state_name = ''
                if p.get('state_id'):
                    if isinstance(p['state_id'], list) and len(p['state_id']) > 1:
                        state_name = p['state_id'][1]
                    elif isinstance(p['state_id'], str):
                        state_name = p['state_id']
                
                country_name = ''
                if p.get('country_id'):
                    if isinstance(p['country_id'], list) and len(p['country_id']) > 1:
                        country_name = p['country_id'][1]
                    elif isinstance(p['country_id'], str):
                        country_name = p['country_id']
                
                # Asegurar que los campos de texto sean strings
                email = p.get('email') or ''
                if email is False:
                    email = ''
                
                phone = p.get('phone') or ''
                if phone is False:
                    phone = ''
                
                mobile = p.get('mobile') or ''
                if mobile is False:
                    mobile = ''
                
                website = p.get('website') or ''
                if website is False:
                    website = ''
                
                street = p.get('street') or ''
                if street is False:
                    street = ''
                
                street2 = p.get('street2') or ''
                if street2 is False:
                    street2 = ''
                
                city = p.get('city') or ''
                if city is False:
                    city = ''
                
                zip_code = p.get('zip') or ''
                if zip_code is False:
                    zip_code = ''
                
                vat = p.get('vat') or ''
                if vat is False:
                    vat = ''
                
                comment = p.get('comment') or ''
                if comment is False:
                    comment = ''
                
                transformed_providers.append(Provider(
                    id=p.get('id'),
                    name=p.get('name', ''),
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
                    supplier_rank=p.get('supplier_rank', 0),
                    customer_rank=p.get('customer_rank', 0),
                    is_company=p.get('is_company', True),
                    category_id=p.get('category_id', []),
                    comment=comment,
                    active=p.get('active', True)
                ))
        
            print(f"ODOO_SERVICE: Proveedores transformados: {len(transformed_providers)}")
            return transformed_providers
        except Exception as e:
            print(f"ODOO_SERVICE: Error obteniendo proveedores: {str(e)}")
            return self._get_fallback_providers()
    
    def get_supplier_by_name(self, name: str) -> Optional[Provider]:
        """Busca un proveedor por nombre"""
        try:
            suppliers = self._execute_kw(
                'res.partner',
                'search_read',
                [[['name', 'ilike', name], ['supplier_rank', '>', 0]]],
                {'fields': ['id', 'name', 'email', 'phone', 'vat'], 'limit': 1}
            )
            
            if suppliers:
                s = suppliers[0]
                return Provider(
                    id=s['id'],
                    name=s['name'],
                    email=s.get('email', ''),
                    phone=s.get('phone', ''),
                    vat=s.get('vat', ''),
                    supplier_rank=1,
                    is_company=True,
                    active=True
                )
            return None
            
        except Exception as e:
            print(f"Error buscando proveedor {name}: {e}")
            return None
    
    def create_supplier(self, supplier_data: ProviderCreate) -> Optional[Provider]:
        """Crea un nuevo proveedor en Odoo"""
        try:
            # Preparar datos del proveedor
            vals = {
                'name': supplier_data.name,
                'is_company': True,
                'supplier_rank': 1,
                'customer_rank': 0,
                'email': supplier_data.email or '',
                'phone': supplier_data.phone or '',
                'mobile': supplier_data.mobile or '',
                'website': supplier_data.website or '',
                'street': supplier_data.street or '',
                'street2': supplier_data.street2 or '',
                'city': supplier_data.city or '',
                'zip': supplier_data.zip or '',
                'vat': supplier_data.vat or '',
                'comment': supplier_data.comment or '',
                'active': supplier_data.active if supplier_data.active is not None else True
            }
            
            # Crear proveedor
            supplier_id = self._execute_kw(
                'res.partner',
                'create',
                [vals]
            )
            
            if supplier_id:
                # Obtener el proveedor creado
                created_supplier = self._execute_kw(
                    'res.partner',
                    'read',
                    [supplier_id],
                    {'fields': ['id', 'name', 'email', 'phone', 'mobile', 'website',
                               'street', 'street2', 'city', 'zip', 'vat', 'comment', 'active']}
                )
                
                if created_supplier:
                    s = created_supplier[0]
                    return Provider(
                        id=s['id'],
                        name=s['name'],
                        email=s.get('email', ''),
                        phone=s.get('phone', ''),
                        mobile=s.get('mobile', ''),
                        website=s.get('website', ''),
                        street=s.get('street', ''),
                        street2=s.get('street2', ''),
                        city=s.get('city', ''),
                        zip=s.get('zip', ''),
                        vat=s.get('vat', ''),
                        comment=s.get('comment', ''),
                        supplier_rank=1,
                        customer_rank=0,
                        is_company=True,
                        active=s.get('active', True)
                    )
            
            print("Error: No se pudo crear el proveedor")
            return None
                
        except Exception as e:
            print(f"Error creando proveedor: {e}")
            return None
    
    def _get_fallback_providers(self) -> List[Provider]:
        """Datos de proveedores de respaldo"""
        return [
            Provider(
                id=1,
                name="Proveedor Ejemplo S.L.",
                email="contacto@proveedor1.com",
                phone="+34 123 456 789",
                mobile="+34 987 654 321",
                website="https://www.proveedor1.com",
                street="Calle Principal 123",
                street2="Piso 2, Oficina A",
                city="Madrid",
                state="Madrid",
                zip="28001",
                country="España",
                vat="ESB12345678",
                supplier_rank=1,
                customer_rank=0,
                is_company=True,
                category_id=[],
                comment="Proveedor principal de electrónicos",
                active=True
            ),
            Provider(
                id=2,
                name="Distribuciones Norte S.A.",
                email="ventas@distribnorte.com",
                phone="+34 234 567 890",
                mobile="+34 876 543 210",
                website="https://www.distribnorte.com",
                street="Avenida Industrial 456",
                street2="Nave 15",
                city="Barcelona",
                state="Barcelona",
                zip="08001",
                country="España",
                vat="ESA87654321",
                supplier_rank=1,
                customer_rank=0,
                is_company=True,
                category_id=[],
                comment="Especialistas en productos para el hogar",
                active=True
            )
        ]

# Instancia global del servicio
odoo_provider_service = OdooProviderService()