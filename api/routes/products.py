from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from ..models.schemas import Product, User, PaginatedResponse, ProductCreate
from ..services.auth_service import get_current_active_user
from ..services.odoo_service import odoo_service
from ..services.odoo_product_service import OdooProductService
from ..utils.config import config

router = APIRouter(prefix="/api/v1", tags=["products"])

@router.get("/products", response_model=PaginatedResponse[Product])
async def get_products(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    sort_by: Optional[str] = Query('id', description="Campo por el que ordenar"),
    sort_order: Optional[str] = Query('asc', description="asc o desc"),
    search: Optional[str] = Query(None, description="Término de búsqueda en nombre y descripción"),
    category: Optional[str] = Query(None, description="Filtrar por categoría"),
    current_user: User = Depends(get_current_active_user)
):
    """Obtiene lista paginada de productos REALES de Odoo"""
    try:
        products, total = odoo_service.get_paginated_products(
            page=page, 
            limit=size, 
            sort_by=sort_by, 
            sort_order=sort_order,
            search=search,
            category=category
        )
        return PaginatedResponse(items=products, total=total, page=page, size=size)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/products/all", response_model=List[Product])
async def get_all_products(current_user: User = Depends(get_current_active_user)):
    """Obtiene todos los productos sin paginación"""
    try:
        return odoo_service.get_products()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/products/{product_id}", response_model=Product)
async def get_product(
    product_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Obtiene un producto específico por ID"""
    try:
        product = odoo_service.get_product_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/products", response_model=Product, status_code=201)
async def create_product(
    product_data: ProductCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Crea un nuevo producto en Odoo (real)"""
    try:
        product_service = OdooProductService()
        created_product_id = product_service.create_product(product_data.dict())
        if not created_product_id:
            raise HTTPException(status_code=400, detail="Failed to create product in Odoo")
        
        new_product = odoo_service.get_product_by_id(created_product_id)
        if not new_product:
            raise HTTPException(status_code=404, detail="Newly created product not found")
            
        return new_product
    except Exception as e:
        import logging
        logging.error(f"Error creating product: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/products/{product_id}", response_model=Product)
async def update_product(
    product_id: int,
    update_data: dict,
    current_user: User = Depends(get_current_active_user)
):
    """Actualiza un producto existente en Odoo (real)"""
    import logging
    try:
        product_service = OdooProductService()
        success = product_service.update_product(product_id, update_data)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to update product in Odoo")
        
        updated_product = odoo_service.get_product_by_id(product_id)
        if not updated_product:
            raise HTTPException(status_code=404, detail="Updated product not found")

        return updated_product
    except Exception as e:
        logging.error(f"Error al actualizar producto {product_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/products/{product_id}")
async def delete_product(
    product_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Archiva (desactiva) un producto en Odoo (real)"""
    import logging
    try:
        product_service = OdooProductService()
        success = product_service.archive_product(product_id)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to archive product in Odoo")
        return {"message": f"Product {product_id} archived successfully"}
    except Exception as e:
        logging.error(f"Error archivando producto {product_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))