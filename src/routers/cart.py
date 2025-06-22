"""
Módulo de Roteamento para o Carrinho de Compras do Usuário.

Define todos os endpoints da API para visualizar e manipular o carrinho de compras
de um usuário autenticado. Todas as rotas neste módulo exigem um usuário
logado para serem acessadas.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import auth, crud, models, schemas
from ..database import get_db

# -------------------------------------------------------------------------- #
#                                ROUTER SETUP                                #
# -------------------------------------------------------------------------- #

router = APIRouter(
    prefix="/cart",
    tags=["Shopping Cart"],
    dependencies=[Depends(auth.get_current_user)],
)


# -------------------------------------------------------------------------- #
#                        SHOPPING CART API ENDPOINTS                         #
# -------------------------------------------------------------------------- #


@router.get("/", response_model=schemas.Cart)
def read_my_cart(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Retorna o carrinho de compras completo do usuário atualmente autenticado.

    Args:
        db (Session): A sessão do banco de dados, injetada por dependência.
        current_user (models.User): O usuário logado, obtido a partir do token.

    Raises:
        HTTPException(404): Se um carrinho não for encontrado para o usuário.

    Returns:
        schemas.Cart: O objeto do carrinho, incluindo itens e preço total.
    """
    if current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superusers do not have a shopping cart.",
        )
    cart = crud.get_cart_by_user_id(db, user_id=current_user.id)
    if not cart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart not found for this user.",
        )
    return cart


@router.post("/items/", response_model=schemas.CartItem)
def add_product_to_cart(
    item: schemas.CartItemCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Adiciona um produto ao carrinho do usuário ou atualiza sua quantidade.

    Se o produto já existir no carrinho, a quantidade fornecida é somada
    à quantidade existente. Caso contrário, um novo item é criado no carrinho.

    Args:
        item (schemas.CartItemCreate): Dados do item a ser adicionado.
        db (Session): A sessão do banco de dados.
        current_user (models.User): O usuário logado.

    Raises:
        HTTPException(404): Se o produto que está sendo adicionado não existir.

    Returns:
        schemas.CartItem: O item de carrinho criado ou atualizado.
    """
    if current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superusers cannot add items to a cart.",
        )

    cart = current_user.cart
    db_product = crud.get_product(db, product_id=item.product_id)
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found."
        )

    return crud.add_item_to_cart(db, cart_id=cart.id, item=item)


@router.delete("/items/{product_id}", response_model=dict)
def remove_product_from_cart(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Remove um produto específico do carrinho do usuário atual.

    Args:
        product_id (int): O ID do produto a ser removido do carrinho.
        db (Session): A sessão do banco de dados.
        current_user (models.User): O usuário logado.

    Raises:
        HTTPException(404): Se o produto não for encontrado no carrinho do usuário.

    Returns:
        dict: Uma mensagem de confirmação de sucesso.
    """
    if current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superusers do not have a cart to remove items from.",
        )

    cart = current_user.cart
    item_removed = crud.remove_cart_item(db, cart_id=cart.id, product_id=product_id)

    if not item_removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found in cart."
        )

    return {"message": "Item removed from cart successfully."}


@router.put("/items/{product_id}", response_model=schemas.CartItem)
def update_cart_item(
    product_id: int,
    item_update: schemas.CartItemUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Atualiza a quantidade de um item no carrinho do usuário.
    """
    cart = current_user.cart

    db_product = crud.get_product(db, product_id=product_id)
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Product not found."
        )

    updated_item = crud.update_cart_item_quantity(
        db, cart_id=cart.id, product_id=product_id, quantity=item_update.quantity
    )

    if updated_item is None and item_update.quantity <= 0:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)

    if not updated_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Item not in cart."
        )

    return updated_item
