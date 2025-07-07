from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict

from ..models.schemas import Product, User, PaginatedResponse, ProductCreate, OdooProductUpdate
from ..services.auth_service import get_current_active_user
from ..services.odoo_product_service import OdooProductService

router = APIRouter(prefix="/api/v1", tags=["products"])

# Helper para no instanciar el servicio en cada ruta
# FastAPI lo manejará como un singleton en el scope de la request
def get_product_service():
    service = OdooProductService()
    # Inicializar campos personalizados al arrancar
    service.initialize_custom_fields()
    return service

@router.get("/products", response_model=PaginatedResponse[Product])
async def get_products(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=1000), # Límite aumentado para pruebas
    sort_by: Optional[str] = Query('id', description="Campo por el que ordenar"),
    sort_order: Optional[str] = Query('asc', description="asc o desc"),
    search: Optional[str] = Query(None, description="Término de búsqueda en nombre y código"),
    category: Optional[str] = Query(None, description="Filtrar por nombre de categoría"),
    include_inactive: bool = Query(False, description="Incluir productos inactivos (archivados)"),
    current_user: User = Depends(get_current_active_user),
    product_service: OdooProductService = Depends(get_product_service)
):
    """Obtiene lista paginada de productos REALES de Odoo"""
    import logging
    logger = logging.getLogger("api.routes.products")
    logger.info(f"Llamada a /products page={page} size={size} search={search} category={category}")
    products, total = product_service.get_paginated_products(
        page=page, 
        limit=size, 
        sort_by=sort_by, 
        sort_order=sort_order,
        search=search,
        category=category,
        include_inactive=include_inactive
    )
    logger.info(f"Respuesta de get_paginated_products: {len(products)} productos, total={total}")
    pages = (total + size - 1) // size if size else 1
    logger.info(f"Paginas calculadas: {pages}")
    return PaginatedResponse(data=products, total=total, page=page, limit=size, pages=pages)

@router.get("/products/{product_id}", response_model=Product)
async def get_product(
    product_id: int,
    current_user: User = Depends(get_current_active_user),
    product_service: OdooProductService = Depends(get_product_service)
):
    """Obtiene un producto específico por ID"""
    product = product_service.get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product

@router.post("/products", response_model=Product, status_code=201)
async def create_product(
    product_data: ProductCreate,
    current_user: User = Depends(get_current_active_user),
    product_service: OdooProductService = Depends(get_product_service)
):
    """Crea un nuevo producto en Odoo (real)"""
    # El servicio ya maneja la lógica de creación y las excepciones
    created_product_dict = product_service.create_product(product_data)
    return created_product_dict

@router.put("/products/{product_id}", response_model=Product)
async def update_product(
    product_id: int,
    update_data: OdooProductUpdate, # Usar el schema para validación
    current_user: User = Depends(get_current_active_user),
    product_service: OdooProductService = Depends(get_product_service)
):
    """Actualiza un producto existente en Odoo (real)"""
    # Convertimos el modelo Pydantic a un diccionario, excluyendo campos no seteados
    update_dict = update_data.model_dump(exclude_unset=True)
    if not update_dict:
        raise HTTPException(status_code=400, detail="No se proporcionaron datos para actualizar")

    updated_product = product_service.update_product(product_id, update_dict)
    if not updated_product:
        # El servicio ya loguea el error, aquí solo informamos al cliente
        raise HTTPException(status_code=404, detail=f"No se pudo actualizar el producto {product_id}. Puede que no exista o haya un error en Odoo.")
    return updated_product

@router.delete("/products/{product_id}", status_code=204)
async def delete_product(
    product_id: int,
    current_user: User = Depends(get_current_active_user),
    product_service: OdooProductService = Depends(get_product_service)
):
    """Archiva (desactiva) un producto en Odoo (real)"""
    success = product_service.archive_product(product_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"No se pudo archivar el producto {product_id}. Puede que no exista o ya esté archivado.")
    # No se devuelve contenido en un 204
    return
