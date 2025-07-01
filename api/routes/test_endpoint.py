from fastapi import APIRouter, UploadFile, File, Depends
from fastapi.responses import JSONResponse
from ..models.schemas import User
from ..services.auth_service import get_current_user

router = APIRouter(
    prefix="/api/v1/test",
    tags=["Test Endpoint"],
    responses={404: {"description": "Not found"}}
)

@router.post("/upload-test")
def upload_test(file: UploadFile = File(...), current_user: User = Depends(get_current_user)) -> JSONResponse:
    return JSONResponse(content={
        "message": "Archivo recibido con éxito",
        "filename": file.filename
    })
