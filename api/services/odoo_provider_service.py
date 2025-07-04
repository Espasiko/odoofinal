from typing import List, Optional
from .odoo_base_service import OdooBaseService
from ..models.schemas import Provider, ProviderCreate

class OdooProviderService(OdooBaseService):
    """Servicio para gestión de proveedores en Odoo"""

    def get_paginated_providers(self, page: int = 1, limit: int = 10, search_term: str | None = None):
        """Obtiene proveedores paginados y el total"""
        import logging
        logger = logging.getLogger("odoo_provider_service.paginated")
        logger.info(f"--- get_paginated_providers page={page} limit={limit} ---")
        offset = (page - 1) * limit
        try:
            all_providers = self.get_providers(offset=0, limit=10000)
            logger.info(f"Total proveedores obtenidos de Odoo: {len(all_providers)}")
            paginated = all_providers[offset:offset+limit]
            total = len(all_providers)
            logger.info(f"Proveedores devueltos: {len(paginated)} (offset={offset})")
            return paginated, total
        except Exception as e:
            logger.error(f"EXCEPCIÓN CRÍTICA en get_paginated_providers: {e}", exc_info=True)
            return [], 0
    
    def get_providers(self, offset: int = 0, limit: int = 100, search_term: str | None = None) -> List[Provider]:
        """Obtiene proveedores desde Odoo"""
        try:
            if not self._models:
                self._get_connection()
        
            print(f"ODOO_SERVICE: Obteniendo proveedores de Odoo con offset {offset} y límite {limit}...")
            # Construir dominio de búsqueda dinámico
            domain = [['is_company', '=', True], ['supplier_rank', '>', 0]]
            if search_term:
                domain.append(['name', 'ilike', search_term])
            odoo_providers = self._execute_kw(
                'res.partner',
                'search_read',
                [domain],
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

                # Saneamiento de campos que pueden ser False en lugar de None o string vacío
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
                    id=p['id'],
                    name=p.get('name', 'N/A'),
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
                    is_company=p.get('is_company', False),
                    category_id=p.get('category_id', []),
                    comment=comment,
                    active=p.get('active', False)
                ))
            print("ODOO_SERVICE: Transformación completada.")
            return transformed_providers
        except Exception as e:
            print(f"ODOO_SERVICE: Error conectando a Odoo o procesando datos: {e}")
            return self._get_fallback_providers()

    def get_provider_by_id(self, provider_id: int) -> Optional[Provider]:
        """Obtiene un proveedor específico por su ID directamente desde Odoo"""
        import logging
        logger = logging.getLogger("odoo_provider_service.get_provider_by_id")
        try:
            if not self._models:
                self._get_connection()

            result = self._execute_kw(
                'res.partner',
                'read',
                [[provider_id]],
                {'fields': [
                    'id', 'name', 'email', 'phone', 'mobile', 'website',
                    'street', 'street2', 'city', 'state_id', 'zip', 'country_id',
                    'vat', 'supplier_rank', 'customer_rank', 'is_company',
                    'category_id', 'comment', 'active'
                ]}
            )
            if not result:
                return None
            p = result[0]
            # Procesar campos anidados como en get_providers
            state_name = ''
            if p.get('state_id'):
                state_name = p['state_id'][1] if isinstance(p['state_id'], list) and len(p['state_id']) > 1 else p['state_id']
            country_name = ''
            if p.get('country_id'):
                country_name = p['country_id'][1] if isinstance(p['country_id'], list) and len(p['country_id']) > 1 else p['country_id']

            return Provider(
                id=p['id'],
                name=p.get('name', 'N/A'),
                email=p.get('email') or '',
                phone=p.get('phone') or '',
                mobile=p.get('mobile') or '',
                website=p.get('website') or '',
                street=p.get('street') or '',
                street2=p.get('street2') or '',
                city=p.get('city') or '',
                state=state_name,
                zip=p.get('zip') or '',
                country=country_name,
                vat=p.get('vat') or '',
                supplier_rank=p.get('supplier_rank', 0),
                customer_rank=p.get('customer_rank', 0),
                is_company=p.get('is_company', False),
                category_id=p.get('category_id', []),
                comment=p.get('comment') or '',
                active=p.get('active', False)
            )
        except Exception as e:
            logger.error(f"Error obteniendo proveedor {provider_id}: {e}")
            return None

    # Alias para mantener compatibilidad con interfaz anterior
    def create_provider(self, supplier_data):
        return self.create_supplier(supplier_data)

    def create_supplier(self, supplier_data) -> Optional[Provider]:
        """
        Crea un nuevo proveedor en Odoo.
        Acepta un Pydantic model ProviderCreate o un dict.
        Sanea los campos de string que puedan ser False o None a "".
        """
        import logging
        logger = logging.getLogger("odoo_provider_service.create_supplier")

        try:
            if isinstance(supplier_data, ProviderCreate):
                data = supplier_data.dict()
            elif isinstance(supplier_data, dict):
                data = supplier_data
            else:
                raise ValueError("El formato de datos del proveedor no es válido.")

            # --- Comprobación de duplicados ---
            vat_value = data.get('vat')
            existing_ids: list = []
            if vat_value:
                existing_ids = self._execute_kw('res.partner', 'search', [[['vat', '=', vat_value], ['is_company', '=', True], ['supplier_rank', '>', 0]]]) or []
            if not existing_ids and data.get('name'):
                # Búsqueda aproximada por nombre si no hay VAT o no se encontró coincidencia
                existing_ids = self._execute_kw('res.partner', 'search', [[['name', 'ilike', data['name']], ['is_company', '=', True], ['supplier_rank', '>', 0]]]) or []

            if existing_ids:
                logger.info(f"Proveedor duplicado detectado, id existente: {existing_ids[0]}. No se crea uno nuevo.")
                return existing_ids[0]

            # Saneamiento de campos string
            all_string_fields = [
                'name', 'email', 'phone', 'comment', 'vat', 'website', 'mobile', 'street', 'street2', 'city', 'zip'
            ]
            for k in all_string_fields:
                if k in data and (data[k] is False or data[k] is None):
                    data[k] = ""
            
            # Mapeo de claves del frontend (español) a Odoo (inglés) si es necesario
            field_mapping = {
                "nombre": "name",
                "correo_electronico": "email",
                "telefono": "phone",
                "nif": "vat",
                "sitio_web": "website",
                "movil": "mobile",
                "calle": "street",
                "calle2": "street2",
                "ciudad": "city",
                "codigo_postal": "zip",
                "comentarios": "comment",
                "activo": "active"
            }
            
            # Normalizar el diccionario de datos usando el mapeo
            normalized_data = {}
            for key, value in data.items():
                odoo_key = field_mapping.get(key, key)
                normalized_data[odoo_key] = value

            # Construir el diccionario de valores para Odoo
            vals = {}
            all_fields = [
                'name', 'email', 'phone', 'comment', 'vat', 'website', 'mobile',
                'street', 'street2', 'city', 'zip',
                'active', 'is_company', 'supplier_rank', 'customer_rank'
            ]

            for field in all_fields:
                if field in normalized_data and normalized_data[field] is not None:
                    vals[field] = normalized_data[field]

            # Establecer valores por defecto para campos clave si no se proporcionan
            vals.setdefault('is_company', True)
            vals.setdefault('supplier_rank', 1)
            vals.setdefault('customer_rank', 0)
            vals.setdefault('active', True)

            # Validar que el nombre no esté vacío
            if not vals.get('name'):
                logger.error("Error al crear proveedor: el campo 'name' es obligatorio.")
                return None
            
            logger.info(f"Creando proveedor en Odoo con valores: {vals}")
            provider_id = self._execute_kw('res.partner', 'create', [vals])
            
            if not provider_id:
                logger.error("Error: Odoo no devolvió un ID para el nuevo proveedor.")
                return None

            logger.info(f"Proveedor creado con ID: {provider_id}. Leyendo datos de vuelta...")
            
            # Leer el proveedor recién creado para devolver el objeto completo
            created_provider_data = self._execute_kw('res.partner', 'read', [provider_id], {'fields': list(vals.keys())})
            
            if not created_provider_data:
                logger.error(f"No se pudo leer el proveedor con ID {provider_id} después de crearlo.")
                return None
            
            # Devolver como instancia del modelo Provider
            return Provider(**created_provider_data[0])

        except Exception as e:
            logger.error(f"Error creando proveedor: {e}")
            return None

    def update_provider(self, provider_id: int, update_data: dict) -> Optional[Provider]:
        """
        Actualiza un proveedor existente en Odoo. Sanea campos como create_supplier.
        """
        import logging
        logger = logging.getLogger("odoo_provider_service.update_provider")
        try:
            # Saneo de campos string
            all_string_fields = [
                'name', 'email', 'phone', 'comment', 'vat', 'website', 'mobile', 'street', 'street2', 'city', 'zip'
            ]
            for k in all_string_fields:
                if k in update_data and (update_data[k] is False or update_data[k] is None):
                    update_data[k] = ""

            # Preparar vals solo con campos que vienen en la petición
            vals = {}
            updatable_fields = [
                'name', 'email', 'phone', 'comment', 'vat', 'website', 'mobile',
                'street', 'street2', 'city', 'zip',
                'active', 'is_company', 'supplier_rank', 'customer_rank'
            ]

            for field in updatable_fields:
                if field in update_data:
                    vals[field] = update_data[field]

            # Actualizar en Odoo
            self._execute_kw('res.partner', 'write', [[provider_id], vals])

            # Leer el proveedor actualizado y devolverlo
            provider = self._execute_kw('res.partner', 'read', [[provider_id]], {'fields': list(vals.keys())})
            if provider:
                return Provider(**provider[0])
            return None
        except Exception as e:
            logger.error(f"Error actualizando proveedor {provider_id}: {e}")
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
    def get_paginated_providers(self, page: int = 1, limit: int = 10, search_term: str | None = None):
        """Devuelve tupla (lista_proveedores, total) con paginación real o simulada"""
        # Calcular desplazamiento
        offset = (page - 1) * limit if limit else 0
        # Obtener lote
        providers = self.get_providers(offset=offset, limit=limit, search_term=search_term)
        try:
            total = self._execute_kw(
                'res.partner',
                'search_count',
                [[['is_company', '=', True], ['supplier_rank', '>', 0]]]
            )
            if total is None:
                total = len(providers)
        except Exception:
            # En caso de error de conexión, usar longitud del lote
            total = len(providers)
        return providers, total

# Instancia global del servicio
odoo_provider_service = OdooProviderService()
