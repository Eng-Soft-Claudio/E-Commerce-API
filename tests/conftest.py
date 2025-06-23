"""
Arquivo de Configuração Central do Pytest (Conftest)

Esta versão implementa a abordagem robusta de criar uma instância de aplicação
isolada para cada teste, garantindo 100% de controle sobre o ambiente.
As fixtures de usuário foram refatoradas para separar claramente a definição
dos "payloads" (dados de teste) da criação dos "objetos" (usuários no BD).
Isso corrige erros de validação e torna os testes mais claros e robustos.
"""

import pytest
from typing import Generator, Dict, Any
from fastapi import FastAPI  # noqa: F401
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import Session, sessionmaker

from src.database import Base, get_db
from src import models, crud
from src.schemas import UserCreate
from src.auth import create_access_token
from src.main import app as main_app

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
    """Cria e destrói um banco de dados em memória para cada teste."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Fixture principal que monta a aplicação FastAPI completa com override de DB."""

    def override_get_db():
        """Substitui a dependência get_db para usar o banco de dados de teste."""
        try:
            yield db_session
        finally:
            db_session.close()

    main_app.dependency_overrides[get_db] = override_get_db

    with TestClient(main_app) as test_client:
        yield test_client


# -------------------------------------------------------------------------- #
#                 FIXTURES DE DADOS (PAYLOADS) PARA USUÁRIOS                 #
# -------------------------------------------------------------------------- #


@pytest.fixture(scope="session")
def test_superuser_payload() -> Dict[str, Any]:
    """Retorna um dicionário (payload) com dados para criar um superuser."""
    return {
        "email": "admin@test.com",
        "password": "password123",
        "full_name": "Admin User",
        "cpf": "08913845024",
        "phone": "(11) 99999-8888",
        "address_street": "Admin Street",
        "address_number": "100",
        "address_complement": "Sala 1",
        "address_zip": "12345-001",
        "address_city": "Adminville",
        "address_state": "AD",
    }


@pytest.fixture(scope="session")
def test_user_payload() -> Dict[str, Any]:
    """Retorna um dicionário (payload) com dados para criar um usuário comum."""
    return {
        "email": "user@test.com",
        "password": "password123",
        "full_name": "Common User",
        "cpf": "25409257073",
        "phone": "(22) 88888-7777",
        "address_street": "User Avenue",
        "address_number": "202",
        "address_complement": None,
        "address_zip": "54321-002",
        "address_city": "Userville",
        "address_state": "US",
    }


# -------------------------------------------------------------------------- #
#               FIXTURES DE CRIAÇÃO DE USUÁRIOS E AUTENTICAÇÃO               #
# -------------------------------------------------------------------------- #


@pytest.fixture(scope="function")
def test_superuser(db_session: Session, test_superuser_payload: Dict) -> models.User:
    """Cria um superuser de teste diretamente no banco de dados e retorna o objeto."""
    user_schema = UserCreate(**test_superuser_payload)
    user_model = crud.create_user(db=db_session, user=user_schema, is_superuser=True)
    return user_model


@pytest.fixture(scope="function")
def test_user(client: TestClient, test_user_payload: Dict) -> Dict:
    """Cria um usuário comum via API e retorna o JSON da resposta."""
    response = client.post("/auth/users/", json=test_user_payload)
    assert response.status_code == 201, (
        f"A criação do usuário de teste via API falhou: {response.text}"
    )
    return response.json()


@pytest.fixture(scope="function")
def superuser_token_headers(test_superuser: models.User) -> Dict[str, str]:
    """Gera o cabeçalho de autenticação para o superuser."""
    token = create_access_token(data={"sub": test_superuser.email})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def user_token_headers(test_user: Dict) -> Dict[str, str]:
    """Gera o cabeçalho de autenticação para o usuário comum."""
    token = create_access_token(data={"sub": test_user["email"]})
    return {"Authorization": f"Bearer {token}"}
