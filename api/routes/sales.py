from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime

from ..models.schemas import Sale, User, PaginatedResponse
from ..services.auth_service import get_current_active_user

router = APIRouter(prefix="/api/v1", tags=["sales"])

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
    current_user: User = Depends(get_current_active_user)
):
    """Obtiene lista paginada de ventas"""
    try:
        start = (page - 1) * limit
        end = start + limit
        sales = fake_sales_db[start:end]
        total = len(fake_sales_db)
        return PaginatedResponse(items=sales, total=total, page=page, size=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sales/{sale_id}", response_model=Sale)
async def get_sale(
    sale_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Obtiene una venta específica por ID"""
    try:
        sale = next((s for s in fake_sales_db if s.id == sale_id), None)
        if sale is None:
            raise HTTPException(status_code=404, detail="Sale not found")
        return sale
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sales", response_model=Sale)
async def create_sale(
    sale: Sale,
    current_user: User = Depends(get_current_active_user)
):
    """Crea una nueva venta"""
    sale.id = max(s.id for s in fake_sales_db) + 1 if fake_sales_db else 1
    fake_sales_db.append(sale)
    return sale

@router.put("/sales/{sale_id}", response_model=Sale)
async def update_sale(
    sale_id: int,
    sale: Sale,
    current_user: User = Depends(get_current_active_user)
):
    """Actualiza una venta existente"""
    index = next((i for i, s in enumerate(fake_sales_db) if s.id == sale_id), None)
    if index is None:
        raise HTTPException(status_code=404, detail="Sale not found")
    sale.id = sale_id
    fake_sales_db[index] = sale
    return sale

@router.delete("/sales/{sale_id}")
async def delete_sale(
    sale_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Elimina una venta"""
    global fake_sales_db
    sale = next((s for s in fake_sales_db if s.id == sale_id), None)
    if sale is None:
        raise HTTPException(status_code=404, detail="Sale not found")
    fake_sales_db = [s for s in fake_sales_db if s.id != sale_id]
    return {"ok": True}
