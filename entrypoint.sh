#!/bin/sh

# ========================================================================== #
#     SCRIPT DE ENTRYPOINT PARA O CONTÊINER DA API FASTAPI (VERSÃO RENDER)   #
# ========================================================================== #
# Este script executa as tarefas essenciais na inicialização do contêiner:
# 1. Executa as migrações do banco de dados com o Alembic para garantir que
#    o schema esteja atualizado com o código mais recente.
# 2. Inicia o servidor Uvicorn para servir a aplicação FastAPI.
#
# NOTA: O bloco de verificação da disponibilidade do banco (com nc) foi
# removido, pois o Render já gerencia o ciclo de vida e a prontidão do
# banco de dados antes de executar este script.

# -------------------------------------------------------------------------- #
#                        EXECUÇÃO DA MIGRAÇÃO DO BANCO DE DADOS               #
# -------------------------------------------------------------------------- #
echo "Executando migrações do banco de dados (Alembic)..."
alembic upgrade head
echo "Migrações concluídas."


# -------------------------------------------------------------------------- #
#                        INICIALIZAÇÃO DO SERVIDOR WEB                       #
# -------------------------------------------------------------------------- #
# Inicia o servidor Uvicorn, tornando a API acessível.
# O host 0.0.0.0 é essencial para que a aplicação seja acessível de fora do contêiner.
echo "Iniciando a aplicação FastAPI com Uvicorn na porta 8000..."
uvicorn src.main:app --host 0.0.0.0 --port 8000