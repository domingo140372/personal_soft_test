## archivo de conexion a la base de datos
"""
import os 
from dotenv import load_dotenv
from sqlmodel import create_engine, SQLModel, Session

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./database.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
#engine = create_engine(sqlite_url, echo=True)

def create_db_and_tables():
    # Crea la base de datos y las tablas a partir de los modelos de SQLModel.
    SQLModel.metadata.create_all(engine)

def get_session():
    #Generador de dependencias para la sesión de la base de datos.
    with Session(engine) as session:
        yield session
"""

# app/database.py
from sqlmodel import SQLModel, create_engine, Session
from typing import Generator
from .config import settings

engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})

def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
