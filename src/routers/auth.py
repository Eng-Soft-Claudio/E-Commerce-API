"""
Módulo de Roteamento para Autenticação e Gerenciamento de Usuários.

Define os endpoints públicos para registro de novos usuários e para
obtenção de tokens de acesso (login).
"""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .. import auth, crud, schemas, models
from ..database import get_db

# -------------------------------------------------------------------------- #
#                                ROUTER SETUP                                #
# -------------------------------------------------------------------------- #

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# -------------------------------------------------------------------------- #
#                        AUTHENTICATION API ENDPOINTS                        #
# -------------------------------------------------------------------------- #


@router.post("/token", response_model=schemas.Token)
async def login_for_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    Endpoint de login para obter um token de acesso.

    Este endpoint segue o fluxo do OAuth2 'Password Flow'. Ele recebe as
    credenciais do usuário (email como 'username' e a senha) em um formulário,
    verifica se são válidas e, em caso afirmativo, retorna um token JWT.

    Args:
        db (Session): A sessão do banco de dados.
        form_data (OAuth2PasswordRequestForm): Formulário com 'username' e 'password'.

    Raises:
        HTTPException(401): Se as credenciais forem inválidas.

    Returns:
        schemas.Token: O token de acesso JWT e o tipo de token ('bearer').
    """
    user = crud.get_user_by_email(db, email=form_data.username)
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/users/", response_model=schemas.User, status_code=201)
def create_user_endpoint(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Cria um novo usuário (registro público).

    Verifica se o email já existe no sistema antes de criar um novo
    registro de usuário.

    Args:
        user (schemas.UserCreate): Os dados do novo usuário.
        db (Session): A sessão do banco de dados.

    Raises:
        HTTPException(400): Se o email já estiver registrado.

    Returns:
        schemas.User: O usuário recém-criado (sem a senha).
    """
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


# -------------------------------------------------------------------------- #
#                             USER PROFILE ENDPOINT                          #
# -------------------------------------------------------------------------- #


@router.get("/users/me/", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    """
    Retorna os dados do usuário atualmente logado.

    Utiliza a dependência get_current_user para identificar e retornar
    as informações do usuário que fez a requisição.
    """
    return current_user
