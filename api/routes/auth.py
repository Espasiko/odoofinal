from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from typing import Annotated

from ..models.schemas import Token, User, SessionResponse
from ..services.auth_service import auth_service, fake_users_db, get_current_active_user
from ..utils.config import config

router = APIRouter(tags=["authentication"])

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    """Endpoint para autenticación y obtención de token"""
    user = auth_service.authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_service.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

@router.get("/session", response_model=SessionResponse)
async def get_session(current_user: User = Depends(get_current_active_user)) -> SessionResponse:
    """Obtiene información de la sesión actual y refresca el token."""
    access_token_expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = auth_service.create_access_token(
        data={"sub": current_user.username}, expires_delta=access_token_expires
    )
    return SessionResponse(
        access_token=new_access_token,
        token_type="bearer",
        user=current_user
    )
