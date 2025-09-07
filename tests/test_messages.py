def test_send_clean_message(client):
    """Debe aceptar un mensaje limpio."""
    # Crear un usuario primero
    client.post("/users/", json={"name": "Laura", "email": "laura@test.com", "phone": "555"})
    
    response = client.post("/messages/", json={"user_id": 1, "content": "Hola, buenos días"})
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Hola, buenos días"

def test_send_insult_message(client):
    """Debe rechazar un mensaje con insultos."""
    client.post("/users/", json={"name": "Pedro", "email": "pedro@test.com", "phone": "777"})
    
    response = client.post("/messages/", json={"user_id": 1, "content": "Eres un feo"})
    assert response.status_code == 400
    assert "insulto" in response.json()["detail"]

def test_send_groseria_message(client):
    """Debe rechazar un mensaje con groserías."""
    client.post("/users/", json={"name": "Marta", "email": "marta@test.com", "phone": "888"})
    
    response = client.post("/messages/", json={"user_id": 1, "content": "maldito sea"})
    assert response.status_code == 400
    assert "grosería" in response.json()["detail"]
