"""
Módulo de Roteamento para Pedidos (Orders).

Define os endpoints para criar e visualizar os pedidos de um usuário,
concluindo o ciclo de compra do e-commerce. Também inclui endpoints
protegidos para administradores visualizarem e gerenciarem todos os pedidos.
"""

# -------------------------------------------------------------------------- #
#                             IMPORTS NECESSÁRIOS                            #
# -------------------------------------------------------------------------- #
from pydantic import BaseModel
from typing import List
from sqlalchemy.orm import Session, joinedload
from fastapi import APIRouter, Depends, HTTPException, status

from .. import auth, crud, models, schemas
from ..database import get_db

# -------------------------------------------------------------------------- #
#                                ROUTER SETUP                                #
# -------------------------------------------------------------------------- #

router = APIRouter(
    prefix="/orders", tags=["Orders"], dependencies=[Depends(auth.get_current_user)]
)

# -------------------------------------------------------------------------- #
#                       SCHEMAS ESPECÍFICOS PARA ESTA ROTA                   #
# -------------------------------------------------------------------------- #


class StatusUpdate(BaseModel):
    """Schema simples para receber a atualização de status no corpo da requisição PUT."""

    status: str


# -------------------------------------------------------------------------- #
#                        ENDPOINTS PARA ADMINISTRADORES                      #
# -------------------------------------------------------------------------- #


@router.get(
    "/admin",
    response_model=List[schemas.AdminOrder],
    dependencies=[Depends(auth.get_current_superuser)],
)
def read_all_orders_admin(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    """[Admin] Retorna uma lista de todos os pedidos no sistema."""
    orders = crud.get_all_orders(db, skip=skip, limit=limit)
    return orders


@router.put(
    "/{order_id}/status",
    response_model=schemas.AdminOrder,
    dependencies=[Depends(auth.get_current_superuser)],
)
def update_order_status_admin(
    order_id: int, status_update: StatusUpdate, db: Session = Depends(get_db)
):
    """[Admin] Atualiza o status de um pedido específico."""
    order_in_db = crud.get_order_by_id(db, order_id=order_id)

    if not order_in_db:
        raise HTTPException(status_code=404, detail="Pedido não encontrado.")

    allowed_statuses = ["pending_payment", "paid", "shipped", "delivered", "cancelled"]
    if status_update.status not in allowed_statuses:
        raise HTTPException(
            status_code=400, detail=f"Status '{status_update.status}' é inválido."
        )

    order_in_db.status = status_update.status
    db.commit()

    reloaded_order = (
        db.query(models.Order)
        .options(
            joinedload(models.Order.customer),
            joinedload(models.Order.items).joinedload(models.OrderItem.product),
        )
        .filter(models.Order.id == order_id)
        .first()
    )

    if not reloaded_order:
        raise HTTPException(
            status_code=404, detail="Falha ao recarregar o pedido após a atualização."
        )

    return reloaded_order


# -------------------------------------------------------------------------- #
#                          ENDPOINTS PARA CLIENTES                           #
# -------------------------------------------------------------------------- #


@router.post("/", response_model=schemas.Order, status_code=status.HTTP_201_CREATED)
def create_order(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Cria um novo pedido a partir do carrinho atual do usuário."""
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


@router.get("/", response_model=List[schemas.Order])
def read_my_orders(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Retorna o histórico de todos os pedidos feitos pelo usuário atual."""
    return crud.get_orders_by_user(db, user_id=current_user.id)


@router.get("/{order_id}", response_model=schemas.Order)
def read_single_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """
    Busca e retorna um único pedido pelo seu ID.
    Esta rota deve vir DEPOIS de outras rotas mais específicas como /admin.
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
