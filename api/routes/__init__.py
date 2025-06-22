"""Routes package for API endpoints"""

from .auth import router as auth_router
from .products import router as products_router
from .providers import router as providers_router
from .dashboard import router as dashboard_router
from .customers import router as customers_router
from .sales import router as sales_router
from .tasks import router as tasks_router
from .ocr import router as ocr_router

__all__ = [
    "auth_router",
    "products_router",
    "providers_router",
    "dashboard_router",
    "customers_router",
    "sales_router",
    "tasks_router",
    "ocr_router"
]
