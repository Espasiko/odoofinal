from typing import Optional
from pydantic import BaseModel

class ProviderCreate(BaseModel):
    nombre: Optional[str] = None
    name: Optional[str] = None
    correo: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    phone: Optional[str] = None
    comentario: Optional[str] = None
    comment: Optional[str] = None
    # Otros campos opcionales para compatibilidad con el frontend