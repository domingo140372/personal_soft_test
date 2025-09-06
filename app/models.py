## modelos para crear las relaciones entre entidades
from typing import Optional
from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime, timezone
from uuid import UUID, uuid4

class User(SQLModel, table=True):
    """Modelo de la tabla de usuarios con UUID."""
    id: Optional[UUID] = Field(default_factory=uuid4, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: str = Field(index=True, unique=True)
    password_hash: str
    is_active: bool = Field(default=True)
    full_name: Optional[str] = Field(default=None)
    create_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    messages: list["Message"] = Relationship(back_populates="user")

class Message(SQLModel, table=True):
    """Modelo para los mensajes con todos los metadatos."""
    message_id: Optional[str] = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    session_id: str = Field(index=True)
    user_id: UUID = Field(foreign_key="user.id")
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sender: str  # 'user' o 'system'
    message_length: int
    word_count: int
    
    user: User = Relationship(back_populates="messages")

class Token(SQLModel):
    """Modelo para el token de autenticación."""
    access_token: str
    token_type: str = "bearer"
    create_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
