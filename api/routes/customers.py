from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List

from ..models.schemas import Customer, User, PaginatedResponse
from ..services.auth_service import get_current_active_user

router = APIRouter(prefix="/api/v1", tags=["customers"])

# Datos simulados de clientes
fake_customers_db = [
    Customer(id=1, name="Juan Pérez", email="juan.perez@email.com", phone="+34 600 123 456", address="Calle Mayor 123, Madrid", total_purchases=1549.98),
    Customer(id=2, name="María García", email="maria.garcia@email.com", phone="+34 600 234 567", address="Avenida Libertad 45, Barcelona", total_purchases=649.99),
    Customer(id=3, name="Carlos López", email="carlos.lopez@email.com", phone="+34 600 345 678", address="Plaza España 12, Valencia", total_purchases=1599.98),
    Customer(id=4, name="Ana Martínez", email="ana.martinez@email.com", phone="+34 600 456 789", address="Calle Sol 78, Sevilla", total_purchases=899.99),
    Customer(id=5, name="Luis Rodríguez", email="luis.rodriguez@email.com", phone="+34 600 567 890", address="Avenida del Mar 34, Málaga", total_purchases=0.0),
]

@router.get("/customers", response_model=PaginatedResponse[Customer])
async def get_customers(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_active_user)
):
    """Obtiene lista paginada de clientes"""
    try:
        # Calcular paginación
        total = len(fake_customers_db)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        customers = fake_customers_db[start_idx:end_idx]
        
        return PaginatedResponse(
            data=customers,
            total=total,
            page=page,
            limit=limit,
            pages=(total + limit - 1) // limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo clientes: {str(e)}")

@router.get("/customers/{customer_id}", response_model=Customer)
async def get_customer(
    customer_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Obtiene un cliente específico por ID"""
    try:
        customer = next((customer for customer in fake_customers_db if customer.id == customer_id), None)
        if not customer:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        return customer
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo cliente: {str(e)}")

@router.post("/customers", response_model=Customer)
async def create_customer(
    customer: Customer,
    current_user: User = Depends(get_current_active_user)
):
    """Crea un nuevo cliente"""
    # Generar nuevo ID
    new_id = max([customer.id for customer in fake_customers_db], default=0) + 1
    customer.id = new_id
    fake_customers_db.append(customer)
    return customer

@router.put("/customers/{customer_id}", response_model=Customer)
async def update_customer(
    customer_id: int,
    customer: Customer,
    current_user: User = Depends(get_current_active_user)
):
    """Actualiza un cliente existente"""
    # Buscar el cliente existente
    existing_customer_idx = next((i for i, customer_data in enumerate(fake_customers_db) if customer_data.id == customer_id), None)
    if existing_customer_idx is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    # Actualizar el cliente
    customer.id = customer_id
    fake_customers_db[existing_customer_idx] = customer
    return customer

@router.delete("/customers/{customer_id}")
async def delete_customer(
    customer_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """Elimina un cliente"""
    # Buscar el cliente existente
    existing_customer_idx = next((i for i, customer in enumerate(fake_customers_db) if customer.id == customer_id), None)
    if existing_customer_idx is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    # Eliminar el cliente
    fake_customers_db.pop(existing_customer_idx)
    return {"message": "Cliente eliminado correctamente"}
