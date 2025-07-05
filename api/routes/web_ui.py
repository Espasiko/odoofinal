from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
import os
from pathlib import Path

# Configurar templates
template_dir = Path(__file__).parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(template_dir))

router = APIRouter(
    tags=["Web UI"],
    responses={404: {"description": "Not found"}}
)

@router.get("/{full_path:path}", response_class=HTMLResponse)
async def serve_react_app(request: Request, full_path: str):
    """
    Servir la aplicación React para cualquier ruta que no sea API
    Esto permite que las rutas del frontend funcionen correctamente al recargar la página
    """
    # Verificar si es una ruta de API o una ruta existente
    if full_path.startswith("api/") or full_path in ["ocr", "mapeo", "docs-ui", "health", "docs", "redoc", "openapi.json"]:
        # No manejar rutas de API o rutas ya definidas
        return HTMLResponse(content="Not Found", status_code=404)
    
    # Servir el archivo index.html para cualquier otra ruta
    # Primero intentamos servirlo desde la raíz del proyecto
    frontend_path = Path(__file__).parent.parent.parent / "index.html"
    
    if frontend_path.exists():
        return FileResponse(frontend_path)
    
    # Si no está en la raíz, intentamos en /static
    static_frontend_path = Path(__file__).parent.parent.parent / "static" / "index.html"
    if static_frontend_path.exists():
        return FileResponse(static_frontend_path)
    
    # Si no existe el archivo index.html en ninguna ubicación, mostrar error
    return HTMLResponse(
        content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Error: Archivo no encontrado</title>
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; text-align: center; }
                .error { color: red; font-weight: bold; }
            </style>
        </head>
        <body>
            <h1 class="error">Error: No se encontró el archivo index.html</h1>
            <p>No se pudo encontrar el archivo principal de la aplicación React.</p>
        </body>
        </html>
        """,
        status_code=404
    )

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
    Página principal - redirige a la interfaz de Mistral OCR
    """
    return templates.TemplateResponse("mistral_ocr.html", {"request": request})

@router.get("/ocr", response_class=HTMLResponse)
async def mistral_ocr_ui(request: Request):
    """
    Interfaz web para Mistral OCR
    
    Proporciona una interfaz gráfica moderna para:
    - Subir documentos (PDF, PNG, JPG, JPEG, AVIF)
    - Procesar con IA de Mistral
    - Visualizar resultados del OCR
    - Descargar texto extraído
    """
    return templates.TemplateResponse("mistral_ocr.html", {"request": request})

@router.get("/mapeo", response_class=HTMLResponse)
async def mapeo_ui(request: Request):
    """
    Interfaz web para mapeo de datos de proveedores
    """
    # Obtener archivos disponibles (esto se puede mejorar)
    archivos_ejemplo = []
    archivos_subidos = []
    archivos_odoo = []
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "archivos_ejemplo": archivos_ejemplo,
        "archivos_subidos": archivos_subidos,
        "archivos_odoo": archivos_odoo
    })

@router.get("/docs-ui", response_class=HTMLResponse)
async def docs_redirect(request: Request):
    """
    Redirigir a la documentación de la API
    """
    return HTMLResponse(
        content="""
        <!DOCTYPE html>
        <html>
        <head>
            <meta http-equiv="refresh" content="0; url=/docs">
            <title>Redirigiendo a la documentación...</title>
        </head>
        <body>
            <p>Redirigiendo a la <a href="/docs">documentación de la API</a>...</p>
        </body>
        </html>
        """
    )