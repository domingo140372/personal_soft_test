# test_app.py

import pytest
from app.services import MessageService
from app.schemas import MessageCreate
from app.crud import create_db_message
from app.models import User
from sqlmodel import Session
from fastapi.testclient import TestClient
from uuid import uuid4

# --- Pruebas de Servicios (Lógica de Negocio) ---
# Usamos mock para aislar la capa de servicios de la base de datos.
def test_process_message_inappropriate_content(mocker):
    """
    Prueba que el servicio rechace mensajes con contenido inapropiado.
    """
    mock_session = mocker.Mock(spec=Session)
    service = MessageService(session=mock_session)
    
    inappropriate_message = MessageCreate(
        session_id="test-session",
        content="Este es un mensaje con una mala_palabra",
        sender="user"
    )
    
    with pytest.raises(Exception):
        service.process_and_create_message(uuid4(), inappropriate_message)

def test_process_message_success(mocker):
    """
    Prueba que el servicio procese mensajes válidos correctamente.
    """
    mock_session = mocker.Mock(spec=Session)
    service = MessageService(session=mock_session)
    
    valid_message = MessageCreate(
        session_id="test-session",
        content="Este es un mensaje de prueba",
        sender="user"
    )

    # Mock del repositorio para evitar tocar la DB
    mocker.patch(
        "app.crud.create_db_message",
        return_value=valid_message
    )

    result = service.process_and_create_message(uuid4(), valid_message)
    
    assert result.content == "Este es un mensaje de prueba"
    assert result.word_count == 5

# --- Pruebas de Integración (Endpoints de la API) ---
# Usamos el TestClient para simular peticiones HTTP reales.

def test_create_user_endpoint(client: TestClient):
    """
    Prueba que el endpoint POST /users/ cree un usuario correctamente.
    """
    user_data = {
        "username": f"testuser_{uuid4()}",
        "password": "password123",
        "full_name": "Test User"
    }
    response = client.post("/users/", json=user_data)
    
    assert response.status_code == 201
    assert "id" in response.json()
    assert response.json()["username"] == user_data["username"]

def test_login_and_create_message_endpoint(client: TestClient):
    """
    Prueba el flujo completo: login, obtención de token y envío de mensaje.
    """
    # 1. Crear un usuario de prueba
    username = f"testuser_{uuid4()}"
    password = "password123"
    client.post("/users/", json={"username": username, "password": password})
    
    # 2. Obtener un token
    login_data = {"username": username, "password": password}
    token_response = client.post("/token", data=login_data)
    assert token_response.status_code == 200
    token = token_response.json()["access_token"]
    
    # 3. Enviar un mensaje con el token
    message_data = {
        "session_id": "test-session",
        "content": "Hola mundo, esta es una prueba.",
        "sender": "user"
    }
    headers = {"Authorization": f"Bearer {token}"}
    message_response = client.post("/api/messages", json=message_data, headers=headers)
    
    assert message_response.status_code == 201
    assert "message_id" in message_response.json()
    assert message_response.json()["content"] == message_data["content"]
    assert message_response.json()["word_count"] == 7
    
def test_get_messages_endpoint(client: TestClient):
    """
    Prueba que el endpoint GET /api/messages/{session_id} devuelva los mensajes correctos.
    """
    # 1. Crear un usuario y obtener un token (como en la prueba anterior)
    username = f"testuser_{uuid4()}"
    password = "password123"
    client.post("/users/", json={"username": username, "password": password})
    token_response = client.post("/token", data={"username": username, "password": password})
    token = token_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Enviar varios mensajes a una sesión
    session_id = f"test-session-{uuid4()}"
    client.post("/api/messages", json={"session_id": session_id, "content": "msg 1", "sender": "user"}, headers=headers)
    client.post("/api/messages", json={"session_id": session_id, "content": "msg 2", "sender": "system"}, headers=headers)
    client.post("/api/messages", json={"session_id": session_id, "content": "msg 3", "sender": "user"}, headers=headers)

    # 3. Probar el endpoint GET sin filtros
    get_all_response = client.get(f"/api/messages/{session_id}", headers=headers)
    assert get_all_response.status_code == 200
    assert len(get_all_response.json()) == 3
    
    # 4. Probar el endpoint GET con filtro de remitente
    get_user_response = client.get(f"/api/messages/{session_id}?sender=user", headers=headers)
    assert get_user_response.status_code == 200
    assert len(get_user_response.json()) == 2