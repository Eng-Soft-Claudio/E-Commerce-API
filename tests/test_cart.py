"""
Suíte de Testes para o recurso de Carrinho de Compras (Shopping Cart).

Testa todos os endpoints sob o prefixo '/cart', cobrindo:
- O fluxo de vida completo do carrinho de um usuário comum.
- Validações de permissão (ex: superuser não pode ter carrinho).
- Casos de borda como adicionar produtos inexistentes ou manipular um carrinho vazio.
"""

import pytest
from fastapi.testclient import TestClient
from typing import Dict, Any
from sqlalchemy.orm import Session
from src.models import Cart

# -------------------------------------------------------------------------- #
#                        FUNÇÃO AUXILIAR DE SETUP                            #
# -------------------------------------------------------------------------- #


def create_product_for_testing(
    client: TestClient, headers: Dict[str, str]
) -> Dict[str, Any]:
    """Função auxiliar para criar uma categoria e um produto para testes."""
    cat_resp = client.post(
        "/categories/", headers=headers, json={"title": "Carrinho Categ"}
    )
    assert cat_resp.status_code == 201

    prod_data = {
        "name": "Item de Teste Carrinho",
        "price": 10.99,
        "category_id": cat_resp.json()["id"],
    }
    prod_resp = client.post("/products/", headers=headers, json=prod_data)
    assert prod_resp.status_code == 201
    return prod_resp.json()


# -------------------------------------------------------------------------- #
#                         TESTES DE CONTROLE DE ACESSO                       #
# -------------------------------------------------------------------------- #


