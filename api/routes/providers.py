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

from api.models.provider_create import ProviderCreate

@router.post("/providers", response_model=Provider)
async def create_provider(
    provider: ProviderCreate,
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Crea un nuevo proveedor REAL en Odoo 18 (campos español/inglés, robusto)"""
    import logging
    logger = logging.getLogger("providers_create_endpoint")
    data = provider.dict(exclude_unset=True)

    # --- MAPEO UNIVERSAL DE CAMPOS CLAVE (español/inglés) ---
    if 'nombre' in data:
        data['name'] = data['nombre']
    if 'correo' in data:
        data['email'] = data['correo']
    if 'telefono' in data:
        data['phone'] = data['telefono']
    if 'comentario' in data:
        data['comment'] = data['comentario']

    # Campos string que espera Provider y Odoo
    all_string_fields = [
        'name', 'email', 'phone', 'comment', 'vat', 'website', 'mobile', 'street', 'street2', 'city', 'zip'
    ]
    provider_fields = {k: v for k, v in data.items() if k in all_string_fields}

    # Refuerzo de saneo: convertir False/None a string vacío en TODOS los campos relevantes
    for k in all_string_fields:
        if k in provider_fields and (provider_fields[k] is False or provider_fields[k] is None):
            provider_fields[k] = ""

    logger.info(f"Campos enviados a Odoo para crear proveedor: {provider_fields}")
    if not provider_fields.get('name'):
        raise HTTPException(status_code=400, detail="El campo 'name' es obligatorio")

    created = odoo_service.create_supplier(provider_fields)
    if not created:
        raise HTTPException(status_code=500, detail="Error al crear proveedor en Odoo")
    return created

from api.models.provider_update import ProviderUpdate

@router.put("/providers/{provider_id}", response_model=Provider)
async def update_provider(
    provider_id: int,
    provider: ProviderUpdate,
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Actualiza un proveedor existente en Odoo (real, flexible y robusto)"""
    import logging
    logger = logging.getLogger("providers_endpoint")

    update_data = provider.dict(exclude_unset=True)

    # --- MAPEO UNIVERSAL DE CAMPOS CLAVE (español/inglés) ---
    if 'nombre' in update_data:
        update_data['name'] = update_data['nombre']
    if 'correo' in update_data:
        update_data['email'] = update_data['correo']
    if 'telefono' in update_data:
        update_data['phone'] = update_data['telefono']
    if 'comentario' in update_data:
        update_data['comment'] = update_data['comentario']

    # --- CONSTRUCCIÓN DEL PAYLOAD DE ACTUALIZACIÓN ---
    # Lista completa de campos que se pueden actualizar
    updatable_fields = [
        'name', 'email', 'phone', 'comment', 'vat', 'website', 'mobile',
        'street', 'street2', 'city', 'zip',
        'active', 'is_company', 'supplier_rank', 'customer_rank'
    ]
    
    # Crear el diccionario de actualización solo con los campos permitidos
    update_payload = {k: v for k, v in update_data.items() if k in updatable_fields}

    # Saneo de campos de texto
    string_fields_to_sanitize = [
        'name', 'email', 'phone', 'comment', 'vat', 'website', 'mobile', 
        'street', 'street2', 'city', 'zip'
    ]
    for field in string_fields_to_sanitize:
        if field in update_payload and (update_payload[field] is False or update_payload[field] is None):
            update_payload[field] = ""

    logger.info(f"Campos enviados a Odoo para update proveedor: {update_payload}")
    if not update_payload:
        raise HTTPException(status_code=400, detail="No se proporcionaron campos válidos para actualizar")

    updated = odoo_service.update_provider(provider_id, update_payload)
    if not updated:
        raise HTTPException(status_code=500, detail="Error al actualizar proveedor en Odoo")
    return updated

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
