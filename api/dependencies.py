from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
import logging

from .models.user import User
from .services.auth_service import auth_service

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Esquema de autenticación
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(request: Request, token: str = Depends(oauth2_scheme)) -> User:
    """
    Valida el token JWT y devuelve el usuario actual si es válido.
    """
    try:
        user_in_db = auth_service.get_user_from_token(token)
        return User(
            username=user_in_db.username,
            email=user_in_db.email,
            full_name=user_in_db.full_name,
            disabled=user_in_db.disabled
        )
    except Exception as e:
        logger.error(f"Error al obtener usuario desde token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Verifica que el usuario actual esté activo.
    """
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
