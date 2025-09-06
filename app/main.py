## archivo  principal para arrancar la aplicacion

from typing import List, Annotated, Optional
from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import timedelta, datetime, timezone
from jose import JWTError, jwt
from .database import create_db_and_tables, get_session
from .models import User, Token
from .schemas import UserCreate, UserUpdate, Login, MessageCreate, MessageResponse
from .crud import (
    create_user_db, 
    get_user_by_username, 
    update_user_db, 
    soft_delete_user_db,
    verify_password,
    process_and_create_message_db, 
    get_messages_by_session_id
)
from sqlmodel import Session

# (Tus otras importaciones y código existente)
# Secreto y algoritmo para los tokens JWT
SECRET_KEY = ""
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120

# Dependencia para el token OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI(
        title="Api_MENSAJES",  
        description="API para la gestión de mensajes", 
        version="1.1.0", 
    )

def create_access_token(data: dict, expires_delta: timedelta):
    """Crea un token de acceso JWT con tiempo de expiración."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], session: Annotated[Session, Depends(get_session)]):
    """Dependencia para obtener el usuario actual a partir del token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user_by_username(username=username, session=session)
    if user is None:
        raise credentials_exception
    return user

@app.on_event("startup")
def on_startup():
    """Inicializa la base de datos al inicio de la aplicación."""
    create_db_and_tables()

@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], 
    session: Annotated[Session, Depends(get_session)]
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
    session: Annotated[Session, Depends(get_session)]
):
    """Ruta para crear un nuevo usuario."""
    db_user = get_user_by_username(user.username, session)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya está registrado."
        )
    return create_user_db(user, session)

@app.put("/users/{user_id}", response_model=User)
def update_user(
    user_id: int, 
    user_update: UserUpdate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Ruta para actualizar un usuario (requiere autenticación)."""
    db_user = update_user_db(user_id, user_update, session)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado."
        )
    return db_user

@app.delete("/users/{user_id}")
def delete_user(
    user_id: int, 
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Ruta para borrar lógicamente un usuario (requiere autenticación)."""
    response = soft_delete_user_db(user_id, session)
    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado."
        )
    return response

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    """Ruta para obtener el usuario actual (requiere autenticación)."""
    return current_user

@app.post("/api/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def create_message_endpoint(
    message: MessageCreate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Crea un nuevo mensaje, lo procesa y devuelve una respuesta.
    - **message**: Datos del mensaje a enviar (session_id, content, sender).
    - Requiere autenticación (token JWT).
    """
    try:
        db_message = process_and_create_message_db(current_user.id, message, session)
        return db_message
    except HTTPException as e:
        # Reenvía las excepciones HTTP del CRUD
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar el mensaje: {e}"
        )

@app.get("/api/messages/{session_id}", response_model=List[MessageResponse])
def get_messages_in_session(
    session_id: str,
    session: Annotated[Session, Depends(get_session)],
    limit: Annotated[int, Query(le=100, description="Límite de mensajes a devolver")] = 100,
    offset: Annotated[int, Query(ge=0, description="Número de mensajes a omitir")] = 0,
    sender: Annotated[Optional[str], Query(description="Filtrar por remitente ('user' o 'system')")] = None,
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Recupera todos los mensajes de una sesión dada.
    - **session_id**: El ID de la sesión.
    - Opcionalmente, se puede filtrar por 'sender' y usar paginación.
    """
    messages = get_messages_by_session_id(session_id, session, limit, offset, sender)
    return messages