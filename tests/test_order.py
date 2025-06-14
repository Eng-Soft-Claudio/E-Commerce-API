"""
Suíte de Testes para o recurso de Pedidos (Orders).

Testa todos os endpoints sob o prefixo '/orders', cobrindo o fluxo de
vida completo de um pedido.
"""

import pytest
from typing import Dict
from fastapi.testclient import TestClient

from sqlalchemy.orm import Session
from src.auth import create_access_token
from src.schemas import UserCreate
from src import crud

# -------------------------------------------------------------------------- #
#                        FUNÇÃO AUXILIAR DE SETUP                            #
# -------------------------------------------------------------------------- #


def create_product_and_add_to_cart(
    client: TestClient, user_headers: Dict, admin_headers: Dict
) -> Dict:
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
    client: TestClient, superuser_token_headers: Dict
):
    """Testa que superusers não podem criar pedidos (espera 403)."""
    response = client.post("/orders/", headers=superuser_token_headers)
    assert response.status_code == 403


def test_create_order_unauthorized(client: TestClient):
    """Testa que clientes não autenticados não podem criar pedidos (espera 401)."""
    response = client.post("/orders/")
    assert response.status_code == 401


def test_create_order_from_empty_cart_fails(
    client: TestClient, user_token_headers: Dict
):
    """Testa a criação de um pedido com um carrinho vazio (espera 400)."""
    response = client.post("/orders/", headers=user_token_headers)
    assert response.status_code == 400


# -------------------------------------------------------------------------- #
#                       TESTES DO FLUXO PRINCIPAL E HISTÓRICO                #
# -------------------------------------------------------------------------- #


def test_order_creation_and_history_flow(
    client: TestClient, user_token_headers: Dict, superuser_token_headers: Dict
):
    """
    Testa o fluxo de ponta-a-ponta: popular carrinho -> criar pedido ->
    verificar detalhes -> verificar histórico -> verificar carrinho vazio.
    """
    # 1. Setup
    product = create_product_and_add_to_cart(
        client, user_token_headers, superuser_token_headers
    )

    # 2. Criação
    order_response = client.post("/orders/", headers=user_token_headers)
    assert order_response.status_code == 201
    order_data = order_response.json()
    order_id = order_data["id"]

    # 3. Verificação
    assert order_data["total_price"] == pytest.approx(product["price"] * 2)

    # 4. Histórico
    history_response = client.get("/orders/", headers=user_token_headers)
    assert history_response.status_code == 200
    assert any(order["id"] == order_id for order in history_response.json())

    # 5. Carrinho Vazio
    cart_response = client.get("/cart/", headers=user_token_headers)
    assert cart_response.status_code == 200
    assert cart_response.json()["items"] == []


def test_user_can_see_own_single_order(
    client: TestClient, user_token_headers: Dict, superuser_token_headers: Dict
):
    """
    Testa se um usuário comum pode buscar e visualizar um de seus próprios pedidos.

    Este é o teste de 'caminho feliz' para a função 'read_single_order'
    e cobrirá a linha final 'return order'.
    """
    # 1. Setup: Cria um produto e um pedido para o usuário de teste
    product = create_product_and_add_to_cart(
        client, user_token_headers, superuser_token_headers
    )
    order_response = client.post("/orders/", headers=user_token_headers)
    assert order_response.status_code == 201
    order_id = order_response.json()["id"]

    # 2. Teste: O mesmo usuário tenta buscar o pedido que acabou de criar
    get_response = client.get(f"/orders/{order_id}", headers=user_token_headers)

    # 3. Assert: A requisição deve ser bem-sucedida (200 OK)
    assert get_response.status_code == 200
    order_data = get_response.json()
    assert order_data["id"] == order_id
    assert order_data["items"][0]["product"]["id"] == product["id"]


# -------------------------------------------------------------------------- #
#                       TESTES DE CASOS DE BORDA DE PERMISSÃO                #
# -------------------------------------------------------------------------- #


def test_user_cannot_see_another_users_order(
    client: TestClient,
    user_token_headers: Dict,
    superuser_token_headers: Dict,
    db_session: Session,  # <- Anotação de tipo correta
):
    """
    Testa se um usuário comum não pode visualizar o pedido de outro usuário.
    Cobre o bloco de verificação de permissão em `read_single_order`.
    """
    # 1. Setup do Produto
    product = create_product_and_add_to_cart(
        client, user_token_headers, superuser_token_headers
    )

    # 2. Setup do Usuário B (Dono do Pedido)
    user_b_schema = UserCreate(email="user.b@test.com", password="passwordB")
    user_b = crud.create_user(db=db_session, user=user_b_schema)

    # 3. Usuário B cria seu pedido
    user_b_token = create_access_token(data={"sub": user_b.email})
    user_b_headers = {"Authorization": f"Bearer {user_b_token}"}
    client.post(
        "/cart/items/",
        headers=user_b_headers,
        json={"product_id": product["id"], "quantity": 1},
    )
    order_b_response = client.post("/orders/", headers=user_b_headers)
    order_b_id = order_b_response.json()["id"]

    # 4. Usuário A (invasor) tenta acessar o pedido de B
    response = client.get(f"/orders/{order_b_id}", headers=user_token_headers)

    # 5. Assert: Espera 403 Forbidden
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authorized to view this order."


def test_read_single_nonexistent_order(client: TestClient, user_token_headers: Dict):
    """Testa a busca por um pedido com um ID que não existe (espera 404)."""
    response = client.get("/orders/9999", headers=user_token_headers)
    assert response.status_code == 404
