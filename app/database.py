# app/database.py
from sqlmodel import SQLModel, create_engine, Session
from typing import Generator
from .config import settings

# Crear engine según el dialecto
if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(settings.DATABASE_URL)

def create_db_and_tables() -> None:
    """
    Importa explícitamente todos los módulos que definen modelos para que
    SQLModel registre las tablas en SQLModel.metadata, luego crea las tablas.
    """
    # IMPORTANTE: importar aquí evita import cycles y asegura que las clases
    # estén registradas en SQLModel.metadata antes de crear las tablas.
    import app.users.models  # noqa: F401
    import app.messages.models  # noqa: F401
    # Si tienes más módulos: import app.otro.modulo.models

    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
