from fastapi import APIRouter, Depends, HTTPException, Query
from ..models.schemas import Provider, ProviderCreate, ProviderUpdate, User, PaginatedResponse
from typing import List

from ..services.auth_service import get_current_active_user
from ..services.odoo_service import odoo_service

router = APIRouter(prefix="/api/v1", tags=["providers"])

@router.get("/providers", response_model=PaginatedResponse[Provider])
async def get_providers(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_active_user)
):
    """Obtiene lista paginada de proveedores"""
    try:
        providers, total = odoo_service.get_paginated_providers(page=page, limit=size)
        return PaginatedResponse(items=providers, total=total, page=page, size=size)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/providers/all", response_model=List[Provider])
async def get_all_providers(
    current_user: User = Depends(get_current_active_user)
):
    """Obtiene todos los proveedores sin paginación"""
    try:
        return odoo_service.get_providers()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/providers/{provider_id}", response_model=Provider)
async def get_provider(
    provider_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Obtiene un proveedor específico por ID"""
    try:
        provider = odoo_service.get_provider_by_id(provider_id)
        if provider is None:
            raise HTTPException(status_code=404, detail="Provider not found")
        return provider
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/providers", response_model=Provider)
async def create_provider(
    provider: ProviderCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Crea un nuevo proveedor REAL en Odoo 18 (campos español/inglés, robusto)"""
    import logging
    try:
        created_provider_id = odoo_service.create_provider(provider.dict())
        if not created_provider_id:
            raise HTTPException(status_code=400, detail="Failed to create provider in Odoo")
        
        new_provider = odoo_service.get_provider_by_id(created_provider_id)
        if not new_provider:
             raise HTTPException(status_code=404, detail="Could not retrieve newly created provider.")

        return new_provider
    except Exception as e:
        logging.error(f"Error al crear proveedor: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/providers/{provider_id}", response_model=Provider)
async def update_provider(
    provider_id: int,
    provider: ProviderUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Actualiza un proveedor existente en Odoo (real, flexible y robusto)"""
    import logging
    try:
        success = odoo_service.update_provider(provider_id, provider.dict(exclude_unset=True))
        if not success:
            raise HTTPException(status_code=400, detail="Failed to update provider in Odoo")
        
        updated_provider = odoo_service.get_provider_by_id(provider_id)
        if not updated_provider:
            raise HTTPException(status_code=404, detail="Could not retrieve updated provider.")

        return updated_provider
    except Exception as e:
        logging.error(f"Error al actualizar proveedor {provider_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/providers/{provider_id}")
async def delete_provider(
    provider_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Elimina un proveedor (simulado)"""
    raise HTTPException(status_code=501, detail="Provider deletion is not implemented yet.")
