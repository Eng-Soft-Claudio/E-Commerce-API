"""
Define os schemas Pydantic para validação de dados da API.

Este módulo estabelece os "contratos" de dados para a aplicação. Todos os
schemas de criação (ex: UserCreate, ProductCreate) definem os dados de
entrada obrigatórios, enquanto os schemas de leitura (ex: User, Product)
definem a estrutura dos dados de saída. A biblioteca 'validate_docbr' é
utilizada para garantir a validade de documentos como o CPF.
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
    field_validator,
)
from validate_docbr import CPF

# -------------------------------------------------------------------------- #
#                        SCHEMAS DE PRODUTO E CATEGORIA                      #
# -------------------------------------------------------------------------- #


class ProductBase(BaseModel):
    """Schema base com os campos essenciais de um produto."""

    sku: str
    name: str
    image_url: Optional[str] = None
    price: float
    description: Optional[str] = None


class ProductCreate(ProductBase):
    """Schema para a criação de um novo produto."""

    category_id: int
    stock: int = Field(0, ge=0)


class ProductUpdate(BaseModel):
    """
    Schema para a atualização de um produto existente.
    Todos os campos são opcionais para permitir atualizações parciais.
    """

    sku: Optional[str] = None
    name: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    stock: Optional[int] = None
    category_id: Optional[int] = None
    image_url: Optional[str] = None


class CategoryCreate(BaseModel):
    """Schema para a criação de uma nova categoria."""

    title: str
    description: Optional[str] = None


class CategoryBase(BaseModel):
    """Schema base com os campos essenciais de uma categoria."""

    id: int
    title: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class Product(ProductBase):
    """Schema de leitura para um produto, incluindo os dados de sua categoria."""

    id: int
    stock: int
    category: CategoryBase
    model_config = ConfigDict(from_attributes=True)


class Category(CategoryBase):
    """Schema de leitura para uma categoria, incluindo a lista de seus produtos."""

    products: List[Product] = []


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
    quantity: int = Field(1, gt=0)


class CartItemUpdate(BaseModel):
    """
    Schema para atualizar a quantidade de um item no carrinho.
    Permite quantidade >= 0 para tratar a remoção na lógica de negócio.
    """

    quantity: int = Field(ge=0)


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
        """Calcula o preço total do carrinho, ignorando produtos removidos."""
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
    """Schema base com os dados de perfil de um usuário."""

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

    @field_validator("cpf")
    @classmethod
    def validate_cpf(cls, v: str) -> str:
        """
        Valida o campo CPF usando a biblioteca `validate_docbr`.
        Retorna o valor original se for válido, ou levanta um `ValueError`.
        """
        cpf_validator = CPF()
        if not cpf_validator.validate(v):
            raise ValueError("CPF fornecido é inválido.")
        return v


class UserCreate(UserBase):
    """Schema para a criação de um usuário, exigindo todos os dados e senha."""

    password: str = Field(..., min_length=6)


class User(UserBase):
    """Schema de leitura para um usuário, incluindo ID e status de superuser."""

    id: int
    is_superuser: bool
    orders: List[Order] = []

    model_config = ConfigDict(from_attributes=True)


class AdminOrder(Order):
    """Schema de leitura para um pedido na visão do admin, incluindo o cliente."""

    customer: UserBase


class Token(BaseModel):
    """Schema para o token de acesso JWT."""

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Schema para os dados decodificados de dentro de um token JWT."""

    email: Optional[str] = None

class ForgotPasswordRequest(BaseModel):
    """Schema para a solicitação de recuperação de senha."""
    email: str

class ResetPasswordRequest(BaseModel):
    """Schema para a redefinição de senha com o token."""
    token: str
    new_password: str = Field(..., min_length=6)
