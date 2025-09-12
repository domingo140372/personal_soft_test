###### routes of messages
# app/messages/routes.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional, Annotated
from sqlmodel import Session
from uuid import UUID
from app.database import get_session
from .schemas import MessageCreate, MessageResponse
from .crud import create_db_message, get_messages_by_session_id
from app.users.crud import get_user_by_username  # optional
from app.services import MessageService, get_message_service

router = APIRouter()

@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def create_message(message: MessageCreate, message_service: Annotated[MessageService, Depends(get_message_service)], current_user: Annotated[object, Depends(lambda: None)] = None):
    # current_user placeholder — wire real auth dependency in integration
    try:
        # Here message_service will compute metadata and persist by calling create_db_message (in services you can import that)
        db_msg = message_service.process_and_create_message(UUID(int=0), message)  # replace user id properly in integration
        return db_msg
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{session_id}", response_model=List[MessageResponse])
def get_messages(session_id: str, message_service: Annotated[MessageService, Depends(get_message_service)], limit: Annotated[int, Query(le=100)] = 100, offset: Annotated[int, Query(ge=0)] = 0, sender: Optional[str] = None):
    msgs = message_service.get_messages(session_id, limit, offset, sender)
    return msgs
