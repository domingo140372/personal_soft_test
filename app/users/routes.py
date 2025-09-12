#### routes de Users
# app/users/routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Annotated
from sqlmodel import Session

from app.database import get_session
from .schemas import UserCreate, UserUpdate, UserRead
from .crud import create_user_db, update_user_db, soft_delete_user_db, get_user_by_username, verify_password
from .models import User
from app.users.auth import router as auth_router  # no usado aquí, auth se registra desde routes.init_routes

router = APIRouter()

@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, session: Annotated[Session, Depends(get_session)]):
    db_user = get_user_by_username(user.username, session)
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El nombre de usuario ya está registrado.")
    new_user = create_user_db(user, session)
    return new_user

@router.put("/{user_id}", response_model=UserRead)
def update_user(user_id: str, user_update: UserUpdate, session: Annotated[Session, Depends(get_session)], current_user: Annotated[User, Depends(lambda: None)] = None):
    # current_user dependency can be connected to real get_current_user (see auth integration)
    updated = update_user_db(user_id, user_update, session)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")
    return updated

@router.delete("/{user_id}")
def delete_user(user_id: str, session: Annotated[Session, Depends(get_session)], current_user: Annotated[User, Depends(lambda: None)] = None):
    ok = soft_delete_user_db(user_id, session)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado.")
    return {"status": "success"}
