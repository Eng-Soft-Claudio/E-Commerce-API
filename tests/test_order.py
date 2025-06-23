"""
Suíte de Testes para o recurso de Pedidos (Orders).

Testa todos os endpoints sob o prefixo '/orders', cobrindo o fluxo de
vida completo de um pedido.
"""

import pytest
from typing import Dict, Any
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from src.auth import create_access_token
from src.schemas import UserCreate
from src import crud
from src.models import Product

# -------------------------------------------------------------------------- #
#                        FUNÇÃO AUXILIAR DE SETUP                            #
# -------------------------------------------------------------------------- #


def create_product_and_add_to_cart(
    client: TestClient, user_headers: Dict[str, str], admin_headers: Dict[str, str]
) -> Dict[str, Any]:
    """Função auxiliar que cria um produto e o adiciona ao carrinho do usuário."""
    cat_resp = client.post(
        "/categories/", headers=admin_headers, json={"title": "Pedido Categ"}
    )
    assert cat_resp.status_code == 201

    prod_data = {
        "name": "Item Para Pedido",
        "price": 25.50,
        "category_id": cat_resp.json()["id"],
    }
    prod_resp = client.post("/products/", headers=admin_headers, json=prod_data)
    assert prod_resp.status_code == 201
    product = prod_resp.json()

    add_to_cart_resp = client.post(
        "/cart/items/",
        headers=user_headers,
        json={"product_id": product["id"], "quantity": 2},
    )
    assert add_to_cart_resp.status_code == 200
    return product


# -------------------------------------------------------------------------- #
#                         TESTES DE CONTROLE DE ACESSO                       #
# -------------------------------------------------------------------------- #


def test_superuser_cannot_create_order(
    client: TestClient, superuser_token_headers: Dict[str, str]
):
    """Testa que superusers não podem criar pedidos (espera 403)."""
    response = client.post("/orders/", headers=superuser_token_headers)
    assert response.status_code == 403


def test_create_order_unauthorized(client: TestClient):
    """Testa que clientes não autenticados não podem criar pedidos (espera 401)."""
    response = client.post("/orders/")
    assert response.status_code == 401


def test_create_order_from_empty_cart_fails(
    client: TestClient, user_token_headers: Dict[str, str]
):
    """Testa a criação de um pedido com um carrinho vazio (espera 400)."""
    response = client.post("/orders/", headers=user_token_headers)
    assert response.status_code == 400


# -------------------------------------------------------------------------- #
#                       TESTES DO FLUXO PRINCIPAL E HISTÓRICO                #
# -------------------------------------------------------------------------- #


def test_order_creation_and_history_flow(
    client: TestClient,
    user_token_headers: Dict[str, str],
    superuser_token_headers: Dict[str, str],
):
    """
    Testa o fluxo de ponta-a-ponta: popular carrinho -> criar pedido ->
    verificar detalhes -> verificar histórico -> verificar carrinho vazio.
    """
    product = create_product_and_add_to_cart(
        client, user_token_headers, superuser_token_headers
    )

    order_response = client.post("/orders/", headers=user_token_headers)
    assert order_response.status_code == 201
    order_data = order_response.json()
    order_id = order_data["id"]

    assert order_data["total_price"] == pytest.approx(product["price"] * 2)

    history_response = client.get("/orders/", headers=user_token_headers)
    assert history_response.status_code == 200
    assert any(order["id"] == order_id for order in history_response.json())

    cart_response = client.get("/cart/", headers=user_token_headers)
    assert cart_response.status_code == 200
    assert cart_response.json()["items"] == []


def test_user_can_see_own_single_order(
    client: TestClient,
    user_token_headers: Dict[str, str],
    superuser_token_headers: Dict[str, str],
):
    """
    Testa se um usuário comum pode buscar e visualizar um de seus próprios pedidos.
    """
    product = create_product_and_add_to_cart(
        client, user_token_headers, superuser_token_headers
    )
    order_response = client.post("/orders/", headers=user_token_headers)
    assert order_response.status_code == 201
    order_id = order_response.json()["id"]

    get_response = client.get(f"/orders/{order_id}", headers=user_token_headers)
    assert get_response.status_code == 200
    order_data = get_response.json()
    assert order_data["id"] == order_id
    assert order_data["items"][0]["product"]["id"] == product["id"]


