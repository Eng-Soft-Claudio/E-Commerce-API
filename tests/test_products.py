"""
Suíte de Testes para o recurso de Produtos (Products).

Testa todos os endpoints sob o prefixo '/products', cobrindo:
- Acesso público a endpoints de leitura.
- Controle de acesso baseado em permissões para operações de escrita.
- A lógica de negócio de associar um produto a uma categoria.
- Validação de SKU único na criação e atualização.
- Gerenciamento de estoque através dos endpoints de admin.
- Casos de borda como IDs não encontrados e dados inválidos.
"""

# -------------------------------------------------------------------------- #
#                             IMPORTS NECESSÁRIOS                            #
# -------------------------------------------------------------------------- #

from typing import Dict

from fastapi.testclient import TestClient

# -------------------------------------------------------------------------- #
#                        FUNÇÃO AUXILIAR DE SETUP                            #
# -------------------------------------------------------------------------- #


def create_category_and_get_id(client: TestClient, headers: Dict, title: str) -> int:
    """Função auxiliar para criar uma categoria de teste e retornar seu ID."""
    category_data = {"title": title, "description": f"Categoria {title}"}
    response = client.post("/categories/", headers=headers, json=category_data)
    assert response.status_code == 201, response.text
    return response.json()["id"]


# -------------------------------------------------------------------------- #
#                       TESTES DE ACESSO PÚBLICO                             #
# -------------------------------------------------------------------------- #


def test_read_products_publicly(client: TestClient):
    """Testa se GET /products/ é público e retorna uma lista vazia em um BD limpo."""
    response = client.get("/products/")
    assert response.status_code == 200
    assert response.json() == []


def test_read_single_product_not_found(client: TestClient):
    """Testa a solicitação de um produto com um ID que não existe."""
    response = client.get("/products/9999")
    assert response.status_code == 404
    assert "Produto não encontrado" in response.json()["detail"]


# -------------------------------------------------------------------------- #
#         TESTES DE CRUD COMPLETO E VALIDAÇÃO (COMO SUPERUSER)               #
# -------------------------------------------------------------------------- #


def test_superuser_product_crud_cycle(
    client: TestClient, superuser_token_headers: Dict
):
    """Testa o ciclo de vida completo (CRUD) de um produto por um superuser."""
    category_id = create_category_and_get_id(
        client, superuser_token_headers, "Eletronicos"
    )

    product_data = {
        "name": "Laptop Pro",
        "sku": "LP12345",
        "price": 5000.0,
        "category_id": category_id,
        "stock": 10,
    }
    create_response = client.post(
        "/products/", headers=superuser_token_headers, json=product_data
    )
    assert create_response.status_code == 201, create_response.text
    product = create_response.json()
    product_id = product["id"]

    assert product["name"] == product_data["name"]
    assert product["sku"] == product_data["sku"]
    assert product["stock"] == product_data["stock"]

    read_response = client.get(f"/products/{product_id}")
    assert read_response.status_code == 200
    assert read_response.json()["name"] == product_data["name"]

    update_data = {"name": "Laptop Ultra", "price": 5500.0, "stock": 5}
    update_response = client.put(
        f"/products/{product_id}", headers=superuser_token_headers, json=update_data
    )
    assert update_response.status_code == 200, update_response.text
    updated_product = update_response.json()
    assert updated_product["name"] == update_data["name"]
    assert updated_product["price"] == update_data["price"]
    assert updated_product["stock"] == update_data["stock"]

    delete_response = client.delete(
        f"/products/{product_id}", headers=superuser_token_headers
    )
    assert delete_response.status_code == 200

    confirm_response = client.get(f"/products/{product_id}")
    assert confirm_response.status_code == 404


# -------------------------------------------------------------------------- #
#                        TESTES DE CASOS DE BORDA                            #
# -------------------------------------------------------------------------- #


def test_create_product_with_duplicate_sku(
    client: TestClient, superuser_token_headers: Dict
):
    """Testa a falha ao criar um produto com um SKU que já existe."""
    category_id = create_category_and_get_id(client, superuser_token_headers, "Livros")
    product_data = {
        "name": "Livro de Teste",
        "sku": "LIVRO-SKU-UNICO",
        "price": 29.99,
        "category_id": category_id,
    }
    client.post(
        "/products/", headers=superuser_token_headers, json=product_data
    ).raise_for_status()

    product_data_2 = {**product_data, "name": "Outro Livro"}
    response = client.post(
        "/products/", headers=superuser_token_headers, json=product_data_2
    )
    assert response.status_code == 400
    assert "SKU já cadastrado" in response.json()["detail"]


