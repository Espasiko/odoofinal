from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from pathlib import Path

# Importar configuración
from api.utils.config import config

# Importar rutas
from api.routes.auth import router as auth_router
from api.routes.products import router as products_router
from api.routes.providers import router as providers_router
# from api.routes.inventory import router as inventory_router
# from api.routes.sales import router as sales_router
# from api.routes.customers import router as customers_router
# from api.routes.dashboard import router as dashboard_router
# from api.routes.tasks import router as tasks_router
# from api.routes.ocr import router as ocr_router
from api.routes.mistral_ocr import router as mistral_ocr_router
from api.routes.invoices import router as invoices_router

from api.routes.web_ui import router as web_ui_router
from api.routes.mistral_llm_excel import router as mistral_llm_excel_router
from api.routes.excel_importer import router as excel_importer_router

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

# Configurar archivos estáticos
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Incluir rutas de API
app.include_router(auth_router)
app.include_router(products_router)
app.include_router(providers_router)
# app.include_router(inventory_router)
# app.include_router(sales_router)
# app.include_router(customers_router)
# app.include_router(dashboard_router)
# app.include_router(tasks_router)
# app.include_router(ocr_router)
app.include_router(mistral_ocr_router)
app.include_router(invoices_router)

app.include_router(mistral_llm_excel_router)
app.include_router(excel_importer_router)

# Incluir rutas de interfaz web (al final para que no interfieran con las API)
app.include_router(web_ui_router)

# El endpoint raíz ahora se maneja en web_ui_router

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
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
