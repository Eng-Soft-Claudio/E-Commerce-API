"""
Módulo de Roteamento para Gerenciamento de Usuários (Admin).

Define os endpoints que permitem a um administrador visualizar e gerenciar
os usuários da plataforma.
"""

# -------------------------------------------------------------------------- #
#                             IMPORTS NECESSÁRIOS                            #
# -------------------------------------------------------------------------- #
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import crud, schemas, auth
from ..database import get_db

# -------------------------------------------------------------------------- #
#                                ROUTER SETUP                                #
# -------------------------------------------------------------------------- #
router = APIRouter(
    prefix="/admin/users",
    tags=["Admin: Users"],
    dependencies=[Depends(auth.get_current_superuser)],
)


# -------------------------------------------------------------------------- #
#                        ENDPOINTS DE GERENCIAMENTO DE USUÁRIOS              #
# -------------------------------------------------------------------------- #
@router.get("/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    [Admin] Retorna uma lista de todos os usuários (clientes) do sistema.

    Este endpoint é protegido e requer privilégios de superusuário.
    Ele utiliza paginação para lidar com um grande número de usuários.
    """
    users = crud.get_all_users(db, skip=skip, limit=limit)
    return users
