from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query

from ..models.schemas import InventoryItem, User, PaginatedResponse
from ..services.auth_service import auth_service

router = APIRouter(prefix="/api/v1", tags=["inventory"])

# Datos simulados de inventario
from datetime import datetime

fake_inventory_db = [
    InventoryItem(id=1, product_id=[1, 101], location_id=[1, 201], quantity=12, product_name="Refrigerador Samsung RT38K5982BS", location="Almacén A", last_updated=datetime(2024, 1, 15)),
    InventoryItem(id=2, product_id=[2, 102], location_id=[1, 201], quantity=8, product_name="Lavadora LG F4WV5012S0W", location="Almacén A", last_updated=datetime(2024, 1, 14)),
    InventoryItem(id=3, product_id=[3, 103], location_id=[2, 202], quantity=5, product_name="Televisor Sony KD-55X80J", location="Almacén B", last_updated=datetime(2024, 1, 13)),
    InventoryItem(id=4, product_id=[1, 101], location_id=[2, 202], quantity=3, product_name="Refrigerador Samsung RT38K5982BS", location="Almacén B", last_updated=datetime(2024, 1, 12)),
    InventoryItem(id=5, product_id=[2, 102], location_id=[3, 203], quantity=15, product_name="Lavadora LG F4WV5012S0W", location="Almacén C", last_updated=datetime(2024, 1, 11)),
]

@router.get("/inventory", response_model=PaginatedResponse[InventoryItem])
async def get_inventory(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Obtiene lista paginada de inventario"""
    try:
        # Calcular paginación
        total = len(fake_inventory_db)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        inventory_items = fake_inventory_db[start_idx:end_idx]
        
        return PaginatedResponse(
            data=inventory_items,
            total=total,
            page=page,
            limit=limit,
            pages=(total + limit - 1) // limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo inventario: {str(e)}")

@router.get("/inventory/{item_id}", response_model=InventoryItem)
async def get_inventory_item(
    item_id: int,
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Obtiene un item de inventario específico por ID"""
    try:
        item = next((item for item in fake_inventory_db if item.id == item_id), None)
        if not item:
            raise HTTPException(status_code=404, detail="Item de inventario no encontrado")
        return item
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo item de inventario: {str(e)}")

@router.post("/inventory", response_model=InventoryItem)
async def create_inventory_item(
    item: InventoryItem,
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Crea un nuevo item de inventario"""
    # Generar nuevo ID
    new_id = max([item.id for item in fake_inventory_db], default=0) + 1
    item.id = new_id
    # Validar y transformar product_id y location_id si vienen como int
    if isinstance(item.product_id, int):
        item.product_id = [item.product_id, getattr(item, "product_name", "")]
    if isinstance(item.location_id, int):
        item.location_id = [item.location_id, getattr(item, "location", "")]
    fake_inventory_db.append(item)
    return item

@router.put("/inventory/{item_id}", response_model=InventoryItem)
async def update_inventory_item(
    item_id: int,
    item: InventoryItem,
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Actualiza un item de inventario existente"""
    # Buscar el item existente
    existing_item_idx = next((i for i, item_data in enumerate(fake_inventory_db) if item_data.id == item_id), None)
    if existing_item_idx is None:
        raise HTTPException(status_code=404, detail="Item de inventario no encontrado")
    # Validar y transformar product_id y location_id si vienen como int
    if isinstance(item.product_id, int):
        item.product_id = [item.product_id, getattr(item, "product_name", "")]
    if isinstance(item.location_id, int):
        item.location_id = [item.location_id, getattr(item, "location", "")]
    # Actualizar el item
    item.id = item_id
    fake_inventory_db[existing_item_idx] = item
    return item

@router.delete("/inventory/{item_id}")
async def delete_inventory_item(
    item_id: int,
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Elimina un item de inventario"""
    # Buscar el item existente
    existing_item_idx = next((i for i, item in enumerate(fake_inventory_db) if item.id == item_id), None)
    if existing_item_idx is None:
        raise HTTPException(status_code=404, detail="Item de inventario no encontrado")
    
    # Eliminar el item
    fake_inventory_db.pop(existing_item_idx)
    return {"message": "Item de inventario eliminado correctamente"}
