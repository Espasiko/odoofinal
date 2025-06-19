from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from ..models.schemas import Product, User, PaginatedResponse, ProductCreate
from ..services.auth_service import auth_service
from ..services.odoo_service import odoo_service
from ..utils.config import config

router = APIRouter(prefix="/api/v1", tags=["products"])

@router.get("/products/all", response_model=List[Product])
async def get_all_products():
    """Obtiene todos los productos sin paginación"""
    try:
        # Obtener todos los productos desde Odoo
        products = odoo_service.get_products()
        return products
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo productos: {str(e)}")

@router.get("/products", response_model=PaginatedResponse[Product])
async def get_products(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
):
    """Obtiene lista paginada de productos"""
    try:
        # Obtener productos desde Odoo
        all_products = odoo_service.get_products()
        
        # Calcular paginación
        total = len(all_products)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        products = all_products[start_idx:end_idx]
        
        return PaginatedResponse(
            data=products,
            total=total,
            page=page,
            limit=limit,
            pages=(total + limit - 1) // limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo productos: {str(e)}")

@router.get("/products/{product_id}", response_model=Product)
async def get_product(
    product_id: int,
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Obtiene un producto específico por ID"""
    try:
        product = odoo_service.get_product_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        return product
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo producto: {str(e)}")

@router.post("/products", response_model=Product)
async def create_product(
    product: ProductCreate,  # Cambiado de Product a ProductCreate
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Crea un nuevo producto (simulado)"""
    # En una implementación real, se crearía en Odoo y se devolvería el producto completo
    # Por ahora, simulamos la creación y devolvemos un objeto Product con un ID
    # Asumiendo que odoo_service.create_product(product) devuelve el producto creado con su ID
    product_created = odoo_service.create_product(product)
    if not product_created:
        raise HTTPException(status_code=500, detail="Error al crear el producto en Odoo")
    return product_created

    # Simulación anterior:
    # return Product(id=999, name=product.name, code=product.code, category=product.category, price=product.price, stock_quantity=product.stock, image_url=product.image_url, is_active=True)

@router.put("/products/{product_id}", response_model=Product)
async def update_product(
    product_id: int,
    product: Product,
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Actualiza un producto existente (simulado)"""
    # Verificar que el producto existe
    existing_product = odoo_service.get_product_by_id(product_id)
    if not existing_product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    # Por ahora retornamos el producto actualizado
    # En una implementación real, se actualizaría en Odoo
    product.id = product_id
    return product

@router.delete("/products/{product_id}")
async def delete_product(
    product_id: int,
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Elimina un producto (simulado)"""
    # Verificar que el producto existe
    existing_product = odoo_service.get_product_by_id(product_id)
    if not existing_product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    # Por ahora solo retornamos éxito
    # En una implementación real, se eliminaría de Odoo
    return {"message": "Producto eliminado correctamente"}
