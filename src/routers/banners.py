"""
Módulo de Roteamento para o recurso 'Banner'.

Define todos os endpoints da API relacionados aos banners da página inicial.
As operações de escrita (criar, atualizar, deletar) são protegidas e exigem
privilégios de administrador, enquanto a leitura dos banners ativos é
pública para que o frontend possa exibi-los.
"""

# -------------------------------------------------------------------------- #
#                             IMPORTS NECESSÁRIOS                            #
# -------------------------------------------------------------------------- #

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import auth, crud, schemas
from ..database import get_db

# -------------------------------------------------------------------------- #
#                                ROUTER SETUP                                #
# -------------------------------------------------------------------------- #

router = APIRouter(prefix="/banners", tags=["Banners"])

# -------------------------------------------------------------------------- #
#                        ENDPOINTS PÚBLICOS DE BANNER                        #
# -------------------------------------------------------------------------- #


@router.get("/active/", response_model=List[schemas.Banner])
def read_active_banners(db: Session = Depends(get_db)):
    """[Público] Lista todos os banners ativos para exibição no frontend."""
    return crud.get_active_banners(db)


# -------------------------------------------------------------------------- #
#                      ENDPOINTS DE GERENCIAMENTO (ADMIN)                    #
# -------------------------------------------------------------------------- #


@router.get(
    "/",
    response_model=List[schemas.Banner],
    dependencies=[Depends(auth.get_current_superuser)],
)
def read_all_banners_admin(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    """[Admin] Lista todos os banners (ativos e inativos) para o painel de gerenciamento."""
    banners = crud.get_all_banners(db, skip=skip, limit=limit)
    return banners


@router.post(
    "/",
    response_model=schemas.Banner,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(auth.get_current_superuser)],
)
def create_banner_endpoint(
    banner: schemas.BannerCreate, db: Session = Depends(get_db)
):
    """[Admin] Cria um novo banner."""
    return crud.create_banner(db=db, banner=banner)


@router.put(
    "/{banner_id}",
    response_model=schemas.Banner,
    dependencies=[Depends(auth.get_current_superuser)],
)
def update_banner_endpoint(
    banner_id: int, banner: schemas.BannerUpdate, db: Session = Depends(get_db)
):
    """[Admin] Atualiza um banner existente."""
    db_banner = crud.update_banner(db, banner_id=banner_id, banner_data=banner)
    if not db_banner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Banner não encontrado."
        )
    return db_banner


@router.delete(
    "/{banner_id}",
    response_model=dict,
    dependencies=[Depends(auth.get_current_superuser)],
)
def delete_banner_endpoint(banner_id: int, db: Session = Depends(get_db)):
    """[Admin] Deleta um banner do sistema."""
    db_banner = crud.delete_banner(db, banner_id=banner_id)
    if not db_banner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Banner não encontrado."
        )
    return {"message": "Banner deletado com sucesso."}