from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from ..models.schemas import Product, User, PaginatedResponse, ProductCreate
from ..services.auth_service import auth_service
from ..services.odoo_service import odoo_service
from ..utils.config import config

router = APIRouter(prefix="/api/v1", tags=["products"])

@router.get("/products/all", response_model=List[Product])
async def get_all_products(
    limit: int = Query(100, ge=1, le=200, description="Número máximo de productos a devolver")
):
    """Obtiene todos los productos sin paginación, con un límite configurable"""
    try:
        import time
        start_time = time.time()
        
        # Obtener el total de productos disponibles
        total_count = 0
        if hasattr(odoo_service, 'get_product_count'):
            total_count = odoo_service.get_product_count()
            print(f"API: Total de productos disponibles en Odoo: {total_count}")
        else:
            print("API: Método get_product_count no disponible en OdooService")
        
        # Obtener productos desde Odoo con un límite
        products = odoo_service.get_products(offset=0, limit=limit)
        print(f"API: Se obtuvieron {len(products)} productos de un límite de {limit}")
        
        end_time = time.time()
        print(f"API: Tiempo de respuesta para /products/all: {end_time - start_time:.2f} segundos")
        
        return products
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo productos: {str(e)}")

@router.get("/products", response_model=PaginatedResponse[Product])
async def get_products(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100)
):
    """Obtiene lista paginada de productos"""
    try:
        # Calcular offset y limit para paginación
        offset = (page - 1) * size
        limit = size
        
        # Obtener productos desde Odoo con paginación
        products = odoo_service.get_products(offset=offset, limit=limit)
        
        # Obtener el total de productos usando get_product_count si está disponible
        total = 0
        if hasattr(odoo_service, 'get_product_count'):
            total = odoo_service.get_product_count()
            print(f"API: Total de productos disponibles en Odoo para paginación: {total}")
        else:
            print("API: Método get_product_count no disponible, usando estimación")
            total = len(products) if products else 0
        
        return PaginatedResponse(
            data=products,
            total=total,
            page=page,
            size=size
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo productos paginados: {str(e)}")

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
