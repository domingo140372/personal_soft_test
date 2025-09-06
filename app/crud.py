## archivo para crear las consultas a la BD
from sqlmodel import Session, select, func
from passlib.context import CryptContext
from fastapi import HTTPException, status
from .models import User, Message
from .schemas import UserCreate, UserUpdate, MessageCreate, MessageResponse
from typing import Optional

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str):
    """Genera un hash seguro para la contraseña."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    """Verifica si la contraseña ingresada coincide con el hash almacenado."""
    return pwd_context.verify(plain_password, hashed_password)

def create_user_db(user: UserCreate, session: Session):
    """Crea un nuevo usuario en la base de datos."""
    hashed_password = get_password_hash(user.password)
    db_user = User(username=user.username, password_hash=hashed_password, full_name=user.full_name)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

def get_user_by_username(username: str, session: Session):
    """Obtiene un usuario por su nombre de usuario."""
    statement = select(User).where(User.username == username, User.is_active == True)
    return session.exec(statement).first()

def get_user_by_email(email: str, session: Session):
    """Obtiene un usuario por su nombre de usuario."""
    statement = select(User).where(User.email == email, User.is_active == True)
    return session.exec(statement).first()

def get_all_users(session: Session):
    """Obtiene todos los usuarios activos."""
    statement = select(User).where(User.is_active == True)
    return session.exec(statement).all()

def update_user_db(user_id: int, user_update: UserUpdate, session: Session):
    """Actualiza los datos de un usuario."""
    db_user = session.get(User, user_id)
    if not db_user:
        return None
    
    update_data = user_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user, key, value)

    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

def soft_delete_user_db(user_id: int, session: Session):
    """Realiza un 'borrado lógico' de un usuario."""
    db_user = session.get(User, user_id)
    if not db_user:
        return None
    
    db_user.is_active = False
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return {"message": "Usuario desactivado lógicamente"}


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def process_and_create_message_db(user_id: UUID, message: MessageCreate, session: Session):
    """
    Pipeline de procesamiento de mensajes:
    1. Valida y filtra el contenido.
    2. Agrega metadatos.
    3. Almacena en la base de datos.
    """
    
    # 1. Validación y Filtrado de Contenido (simple)
    inappropriate_words = ["marica", "godo", "feo", "gay", "negro"]
    if any(word in message.content.lower() for word in inappropriate_words):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El mensaje contiene contenido inapropiado."
        )

    # 2. Agregar Metadatos
    word_count = len(message.content.split())
    message_length = len(message.content)

    # 3. Almacenar en la Base de Datos
    db_message = Message(
        session_id=message.session_id,
        user_id=user_id,
        content=message.content,
        sender=message.sender,
        message_length=message_length,
        word_count=word_count
    )
    
    session.add(db_message)
    session.commit()
    session.refresh(db_message)
    
    return db_message

def get_messages_by_session_id(
    session_id: str, 
    session: Session,
    limit: int = 100,
    offset: int = 0,
    sender: Optional[str] = None
):
    """Recupera mensajes por session_id con paginación y filtro de remitente."""
    statement = select(Message).where(Message.session_id == session_id)
    
    if sender:
        statement = statement.where(func.lower(Message.sender) == sender.lower())
    
    statement = statement.offset(offset).limit(limit)
    
    messages = session.exec(statement).all()
    
    return messages