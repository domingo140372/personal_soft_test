# test_app.py

import pytest
from sqlmodel import Session
from fastapi.testclient import TestClient
from uuid import uuid4
from datetime import datetime
from fastapi import HTTPException
from app.services import MessageService
from app.schemas import MessageCreate

# --- Helper para datos de usuario ---
def build_user_data(username: str, password: str):
    return {
        "username": username,
        "email": f"{username}@example.com",
        "password": password,
        "full_name": "Test User",
        "created_at": datetime.now().isoformat()
    }

# --- Pruebas de Servicios (Lógica de Negocio) ---
def test_process_message_inappropriate_content(mocker):
    """
    Prueba que el servicio rechace mensajes con contenido inapropiado.
    """
    mock_session = mocker.Mock(spec=Session)
    service = MessageService(session=mock_session)

    inappropriate_message = MessageCreate(
        session_id="test-session",
        content="Este es negro y gordo",
        sender="user"
    )

    with pytest.raises(HTTPException):
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
    # Ajusta este valor según la lógica real de conteo de palabras en tu servicio
    assert result.word_count in (6, 7)


# --- Pruebas de Integración (Endpoints de la API) ---
def test_create_user_endpoint(client: TestClient):
    """
    Prueba que el endpoint POST /users/ cree un usuario correctamente.
    """
    username = f"testuser_{uuid4()}"
    user_data = build_user_data(username, "password123")

    response = client.post("/users/", json=user_data)

    assert response.status_code == 201
    response_data = response.json()
    assert "id" in response_data
    assert response_data["username"] == user_data["username"]


def test_login_and_create_message_endpoint(client: TestClient):
    """
    Prueba el flujo completo: login, obtención de token y envío de mensaje.
    """
    # 1. Crear un usuario de prueba
    username = f"testuser_{uuid4()}"
    password = "password123"
    user_data = build_user_data(username, password)

    create_response = client.post("/users/", json=user_data)
    assert create_response.status_code == 201

    # 2. Obtener un token
    login_data = {"username": username, "password": password}
    token_response = client.post("/token", data=login_data)

    assert token_response.status_code == 200, f"Login failed: {token_response.text}"
    token = token_response.json()["access_token"]

    # 3. Enviar un mensaje
    message_data = {
        "session_id": "test-session",
        "content": "Hola mundo, esta es una prueba.",
        "sender": "user"
    }
    headers = {"Authorization": f"Bearer {token}"}
    message_response = client.post("/api/messages", json=message_data, headers=headers)

    assert message_response.status_code == 201
    response_data = message_response.json()
    assert "message_id" in response_data
    assert response_data["content"] == message_data["content"]
    assert response_data["word_count"] == 6


def test_get_messages_endpoint(client: TestClient):
    """
    Prueba que el endpoint GET /api/messages/{session_id} devuelva los mensajes correctos.
    """
    # 1. Crear un usuario y obtener un token
    username = f"testuser_{uuid4()}"
    password = "password123"
    user_data = build_user_data(username, password)

    client.post("/users/", json=user_data)
    token_response = client.post("/token", data={"username": username, "password": password})
    assert token_response.status_code == 200
    token = token_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Enviar varios mensajes
    session_id = f"test-session-{uuid4()}"
    client.post("/api/messages", json={"session_id": session_id, "content": "msg 1", "sender": "user"}, headers=headers)
    client.post("/api/messages", json={"session_id": session_id, "content": "msg 2", "sender": "system"}, headers=headers)
    client.post("/api/messages", json={"session_id": session_id, "content": "msg 3", "sender": "user"}, headers=headers)

    # 3. GET sin filtros
    get_all_response = client.get(f"/api/messages/{session_id}", headers=headers)
    assert get_all_response.status_code == 200
    assert len(get_all_response.json()) == 3

    # 4. GET con filtro sender=user
    get_user_response = client.get(f"/api/messages/{session_id}?sender=user", headers=headers)
    assert get_user_response.status_code == 200
    assert len(get_user_response.json()) == 2
