## app/main.py
"""
Archivo principal para arrancar la aplicación FastAPI.
Contiene endpoints, autenticación JWT, integración con la base de datos
y la inicialización del cliente Redis + registro del middleware de rate limit.
"""

from typing import List, Annotated, Optional
from datetime import timedelta, datetime, timezone
import socketio # para recibir y enviar notificaciones en tiempo real

# FastAPI y dependencias
from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session

# JWT (python-jose)
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

# Configuración centralizada
from .config import settings

# Redis async client
from redis.asyncio import Redis

# Middleware de rate limiting (archivo: app/middleware/rate_limit.py)
# IMPORTANTE: asegúrate de que el módulo exista en app/middleware/rate_limit.py
from .middlewares.rate_limit import RedisRateLimitMiddleware

# OAuth2 scheme (tokenUrl apunta a /token)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# ---------------------------------------------------------------------------
# Variables de configuración (desde settings)
# ---------------------------------------------------------------------------
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = getattr(settings, "ACCESS_TOKEN_EXPIRE_MINUTES", 120)

# Redis connection params (usamos host/port/db en settings)
REDIS_HOST = settings.REDIS_HOST
REDIS_PORT = settings.REDIS_PORT
REDIS_DB = settings.REDIS_DB

# Rate limit defaults (de settings)
RATE_LIMIT = settings.RATE_LIMIT
RATE_WINDOW = settings.RATE_LIMIT_WINDOW

# ---------------------------------------------------------------------------
# Crear la aplicación y registrar middleware (antes del arranque)
# ---------------------------------------------------------------------------

sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")
app = FastAPI(
    title="Api_MENSAJES",
    description="API para la gestión de usuarios y mensajes con JWT y Redis",
    version="1.1.0",
)
app_sio = socketio.ASGIApp(sio, other_asgi_app=app)

# Registrar el middleware YA (no en startup). Pasamos redis_client=None temporalmente.
# En startup inyectaremos el cliente real en el middleware.
app.add_middleware(
    RedisRateLimitMiddleware,
    redis_client=None,     # se completará en startup
    rate_limit=RATE_LIMIT,
    time_window=RATE_WINDOW,
)

# ---------------------------------------------------------------------------
# Helpers JWT
# ---------------------------------------------------------------------------
def create_access_token(data: dict, expires_delta: timedelta):
    """
    Crea un token JWT firmado con SECRET_KEY y con expiración.
    - data: dict con payload (por ejemplo {"sub": username})
    - expires_delta: timedelta con duración
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[Session, Depends(get_session)],
):
    """
    Dependencia: decodifica el token y devuelve el usuario de la base de datos.
    Lanza 401 si el token o el usuario no son válidos.
    """
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


# ---------------------------------------------------------------------------
# Dependencias auxiliares
# ---------------------------------------------------------------------------
async def get_all_users_list(session: Annotated[Session, Depends(get_session)]):
    """Obtiene el listado de usuarios activos desde el repositorio (crud)."""
    return get_all_users(session=session)


# ---------------------------------------------------------------------------
# Eventos: startup / shutdown
# - En startup: crear tablas y conectar Redis; inyectar redis_client en middleware ya registrado.
# - En shutdown: cerrar conexión Redis.
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def on_startup():
    # 1) Inicializar/crear tablas DB
    create_db_and_tables()

    # 2) Crear cliente Redis y guardar en app.state
    app.state.redis = Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

    # 3) Inyectar el redis_client real dentro de la configuración del middleware registrado.
    #    Evitamos llamar a add_middleware() aquí (eso causa el RuntimeError).
    for mw in app.user_middleware:
        # mw.options es el dict que contiene las opciones pasadas a add_middleware
        if "redis_client" in mw.options and mw.options["redis_client"] is None:
            mw.options["redis_client"] = app.state.redis


@app.on_event("shutdown")
async def on_shutdown():
    # Cerrar redis si existe
    if hasattr(app.state, "redis"):
        try:
            await app.state.redis.close()
        except Exception:
            # no crítico; loggear si quieres
            pass

# Eventos de Socket.IO
# este parte falta configurar de una manera mas completa
# por ahora solo estoy atendiendo a las solicitudes de la prueba
# pero se puede mejorar usando un archi aparte llamado events.py
# donde podramos capturar eventos como envio de mensajes o notificaciones
# al mismo tiempo habria que capturar los enventos en el front con JS
@sio.event
async def connect(sid, environ):
    print(f"Cliente conectado: {sid}")

@sio.event
async def disconnect(sid):
    print(f"Cliente desconectado: {sid}")

@sio.event
async def send_message(sid, data):
    print(f"Mensaje recibido de {sid}: {data}")
    await sio.emit("new_message", {"msg": data}, skip_sid=sid)

# ---------------------------------------------------------------------------
# Endpoints: auth, users y mensajes (mantengo tu estructura original)
# ---------------------------------------------------------------------------
@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[Session, Depends(get_session)],
):
    """Login y generación de token JWT (OAuth2 password flow)."""
    user = get_user_by_username(username=form_data.username, session=session)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/users/", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user(
    user: UserCreate,
    session: Annotated[Session, Depends(get_session)],
):
    """Crear usuario nuevo."""
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
    """Actualizar usuario (requiere token válido)."""
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
    """Borrado lógico de un usuario (requiere token)."""
    response = soft_delete_user_db(user_id, session)
    if not response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado.",
        )
    return response


@app.get("/users/me", response_model=User)
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    """Obtener datos del usuario autenticado."""
    return current_user


@app.get("/users/all", response_model=List[UserRead])
async def read_users_all(users: Annotated[User, Depends(get_all_users_list)]):
    """Listado de usuarios activos."""
    return users


# ---------------------------------------------------------------------------
# Mensajería
# ---------------------------------------------------------------------------
@app.post("/api/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def create_message_endpoint(
    message: MessageCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    message_service: Annotated[MessageService, Depends(get_message_service)],
):
    """
    Crea y procesa un mensaje (usa la capa de services).
    """
    try:
        db_message = message_service.process_and_create_message(current_user.id, message)
        return db_message
    except HTTPException:
        raise
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
    """Recuperar mensajes de una sesión con paginación y filtro opcional."""
    messages = message_service.get_messages(session_id, limit, offset, sender)
    return messages
