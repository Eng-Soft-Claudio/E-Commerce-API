"""
Módulo de Banco de Dados com Inicialização Segura.

Esta implementação inclui uma lógica de criação de tabelas diretamente na
dependência get_db, usando uma verificação de estado para garantir que a
criação ocorra apenas uma vez. Esta abordagem é robusta para o ambiente de
desenvolvimento com Uvicorn e SQLite. A saída de status é gerenciada
pelo módulo de logging.
"""

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.engine import Engine

# -------------------------------------------------------------------------- #
#                       CONFIGURAÇÃO INICIAL E LOGGING                       #
# -------------------------------------------------------------------------- #
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# -------------------------------------------------------------------------- #
#                         CONFIGURAÇÃO DO BANCO DE DADOS                     #
# -------------------------------------------------------------------------- #

SQLALCHEMY_DATABASE_URL = "sqlite:///./minha_api.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# -------------------------------------------------------------------------- #
#                CRIAÇÃO DE TABELAS E DEPENDÊNCIA GET_DB                     #
# -------------------------------------------------------------------------- #

_database_initialized = False


def init_db(eng: Engine):
    """
    Verifica e cria todas as tabelas no banco de dados, se ainda não tiver
    sido inicializado nesta sessão.
    """
    global _database_initialized
    if not _database_initialized:
        log.info("Banco de dados não inicializado. Criando tabelas...")
        try:
            from src import models  # noqa: F401

            Base.metadata.create_all(bind=eng)
            _database_initialized = True
            log.info("Tabelas criadas com sucesso.")
        except Exception as e:# pragma: no cover
            log.error(
                "Falha catastrófica ao criar tabelas do banco de dados.", exc_info=True
            )
            raise e


def get_db():
    """
    Dependência do FastAPI que cria e gerencia uma sessão de DB por requisição.

    Também garante que a função de inicialização do DB seja chamada na primeira vez.
    """
    init_db(engine)

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
