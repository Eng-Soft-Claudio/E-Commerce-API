"""
Módulo CRUD (Create, Read, Update, Delete) para os modelos.

Este arquivo abstrai a lógica de acesso ao banco de dados, separando-a
da lógica dos endpoints da API. Cada função aqui interage diretamente com
a sessão do banco de dados para manipular os dados.
"""

from typing import Optional
from sqlalchemy.orm import Session
from . import models, schemas, auth

# -------------------------------------------------------------------------- #
#                         CRUD FUNCTIONS - CATEGORY                          #
# -------------------------------------------------------------------------- #


def get_category(db: Session, category_id: int):
    """Busca uma única categoria pelo seu ID."""
    return db.query(models.Category).filter(models.Category.id == category_id).first()


def get_categories(db: Session, skip: int = 0, limit: int = 100):
    """Busca uma lista de categorias com paginação."""
    return db.query(models.Category).offset(skip).limit(limit).all()


def create_category(db: Session, category: schemas.CategoryCreate):
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
):
    """Atualiza uma categoria existente no banco de dados."""
    db_category = get_category(db, category_id)
    if db_category:
        db_category.title = category_data.title
        db_category.description = category_data.description
        db.commit()
        db.refresh(db_category)
    return db_category


def delete_category(db: Session, category_id: int):
    """Deleta uma categoria do banco de dados."""
    db_category = get_category(db, category_id)
    if db_category:
        db.delete(db_category)
        db.commit()
    return db_category


# -------------------------------------------------------------------------- #
#                          CRUD FUNCTIONS - USERS                            #
# -------------------------------------------------------------------------- #


def get_user_by_email(db: Session, email: str):
    """Busca um usuário pelo seu email."""
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, user: schemas.UserCreate, is_superuser: bool = False):
    """
    Cria um novo usuário, com a senha hasheada.
    """
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        email=user.email, hashed_password=hashed_password, is_superuser=is_superuser
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    if not db_user.is_superuser:
        db_cart = models.Cart(owner=db_user)
        db.add(db_cart)
        db.commit()

    return db_user


# -------------------------------------------------------------------------- #
#                         CRUD FUNCTIONS - PRODUCTS                          #
# -------------------------------------------------------------------------- #
def get_product(db: Session, product_id: int):
    """Busca um único produto pelo seu ID."""
    return db.query(models.Product).filter(models.Product.id == product_id).first()


def get_products(db: Session, skip: int = 0, limit: int = 100):
    """Busca uma lista de produtos com paginação."""
    return db.query(models.Product).offset(skip).limit(limit).all()


def create_product(db: Session, product: schemas.ProductCreate):
    """Cria um novo produto no banco de dados associado a uma categoria."""
    db_product = models.Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


def update_product(db: Session, product_id: int, product_data: schemas.ProductUpdate):
    """Atualiza um produto existente no banco de dados."""
    db_product = get_product(db, product_id)
    if db_product:
        db_product.name = product_data.name
        db_product.price = product_data.price
        db_product.description = product_data.description
        db.commit()
        db.refresh(db_product)
    return db_product


def delete_product(db: Session, product_id: int):
    """Deleta um produto do banco de dados."""
    db_product = get_product(db, product_id)
    if db_product:
        db.delete(db_product)
        db.commit()
    return db_product


# -------------------------------------------------------------------------- #
#                          CRUD FUNCTIONS - CART                             #
# -------------------------------------------------------------------------- #
def get_cart_by_user_id(db: Session, user_id: int):
    """Busca o carrinho de um usuário pelo ID do usuário."""
    return db.query(models.Cart).filter(models.Cart.user_id == user_id).first()


def add_item_to_cart(db: Session, cart_id: int, item: schemas.CartItemCreate):
    """Adiciona ou atualiza um item no carrinho."""
    db_cart_item = (
        db.query(models.CartItem)
        .filter_by(cart_id=cart_id, product_id=item.product_id)
        .first()
    )

    if db_cart_item:
        db_cart_item.quantity += item.quantity
    else:
        db_cart_item = models.CartItem(**item.model_dump(), cart_id=cart_id)
        db.add(db_cart_item)

    db.commit()
    db.refresh(db_cart_item)
    return db_cart_item


def remove_cart_item(db: Session, cart_id: int, product_id: int):
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


def create_order_from_cart(db: Session, user: models.User) -> Optional[models.Order]:
    """Cria um pedido a partir do carrinho de um usuário e limpa o carrinho."""
    cart = user.cart
    if not cart or not cart.items:
        return None

    total_price = 0
    order_items_data = []
    for cart_item in cart.items:
        price = cart_item.product.price * cart_item.quantity
        total_price += price
        order_items_data.append(
            models.OrderItem(
                product_id=cart_item.product_id,
                quantity=cart_item.quantity,
                price_at_purchase=cart_item.product.price,
            )
        )

    new_order = models.Order(
        user_id=user.id, total_price=total_price, items=order_items_data
    )
    db.add(new_order)

    db.query(models.CartItem).filter_by(cart_id=cart.id).delete()

    db.commit()
    db.refresh(new_order)
    return new_order


def get_orders_by_user(db: Session, user_id: int):
    """Busca todos os pedidos de um usuário."""
    return db.query(models.Order).filter(models.Order.user_id == user_id).all()


def get_order_by_id(db: Session, order_id: int):
    """Busca um pedido específico pelo seu ID."""
    return db.query(models.Order).filter(models.Order.id == order_id).first()
