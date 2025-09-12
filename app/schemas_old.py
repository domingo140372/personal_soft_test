## archivo donde creamos los esquemas a usar  para interactuar con la BD
from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    """Esquema para la creación de un nuevo usuario."""
    username: str
    email: str
    password: str
    full_name: Optional[str] = None
    created_at: datetime

class UserUpdate(BaseModel):
    """Esquema para la actualización de un usuario."""
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None

class Login(BaseModel):
    """Esquema para la solicitud de login."""
    username: str
    password: str

class UserRead(BaseModel):
    id: UUID
    username: str
    email: str
    full_name: str | None = None
    is_active: bool
    create_at: datetime

    class Config:
        from_attributes = True  


""" Esquemas para el manejo de mensajes """
class MessageCreate(BaseModel):
    """Esquema para la creación de un nuevo mensaje desde el cliente."""
    session_id: str
    content: str
    sender: str

class MessageMetaData(BaseModel):
    """ Metadata del los mensajes """
    word_count: int
    character_count: int
    created_at: datetime

class MessageResponse(BaseModel):
    """Esquema completo para la respuesta del mensaje."""
    message_id: str
    session_id: str
    user_id: UUID
    content: str
    created_at: datetime
    sender: str
    metadata: MessageMetaData

