# ========================================================================== #
#                    DOCKERFILE PARA APLICAÇÃO FASTAPI                       #
# ========================================================================== #
# Este Dockerfile define os passos para criar uma imagem Docker para a
# aplicação FastAPI. Ele configura um ambiente Python, instala as
# dependências, copia o código fonte e define o comando de inicialização.
#

# -------------------------------------------------------------------------- #
#                                IMAGEM BASE                                 #
# -------------------------------------------------------------------------- #
# Utiliza uma imagem oficial do Python como base. A tag "slim" oferece um
# bom equilíbrio entre tamanho reduzido e a disponibilidade das bibliotecas
# de sistema essenciais.
FROM python:3.13-slim

# -------------------------------------------------------------------------- #
#                         DIRETÓRIO DE TRABALHO                              #
# -------------------------------------------------------------------------- #
# Define o diretório de trabalho padrão dentro do contêiner. Todos os
# comandos subsequentes (RUN, COPY, CMD) serão executados a partir deste
# caminho.
WORKDIR /app

# -------------------------------------------------------------------------- #
#                      INSTALAÇÃO DE DEPENDÊNCIAS                            #
# -------------------------------------------------------------------------- #
# Copia o arquivo de dependências separadamente para aproveitar o cache de
# camadas do Docker. Esta etapa só será re-executada se o conteúdo do
# requirements.txt for alterado.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# -------------------------------------------------------------------------- #
#                           CÓPIA DO CÓDIGO FONTE                            #
# -------------------------------------------------------------------------- #
# Copia o código fonte da aplicação para dentro do contêiner. Em um
# ambiente de desenvolvimento, este código será "sobreposto" pelo volume
# montado no docker-compose.yml, mas é crucial para criar uma imagem
# autocontida que funcione de forma independente.
COPY ./src ./src

# -------------------------------------------------------------------------- #
#                      CONFIGURAÇÃO DE REDE E EXECUÇÃO                       #
# -------------------------------------------------------------------------- #
# Expõe a porta em que a aplicação será executada dentro do contêiner,
# permitindo que o Docker mapeie essa porta para o host.
EXPOSE 8000

# Define o comando padrão para iniciar a aplicação quando o contêiner for
# executado.
# --host 0.0.0.0: Faz o servidor escutar em todas as interfaces de rede,
#   tornando-o acessível de fora do contêiner.
# --reload: Ativa o recarregamento automático do servidor ao detectar
#   alterações nos arquivos, ideal para o desenvolvimento .
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]