"""
Módulo CRUD (Create, Read, Update, Delete) para os modelos.

Este arquivo abstrai a lógica de acesso ao banco de dados, separando-a da
lógica dos endpoints da API. Cada função aqui interage diretamente com a
sessão do SQLAlchemy para manipular os dados, garantindo a consistência das
transações e encapsulando as regras de negócio de acesso a dados.
"""

# -------------------------------------------------------------------------- #
#                             IMPORTS NECESSÁRIOS                            #
# -------------------------------------------------------------------------- #

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session, joinedload, selectinload

from . import auth, models, schemas

# -------------------------------------------------------------------------- #
#                         CRUD FUNCTIONS - CATEGORY                          #
# -------------------------------------------------------------------------- #


def get_category(db: Session, category_id: int) -> Optional[models.Category]:
    """Busca uma única categoria pelo seu ID."""
    return db.query(models.Category).filter(models.Category.id == category_id).first()


def get_categories(
    db: Session, skip: int = 0, limit: int = 100
) -> list[models.Category]:
    """Busca uma lista de categorias com paginação."""
    return db.query(models.Category).offset(skip).limit(limit).all()


def create_category(db: Session, category: schemas.CategoryCreate) -> models.Category:
    """Cria uma nova categoria no banco de dados."""
    db_category = models.Category(
        title=category.title, description=category.description
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


def update_category(
    db: Session, category_id: int, category_data: schemas.CategoryCreate
) -> Optional[models.Category]:
    """Atualiza uma categoria existente no banco de dados."""
    db_category = get_category(db, category_id)
    if db_category:
        db_category.title = category_data.title
        db_category.description = category_data.description
        db.commit()
        db.refresh(db_category)
    return db_category


def delete_category(db: Session, category_id: int) -> Optional[models.Category]:
    """Deleta uma categoria do banco de dados."""
    db_category = get_category(db, category_id)
    if db_category:
        db.delete(db_category)
        db.commit()
    return db_category


# -------------------------------------------------------------------------- #
#                          CRUD FUNCTIONS - USERS                            #
# -------------------------------------------------------------------------- #


def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """Busca um usuário pelo seu email."""
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(
    db: Session, user: schemas.UserCreate, is_superuser: bool = False
) -> models.User:
    """Cria um novo usuário, com a senha hasheada e todos os dados pessoais."""
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        **user.model_dump(exclude={"password"}),
        hashed_password=hashed_password,
        is_superuser=is_superuser,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    if not db_user.is_superuser:
        db_cart = models.Cart(owner=db_user)
        db.add(db_cart)
        db.commit()

    return db_user


def get_all_users(db: Session, skip: int = 0, limit: int = 100) -> list[models.User]:
    """[Admin] Busca todos os usuários (clientes), com paginação."""
    return (
        db.query(models.User)
        .filter(models.User.is_superuser.is_(False))
        .offset(skip)
        .limit(limit)
        .all()
    )


# -------------------------------------------------------------------------- #
#                         CRUD FUNCTIONS - PRODUCTS                          #
# -------------------------------------------------------------------------- #


def get_product(db: Session, product_id: int) -> Optional[models.Product]:
    """Busca um único produto pelo seu ID."""
    return db.query(models.Product).filter(models.Product.id == product_id).first()


def get_product_by_sku(db: Session, sku: str) -> Optional[models.Product]:
    """Busca um único produto pelo seu SKU."""
    return db.query(models.Product).filter(models.Product.sku == sku).first()


def get_products(
    db: Session, skip: int = 0, limit: int = 100, category_id: Optional[int] = None
) -> list[models.Product]:
    """Busca uma lista de produtos, com filtro opcional por categoria."""
    query = db.query(models.Product)
    if category_id is not None:
        query = query.filter(models.Product.category_id == category_id)
    return query.offset(skip).limit(limit).all()


def create_product(db: Session, product: schemas.ProductCreate) -> models.Product:
    """Cria um novo produto no banco de dados."""
    db_product = models.Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


def update_product(
    db: Session, product_id: int, product_data: schemas.ProductUpdate
) -> Optional[models.Product]:
    """Atualiza um produto existente, tratando apenas os campos fornecidos."""
    db_product = get_product(db, product_id)
    if not db_product:
        return None

    update_data: Dict[str, Any] = product_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_product, key, value)

    db.commit()
    db.refresh(db_product)
    return db_product


