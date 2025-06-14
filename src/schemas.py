"""
Define os schemas Pydantic para validação de dados da API.
"""

from pydantic import BaseModel, computed_field, ConfigDict
from typing import List, Optional
from datetime import datetime

# -------------------------------------------------------------------------- #
#                         Schemas Base Reutilizáveis                         #
# -------------------------------------------------------------------------- #


class ProductBase(BaseModel):
    """Schema base para um produto, usado em listas."""

    name: str
    price: float
    description: Optional[str] = None


class CategoryBase(BaseModel):
    """Schema base para uma categoria, contendo atributos comuns."""

    title: str
    description: Optional[str] = None


# -------------------------------------------------------------------------- #
#                         Schemas de Produto                                 #
# -------------------------------------------------------------------------- #


class ProductCreate(ProductBase):
    """Schema para a criação de um novo produto."""

    category_id: int


class ProductUpdate(ProductBase):
    """Schema para a atualização de um produto existente."""

    pass


class CategoryInProduct(CategoryBase):
    """Schema para determinar a categoria de um produto."""

    id: int
    model_config = ConfigDict(from_attributes=True)


class Product(ProductBase):
    """Schema para a leitura de um produto, incluindo seu ID e categoria."""

    id: int
    category: CategoryInProduct
    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------------------- #
#                        Schemas de Categoria                                #
# -------------------------------------------------------------------------- #


class CategoryCreate(CategoryBase):
    """Schema para a criação de uma nova categoria."""

    pass


class Category(CategoryBase):
    """Schema para a leitura de uma categoria, incluindo seus produtos."""

    id: int
    products: List[ProductBase] = []
    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------------------- #
#                             SCHEMAS DE USUÁRIO                             #
# -------------------------------------------------------------------------- #


class UserBase(BaseModel):
    """Schema base para um usuário."""

    email: str


class UserCreate(UserBase):
    """Schema para a criação de um usuário, exige uma senha."""

    password: str


class User(UserBase):
    """Schema para a leitura de um usuário, nunca inclui a senha."""

    id: int
    is_superuser: bool
    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------------------- #
#                               SCHEMAS DE TOKEN                             #
# -------------------------------------------------------------------------- #


class Token(BaseModel):
    """Schema para o token de acesso."""

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """
    Schema para os dados validados contidos dentro do token JWT.

    Como instanciamos esta classe somente após validar o payload, o campo
    'email' pode ser definido como obrigatório.
    """

    email: str


# -------------------------------------------------------------------------- #
#                           CART SCHEMAS                                     #
# -------------------------------------------------------------------------- #


class ProductInCart(ProductBase):
    """Schema para o produto dentro de um item de carrinho."""

    id: int
    model_config = ConfigDict(from_attributes=True)


class CartItemBase(BaseModel):
    """Schema base para um item de carrinho."""

    quantity: int


class CartItemCreate(BaseModel):
    """Schema para adicionar um item ao carrinho."""

    product_id: int
    quantity: int = 1


class CartItemUpdate(BaseModel):
    """Schema para atualizar a quantidade de um item no carrinho."""

    quantity: int


class CartItem(CartItemBase):
    """Schema para exibir um item completo no carrinho."""

    id: int
    product: ProductInCart
    model_config = ConfigDict(from_attributes=True)


class Cart(BaseModel):
    """Schema principal para exibir o carrinho de um usuário."""

    id: int
    items: List[CartItem] = []

    @computed_field
    @property
    def total_price(self) -> float:
        """Calcula o preço total do carrinho."""
        return sum(item.product.price * item.quantity for item in self.items)

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------------------- #
#                              ORDER SCHEMAS                                 #
# -------------------------------------------------------------------------- #


class OrderItem(BaseModel):
    """Schema para exibir um item dentro de um pedido."""

    quantity: int
    price_at_purchase: float
    product: Optional[ProductInCart]

    model_config = ConfigDict(from_attributes=True)


class Order(BaseModel):
    """Schema principal para exibir um pedido."""

    id: int
    created_at: datetime
    total_price: float
    items: List[OrderItem]

    model_config = ConfigDict(from_attributes=True)
