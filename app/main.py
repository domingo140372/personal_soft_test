## app/main.py
"""
Archivo principal para arrancar la aplicación FastAPI.
Aquí se definen los endpoints, dependencias, seguridad, middlewares y conexiones externas.
"""

import os
from typing import List, Annotated, Optional
from datetime import timedelta, datetime, timezone

# FastAPI y dependencias
from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session

# JWT
from jose import JWTError, jwt

# Base de datos y modelos
from .database import create_db_and_tables, get_session
from .models import User, Token
from .schemas import UserCreate, UserUpdate, UserRead, MessageResponse, MessageCreate
from .services import get_message_service, MessageService
from .crud import (
    create_user_db,
    get_user_by_username,
    update_user_db,
    soft_delete_user_db,
    verify_password,
    get_all_users,
)

# Configuración centralizada desde config.py
from .config import (
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REDIS_URL,
)

# Redis
from redis.asyncio import Redis

# Middleware de limitación de tasa
from .middlewares import RedisRateLimitMiddleware

# OAuth2 scheme para autenticación con JWT
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Crear aplicación FastAPI
app = FastAPI(
    title="Api_MENSAJES",
    description="API para la gestión de usuarios y mensajes con JWT y Redis",
    version="1.1.0",
)

# ---------------------------------------------------------------------------
# JWT: creación y validación de tokens
# ---------------------------------------------------------------------------

def create_access_token(data: dict, expires_delta: timedelta):
    """Crea un token JWT con expiración."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[Session, Depends(get_session)],
):
    """Obtiene el usuario actual a partir del token JWT."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user_by_username(username=username, session=session)
    if user is None:
        raise credentials_exception
    return user


async def get_all_users_list(session: Annotated[Session, Depends(get_session)]):
    """Obtiene el listado de todos los usuarios."""
    return get_all_users(session=session)

# ---------------------------------------------------------------------------
# Eventos de la aplicación (startup y shutdown)
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def on_startup():
    """
    Inicializa la base de datos y el cliente de Redis al inicio de la aplicación.
    También agrega el middleware de limitación de tasa.
    """
    # Crear tablas en la BD (ejemplo con SQLite)
    create_db_and_tables()

    # Inicializar Redis y guardarlo en el estado de la app
    app.state.redis = Redis.from_url(REDIS_URL, decode_responses=True)

    # Agregar middleware de rate limiting usando Redis
    app.add_middleware(RedisRateLimitMiddleware, redis_client=app.state.redis)


@app.on_event("shutdown")
async def on_shutdown():
    """
    Cierra la conexión con Redis cuando se apaga la aplicación.
    """
    await app.state.redis.close()

# ---------------------------------------------------------------------------
# Endpoints de autenticación y gestión de usuarios
# ---------------------------------------------------------------------------

@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[Session, Depends(get_session)],
):
    """Ruta para el login y obtención del token."""
    user = get_user_by_username(username=form_data.username, session=session)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/users/", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user(
    user: UserCreate,
    session: Annotated[Session, Depends(get_session)],
):
    """Ruta para crear un nuevo usuario."""
    db_user = get_user_by_username(user.username, session)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya está registrado.",
        )
    return create_user_db(user, session)


@app.put("/users/{user_id}", response_model=User)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Ruta para actualizar un usuario (requiere autenticación)."""
    db_user = update_user_db(user_id, user_update, session)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado.",
        )
    return db_user


@app.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Ruta para borrar lógicamente un usuario (requiere autenticación)."""
    response = soft_delete_user_db(user_id, session)
    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado.",
        )
    return response


@app.get("/users/me", response_model=User)
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    """Ruta para obtener el usuario actual (requiere autenticación)."""
    return current_user


@app.get("/users/all", response_model=List[UserRead])
async def read_users_all(users: Annotated[User, Depends(get_all_users_list)]):
    """Ruta para obtener listado de usuarios."""
    return users

# ---------------------------------------------------------------------------
# Endpoints de mensajes
# ---------------------------------------------------------------------------

@app.post("/api/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def create_message_endpoint(
    message: MessageCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    message_service: Annotated[MessageService, Depends(get_message_service)],
):
    """
    Crea un nuevo mensaje, lo procesa y devuelve una respuesta.
    La lógica de negocio es manejada por el servicio.
    """
    try:
        db_message = message_service.process_and_create_message(current_user.id, message)
        return db_message
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno del servidor al procesar el mensaje: {e}",
        )


@app.get("/api/messages/{session_id}", response_model=List[MessageResponse])
def get_messages_in_session(
    session_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    message_service: Annotated[MessageService, Depends(get_message_service)],
    limit: Annotated[int, Query(le=100, description="Límite de mensajes a devolver")] = 100,
    offset: Annotated[int, Query(ge=0, description="Número de mensajes a omitir")] = 0,
    sender: Annotated[Optional[str], Query(description="Filtrar por remitente ('user' o 'system')")] = None,
):
    """
    Recupera todos los mensajes de una sesión dada.
    """
    messages = message_service.get_messages(session_id, limit, offset, sender)
    return messages
