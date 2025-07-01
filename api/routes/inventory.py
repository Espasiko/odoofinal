from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List

from ..models.schemas import InventoryItem, User, PaginatedResponse
from ..services.auth_service import get_current_active_user

router = APIRouter(prefix="/api/v1", tags=["inventory"])

fake_inventory_db: List[InventoryItem] = [
    InventoryItem(id=1, product_id=1, product_name="Refrigerador Samsung RT38K5982BS", location="Almacén A", quantity=15, last_updated="2024-01-20T10:00:00"),
    InventoryItem(id=2, product_id=2, product_name="Lavadora LG F4WV5012S0W", location="Almacén B", quantity=8, last_updated="2024-01-20T11:30:00"),
    InventoryItem(id=3, product_id=3, product_name="Televisor Sony KD-55X80J", location="Almacén A", quantity=25, last_updated="2024-01-19T15:00:00"),
    InventoryItem(id=4, product_id=4, product_name="Laptop Dell XPS 15", location="Almacén C", quantity=4, last_updated="2024-01-20T09:00:00"),
    InventoryItem(id=5, product_id=5, product_name="Smartphone iPhone 14 Pro", location="Almacén B", quantity=30, last_updated="2024-01-18T18:00:00"),
]

@router.get("/inventory", response_model=PaginatedResponse[InventoryItem])
async def get_inventory(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_active_user)
):
    """Obtiene lista paginada de inventario"""
    try:
        start = (page - 1) * limit
        end = start + limit
        inventory = fake_inventory_db[start:end]
        total = len(fake_inventory_db)
        return PaginatedResponse(items=inventory, total=total, page=page, size=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/inventory/{item_id}", response_model=InventoryItem)
async def get_inventory_item(
    item_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Obtiene un item de inventario específico por ID"""
    try:
        item = next((i for i in fake_inventory_db if i.id == item_id), None)
        if item is None:
            raise HTTPException(status_code=404, detail="Inventory item not found")
        return item
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/inventory", response_model=InventoryItem)
async def create_inventory_item(
    item: InventoryItem,
    current_user: User = Depends(get_current_active_user)
):
    """Crea un nuevo item de inventario"""
    item.id = max(i.id for i in fake_inventory_db) + 1 if fake_inventory_db else 1
    fake_inventory_db.append(item)
    return item

@router.put("/inventory/{item_id}", response_model=InventoryItem)
async def update_inventory_item(
    item_id: int,
    item: InventoryItem,
    current_user: User = Depends(get_current_active_user)
):
    """Actualiza un item de inventario existente"""
    index = next((i for i, it in enumerate(fake_inventory_db) if it.id == item_id), None)
    if index is None:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    item.id = item_id
    fake_inventory_db[index] = item
    return item

@router.delete("/inventory/{item_id}")
async def delete_inventory_item(
    item_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Elimina un item de inventario"""
    global fake_inventory_db
    item = next((i for i in fake_inventory_db if i.id == item_id), None)
    if item is None:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    fake_inventory_db = [i for i in fake_inventory_db if i.id != item_id]
    return {"ok": True}