def delete_product(db: Session, product_id: int) -> Optional[models.Product]:
    """Deleta um produto do banco de dados."""
    db_product = get_product(db, product_id)
    if db_product:
        db.delete(db_product)
        db.commit()
    return db_product


# -------------------------------------------------------------------------- #
#                          CRUD FUNCTIONS - CART                             #
# -------------------------------------------------------------------------- #


def get_cart_by_user_id(db: Session, user_id: int) -> Optional[models.Cart]:
    """Busca o carrinho de um usuário pelo ID do usuário, pré-carregando os itens."""
    return (
        db.query(models.Cart)
        .options(joinedload(models.Cart.items).joinedload(models.CartItem.product))
        .filter(models.Cart.user_id == user_id)
        .first()
    )


def add_item_to_cart(
    db: Session, cart_id: int, item: schemas.CartItemCreate
) -> Optional[models.CartItem]:
    """
    Adiciona um item ao carrinho ou atualiza sua quantidade.
    Retorna `None` se não houver estoque suficiente.
    """
    product = get_product(db, item.product_id)
    if not product:
        return None

    db_cart_item = (
        db.query(models.CartItem)
        .filter_by(cart_id=cart_id, product_id=item.product_id)
        .first()
    )

    current_quantity = db_cart_item.quantity if db_cart_item else 0
    requested_quantity = current_quantity + item.quantity

    if product.stock < requested_quantity:
        return None

    if db_cart_item:
        db_cart_item.quantity = requested_quantity
    else:
        db_cart_item = models.CartItem(**item.model_dump(), cart_id=cart_id)
        db.add(db_cart_item)

    db.commit()
    db.refresh(db_cart_item)
    return db_cart_item


def update_cart_item_quantity(
    db: Session, cart_id: int, product_id: int, quantity: int
) -> Optional[models.CartItem]:
    """
    Atualiza a quantidade de um item específico no carrinho.
    Retorna `None` se a quantidade for inválida, o item não existir,
    ou o estoque for insuficiente.
    """
    if quantity <= 0:
        remove_cart_item(db, cart_id=cart_id, product_id=product_id)
        return None

    db_cart_item = (
        db.query(models.CartItem)
        .filter_by(cart_id=cart_id, product_id=product_id)
        .first()
    )
    if not db_cart_item or not db_cart_item.product:
        return None

    if db_cart_item.product.stock < quantity:
        return None

    db_cart_item.quantity = quantity
    db.commit()
    db.refresh(db_cart_item)

    return db_cart_item


def remove_cart_item(
    db: Session, cart_id: int, product_id: int
) -> Optional[models.CartItem]:
    """Remove um item do carrinho pelo ID do produto."""
    db_cart_item = (
        db.query(models.CartItem)
        .filter_by(cart_id=cart_id, product_id=product_id)
        .first()
    )
    if db_cart_item:
        db.delete(db_cart_item)
        db.commit()
    return db_cart_item


# -------------------------------------------------------------------------- #
#                         CRUD FUNCTIONS - ORDER                             #
# -------------------------------------------------------------------------- #


