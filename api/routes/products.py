from fastapi import APIRouter, Depends, HTTPException, Query, Request
import logging
from typing import List, Optional

from ..models.schemas import Product, User, PaginatedResponse, ProductCreate
from ..services.auth_service import auth_service
from ..services.odoo_service import odoo_service
from ..services.odoo_product_service import OdooProductService
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

@router.post("/products")
async def create_product(request: Request):
    logger = logging.getLogger("products_endpoint")
    product_data = await request.json()
    logger.info(f"Creando producto | Data recibida: {product_data}")
    try:
        # Transformación Frontend → Odoo
        logger.debug(f"Transformación Front→Odoo | Entrada: {product_data}")
        odoo_data = OdooProductService.front_to_odoo_product_dict(product_data)
        logger.debug(f"Transformación Front→Odoo | Salida: {odoo_data}")
        # Crear producto pasando el dict completo, sin ProductCreate restrictivo
        product_created = odoo_service.create_product(odoo_data)
        if not product_created:
            raise HTTPException(status_code=500, detail="Error al crear el producto en Odoo")
        template_id = getattr(product_created, 'template_id', None)
        return {"id": product_created.id, "template_id": template_id}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error creando producto: {str(e)}", exc_info=True)
        # Mostrar el error real de Odoo si está disponible
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.put("/products/{product_id}", response_model=Product)
async def update_product(
    product_id: int,
    update_data: dict,
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Actualiza un producto existente en Odoo (real)"""
    import logging
    logger = logging.getLogger("products_endpoint")
    logger.info(f"Update request para producto {product_id}: {update_data}")
    # Validar existencia
    existing_product = odoo_service.get_product_by_id(product_id)
    if not existing_product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    # Solo tomar campos válidos para update
    allowed_fields = [
        'name', 'list_price', 'default_code', 'categ_id', 'active', 'type', 'standard_price',
        'barcode', 'weight', 'sale_ok', 'purchase_ok', 'available_in_pos', 'to_weight',
        'is_published', 'website_sequence', 'description_sale', 'description_purchase',
        'seller_ids', 'product_tag_ids', 'public_categ_ids', 'pos_categ_ids', 'taxes_id', 'supplier_taxes_id'
    ]
    update_fields = {k: v for k, v in update_data.items() if k in allowed_fields}
    if not update_fields:
        raise HTTPException(status_code=400, detail="No se proporcionaron campos válidos para actualizar")
    # Validación y adaptación extra: si el campo es list_price y viene como string, convertir a float
    if 'list_price' in update_fields and isinstance(update_fields['list_price'], str):
        try:
            update_fields['list_price'] = float(update_fields['list_price'].replace(",", "."))
        except Exception:
            raise HTTPException(status_code=400, detail="El campo 'list_price' debe ser un número válido.")
    # Validar nombre si viene incluido
    if 'name' in update_fields and (not isinstance(update_fields['name'], str) or not update_fields['name'].strip()):
        raise HTTPException(status_code=400, detail="El campo 'name' es obligatorio y debe ser string.")
    updated = odoo_service.update_product(product_id, update_fields)
    if not updated:
        raise HTTPException(status_code=500, detail="Error al actualizar producto en Odoo")
    return updated

@router.delete("/products/{product_id}")
async def delete_product(
    product_id: int,
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Archiva (desactiva) un producto en Odoo (real)"""
    import logging
    logger = logging.getLogger("products_endpoint")
    logger.info(f"Archive request para producto {product_id}")
    existing_product = odoo_service.get_product_by_id(product_id)
    if not existing_product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    archived = odoo_service.archive_product(product_id)
    if not archived:
        raise HTTPException(status_code=500, detail="Error al archivar producto en Odoo")
    return {"message": "Producto archivado correctamente"}
