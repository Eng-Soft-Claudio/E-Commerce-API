"""
Suíte de Testes para a Infraestrutura da Aplicação.

Testa componentes de baixo nível como as dependências de banco de dados,
garantindo que o ciclo de vida da sessão (abertura e fechamento) funcione
como esperado fora do ambiente de teste com 'overrides'.
"""
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Componentes da aplicação real que queremos testar
from src.database import get_db, Base, engine

# -------------------------------------------------------------------------- #
#                       SETUP DA APLICAÇÃO E ENDPOINT DE TESTE                   #
# -------------------------------------------------------------------------- #

# SOLUÇÃO WARNING: Renomeado para não começar com 'test_'
app_for_db_test = FastAPI()

@app_for_db_test.get("/test-db")
def db_dependency_test_endpoint(db: Session = Depends(get_db)):
    """
    Este endpoint simples existe apenas para usar a dependência 'get_db' real.
    Verifica se a sessão recebida está ativa.
    """
    # SOLUÇÃO FALHA 1 & 2: A asserção é feita aqui, no lugar certo.
    # a sessão deve estar ativa ao ser usada dentro do endpoint.
    assert db.is_active
    return {"status": "success"}

# -------------------------------------------------------------------------- #
#                             TESTE DA DEPENDÊNCIA GET_DB                          #
# -------------------------------------------------------------------------- #

def test_get_db_dependency_lifecycle():
    """
    Testa se a dependência get_db original cria, fornece e fecha uma sessão.

    Este teste garante a cobertura das linhas da função 'get_db' que eram
    excluídas nos outros testes devido ao uso de 'dependency_overrides'.
    """
    # 1. Setup: Cria as tabelas no banco de dados em memória.
    # Como não usamos fixtures daqui, precisamos fazer o setup manualmente.
    Base.metadata.create_all(bind=engine)

    # 2. Execução: Usa um TestClient com nossa app de teste local.
    with TestClient(app_for_db_test) as client:
        # Quando fazemos a requisição, o FastAPI executa todo o ciclo
        # de vida da dependência:
        # - Chama get_db()
        # - Executa até o 'yield db'
        # - Injeta 'db' no endpoint
        # - O endpoint executa e retorna
        # - O bloco 'finally: db.close()' é executado
        response = client.get("/test-db")
        assert response.status_code == 200
        assert response.json() == {"status": "success"}
    
    # 3. Teardown: Limpa o banco de dados.
    Base.metadata.drop_all(bind=engine)