# -------------------------------------------------------------------------- #
#                     TESTES DE BORDA COM PRODUTOS DELETADOS                 #
# -------------------------------------------------------------------------- #


def test_create_order_successfully_ignores_deleted_products(
    client: TestClient,
    user_token_headers: Dict[str, str],
    superuser_token_headers: Dict[str, str],
    db_session: Session,
):
    """Testa se um pedido ignora itens cujo produto foi deletado, mas cria o pedido com os itens válidos."""
    product_valid = create_product_and_add_to_cart(
        client, user_token_headers, superuser_token_headers
    )
    product_to_delete = create_product_and_add_to_cart(
        client, user_token_headers, superuser_token_headers
    )
    db_product_to_delete = db_session.get(Product, product_to_delete["id"])
    assert db_product_to_delete is not None

    db_session.delete(db_product_to_delete)
    db_session.commit()

    order_response = client.post("/orders/", headers=user_token_headers)
    assert order_response.status_code == 201

    order_data = order_response.json()
    assert len(order_data["items"]) == 1
    assert order_data["items"][0]["product"]["id"] == product_valid["id"]
    assert order_data["total_price"] == pytest.approx(product_valid["price"] * 2)


def test_create_order_from_cart_with_only_deleted_products_fails(
    client: TestClient,
    user_token_headers: Dict[str, str],
    superuser_token_headers: Dict[str, str],
    db_session: Session,
):
    """Testa que um pedido falha se todos os seus itens eram produtos que foram deletados."""
    product_to_delete = create_product_and_add_to_cart(
        client, user_token_headers, superuser_token_headers
    )
    db_product_to_delete = db_session.get(Product, product_to_delete["id"])
    assert db_product_to_delete is not None

    db_session.delete(db_product_to_delete)
    db_session.commit()

    order_response = client.post("/orders/", headers=user_token_headers)
    assert order_response.status_code == 400
    assert "empty cart" in order_response.json()["detail"]

    cart_response = client.get("/cart/", headers=user_token_headers)
    assert not cart_response.json()["items"]


# -------------------------------------------------------------------------- #
#                       TESTES DE CASOS DE BORDA DE PERMISSÃO                #
# -------------------------------------------------------------------------- #


def test_user_cannot_see_another_users_order(
    client: TestClient,
    user_token_headers: Dict[str, str],
    superuser_token_headers: Dict[str, str],
    db_session: Session,
):
    """Testa se um usuário comum não pode visualizar o pedido de outro usuário."""
    user_b_schema = UserCreate(
        email="user.b@test.com",
        password="passwordB",
        full_name="User B",
        cpf="31212334086",
        phone="(33)77777-7777",
        address_street="Another Street",
        address_number="3",
        address_zip="67890-000",
        address_city="Another City",
        address_state="AC",
    )
    user_b = crud.create_user(db=db_session, user=user_b_schema)
    user_b_token = create_access_token(data={"sub": user_b.email})
    user_b_headers = {"Authorization": f"Bearer {user_b_token}"}

    product = create_product_and_add_to_cart(
        client, user_b_headers, superuser_token_headers
    )
    order_b_response = client.post("/orders/", headers=user_b_headers)
    order_b_id = order_b_response.json()["id"]

    response = client.get(f"/orders/{order_b_id}", headers=user_token_headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to view this order."


def test_read_single_nonexistent_order(
    client: TestClient, user_token_headers: Dict[str, str]
):
    """Testa a busca por um pedido com um ID que não existe (espera 404)."""
    response = client.get("/orders/9999", headers=user_token_headers)
    assert response.status_code == 404
