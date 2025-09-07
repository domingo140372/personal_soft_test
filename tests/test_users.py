def test_create_user(client):
    """Debe crear un usuario nuevo."""
    response = client.post("/users/", json={"name": "Carlos", "email": "carlos@test.com", "phone": "123456"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Carlos"
    assert data["email"] == "carlos@test.com"

def test_get_user(client):
    """Debe devolver el usuario creado previamente."""
    client.post("/users/", json={"name": "Ana", "email": "ana@test.com", "phone": "987654"})
    response = client.get("/users/1")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Ana"

def test_delete_user(client):
    """Debe marcar un usuario como eliminado (borrado lógico)."""
    client.post("/users/", json={"name": "Pepe", "email": "pepe@test.com", "phone": "111222"})
    response = client.delete("/users/1")
    assert response.status_code == 200
    data = response.json()
    assert data["is_deleted"] is True
