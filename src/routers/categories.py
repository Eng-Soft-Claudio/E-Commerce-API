"""
Módulo de Roteamento para o recurso 'Categoria'.

Define todos os endpoints da API relacionados a categorias usando um APIRouter,
que será incluído na aplicação principal FastAPI.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db

# -------------------------------------------------------------------------- #
#                           ROUTER SETUP                                     #
# -------------------------------------------------------------------------- #

router = APIRouter(
    prefix="/categories",
    tags=["Categories"],
    responses={404: {"description": "Not found"}},
)

# -------------------------------------------------------------------------- #
#                         CATEGORY API ENDPOINTS                             #
# -------------------------------------------------------------------------- #

@router.post("/", response_model=schemas.Category, status_code=201)
def create_category_endpoint(
    category: schemas.CategoryCreate, db: Session = Depends(get_db)
):
    """Cria uma nova categoria."""
    return crud.create_category(db=db, category=category)


@router.get("/", response_model=list[schemas.Category])
def read_categories_endpoint(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    """Lista todas as categorias com paginação."""
    categories = crud.get_categories(db, skip=skip, limit=limit)
    return categories


@router.get("/{category_id}", response_model=schemas.Category)
def read_category_endpoint(category_id: int, db: Session = Depends(get_db)):
    """Busca uma única categoria pelo ID."""
    db_category = crud.get_category(db, category_id=category_id)
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return db_category


@router.put("/{category_id}", response_model=schemas.Category)
def update_category_endpoint(
    category_id: int, category: schemas.CategoryCreate, db: Session = Depends(get_db)
):
    """Atualiza uma categoria existente."""
    db_category = crud.update_category(
        db, category_id=category_id, category_data=category
    )
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return db_category


@router.delete("/{category_id}", response_model=dict)
def delete_category_endpoint(category_id: int, db: Session = Depends(get_db)):
    """Deleta uma categoria."""
    db_category = crud.delete_category(db, category_id=category_id)
    if db_category is None:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category deleted successfully"}