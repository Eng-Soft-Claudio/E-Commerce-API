"""
Define os schemas Pydantic para validação de dados da API.
"""
from pydantic import BaseModel
from typing import List, Optional 

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

class Product(ProductBase):
    """Schema para a leitura de um produto, incluindo seu ID e categoria."""
    id: int
    category: CategoryBase 

    class Config:
        from_attributes = True

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

    class Config:
        from_attributes = True