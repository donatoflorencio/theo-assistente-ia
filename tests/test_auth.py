from app import create_app


def test_login_success():
    client = create_app().test_client()
    response = client.post("/login", json={"password": "test-password"})
    assert response.status_code == 200
    assert response.get_json()["success"] is True


def test_login_invalid_password():
    client = create_app().test_client()
    response = client.post("/login", json={"password": "wrong"})
    assert response.status_code == 401


def test_chat_requires_login():
    client = create_app().test_client()
    response = client.post("/chat", json={"message": "hello"})
    assert response.status_code == 401


def test_empty_chat_message():
    client = create_app().test_client()
    client.post("/login", json={"password": "test-password"})
    response = client.post("/chat", json={"message": "  "})
    assert response.status_code == 400
