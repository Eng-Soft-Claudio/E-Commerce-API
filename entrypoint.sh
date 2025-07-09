#!/bin/sh

# ========================================================================== #
#     SCRIPT DE ENTRYPOINT PARA O CONTÊINER DA API FASTAPI                   #
# ========================================================================== #
# Este script executa as tarefas essenciais na inicialização do contêiner:
# 1. Aguarda até que o banco de dados PostgreSQL esteja pronto para aceitar
#    conexões (relevante para o Docker, mas não prejudica no Render).
# 2. Executa as migrações do banco de dados com o Alembic para garantir que
#    o schema esteja atualizado com o código mais recente.
# 3. Inicia o servidor Uvicorn para servir a aplicação FastAPI.

# Aguarda o banco de dados ficar disponível. O nc (netcat) testa se a porta está aberta.
# As variáveis (ex: $POSTGRES_SERVER) vêm das variáveis de ambiente do Render.
echo "Aguardando o banco de dados iniciar em $POSTGRES_SERVER:$POSTGRES_PORT..."
while ! nc -z $POSTGRES_SERVER $POSTGRES_PORT; do
  sleep 1
done
echo "Banco de dados iniciado com sucesso."

# -------------------------------------------------------------------------- #
#                        EXECUÇÃO DA MIGRAÇÃO DO BANCO DE DADOS               #
# -------------------------------------------------------------------------- #
# Esta é a etapa crucial. Ela sincroniza o banco de dados com os modelos do
# seu código (incluindo a nova tabela 'banners') antes que a aplicação comece
# a aceitar requisições.
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