from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from ..services.odoo_service import OdooService

router = APIRouter(prefix='/api/v1')

# Modelo para la respuesta de proveedores
class Provider(BaseModel):
    id: int
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    vat: Optional[str] = None
    website: Optional[str] = None
    street: Optional[str] = None
    street2: Optional[str] = None
    city: Optional[str] = None
    zip: Optional[str] = None
    country: Optional[str] = None
    supplier_rank: int
    is_company: bool
    active: bool
    ref: Optional[str] = None
    comment: Optional[str] = None

# Modelo para respuesta paginada
class PaginatedResponse(BaseModel):
    data: List[Provider]
    total: int
    page: int
    limit: int
    pages: int
    size: int

@router.get('/suppliers', response_model=PaginatedResponse)
async def get_suppliers(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None
):
    try:
        # Obtener instancia de OdooService
        odoo_service = OdooService()
        
        # Definir dominio de búsqueda
        domain = [['supplier_rank', '>', 0]]
        if search:
            domain.append(['name', 'ilike', f'%{search}%'])
        
        # Obtener proveedores desde Odoo
        suppliers = odoo_service._execute_kw(
            'res.partner',
            'search_read',
            [domain],
            {
                'fields': [
                    'id', 'name', 'email', 'phone', 'mobile', 'vat', 'website',
                    'street', 'street2', 'city', 'zip', 'country_id',
                    'supplier_rank', 'is_company', 'active', 'ref', 'comment'
                ],
                'offset': (page - 1) * limit,
                'limit': limit
            }
        )
        
        # Obtener total de proveedores para paginación
        total = odoo_service._execute_kw(
            'res.partner',
            'search_count',
            [domain]
        )
        
        # Mapear country_id a country si existe
        for supplier in suppliers:
            if supplier.get('country_id') and isinstance(supplier['country_id'], (list, tuple)) and len(supplier['country_id']) > 1:
                supplier['country'] = supplier['country_id'][1]
            else:
                supplier['country'] = None
            supplier.pop('country_id', None)
        
        return {
            'data': suppliers,
            'total': total,
            'page': page,
            'limit': limit,
            'pages': (total + limit - 1) // limit,
            'size': len(suppliers)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error obteniendo proveedores: {str(e)}')
