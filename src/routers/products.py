"""
Módulo de Roteamento para o recurso 'Produto'.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, schemas, auth
from ..database import get_db

# -------------------------------------------------------------------------- #
#                           ROUTER SETUP                                     #
# -------------------------------------------------------------------------- #

router = APIRouter(
    prefix="/products",
    tags=["Products"],
    responses={404: {"description": "Not found"}},
)

# -------------------------------------------------------------------------- #
#                         PRODUCT API ENDPOINTS                              #
# -------------------------------------------------------------------------- #


# --- Operações de Escrita (PROTEGIDAS PARA SUPERUSER) ---
@router.post(
    "/",
    response_model=schemas.Product,
    status_code=201,
    dependencies=[Depends(auth.get_current_superuser)],
)
def create_product_endpoint(
    product: schemas.ProductCreate, db: Session = Depends(get_db)
):
    """Cria um novo produto. Requer privilégios de administrador."""
    db_category = crud.get_category(db, category_id=product.category_id)
    if db_category is None:
        raise HTTPException(
            status_code=404, detail="Category not found to link product"
        )
    return crud.create_product(db=db, product=product)


@router.put(
    "/{product_id}",
    response_model=schemas.Product,
    dependencies=[Depends(auth.get_current_superuser)],
)
def update_product_endpoint(
    product_id: int, product: schemas.ProductUpdate, db: Session = Depends(get_db)
):
    """Atualiza um produto. Requer privilégios de administrador."""
    db_product = crud.update_product(db, product_id=product_id, product_data=product)
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product


@router.delete(
    "/{product_id}",
    response_model=dict,
    dependencies=[Depends(auth.get_current_superuser)],
)
def delete_product_endpoint(product_id: int, db: Session = Depends(get_db)):
    """Deleta um produto. Requer privilégias de administrador."""
    db_product = crud.delete_product(db, product_id=product_id)
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted successfully"}


# --- Operações de Leitura (PÚBLICAS) ---
@router.get("/", response_model=list[schemas.Product])
def read_products_endpoint(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    """Lista todos os produtos. Acesso público."""
    products = crud.get_products(db, skip=skip, limit=limit)
    return products


@router.get("/{product_id}", response_model=schemas.Product)
def read_product_endpoint(product_id: int, db: Session = Depends(get_db)):
    """Busca um único produto pelo ID. Acesso público."""
    db_product = crud.get_product(db, product_id=product_id)
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product