class OrderCreationError(Exception):
    """Exceção customizada para erros na criação do pedido."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


def create_order_from_cart(db: Session, user: models.User) -> models.Order:
    """
    Cria um pedido a partir do carrinho de um usuário, decrementando o estoque.
    A operação é transacional: ou tudo funciona, ou nada é alterado.
    Lança `OrderCreationError` em caso de falha (carrinho vazio, estoque).
    """
    cart = get_cart_by_user_id(db, user.id)
    if not cart or not cart.items:
        raise OrderCreationError("Carrinho vazio. Não é possível criar um pedido.")

    total_price = 0.0
    order_items_to_create = []

    try:
        for item in cart.items:
            product = (
                db.query(models.Product)
                .filter_by(id=item.product_id)
                .with_for_update()
                .first()
            )

            if not product:
                raise OrderCreationError(
                    f"Produto com ID {item.product_id} não existe mais."
                )

            if product.stock < item.quantity:
                raise OrderCreationError(
                    f"Estoque insuficiente para o produto '{product.name}'."
                )

            product.stock -= item.quantity
            total_price += product.price * item.quantity

            order_items_to_create.append(
                models.OrderItem(
                    product_id=product.id,
                    quantity=item.quantity,
                    price_at_purchase=product.price,
                )
            )

        new_order = models.Order(
            user_id=user.id, total_price=total_price, items=order_items_to_create
        )
        db.add(new_order)

        db.query(models.CartItem).filter(models.CartItem.cart_id == cart.id).delete()

        db.commit()
        db.refresh(new_order)
        return new_order

    except Exception as e:
        db.rollback()
        if isinstance(e, OrderCreationError):
            raise e
        raise OrderCreationError(
            f"Ocorreu um erro inesperado: {str(e)}", status_code=500
        )


def get_orders_by_user(db: Session, user_id: int) -> list[models.Order]:
    """Busca todos os pedidos de um usuário."""
    return (
        db.query(models.Order)
        .filter(models.Order.user_id == user_id)
        .order_by(models.Order.created_at.desc())
        .all()
    )


def get_order_by_id(db: Session, order_id: int) -> Optional[models.Order]:
    """Busca um pedido específico pelo seu ID."""
    return db.query(models.Order).filter(models.Order.id == order_id).first()


def get_all_orders(db: Session, skip: int = 0, limit: int = 100) -> list[models.Order]:
    """Busca todos os pedidos, pré-carregando os relacionamentos com 'selectinload'."""
    return (
        db.query(models.Order)
        .options(
            joinedload(models.Order.customer),
            selectinload(models.Order.items).joinedload(models.OrderItem.product),
        )
        .order_by(models.Order.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# -------------------------------------------------------------------------- #
#                      CRUD FUNCTIONS - PASSWORD RESET                       #
# -------------------------------------------------------------------------- #


def create_password_reset_token(
    db: Session, email: str, token: str
) -> models.PasswordResetToken:
    """
    Cria e armazena um novo token de recuperação de senha no banco de dados.

    Define um tempo de expiração para o token (e.g., 1 hora a partir de agora)
    e o associa ao e-mail do usuário.
    """
    expires_delta = timedelta(hours=1)
    expires_at = datetime.now(timezone.utc) + expires_delta

    db.query(models.PasswordResetToken).filter_by(email=email).update({"used": True})

    reset_token = models.PasswordResetToken(
        email=email, token=token, expires_at=expires_at
    )
    db.add(reset_token)
    db.commit()
    db.refresh(reset_token)
    return reset_token


def get_user_by_password_reset_token(db: Session, token: str) -> Optional[models.User]:
    """
    Valida um token de recuperação de senha e retorna o usuário correspondente.

    Verifica se o token existe, não foi usado e não expirou. Se for válido,
    marca o token como usado e retorna o objeto do usuário para que sua senha
    possa ser alterada.
    """
    reset_token = db.query(models.PasswordResetToken).filter_by(token=token).first()

    if not reset_token or reset_token.used:
        return None
    token_expires_at = reset_token.expires_at.replace(tzinfo=timezone.utc)

    if token_expires_at < datetime.now(timezone.utc):
        return None
    user = get_user_by_email(db, email=reset_token.email)
    if not user:
        return None

    reset_token.used = True
    db.commit()

    return user


def update_user_password(
    db: Session, user: models.User, new_password: str
) -> models.User:
    """
    Atualiza a senha de um usuário específico no banco de dados.

    Recebe o objeto do usuário e a nova senha, gera o hash e salva
    a alteração.
    """
    user.hashed_password = auth.get_password_hash(new_password)
    db.commit()
    db.refresh(user)
    return user
