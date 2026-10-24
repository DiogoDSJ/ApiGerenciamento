from app.models import User, UserRole
from app.security import bcrypt_context, create_refresh_token


def test_create_user_success(client):
    """Cadastro de novo usuário no sistema."""
    payload = {
        "username": "novo_usuario",
        "email": "novo@erp.com",
        "password": "senha_segura_123",
        "role": "funcionario",
    }
    response = client.post("/auth/create_user", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["username"] == "novo_usuario"
    assert body["data"]["email"] == "novo@erp.com"


def test_create_user_duplicate_username_fails(client, test_admin_user):
    """Tentativa de cadastrar usuário com username duplicado dispara 409."""
    payload = {
        "username": test_admin_user.username,
        "email": "diferente@erp.com",
        "password": "outra_senha_123",
        "role": "funcionario",
    }
    response = client.post("/auth/create_user", json=payload)

    assert response.status_code == 409
    assert response.json()["error_code"] == "USER_ALREADY_EXISTS"


def test_login_success(client, db_session):
    """Login com credenciais corretas deve retornar par de tokens JWT."""
    username = "auth_tester"
    password = "minha_senha_secreta"
    user = User(
        username=username,
        email="auth_tester@erp.com",
        password=bcrypt_context.hash(password),
        role=UserRole.ADMIN,
    )
    db_session.add(user)
    db_session.commit()

    # Como a rota usa Depends() no LoginSchema, os dados vão como form/query
    response = client.post(f"/auth/login?username={username}&password={password}")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "access_token" in body["data"]
    assert "refresh_token" in body["data"]
    assert body["data"]["token_type"] == "bearer"


def test_login_invalid_password_fails(client, test_admin_user):
    """Senha incorreta dispara AuthenticationException (401)."""
    response = client.post(
        f"/auth/login?username={test_admin_user.username}&password=senha_errada"
    )

    assert response.status_code == 401
    assert response.json()["error_code"] == "INVALID_CREDENTIALS"


def test_read_me_authenticated_user(client, test_admin_user):
    """Rota /auth/me retorna os dados do usuário autenticado atual."""
    response = client.get("/auth/me")

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["username"] == test_admin_user.username
    assert body["data"]["email"] == test_admin_user.email


def test_refresh_token_success(client, test_admin_user):
    """Renovação de access token utilizando refresh token válido."""
    # Gera um refresh token legítimo para o usuário do teste
    from app.routers.auth_routes import create_refresh_token
    refresh_token = create_refresh_token(test_admin_user.username)

    payload = {"refresh_token": refresh_token}
    response = client.post("/auth/refresh", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "acess_token" in body["data"]