def test_update_product_with_duplicate_sku(
    client: TestClient, superuser_token_headers: Dict
):
    """Testa a falha ao atualizar um produto para um SKU que já pertence a outro."""
    category_id = create_category_and_get_id(
        client, superuser_token_headers, "Ferramentas"
    )
    prod1_data = {
        "name": "Martelo",
        "sku": "FER-001",
        "price": 50,
        "category_id": category_id,
    }
    client.post("/products/", headers=superuser_token_headers, json=prod1_data)
    prod2_data = {
        "name": "Chave de Fenda",
        "sku": "FER-002",
        "price": 20,
        "category_id": category_id,
    }
    response = client.post(
        "/products/", headers=superuser_token_headers, json=prod2_data
    )
    product_2_id = response.json()["id"]

    update_data = {"sku": "FER-001"}
    update_response = client.put(
        f"/products/{product_2_id}", headers=superuser_token_headers, json=update_data
    )
    assert update_response.status_code == 400
    assert "SKU já pertence a outro produto" in update_response.json()["detail"]


# -------------------------------------------------------------------------- #
#                        TESTES DE CASOS DE BORDA                            #
# -------------------------------------------------------------------------- #


def test_create_product_with_nonexistent_category(
    client: TestClient, superuser_token_headers: Dict
):
    """Testa a criação de um produto com category_id inválida (espera 404)."""
    product_data = {
        "name": "Produto Órfão",
        "sku": "ORFAO-01",
        "price": 10.0,
        "category_id": 9999,
        "stock": 5,
    }
    response = client.post(
        "/products/", headers=superuser_token_headers, json=product_data
    )
    assert response.status_code == 404
    assert "Categoria não encontrada" in response.json()["detail"]


def test_update_product_with_nonexistent_category(
    client: TestClient, superuser_token_headers: Dict
):
    """
    Testa a atualização de um produto para uma category_id inválida (espera 404).
    """
    category_id = create_category_and_get_id(
        client, superuser_token_headers, "Cat Original"
    )
    prod_data = {
        "name": "Produto a ser movido",
        "sku": "MOVER-01",
        "price": 50,
        "category_id": category_id,
    }
    prod_resp = client.post(
        "/products/", headers=superuser_token_headers, json=prod_data
    )
    product_id = prod_resp.json()["id"]

    update_data = {"category_id": 9999}
    response = client.put(
        f"/products/{product_id}", headers=superuser_token_headers, json=update_data
    )
    assert response.status_code == 404, response.text
    assert "Categoria não encontrada" in response.json()["detail"]


def test_update_nonexistent_product(client: TestClient, superuser_token_headers: Dict):
    """Testa a falha ao tentar atualizar um produto com ID inexistente."""
    update_data = {"name": "Produto Fantasma", "price": 99.99}
    response = client.put(
        "/products/9999", headers=superuser_token_headers, json=update_data
    )
    assert response.status_code == 404
    assert "Produto não encontrado" in response.json()["detail"]


def test_delete_nonexistent_product(client: TestClient, superuser_token_headers: Dict):
    """Testa a falha ao tentar deletar um produto com ID inexistente."""
    response = client.delete("/products/9999", headers=superuser_token_headers)
    assert response.status_code == 404
    assert "Produto não encontrado" in response.json()["detail"]


def test_read_products_filtered_by_category(
    client: TestClient, superuser_token_headers: Dict
):
    """Testa se a listagem de produtos com o filtro de categoria funciona."""
    cat_a_id = create_category_and_get_id(
        client, superuser_token_headers, title="Cat A"
    )
    cat_b_id = create_category_and_get_id(
        client, superuser_token_headers, title="Cat B"
    )

    client.post(
        "/products/",
        headers=superuser_token_headers,
        json={
            "name": "Produto A",
            "sku": "PROD-A",
            "price": 10,
            "category_id": cat_a_id,
        },
    ).raise_for_status()

    client.post(
        "/products/",
        headers=superuser_token_headers,
        json={
            "name": "Produto B",
            "sku": "PROD-B",
            "price": 20,
            "category_id": cat_b_id,
        },
    ).raise_for_status()

    response = client.get(f"/products/?category_id={cat_a_id}")
    assert response.status_code == 200

    products = response.json()
    assert len(products) == 1
    assert products[0]["name"] == "Produto A"
    assert products[0]["category"]["id"] == cat_a_id
