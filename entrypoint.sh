#!/bin/sh

# entrypoint.sh: Script de inicialização para o contêiner da API.

# 1. Mensagem de Início
echo "--- [ENTRYPOINT] Contêiner iniciando... ---"

# 2. Inicializa o Banco de Dados
#    Executa nosso script Python para garantir que todas as tabelas
#    do SQLAlchemy existam antes que a aplicação comece.
echo "--- [ENTRYPOINT] Verificando e inicializando o banco de dados... ---"
python create_db.py

# 3. Inicia a Aplicação FastAPI
#    Passa o controle para o comando Uvicorn. O '$@' garante que
#    quaisquer argumentos passados ao 'docker run' ou 'docker-compose'
#    sejam repassados para o uvicorn (não usaremos isso agora, mas é boa prática).
echo "--- [ENTRYPOINT] Iniciando o servidor Uvicorn... ---"
exec "$@"