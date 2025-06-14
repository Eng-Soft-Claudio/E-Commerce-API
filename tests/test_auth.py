"""
Suíte de Testes para os recursos de Autenticação e Usuários.

Testa todos os endpoints sob o prefixo '/auth', cobrindo:
- Registro de novos usuários (sucesso e falha por e-mail duplicado).
- Login de usuários (sucesso e falha por credenciais incorretas).
- Acesso ao perfil do usuário (`/users/me`) e suas proteções.
"""

from fastapi.testclient import TestClient
from typing import Dict

from src.auth import create_access_token

# -------------------------------------------------------------------------- #
#                             TESTES DE REGISTRO DE USUÁRIO                    #
# -------------------------------------------------------------------------- #


def test_create_user_success(client: TestClient):
    """
    Testa o registro bem-sucedido de um novo usuário comum.

    """
    client.post(
        "/auth/users/",
        json={"email": "temp.admin.for.test@example.com", "password": "a"},
    )

    user_data = {
        "email": "test.register@example.com",
        "password": "averysecretpassword",
    }
    response = client.post("/auth/users/", json=user_data)

    assert response.status_code == 201
    created_user = response.json()
    assert created_user["is_superuser"] is False


def test_create_user_with_existing_email(client: TestClient, test_user: Dict):
    """
    Testa a falha ao tentar registrar um usuário com um e-mail que já existe.

    Usa a fixture `test_user` que já cria um usuário com 'user@test.com'.
    Espera-se uma resposta 400 Bad Request.
    """
    user_data = {"email": test_user["email"], "password": "anotherpassword"}
    response = client.post("/auth/users/", json=user_data)

    assert response.status_code == 400
    assert response.json() == {"detail": "Email already registered"}


# -------------------------------------------------------------------------- #
#                                 TESTES DE LOGIN                            #
# -------------------------------------------------------------------------- #


def test_login_for_access_token_success(client: TestClient, test_user: Dict):
    """
    Testa o login bem-sucedido de um usuário com credenciais corretas.

    Verifica se a resposta contém 'access_token' e 'token_type'.
    """
    login_data = {"username": test_user["email"], "password": "password123"}
    response = client.post("/auth/token", data=login_data)

    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"


def test_login_with_wrong_password(client: TestClient, test_user: Dict):
    """Testa a falha de login ao fornecer a senha incorreta."""
    login_data = {"username": test_user["email"], "password": "wrongpassword"}
    response = client.post("/auth/token", data=login_data)

    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect email or password"}


def test_login_with_nonexistent_email(client: TestClient):
    """Testa a falha de login ao fornecer um e-mail que não está registrado."""
    login_data = {"username": "ghost@example.com", "password": "password"}
    response = client.post("/auth/token", data=login_data)

    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect email or password"}


# -------------------------------------------------------------------------- #
#                          TESTES DO ENDPOINT DE PERFIL (/users/me)          #
# -------------------------------------------------------------------------- #


def test_read_users_me_success(
    client: TestClient, test_user: Dict, user_token_headers: Dict[str, str]
):
    """
    Testa se um usuário autenticado pode acessar seus próprios dados no endpoint /users/me/.
    """
    response = client.get("/auth/users/me/", headers=user_token_headers)

    assert response.status_code == 200
    profile_data = response.json()
    assert profile_data["email"] == test_user["email"]
    assert profile_data["id"] == test_user["id"]
    assert profile_data["is_superuser"] is False


def test_read_users_me_unauthorized(client: TestClient):
    """Testa se o acesso ao endpoint /users/me/ é bloqueado sem autenticação."""
    response = client.get("/auth/users/me/")

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


# -------------------------------------------------------------------------- #
#                       TESTES DE CASOS DE BORDA DE TOKEN                      #
# -------------------------------------------------------------------------- #


def test_read_users_me_with_invalid_token(client: TestClient):
    """
    Testa o acesso ao endpoint /users/me/ com um token malformado ou inválido.

    Espera-se uma resposta 401 Unauthorized, cobrindo o bloco 'except JWTError'
    na dependência 'get_current_user'.
    """
    invalid_token_headers = {"Authorization": "Bearer not-a-valid-token"}
    response = client.get("/auth/users/me/", headers=invalid_token_headers)

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


# -------------------------------------------------------------------------- #
#                       TESTES DE CASOS DE BORDA DE TOKEN                    #
# -------------------------------------------------------------------------- #


def test_get_current_user_with_token_missing_sub(client: TestClient):
    """
    Testa a falha de autenticação com um token JWT válido mas sem o campo 'sub'.

    Cobre a linha: if email is None: raise credentials_exception
    """
    token_sem_sub = create_access_token(data={"outro_campo": "valor"})
    headers = {"Authorization": f"Bearer {token_sem_sub}"}

    response = client.get("/auth/users/me/", headers=headers)

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


def test_get_current_user_with_nonexistent_user_in_db(client: TestClient):
    """
    Testa a falha de autenticação com um token válido cujo usuário não existe mais no DB.

    Cobre a linha: if user is None: raise credentials_exception
    """
    email_fantasma = "ghost@example.com"
    token_usuario_deletado = create_access_token(data={"sub": email_fantasma})
    headers = {"Authorization": f"Bearer {token_usuario_deletado}"}

    response = client.get("/auth/users/me/", headers=headers)

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"
