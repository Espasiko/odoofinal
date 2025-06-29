from datetime import datetime, timedelta
from typing import Optional
import jwt
import logging
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from uuid import uuid4

from ..models.schemas import User, UserInDB, TokenData
from ..utils.config import config

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        return plain_password == hashed_password

    @staticmethod
    def get_user(db: dict, username: str) -> Optional[UserInDB]:
        if username in db:
            user_dict = db[username]
            return UserInDB(**user_dict)
        return None

    @classmethod
    def authenticate_user(cls, fake_db: dict, username: str, password: str) -> Optional[UserInDB]:
        user = cls.get_user(fake_db, username)
        if not user or not cls.verify_password(password, user.hashed_password):
            return None
        return user

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)

    def get_user_from_token(self, token: str) -> UserInDB:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        if not token:
            logger.error("No se recibió ningún token para validación.")
            raise credentials_exception

        try:
            logger.info(f"Intentando decodificar token: {token[:30]}...")
            payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                logger.error("El token no contiene el campo 'sub' (username).")
                raise credentials_exception
            token_data = TokenData(username=username)
        except jwt.ExpiredSignatureError:
            logger.error("El token ha expirado.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.PyJWTError as e:
            logger.error(f"Error de validación de JWT: {e}")
            raise credentials_exception
        
        user = self.get_user(fake_users_db, username=token_data.username)
        if user is None:
            logger.error(f"Usuario '{token_data.username}' no encontrado en la base de datos.")
            raise credentials_exception
        
        logger.info(f"Token validado exitosamente para el usuario: {user.username}")
        return user

# Instancia del servicio
auth_service = AuthService()

# Funciones de dependencia para usar en las rutas
async def get_current_user(request: Request, token: str = Depends(oauth2_scheme)) -> UserInDB:
    logger.info(f"Authorization header recibido: {request.headers.get('Authorization')}")
    return auth_service.get_user_from_token(token)

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
