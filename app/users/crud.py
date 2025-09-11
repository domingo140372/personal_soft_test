#### crud of Users
# app/users/crud.py
from sqlmodel import Session, select
from passlib.context import CryptContext
from .models import User
from .schemas import UserCreate, UserUpdate
from typing import Optional
from uuid import UUID

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_user_db(user_in: UserCreate, session: Session) -> User:
    db_user = User(
        username=user_in.username,
        email=user_in.email,
        password_hash=hash_password(user_in.password),
        full_name=user_in.full_name
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

def get_user_by_username(username: str, session: Session) -> Optional[User]:
    statement = select(User).where(User.username == username, User.is_active == True)
    return session.exec(statement).first()

def update_user_db(user_id: UUID, user_update: UserUpdate, session: Session) -> Optional[User]:
    user = session.get(User, user_id)
    if not user:
        return None
    for k, v in user_update.dict(exclude_unset=True).items():
        setattr(user, k, v)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

def soft_delete_user_db(user_id: UUID, session: Session) -> bool:
    user = session.get(User, user_id)
    if not user:
        return False
    user.is_active = False
    session.add(user)
    session.commit()
    return True
