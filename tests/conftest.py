# conftest.py

import pytest
from sqlmodel import create_engine, SQLModel, Session
from app.main import app
from app.database import get_session
from app.models import User, Message
from fastapi.testclient import TestClient

# Usamos una base de datos en memoria para las pruebas
sqlite_file_name = "test_database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

@pytest.fixture(name="session")
def session_fixture():
    """Fixtura para una sesión de base de datos de prueba."""
    create_db_and_tables()
    with Session(engine) as session:
        yield session
    # Limpiar la base de datos después de la prueba
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Fixtura para un cliente de prueba de FastAPI."""

    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()