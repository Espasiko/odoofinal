from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from ..models.schemas import Product, User, PaginatedResponse, ProductCreate
from ..services.auth_service import auth_service
from ..services.odoo_service import odoo_service
from ..utils.config import config

router = APIRouter(prefix="/api/v1", tags=["products"])

@router.get("/products/all", response_model=List[Product])
async def get_all_products(
    current_user: User = Depends(auth_service.get_current_active_user)
):
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
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(auth_service.get_current_active_user)
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

@router.put("/products/{product_id}")
async def update_product(product_id: int, product: ProductCreate):
    """Actualizar un producto existente"""
    try:
        print(f"PRODUCTS_ROUTE: Actualizando producto ID: {product_id}")
        print(f"PRODUCTS_ROUTE: Datos recibidos: {product.dict()}")
        
        # Usar el servicio de Odoo para actualizar el producto
        updated_product = odoo_service.update_product(product_id, product.dict())
        
        if updated_product:
            print(f"PRODUCTS_ROUTE: Producto actualizado exitosamente: {updated_product.name}")
            return {
                "message": "Producto actualizado exitosamente",
                "product": updated_product
            }
        else:
            print(f"PRODUCTS_ROUTE: Error actualizando producto {product_id}")
            raise HTTPException(status_code=404, detail="Producto no encontrado o error en la actualización")
            
    except Exception as e:
        print(f"PRODUCTS_ROUTE: Excepción actualizando producto: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@router.delete("/products/{product_id}")
async def delete_product(
    product_id: int,
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Eliminar un producto (marcar como inactivo en Odoo)"""
    try:
        print(f"PRODUCTS_ROUTE: Eliminando producto ID: {product_id}")
        
        # Usar el servicio de Odoo para eliminar (marcar como inactivo) el producto
        success = odoo_service.delete_product(product_id)
        
        if success:
            print(f"PRODUCTS_ROUTE: Producto {product_id} eliminado exitosamente")
            return {"message": "Producto eliminado exitosamente"}
        else:
            print(f"PRODUCTS_ROUTE: Error eliminando producto {product_id}")
            raise HTTPException(status_code=404, detail="Producto no encontrado o error en la eliminación")
            
    except Exception as e:
        print(f"PRODUCTS_ROUTE: Excepción eliminando producto: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")
