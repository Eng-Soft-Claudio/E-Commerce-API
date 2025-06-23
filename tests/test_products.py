"""
Suíte de Testes para o recurso de Produtos (Products).

Testa todos os endpoints sob o prefixo '/products', cobrindo:
- Acesso público a endpoints de leitura.
- Controle de acesso baseado em permissões para operações de escrita.
- A lógica de negócio de associar um produto a uma categoria.
- Casos de borda como IDs não encontrados e dados inválidos.
"""

from fastapi.testclient import TestClient
from typing import Dict

# -------------------------------------------------------------------------- #
#                        FUNÇÃO AUXILIAR DE SETUP                            #
# -------------------------------------------------------------------------- #


def create_category_and_get_id(
    client: TestClient, headers: Dict[str, str], title: str = "Categoria Para Produtos"
) -> int:
    """Função auxiliar para criar uma categoria de teste e retornar seu ID."""
    category_data = {"title": title, "description": "Usada nos testes"}
    response = client.post("/categories/", headers=headers, json=category_data)
    assert response.status_code == 201
    return response.json()["id"]


# -------------------------------------------------------------------------- #
#                TESTES DE ACESSO PÚBLICO E NÃO-AUTENTICADO                  #
# -------------------------------------------------------------------------- #


def test_read_products_publicly(client: TestClient):
    """Testa se GET /products/ é público e retorna uma lista vazia em um BD limpo."""
    response = client.get("/products/")
    assert response.status_code == 200
    assert response.json() == []


def test_read_single_product_not_found(client: TestClient):
    """Testa a solicitação de um produto com um ID que não existe (espera 404)."""
    response = client.get("/products/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


def test_create_product_unauthorized(client: TestClient):
    """Testa se um cliente não autenticado é bloqueado de criar um produto (espera 401)."""
    product_data = {"name": "Produto Falha", "price": 10.0, "category_id": 1}
    response = client.post("/products/", json=product_data)
    assert response.status_code == 401


# -------------------------------------------------------------------------- #
#                       TESTES DE CONTROLE DE ACESSO (PERMISSÕES)            #
# -------------------------------------------------------------------------- #


def test_create_product_as_common_user_is_forbidden(
    client: TestClient, user_token_headers: Dict[str, str]
):
    """Testa se um usuário comum não pode criar um produto (espera 403)."""
    product_data = {"name": "Produto Proibido", "price": 10.0, "category_id": 1}
    response = client.post("/products/", headers=user_token_headers, json=product_data)
    assert response.status_code == 403


# -------------------------------------------------------------------------- #
#         TESTES DE CRUD COMPLETO E FILTRAGEM (COMO SUPERUSER)               #
# -------------------------------------------------------------------------- #


def test_superuser_product_crud_cycle(
    client: TestClient, superuser_token_headers: Dict[str, str]
):
    """Testa o ciclo de vida completo (CRUD) de um produto por um superuser."""
    category_id = create_category_and_get_id(client, superuser_token_headers)

    product_data = {"name": "Laptop Pro", "price": 5000, "category_id": category_id}
    create_response = client.post(
        "/products/", headers=superuser_token_headers, json=product_data
    )
    assert create_response.status_code == 201
    product = create_response.json()
    product_id = product["id"]
    assert product["name"] == product_data["name"]
    assert product["category"]["id"] == category_id

    read_response = client.get(f"/products/{product_id}")
    assert read_response.status_code == 200
    assert read_response.json()["name"] == product_data["name"]

    update_data = {"name": "Laptop Ultra", "price": 5500, "description": "Novo!"}
    update_response = client.put(
        f"/products/{product_id}", headers=superuser_token_headers, json=update_data
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == update_data["name"]

    delete_response = client.delete(
        f"/products/{product_id}", headers=superuser_token_headers
    )
    assert delete_response.status_code == 200

    confirm_response = client.get(f"/products/{product_id}")
    assert confirm_response.status_code == 404


def test_read_products_filtered_by_category(
    client: TestClient, superuser_token_headers: Dict[str, str]
):
    """Testa a listagem de produtos com o filtro de categoria."""
    cat_a_id = create_category_and_get_id(
        client, superuser_token_headers, title="Cat A"
    )
    cat_b_id = create_category_and_get_id(
        client, superuser_token_headers, title="Cat B"
    )

    client.post(
        "/products/",
        headers=superuser_token_headers,
        json={"name": "Produto A", "price": 10, "category_id": cat_a_id},
    ).raise_for_status()
    client.post(
        "/products/",
        headers=superuser_token_headers,
        json={"name": "Produto B", "price": 20, "category_id": cat_b_id},
    ).raise_for_status()

    response = client.get(f"/products/?category_id={cat_a_id}")
    assert response.status_code == 200

    products = response.json()
    assert len(products) == 1
    assert products[0]["name"] == "Produto A"
    assert products[0]["category"]["id"] == cat_a_id


# -------------------------------------------------------------------------- #
#                        TESTES DE CASOS DE BORDA                            #
# -------------------------------------------------------------------------- #


def test_create_product_with_nonexistent_category(
    client: TestClient, superuser_token_headers: Dict[str, str]
):
    """Testa a criação de um produto com category_id inválida (espera 404)."""
    product_data = {"name": "Órfão", "price": 10, "category_id": 999}
    response = client.post(
        "/products/", headers=superuser_token_headers, json=product_data
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Category not found to link product"


def test_update_nonexistent_product(
    client: TestClient, superuser_token_headers: Dict[str, str]
):
    """Testa a atualização de um produto com um ID inexistente."""
    update_data = {"name": "Produto Fantasma", "price": 99.99}
    response = client.put(
        "/products/9999", headers=superuser_token_headers, json=update_data
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


def test_delete_nonexistent_product(
    client: TestClient, superuser_token_headers: Dict[str, str]
):
    """Testa a deleção de um produto com um ID inexistente."""
    response = client.delete("/products/9999", headers=superuser_token_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"
