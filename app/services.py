# app/services.py

from sqlmodel import Session
from fastapi import HTTPException, status, Depends
from typing import Annotated
from .schemas import MessageCreate
from .crud import create_db_message, get_messages_by_session_id
from .database import get_session
from uuid import UUID

class MessageService:
    def __init__(self, session: Session):
        self.session = session
    
    def process_and_create_message(self, user_id: UUID, message: MessageCreate):
        """
        Pipeline de procesamiento de mensajes (lógica de negocio).
        1. Valida y filtra el contenido.
        2. Agrega metadatos.
        3. Almacena usando el repositorio.
        """
        
        # 1. Validación y Filtrado de Contenido (simple)
        inappropriate_words = ["negro", "gordo", "feo", "maldito"]
        if any(word in message.content.lower() for word in inappropriate_words):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El mensaje contiene contenido inapropiado."
            )

        # 2. Agregar Metadatos
        word_count = len(message.content.split())
        message_length = len(message.content)

        # 3. Usar el repositorio para almacenar en la base de datos
        db_message = create_db_message(
            session=self.session,
            user_id=user_id,
            session_id=message.session_id,
            content=message.content,
            sender=message.sender,
            message_length=message_length,
            word_count=word_count
        )
        
        return db_message

    def get_messages(self, session_id: str, limit: int, offset: int, sender: str):
        """Obtiene mensajes usando el repositorio."""
        return get_messages_by_session_id(
            session_id=session_id,
            session=self.session,
            limit=limit,
            offset=offset,
            sender=sender
        )

# Para usar Inyección de Dependencias en FastAPI
def get_message_service(session: Annotated[Session, Depends(get_session)]):
    return MessageService(session=session)