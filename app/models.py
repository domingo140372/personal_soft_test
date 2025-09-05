## modelos para crear las relaciones entre entidades
from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime


class User(SQLModel, table=True):
    """Modelo de la tabla de usuarios."""
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    password_hash: str
    is_active: bool = Field(default=True)
    full_name: Optional[str] = Field(default=None)
    create_at: datetime = datetime.now()

class Token(SQLModel):
    """Modelo para el token de autenticación."""
    access_token: str
    token_type: str = "bearer"
