"""
Script de Inicialização do Banco de Dados de Desenvolvimento.

Este script é projetado para ser executado manualmente uma única vez ou sempre que
o schema do banco de dados for alterado. Sua única responsabilidade é conectar-se
ao banco de dados definido em 'src/database.py' e criar todas as tabelas
com base nos modelos definidos em 'src/models.py'.

Isso garante que a aplicação FastAPI, ao ser iniciada, encontrará um banco de
dados já inicializado e com a estrutura de tabelas correta.
"""

# -------------------------------------------------------------------------- #
#                             IMPORTS E CONFIGURAÇÃO DE CAMINHO              #
# -------------------------------------------------------------------------- #

import sys
from pathlib import Path

SRC_PATH = Path(__file__).parent / "src"
sys.path.append(str(SRC_PATH))

from database import engine, Base
from src import models  # noqa: F401


# -------------------------------------------------------------------------- #
#                            EXECUÇÃO PRINCIPAL                              #
# -------------------------------------------------------------------------- #


def initialize_database():
    """
    Função principal que executa a criação de todas as tabelas.
    """
    print("--- [DB_INIT] Iniciando criação do banco de dados e tabelas... ---")

    try:
        Base.metadata.create_all(bind=engine)
        print("--- [DB_INIT] Banco de dados e tabelas criados com sucesso! ---")
        print(
            "--- [DB_INIT] O arquivo 'minha_api.db' está pronto para uso na raiz do projeto. ---"
        )

    except Exception as e:
        print(f"--- [DB_INIT] Ocorreu um erro ao criar as tabelas: {e} ---")


if __name__ == "__main__":
    initialize_database()
