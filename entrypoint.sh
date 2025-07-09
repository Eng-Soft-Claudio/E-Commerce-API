#!/bin/sh

# ========================================================================== #
#  SCRIPT DE ENTRYPOINT ROBUSTO PARA O CONTÊINER DA API FASTAPI (PRODUÇÃO)  #
# ========================================================================== #
# Este script garante a correta inicialização da aplicação:
# 1. Executa as migrações do Alembic.
# 2. VERIFICA se a migração foi bem-sucedida. Se falhar, o script para
#    imediatamente, fazendo com que o deploy no Render falhe e exiba o
#    erro nos logs.
# 3. Se a migração for bem-sucedida, inicia o servidor Uvicorn.

# -------------------------------------------------------------------------- #
#                        EXECUÇÃO E VERIFICAÇÃO DA MIGRAÇÃO                   #
# -------------------------------------------------------------------------- #
echo "Executando migrações do banco de dados (Alembic)..."

# Executa o comando e verifica o código de saída ($?)
alembic upgrade head

# A variável $? contém o código de saída do último comando executado.
# 0 significa sucesso, qualquer outro valor significa erro.
if [ $? -ne 0 ]; then
  echo "!!! FALHA NA MIGRAÇÃO DO BANCO DE DADOS (ALEMBIC) !!!"
  echo "O deploy será interrompido. Verifique os erros acima."
  exit 1
fi

echo "Migrações do banco de dados concluídas com sucesso."


# -------------------------------------------------------------------------- #
#                        INICIALIZAÇÃO DO SERVIDOR WEB                       #
# -------------------------------------------------------------------------- #
# Esta linha só será executada se as migrações tiverem sucesso.
echo "Iniciando a aplicação FastAPI com Uvicorn na porta 8000..."
uvicorn src.main:app --host 0.0.0.0 --port 8000