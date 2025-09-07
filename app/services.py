# app/services.py

from __future__ import annotations

from typing import Annotated, Optional
from uuid import UUID

from fastapi import Depends, status
from sqlmodel import Session

from .schemas import MessageCreate
from .crud import create_db_message, get_messages_by_session_id
from .database import get_session


# =============================
# Excepción de dominio (servicio)
# =============================

class ServiceError(Exception):
    """
    Excepción de dominio para la capa de servicios.
    No devuelve HTTP directamente; el handler global en FastAPI
    se encargará de transformar esto al JSON estándar:
    {
      "status": "error",
      "error": { "code": "...", "message": "...", "details": "..." }
    }
    """
    def __init__(
        self,
        code: str,
        message: str,
        details: Optional[str] = None,
        http_status: int = status.HTTP_400_BAD_REQUEST,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details
        self.http_status = http_status


# =============================
# Servicio de Mensajes
# =============================

ALLOWED_SENDERS = {"user", "system"}
INAPPROPRIATE_WORDS = {
    "insultos": ["negro", "gordo", "feo", "maldito"],
    "groserias": ["puta", "mierda", "carajo"],
    "ofensivos": ["idiota", "imbecil", "estupido"],
}


class MessageService:
    def __init__(self, session: Session):
        self.session = session

    def process_and_create_message(self, user_id: UUID, message: MessageCreate):
        """
        Pipeline de procesamiento de mensajes (lógica de negocio).
        1) Validaciones de formato y contenido
        2) Cálculo de metadatos
        3) Persistencia
        """

        # 1) Validaciones
        # 1.1 Sender válido
        if message.sender not in ALLOWED_SENDERS:
            raise ServiceError(
                code="INVALID_FORMAT",
                message="Formato de mensaje inválido",
                details="El campo 'sender' debe ser 'user' o 'system'",
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        # 1.2 Contenido no vacío
        if not message.content or not message.content.strip():
            raise ServiceError(
                code="EMPTY_CONTENT",
                message="Contenido de mensaje vacío",
                details="El campo 'content' no puede estar vacío",
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        # 1.3 Filtrado de contenido inapropiado
        content_lower = message.content.lower()
        for category, words in INAPPROPRIATE_WORDS.items():
            if any(bad in content_lower for bad in words):
                raise ServiceError(
                    code="INAPPROPRIATE_CONTENT",
                    message="Contenido inapropiado detectado",
                    details=f"El contenido incluye palabras no permitidas de la categoría '{category}'",
                    http_status=status.HTTP_400_BAD_REQUEST,
                )
        # 2) Metadatos
        word_count = len(message.content.split())
        message_length = len(message.content)

        # 3) Persistencia
        db_message = create_db_message(
            session=self.session,
            user_id=user_id,
            session_id=message.session_id,
            content=message.content,
            sender=message.sender,
            message_length=message_length,
            word_count=word_count,
        )
        return db_message

    def get_messages(self, session_id: str, limit: int, offset: int, sender: Optional[str]):
        """Obtiene mensajes usando el repositorio, con validación opcional de sender."""
        if sender is not None and sender not in ALLOWED_SENDERS:
            raise ServiceError(
                code="INVALID_FILTER",
                message="Filtro inválido",
                details="El parámetro 'sender' (si se envía) debe ser 'user' o 'system'",
                http_status=status.HTTP_400_BAD_REQUEST,
            )

        return get_messages_by_session_id(
            session_id=session_id,
            session=self.session,
            limit=limit,
            offset=offset,
            sender=sender,
        )


# =============================
# Inyección de dependencias
# =============================

def get_message_service(session: Annotated[Session, Depends(get_session)]):
    return MessageService(session=session)
