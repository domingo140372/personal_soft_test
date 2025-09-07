import pytest
from sqlmodel import create_engine, SQLModel, Session
from fastapi.testclient import TestClient
import fakeredis

from app.main import app
from app.database import get_session
from app.middleware import RedisRateLimitMiddleware

# Usamos SQLite en memoria para los tests
sqlite_url = "sqlite:///:memory:"
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

@pytest.fixture(name="session")
def session_fixture():
    """Fixture de sesión de base de datos para pruebas."""
    create_db_and_tables()
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)

@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Fixture para cliente de pruebas con Redis simulado."""
    # Sobrescribir la dependencia de la BD
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override

    # Redis simulado con fakeredis
    fake_redis = fakeredis.FakeStrictRedis()
    app.state.redis = fake_redis

    # Inyectar el middleware con Redis falso
    app.user_middleware.clear()
    app.add_middleware(RedisRateLimitMiddleware, redis_client=fake_redis)

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
s