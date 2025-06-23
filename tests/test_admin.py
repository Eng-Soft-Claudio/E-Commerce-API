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
from typing import Dict, Any
from sqlalchemy.orm import Session
from src.models import Order, User  # noqa: F401

# -------------------------------------------------------------------------- #
#                  TESTES PARA O ENDPOINT GET /admin/users                   #
# -------------------------------------------------------------------------- #


def test_superuser_can_list_users(
    client: TestClient, superuser_token_headers: Dict[str, str], test_user: Dict
):
    """Testa se um superusuário pode listar todos os clientes."""
    response = client.get("/admin/users/", headers=superuser_token_headers)
    assert response.status_code == 200
    users_data = response.json()
    assert isinstance(users_data, list)
    assert any(user["email"] == test_user["email"] for user in users_data)


def test_common_user_cannot_list_users(
    client: TestClient, user_token_headers: Dict[str, str]
):
    """Testa se um usuário comum é proibido de acessar a lista de usuários."""
    response = client.get("/admin/users/", headers=user_token_headers)
    assert response.status_code == 403


# -------------------------------------------------------------------------- #
#               FIXTURE E TESTES PARA ORDENS E DASHBOARD                     #
# -------------------------------------------------------------------------- #


@pytest.fixture(scope="function")
def order_for_admin_tests(
    client: TestClient,
    user_token_headers: Dict[str, str],
    superuser_token_headers: Dict[str, str],
) -> Dict[str, Any]:
    """Fixture que cria um pedido para ser usado nos testes de admin."""
    cat_resp = client.post(
        "/categories/",
        headers=superuser_token_headers,
        json={"title": "Admin Test Categ"},
    )
    prod_data = {
        "name": "Produto para Teste Admin",
        "price": 99.99,
        "category_id": cat_resp.json()["id"],
    }
    client.post(
        "/products/", headers=superuser_token_headers, json=prod_data
    ).raise_for_status()
    client.post(
        "/cart/items/",
        headers=user_token_headers,
        json={"product_id": prod_data["category_id"], "quantity": 1},
    ).raise_for_status()
    order_response = client.post("/orders/", headers=user_token_headers)
    assert order_response.status_code == 201
    return order_response.json()


def test_superuser_can_list_all_orders(
    client: TestClient,
    superuser_token_headers: Dict[str, str],
    order_for_admin_tests: Dict[str, Any],
):
    """Testa se um superuser pode listar todos os pedidos no sistema."""
    response = client.get("/orders/admin", headers=superuser_token_headers)
    assert response.status_code == 200
    assert any(order["id"] == order_for_admin_tests["id"] for order in response.json())


def test_superuser_can_update_order_status(
    client: TestClient,
    superuser_token_headers: Dict[str, str],
    order_for_admin_tests: Dict[str, Any],
    db_session: Session,
):
    """Testa o caminho feliz da atualização de status de um pedido."""
    order_id = order_for_admin_tests["id"]
    response = client.put(
        f"/orders/{order_id}/status",
        headers=superuser_token_headers,
        json={"status": "shipped"},
    )
    assert response.status_code == 200
    db_session.expire_all()
    order_after = db_session.get(Order, order_id)
    assert order_after and order_after.status == "shipped"


def test_update_order_with_nonexistent_id(
    client: TestClient, superuser_token_headers: Dict[str, str]
):
    """Testa a falha ao tentar atualizar um pedido com ID inexistente."""
    response = client.put(
        "/orders/9999/status", headers=superuser_token_headers, json={"status": "paid"}
    )
    assert response.status_code == 404


def test_update_order_with_invalid_status(
    client: TestClient,
    superuser_token_headers: Dict[str, str],
    order_for_admin_tests: Dict[str, Any],
):
    """Testa a falha ao usar um status inválido."""
    order_id = order_for_admin_tests["id"]
    response = client.put(
        f"/orders/{order_id}/status",
        headers=superuser_token_headers,
        json={"status": "status_inventado"},
    )
    assert response.status_code == 400


def test_update_order_status_fails_on_reload(
    client: TestClient,
    superuser_token_headers: Dict[str, str],
    order_for_admin_tests: Dict[str, Any],
    mocker,
):
    """Testa a falha de recarregamento do pedido após o update (cobre a linha 91)."""
    order_id = order_for_admin_tests["id"]

    mock_query_chain = mocker.patch("src.routers.orders.Session.query")
    mock_query_chain.return_value.options.return_value.filter.return_value.first.return_value = None

    response = client.put(
        f"/orders/{order_id}/status",
        headers=superuser_token_headers,
        json={"status": "paid"},
    )

    assert response.status_code == 404
    assert (
        "Falha ao recarregar o pedido após a atualização" in response.json()["detail"]
    )


# -------------------------------------------------------------------------- #
#                 TESTES PARA O ENDPOINT GET /admin/stats                    #
# -------------------------------------------------------------------------- #


def test_get_dashboard_stats_on_clean_db(
    client: TestClient, superuser_token_headers: Dict[str, str]
):
    """Testa se as estatísticas retornam zero para um banco de dados limpo."""
    response = client.get("/admin/stats/", headers=superuser_token_headers)
    assert response.status_code == 200
    assert response.json()["total_sales"] == 0


def test_get_dashboard_stats_with_data(
    client: TestClient,
    superuser_token_headers: Dict[str, str],
    order_for_admin_tests: Dict[str, Any],
    db_session: Session,
):
    """Testa se as estatísticas refletem corretamente os dados existentes."""
    response = client.get("/admin/stats/", headers=superuser_token_headers)
    assert response.json()["total_orders"] == 1

    order_id = order_for_admin_tests["id"]
    order = db_session.get(Order, order_id)
    assert order
    order.status = "paid"
    db_session.commit()

    response_after = client.get("/admin/stats/", headers=superuser_token_headers)
    assert response_after.json()["total_sales"] == 99.99
