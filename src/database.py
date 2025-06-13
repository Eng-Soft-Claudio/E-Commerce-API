"""
Módulo para configurar a conexão do banco de dados para a aplicação.

Este arquivo define a URL do banco de dados, cria o motor (engine) de conexão
do SQLAlchemy, e fornece uma fábrica de sessões (SessionLocal) junto com uma
função de dependência (get_db) para ser usada nos endpoints da API.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# -------------------------------------------------------------------------- #
#                               DATABASE SETUP                               #
# -------------------------------------------------------------------------- #

SQLALCHEMY_DATABASE_URL = "sqlite:///./minha_api.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# -------------------------------------------------------------------------- #
#                             DATABASE DEPENDENCY                            #
# -------------------------------------------------------------------------- #

def get_db():
    """
    Função de dependência do FastAPI para obter uma sessão de banco de dados.

    Cria uma nova sessão (SessionLocal) para cada requisição e garante
    que ela seja sempre fechada após o término da requisição, mesmo que
    ocorra um erro, usando um bloco try...finally.

    Yields:
        db (Session): O objeto de sessão do SQLAlchemy.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()