"""
Arquivo de Configuração Central do Pytest (Conftest) - Versão Definitiva.

Esta versão implementa a abordagem robusta de criar uma instância de aplicação
isolada para cada teste, garantindo 100% de controle sobre o ambiente.
"""

import pytest
from typing import Generator, Dict
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import Session, sessionmaker

from src.database import Base, get_db
from src import models  # noqa: F401
from src import crud
from src.schemas import UserCreate
from src.auth import create_access_token
from src.routers import auth, cart, categories, orders, products

# -------------------------------------------------------------------------- #
#                       SETUP DO BANCO DE DADOS DE TESTE                     #
# -------------------------------------------------------------------------- #

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# -------------------------------------------------------------------------- #
#                             FIXTURES PRINCIPAIS                            #
# -------------------------------------------------------------------------- #


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """
    Fixture que gerencia o ciclo de vida completo do banco de dados para um único teste.
    """
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """
    Fixture principal que monta uma aplicação FastAPI de teste completa.
    """
    test_app = FastAPI()

    def override_get_db():
        yield db_session

    test_app.dependency_overrides[get_db] = override_get_db

    test_app.include_router(auth.router)
    test_app.include_router(cart.router)
    test_app.include_router(orders.router)
    test_app.include_router(categories.router)
    test_app.include_router(products.router)

    with TestClient(test_app) as test_client:
        yield test_client


# -------------------------------------------------------------------------- #
#                        FIXTURES DE USUÁRIO E AUTENTICAÇÃO                  #
# -------------------------------------------------------------------------- #


@pytest.fixture(scope="function")
def test_superuser(db_session: Session) -> Dict:
    """
    Fixture que cria um superuser de teste DIRETAMENTE no banco para garantir
    consistência, contornando a lógica de 'primeiro usuário' da API.
    """
    user_schema = UserCreate(email="admin@test.com", password="password123")
    user_model = crud.create_user(db=db_session, user=user_schema, is_superuser=True)
    return {
        "id": user_model.id,
        "email": user_model.email,
        "is_superuser": user_model.is_superuser,
    }


@pytest.fixture(scope="function")
def test_user(client: TestClient) -> Dict:
    """Cria um usuário comum de teste via API."""
    user_data = {"email": "user@test.com", "password": "password123"}
    response = client.post("/auth/users/", json=user_data)
    assert response.status_code == 201
    return response.json()


@pytest.fixture(scope="function")
def superuser_token_headers(test_superuser: Dict) -> Dict[str, str]:
    """Gera o cabeçalho de autenticação para o superuser."""
    token = create_access_token(data={"sub": test_superuser["email"]})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def user_token_headers(test_user: Dict) -> Dict[str, str]:
    """Gera o cabeçalho de autenticação para o usuário comum."""
    token = create_access_token(data={"sub": test_user["email"]})
    return {"Authorization": f"Bearer {token}"}
