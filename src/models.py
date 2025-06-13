"""
Define os modelos do SQLAlchemy ORM.
...
"""
from sqlalchemy import String, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List

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
    price: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str | None] = mapped_column(String)

    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))

    category: Mapped["Category"] = relationship(back_populates="products")