def test_superuser_has_no_cart(
    client: TestClient, superuser_token_headers: Dict[str, str]
):
    """Testa se superusers não podem acessar o endpoint do carrinho (espera 403)."""
    response = client.get("/cart/", headers=superuser_token_headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Superusers do not have a shopping cart."


def test_cart_access_unauthorized(client: TestClient):
    """Testa se clientes não autenticados não podem acessar o carrinho (espera 401)."""
    response = client.get("/cart/")
    assert response.status_code == 401


# -------------------------------------------------------------------------- #
#               TESTES DO FLUXO COMPLETO DO CARRINHO DE COMPRAS              #
# -------------------------------------------------------------------------- #


def test_user_cart_full_flow(
    client: TestClient,
    user_token_headers: Dict[str, str],
    superuser_token_headers: Dict[str, str],
):
    """
    Testa o fluxo completo do carrinho de um usuário comum.
    1. Visualiza o carrinho vazio.
    2. Adiciona um item e verifica o estado do carrinho.
    3. Adiciona mais do mesmo item e verifica a atualização da quantidade.
    4. Remove o item e verifica se o carrinho volta a ficar vazio.
    """
    product = create_product_for_testing(client, superuser_token_headers)
    product_id = product["id"]
    product_price = product["price"]

    cart_resp = client.get("/cart/", headers=user_token_headers)
    assert cart_resp.status_code == 200
    assert cart_resp.json()["items"] == []

    add_resp = client.post(
        "/cart/items/",
        headers=user_token_headers,
        json={"product_id": product_id, "quantity": 2},
    )
    assert add_resp.status_code == 200

    cart_resp_after_add = client.get("/cart/", headers=user_token_headers)
    cart_data = cart_resp_after_add.json()
    assert len(cart_data["items"]) == 1
    assert cart_data["items"][0]["quantity"] == 2
    assert cart_data["total_price"] == pytest.approx(product_price * 2)

    client.post(
        "/cart/items/",
        headers=user_token_headers,
        json={"product_id": product_id, "quantity": 1},
    )

    cart_resp_after_update = client.get("/cart/", headers=user_token_headers)
    cart_data_updated = cart_resp_after_update.json()
    assert len(cart_data_updated["items"]) == 1
    assert cart_data_updated["items"][0]["quantity"] == 3
    assert cart_data_updated["total_price"] == pytest.approx(product_price * 3)

    del_resp = client.delete(f"/cart/items/{product_id}", headers=user_token_headers)
    assert del_resp.status_code == 200

    cart_resp_final = client.get("/cart/", headers=user_token_headers)
    assert cart_resp_final.json()["items"] == []


# -------------------------------------------------------------------------- #
#          TESTES DE ATUALIZAÇÃO DE ITENS NO CARRINHO (PUT)                  #
# -------------------------------------------------------------------------- #


def test_update_cart_item_quantity_successfully(
    client: TestClient,
    user_token_headers: Dict[str, str],
    superuser_token_headers: Dict[str, str],
):
    """Testa a atualização bem-sucedida da quantidade de um item no carrinho."""
    product = create_product_for_testing(client, superuser_token_headers)
    product_id = product["id"]
    client.post(
        "/cart/items/",
        headers=user_token_headers,
        json={"product_id": product_id, "quantity": 1},
    )

    update_response = client.put(
        f"/cart/items/{product_id}",
        headers=user_token_headers,
        json={"quantity": 5},
    )
    assert update_response.status_code == 200
    updated_item = update_response.json()
    assert updated_item["quantity"] == 5

    cart_response = client.get("/cart/", headers=user_token_headers)
    cart_data = cart_response.json()
    assert len(cart_data["items"]) == 1
    assert cart_data["items"][0]["quantity"] == 5
    assert cart_data["total_price"] == pytest.approx(product["price"] * 5)


def test_update_cart_item_quantity_to_zero_removes_item(
    client: TestClient,
    user_token_headers: Dict[str, str],
    superuser_token_headers: Dict[str, str],
):
    """Testa se atualizar a quantidade de um item para 0 o remove do carrinho."""
    product = create_product_for_testing(client, superuser_token_headers)
    product_id = product["id"]
    client.post(
        "/cart/items/",
        headers=user_token_headers,
        json={"product_id": product_id, "quantity": 2},
    )
    update_response = client.put(
        f"/cart/items/{product_id}",
        headers=user_token_headers,
        json={"quantity": 0},
    )
    assert update_response.status_code == 204
    cart_response = client.get("/cart/", headers=user_token_headers)
    assert not cart_response.json()["items"]


def test_update_cart_item_for_nonexistent_product(
    client: TestClient, user_token_headers: Dict[str, str]
):
    """Testa a falha ao tentar atualizar um produto que não existe no BD."""
    response = client.put(
        "/cart/items/9999",
        headers=user_token_headers,
        json={"quantity": 5},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found."


def test_update_cart_item_that_is_not_in_cart(
    client: TestClient,
    user_token_headers: Dict[str, str],
    superuser_token_headers: Dict[str, str],
):
    """Testa a falha ao tentar atualizar um item que não está no carrinho."""
    product = create_product_for_testing(client, superuser_token_headers)
    product_id = product["id"]
    response = client.put(
        f"/cart/items/{product_id}",
        headers=user_token_headers,
        json={"quantity": 5},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Item not in cart."


# -------------------------------------------------------------------------- #
#                             TESTES DE CASOS DE BORDA                       #
# -------------------------------------------------------------------------- #


def test_add_nonexistent_product_to_cart(
    client: TestClient, user_token_headers: Dict[str, str]
):
    """Testa adicionar um produto com ID inválido ao carrinho (espera 404)."""
    item_data = {"product_id": 9999, "quantity": 1}
    response = client.post("/cart/items/", headers=user_token_headers, json=item_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found."


def test_remove_nonexistent_product_from_cart(
    client: TestClient, user_token_headers: Dict[str, str]
):
    """Testa remover um produto que não está no carrinho (espera 404)."""
    response = client.delete("/cart/items/9999", headers=user_token_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found in cart."


def test_superuser_cannot_add_item_to_cart(
    client: TestClient, superuser_token_headers: Dict[str, str]
):
    """
    Testa se um superuser é proibido de adicionar itens, mesmo que não tenha carrinho.
    Cobre a linha 87 em routers/cart.py.
    """
    item_data = {"product_id": 1, "quantity": 1}
    response = client.post(
        "/cart/items/", headers=superuser_token_headers, json=item_data
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Superusers cannot add items to a cart."


def test_superuser_cannot_remove_item_from_cart(
    client: TestClient, superuser_token_headers: Dict[str, str]
):
    """
    Testa se um superuser é proibido de remover itens.
    Cobre a linha 123 em routers/cart.py.
    """
    response = client.delete("/cart/items/1", headers=superuser_token_headers)
    assert response.status_code == 403
    assert (
        response.json()["detail"]
        == "Superusers do not have a cart to remove items from."
    )


def test_read_cart_when_cart_is_missing(
    client: TestClient,
    user_token_headers: Dict[str, str],
    db_session: Session,
    test_user: Dict,
):
    """
    Testa o caso raro de um usuário não ter um carrinho associado.
    Cobre a linha 56 em routers/cart.py.
    """
    user_id = test_user["id"]
    cart_to_delete = db_session.query(Cart).filter(Cart.user_id == user_id).first()
    assert cart_to_delete is not None, "O carrinho deveria ter sido criado."

    db_session.delete(cart_to_delete)
    db_session.commit()

    response = client.get("/cart/", headers=user_token_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Cart not found for this user."
