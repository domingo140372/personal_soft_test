## archivo donde creamos los esquemas a usar  para interactuar con la BD
from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    """Esquema para la creación de un nuevo usuario."""
    username: str
    email: str
    password: str
    full_name: Optional[str] = None
    created_at: str

class UserUpdate(BaseModel):
    """Esquema para la actualización de un usuario."""
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None

class Login(BaseModel):
    """Esquema para la solicitud de login."""
    username: str
    password: str

