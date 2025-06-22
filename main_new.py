from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer

# Importar configuración
from api.utils.config import config

# Importar rutas
from api.routes.auth import router as auth_router
from api.routes.products import router as products_router
from api.routes.providers import router as providers_router
from api.routes.inventory import router as inventory_router
from api.routes.sales import router as sales_router
from api.routes.customers import router as customers_router
from api.routes.dashboard import router as dashboard_router
from api.routes.tasks import router as tasks_router
from api.routes.ocr import router as ocr_router

# Crear aplicación FastAPI
app = FastAPI(
    title=config.API_TITLE,
    description=config.API_DESCRIPTION,
    version=config.API_VERSION
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Incluir rutas
app.include_router(auth_router)
app.include_router(products_router)
app.include_router(providers_router)
app.include_router(inventory_router)
app.include_router(sales_router)
app.include_router(customers_router)
app.include_router(dashboard_router)
app.include_router(tasks_router)
app.include_router(ocr_router)

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "API de ManusOdoo - Dashboard de Electrodomésticos",
        "version": config.API_VERSION,
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Endpoint de verificación de salud"""
    return {
        "status": "healthy",
        "version": config.API_VERSION
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_new:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Cambiado a False
        log_level="info"
    )
