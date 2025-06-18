from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime

from ..models.schemas import Sale, User, PaginatedResponse
from ..services.auth_service import auth_service

router = APIRouter(prefix="/api/v1", tags=["sales"])

# Datos simulados de ventas
fake_sales_db = [
    Sale(id=1, name="S00041", partner_id=[1, 301], customer_id=1, customer_name="Juan Pérez", product_id=1, product_name="Refrigerador Samsung RT38K5982BS", quantity=1, unit_price=899.99, amount_total=899.99, state="completed", date=datetime(2024, 1, 15), date_order=datetime(2024, 1, 15)),
    Sale(id=2, name="S00042", partner_id=[2, 302], customer_id=2, customer_name="María García", product_id=2, product_name="Lavadora LG F4WV5012S0W", quantity=1, unit_price=649.99, amount_total=649.99, state="completed", date=datetime(2024, 1, 14), date_order=datetime(2024, 1, 14)),
    Sale(id=3, name="S00043", partner_id=[3, 303], customer_id=3, customer_name="Carlos López", product_id=3, product_name="Televisor Sony KD-55X80J", quantity=2, unit_price=799.99, amount_total=1599.98, state="pending", date=datetime(2024, 1, 13), date_order=datetime(2024, 1, 13)),
    Sale(id=4, name="S00044", partner_id=[1, 301], customer_id=1, customer_name="Juan Pérez", product_id=2, product_name="Lavadora LG F4WV5012S0W", quantity=1, unit_price=649.99, amount_total=649.99, state="completed", date=datetime(2024, 1, 12), date_order=datetime(2024, 1, 12)),
    Sale(id=5, name="S00045", partner_id=[4, 304], customer_id=4, customer_name="Ana Martínez", product_id=1, product_name="Refrigerador Samsung RT38K5982BS", quantity=1, unit_price=899.99, amount_total=899.99, state="cancelled", date=datetime(2024, 1, 11), date_order=datetime(2024, 1, 11)),
]

@router.get("/sales", response_model=PaginatedResponse[Sale])
async def get_sales(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Obtiene lista paginada de ventas"""
    try:
        # Calcular paginación
        total = len(fake_sales_db)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        sales = fake_sales_db[start_idx:end_idx]
        
        return PaginatedResponse(
            data=sales,
            total=total,
            page=page,
            limit=limit,
            pages=(total + limit - 1) // limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo ventas: {str(e)}")

@router.get("/sales/{sale_id}", response_model=Sale)
async def get_sale(
    sale_id: int,
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Obtiene una venta específica por ID"""
    try:
        sale = next((sale for sale in fake_sales_db if sale.id == sale_id), None)
        if not sale:
            raise HTTPException(status_code=404, detail="Venta no encontrada")
        return sale
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo venta: {str(e)}")

@router.post("/sales", response_model=Sale)
async def create_sale(
    sale: Sale,
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Crea una nueva venta"""
    # Generar nuevo ID
    new_id = max([sale.id for sale in fake_sales_db], default=0) + 1
    sale.id = new_id
    fake_sales_db.append(sale)
    return sale

@router.put("/sales/{sale_id}", response_model=Sale)
async def update_sale(
    sale_id: int,
    sale: Sale,
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Actualiza una venta existente"""
    # Buscar la venta existente
    existing_sale_idx = next((i for i, sale_data in enumerate(fake_sales_db) if sale_data.id == sale_id), None)
    if existing_sale_idx is None:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    
    # Actualizar la venta
    sale.id = sale_id
    fake_sales_db[existing_sale_idx] = sale
    return sale

@router.delete("/sales/{sale_id}")
async def delete_sale(
    sale_id: int,
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Elimina una venta"""
    # Buscar la venta existente
    existing_sale_idx = next((i for i, sale in enumerate(fake_sales_db) if sale.id == sale_id), None)
    if existing_sale_idx is None:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    
    # Eliminar la venta
    fake_sales_db.pop(existing_sale_idx)
    return {"message": "Venta eliminada correctamente"}
