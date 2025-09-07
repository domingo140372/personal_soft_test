def test_rate_limit(client):
    """Debe bloquear después de exceder el límite de requests."""
    url = "/messages/"  # o el endpoint que quieras proteger
    
    # Crear un usuario para asociar mensajes
    client.post("/users/", json={"name": "Jose", "email": "jose@test.com", "phone": "000"})
    
    # 5 peticiones permitidas
    for _ in range(5):
        response = client.post(url, json={"user_id": 1, "content": "Mensaje limpio"})
        assert response.status_code == 200

    # 6ta petición bloqueada
    response = client.post(url, json={"user_id": 1, "content": "Mensaje extra"})
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.text
