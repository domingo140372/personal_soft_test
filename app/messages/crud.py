#### cruds of messages

# app/messages/crud.py
from sqlmodel import Session, select
from .models import Message
from typing import List, Optional
from uuid import UUID

def create_db_message(session: Session, user_id: UUID, session_id: str, content: str, sender: str, message_length: int, word_count: int) -> Message:
    msg = Message(
        session_id=session_id,
        content=content,
        sender=sender,
        user_id=user_id,
        message_length=message_length,
        word_count=word_count
    )
    session.add(msg)
    session.commit()
    session.refresh(msg)
    return msg

def get_messages_by_session_id(session: Session, session_id: str, limit: int = 100, offset: int = 0, sender: Optional[str] = None) -> List[Message]:
    statement = select(Message).where(Message.session_id == session_id)
    if sender:
        statement = statement.where(Message.sender == sender)
    statement = statement.limit(limit).offset(offset)
    return session.exec(statement).all()
