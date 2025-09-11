#### schemas of messages
from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from datetime import datetime


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

    class Config:
        orm_mode = True

