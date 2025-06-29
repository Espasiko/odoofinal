from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from datetime import datetime
from ..models.schemas import Sale, Product

from ..models.schemas import DashboardStats, User
from ..services.auth_service import get_current_active_user

router = APIRouter(prefix="/api/v1", tags=["dashboard"])

@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_active_user)
):
    """Obtiene estadísticas del dashboard desde Odoo"""
    try:
        from ..services.odoo_service import odoo_service
        products = odoo_service.get_products()
        total_products = len(products)
        low_stock_products = []
        out_of_stock_products = []
        for p in products:
            try:
                if isinstance(p, dict):
                    p = Product(**p)
                if hasattr(p, 'stock'):
                    stock_value = getattr(p, 'stock')
                    if stock_value is not None:
                        try:
                            stock_int = int(stock_value)
                            if stock_int < 5:
                                low_stock_products.append(p)
                            if stock_int == 0:
                                out_of_stock_products.append(p)
                        except (ValueError, TypeError):
                            pass
            except Exception as inner_e:
                print(f"Error procesando producto {getattr(p, 'id', 'N/A')} para stock: {inner_e}")
        total_stock = sum(int(p.stock) for p in products if hasattr(p, 'stock') and p.stock and str(p.stock).isdigit())
        sales = odoo_service.get_sales()
        category_counts = {}
        for p in products:
            category = getattr(p, 'category', 'Sin categoría')
            if category not in category_counts:
                category_counts[category] = 0
            category_counts[category] += 1
        top_categories = sorted(category_counts.items(), key=lambda item: item[1], reverse=True)[:5]
        top_categories = [{"name": cat, "count": count} for cat, count in top_categories]
        stats = DashboardStats(
            totalProducts=total_products,
            totalSales=len(sales) if sales else 0,
            totalCustomers=len(odoo_service.get_customers()),
            inventoryStats=dict(
                lowStockProducts=len(low_stock_products),
                outOfStockProducts=len(out_of_stock_products),
                totalStock=total_stock
            ),
            topCategories=top_categories,
            low_stock_products=low_stock_products[:10],
            recentSales=sales[:10] if sales else []
        )
        return stats
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error obteniendo estadísticas del dashboard: {str(e)}")

@router.get("/dashboard/categories")
async def get_categories(
    current_user: User = Depends(get_current_active_user)
):
    """Obtiene categorías de productos desde Odoo"""
    try:
        from ..services.odoo_service import odoo_service
        products = odoo_service.get_products()
        category_counts = {}
        category_ids = {}
        for product in products:
            category = getattr(product, 'category', 'Sin categoría')
            categ_id = getattr(product, 'categ_id', [0])
            if category not in category_counts:
                category_counts[category] = 0
                category_ids[category] = categ_id[0] if isinstance(categ_id, list) and categ_id else 0
            category_counts[category] += 1
        categories = []
        for category, count in category_counts.items():
            categories.append({
                "id": category_ids[category],
                "name": category,
                "count": count
            })
        categories.sort(key=lambda x: x["count"], reverse=True)
        return {"categories": categories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo categorías: {str(e)}")
