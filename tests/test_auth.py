"""
Suíte de Testes para os recursos de Autenticação e Usuários.
"""

from fastapi.testclient import TestClient
from typing import Dict, Any
from src.auth import create_access_token

# -------------------------------------------------------------------------- #
#                             TESTES DE REGISTRO DE USUÁRIO                  #
# -------------------------------------------------------------------------- #


def test_create_user_success(client: TestClient, test_user_payload: Dict[str, Any]):
    """Testa o registro bem-sucedido de um novo usuário comum."""
    user_payload = test_user_payload.copy()
    user_payload["email"] = "register_success@test.com"

    response = client.post("/auth/users/", json=user_payload)

    assert response.status_code == 201
    created_user = response.json()
    assert created_user["email"] == user_payload["email"]
    assert not created_user["is_superuser"]


def test_create_user_with_existing_email(
    client: TestClient, test_user: Dict, test_user_payload: Dict[str, Any]
):
    """Testa a falha ao tentar registrar um usuário com um e-mail que já existe."""
    response = client.post("/auth/users/", json=test_user_payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


def test_create_user_with_invalid_cpf(
    client: TestClient, test_user_payload: Dict[str, Any]
):
    """Testa a falha ao registrar um usuário com um CPF inválido."""
    user_payload = test_user_payload.copy()
    user_payload["email"] = "invalid.cpf@test.com"
    user_payload["cpf"] = "123.456.789-00"  

    response = client.post("/auth/users/", json=user_payload)

    assert response.status_code == 422  
    error_details = response.json()["detail"]
    assert any("CPF inválido" in e["msg"] for e in error_details)


# -------------------------------------------------------------------------- #
#                                 TESTES DE LOGIN                            #
# -------------------------------------------------------------------------- #


def test_login_for_access_token_success(
    client: TestClient, test_user: Dict, test_user_payload: Dict[str, Any]
):
    """Testa o login bem-sucedido de um usuário com credenciais corretas."""
    login_data = {
        "username": test_user_payload["email"],
        "password": test_user_payload["password"],
    }
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
    assert response.json()["detail"] == "Incorrect email or password"


def test_login_with_nonexistent_email(client: TestClient):
    """Testa a falha de login ao fornecer um e-mail que não está registrado."""
    login_data = {"username": "ghost@example.com", "password": "password"}
    response = client.post("/auth/token", data=login_data)
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


# -------------------------------------------------------------------------- #
#                          TESTES DO ENDPOINT DE PERFIL (/users/me)          #
# -------------------------------------------------------------------------- #


def test_read_users_me_success(
    client: TestClient, test_user: Dict, user_token_headers: Dict[str, str]
):
    """Testa se um usuário autenticado pode acessar seus próprios dados."""
    response = client.get("/auth/users/me/", headers=user_token_headers)
    assert response.status_code == 200
    profile_data = response.json()
    assert profile_data["email"] == test_user["email"]
    assert profile_data["id"] == test_user["id"]
    assert not profile_data["is_superuser"]


def test_read_users_me_unauthorized(client: TestClient):
    """Testa se o acesso ao endpoint /users/me/ é bloqueado sem autenticação."""
    response = client.get("/auth/users/me/")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


# -------------------------------------------------------------------------- #
#                       TESTES DE CASOS DE BORDA DE TOKEN                    #
# -------------------------------------------------------------------------- #
def test_read_users_me_with_invalid_token(client: TestClient):
    """Testa o acesso com um token malformado."""
    headers = {"Authorization": "Bearer not-a-valid-token"}
    response = client.get("/auth/users/me/", headers=headers)
    assert response.status_code == 401


def test_get_current_user_with_token_missing_sub(client: TestClient):
    """Testa a falha com um token JWT válido mas sem o campo 'sub'."""
    token = create_access_token(data={"outro_campo": "valor"})
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/auth/users/me/", headers=headers)
    assert response.status_code == 401


def test_get_current_user_with_nonexistent_user_in_db(client: TestClient):
    """Testa a falha com um token válido cujo usuário não existe mais no DB."""
    token = create_access_token(data={"sub": "ghost@example.com"})
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/auth/users/me/", headers=headers)
    assert response.status_code == 401
