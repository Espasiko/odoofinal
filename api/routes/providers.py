from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List

from ..models.schemas import Provider, User, PaginatedResponse
from ..services.auth_service import auth_service
from ..services.odoo_service import odoo_service

router = APIRouter(prefix="/api/v1", tags=["providers"])

@router.get("/providers", response_model=PaginatedResponse[Provider])
async def get_providers(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Obtiene lista paginada de proveedores"""
    try:
        # Obtener proveedores desde Odoo
        all_providers = odoo_service.get_providers()
        
        # Calcular paginación
        total = len(all_providers)
        start_idx = (page - 1) * size
        end_idx = start_idx + size
        providers = all_providers[start_idx:end_idx]
        
        return PaginatedResponse(
            data=providers,
            total=total,
            page=page,
            size=size,
            pages=(total + size - 1) // size
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo proveedores: {str(e)}")

@router.get("/providers/all", response_model=List[Provider])
async def get_all_providers(
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Obtiene todos los proveedores sin paginación"""
    try:
        # Obtener todos los proveedores desde Odoo
        providers = odoo_service.get_providers()
        return providers
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo proveedores: {str(e)}")

@router.get("/providers/{provider_id}", response_model=Provider)
async def get_provider(
    provider_id: int,
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Obtiene un proveedor específico por ID"""
    try:
        providers = odoo_service.get_providers()
        provider = next((p for p in providers if p.id == provider_id), None)
        if not provider:
            raise HTTPException(status_code=404, detail="Proveedor no encontrado")
        return provider
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo proveedor: {str(e)}")

@router.post("/providers", response_model=Provider)
async def create_provider(
    provider: Provider,
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Crea un nuevo proveedor (simulado)"""
    # Por ahora retornamos el proveedor con un ID simulado
    # En una implementación real, se crearía en Odoo
    provider.id = 999  # ID simulado
    return provider

@router.put("/providers/{provider_id}", response_model=Provider)
async def update_provider(
    provider_id: int,
    provider: Provider,
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Actualiza un proveedor existente (simulado)"""
    # Verificar que el proveedor existe
    providers = odoo_service.get_providers()
    existing_provider = next((p for p in providers if p.id == provider_id), None)
    if not existing_provider:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    
    # Por ahora retornamos el proveedor actualizado
    # En una implementación real, se actualizaría en Odoo
    provider.id = provider_id
    return provider

@router.delete("/providers/{provider_id}")
async def delete_provider(
    provider_id: int,
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Elimina un proveedor (simulado)"""
    # Verificar que el proveedor existe
    providers = odoo_service.get_providers()
    existing_provider = next((p for p in providers if p.id == provider_id), None)
    if not existing_provider:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    
    # Por ahora solo retornamos éxito
    # En una implementación real, se eliminaría de Odoo
    return {"message": "Proveedor eliminado correctamente"}
