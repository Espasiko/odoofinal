from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
import os
import uuid
import shutil
from typing import Dict, Any
import logging
from ..models.user import User
from ..dependencies import get_current_user

# Configuración de logger
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/files",
    tags=["files"],
    responses={404: {"description": "No encontrado"}},
)

# Directorio para archivos temporales
TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "temp")
os.makedirs(TEMP_DIR, exist_ok=True)

# URL base para acceder a los archivos
BASE_URL = os.environ.get("API_URL", "http://localhost:8000")

@router.post("/upload-temp", response_model=Dict[str, Any])
async def upload_temp_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Sube un archivo temporal y devuelve una URL accesible
    """
    try:
        # Generar un nombre único para el archivo
        file_extension = os.path.splitext(file.filename)[1] if file.filename else ".pdf"
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(TEMP_DIR, unique_filename)
        
        # Guardar el archivo
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Crear URL accesible
        file_url = f"{BASE_URL}/temp/{unique_filename}"
        
        logger.info(f"Archivo temporal subido: {file_path}, URL: {file_url}")
        
        return {
            "filename": unique_filename,
            "url": file_url,
            "original_filename": file.filename,
            "size": str(os.path.getsize(file_path))
        }
    except Exception as e:
        logger.error(f"Error al subir archivo temporal: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al subir archivo temporal: {str(e)}"
        )
