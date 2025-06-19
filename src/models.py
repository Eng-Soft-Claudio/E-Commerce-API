"""
Define os modelos do SQLAlchemy ORM.
...
"""

from sqlalchemy import Integer, String, Float, ForeignKey, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional

from .database import Base

# -------------------------------------------------------------------------- #
#                                ORM MODELS                                  #
# -------------------------------------------------------------------------- #


class Category(Base):
    """
    Modelo SQLAlchemy representando a tabela 'categories' no banco de dados.
    """

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    products: Mapped[List["Product"]] = relationship(
        back_populates="category", cascade="all, delete-orphan"
    )


class Product(Base):
    """
    Modelo SQLAlchemy representando a tabela 'products' no banco de dados.
    """

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    image_url: Mapped[Optional[str]]
    price: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str | None] = mapped_column(String)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    category: Mapped["Category"] = relationship(back_populates="products")


class User(Base):
    """
    Modelo SQLAlchemy representando a tabela 'users' no banco de dados.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    cart: Mapped["Cart"] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )
    orders: Mapped[List["Order"]] = relationship(back_populates="customer")


class Cart(Base):
    """Modelo para o carrinho de compras, ligado a um usuário."""

    __tablename__ = "carts"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    owner: Mapped["User"] = relationship(back_populates="cart")
    items: Mapped[List["CartItem"]] = relationship(
        back_populates="cart", cascade="all, delete-orphan"
    )


class CartItem(Base):
    """Modelo para um item dentro de um carrinho de compras."""

    __tablename__ = "cart_items"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    cart_id: Mapped[int] = mapped_column(ForeignKey("carts.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    cart: Mapped["Cart"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship()


class Order(Base):
    """Modelo para um pedido, representando uma compra finalizada."""

    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    total_price: Mapped[float] = mapped_column(Float)
    customer: Mapped["User"] = relationship(back_populates="orders")
    items: Mapped[List["OrderItem"]] = relationship(cascade="all, delete-orphan")
    status: Mapped[str] = mapped_column(String, default="pending_payment")
    payment_intent_id: Mapped[Optional[str]] = mapped_column(
        String, unique=True, index=True
    )


class OrderItem(Base):
    """Modelo para um item individual dentro de um pedido."""

    __tablename__ = "order_items"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer)
    price_at_purchase: Mapped[float] = mapped_column(Float)
    product: Mapped[Optional["Product"]] = relationship()
