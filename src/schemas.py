"""
Define os schemas Pydantic para validação de dados da API.

Este módulo estabelece os "contratos" de dados para a aplicação, utilizando
uma biblioteca externa robusta para validação de documentos brasileiros,
como o CPF, para garantir maior confiabilidade e manutenibilidade.
"""

# -------------------------------------------------------------------------- #
#                             IMPORTS NECESSÁRIOS                            #
# -------------------------------------------------------------------------- #
from datetime import datetime
from typing import List, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    model_validator,
)
from validate_docbr import CPF

# -------------------------------------------------------------------------- #
#                        SCHEMAS DE PRODUTO E CATEGORIA                      #
# -------------------------------------------------------------------------- #


class ProductBase(BaseModel):
    """Schema base com os campos essenciais de um produto."""

    name: str
    image_url: Optional[str] = None
    price: float
    description: Optional[str] = None


class CategoryBase(BaseModel):
    """Schema base com os campos essenciais de uma categoria."""

    id: int
    title: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class Category(CategoryBase):
    """Schema de leitura para uma categoria, incluindo a lista de seus produtos."""

    products: List[ProductBase] = []


class CategoryCreate(BaseModel):
    """Schema para a criação de uma nova categoria."""

    title: str
    description: Optional[str] = None


class ProductCreate(ProductBase):
    """Schema para a criação de um novo produto."""

    category_id: int


class ProductUpdate(ProductBase):
    """Schema para a atualização de um produto existente."""

    pass


class Product(ProductBase):
    """Schema de leitura para um produto, incluindo os dados de sua categoria."""

    id: int
    category: CategoryBase
    model_config = ConfigDict(from_attributes=True)


Category.model_rebuild()

# -------------------------------------------------------------------------- #
#                         SCHEMAS DE CARRINHO DE COMPRAS                     #
# -------------------------------------------------------------------------- #


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
    """Schema de leitura para um item de carrinho."""

    id: int
    product: Product
    model_config = ConfigDict(from_attributes=True)


class Cart(BaseModel):
    """Schema principal de leitura para o carrinho de um usuário."""

    id: int
    items: List[CartItem] = []

    @computed_field
    @property
    def total_price(self) -> float:
        """Calcula o preço total do carrinho."""
        return sum(
            item.product.price * item.quantity for item in self.items if item.product
        )

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------------------- #
#                      SCHEMAS DE PEDIDO E ITENS DE PEDIDO                   #
# -------------------------------------------------------------------------- #


class OrderItem(BaseModel):
    """Schema de leitura para um item individual dentro de um pedido."""

    quantity: int
    price_at_purchase: float
    product: Optional[Product]
    model_config = ConfigDict(from_attributes=True)


class OrderBase(BaseModel):
    """Schema base com os campos essenciais de um pedido."""

    id: int
    created_at: datetime
    total_price: float
    status: str
    items: List[OrderItem] = []


class Order(OrderBase):
    """Schema principal de leitura para um pedido de um usuário."""

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------------------- #
#                           SCHEMAS DE USUÁRIO E TOKEN                       #
# -------------------------------------------------------------------------- #


class UserBase(BaseModel):
    """
    Schema base para um usuário, com todos os seus dados.
    """

    email: str
    full_name: str
    cpf: str
    phone: str
    address_street: str
    address_number: str
    address_complement: Optional[str] = None
    address_zip: str
    address_city: str
    address_state: str

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def validate_and_format_cpf(cls, data):
        """
        Valida o campo CPF utilizando a biblioteca validate_docbr.
        Este validador funciona tanto para criação (dicts) quanto para leitura (objetos).
        """
        cpf_value = None
        if isinstance(data, dict):
            cpf_value = data.get("cpf")
        elif hasattr(data, "cpf"):
            cpf_value = data.cpf

        if cpf_value:
            cpf_validator = CPF()
            if not cpf_validator.validate(cpf_value):
                raise ValueError("CPF inválido.")
            if isinstance(data, dict):
                data["cpf"] = cpf_validator.mask(cpf_value)
            else:
                setattr(data, "cpf", cpf_validator.mask(cpf_value))

        return data


class UserCreate(UserBase):
    """Schema para a criação de um usuário."""

    full_name: str = Field(..., min_length=3)
    password: str = Field(..., min_length=6)


class User(UserBase):
    """Schema de leitura para um usuário."""

    id: int
    is_superuser: bool
    orders: List[Order] = []


class AdminOrder(Order):
    """Schema de leitura para um pedido na visão do admin."""

    customer: UserBase


class Token(BaseModel):
    """Schema para o token de acesso JWT."""

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Schema para os dados decodificados de dentro de um token JWT."""

    email: Optional[str] = None
