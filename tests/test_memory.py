from app import create_app


def test_login_success():
    app = create_app()
    client = app.test_client()

    response = client.post("/login", json={"password": "dev-password"})

    assert response.status_code == 200
    assert response.get_json()["success"] is True


def test_login_invalid_password():
    app = create_app()
    client = app.test_client()

    response = client.post("/login", json={"password": "senha-errada"})

    assert response.status_code == 401
    assert "error" in response.get_json()


def test_home_requires_login():
    app = create_app()
    client = app.test_client()

    response = client.get("/")
    assert response.status_code == 200
    assert b"Digite sua senha" in response.data
