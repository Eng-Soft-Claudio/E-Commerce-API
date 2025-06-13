"""
Módulo CRUD (Create, Read, Update, Delete) para todos os modelos.

Este arquivo abstrai a lógica de acesso ao banco de dados, separando-a
da lógica dos endpoints da API. Cada função aqui interage diretamente com
a sessão do banco de dados para manipular os dados dos modelos.
"""
from sqlalchemy.orm import Session
from . import models, schemas

# -------------------------------------------------------------------------- #
#                              CRUD FUNCTIONS                              #
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
    """
    Atualiza um produto existente no banco de dados.

    Não permite a alteração do 'category_id'.
    """
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
