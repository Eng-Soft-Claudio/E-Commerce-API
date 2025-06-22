"""
Suíte de Testes para Endpoints de Administração.

Testa todas as rotas protegidas sob os prefixos '/admin', garantindo que
as permissões funcionem e que os dados retornados estejam corretos.
"""

# -------------------------------------------------------------------------- #
#                             IMPORTS NECESSÁRIOS                            #
# -------------------------------------------------------------------------- #
import pytest
from fastapi.testclient import TestClient
from typing import Dict
from sqlalchemy.orm import Session
from src.models import Order

# -------------------------------------------------------------------------- #
#                  TESTES PARA O ENDPOINT GET /admin/users                   #
# -------------------------------------------------------------------------- #


def test_superuser_can_list_users(
    client: TestClient, superuser_token_headers: Dict, test_user: Dict
):
    """Testa se um superusuário pode listar todos os clientes."""
    response = client.get("/admin/users/", headers=superuser_token_headers)
    assert response.status_code == 200

    users = response.json()
    assert isinstance(users, list)
    assert len(users) >= 1

    user_emails = [user["email"] for user in users]
    assert test_user["email"] in user_emails


def test_common_user_cannot_list_users(client: TestClient, user_token_headers: Dict):
    """Testa se um usuário comum é proibido de acessar a lista de usuários."""
    response = client.get("/admin/users/", headers=user_token_headers)
    assert response.status_code == 403
    assert "doesn't have enough privileges" in response.json()["detail"]


def test_unauthorized_client_cannot_list_users(client: TestClient):
    """Testa se um cliente não autenticado não pode listar usuários."""
    response = client.get("/admin/users/")
    assert response.status_code == 401


# -------------------------------------------------------------------------- #
#             TESTES PARA O ENDPOINT PUT /orders/{order_id}/status           #
# -------------------------------------------------------------------------- #


@pytest.fixture(scope="function")
def order_for_status_update(
    client: TestClient, user_token_headers: Dict, superuser_token_headers: Dict
) -> Dict:
    """Fixture que cria um pedido para ser usado nos testes de atualização."""
    cat_resp = client.post(
        "/categories/",
        headers=superuser_token_headers,
        json={"title": "Status Update Categ"},
    )
    prod_data = {
        "name": "Produto para Status",
        "price": 99.99,
        "category_id": cat_resp.json()["id"],
    }
    prod_resp = client.post(
        "/products/", headers=superuser_token_headers, json=prod_data
    )
    client.post(
        "/cart/items/",
        headers=user_token_headers,
        json={"product_id": prod_resp.json()["id"], "quantity": 1},
    )
    order_response = client.post("/orders/", headers=user_token_headers)
    assert order_response.status_code == 201
    return order_response.json()


def test_superuser_can_update_order_status(
    client: TestClient,
    superuser_token_headers: Dict,
    order_for_status_update: Dict,
    db_session: Session,
):
    """Testa se um superusuário pode alterar com sucesso o status de um pedido."""
    order_id = order_for_status_update["id"]
    new_status = "shipped"

    order_before = db_session.get(Order, order_id)
    assert order_before is not None, "A fixture deveria ter criado o pedido."
    assert order_before.status == "pending_payment"

    response = client.put(
        f"/orders/{order_id}/status",
        headers=superuser_token_headers,
        json={"status": new_status},
    )

    assert response.status_code == 200
    updated_order_data = response.json()
    assert updated_order_data["id"] == order_id
    assert updated_order_data["status"] == new_status
    assert "customer" in updated_order_data

    db_session.refresh(order_before)
    assert order_before.status == new_status


def test_common_user_cannot_update_order_status(
    client: TestClient, user_token_headers: Dict, order_for_status_update: Dict
):
    """Testa se um usuário comum é proibido de alterar o status de um pedido."""
    order_id = order_for_status_update["id"]
    response = client.put(
        f"/orders/{order_id}/status",
        headers=user_token_headers,
        json={"status": "shipped"},
    )
    assert response.status_code == 403


def test_superuser_cannot_update_with_invalid_status(
    client: TestClient, superuser_token_headers: Dict, order_for_status_update: Dict
):
    """Testa a falha ao tentar atualizar com um status que não está na lista de permitidos."""
    order_id = order_for_status_update["id"]
    response = client.put(
        f"/orders/{order_id}/status",
        headers=superuser_token_headers,
        json={"status": "status_inventado"},
    )
    assert response.status_code == 400
    assert "é inválido" in response.json()["detail"]


def test_superuser_cannot_update_nonexistent_order(
    client: TestClient, superuser_token_headers: Dict
):
    """Testa a falha ao tentar atualizar um pedido que não existe."""
    response = client.put(
        "/orders/99999/status", headers=superuser_token_headers, json={"status": "paid"}
    )
    assert response.status_code == 404
    assert "Pedido não encontrado" in response.json()["detail"]
