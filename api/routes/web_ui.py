from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
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