from datetime import datetime, timedelta
from typing import Optional
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from uuid import uuid4

from ..models.schemas import User, UserInDB, TokenData
from ..utils.config import config

# Esquema de autenticación
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Base de datos simulada (en memoria)
fake_users_db = {
    "admin": {
        "username": "admin",
        "full_name": "Administrador",
        "email": "admin@example.com",
        "hashed_password": "admin_password_secure",
        "disabled": False,
    },
    "yo@mail.com": {
        "username": "yo@mail.com",
        "full_name": "Usuario Odoo",
        "email": "yo@mail.com",
        "hashed_password": "admin",
        "disabled": False,
    }
}

class AuthService:
    """Servicio de autenticación y autorización"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verifica la contraseña (en un entorno real, usaríamos bcrypt)"""
        return plain_password == hashed_password
    
    @staticmethod
    def get_user(db: dict, username: str) -> Optional[UserInDB]:
        """Obtiene un usuario de la base de datos"""
        if username in db:
            user_dict = db[username]
            return UserInDB(**user_dict)
        return None
    
    @classmethod
    def authenticate_user(cls, fake_db: dict, username: str, password: str) -> Optional[UserInDB]:
        """Autentica un usuario"""
        user = cls.get_user(fake_db, username)
        if not user:
            return None
        if not cls.verify_password(password, user.hashed_password):
            return None
        return user
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Crea un token de acceso JWT"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
        return encoded_jwt
    
    async def get_current_user(self, token: str = Depends(oauth2_scheme)) -> UserInDB:
        """Obtiene el usuario actual desde el token"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
            token_data = TokenData(username=username)
        except jwt.PyJWTError:
            raise credentials_exception
        user = self.get_user(fake_users_db, username=token_data.username)
        if user is None:
            raise credentials_exception
        return user
    
    async def get_current_active_user(self, token: str = Depends(oauth2_scheme)) -> User:
        """Obtiene el usuario actual activo"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
            token_data = TokenData(username=username)
        except jwt.PyJWTError:
            raise credentials_exception
        user = self.get_user(fake_users_db, username=token_data.username)
        if user is None:
            raise credentials_exception
        if user.disabled:
            raise HTTPException(status_code=400, detail="Inactive user")
        return user
    
    @staticmethod
    def generate_session_id() -> str:
        """Genera un ID de sesión único"""
        return str(uuid4())

# Instancia del servicio
auth_service = AuthService()

# Función de conveniencia para usar en las rutas
async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    """Función de conveniencia para obtener el usuario actual"""
    return await auth_service.get_current_user(token)
