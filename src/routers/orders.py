"""
Módulo de Roteamento para Pedidos (Orders).

Define os endpoints para criar e visualizar os pedidos de um usuário,
concluindo o ciclo de compra do e-commerce.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import auth, crud, models, schemas
from ..database import get_db

# -------------------------------------------------------------------------- #
#                                ROUTER SETUP                                #
# -------------------------------------------------------------------------- #

router = APIRouter(
    prefix="/orders", tags=["Orders"], dependencies=[Depends(auth.get_current_user)]
)


# -------------------------------------------------------------------------- #
#                             ORDER API ENDPOINTS                            #
# -------------------------------------------------------------------------- #


@router.post("/", response_model=schemas.Order, status_code=status.HTTP_201_CREATED)
def create_order(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Cria um novo pedido a partir do carrinho atual do usuário.

    Esta operação converte o conteúdo do carrinho em um pedido permanente,
    armazenando um snapshot dos preços, e limpa o carrinho após a conclusão.

    Args:
        db (Session): A sessão do banco de dados.
        current_user (models.User): O usuário autenticado que está fazendo o pedido.

    Raises:
        HTTPException(403): Se um superuser tentar criar um pedido.
        HTTPException(400): Se o carrinho estiver vazio no momento da finalização.

    Returns:
        schemas.Order: O pedido recém-criado.
    """
    if current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superusers cannot create orders.",
        )

    order = crud.create_order_from_cart(db, user=current_user)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create an order from an empty cart.",
        )
    return order


@router.get("/", response_model=list[schemas.Order])
def read_my_orders(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Retorna o histórico de todos os pedidos feitos pelo usuário atual.

    Args:
        db (Session): A sessão do banco de dados.
        current_user (models.User): O usuário autenticado.

    Returns:
        list[schemas.Order]: Uma lista de todos os pedidos do usuário.
    """
    return crud.get_orders_by_user(db, user_id=current_user.id)


@router.get("/{order_id}", response_model=schemas.Order)
def read_single_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Busca e retorna um único pedido pelo seu ID.

    Impõe uma verificação de permissão: usuários normais só podem ver
    seus próprios pedidos, enquanto superusers podem ver qualquer pedido.

    Args:
        order_id (int): O ID do pedido a ser buscado.
        db (Session): A sessão do banco de dados.
        current_user (models.User): O usuário autenticado.

    Raises:
        HTTPException(404): Se o pedido não for encontrado.
        HTTPException(403): Se um usuário tentar ver um pedido que não lhe pertence.

    Returns:
        schemas.Order: O objeto do pedido encontrado.
    """
    order = crud.get_order_by_id(db, order_id=order_id)

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Order not found."
        )
    if not current_user.is_superuser and order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this order.",
        )
    return order
