from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from datetime import datetime
from ..models.schemas import Sale, Product

from ..models.schemas import DashboardStats, User
from ..services.auth_service import auth_service

router = APIRouter(prefix="/api/v1", tags=["dashboard"])

@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Obtiene estadísticas del dashboard desde Odoo"""
    try:
        # Obtener datos reales desde Odoo
        from ..services.odoo_service import odoo_service
        
        # Obtener productos desde Odoo
        products = odoo_service.get_products()
        total_products = len(products)
        
        # Calcular productos con stock bajo (menos de 5 unidades)
        print(f"DEBUG: Analizando {len(products)} productos para stock")
        for i, p in enumerate(products[:3]):  # Solo los primeros 3 para debug
            print(f"DEBUG: Producto {i}: stock={getattr(p, 'stock', 'NO_ATTR')}, type={type(getattr(p, 'stock', None))}")
        
        low_stock_products = []
        out_of_stock_products = []
        
        for p in products:
            try:
                if hasattr(p, 'stock'):
                    stock_value = getattr(p, 'stock')
                    if stock_value is not None:
                        # Convertir a int si es necesario y validar que sea un número
                        try:
                            stock_int = int(stock_value) if stock_value is not None else 0
                            if stock_int < 5:
                                low_stock_products.append(p)
                            if stock_int == 0:
                                out_of_stock_products.append(p)
                        except (ValueError, TypeError):
                            print(f"DEBUG: No se pudo convertir stock a int: {stock_value}")
            except Exception as e:
                print(f"DEBUG: Error procesando producto {getattr(p, 'name', 'UNKNOWN')}: {e}")
        
        # Calcular total de stock de forma segura
        total_stock = 0
        for p in products:
            try:
                stock_value = getattr(p, 'stock', 0)
                if stock_value is not None:
                    total_stock += int(stock_value)
            except (ValueError, TypeError):
                continue
        
        # Obtener clientes desde Odoo
        customers = odoo_service.get_customers()
        total_customers = len(customers)
        
        # Obtener ventas recientes desde Odoo
        sales = odoo_service.get_sales()
        monthly_revenue = sum(getattr(s, 'amount_total', 0) for s in sales)
        
        # Calcular categorías principales
        category_counts = {}
        for product in products:
            category = getattr(product, 'category', 'Sin categoría')
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Ordenar categorías por cantidad y tomar las top 5
        sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        total_categorized = sum(count for _, count in sorted_categories)
        
        top_categories = []
        for name, count in sorted_categories:
            percentage = (count / total_categorized * 100) if total_categorized > 0 else 0
            top_categories.append({"name": name, "count": count, "percentage": round(percentage, 1)})
        
        stats = DashboardStats(
            totalProducts=total_products,
            totalCustomers=total_customers,
            monthlyRevenue=monthly_revenue,
            stockStats=StockStats(
                lowStockProducts=len(low_stock_products),
                outOfStockProducts=len(out_of_stock_products),
                totalStock=total_stock
            ),
            topCategories=top_categories,
            low_stock_products=low_stock_products[:10],  # Limitar a 10 productos
            recentSales=sales[:10] if sales else []  # Limitar a 10 ventas recientes
        )
        
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo estadísticas del dashboard: {str(e)}")

@router.get("/dashboard/categories")
async def get_categories(
    current_user: User = Depends(auth_service.get_current_active_user)
):
    """Obtiene categorías de productos desde Odoo"""
    try:
        # Obtener datos reales desde Odoo
        from ..services.odoo_service import odoo_service
        
        # Obtener productos desde Odoo
        products = odoo_service.get_products()
        
        # Calcular categorías y sus conteos
        category_counts = {}
        category_ids = {}
        
        for product in products:
            category = getattr(product, 'category', 'Sin categoría')
            categ_id = getattr(product, 'categ_id', [0])
            
            if category not in category_counts:
                category_counts[category] = 0
                category_ids[category] = categ_id[0] if isinstance(categ_id, list) and categ_id else 0
            
            category_counts[category] += 1
        
        # Convertir a formato esperado
        categories = []
        for category, count in category_counts.items():
            categories.append({
                "id": category_ids[category],
                "name": category,
                "count": count
            })
        
        # Ordenar por cantidad descendente
        categories.sort(key=lambda x: x["count"], reverse=True)
        
        return {"categories": categories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo categorías: {str(e)}")
