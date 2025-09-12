### auth of Users

# app/users/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session
from datetime import timedelta
from typing import Annotated

from app.config import settings
from app.database import get_session
from .crud import get_user_by_username, verify_password
from app.users.schemas import UserRead
from jose import jwt

router = APIRouter()

def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": ( __import__("datetime").datetime.utcnow() + expire )})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

@router.post("/token")
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session: Annotated[Session, Depends(get_session)]):
    user = get_user_by_username(username=form_data.username, session=session)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario o contraseña incorrectos", headers={"WWW-Authenticate": "Bearer"})
    access_token = create_access_token({"sub": user.username}, expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": access_token, "token_type": "bearer"}
